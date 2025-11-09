"""
Facade Pattern - Interfaz simplificada para operaciones de citas
Orquesta operaciones complejas coordinando múltiples servicios
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from app.services.appointment.appointment_service import AppointmentService
from app.services.service_service import ServiceService
from app.repositories.pet_repository import PetRepository
from app.repositories.user_repository import UserRepository
from app.schemas.appointment_schema import AppointmentCreate


class AppointmentFacade:
    """
    Facade Pattern: Simplifica la interacción con el módulo de citas
    Orquesta operaciones complejas que involucran múltiples servicios
    """

    def __init__(self, db: Session):
        self.db = db
        self.appointment_service = AppointmentService(db)
        self.service_service = ServiceService(db)
        self.pet_repo = PetRepository(db)
        self.user_repo = UserRepository(db)

    def agendar_cita_completa(
            self,
            mascota_id: UUID,
            veterinario_id: UUID,
            servicio_id: UUID,
            fecha_hora: datetime,
            motivo: Optional[str] = None,
            usuario_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Operación completa de agendamiento de cita

        Orquesta:
        1. Validación de datos
        2. Obtención de información relacionada
        3. Creación de la cita
        4. Preparación de respuesta enriquecida

        Args:
            mascota_id: ID de la mascota
            veterinario_id: ID del veterinario
            servicio_id: ID del servicio
            fecha_hora: Fecha y hora de la cita
            motivo: Motivo de la consulta
            usuario_id: ID del usuario que agenda

        Returns:
            Dict con información completa de la cita creada

        Raises:
            ValueError: Si hay errores en la operación
        """
        # 1. Crear cita
        appointment_data = AppointmentCreate(
            mascota_id=mascota_id,
            veterinario_id=veterinario_id,
            servicio_id=servicio_id,
            fecha_hora=fecha_hora,
            motivo=motivo
        )

        cita = self.appointment_service.create_appointment(appointment_data, usuario_id)

        # 2. Obtener información relacionada
        mascota = self.pet_repo.get_by_id(mascota_id)
        veterinario = self.user_repo.get_by_id(veterinario_id)
        servicio = self.service_service.get_service_by_id(servicio_id)

        # 3. Preparar respuesta enriquecida
        return {
            "cita": cita.to_dict(),
            "mascota": {
                "id": str(mascota.id),
                "nombre": mascota.nombre,
                "especie": mascota.especie
            },
            "veterinario": {
                "id": str(veterinario.id),
                "nombre": veterinario.nombre
            },
            "servicio": {
                "id": str(servicio.id),
                "nombre": servicio.nombre,
                "duracion_minutos": servicio.duracion_minutos,
                "costo": servicio.costo
            },
            "mensaje": "Cita agendada exitosamente. Se ha enviado confirmación por correo."
        }

    def reprogramar_cita_completa(
            self,
            appointment_id: UUID,
            nueva_fecha: datetime,
            usuario_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Operación completa de reprogramación de cita

        Args:
            appointment_id: ID de la cita
            nueva_fecha: Nueva fecha y hora
            usuario_id: ID del usuario que reprograma

        Returns:
            Dict con información de la cita reprogramada

        Raises:
            ValueError: Si hay errores en la operación
        """
        cita = self.appointment_service.reschedule_appointment(
            appointment_id,
            nueva_fecha,
            usuario_id
        )

        return {
            "cita": cita.to_dict(),
            "mensaje": "Cita reprogramada exitosamente. Se ha enviado notificación por correo."
        }

    def cancelar_cita_completa(
            self,
            appointment_id: UUID,
            usuario_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Operación completa de cancelación de cita

        Args:
            appointment_id: ID de la cita
            usuario_id: ID del usuario que cancela

        Returns:
            Dict con información de la cita cancelada

        Raises:
            ValueError: Si hay errores en la operación
        """
        cita = self.appointment_service.cancel_appointment(appointment_id, usuario_id)

        mensaje = "Cita cancelada exitosamente."
        if cita.cancelacion_tardia:
            mensaje += " Nota: Esta fue una cancelación tardía (menos de 4 horas de anticipación)."

        return {
            "cita": cita.to_dict(),
            "mensaje": mensaje
        }

    def obtener_disponibilidad_veterinario(
            self,
            veterinario_id: UUID,
            fecha: datetime,
            duracion_minutos: int = 30
    ) -> Dict[str, Any]:
        """
        Obtiene la disponibilidad de un veterinario en un día específico

        Args:
            veterinario_id: ID del veterinario
            fecha: Fecha a consultar
            duracion_minutos: Duración estimada de la cita

        Returns:
            Dict con horarios disponibles

        Raises:
            ValueError: Si el veterinario no existe
        """
        veterinario = self.user_repo.get_by_id(veterinario_id)
        if not veterinario:
            raise ValueError("Veterinario no encontrado")

        # Definir horario de trabajo (8:00 AM - 6:00 PM)
        inicio_jornada = fecha.replace(hour=8, minute=0, second=0, microsecond=0)
        fin_jornada = fecha.replace(hour=18, minute=0, second=0, microsecond=0)

        # Obtener citas del día
        self.appointment_service.repository.get_by_date_range(
            inicio_jornada,
            fin_jornada,
            veterinario_id
        )

        # Calcular horarios disponibles
        horarios_disponibles = []
        hora_actual = inicio_jornada

        while hora_actual < fin_jornada:
            disponible = self.appointment_service.repository.check_availability(
                veterinario_id,
                hora_actual,
                duracion_minutos
            )

            if disponible:
                horarios_disponibles.append(hora_actual.isoformat())

            hora_actual = hora_actual + timedelta(minutes=30)  # Intervalos de 30 min

        return {
            "veterinario": {
                "id": str(veterinario.id),
                "nombre": veterinario.nombre
            },
            "fecha": fecha.date().isoformat(),
            "horarios_disponibles": horarios_disponibles,
            "total_disponibles": len(horarios_disponibles)
        }


# Importación necesaria para timedelta
from datetime import timedelta