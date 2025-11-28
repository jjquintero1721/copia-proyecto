"""
Controlador de Seguimiento - Endpoints REST
RF-11: Seguimiento de pacientes

Endpoints:
- POST /medical-history/consultas/{consulta_id}/seguimiento - Crear seguimiento
- GET /medical-history/consultas/{consulta_id}/seguimientos - Listar seguimientos
- POST /follow-up/completar - Completar seguimiento
- GET /follow-up/estadisticas - Obtener estadísticas
"""

from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.security.dependencies import get_current_active_user, require_veterinarian_or_admin, require_staff
from app.schemas.follow_up_schema import (
    FollowUpCreate,
    FollowUpResponse,
    FollowUpListResponse,
    FollowUpCompletionCreate
)
from app.schemas.consultation_schema import ConsultationResponse
from app.commands.follow_up_commands import (
    CreateFollowUpCommand,
    CompleteFollowUpCommand,
    CancelFollowUpCommand
)
from app.utils.responses import success_response, error_response

router = APIRouter()


@router.post(
    "/consultas/{consulta_id}/seguimiento",
    response_model=dict,
    status_code=status.HTTP_201_CREATED
)
async def create_follow_up(
        consulta_id: UUID = Path(..., description="ID de la consulta que requiere seguimiento"),
        follow_up_data: FollowUpCreate = ...,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_veterinarian_or_admin)
):
    """
    Crea una cita de seguimiento para una consulta

    **RF-11 - Criterio de aceptación:**
    DADO que un veterinario recomienda seguimiento
    CUANDO lo programa
    ENTONCES el sistema crea una nueva cita asociada a la consulta original

    **Requiere:** Token JWT válido
    **Acceso:** Veterinarios y Superadmin únicamente

    **Flujo:**
    1. Valida que la consulta original exista
    2. Valida disponibilidad del veterinario
    3. Crea cita de seguimiento vinculada a la consulta
    4. Registra auditoría (Command Pattern)

    **Retorna:**
    - Información completa de la cita de seguimiento creada
    """
    try:
        # Validar que el ID de la consulta en la ruta coincida con el del body
        if consulta_id != follow_up_data.consulta_origen_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El ID de consulta en la ruta no coincide con el del cuerpo"
            )

        # Ejecutar comando con auditoría automática
        cmd = CreateFollowUpCommand(
            db=db,
            follow_up_data=follow_up_data,
            usuario_id=current_user.id
        )
        follow_up_result = cmd.execute()

        return success_response(
            data=follow_up_result,
            message="Seguimiento programado exitosamente"
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear seguimiento: {str(exc)}"
        )


@router.get(
    "/consultas/{consulta_id}/seguimientos",
    response_model=dict
)
async def get_consultation_follow_ups(
        consulta_id: UUID = Path(..., description="ID de la consulta"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene todos los seguimientos de una consulta

    **Requiere:** Token JWT válido
    **Acceso:** Cualquier usuario autenticado

    **Retorna:**
    - Lista de seguimientos programados para la consulta
    - Total de seguimientos
    """
    try:
        from app.services.follow_up.follow_up_service import FollowUpService
        service = FollowUpService(db)

        seguimientos = service.get_follow_ups_by_consultation(consulta_id)

        return success_response(
            data={
                "consulta_id": str(consulta_id),
                "total_seguimientos": len(seguimientos),
                "seguimientos": seguimientos
            },
            message=f"Se encontraron {len(seguimientos)} seguimiento(s)"
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener seguimientos: {str(exc)}"
        )


@router.post(
    "/completar",
    response_model=dict,
    status_code=status.HTTP_201_CREATED
)
async def complete_follow_up(
        completion_data: FollowUpCompletionCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_veterinarian_or_admin)
):
    """
    Registra la consulta de seguimiento completada

    **RF-11 - Criterio de aceptación:**
    DADO que se realiza seguimiento
    CUANDO se guarda la consulta
    ENTONCES se vincula automáticamente al historial clínico

    **Requiere:** Token JWT válido
    **Acceso:** Veterinarios y Superadmin únicamente

    **Flujo:**
    1. Valida que la cita de seguimiento exista
    2. Crea una nueva consulta vinculada al historial clínico
    3. Marca la cita como completada
    4. Registra auditoría (Command Pattern)

    **Retorna:**
    - Consulta de seguimiento creada
    """
    try:
        # Ejecutar comando con auditoría automática
        cmd = CompleteFollowUpCommand(
            db=db,
            completion_data=completion_data,
            veterinario_id=current_user.id
        )
        consultation = cmd.execute()

        return success_response(
            data=ConsultationResponse.model_validate(consultation).model_dump(mode="json"),
            message="Seguimiento completado y vinculado al historial clínico"
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al completar seguimiento: {str(exc)}"
        )


@router.delete(
    "/cancelar/{cita_seguimiento_id}",
    response_model=dict
)
async def cancel_follow_up(
        cita_seguimiento_id: UUID = Path(..., description="ID de la cita de seguimiento"),
        motivo: str = Query(..., min_length=5, description="Motivo de la cancelación"),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """
    Cancela una cita de seguimiento

    **Requiere:** Token JWT válido
    **Acceso:** Staff (Superadmin, Veterinario, Auxiliar)

    **Retorna:**
    - Cita de seguimiento cancelada
    """
    try:
        # Ejecutar comando con auditoría automática
        cmd = CancelFollowUpCommand(
            db=db,
            cita_seguimiento_id=cita_seguimiento_id,
            usuario_id=current_user.id,
            motivo_cancelacion=motivo
        )
        appointment = cmd.execute()

        return success_response(
            data=appointment.to_dict(),
            message="Seguimiento cancelado exitosamente"
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cancelar seguimiento: {str(exc)}"
        )


@router.get(
    "/estadisticas",
    response_model=dict
)
async def get_follow_up_statistics(
        mascota_id: Optional[UUID] = Query(None, description="Filtrar por mascota"),
        veterinario_id: Optional[UUID] = Query(None, description="Filtrar por veterinario"),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """
    Obtiene estadísticas de seguimientos

    **Requiere:** Token JWT válido
    **Acceso:** Staff (Superadmin, Veterinario, Auxiliar)

    **Retorna:**
    - Total de seguimientos
    - Seguimientos completados, pendientes y cancelados
    - Tasa de completitud
    """
    try:
        from app.services.follow_up.follow_up_service import FollowUpService
        service = FollowUpService(db)

        estadisticas = service.get_follow_up_statistics(
            mascota_id=mascota_id,
            veterinario_id=veterinario_id
        )

        return success_response(
            data=estadisticas,
            message="Estadísticas de seguimientos obtenidas"
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas: {str(exc)}"
        )