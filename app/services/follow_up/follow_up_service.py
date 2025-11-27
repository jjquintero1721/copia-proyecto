"""
Servicio de Seguimiento de Pacientes - Lógica de negocio
RF-11: Seguimiento de pacientes
Implementa patrones: Builder, Template Method, Command
"""

from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone, timedelta
from app.utils.datetime_helpers import ensure_timezone_aware, now_utc

from app.models.appointment import Appointment, AppointmentStatus
from app.models.consultation import Consultation
from app.repositories.consultation_repository import ConsultationRepository
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.service_repository import ServiceRepository
from app.schemas.follow_up_schema import (
    FollowUpCreate,
    FollowUpResponse,
    FollowUpCompletionCreate
)
from app.schemas.consultation_schema import ConsultationCreate


class FollowUpService:
    """
    Servicio principal de gestión de seguimientos
    Implementa Template Method para proceso estructurado

    RF-11: Permitir registrar seguimientos posteriores a consultas o tratamientos
    """

    def __init__(self, db: Session):
        self.db = db
        self.consultation_repo = ConsultationRepository(db)
        self.appointment_repo = AppointmentRepository(db)
        self.service_repo = ServiceRepository(db)

    def create_follow_up_appointment(
            self,
            follow_up_data: FollowUpCreate,
            creado_por: UUID
    ) -> Dict[str, Any]:
        """
        Crea una cita de seguimiento desde una consulta original

        Template Method:
        1. Validar consulta origen
        2. Obtener datos de la mascota
        3. Crear cita de seguimiento
        4. Vincular cita con consulta origen
        5. Retornar información completa

        Criterio de aceptación RF-11:
        "DADO que un veterinario recomienda seguimiento
         CUANDO lo programa
         ENTONCES el sistema crea una nueva cita asociada a la consulta original"

        Args:
            follow_up_data: Datos del seguimiento
            creado_por: ID del usuario que crea el seguimiento

        Returns:
            Dict con información de la cita de seguimiento creada

        Raises:
            ValueError: Si hay errores de validación
        """
        # 1. Validar que la consulta origen exista
        consulta_origen = self.consultation_repo.get_by_id(
            follow_up_data.consulta_origen_id
        )
        if not consulta_origen:
            raise ValueError("La consulta original no existe")

        # 2. Validar que el servicio exista y esté activo
        servicio = self.service_repo.get_by_id(follow_up_data.servicio_id)
        if not servicio:
            raise ValueError("El servicio especificado no existe")
        if not servicio.activo:
            raise ValueError("El servicio especificado no está activo")

        # 3. Validar que la fecha de seguimiento sea futura
        fecha_seguimiento_aware = ensure_timezone_aware(follow_up_data.fecha_hora_seguimiento)
        if fecha_seguimiento_aware <= now_utc():
            raise ValueError("La fecha de seguimiento debe ser futura")


        # 4. Validar disponibilidad del veterinario
        if not self.appointment_repo.check_availability(
                veterinario_id=follow_up_data.veterinario_id,
                fecha_hora=follow_up_data.fecha_hora_seguimiento,
                duracion_minutos=servicio.duracion_minutos
        ):
            raise ValueError(
                "El veterinario no está disponible en el horario seleccionado"
            )

        # 5. Crear la cita de seguimiento usando Builder Pattern
        follow_up_appointment = Appointment(
            mascota_id=consulta_origen.historia_clinica.mascota_id,
            veterinario_id=follow_up_data.veterinario_id,
            servicio_id=follow_up_data.servicio_id,
            fecha_hora=follow_up_data.fecha_hora_seguimiento,
            motivo=follow_up_data.motivo_seguimiento,
            estado=AppointmentStatus.AGENDADA,
            notas=(
                f"SEGUIMIENTO de consulta {consulta_origen.id}\n"
                f"Días recomendados: {follow_up_data.dias_recomendados or 'N/A'}\n"
                f"{follow_up_data.notas or ''}"
            ),
            creado_por=creado_por,
            fecha_creacion=datetime.now(timezone.utc)
        )

        # 6. Persistir la cita de seguimiento
        follow_up_appointment = self.appointment_repo.create(follow_up_appointment)

        # 7. Crear relación entre consulta origen y cita de seguimiento
        # (Se almacena en las notas y se puede recuperar por patrón)

        # 8. Retornar información completa
        return {
            "cita_seguimiento_id": follow_up_appointment.id,
            "consulta_origen_id": consulta_origen.id,
            "mascota_id": consulta_origen.historia_clinica.mascota_id,
            "veterinario_id": follow_up_appointment.veterinario_id,
            "servicio_id": follow_up_appointment.servicio_id,
            "fecha_hora_seguimiento": follow_up_appointment.fecha_hora,
            "motivo_seguimiento": follow_up_appointment.motivo,
            "estado": follow_up_appointment.estado.value,
            "dias_recomendados": follow_up_data.dias_recomendados,
            "notas": follow_up_data.notas,
            "fecha_creacion": follow_up_appointment.fecha_creacion
        }

    def get_follow_ups_by_consultation(
            self,
            consulta_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Obtiene todos los seguimientos asociados a una consulta

        Args:
            consulta_id: ID de la consulta original

        Returns:
            Lista de seguimientos
        """
        # Validar que la consulta exista
        consulta = self.consultation_repo.get_by_id(consulta_id)
        if not consulta:
            raise ValueError("La consulta no existe")

        # Buscar citas que contengan referencia a esta consulta en las notas
        # (Búsqueda por patrón en las notas)
        all_appointments = self.appointment_repo.get_all()

        follow_ups = []
        for appointment in all_appointments:
            if appointment.notas and f"SEGUIMIENTO de consulta {consulta_id}" in appointment.notas:
                follow_ups.append({
                    "cita_seguimiento_id": appointment.id,
                    "consulta_origen_id": consulta_id,
                    "mascota_id": appointment.mascota_id,
                    "veterinario_id": appointment.veterinario_id,
                    "servicio_id": appointment.servicio_id,
                    "fecha_hora_seguimiento": appointment.fecha_hora,
                    "motivo_seguimiento": appointment.motivo,
                    "estado": appointment.estado.value,
                    "notas": appointment.notas,
                    "fecha_creacion": appointment.fecha_creacion
                })

        return follow_ups

    def complete_follow_up(
            self,
            completion_data: FollowUpCompletionCreate,
            veterinario_id: UUID
    ) -> Consultation:
        """
        Registra la consulta de seguimiento completada

        Template Method:
        1. Validar cita de seguimiento
        2. Obtener consulta origen
        3. Crear consulta de seguimiento
        4. Vincular al historial clínico
        5. Actualizar estado de cita

        Criterio de aceptación RF-11:
        "DADO que se realiza seguimiento
         CUANDO se guarda la consulta
         ENTONCES se vincula automáticamente al historial clínico"

        Args:
            completion_data: Datos de la consulta de seguimiento
            veterinario_id: ID del veterinario que realiza el seguimiento

        Returns:
            Consultation creada

        Raises:
            ValueError: Si hay errores de validación
        """
        # 1. Validar que la cita de seguimiento exista
        cita_seguimiento = self.appointment_repo.get_by_id(
            completion_data.cita_seguimiento_id
        )
        if not cita_seguimiento:
            raise ValueError("La cita de seguimiento no existe")

        # 2. Validar que la cita esté en estado correcto
        if cita_seguimiento.estado not in [
            AppointmentStatus.CONFIRMADA,
            AppointmentStatus.EN_PROCESO
        ]:
            raise ValueError(
                "La cita debe estar confirmada o en proceso para completar el seguimiento"
            )

        # 3. Obtener la consulta origen desde las notas
        consulta_origen_id = self._extract_original_consultation_id(
            cita_seguimiento.notas
        )
        if not consulta_origen_id:
            raise ValueError("No se pudo identificar la consulta origen")

        consulta_origen = self.consultation_repo.get_by_id(consulta_origen_id)
        if not consulta_origen:
            raise ValueError("La consulta origen no existe")

        # 4. Crear la consulta de seguimiento vinculada al historial clínico
        consultation_data = ConsultationCreate(
            historia_clinica_id=consulta_origen.historia_clinica_id,
            veterinario_id=veterinario_id,
            cita_id=cita_seguimiento.id,
            fecha_hora=datetime.now(timezone.utc),
            motivo=completion_data.motivo,
            anamnesis=completion_data.anamnesis,
            signos_vitales=completion_data.signos_vitales,
            diagnostico=completion_data.diagnostico,
            tratamiento=completion_data.tratamiento,
            vacunas=completion_data.vacunas,
            observaciones=(
                f"SEGUIMIENTO de consulta {consulta_origen.id}\n"
                f"EVOLUCIÓN: {completion_data.evolucion}\n"
                f"{completion_data.observaciones or ''}"
            )
        )

        # Importar servicio de historias clínicas para crear la consulta
        from app.services.medical_history.medical_history_service import MedicalHistoryService
        medical_service = MedicalHistoryService(self.db)

        consulta_seguimiento = medical_service.create_consultation(
            consultation_data,
            veterinario_id
        )

        # 5. Actualizar estado de la cita a COMPLETADA
        cita_seguimiento.estado = AppointmentStatus.COMPLETADA
        self.appointment_repo.update(cita_seguimiento)

        return consulta_seguimiento

    def _extract_original_consultation_id(self, notas: Optional[str]) -> Optional[UUID]:
        """
        Extrae el ID de la consulta origen de las notas de la cita

        Args:
            notas: Notas de la cita

        Returns:
            UUID de la consulta origen o None
        """
        if not notas:
            return None

        import re
        # Patrón para encontrar "SEGUIMIENTO de consulta <UUID>"
        pattern = r"SEGUIMIENTO de consulta ([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
        match = re.search(pattern, notas, re.IGNORECASE)

        if match:
            try:
                return UUID(match.group(1))
            except (ValueError, AttributeError):
                return None

        return None

    def get_follow_up_statistics(
            self,
            mascota_id: Optional[UUID] = None,
            veterinario_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas de seguimientos

        Args:
            mascota_id: Filtrar por mascota (opcional)
            veterinario_id: Filtrar por veterinario (opcional)

        Returns:
            Dict con estadísticas
        """
        all_appointments = self.appointment_repo.get_all()

        # Filtrar citas de seguimiento
        follow_up_appointments = [
            apt for apt in all_appointments
            if apt.notas and "SEGUIMIENTO de consulta" in apt.notas
        ]

        # Aplicar filtros opcionales
        if mascota_id:
            follow_up_appointments = [
                apt for apt in follow_up_appointments
                if apt.mascota_id == mascota_id
            ]

        if veterinario_id:
            follow_up_appointments = [
                apt for apt in follow_up_appointments
                if apt.veterinario_id == veterinario_id
            ]

        # Calcular estadísticas
        total_seguimientos = len(follow_up_appointments)
        seguimientos_completados = len([
            apt for apt in follow_up_appointments
            if apt.estado == AppointmentStatus.COMPLETADA
        ])
        seguimientos_pendientes = len([
            apt for apt in follow_up_appointments
            if apt.estado in [
                AppointmentStatus.AGENDADA,
                AppointmentStatus.CONFIRMADA
            ]
        ])
        seguimientos_cancelados = len([
            apt for apt in follow_up_appointments
            if apt.estado in [
                AppointmentStatus.CANCELADA,
                AppointmentStatus.CANCELADA_TARDIA
            ]
        ])

        return {
            "total_seguimientos": total_seguimientos,
            "completados": seguimientos_completados,
            "pendientes": seguimientos_pendientes,
            "cancelados": seguimientos_cancelados,
            "tasa_completitud": (
                round((seguimientos_completados / total_seguimientos) * 100, 2)
                if total_seguimientos > 0 else 0
            )
        }