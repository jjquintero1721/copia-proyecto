"""
Schemas para Configuración de Notificaciones
RF-06: Notificaciones por correo
Validación con Pydantic
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class NotificationSettingsBase(BaseModel):
    """Schema base para configuración de notificaciones"""
    recordatorios_habilitados: bool = Field(
        default=True,
        description="Habilitar recordatorios automáticos de citas"
    )
    horas_anticipacion_recordatorio: int = Field(
        default=24,
        ge=1,
        le=168,  # Máximo 1 semana
        description="Horas de anticipación para recordatorios (1-168)"
    )
    enviar_confirmacion_cita: bool = Field(
        default=True,
        description="Enviar confirmación al agendar cita"
    )
    enviar_notificacion_reprogramacion: bool = Field(
        default=True,
        description="Enviar notificación al reprogramar cita"
    )
    enviar_notificacion_cancelacion: bool = Field(
        default=True,
        description="Enviar notificación al cancelar cita"
    )
    idioma_preferido: str = Field(
        default="es",
        pattern="^(es|en)$",
        description="Idioma preferido para notificaciones (es/en)"
    )
    correo_alternativo: Optional[EmailStr] = Field(
        default=None,
        description="Correo alternativo para notificaciones (opcional)"
    )


class NotificationSettingsCreate(NotificationSettingsBase):
    """
    Schema para crear configuración de notificaciones
    Usado al crear un nuevo usuario o actualizar configuración
    """
    usuario_id: UUID = Field(
        description="ID del usuario al que pertenece la configuración"
    )


class NotificationSettingsUpdate(BaseModel):
    """
    Schema para actualizar configuración de notificaciones
    Todos los campos son opcionales
    """
    recordatorios_habilitados: Optional[bool] = None
    horas_anticipacion_recordatorio: Optional[int] = Field(None, ge=1, le=168)
    enviar_confirmacion_cita: Optional[bool] = None
    enviar_notificacion_reprogramacion: Optional[bool] = None
    enviar_notificacion_cancelacion: Optional[bool] = None
    idioma_preferido: Optional[str] = Field(None, pattern="^(es|en)$")
    correo_alternativo: Optional[EmailStr] = None


class NotificationSettingsResponse(NotificationSettingsBase):
    """Schema de respuesta para configuración de notificaciones"""
    id: UUID
    usuario_id: UUID
    fecha_creacion: datetime
    fecha_actualizacion: datetime

    class Config:
        from_attributes = True


class EmailProviderInfoResponse(BaseModel):
    """Schema de respuesta con información del proveedor de correo"""
    provider_name: str = Field(description="Nombre del proveedor (SMTP, SendGrid, etc.)")
    is_configured: bool = Field(description="Si el proveedor está configurado")
    is_connected: bool = Field(description="Si la conexión funciona")
    error_message: Optional[str] = Field(default=None, description="Mensaje de error si aplica")


class EmailTestRequest(BaseModel):
    """Schema para solicitud de prueba de envío de correo"""
    to_email: EmailStr = Field(description="Correo destinatario de prueba")
    subject: str = Field(
        default="Prueba de envío - Sistema GDCV",
        description="Asunto del correo de prueba"
    )
    message: str = Field(
        default="Este es un correo de prueba del sistema de notificaciones.",
        description="Mensaje del correo de prueba"
    )


class EmailTestResponse(BaseModel):
    """Schema de respuesta para prueba de envío"""
    success: bool = Field(description="Si el envío fue exitoso")
    message_id: Optional[str] = Field(default=None, description="ID del mensaje enviado")
    provider: str = Field(description="Proveedor usado")
    error: Optional[str] = Field(default=None, description="Error si ocurrió")
    sent_at: Optional[datetime] = Field(default=None, description="Fecha y hora de envío")