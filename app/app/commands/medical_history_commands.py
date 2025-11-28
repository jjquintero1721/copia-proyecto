"""
Comandos de Historia Clínica - Patrón Command para auditoría
RN10-2: Cada modificación registra fecha, hora y usuario
RNF-07: Auditoría
"""

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from app.models.consultation import Consultation
from app.models.audit_log import AuditLog
from app.services.medical_history.medical_history_service import MedicalHistoryService
from app.schemas.consultation_schema import ConsultationCreate, ConsultationUpdate


class Command(ABC):
    """Interfaz base para comandos (Command Pattern)"""

    @abstractmethod
    def execute(self) -> Any:
        """Ejecuta el comando"""
        pass

    @abstractmethod
    def _audit(self, descripcion: str) -> None:
        """Registra auditoría"""
        pass


class CreateConsultationCommand(Command):
    """
    Comando para crear una consulta
    Implementa Command Pattern con auditoría automática
    """

    def __init__(
        self,
        db: Session,
        consultation_data: ConsultationCreate,
        usuario_id: UUID
    ):
        self.db = db
        self.consultation_data = consultation_data
        self.usuario_id = usuario_id
        self.service = MedicalHistoryService(db)

    def execute(self) -> Consultation:
        """
        Ejecuta la creación de consulta con auditoría automática
        """
        # Crear consulta
        consultation = self.service.create_consultation(
            self.consultation_data,
            self.usuario_id
        )

        # Registrar auditoría
        self._audit(
            f"Creación de consulta en historia clínica {consultation.historia_clinica_id}"
        )

        return consultation

    def _audit(self, descripcion: str) -> None:
        """Registra la auditoría del comando"""
        audit_log = AuditLog(
            usuario_id=self.usuario_id,
            accion="CREAR_CONSULTA",
            descripcion=descripcion,
            fecha_hora=datetime.now(timezone.utc)
        )
        self.db.add(audit_log)
        self.db.commit()


class UpdateConsultationCommand(Command):
    """
    Comando para actualizar una consulta
    Implementa Command Pattern con auditoría y Memento
    """

    def __init__(
        self,
        db: Session,
        consultation_id: UUID,
        update_data: ConsultationUpdate,
        usuario_id: UUID
    ):
        self.db = db
        self.consultation_id = consultation_id
        self.update_data = update_data
        self.usuario_id = usuario_id
        self.service = MedicalHistoryService(db)

    def execute(self) -> Consultation:
        """
        Ejecuta la actualización con auditoría y memento automáticos
        """
        # Actualizar consulta (internamente crea memento)
        consultation = self.service.update_consultation(
            self.consultation_id,
            self.update_data,
            self.usuario_id
        )

        # Registrar auditoría
        self._audit(
            f"Actualización de consulta {consultation.id} - Versión {consultation.version}"
        )

        return consultation

    def _audit(self, descripcion: str) -> None:
        """Registra la auditoría del comando"""
        audit_log = AuditLog(
            usuario_id=self.usuario_id,
            accion="ACTUALIZAR_CONSULTA",
            descripcion=descripcion,
            fecha_hora=datetime.now(timezone.utc)
        )
        self.db.add(audit_log)
        self.db.commit()


class RestoreConsultationVersionCommand(Command):
    """
    Comando para restaurar una versión anterior de consulta
    Implementa Command Pattern con Memento Pattern
    """

    def __init__(
        self,
        db: Session,
        consultation_id: UUID,
        version: int,
        usuario_id: UUID
    ):
        self.db = db
        self.consultation_id = consultation_id
        self.version = version
        self.usuario_id = usuario_id
        self.service = MedicalHistoryService(db)

    def execute(self) -> Consultation:
        """
        Ejecuta la restauración de versión
        """
        # Restaurar versión
        consultation = self.service.restore_consultation_version(
            self.consultation_id,
            self.version,
            self.usuario_id
        )

        # Registrar auditoría
        self._audit(
            f"Restauración de consulta {consultation.id} a versión {self.version}"
        )

        return consultation

    def _audit(self, descripcion: str) -> None:
        """Registra la auditoría del comando"""
        audit_log = AuditLog(
            usuario_id=self.usuario_id,
            accion="RESTAURAR_VERSION_CONSULTA",
            descripcion=descripcion,
            fecha_hora=datetime.now(timezone.utc)
        )
        self.db.add(audit_log)
        self.db.commit()