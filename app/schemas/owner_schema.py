"""
Schemas de Propietario - Validación con Pydantic
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


# ==================== SCHEMA DE ENTRADA: CREAR PROPIETARIO ====================
class OwnerCreate(BaseModel):
    """
    Esquema de validación para la creación de un propietario.
    Define los campos requeridos y sus restricciones.
    """
    nombre: str = Field(..., min_length=3, max_length=120)  # Nombre del propietario (obligatorio)
    correo: EmailStr  # Correo electrónico con validación automática de formato
    documento: str = Field(..., min_length=3, max_length=50)  # Documento de identificación (obligatorio)
    telefono: Optional[str] = Field(None, max_length=20)  # Teléfono opcional


# ==================== SCHEMA DE SALIDA: RESPUESTA PROPIETARIO ====================
class OwnerResponse(BaseModel):
    """
    Esquema de respuesta que representa los datos de un propietario.
    Se usa al devolver información al cliente.
    """
    id: UUID  # Identificador único del propietario
    nombre: str
    correo: EmailStr
    documento: str
    telefono: Optional[str]
    activo: bool  # Estado del propietario (activo o no)
    fecha_creacion: datetime  # Fecha en la que se registró el propietario

    class Config:
        # Permite crear instancias del modelo a partir de objetos ORM (como los de SQLAlchemy)
        from_attributes = True
