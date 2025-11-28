"""
Modelo de Configuración de Notificaciones
RF-06: Notificaciones por correo
RN09: Solo correo electrónico

Permite a los usuarios configurar sus preferencias de notificaciones
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.database import Base


class NotificationSettings(Base):
    """
    Modelo de configuración de notificaciones por usuario

    Permite personalizar:
    - Habilitar/deshabilitar recordatorios
    - Tiempo de anticipación para recordatorios
    - Habilitar confirmaciones automáticas
    - Habilitar notificaciones de cambios
    """
    __tablename__ = "configuracion_notificaciones"

    # Identificador único
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Relación con usuario (un usuario tiene una configuración)
    usuario_id = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    # ==================== CONFIGURACIÓN DE RECORDATORIOS ====================
    # Habilitar recordatorios automáticos
    recordatorios_habilitados = Column(Boolean, default=True, nullable=False)

    # Horas de anticipación para recordatorios (por defecto 24 horas)
    horas_anticipacion_recordatorio = Column(Integer, default=24, nullable=False)

    # ==================== CONFIGURACIÓN DE CONFIRMACIONES ====================
    # Enviar confirmación cuando se agenda una cita
    enviar_confirmacion_cita = Column(Boolean, default=True, nullable=False)

    # Enviar notificación cuando se reprograma una cita
    enviar_notificacion_reprogramacion = Column(Boolean, default=True, nullable=False)

    # Enviar notificación cuando se cancela una cita
    enviar_notificacion_cancelacion = Column(Boolean, default=True, nullable=False)

    # ==================== CONFIGURACIÓN ADICIONAL ====================
    # Idioma preferido para las notificaciones
    idioma_preferido = Column(String(5), default="es", nullable=False)

    # Correo alternativo para notificaciones (opcional)
    correo_alternativo = Column(String(150), nullable=True)

    # Auditoría
    fecha_creacion = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    fecha_actualizacion = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relaciones
    usuario = relationship("User", backref="configuracion_notificaciones")

    def __repr__(self):
        return (f"<ConfiguracionNotificaciones usuario_id={self.usuario_id} "
                f"recordatorios={self.recordatorios_habilitados}>")

    def to_dict(self):
        """Convierte la configuración a diccionario"""
        return {
            "id": str(self.id),
            "usuario_id": str(self.usuario_id),
            "recordatorios_habilitados": self.recordatorios_habilitados,
            "horas_anticipacion_recordatorio": self.horas_anticipacion_recordatorio,
            "enviar_confirmacion_cita": self.enviar_confirmacion_cita,
            "enviar_notificacion_reprogramacion": self.enviar_notificacion_reprogramacion,
            "enviar_notificacion_cancelacion": self.enviar_notificacion_cancelacion,
            "idioma_preferido": self.idioma_preferido,
            "correo_alternativo": self.correo_alternativo,
            "fecha_creacion": (self.fecha_creacion.isoformat()
                               if self.fecha_creacion else None),
            "fecha_actualizacion": (self.fecha_actualizacion.isoformat()
                                    if self.fecha_actualizacion else None)
        }

    @classmethod
    def get_default_settings(cls):
        """
        Retorna configuración por defecto para nuevos usuarios
        Principio: Configuración razonable por defecto
        """
        return {
            "recordatorios_habilitados": True,
            "horas_anticipacion_recordatorio": 24,
            "enviar_confirmacion_cita": True,
            "enviar_notificacion_reprogramacion": True,
            "enviar_notificacion_cancelacion": True,
            "idioma_preferido": "es",
            "correo_alternativo": None
        }

    def should_send_reminder(self) -> bool:
        """Verifica si se deben enviar recordatorios para este usuario"""
        return self.recordatorios_habilitados

    def should_send_confirmation(self) -> bool:
        """Verifica si se debe enviar confirmación de cita"""
        return self.enviar_confirmacion_cita

    def should_send_reschedule_notification(self) -> bool:
        """Verifica si se debe enviar notificación de reprogramación"""
        return self.enviar_notificacion_reprogramacion

    def should_send_cancellation_notification(self) -> bool:
        """Verifica si se debe enviar notificación de cancelación"""
        return self.enviar_notificacion_cancelacion

    def get_reminder_hours(self) -> int:
        """Obtiene las horas de anticipación para recordatorios"""
        return self.horas_anticipacion_recordatorio

    def get_notification_email(self, user_email: str) -> str:
        """
        Obtiene el correo para enviar notificaciones
        Prioriza correo alternativo si existe
        """
        return self.correo_alternativo if self.correo_alternativo else user_email