"""
Schemas de Propietario - Validación con Pydantic
CORRECCIÓN ARQUITECTURAL: Incluye usuario_id en las respuestas
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


# ==================== SCHEMA DE ENTRADA: CREAR PROPIETARIO ====================
class OwnerCreate(BaseModel):
    """
    Esquema de validación para la creación de un propietario.


    Los propietarios se crean automáticamente al registrar un usuario
    con rol PROPIETARIO mediante POST /auth/register.

    Se mantiene por compatibilidad con código existente.
    """
    nombre: str = Field(..., min_length=3, max_length=120)
    correo: EmailStr
    documento: str = Field(..., min_length=3, max_length=50)
    telefono: Optional[str] = Field(None, max_length=20)


# ==================== SCHEMA DE SALIDA: RESPUESTA PROPIETARIO ====================
class OwnerResponse(BaseModel):
    """
    Esquema de respuesta que representa los datos de un propietario.

    Incluye usuario_id para mostrar la relación
    """
    id: UUID
    usuario_id: UUID
    nombre: str
    correo: EmailStr
    documento: str
    telefono: Optional[str]
    activo: bool
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# ==================== SCHEMA DE ACTUALIZACIÓN ====================
class OwnerUpdate(BaseModel):
    """
    Esquema para actualizar datos de un propietario existente.
    Todos los campos son opcionales.
    """
    nombre: Optional[str] = Field(None, min_length=3, max_length=120)
    telefono: Optional[str] = Field(None, max_length=20)
    documento: Optional[str] = Field(None, min_length=3, max_length=50)
    activo: Optional[bool] = None

    class Config:
        from_attributes = True