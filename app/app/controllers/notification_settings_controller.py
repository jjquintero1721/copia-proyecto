"""
Controlador de Configuración de Notificaciones
RF-06: Notificaciones por correo
Endpoints para gestionar preferencias de notificaciones
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.models.notification_settings import NotificationSettings
from app.repositories.notification_settings_repository import NotificationSettingsRepository
from app.schemas.notification_settings_schema import (
    NotificationSettingsCreate,
    NotificationSettingsUpdate,
    NotificationSettingsResponse,
    EmailProviderInfoResponse,
    EmailTestRequest,
    EmailTestResponse
)
from app.security.dependencies import get_current_active_user
from app.utils.responses import success_response
from app.adapters.email_adapter_factory import (
    EmailAdapterFactory,
    EmailProviderType,
    get_email_adapter
)
from app.adapters.email_adapter import EmailMessage

router = APIRouter()


@router.get("/settings", response_model=dict)
async def get_my_notification_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene la configuración de notificaciones del usuario actual
    """
    try:
        repo = NotificationSettingsRepository(db)
        settings = repo.get_or_create_for_user(current_user.id)

        return success_response(
            data=settings.to_dict(),
            message="Configuración de notificaciones obtenida"
        )

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener configuración: {str(error)}"
        )


@router.post("/settings", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_notification_settings(
    settings_data: NotificationSettingsCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Crea configuración de notificaciones
    Solo superadmins pueden crear para otros usuarios
    """
    try:
        # Verificar permisos
        if settings_data.usuario_id != current_user.id:
            if current_user.rol.value != "superadmin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permisos para crear configuración de otros usuarios"
                )

        repo = NotificationSettingsRepository(db)

        # Verificar si ya existe
        if repo.exists_for_user(settings_data.usuario_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe configuración para este usuario"
            )

        # Crear configuración
        settings = NotificationSettings(**settings_data.dict())
        created_settings = repo.create(settings)

        return success_response(
            data=created_settings.to_dict(),
            message="Configuración de notificaciones creada",
            status_code=status.HTTP_201_CREATED
        )

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear configuración: {str(error)}"
        )


@router.put("/settings", response_model=dict)
async def update_my_notification_settings(
    settings_data: NotificationSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Actualiza la configuración de notificaciones del usuario actual
    """
    try:
        repo = NotificationSettingsRepository(db)
        settings = repo.get_by_user_id(current_user.id)

        if not settings:
            # Crear configuración si no existe
            settings = repo.create_default_for_user(current_user.id)

        # Actualizar campos
        update_data = settings_data.dict(exclude_unset=True)
        updated_settings = repo.update(settings.id, **update_data)

        return success_response(
            data=updated_settings.to_dict(),
            message="Configuración actualizada exitosamente"
        )

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar configuración: {str(error)}"
        )


@router.get("/provider-info", response_model=dict)
async def get_email_provider_info(
    _current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene información del proveedor de correo configurado
    Solo para staff/admin
    """
    try:
        EmailAdapterFactory()
        adapter = get_email_adapter()

        provider_name = adapter.get_provider_name()
        is_connected = adapter.verify_connection()

        return success_response(
            data={
                "provider_name": provider_name,
                "is_configured": True,
                "is_connected": is_connected,
                "error_message": None if is_connected else "No se pudo conectar"
            },
            message="Información del proveedor obtenida"
        )

    except Exception as error:
        return success_response(
            data={
                "provider_name": "Unknown",
                "is_configured": False,
                "is_connected": False,
                "error_message": str(error)
            },
            message="Error al obtener información del proveedor"
        )


@router.post("/test-email", response_model=dict)
async def send_test_email(
    test_data: EmailTestRequest,
    _current_user: User = Depends(get_current_active_user)
):
    """
    Envía un correo de prueba
    Solo para staff/admin
    """
    try:
        adapter = get_email_adapter()

        # Construir mensaje de prueba
        message = EmailMessage(
            to=test_data.to_email,
            subject=test_data.subject,
            body_html=f"""
                <html>
                <body>
                    <h2>Correo de Prueba - Sistema GDCV</h2>
                    <p>{test_data.message}</p>
                    <hr>
                    <p><small>Enviado por el sistema de notificaciones GDCV</small></p>
                </body>
                </html>
            """,
            body_text=test_data.message
        )

        # Enviar
        result = adapter.send_email(message)

        if result.success:
            return success_response(
                data={
                    "success": True,
                    "message_id": result.message_id,
                    "provider": result.provider,
                    "sent_at": result.sent_at.isoformat() if result.sent_at else None
                },
                message="Correo de prueba enviado exitosamente"
            )

        return success_response(
            data={
                "success": False,
                "error": result.error,
                "provider": result.provider
            },
            message="Error al enviar correo de prueba"
        )

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al enviar correo de prueba: {str(error)}"
        )