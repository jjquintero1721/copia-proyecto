"""
Schemas de Usuario - Validación con Pydantic
RF-01: Registro de usuarios
RF-02: Gestión de usuarios internos
CORRECCIÓN ARQUITECTURAL: Incluye documento para propietarios
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum


# ==================== ENUM DE ROLES ====================
class UserRoleEnum(str, Enum):
    """Enumeración de roles para validación de entrada"""
    SUPERADMIN = "superadmin"
    VETERINARIO = "veterinario"
    AUXILIAR = "auxiliar"
    PROPIETARIO = "propietario"


# ==================== SCHEMA DE ENTRADA: CREAR USUARIO ====================
class UserCreate(BaseModel):
    """
    Esquema de validación para la creación de un usuario.

    Incluye documento opcional
    - Requerido cuando rol = PROPIETARIO
    - Opcional para otros roles
    """
    nombre: str = Field(..., min_length=3, max_length=100)
    correo: EmailStr
    telefono: Optional[str] = Field(None, max_length=20)
    contrasena: str = Field(..., min_length=8, max_length=50)
    rol: UserRoleEnum = Field(default=UserRoleEnum.PROPIETARIO)

    # documento para propietarios
    documento: Optional[str] = Field(
        None,
        min_length=3,
        max_length=50,
        description="Documento de identidad (requerido para propietarios)"
    )


# ==================== SCHEMA DE SALIDA: RESPUESTA USUARIO ====================
class UserResponse(BaseModel):
    """
    Esquema de respuesta que representa los datos de un usuario.
    Incluye propietario_id y documento si aplica
    """
    id: UUID
    nombre: str
    correo: EmailStr
    telefono: Optional[str]
    rol: str
    activo: bool
    fecha_creacion: datetime

    # Campos adicionales si es propietario
    propietario_id: Optional[UUID] = None
    documento: Optional[str] = None

    class Config:
        from_attributes = True


# ==================== SCHEMA DE ACTUALIZACIÓN ====================
class UserUpdate(BaseModel):
    """Esquema para actualizar datos de un usuario existente"""
    nombre: Optional[str] = Field(None, min_length=3, max_length=100)
    telefono: Optional[str] = Field(None, max_length=20)
    activo: Optional[bool] = None


# ==================== SCHEMA DE CAMBIO DE CONTRASEÑA ====================
class UserChangePassword(BaseModel):
    """Esquema para cambiar la contraseña de un usuario"""
    contrasena_actual: str = Field(..., min_length=8)
    contrasena_nueva: str = Field(..., min_length=8, max_length=50)


# ==================== SCHEMA DE LOGIN ====================
class LoginRequest(BaseModel):
    """Esquema para solicitud de login"""
    correo: EmailStr
    contrasena: str


class LoginResponse(BaseModel):
    """Esquema de respuesta exitosa de login"""
    access_token: str
    token_type: str = "bearer"
    usuario: UserResponse


# ==================== SCHEMA DE TOKEN ====================
class TokenData(BaseModel):
    """Esquema para datos del token JWT"""
    correo: Optional[str] = None
    user_id: Optional[str] = None
    rol: Optional[str] = None