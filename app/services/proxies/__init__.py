"""
Módulo de Proxies - Patrón Proxy
Control de acceso y caché para servicios críticos

Implementa:
- CacheProxy: Caché de citas del día (RNF-04)
- AuthProxy: Control de acceso avanzado (RF-02, RF-03, RN03, RN04, RN05)
- ProxyFactory: Creación simplificada de proxies (Factory Method)

Relaciona con: RF-02, RF-03, RF-05, RNF-01, RNF-04, RNF-07

Uso recomendado:
    from app.services.proxies import ProxyFactory

    # Con caché y autorización
    service = ProxyFactory.create_appointment_service_with_cache_and_auth(
        db=db,
        current_user=current_user
    )
"""

from .interfaces import AppointmentServiceInterface
from .cache_proxy import CacheProxy
from .auth_proxy import AuthProxy, PermissionDeniedException
from .proxy_factory import ProxyFactory
from .redis_config import get_redis_client, is_redis_available
from .user_auth_proxy import UserAuthProxy

__all__ = [
    'AppointmentServiceInterface',
    'CacheProxy',
    'AuthProxy',
    'PermissionDeniedException',
    'ProxyFactory',
    'get_redis_client',
    'is_redis_available',
    'UserAuthProxy',
]