"""
Controlador de Historias Clínicas
RF-07: Gestión de historias clínicas
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.services.medical_history.medical_history_service import MedicalHistoryService
from app.schemas.consultation_schema import (
    ConsultationCreate,
    ConsultationUpdate,
    ConsultationResponse,
    MedicalHistoryResponse
)
from app.models.user import User
from app.security.dependencies import (
    get_current_active_user,
    require_staff,
    require_veterinarian_or_admin
)
from app.utils.responses import success_response
from app.commands.medical_history_commands import (
    CreateConsultationCommand,
    UpdateConsultationCommand,
    RestoreConsultationVersionCommand
)

router = APIRouter()

ID_CONSULTA_MSG = "ID de la consulta"


# ==================== CONSULTAS ====================

@router.post("/consultas", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_consultation(
    consultation_data: ConsultationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff)
):
    """
    Crea una nueva consulta en una historia clínica

    **Requiere:** Token JWT válido
    **Acceso:** Staff (Superadmin, Veterinario, Auxiliar)

    **RF-07:** Gestión de historias clínicas
    **RN10-2:** Registra fecha, hora y usuario

    **Validaciones:**
    - Historia clínica debe existir
    - Veterinario debe existir
    - Campos obligatorios: motivo, diagnóstico, tratamiento
    """
    try:
        cmd = CreateConsultationCommand(
            db=db,
            consultation_data=consultation_data,
            usuario_id=current_user.id
        )
        consultation = cmd.execute()

        return success_response(
            data=ConsultationResponse.model_validate(consultation).model_dump(mode="json"),
            message="Consulta creada exitosamente",
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
            detail=f"Error al crear consulta: {str(exc)}"
        )


@router.get("/consultas/{consultation_id}", response_model=dict)
async def get_consultation(
    consultation_id: UUID = Path(..., description=ID_CONSULTA_MSG),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene una consulta por ID

    **Requiere:** Token JWT válido
    **Acceso:** Cualquier usuario autenticado
    """
    try:
        service = MedicalHistoryService(db)
        consultation = service.get_consultation_by_id(consultation_id)

        if not consultation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consulta no encontrada"
            )

        return success_response(
            data=ConsultationResponse.model_validate(consultation).model_dump(mode="json"),
            message="Consulta encontrada"
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener consulta: {str(exc)}"
        )


@router.put("/consultas/{consultation_id}", response_model=dict)
async def update_consultation(
    consultation_id: UUID = Path(..., description=ID_CONSULTA_MSG),
    update_data: ConsultationUpdate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff)
):
    """
    Actualiza una consulta existente

    **Requiere:** Token JWT válido
    **Acceso:** Staff (Superadmin, Veterinario, Auxiliar)

    **RN10-2:** Registra cambios con fecha, hora y usuario
    **Memento Pattern:** Crea snapshot antes de actualizar
    """
    try:
        cmd = UpdateConsultationCommand(
            db=db,
            consultation_id=consultation_id,
            update_data=update_data,
            usuario_id=current_user.id
        )
        consultation = cmd.execute()

        return success_response(
            data=ConsultationResponse.model_validate(consultation).model_dump(mode="json"),
            message="Consulta actualizada exitosamente"
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar consulta: {str(exc)}"
        )


@router.get("/consultas/{consultation_id}/historial", response_model=dict)
async def get_consultation_history(
    consultation_id: UUID = Path(..., description=ID_CONSULTA_MSG),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene el historial de versiones de una consulta

    **Requiere:** Token JWT válido
    **Acceso:** Cualquier usuario autenticado

    **Memento Pattern:** Recupera snapshots anteriores
    """
    try:
        service = MedicalHistoryService(db)
        mementos = service.get_consultation_history(consultation_id, skip, limit)

        return success_response(
            data=[m.to_dict() for m in mementos],
            message=f"Historial de versiones ({len(mementos)} versiones)"
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener historial: {str(exc)}"
        )


@router.post("/consultas/{consultation_id}/restaurar/{version}", response_model=dict)
async def restore_consultation_version(
    consultation_id: UUID = Path(..., description="ID de la consulta"),
    version: int = Path(..., ge=1, description="Versión a restaurar"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_veterinarian_or_admin)
):
    """
    Restaura una versión anterior de una consulta

    **Requiere:** Token JWT válido
    **Acceso:** Veterinarios y Superadmin únicamente

    **Memento Pattern:** Restaura snapshot de versión anterior
    """
    try:
        cmd = RestoreConsultationVersionCommand(
            db=db,
            consultation_id=consultation_id,
            version=version,
            usuario_id=current_user.id
        )
        consultation = cmd.execute()

        return success_response(
            data=ConsultationResponse.model_validate(consultation).model_dump(mode="json"),
            message=f"Versión {version} restaurada exitosamente"
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al restaurar versión: {str(exc)}"
        )


# ==================== HISTORIAS CLÍNICAS ====================

@router.get("/historias/{historia_id}", response_model=dict)
async def get_medical_history(
    historia_id: UUID = Path(..., description="ID de la historia clínica"),
    include_consultas: bool = Query(True, description="Incluir lista de consultas"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene una historia clínica completa

    **Requiere:** Token JWT válido
    **Acceso:** Cualquier usuario autenticado

    **RF-07:** Mantener historial clínico completo
    """
    try:
        service = MedicalHistoryService(db)
        historia = service.get_medical_history_complete(historia_id, include_consultas)

        if not historia:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Historia clínica no encontrada"
            )

        return success_response(
            data=historia,
            message="Historia clínica encontrada"
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener historia clínica: {str(exc)}"
        )


@router.get("/mascotas/{mascota_id}/historia", response_model=dict)
async def get_medical_history_by_pet(
    mascota_id: UUID = Path(..., description="ID de la mascota"),
    include_consultas: bool = Query(True, description="Incluir lista de consultas"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene la historia clínica de una mascota

    **Requiere:** Token JWT válido
    **Acceso:** Cualquier usuario autenticado
    """
    try:
        service = MedicalHistoryService(db)
        historia = service.get_medical_history_by_mascota(mascota_id)

        if not historia:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Historia clínica no encontrada para esta mascota"
            )

        # Obtener completa
        historia_completa = service.get_medical_history_complete(
            historia.id,
            include_consultas
        )

        return success_response(
            data=historia_completa,
            message="Historia clínica de la mascota"
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener historia clínica: {str(exc)}"
        )


@router.get("/historias/{historia_id}/consultas", response_model=dict)
async def list_consultations_by_history(
    historia_id: UUID = Path(..., description="ID de la historia clínica"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lista todas las consultas de una historia clínica

    **Requiere:** Token JWT válido
    **Acceso:** Cualquier usuario autenticado
    """
    try:
        service = MedicalHistoryService(db)
        consultas = service.get_consultations_by_historia_clinica(
            historia_id,
            skip,
            limit
        )

        return success_response(
            data=[ConsultationResponse.model_validate(c).model_dump(mode="json") for c in consultas],
            message=f"Consultas encontradas: {len(consultas)}"
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar consultas: {str(exc)}"
        )