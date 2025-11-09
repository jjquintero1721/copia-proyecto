"""
Dependencies de Seguridad - Autenticación y Autorización
Implementa Patrón Proxy para control de acceso
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.security.auth import decode_access_token
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository

# Esquema de seguridad Bearer Token
security = HTTPBearer()


def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
) -> User:
    """
    Dependency para obtener el usuario actual desde el token JWT
    """
    token = credentials.credentials

    # Decodificar token
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Obtener correo del payload
    correo: str = payload.get("sub")
    if not correo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Buscar usuario en BD
    repository = UserRepository(db)
    user = repository.get_by_correo(correo)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado"
        )

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency para verificar que el usuario esté activo
    """
    if not current_user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    return current_user


# ==================== PATRÓN PROXY - CONTROL DE ACCESO ====================

class RoleChecker:
    """
    Proxy Pattern - Control de acceso basado en roles
    RN03, RN04, RN05: Permisos según roles
    """

    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        """
        Verifica que el usuario tenga uno de los roles permitidos
        """
        if current_user.rol.value not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Roles permitidos: {', '.join(self.allowed_roles)}"
            )
        return current_user


# ==================== PERMISOS POR ROL ====================

# Solo superadmin
require_superadmin = RoleChecker([UserRole.SUPERADMIN.value])

# Superadmin o veterinario
require_admin_or_vet = RoleChecker([
    UserRole.SUPERADMIN.value,
    UserRole.VETERINARIO.value
])

# Superadmin, veterinario o auxiliar (personal de la clínica)
require_staff = RoleChecker([
    UserRole.SUPERADMIN.value,
    UserRole.VETERINARIO.value,
    UserRole.AUXILIAR.value
])

# Cualquier rol autenticado
require_authenticated = Depends(get_current_active_user)


# ==================== VERIFICACIÓN DE PROPIETARIO ====================

def verify_owner_or_staff(
        user_id: UUID,
        current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Verifica que el usuario sea el propietario del recurso o sea staff
    Útil para endpoints donde el propietario puede ver solo sus datos
    """
    # Si es staff, tiene acceso total
    if current_user.rol.value in [
        UserRole.SUPERADMIN.value,
        UserRole.VETERINARIO.value,
        UserRole.AUXILIAR.value
    ]:
        return current_user

    # Si es propietario, solo puede acceder a sus propios datos
    if str(current_user.id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para acceder a este recurso"
        )

    return current_user