"""
Controlador de Triage
RF-08: Triage (clasificación de prioridad)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.services.triage_service import TriageService
from app.schemas.triage_schema import (
    TriageCreate,
    TriageUpdate,
    TriageResponse,
    TriagePriorityEnum
)
from app.models.user import User
from app.security.dependencies import (
    get_current_active_user,
    require_staff
)
from app.utils.responses import success_response

router = APIRouter()


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_triage(
        triage_data: TriageCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """
    Registra un nuevo triage (clasificación de prioridad)

    **Requiere:** Token JWT válido
    **Acceso:** Staff (Superadmin, Veterinario, Auxiliar)

    **RF-08:** Triage (clasificación de prioridad)

    **Validaciones:**
    - Mascota debe existir
    - Si se asocia a cita, esta debe existir
    - Prioridad se calcula automáticamente usando Chain of Responsibility
    - Para prioridad URGENTE, observaciones deben tener mínimo 10 caracteres

    **Chain of Responsibility:**
    1. EstadoCriticoHandler: signos vitales críticos → URGENTE
    2. SignosDolorHandler: dolor severo, sangrado, shock → URGENTE
    3. SignosVitalesHandler: signos anormales → ALTA/MEDIA
    4. EstadoEstableHandler: sin alertas → BAJA
    """
    try:
        service = TriageService(db)
        triage = service.create_triage(triage_data, current_user.id)

        return success_response(
            data=triage.to_dict(),
            message=f"Triage registrado exitosamente con prioridad {triage.prioridad.value.upper()}"
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar triage: {str(exc)}"
        )


@router.get("/", response_model=dict)
async def get_all_triages(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        prioridad: Optional[TriagePriorityEnum] = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """
    Obtiene todos los triages con filtros opcionales

    **Requiere:** Token JWT válido
    **Acceso:** Staff (Superadmin, Veterinario, Auxiliar)

    **Filtros disponibles:**
    - prioridad: urgente, alta, media, baja
    - skip y limit para paginación
    """
    try:
        service = TriageService(db)
        prioridad_str = prioridad.value if prioridad else None
        triages = service.get_all_triages(skip, limit, prioridad_str)

        return success_response(
            data=[triage.to_dict() for triage in triages],
            message=f"Se encontraron {len(triages)} triages"
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener triages: {str(exc)}"
        )


@router.get("/urgencias", response_model=dict)
async def get_cola_urgencias(
        limit: int = Query(50, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """
    Obtiene la cola de urgencias (prioridad URGENTE y ALTA)

    **Requiere:** Token JWT válido
    **Acceso:** Staff (Superadmin, Veterinario, Auxiliar)

    **Útil para:**
    - Dashboard médico
    - Organizar orden de atención
    - Visualizar pacientes críticos
    """
    try:
        service = TriageService(db)
        triages = service.get_cola_urgencias(limit)

        return success_response(
            data=[triage.to_dict() for triage in triages],
            message=f"Cola de urgencias: {len(triages)} pacientes"
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener cola de urgencias: {str(exc)}"
        )


@router.get("/{triage_id}", response_model=dict)
async def get_triage(
        triage_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene un triage por ID

    **Requiere:** Token JWT válido
    **Acceso:** Usuario autenticado
    """
    try:
        service = TriageService(db)
        triage = service.get_triage_by_id(triage_id)

        if not triage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Triage no encontrado"
            )

        return success_response(
            data=triage.to_dict(),
            message="Triage encontrado"
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener triage: {str(exc)}"
        )


@router.get("/cita/{cita_id}", response_model=dict)
async def get_triage_by_cita(
        cita_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene el triage asociado a una cita

    **Requiere:** Token JWT válido
    **Acceso:** Usuario autenticado
    """
    try:
        service = TriageService(db)
        triage = service.get_triage_by_cita(cita_id)

        if not triage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró triage para esta cita"
            )

        return success_response(
            data=triage.to_dict(),
            message="Triage de la cita encontrado"
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener triage de la cita: {str(exc)}"
        )


@router.get("/mascota/{mascota_id}", response_model=dict)
async def get_triages_by_mascota(
        mascota_id: UUID,
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene el historial de triages de una mascota

    **Requiere:** Token JWT válido
    **Acceso:** Usuario autenticado

    **Útil para:**
    - Ver evolución del paciente
    - Historial de urgencias
    - Análisis de prioridades pasadas
    """
    try:
        service = TriageService(db)
        triages = service.get_triages_by_mascota(mascota_id, skip, limit)

        return success_response(
            data=[triage.to_dict() for triage in triages],
            message=f"Historial de triages: {len(triages)} registros"
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener historial de triages: {str(exc)}"
        )


@router.put("/{triage_id}", response_model=dict)
async def update_triage(
        triage_id: UUID,
        update_data: TriageUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """
    Actualiza un triage existente

    **Requiere:** Token JWT válido
    **Acceso:** Staff (Superadmin, Veterinario, Auxiliar)

    **Nota:** La prioridad se recalcula automáticamente si se actualizan signos vitales

    **Uso poco común:** Normalmente los triages no se actualizan, se crea uno nuevo
    """
    try:
        service = TriageService(db)
        triage = service.update_triage(triage_id, update_data)

        return success_response(
            data=triage.to_dict(),
            message="Triage actualizado exitosamente"
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar triage: {str(exc)}"
        )


@router.delete("/{triage_id}", response_model=dict)
async def delete_triage(
        triage_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """
    Elimina un triage

    **Requiere:** Token JWT válido
    **Acceso:** Staff (Superadmin, Veterinario, Auxiliar)

    **Advertencia:** Esta acción es irreversible
    """
    try:
        service = TriageService(db)
        service.delete_triage(triage_id)

        return success_response(
            data=None,
            message="Triage eliminado exitosamente"
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar triage: {str(exc)}"
        )