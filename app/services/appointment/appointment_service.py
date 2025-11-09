"""
Servicio de Citas - Lógica de negocio principal
RF-05: Gestión de citas (agendar, reprogramar, cancelar)
Integra todos los patrones de diseño
"""

from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from app.models.appointment import Appointment, AppointmentStatus
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.service_repository import ServiceRepository
from app.repositories.pet_repository import PetRepository
from app.repositories.user_repository import UserRepository
from app.schemas.appointment_schema import AppointmentCreate, AppointmentUpdate

from .states import AppointmentStateManager
from .strategies import GestorAgendamiento, PoliticaEstandar, PoliticaReprogramacion
from .observers import get_gestor_citas


class AppointmentService:
    """
    Servicio principal de gestión de citas
    Implementa patrones: State, Strategy, Observer, Template Method
    """
    CITA_NOT_FOUND_MSG = "Cita no encontrado"

    def __init__(self, db: Session):
        self.db = db
        self.repository = AppointmentRepository(db)
        self.service_repo = ServiceRepository(db)
        self.pet_repo = PetRepository(db)
        self.user_repo = UserRepository(db)

        # Gestor de estados (State Pattern)
        self.state_manager = AppointmentStateManager

        # Gestor de observadores (Observer Pattern)
        self.gestor_citas = get_gestor_citas()

    def create_appointment(
            self,
            appointment_data: AppointmentCreate,
            creado_por: Optional[UUID] = None
    ) -> Appointment:
        """
        Crea una nueva cita

        Template Method:
        1. Validar datos
        2. Validar anticipación (Strategy)
        3. Validar disponibilidad
        4. Crear cita
        5. Notificar (Observer)

        Args:
            appointment_data: Datos de la cita
            creado_por: ID del usuario que crea la cita

        Returns:
            Appointment creada

        Raises:
            ValueError: Si hay errores de validación
        """
        # 1. Validar que existan las entidades relacionadas
        self._validar_entidades(appointment_data)

        # 2. Validar anticipación usando Strategy Pattern
        gestor = GestorAgendamiento(PoliticaEstandar())
        es_valida, mensaje_error = gestor.validar(appointment_data.fecha_hora)
        if not es_valida:
            raise ValueError(mensaje_error)

        # 3. Validar disponibilidad del veterinario
        servicio = self.service_repo.get_by_id(appointment_data.servicio_id)
        if not self.repository.check_availability(
                veterinario_id=appointment_data.veterinario_id,
                fecha_hora=appointment_data.fecha_hora,
                duracion_minutos=servicio.duracion_minutos
        ):
            raise ValueError(
                "El horario no está disponible. Por favor seleccione otro horario."
            )

        # 4. Crear la cita
        appointment = Appointment(
            mascota_id=appointment_data.mascota_id,
            veterinario_id=appointment_data.veterinario_id,
            servicio_id=appointment_data.servicio_id,
            fecha_hora=appointment_data.fecha_hora,
            motivo=appointment_data.motivo,
            estado=AppointmentStatus.AGENDADA,
            creado_por=creado_por
        )

        appointment = self.repository.create(appointment)

        # 5. Notificar a observadores (Observer Pattern)
        self.gestor_citas.notificar(
            "CITA_CREADA",
            appointment,
            usuario_id=creado_por,
            accion="Creación de cita"
        )

        return appointment

    def get_appointment_by_id(self, appointment_id: UUID) -> Optional[Appointment]:
        """Obtiene una cita por ID"""
        return self.repository.get_by_id(appointment_id)

    def get_all_appointments(
            self,
            skip: int = 0,
            limit: int = 100,
            estado: Optional[AppointmentStatus] = None,
            mascota_id: Optional[UUID] = None,
            veterinario_id: Optional[UUID] = None,
            fecha_desde: Optional[datetime] = None,
            fecha_hasta: Optional[datetime] = None
    ) -> List[Appointment]:
        """
        Obtiene todas las citas con filtros opcionales

        Args:
            skip: Registros a omitir (paginación)
            limit: Límite de registros
            estado: Filtrar por estado
            mascota_id: Filtrar por mascota
            veterinario_id: Filtrar por veterinario
            fecha_desde: Filtrar desde fecha
            fecha_hasta: Filtrar hasta fecha

        Returns:
            Lista de citas
        """
        return self.repository.get_all(
            skip=skip,
            limit=limit,
            estado=estado,
            mascota_id=mascota_id,
            veterinario_id=veterinario_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta
        )

    def reschedule_appointment(
            self,
            appointment_id: UUID,
            nueva_fecha: datetime,
            usuario_id: Optional[UUID] = None
    ) -> Appointment:
        """
        Reprograma una cita existente

        RN08-3: Reprogramaciones solo se permiten hasta 2 horas antes

        Args:
            appointment_id: ID de la cita
            nueva_fecha: Nueva fecha y hora
            usuario_id: ID del usuario que reprograma

        Returns:
            Appointment reprogramada

        Raises:
            ValueError: Si no se puede reprogramar
        """
        # Obtener cita
        appointment = self.repository.get_by_id(appointment_id)
        if not appointment:
            raise ValueError(self.CITA_NOT_FOUND_MSG)

        # Validar anticipación con Strategy Pattern
        gestor = GestorAgendamiento(PoliticaReprogramacion())
        es_valida, mensaje_error = gestor.validar(nueva_fecha)
        if not es_valida:
            raise ValueError(mensaje_error)

        # Validar disponibilidad del veterinario
        servicio = self.service_repo.get_by_id(appointment.servicio_id)
        if not self.repository.check_availability(
                veterinario_id=appointment.veterinario_id,
                fecha_hora=nueva_fecha,
                duracion_minutos=servicio.duracion_minutos,
                exclude_appointment_id=appointment_id
        ):
            raise ValueError("El nuevo horario no está disponible")

        # Guardar fecha anterior para auditoría
        fecha_anterior = appointment.fecha_hora

        # Reprogramar usando State Pattern
        try:
            self.state_manager.reprogramar(appointment, nueva_fecha)
            appointment = self.repository.update(appointment)

            # Notificar a observadores
            self.gestor_citas.notificar(
                "CITA_REPROGRAMADA",
                appointment,
                usuario_id=usuario_id,
                fecha_anterior=fecha_anterior.isoformat(),
                fecha_nueva=nueva_fecha.isoformat()
            )

            return appointment

        except ValueError as e:
            raise ValueError(f"No se puede reprogramar: {str(e)}")

    def confirm_appointment(
            self,
            appointment_id: UUID,
            usuario_id: Optional[UUID] = None
    ) -> Appointment:
        """
        Confirma una cita

        Args:
            appointment_id: ID de la cita
            usuario_id: ID del usuario que confirma

        Returns:
            Appointment confirmada

        Raises:
            ValueError: Si no se puede confirmar
        """
        appointment = self.repository.get_by_id(appointment_id)
        if not appointment:
            raise ValueError(self.CITA_NOT_FOUND_MSG)

        try:
            # Confirmar usando State Pattern
            self.state_manager.confirmar(appointment)
            appointment = self.repository.update(appointment)

            # Notificar a observadores
            self.gestor_citas.notificar(
                "CITA_CONFIRMADA",
                appointment,
                usuario_id=usuario_id
            )

            return appointment

        except ValueError as e:
            raise ValueError(f"No se puede confirmar: {str(e)}")

    def cancel_appointment(
            self,
            appointment_id: UUID,
            usuario_id: Optional[UUID] = None
    ) -> Appointment:
        """
        Cancela una cita

        RN08-2: Cancelaciones con menos de 4 horas se registran como tardías

        Args:
            appointment_id: ID de la cita
            usuario_id: ID del usuario que cancela

        Returns:
            Appointment cancelada

        Raises:
            ValueError: Si no se puede cancelar
        """
        appointment = self.repository.get_by_id(appointment_id)
        if not appointment:
            raise ValueError(self.CITA_NOT_FOUND_MSG)

        try:
            # Cancelar usando State Pattern (detecta cancelación tardía)
            self.state_manager.cancelar(appointment)
            appointment = self.repository.update(appointment)

            # Notificar a observadores
            self.gestor_citas.notificar(
                "CITA_CANCELADA",
                appointment,
                usuario_id=usuario_id,
                cancelacion_tardia=appointment.cancelacion_tardia
            )

            return appointment

        except ValueError as e:
            raise ValueError(f"No se puede cancelar: {str(e)}")

    def start_appointment(
            self,
            appointment_id: UUID,
            usuario_id: Optional[UUID] = None
    ) -> Appointment:
        """
        Inicia una cita (cambiar a estado EN_PROCESO)

        Args:
            appointment_id: ID de la cita
            usuario_id: ID del usuario que inicia

        Returns:
            Appointment en proceso

        Raises:
            ValueError: Si no se puede iniciar
        """
        appointment = self.repository.get_by_id(appointment_id)
        if not appointment:
            raise ValueError("Cita no encontrada")

        try:
            self.state_manager.iniciar(appointment)
            appointment = self.repository.update(appointment)

            self.gestor_citas.notificar(
                "CITA_INICIADA",
                appointment,
                usuario_id=usuario_id
            )

            return appointment

        except ValueError as e:
            raise ValueError(f"No se puede iniciar: {str(e)}")

    def complete_appointment(
            self,
            appointment_id: UUID,
            notas: Optional[str] = None,
            usuario_id: Optional[UUID] = None
    ) -> Appointment:
        """
        Completa una cita (cambiar a estado COMPLETADA)

        Args:
            appointment_id: ID de la cita
            notas: Notas finales de la cita
            usuario_id: ID del usuario que completa

        Returns:
            Appointment completada

        Raises:
            ValueError: Si no se puede completar
        """
        appointment = self.repository.get_by_id(appointment_id)
        if not appointment:
            raise ValueError("Cita no encontrada")

        try:
            if notas:
                appointment.notas = notas

            self.state_manager.finalizar(appointment)
            appointment = self.repository.update(appointment)

            self.gestor_citas.notificar(
                "CITA_COMPLETADA",
                appointment,
                usuario_id=usuario_id
            )

            return appointment

        except ValueError as e:
            raise ValueError(f"No se puede completar: {str(e)}")

    def _validar_entidades(self, appointment_data: AppointmentCreate) -> None:
        """
        Valida que existan las entidades relacionadas

        Raises:
            ValueError: Si alguna entidad no existe
        """
        # Validar mascota
        if not self.pet_repo.get_by_id(appointment_data.mascota_id):
            raise ValueError("La mascota no existe")

        # Validar veterinario
        veterinario = self.user_repo.get_by_id(appointment_data.veterinario_id)
        if not veterinario:
            raise ValueError("El veterinario no existe")
        if veterinario.rol.value not in ["veterinario", "superadmin"]:
            raise ValueError("El usuario seleccionado no es un veterinario")

        # Validar servicio
        servicio = self.service_repo.get_by_id(appointment_data.servicio_id)
        if not servicio:
            raise ValueError("El servicio no existe")
        if not servicio.activo:
            raise ValueError("El servicio no está disponible")