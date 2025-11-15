"""
Schemas de Seguimiento - Validaciones con Pydantic
RF-11: Seguimiento de pacientes
"""

from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone


class FollowUpCreate(BaseModel):
    """
    Schema para crear un seguimiento desde una consulta

    RF-11: Permite programar seguimientos posteriores a consultas o tratamientos
    """
    consulta_origen_id: UUID = Field(
        ...,
        description="ID de la consulta original que requiere seguimiento"
    )
    veterinario_id: UUID = Field(
        ...,
        description="ID del veterinario asignado al seguimiento"
    )
    servicio_id: UUID = Field(
        ...,
        description="ID del servicio para el seguimiento"
    )
    fecha_hora_seguimiento: datetime = Field(
        ...,
        description="Fecha y hora programada para el seguimiento"
    )
    motivo_seguimiento: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Motivo o razón del seguimiento"
    )
    dias_recomendados: Optional[int] = Field(
        None,
        ge=1,
        le=365,
        description="Días recomendados para el seguimiento desde la consulta original"
    )
    notas: Optional[str] = Field(
        None,
        max_length=1000,
        description="Notas adicionales sobre el seguimiento"
    )


class FollowUpResponse(BaseModel):
    """
    Schema de respuesta de seguimiento creado
    """
    cita_seguimiento_id: UUID = Field(
        ...,
        description="ID de la cita de seguimiento creada"
    )
    consulta_origen_id: UUID = Field(
        ...,
        description="ID de la consulta original"
    )
    mascota_id: UUID = Field(
        ...,
        description="ID de la mascota"
    )
    veterinario_id: UUID = Field(
        ...,
        description="ID del veterinario asignado"
    )
    servicio_id: UUID = Field(
        ...,
        description="ID del servicio"
    )
    fecha_hora_seguimiento: datetime = Field(
        ...,
        description="Fecha y hora del seguimiento"
    )
    motivo_seguimiento: str = Field(
        ...,
        description="Motivo del seguimiento"
    )
    estado: str = Field(
        ...,
        description="Estado de la cita de seguimiento"
    )
    dias_recomendados: Optional[int] = None
    notas: Optional[str] = None
    fecha_creacion: datetime

    class Config:
        from_attributes = True


class FollowUpListResponse(BaseModel):
    """
    Schema para listar seguimientos de una consulta
    """
    consulta_id: UUID
    total_seguimientos: int
    seguimientos: list[FollowUpResponse]

    class Config:
        from_attributes = True


class FollowUpCompletionCreate(BaseModel):
    """
    Schema para registrar la consulta de seguimiento completada

    RF-11: El seguimiento se vincula automáticamente al historial clínico
    """
    cita_seguimiento_id: UUID = Field(
        ...,
        description="ID de la cita de seguimiento"
    )
    motivo: str = Field(
        ...,
        min_length=5,
        max_length=300,
        description="Motivo de la consulta de seguimiento"
    )
    anamnesis: Optional[str] = Field(
        None,
        description="Historia actualizada del paciente"
    )
    signos_vitales: Optional[str] = Field(
        None,
        description="Signos vitales registrados"
    )
    diagnostico: str = Field(
        ...,
        min_length=10,
        description="Diagnóstico de la consulta de seguimiento"
    )
    tratamiento: str = Field(
        ...,
        min_length=5,
        description="Tratamiento aplicado o actualizado"
    )
    evolucion: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Evolución del paciente respecto a la consulta original"
    )
    vacunas: Optional[str] = Field(
        None,
        description="Vacunas administradas"
    )
    observaciones: Optional[str] = Field(
        None,
        description="Observaciones adicionales"
    )
    requiere_nuevo_seguimiento: bool = Field(
        default=False,
        description="Indica si se requiere un nuevo seguimiento"
    )