"""
Command Pattern - Comandos para operaciones de citas con auditoría
RNF-07: Auditoría completa de operaciones
"""

from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.services.appointment.appointment_service import AppointmentService
from app.services.appointment.appointment_facade import AppointmentFacade
from app.services.decorators import AuditDecorator
from app.schemas.appointment_schema import AppointmentCreate


class CreateAppointmentCommand:
    """
    Comando para crear una cita con auditoría automática
    """

    def __init__(
            self,
            db: Session,
            mascota_id: UUID,
            veterinario_id: UUID,
            servicio_id: UUID,
            fecha_hora: datetime,
            motivo: Optional[str] = None,
            usuario_id: Optional[UUID] = None
    ):
        self.db = db
        self.mascota_id = mascota_id
        self.veterinario_id = veterinario_id
        self.servicio_id = servicio_id
        self.fecha_hora = fecha_hora
        self.motivo = motivo
        self.usuario_id = usuario_id

    def execute(self):
        """Ejecuta el comando de creación de cita"""
        facade = AppointmentFacade(self.db)

        return facade.agendar_cita_completa(
            mascota_id=self.mascota_id,
            veterinario_id=self.veterinario_id,
            servicio_id=self.servicio_id,
            fecha_hora=self.fecha_hora,
            motivo=self.motivo,
            usuario_id=self.usuario_id
        )


class RescheduleAppointmentCommand:
    """
    Comando para reprogramar una cita con auditoría
    """

    def __init__(
            self,
            db: Session,
            appointment_id: UUID,
            nueva_fecha: datetime,
            usuario_id: Optional[UUID] = None
    ):
        self.db = db
        self.appointment_id = appointment_id
        self.nueva_fecha = nueva_fecha
        self.usuario_id = usuario_id

    def execute(self):
        """Ejecuta el comando de reprogramación"""
        facade = AppointmentFacade(self.db)

        return facade.reprogramar_cita_completa(
            appointment_id=self.appointment_id,
            nueva_fecha=self.nueva_fecha,
            usuario_id=self.usuario_id
        )


class CancelAppointmentCommand:
    """
    Comando para cancelar una cita con auditoría
    """

    def __init__(
            self,
            db: Session,
            appointment_id: UUID,
            motivo_cancelacion: str,
            usuario_id: Optional[UUID] = None
    ):
        self.db = db
        self.appointment_id = appointment_id
        self.motivo_cancelacion = motivo_cancelacion
        self.usuario_id = usuario_id

    def execute(self):
        """Ejecuta el comando de cancelación"""
        facade = AppointmentFacade(self.db)

        return facade.cancelar_cita_completa(
            appointment_id=self.appointment_id,
            usuario_id=self.usuario_id
        )


class ConfirmAppointmentCommand:
    """
    Comando para confirmar una cita
    """

    def __init__(
            self,
            db: Session,
            appointment_id: UUID,
            usuario_id: Optional[UUID] = None
    ):
        self.db = db
        self.appointment_id = appointment_id
        self.usuario_id = usuario_id

    def execute(self):
        """Ejecuta el comando de confirmación"""
        service = AppointmentService(self.db)

        cita = service.confirm_appointment(
            appointment_id=self.appointment_id,
            usuario_id=self.usuario_id
        )

        return {
            "cita": cita.to_dict(),
            "mensaje": "Cita confirmada exitosamente"
        }