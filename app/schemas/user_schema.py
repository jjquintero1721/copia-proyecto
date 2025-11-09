"""
Schemas de Usuario - Validación con Pydantic
Define la estructura y validación de datos de entrada/salida
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRoleEnum(str, Enum):
    """Enumeración de roles para validación"""
    SUPERADMIN = "superadmin"
    VETERINARIO = "veterinario"
    AUXILIAR = "auxiliar"
    PROPIETARIO = "propietario"


class UserCreate(BaseModel):
    """Schema para crear un usuario"""
    nombre: str = Field(..., min_length=3, max_length=100)
    correo: EmailStr
    telefono: Optional[str] = Field(None, max_length=20)
    contrasena: str = Field(..., min_length=8, max_length=50)
    rol: UserRoleEnum

    @field_validator('telefono')
    @classmethod
    def validate_telefono(cls, value):
        if value and not value.replace('+', '').replace(' ', '').replace('-', '').isdigit():
            raise ValueError('El teléfono solo debe contener números y caracteres +, -, espacio')
        return value

    @field_validator('contrasena')
    @classmethod
    def validate_contrasena(cls, value):
        if len(value) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        if not any(char.isdigit() for char in value):
            raise ValueError('La contraseña debe contener al menos un número')
        if not any(char.isupper() for char in value):
            raise ValueError('La contraseña debe contener al menos una mayúscula')
        return value


class UserUpdate(BaseModel):
    """Schema para actualizar un usuario"""
    nombre: Optional[str] = Field(None, min_length=3, max_length=100)
    telefono: Optional[str] = Field(None, max_length=20)
    activo: Optional[bool] = None


class UserChangePassword(BaseModel):
    """Schema para cambiar contraseña"""
    contrasena_actual: str
    contrasena_nueva: str = Field(..., min_length=8, max_length=50)

    @field_validator('contrasena_nueva')
    @classmethod
    def validate_contrasena_nueva(cls, value):
        if len(value) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        if not any(char.isdigit() for char in value):
            raise ValueError('La contraseña debe contener al menos un número')
        if not any(char.isupper() for char in value):
            raise ValueError('La contraseña debe contener al menos una mayúscula')
        return value


class UserResponse(BaseModel):
    """Schema de respuesta de usuario"""
    id: str
    nombre: str
    correo: str
    telefono: Optional[str]
    rol: str
    activo: bool
    fecha_creacion: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """Schema para login"""
    correo: EmailStr
    contrasena: str


class LoginResponse(BaseModel):
    """Schema de respuesta de login"""
    access_token: str
    token_type: str = "bearer"
    usuario: UserResponse