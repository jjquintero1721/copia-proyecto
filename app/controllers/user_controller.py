"""
Controlador de Usuarios
Endpoints CRUD con control de permisos basado en roles
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.services.user_service import UserService
from app.schemas.user_schema import UserResponse, UserUpdate, UserChangePassword
from app.models.user import User
from app.security.dependencies import (
    get_current_active_user,
    require_superadmin,
    require_staff,
    verify_owner_or_staff
)
from app.utils.responses import success_response, error_response

router = APIRouter()


@router.get("/me", response_model=dict)
async def get_current_user_info(
        current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene la información del usuario autenticado

    **Requiere:** Token JWT válido
    **Acceso:** Cualquier usuario autenticado
    """
    return success_response(
        data=current_user.to_dict(),
        message="Información del usuario"
    )


@router.get("/", response_model=dict)
async def list_users(
        skip: int = Query(0, ge=0, description="Número de registros a omitir"),
        limit: int = Query(100, ge=1, le=100, description="Número máximo de registros"),
        activo: Optional[bool] = Query(None, description="Filtrar por estado activo/inactivo"),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """
    Lista todos los usuarios con paginación

    **Requiere:** Token JWT válido
    **Acceso:** Superadmin, Veterinario, Auxiliar (RN03, RN04, RN05)

    **Parámetros:**
    - skip: Paginación - registros a omitir
    - limit: Paginación - máximo de registros (max 100)
    - activo: Filtrar por estado (true/false/null para todos)
    """
    try:
        service = UserService(db)
        users = service.get_all_users(skip, limit, activo)

        return success_response(
            data={
                "total": len(users),
                "skip": skip,
                "limit": limit,
                "usuarios": [user.to_dict() for user in users]
            },
            message="Lista de usuarios"
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener usuarios: {str(exc)}"
        )


@router.get("/search", response_model=dict)
async def search_users(
        q: str = Query(..., min_length=2, description="Término de búsqueda"),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """
    Busca usuarios por nombre o correo

    **Requiere:** Token JWT válido
    **Acceso:** Staff (Superadmin, Veterinario, Auxiliar)

    **Búsqueda:** Case-insensitive en nombre y correo
    """
    try:
        service = UserService(db)
        users = service.search_users(q, skip, limit)

        return success_response(
            data={
                "query": q,
                "total": len(users),
                "usuarios": [user.to_dict() for user in users]
            },
            message=f"Resultados de búsqueda para '{q}'"
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en la búsqueda: {str(exc)}"
        )


@router.get("/rol/{rol}", response_model=dict)
async def get_users_by_role(
        rol: str,
        activo: bool = Query(True, description="Filtrar solo usuarios activos"),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """
    Obtiene usuarios por rol

    **Requiere:** Token JWT válido
    **Acceso:** Staff (Superadmin, Veterinario, Auxiliar)

    **Roles válidos:**
    - superadmin
    - veterinario
    - auxiliar
    - propietario
    """
    try:
        service = UserService(db)
        users = service.get_users_by_rol(rol, activo)

        return success_response(
            data={
                "rol": rol,
                "total": len(users),
                "usuarios": [user.to_dict() for user in users]
            },
            message=f"Usuarios con rol '{rol}'"
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener usuarios por rol: {str(exc)}"
        )


@router.get("/{user_id}", response_model=dict)
async def get_user(
        user_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene un usuario por ID

    **Requiere:** Token JWT válido
    **Acceso:**
    - Staff: Puede ver cualquier usuario
    - Propietario: Solo puede ver su propia información
    """
    try:
        # Verificar permisos: staff puede ver cualquier usuario, propietario solo el suyo
        verify_owner_or_staff(user_id, current_user)

        service = UserService(db)
        user = service.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )

        return success_response(
            data=user.to_dict(),
            message="Usuario encontrado"
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener usuario: {str(exc)}"
        )


@router.put("/{user_id}", response_model=dict)
async def update_user(
        user_id: UUID,
        user_data: UserUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Actualiza un usuario

    **Requiere:** Token JWT válido
    **Acceso:**
    - Superadmin: Puede actualizar cualquier usuario (incluso campo activo)
    - Usuario: Puede actualizar su propia información (nombre, teléfono)

    **Campos actualizables:**
    - nombre: Nombre completo
    - telefono: Número de teléfono
    - activo: Solo superadmin puede modificarlo
    """
    try:
        # Verificar permisos
        verify_owner_or_staff(user_id, current_user)

        # Solo superadmin puede cambiar el campo activo
        if user_data.activo is not None and current_user.rol.value != "superadmin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo superadmin puede activar/desactivar usuarios"
            )

        service = UserService(db)
        user = service.update_user(user_id, user_data)

        return success_response(
            data=user.to_dict(),
            message="Usuario actualizado exitosamente"
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar usuario: {str(exc)}"
        )


@router.post("/{user_id}/change-password", response_model=dict)
async def change_password(
        user_id: UUID,
        password_data: UserChangePassword,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Cambia la contraseña de un usuario

    **Requiere:** Token JWT válido
    **Acceso:** El propio usuario

    **Validaciones:**
    - Contraseña actual correcta
    - Nueva contraseña: mínimo 8 caracteres, 1 número, 1 mayúscula
    """
    try:
        # Solo el usuario puede cambiar su propia contraseña
        if str(current_user.id) != str(user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puedes cambiar tu propia contraseña"
            )

        service = UserService(db)
        user = service.change_password(user_id, password_data)

        return success_response(
            data=user.to_dict(),
            message="Contraseña actualizada exitosamente"
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cambiar contraseña: {str(exc)}"
        )


@router.delete("/{user_id}", response_model=dict)
async def deactivate_user(
        user_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_superadmin)
):
    """
    Desactiva un usuario (borrado lógico)

    **Requiere:** Token JWT válido
    **Acceso:** Solo Superadmin (RN03)

    **Nota:** No se elimina físicamente, solo se marca como inactivo
    """
    try:
        # Evitar que un superadmin se desactive a sí mismo
        if str(current_user.id) == str(user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes desactivarte a ti mismo"
            )

        service = UserService(db)
        user = service.deactivate_user(user_id)

        return success_response(
            data=user.to_dict(),
            message="Usuario desactivado exitosamente"
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al desactivar usuario: {str(exc)}"
        )