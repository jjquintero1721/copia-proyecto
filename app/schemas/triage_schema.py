"""
Schemas de Triage - Validaciones con Pydantic
RF-08: Triage (clasificación de prioridad)
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum


class TriagePriorityEnum(str, Enum):
    """Enumeración de prioridades para validación"""
    URGENTE = "urgente"
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


class TriageGeneralStateEnum(str, Enum):
    """Enumeración de estados generales para validación"""
    CRITICO = "critico"
    DECAIDO = "decaido"
    ALERTA = "alerta"
    ESTABLE = "estable"


class DolorEnum(str, Enum):
    """Enumeración de niveles de dolor"""
    AUSENTE = "ausente"
    LEVE = "leve"
    MODERADO = "moderado"
    SEVERO = "severo"


class TriageCreate(BaseModel):
    """
    Schema para crear un registro de triage
    Valida RF-08 y reglas OCL del DSL
    """
    cita_id: Optional[UUID] = Field(None, description="ID de la cita asociada (opcional)")
    mascota_id: UUID = Field(..., description="ID de la mascota")
    estado_general: TriageGeneralStateEnum = Field(..., description="Estado general del paciente")
    fc: int = Field(..., gt=0, le=300, description="Frecuencia cardíaca (latidos/min)")
    fr: int = Field(..., gt=0, le=200, description="Frecuencia respiratoria (respiraciones/min)")
    temperatura: float = Field(..., gt=35.0, lt=42.0, description="Temperatura en °C")
    dolor: DolorEnum = Field(..., description="Nivel de dolor")
    sangrado: str = Field(..., pattern="^(Si|No)$", description="Presencia de sangrado (Si/No)")
    shock: str = Field(..., pattern="^(Si|No)$", description="Presencia de shock (Si/No)")
    observaciones: Optional[str] = Field(None, max_length=1000, description="Observaciones adicionales")

    @field_validator('temperatura')
    @classmethod
    def validate_temperatura(cls, value):
        """
        Regla OCL: La temperatura debe estar en rango válido (35-42°C para animales)
        """
        if value < 35.0 or value >= 42.0:
            raise ValueError('La temperatura debe estar entre 35.0 y 42.0 grados Celsius')
        return value

    @field_validator('fc')
    @classmethod
    def validate_fc(cls, value):
        """Validar que la frecuencia cardíaca sea positiva"""
        if value <= 0:
            raise ValueError('La frecuencia cardíaca debe ser mayor a 0')
        return value

    @field_validator('fr')
    @classmethod
    def validate_fr(cls, value):
        """
        Regla OCL: La frecuencia respiratoria debe ser positiva
        """
        if value <= 0:
            raise ValueError('La frecuencia respiratoria debe ser mayor a 0')
        return value


class TriageUpdate(BaseModel):
    """Schema para actualizar un triage (raro, pero posible)"""
    estado_general: Optional[TriageGeneralStateEnum] = None
    fc: Optional[int] = Field(None, gt=0, le=300)
    fr: Optional[int] = Field(None, gt=0, le=200)
    temperatura: Optional[float] = Field(None, gt=35.0, lt=42.0)
    dolor: Optional[DolorEnum] = None
    sangrado: Optional[str] = Field(None, pattern="^(Si|No)$")
    shock: Optional[str] = Field(None, pattern="^(Si|No)$")
    observaciones: Optional[str] = Field(None, max_length=1000)


class TriageResponse(BaseModel):
    """Schema de respuesta de triage"""
    id: UUID
    cita_id: Optional[UUID]
    mascota_id: UUID
    usuario_id: UUID
    estado_general: str
    fc: int
    fr: int
    temperatura: float
    dolor: str
    sangrado: str
    shock: str
    prioridad: str
    observaciones: Optional[str]
    fecha_creacion: datetime

    class Config:
        from_attributes = True