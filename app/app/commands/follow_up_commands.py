"""
Command Pattern - Comandos para operaciones de seguimiento con auditoría
RF-11: Seguimiento de pacientes
RNF-07: Auditoría completa de operaciones
"""

from sqlalchemy.orm import Session
from typing import Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from abc import ABC, abstractmethod

from app.models.audit_log import AuditLog
from app.services.follow_up.follow_up_service import FollowUpService
from app.schemas.follow_up_schema import FollowUpCreate, FollowUpCompletionCreate


class Command(ABC):
    """Interfaz base para comandos con auditoría"""

    @abstractmethod
    def execute(self) -> Any:
        """Ejecuta el comando"""

    @abstractmethod
    def _audit(self, descripcion: str) -> None:
        """Registra auditoría del comando"""


class CreateFollowUpCommand(Command):
    """
    Comando para crear un seguimiento con auditoría automática

    RF-11: Programación de seguimientos
    RNF-07: Registro de auditoría
    """

    def __init__(
            self,
            db: Session,
            follow_up_data: FollowUpCreate,
            usuario_id: UUID
    ):
        self.db = db
        self.follow_up_data = follow_up_data
        self.usuario_id = usuario_id
        self.service = FollowUpService(db)

    def execute(self) -> Dict[str, Any]:
        """
        Ejecuta la creación del seguimiento con auditoría automática

        Returns:
            Dict con información de la cita de seguimiento creada
        """
        # Crear seguimiento
        follow_up_result = self.service.create_follow_up_appointment(
            self.follow_up_data,
            self.usuario_id
        )

        # Registrar auditoría
        self._audit(
            f"Creación de seguimiento para consulta {self.follow_up_data.consulta_origen_id}. "
            f"Cita programada para {self.follow_up_data.fecha_hora_seguimiento.isoformat()}"
        )

        return follow_up_result

    def _audit(self, descripcion: str) -> None:
        """
        Registra la auditoría del comando

        RNF-07: Toda acción importante debe registrarse con fecha, hora y usuario
        """
        audit_log = AuditLog(
            usuario_id=self.usuario_id,
            accion="CREAR_SEGUIMIENTO",
            descripcion=descripcion,
            fecha_hora=datetime.now(timezone.utc)
        )
        self.db.add(audit_log)
        self.db.commit()


class CompleteFollowUpCommand(Command):
    """
    Comando para completar un seguimiento con auditoría automática

    RF-11: Registro de consulta de seguimiento vinculada al historial
    RNF-07: Registro de auditoría
    """

    def __init__(
            self,
            db: Session,
            completion_data: FollowUpCompletionCreate,
            veterinario_id: UUID
    ):
        self.db = db
        self.completion_data = completion_data
        self.veterinario_id = veterinario_id
        self.service = FollowUpService(db)

    def execute(self):
        """
        Ejecuta la completación del seguimiento con auditoría automática

        Returns:
            Consultation creada para el seguimiento
        """
        # Completar seguimiento
        consultation = self.service.complete_follow_up(
            self.completion_data,
            self.veterinario_id
        )

        # Registrar auditoría
        self._audit(
            f"Seguimiento completado. Consulta {consultation.id} creada y vinculada "
            f"al historial clínico {consultation.historia_clinica_id}"
        )

        return consultation

    def _audit(self, descripcion: str) -> None:
        """
        Registra la auditoría del comando

        RNF-07: Toda acción importante debe registrarse con fecha, hora y usuario
        """
        audit_log = AuditLog(
            usuario_id=self.veterinario_id,
            accion="COMPLETAR_SEGUIMIENTO",
            descripcion=descripcion,
            fecha_hora=datetime.now(timezone.utc)
        )
        self.db.add(audit_log)
        self.db.commit()


class CancelFollowUpCommand(Command):
    """
    Comando para cancelar un seguimiento con auditoría automática
    """

    def __init__(
            self,
            db: Session,
            cita_seguimiento_id: UUID,
            usuario_id: UUID,
            motivo_cancelacion: str
    ):
        self.db = db
        self.cita_seguimiento_id = cita_seguimiento_id
        self.usuario_id = usuario_id
        self.motivo_cancelacion = motivo_cancelacion

    def execute(self):
        """
        Ejecuta la cancelación del seguimiento

        Returns:
            Appointment actualizada
        """
        # Usar el servicio de citas para cancelar
        from app.services.appointment.appointment_service import AppointmentService
        appointment_service = AppointmentService(self.db)

        appointment = appointment_service.cancel_appointment(
            self.cita_seguimiento_id,
            self.usuario_id
        )

        # Registrar auditoría específica de cancelación de seguimiento
        self._audit(
            f"Seguimiento cancelado. Cita {self.cita_seguimiento_id}. "
            f"Motivo: {self.motivo_cancelacion}"
        )

        return appointment

    def _audit(self, descripcion: str) -> None:
        """Registra la auditoría del comando"""
        audit_log = AuditLog(
            usuario_id=self.usuario_id,
            accion="CANCELAR_SEGUIMIENTO",
            descripcion=descripcion,
            fecha_hora=datetime.now(timezone.utc)
        )
        self.db.add(audit_log)
        self.db.commit()