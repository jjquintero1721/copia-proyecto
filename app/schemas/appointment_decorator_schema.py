"""
Schemas para Decoradores de Citas
Validación con Pydantic
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


class RecordatorioConfig(BaseModel):
    """Schema para configuración de recordatorios"""
    horas_antes: int = Field(ge=1, le=168, description="Horas antes de la cita")
    activo: bool = Field(default=True, description="Recordatorio activo")


class RecordatorioCreate(BaseModel):
    """Schema para crear decorador de recordatorios"""
    recordatorios: List[RecordatorioConfig] = Field(
        min_items=1,
        description="Lista de recordatorios"
    )


class NotasEspecialesCreate(BaseModel):
    """Schema para crear decorador de notas especiales"""
    preparacion_cliente: Optional[str] = None
    instrucciones_veterinario: Optional[str] = None
    requisitos: List[str] = Field(default_factory=list)
    observaciones: Optional[str] = None


class PrioridadCreate(BaseModel):
    """Schema para crear decorador de prioridad"""
    nivel_prioridad: str = Field(
        pattern="^(alta|media|baja)$",
        description="Nivel de prioridad"
    )
    razon: str = Field(
        min_length=10,
        max_length=500,
        description="Razón de la prioridad"
    )


class AppointmentDecoratorResponse(BaseModel):
    """Schema de respuesta para decoradores"""
    id: UUID
    cita_id: UUID
    tipo_decorador: str
    configuracion: Dict[str, Any]
    activo: str
    fecha_creacion: datetime

    class Config:
        from_attributes = True