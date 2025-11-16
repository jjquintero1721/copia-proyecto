"""
ProxyFactory - Patrón Factory Method
Facilita la creación de proxies con configuración correcta

Principios SOLID aplicados:
- Single Responsibility: Solo crea proxies
- Open/Closed: Extensible para nuevos tipos de proxies
- Dependency Inversion: Retorna interfaces, no implementaciones concretas
"""

import logging
from typing import Optional, Callable, Any
from sqlalchemy.orm import Session

from app.models.user import User
from .cache_proxy import CacheProxy
from .auth_proxy import AuthProxy
from .redis_config import get_redis_client

logger = logging.getLogger(__name__)


class ProxyFactory:
    """
    Factory para crear proxies de servicios

    Evita antipatrón: God Object
    Aplica: Factory Method Pattern
    """

    @staticmethod
    def create_appointment_service_with_cache(
            db: Session,
            ttl_seconds: int = CacheProxy.DEFAULT_TTL_SECONDS
    ) -> Any:
        """
        Crea AppointmentService envuelto en CacheProxy

        Args:
            db: Sesión de base de datos
            ttl_seconds: Tiempo de vida del caché en segundos

        Returns:
            CacheProxy que envuelve AppointmentService
        """
        from app.services.appointment import AppointmentService

        # Crear servicio real
        real_service = AppointmentService(db)

        # Obtener cliente Redis (opcional)
        redis_client = get_redis_client()

        # Crear proxies de caché
        cache_proxy = CacheProxy(
            real_service=real_service,
            redis_client=redis_client,
            ttl_seconds=ttl_seconds
        )

        logger.info("AppointmentService creado con CacheProxy")
        return cache_proxy

    @staticmethod
    def create_appointment_service_with_auth(
            db: Session,
            current_user: User,
            audit_callback: Optional[Callable] = None
    ) -> Any:
        """
        Crea AppointmentService envuelto en AuthProxy

        Args:
            db: Sesión de base de datos
            current_user: Usuario que ejecuta operaciones
            audit_callback: Función opcional para auditoría

        Returns:
            AuthProxy que envuelve AppointmentService
        """
        from app.services.appointment import AppointmentService

        # Crear servicio real
        real_service = AppointmentService(db)

        # Crear proxies de autorización
        auth_proxy = AuthProxy(
            real_service=real_service,
            current_user=current_user,
            audit_callback=audit_callback
        )

        logger.info(f"AppointmentService creado con AuthProxy para {current_user.correo}")
        return auth_proxy

    @staticmethod
    def create_appointment_service_with_cache_and_auth(
            db: Session,
            current_user: User,
            ttl_seconds: int = CacheProxy.DEFAULT_TTL_SECONDS,
            audit_callback: Optional[Callable] = None
    ) -> Any:
        """
        Crea AppointmentService envuelto en CacheProxy y AuthProxy

        Orden de envolturas: AuthProxy -> CacheProxy -> AppointmentService
        Esto permite que:
        1. Se verifiquen permisos primero (AuthProxy)
        2. Se use caché si está autorizado (CacheProxy)
        3. Se acceda al servicio real si es necesario

        Args:
            db: Sesión de base de datos
            current_user: Usuario que ejecuta operaciones
            ttl_seconds: Tiempo de vida del caché en segundos
            audit_callback: Función opcional para auditoría

        Returns:
            AuthProxy que envuelve CacheProxy que envuelve AppointmentService
        """
        from app.services.appointment import AppointmentService

        # Crear servicio real
        real_service = AppointmentService(db)

        # Obtener cliente Redis (opcional)
        redis_client = get_redis_client()

        # Envolver en CacheProxy
        cache_proxy = CacheProxy(
            real_service=real_service,
            redis_client=redis_client,
            ttl_seconds=ttl_seconds
        )

        # Envolver en AuthProxy
        auth_proxy = AuthProxy(
            real_service=cache_proxy,
            current_user=current_user,
            audit_callback=audit_callback
        )

        logger.info(
            f"AppointmentService creado con CacheProxy y AuthProxy "
            f"para {current_user.correo}"
        )
        return auth_proxy