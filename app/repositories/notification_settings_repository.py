"""
Repositorio de Configuración de Notificaciones
RF-06: Notificaciones por correo
CRUD para NotificationSettings
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.notification_settings import NotificationSettings


class NotificationSettingsRepository:
    """
    Repositorio para operaciones CRUD de configuración de notificaciones
    Patrón Repository: Abstrae el acceso a datos
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, settings: NotificationSettings) -> NotificationSettings:
        """
        Crea una nueva configuración de notificaciones

        Args:
            settings: Configuración a crear

        Returns:
            Configuración creada

        Raises:
            IntegrityError: Si ya existe configuración para ese usuario
        """
        try:
            self.db.add(settings)
            self.db.commit()
            self.db.refresh(settings)
            return settings
        except IntegrityError as integrity_error:
            self.db.rollback()
            raise ValueError(
                "Ya existe configuración de notificaciones para este usuario"
            ) from integrity_error

    def get_by_id(self, settings_id: UUID) -> Optional[NotificationSettings]:
        """
        Obtiene configuración por ID

        Args:
            settings_id: ID de la configuración

        Returns:
            Configuración o None si no existe
        """
        return (self.db.query(NotificationSettings)
                .filter(NotificationSettings.id == settings_id)
                .first())

    def get_by_user_id(self, user_id: UUID) -> Optional[NotificationSettings]:
        """
        Obtiene configuración por ID de usuario

        Args:
            user_id: ID del usuario

        Returns:
            Configuración o None si no existe
        """
        return (self.db.query(NotificationSettings)
                .filter(NotificationSettings.usuario_id == user_id)
                .first())

    def get_all(self, skip: int = 0, limit: int = 100) -> List[NotificationSettings]:
        """
        Obtiene todas las configuraciones con paginación

        Args:
            skip: Registros a saltar
            limit: Límite de registros

        Returns:
            Lista de configuraciones
        """
        return (self.db.query(NotificationSettings)
                .offset(skip)
                .limit(limit)
                .all())

    def update(
        self,
        settings_id: UUID,
        **kwargs
    ) -> Optional[NotificationSettings]:
        """
        Actualiza una configuración

        Args:
            settings_id: ID de la configuración
            **kwargs: Campos a actualizar

        Returns:
            Configuración actualizada o None si no existe
        """
        settings = self.get_by_id(settings_id)
        if not settings:
            return None

        for key, value in kwargs.items():
            if hasattr(settings, key) and value is not None:
                setattr(settings, key, value)

        self.db.commit()
        self.db.refresh(settings)
        return settings

    def delete(self, settings_id: UUID) -> bool:
        """
        Elimina una configuración

        Args:
            settings_id: ID de la configuración

        Returns:
            True si se eliminó, False si no existía
        """
        settings = self.get_by_id(settings_id)
        if not settings:
            return False

        self.db.delete(settings)
        self.db.commit()
        return True

    def exists_for_user(self, user_id: UUID) -> bool:
        """
        Verifica si existe configuración para un usuario

        Args:
            user_id: ID del usuario

        Returns:
            True si existe configuración
        """
        return (self.db.query(NotificationSettings)
                .filter(NotificationSettings.usuario_id == user_id)
                .count()) > 0

    def create_default_for_user(self, user_id: UUID) -> NotificationSettings:
        """
        Crea configuración por defecto para un usuario

        Args:
            user_id: ID del usuario

        Returns:
            Configuración creada
        """
        default_settings = NotificationSettings.get_default_settings()
        settings = NotificationSettings(
            usuario_id=user_id,
            **default_settings
        )

        return self.create(settings)

    def get_or_create_for_user(self, user_id: UUID) -> NotificationSettings:
        """
        Obtiene configuración existente o crea una por defecto

        Args:
            user_id: ID del usuario

        Returns:
            Configuración del usuario
        """
        settings = self.get_by_user_id(user_id)

        if not settings:
            settings = self.create_default_for_user(user_id)

        return settings

    def get_users_with_reminders_enabled(self) -> List[NotificationSettings]:
        """
        Obtiene usuarios que tienen recordatorios habilitados

        Returns:
            Lista de configuraciones con recordatorios habilitados
        """
        return (self.db.query(NotificationSettings)
                .filter(NotificationSettings.recordatorios_habilitados == True)  # noqa: E712
                .all())