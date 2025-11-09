"""
Schemas de Cita - Validación con Pydantic
RF-05: Gestión de citas
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone
from enum import Enum


class AppointmentStatusEnum(str, Enum):
    """Enumeración de estados para validación"""
    AGENDADA = "agendada"
    CONFIRMADA = "confirmada"
    EN_PROCESO = "en_proceso"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"
    CANCELADA_TARDIA = "cancelada_tardia"


class AppointmentCreate(BaseModel):
    """
    Schema para crear una cita
    Valida RF-05 y RN08-1 (anticipación mínima)
    """
    mascota_id: UUID
    veterinario_id: UUID
    servicio_id: UUID
    fecha_hora: datetime
    motivo: Optional[str] = Field(None, max_length=500)

    @field_validator('fecha_hora')
    @classmethod
    def validate_fecha_hora(cls, value):
        """
        RN08-1: Las citas deben programarse con al menos 4 horas de anticipación
        """
        from datetime import timedelta

        # Asegurarnos de que ambas fechas sean aware (con timezone)
        now = datetime.now(timezone.utc)

        # Si el valor viene sin timezone, asumimos UTC
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)

        min_advance = timedelta(hours=4)

        if value <= now + min_advance:
            raise ValueError(
                'La cita debe programarse con al menos 4 horas de anticipación'
            )

        return value


class AppointmentUpdate(BaseModel):
    """
    Schema para actualizar una cita (reprogramar)
    """
    fecha_hora: datetime
    motivo: Optional[str] = Field(None, max_length=500)

    @field_validator('fecha_hora')
    @classmethod
    def validate_fecha_hora(cls, value):
        """
        RN08-3: Reprogramaciones solo se permiten hasta 2 horas antes
        """
        from datetime import timedelta

        # Asegurarnos de que ambas fechas sean aware (con timezone)
        now = datetime.now(timezone.utc)

        # Si el valor viene sin timezone, asumimos UTC
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)

        min_advance = timedelta(hours=2)

        if value <= now + min_advance:
            raise ValueError(
                'La reprogramación debe hacerse con al menos 2 horas de anticipación'
            )

        return value


class AppointmentResponse(BaseModel):
    """Schema de respuesta de cita"""
    id: UUID
    mascota_id: UUID
    veterinario_id: UUID
    servicio_id: UUID
    fecha_hora: datetime
    estado: str
    motivo: Optional[str]
    cancelacion_tardia: bool
    notas: Optional[str]
    fecha_creacion: datetime

    class Config:
        from_attributes = True


class AppointmentListResponse(BaseModel):
    """Schema de respuesta de lista de citas con información relacionada"""
    id: UUID
    mascota_nombre: str
    veterinario_nombre: str
    servicio_nombre: str
    fecha_hora: datetime
    estado: str
    motivo: Optional[str]
    cancelacion_tardia: bool