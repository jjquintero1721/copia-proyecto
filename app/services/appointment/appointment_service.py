"""
Servicio de Citas - Lógica de negocio principal
RF-05: Gestión de citas (agendar, reprogramar, cancelar)
Integra todos los patrones de diseño
"""

from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date

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
        # ← CAMBIO IMPORTANTE
        self.gestor_citas = get_gestor_citas(self.db)

    def create_appointment(
            self,
            appointment_data: AppointmentCreate,
            creado_por: Optional[UUID] = None
    ) -> Appointment:

        self._validar_entidades(appointment_data)

        gestor = GestorAgendamiento(PoliticaEstandar())
        es_valida, mensaje_error = gestor.validar(appointment_data.fecha_hora)
        if not es_valida:
            raise ValueError(mensaje_error)

        servicio = self.service_repo.get_by_id(appointment_data.servicio_id)
        if not self.repository.check_availability(
                veterinario_id=appointment_data.veterinario_id,
                fecha_hora=appointment_data.fecha_hora,
                duracion_minutos=servicio.duracion_minutos
        ):
            raise ValueError("El horario no está disponible.")

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

        self.gestor_citas.notificar(
            "CITA_CREADA",
            appointment,
            {
                "usuario_id": creado_por,
                "accion": "Creación de cita"
            }
        )

        return appointment

    def get_appointment_by_id(self, appointment_id: UUID) -> Optional[Appointment]:
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

        return self.repository.get_all(
            skip=skip,
            limit=limit,
            estado=estado,
            mascota_id=mascota_id,
            veterinario_id=veterinario_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta
        )

    def get_appointments_by_date(
            self,
            fecha: date,
            veterinario_id: Optional[UUID] = None
    ) -> List[Appointment]:

        from datetime import datetime, timezone, timedelta

        fecha_inicio = datetime.combine(fecha, datetime.min.time()).replace(tzinfo=timezone.utc)
        fecha_fin = fecha_inicio + timedelta(days=1)

        return self.get_all_appointments(
            fecha_desde=fecha_inicio,
            fecha_hasta=fecha_fin,
            veterinario_id=veterinario_id
        )

    def reschedule_appointment(
            self,
            appointment_id: UUID,
            nueva_fecha: datetime,
            usuario_id: Optional[UUID] = None
    ) -> Appointment:

        appointment = self.repository.get_by_id(appointment_id)
        if not appointment:
            raise ValueError(self.CITA_NOT_FOUND_MSG)

        gestor = GestorAgendamiento(PoliticaReprogramacion())
        es_valida, mensaje_error = gestor.validar(nueva_fecha)
        if not es_valida:
            raise ValueError(mensaje_error)

        servicio = self.service_repo.get_by_id(appointment.servicio_id)
        if not self.repository.check_availability(
                veterinario_id=appointment.veterinario_id,
                fecha_hora=nueva_fecha,
                duracion_minutos=servicio.duracion_minutos,
                exclude_appointment_id=appointment_id
        ):
            raise ValueError("El nuevo horario no está disponible")

        fecha_anterior = appointment.fecha_hora

        try:
            self.state_manager.reprogramar(appointment, nueva_fecha)
            appointment = self.repository.update(appointment)

            self.gestor_citas.notificar(
                "CITA_REPROGRAMADA",
                appointment,
                {
                    "usuario_id": usuario_id,
                    "fecha_anterior": fecha_anterior.isoformat(),
                    "fecha_nueva": nueva_fecha.isoformat(),
                    "accion": "Reprogramación de cita"
                }
            )

            return appointment

        except ValueError as e:
            raise ValueError(f"No se puede reprogramar: {str(e)}")

    def confirm_appointment(
            self,
            appointment_id: UUID,
            usuario_id: Optional[UUID] = None
    ) -> Appointment:

        appointment = self.repository.get_by_id(appointment_id)
        if not appointment:
            raise ValueError(self.CITA_NOT_FOUND_MSG)

        try:
            self.state_manager.confirmar(appointment)
            appointment = self.repository.update(appointment)

            self.gestor_citas.notificar(
                "CITA_CONFIRMADA",
                appointment,
                {
                    "usuario_id": usuario_id,
                    "accion": "Confirmación de cita"
                }
            )

            return appointment

        except ValueError as e:
            raise ValueError(f"No se puede confirmar: {str(e)}")

    def cancel_appointment(
            self,
            appointment_id: UUID,
            usuario_id: Optional[UUID] = None
    ) -> Appointment:

        appointment = self.repository.get_by_id(appointment_id)
        if not appointment:
            raise ValueError(self.CITA_NOT_FOUND_MSG)

        try:
            self.state_manager.cancelar(appointment)
            appointment = self.repository.update(appointment)

            self.gestor_citas.notificar(
                "CITA_CANCELADA",
                appointment,
                {
                    "usuario_id": usuario_id,
                    "cancelacion_tardia": appointment.cancelacion_tardia,
                    "accion": "Cancelación de cita"
                }
            )

            return appointment

        except ValueError as e:
            raise ValueError(f"No se puede cancelar: {str(e)}")

    def start_appointment(
            self,
            appointment_id: UUID,
            usuario_id: Optional[UUID] = None
    ) -> Appointment:

        appointment = self.repository.get_by_id(appointment_id)
        if not appointment:
            raise ValueError("Cita no encontrada")

        try:
            self.state_manager.iniciar(appointment)
            appointment = self.repository.update(appointment)

            self.gestor_citas.notificar(
                "CITA_INICIADA",
                appointment,
                {
                    "usuario_id": usuario_id,
                    "accion": "Inicio de cita"
                }
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
                {
                    "usuario_id": usuario_id,
                    "accion": "Finalización de cita"
                }
            )

            return appointment

        except ValueError as e:
            raise ValueError(f"No se puede completar: {str(e)}")

    def _validar_entidades(self, appointment_data: AppointmentCreate) -> None:
        if not self.pet_repo.get_by_id(appointment_data.mascota_id):
            raise ValueError("La mascota no existe")

        veterinario = self.user_repo.get_by_id(appointment_data.veterinario_id)
        if not veterinario:
            raise ValueError("El veterinario no existe")
        if veterinario.rol.value not in ["veterinario", "superadmin"]:
            raise ValueError("El usuario no es un veterinario válido")

        servicio = self.service_repo.get_by_id(appointment_data.servicio_id)
        if not servicio:
            raise ValueError("El servicio no existe")
        if not servicio.activo:
            raise ValueError("El servicio no está disponible")