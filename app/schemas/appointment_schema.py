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


class AppointmentPrivateResponse(BaseModel):
    """
    Schema para mostrar citas de forma anónima a propietarios
    Oculta información sensible de otros propietarios por privacidad

    Relaciona con: RF-07, RN10, RNF-07 (privacidad de datos)
    """
    id: UUID
    fecha_hora: datetime
    fecha_fin: Optional[datetime] = None
    estado: str

    # Información del veterinario (visible para todos)
    veterinario_id: Optional[UUID] = None
    veterinario_nombre: Optional[str] = None

    # Información del servicio (visible para todos)
    servicio_id: Optional[UUID] = None
    servicio_nombre: Optional[str] = None

    # Indicador si es cita propia (para UI)
    es_mi_cita: bool = False

    # Información anónima cuando NO es mi cita
    titulo_anonimo: Optional[str] = "Cita agendada"

    # Información completa solo si es MI cita
    mascota_nombre: Optional[str] = None
    propietario_nombre: Optional[str] = None
    motivo: Optional[str] = None

    class Config:
        from_attributes = True


def convert_to_private_response(
        appointment: "Appointment",
        current_user_id: UUID
) -> AppointmentPrivateResponse:
    """
    Convierte una cita a formato privado según el propietario actual

    Args:
        appointment: Cita completa
        current_user_id: ID del usuario actual (propietario)

    Returns:
        AppointmentPrivateResponse con información filtrada
    """
    # Verificar si la cita pertenece al propietario actual
    es_mi_cita = (
            appointment.mascota and
            appointment.mascota.propietario_id == current_user_id
    )

    return AppointmentPrivateResponse(
        id=appointment.id,
        fecha_hora=appointment.fecha_hora,
        fecha_fin=appointment.fecha_fin,
        estado=appointment.estado.value if hasattr(appointment.estado, 'value') else appointment.estado,
        veterinario_id=appointment.veterinario_id,
        veterinario_nombre=appointment.veterinario.nombre if appointment.veterinario else None,
        servicio_id=appointment.servicio_id,
        servicio_nombre=appointment.servicio.nombre if appointment.servicio else None,
        es_mi_cita=es_mi_cita,
        titulo_anonimo="Cita agendada" if not es_mi_cita else None,
        # Solo incluir detalles si es MI cita
        mascota_nombre=appointment.mascota.nombre if es_mi_cita and appointment.mascota else None,
        propietario_nombre=appointment.mascota.propietario.nombre if es_mi_cita and appointment.mascota and appointment.mascota.propietario else None,
        motivo=appointment.motivo if es_mi_cita else None
    )