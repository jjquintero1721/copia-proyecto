"""
Schemas de Consulta - Validaciones con Pydantic
RF-07: Gestión de historias clínicas
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone


class ConsultationBase(BaseModel):
    """Schema base de consulta"""
    motivo: str = Field(..., min_length=5, max_length=300, description="Motivo de la consulta")
    anamnesis: Optional[str] = Field(None, description="Historia clínica del paciente")
    signos_vitales: Optional[str] = Field(None, description="Signos vitales (FC, FR, Temp, etc.)")
    diagnostico: str = Field(..., min_length=10, description="Diagnóstico médico")
    tratamiento: str = Field(..., min_length=5, description="Tratamiento aplicado")
    vacunas: Optional[str] = Field(None, description="Vacunas administradas")
    observaciones: Optional[str] = Field(None, description="Observaciones adicionales")


class ConsultationCreate(ConsultationBase):
    """Schema para crear una consulta"""
    historia_clinica_id: UUID = Field(..., description="ID de la historia clínica")
    veterinario_id: UUID = Field(..., description="ID del veterinario que realiza la consulta")
    cita_id: Optional[UUID] = Field(None, description="ID de la cita relacionada (opcional)")
    fecha_hora: Optional[datetime] = Field(None, description="Fecha y hora de la consulta (default: ahora)")

    @field_validator('fecha_hora')
    @classmethod
    def validate_fecha_hora(cls, v):
        """Validar que la fecha no sea futura"""
        if v and v > datetime.now(timezone.utc):
            raise ValueError("La fecha de consulta no puede ser futura")
        return v


class ConsultationUpdate(BaseModel):
    """Schema para actualizar una consulta"""
    motivo: Optional[str] = Field(None, min_length=5, max_length=300)
    anamnesis: Optional[str] = None
    signos_vitales: Optional[str] = None
    diagnostico: Optional[str] = Field(None, min_length=10)
    tratamiento: Optional[str] = Field(None, min_length=5)
    vacunas: Optional[str] = None
    observaciones: Optional[str] = None
    descripcion_cambio: Optional[str] = Field(None, max_length=500, description="Descripción del cambio realizado")


class ConsultationResponse(ConsultationBase):
    """Schema de respuesta de consulta"""
    id: UUID
    historia_clinica_id: UUID
    veterinario_id: UUID
    cita_id: Optional[UUID]
    fecha_hora: datetime
    version: int
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime]
    creado_por: UUID
    actualizado_por: Optional[UUID]

    class Config:
        from_attributes = True


class MedicalHistoryResponse(BaseModel):
    """Schema de respuesta de historia clínica completa"""
    id: UUID
    mascota_id: UUID
    numero: str
    notas: Optional[str]
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime]
    total_consultas: int
    consultas: Optional[list[ConsultationResponse]] = None

    class Config:
        from_attributes = True