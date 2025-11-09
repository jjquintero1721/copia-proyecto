"""
Schemas de Servicio - Validación con Pydantic
RF-09: Gestión de servicios ofrecidos
"""

from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class ServiceCreate(BaseModel):
    """Schema para crear un servicio"""
    nombre: str = Field(..., min_length=3, max_length=150)
    descripcion: Optional[str] = Field(None, max_length=500)
    duracion_minutos: int = Field(..., gt=0, le=480)  # Máximo 8 horas
    costo: float = Field(..., ge=0)


class ServiceUpdate(BaseModel):
    """Schema para actualizar un servicio"""
    nombre: Optional[str] = Field(None, min_length=3, max_length=150)
    descripcion: Optional[str] = Field(None, max_length=500)
    duracion_minutos: Optional[int] = Field(None, gt=0, le=480)
    costo: Optional[float] = Field(None, ge=0)
    activo: Optional[bool] = None


class ServiceResponse(BaseModel):
    """Schema de respuesta de servicio"""
    id: UUID
    nombre: str
    descripcion: Optional[str]
    duracion_minutos: int
    costo: float
    activo: bool
    fecha_creacion: datetime

    class Config:
        from_attributes = True