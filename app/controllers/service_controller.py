"""
Controlador de Servicios Ofrecidos
RF-09: Gestión de servicios (consultas, vacunas, cirugías, etc.)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.services.service_service import ServiceService
from app.schemas.service_schema import ServiceCreate, ServiceUpdate, ServiceResponse
from app.models.user import User
from app.security.dependencies import (
    get_current_active_user,
    require_staff,
    require_superadmin
)
from app.utils.responses import success_response

router = APIRouter()


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_service(
    service_data: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff)
):
    """
    Crea un nuevo servicio

    **Requiere:** Token JWT válido
    **Acceso:** Staff (Superadmin, Veterinario, Auxiliar)

    **RF-09:** Gestión de servicios ofrecidos
    """
    try:
        service_service = ServiceService(db)
        service = service_service.create_service(service_data, current_user.id)

        return success_response(
            data=service.to_dict(),
            message="Servicio creado exitosamente",
            status_code=status.HTTP_201_CREATED
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear servicio: {str(exc)}"
        )


@router.get("/", response_model=dict)
async def list_services(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    activo: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lista todos los servicios con filtros opcionales

    **Requiere:** Token JWT válido
    **Acceso:** Cualquier usuario autenticado

    **Parámetros:**
    - skip: Registros a omitir (paginación)
    - limit: Límite de registros (máx 100)
    - activo: Filtrar por estado activo/inactivo
    """
    try:
        service_service = ServiceService(db)
        services = service_service.get_all_services(skip, limit, activo)

        return success_response(
            data={
                "total": len(services),
                "servicios": [s.to_dict() for s in services]
            },
            message="Lista de servicios"
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener servicios: {str(exc)}"
        )


@router.get("/active", response_model=dict)
async def list_active_services(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lista solo servicios activos (para agendar citas)

    **Requiere:** Token JWT válido
    **Acceso:** Cualquier usuario autenticado
    """
    try:
        service_service = ServiceService(db)
        services = service_service.get_active_services(skip, limit)

        return success_response(
            data={
                "total": len(services),
                "servicios": [s.to_dict() for s in services]
            },
            message="Servicios activos disponibles"
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener servicios: {str(exc)}"
        )


@router.get("/{service_id}", response_model=dict)
async def get_service(
    service_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene un servicio por ID

    **Requiere:** Token JWT válido
    **Acceso:** Cualquier usuario autenticado
    """
    try:
        service_service = ServiceService(db)
        service = service_service.get_service_by_id(service_id)

        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Servicio no encontrado"
            )

        return success_response(
            data=service.to_dict(),
            message="Servicio encontrado"
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener servicio: {str(exc)}"
        )


@router.put("/{service_id}", response_model=dict)
async def update_service(
    service_id: UUID,
    service_data: ServiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff)
):
    """
    Actualiza un servicio

    **Requiere:** Token JWT válido
    **Acceso:** Staff (Superadmin, Veterinario, Auxiliar)
    """
    try:
        service_service = ServiceService(db)
        service = service_service.update_service(service_id, service_data)

        return success_response(
            data=service.to_dict(),
            message="Servicio actualizado exitosamente"
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
            detail=f"Error al actualizar servicio: {str(exc)}"
        )


@router.delete("/{service_id}", response_model=dict)
async def deactivate_service(
    service_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin)
):
    """
    Desactiva un servicio (borrado lógico)

    **Requiere:** Token JWT válido
    **Acceso:** Solo Superadmin

    **Nota:** Los servicios desactivados no aparecen disponibles para agendar citas
    """
    try:
        service_service = ServiceService(db)
        service = service_service.deactivate_service(service_id)

        return success_response(
            data=service.to_dict(),
            message="Servicio desactivado exitosamente"
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
            detail=f"Error al desactivar servicio: {str(exc)}"
        )


@router.get("/search/", response_model=dict)
async def search_services(
    q: str = Query(..., min_length=2, description="Término de búsqueda"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Busca servicios por nombre o descripción

    **Requiere:** Token JWT válido
    **Acceso:** Cualquier usuario autenticado

    **Búsqueda:** Case-insensitive en nombre y descripción
    """
    try:
        service_service = ServiceService(db)
        services = service_service.search_services(q, skip, limit)

        return success_response(
            data={
                "query": q,
                "total": len(services),
                "servicios": [s.to_dict() for s in services]
            },
            message=f"Resultados de búsqueda para '{q}'"
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en la búsqueda: {str(exc)}"
        )