"""
Schemas de Usuario - Validación con Pydantic
RF-01: Registro de usuarios
RF-02: Gestión de usuarios internos
CORRECCIÓN ARQUITECTURAL: Incluye documento para propietarios
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
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

    veterinario_encargado_id: Optional[UUID] = Field(
        None,
        description="ID del veterinario encargado (requerido para auxiliares)"
    )

    @field_validator('veterinario_encargado_id')
    @classmethod
    def validar_veterinario_encargado(cls, v, info):
        """
        Valida que si el rol es AUXILIAR, se proporcione un veterinario_encargado_id
        """
        rol = info.data.get('rol')

        # Si el rol es AUXILIAR, el veterinario_encargado_id es obligatorio
        if rol == UserRoleEnum.AUXILIAR and v is None:
            raise ValueError(
                "El campo 'veterinario_encargado_id' es obligatorio para usuarios con rol AUXILIAR"
            )

        # Si el rol NO es AUXILIAR, no debe tener veterinario_encargado_id
        if rol != UserRoleEnum.AUXILIAR and v is not None:
            raise ValueError(
                "El campo 'veterinario_encargado_id' solo aplica para usuarios con rol AUXILIAR"
            )

        return v


# ==================== SCHEMA AUXILIAR: INFO VETERINARIO ====================
class VeterinarioSimple(BaseModel):
    """
    Representación simplificada de un veterinario
    (usado en la respuesta de auxiliares)
    """
    id: UUID
    nombre: str
    correo: EmailStr

    class Config:
        from_attributes = True


# ==================== SCHEMA AUXILIAR: INFO AUXILIAR ====================
class AuxiliarSimple(BaseModel):
    """
    Representación simplificada de un auxiliar
    (usado en la respuesta de veterinarios)
    """
    id: UUID
    nombre: str
    correo: EmailStr
    activo: bool

    class Config:
        from_attributes = True

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

    # Solo para auxiliares
    veterinario_encargado: Optional[VeterinarioSimple] = Field(
        None,
        description="Información del veterinario encargado (solo para auxiliares)"
    )

    # Solo para veterinarios
    auxiliares_a_cargo: Optional[List[AuxiliarSimple]] = Field(
        None,
        description="Lista de auxiliares supervisados (solo para veterinarios)"
    )

    class Config:
        from_attributes = True


# ==================== SCHEMA DE ACTUALIZACIÓN ====================
class UserUpdate(BaseModel):
    """Esquema para actualizar datos de un usuario existente"""
    nombre: Optional[str] = Field(None, min_length=3, max_length=100)
    telefono: Optional[str] = Field(None, max_length=20)
    activo: Optional[bool] = None
    veterinario_encargado_id: Optional[UUID] = Field(
        None,
        description="ID del veterinario encargado (solo para auxiliares)"
    )

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