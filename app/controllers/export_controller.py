"""
Controller - Endpoints para exportación de historias clínicas
RNF-06: Interoperabilidad - Exportar información en formatos estándar
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.schemas.export_schemas import (
    ExportHistoriaClinicaRequest,
    ExportHistoriaClinicaResponse
)
from app.services.export.export_service import ExportService
from app.security.dependencies import get_current_active_user
from app.models.user import User

router = APIRouter(
    tags=["Exportación"]
)


@router.post(
    "/historias-clinicas/{historia_clinica_id}",
    summary="Exportar historia clínica",
    description="""
    Exporta una historia clínica completa en el formato especificado (PDF o CSV).

    **Permisos requeridos**: SUPERADMIN, VETERINARIO, AUXILIAR

    **Formatos soportados**:
    - **PDF**: Documento profesional con toda la información formateada
    - **CSV**: Archivo tabular compatible con Excel y hojas de cálculo

    **Requisitos**:
    - RNF-06: Interoperabilidad - Exportar información en formatos estándar
    - RF-07: Gestión de historias clínicas
    - RN10-1: Las historias clínicas no pueden estar eliminadas

    **Retorna**:
    - Archivo descargable en el formato solicitado
    """,
    responses={
        200: {
            "description": "Archivo generado exitosamente",
            "content": {
                "application/pdf": {
                    "example": "Binary PDF content"
                },
                "text/csv": {
                    "example": "CSV content"
                }
            }
        },
        400: {"description": "Formato no soportado o datos inválidos"},
        403: {"description": "Usuario sin permisos para exportar"},
        404: {"description": "Historia clínica no encontrada"}
    }
)
async def exportar_historia_clinica(
        historia_clinica_id: UUID,
        request: ExportHistoriaClinicaRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
) -> StreamingResponse:
    """
    Endpoint para exportar una historia clínica

    Args:
        historia_clinica_id: ID de la historia clínica a exportar
        request: Formato de exportación deseado
        db: Sesión de base de datos
        current_user: Usuario autenticado

    Returns:
        StreamingResponse: Archivo descargable

    Raises:
        HTTPException: Si hay errores de validación o permisos
    """
    try:
        # Crear servicio de exportación
        export_service = ExportService(db)

        # Ejecutar exportación
        archivo, nombre_archivo, content_type = export_service.exportar_historia_clinica(
            historia_clinica_id=historia_clinica_id,
            formato=request.formato,
            usuario_solicitante_id=current_user.id
        )

        # Retornar archivo como stream
        return StreamingResponse(
            archivo,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{nombre_archivo}"',
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )

    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al exportar historia clínica: {str(e)}"
        )


@router.get(
    "/formatos",
    summary="Listar formatos de exportación disponibles",
    description="Retorna los formatos de exportación soportados por el sistema",
    response_model=dict
)
async def listar_formatos_exportacion(
        current_user: User = Depends(get_current_active_user)
):
    """
    Endpoint para listar formatos de exportación disponibles

    Returns:
        Dict con formatos disponibles
    """
    return {
        "formatos_disponibles": [
            {
                "nombre": "PDF",
                "extension": "pdf",
                "content_type": "application/pdf",
                "descripcion": "Documento PDF profesional con formato completo"
            },
            {
                "nombre": "CSV",
                "extension": "csv",
                "content_type": "text/csv",
                "descripcion": "Archivo CSV compatible con Excel y hojas de cálculo"
            }
        ]
    }