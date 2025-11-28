"""
Configuración de Redis para CacheProxy
Conexión opcional con manejo de errores graceful

Principios aplicados:
- Dependency Injection: Redis es opcional
- Fail-safe: Si Redis no está disponible, el sistema continúa funcionando
- Configuration over Hardcoding: Usa variables de entorno
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def get_redis_client() -> Optional[any]:
    """
    Crea y retorna un cliente de Redis si está configurado

    Returns:
        Cliente de Redis o None si no está disponible/configurado

    Variables de entorno:
        REDIS_HOST: Host de Redis (default: localhost)
        REDIS_PORT: Puerto de Redis (default: 6379)
        REDIS_DB: Base de datos de Redis (default: 0)
        REDIS_PASSWORD: Contraseña de Redis (opcional)
        REDIS_ENABLED: Habilitar Redis (default: False)
    """
    # Verificar si Redis está habilitado
    redis_enabled = os.getenv('REDIS_ENABLED', 'False').lower() == 'true'

    if not redis_enabled:
        logger.info("Redis deshabilitado en configuración")
        return None

    try:
        # Intentar importar redis
        import redis

        # Configuración desde variables de entorno
        config = {
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': int(os.getenv('REDIS_PORT', '6379')),
            'db': int(os.getenv('REDIS_DB', '0')),
            'decode_responses': True,  # Decodificar automáticamente a strings
            'socket_connect_timeout': 5,
            'socket_timeout': 5,
            'retry_on_timeout': True,
            'health_check_interval': 30
        }

        # Agregar password si está configurado
        redis_password = os.getenv('REDIS_PASSWORD')
        if redis_password:
            config['password'] = redis_password

        # Crear cliente
        client = redis.Redis(**config)

        # Verificar conexión
        client.ping()

        logger.info(f"✅ Conexión a Redis establecida ({config['host']}:{config['port']})")
        return client

    except ImportError:
        logger.warning(
            "⚠️ Librería 'redis' no instalada. "
            "Instala con: pip install redis"
        )
        return None

    except Exception as exc:
        logger.warning(
            f"⚠️ No se pudo conectar a Redis: {exc}. "
            "Usando caché en memoria como fallback"
        )
        return None


def is_redis_available(redis_client: Optional[any]) -> bool:
    """
    Verifica si Redis está disponible y funcionando

    Args:
        redis_client: Cliente de Redis

    Returns:
        True si Redis está disponible, False en caso contrario
    """
    if redis_client is None:
        return False

    try:
        redis_client.ping()
        return True
    except Exception:
        return False