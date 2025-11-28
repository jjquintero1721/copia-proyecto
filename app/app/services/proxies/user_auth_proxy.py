"""
UserAuthProxy - Patrón Proxy para autenticación de usuarios
Control de acceso y auditoría en login/registro

Relaciona con: RF-02, RF-03, RN03, RN04, RN05, RNF-07
"""

import logging
from typing import Optional, Tuple, Callable
from uuid import UUID
from datetime import datetime, timezone

from app.models.user import User

logger = logging.getLogger(__name__)


class UserAuthProxy:
    """
    Proxy que añade auditoría y control al servicio de usuarios

    Funciones:
    - Loguea intentos de login (exitosos y fallidos)
    - Audita creación de usuarios
    - Control de intentos de login fallidos (para RN05)
    """

    def __init__(
            self,
            real_service,
            audit_callback: Optional[Callable] = None
    ):
        """
        Args:
            real_service: UserService real
            audit_callback: Función para auditoría
        """
        self._real_service = real_service
        self._audit = audit_callback

        logger.info("🔐 UserAuthProxy inicializado")

    def authenticate(
            self,
            correo: str,
            contrasena: str
    ) -> Optional[Tuple[User, str]]:
        """
        Autentica usuario con logging y auditoría

        Args:
            correo: Email del usuario
            contrasena: Contraseña en texto plano

        Returns:
            (User, token) si exitoso, None si falla
        """
        logger.info(f"🔑 Intento de login para: {correo}")

        # Delegar al servicio real
        result = self._real_service.authenticate(correo, contrasena)

        if result:
            user, token = result
            logger.info(f"✅ Login exitoso: {user.correo} (Rol: {user.rol.value})")

            # Auditar login exitoso
            self._log_action('login_exitoso', {
                'usuario': user.correo,
                'rol': user.rol.value,
                'user_id': str(user.id)
            })
        else:
            logger.warning(f"❌ Login fallido para: {correo}")

            # Auditar login fallido
            self._log_action('login_fallido', {
                'correo': correo,
                'ip': 'unknown'  # Puedes agregar la IP real del request
            })

        return result

    def create_user(self, user_data, creado_por: Optional[UUID] = None) -> User:
        """
        Crea usuario con auditoría

        Args:
            user_data: Datos del usuario a crear
            creado_por: UUID del usuario que crea

        Returns:
            Usuario creado
        """
        logger.info(f"👤 Creando usuario: {user_data.correo} (Rol: {user_data.rol.value})")

        # Delegar al servicio real
        user = self._real_service.create_user(user_data, creado_por)

        # Auditar creación
        self._log_action('usuario_creado', {
            'usuario': user.correo,
            'rol': user.rol.value,
            'creado_por': str(creado_por) if creado_por else None
        })

        logger.info(f"✅ Usuario creado exitosamente: {user.correo}")

        return user

    def _log_action(self, action: str, details: dict):
        """
        Registra acción para auditoría

        Args:
            action: Nombre de la acción
            details: Detalles adicionales
        """
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'action': action,
            'details': details
        }

        # Si hay callback de auditoría, usarlo
        if self._audit:
            try:
                self._audit(log_entry)
            except Exception as exc:
                logger.error(f"Error en callback de auditoría: {exc}")

        # Siempre loguear
        logger.info(f"📋 Auditoría: {action} - {details}")

    # Delegar otros métodos al servicio real
    def __getattr__(self, name):
        """Delega llamadas no definidas al servicio real"""
        return getattr(self._real_service, name)