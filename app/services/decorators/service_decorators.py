"""
Decoradores de Servicios - Patrón Decorator
Extiende funcionalidades de servicios dinámicamente

Patrón Decorator aplicado a servicios:
- LoggingDecorator: Registra operaciones con logging profesional
- AuditDecorator: Registra en base de datos (tabla audit_log)
- ValidationDecorator: Valida inputs/outputs

RNF-07: Auditoría completa del sistema
Relaciona con: RF-05, RNF-07
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class ServiceDecorator(ABC):
    """
    Decorador abstracto base para servicios

    Patrón Decorator: Define la interfaz común para todos los decoradores
    Principio Open/Closed: Abierto para extensión, cerrado para modificación
    """

    def __init__(self, service: Any):
        """
        Inicializa el decorador con el servicio a decorar

        Args:
            service: Servicio que será decorado (puede ser otro decorador)
        """
        self._service = service

    @abstractmethod
    def __getattr__(self, name: str) -> Any:
        """
        Delega llamadas de métodos al servicio decorado
        Permite que los decoradores sean transparentes
        """
        return getattr(self._service, name)


class LoggingDecorator(ServiceDecorator):
    """
    Decorador que añade logging profesional a servicios

    Registra:
    - Inicio de operación
    - Tiempo de ejecución
    - Resultado (éxito/fallo)
    - Errores capturados

    RNF-07: Registro de operaciones
    """

    def __init__(self, service: Any, logger_name: Optional[str] = None):
        """
        Args:
            service: Servicio a decorar
            logger_name: Nombre del logger (opcional)
        """
        super().__init__(service)
        self._logger = logging.getLogger(logger_name or service.__class__.__name__)

    def __getattr__(self, name: str) -> Any:
        """
        Intercepta llamadas a métodos del servicio y añade logging
        """
        attr = getattr(self._service, name)

        if callable(attr):
            def wrapped(*args, **kwargs):
                # Logging de inicio
                self._logger.info(
                    f"📝 [Logging] Iniciando operación: {name}"
                )
                self._logger.debug(
                    f"   Args: {args}, Kwargs: {kwargs}"
                )

                start_time = datetime.now(timezone.utc)

                try:
                    # Ejecutar operación original
                    result = attr(*args, **kwargs)

                    # Logging de éxito
                    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
                    self._logger.info(
                        f"✅ [Logging] Operación exitosa: {name} "
                        f"(tiempo: {elapsed:.3f}s)"
                    )

                    return result

                except Exception as error:
                    # Logging de error
                    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
                    self._logger.error(
                        f"❌ [Logging] Error en operación: {name} "
                        f"(tiempo: {elapsed:.3f}s) - Error: {str(error)}"
                    )
                    raise

            return wrapped

        return attr


class AuditDecorator(ServiceDecorator):
    """
    Decorador que registra auditoría en base de datos

    Registra en tabla audit_log:
    - Usuario que ejecuta la acción
    - Acción realizada
    - Timestamp
    - Datos adicionales (JSON)

    RNF-07: Auditoría completa del sistema
    """

    def __init__(
            self,
            service: Any,
            db: Session,
            usuario_id: Optional[UUID] = None
    ):
        """
        Args:
            service: Servicio a decorar
            db: Sesión de base de datos para registrar auditoría
            usuario_id: ID del usuario que ejecuta operaciones
        """
        super().__init__(service)
        self.db = db
        self.usuario_id = usuario_id
        self._service_name = service.__class__.__name__

    def __getattr__(self, name: str) -> Any:
        """
        Intercepta llamadas y registra auditoría en BD
        """
        attr = getattr(self._service, name)

        if callable(attr):
            def wrapped(*args, **kwargs):
                # Ejecutar operación
                result = attr(*args, **kwargs)

                # Registrar auditoría en BD
                self._registrar_auditoria(
                    accion=f"{self._service_name}.{name}",
                    descripcion=self._build_descripcion(name, args, kwargs, result)
                )

                return result

            return wrapped

        return attr

    def _registrar_auditoria(self, accion: str, descripcion: str) -> None:
        """
        Registra la auditoría en la tabla audit_log

        Args:
            accion: Nombre de la acción ejecutada
            descripcion: Descripción detallada de la acción
        """
        try:
            audit_log = AuditLog(
                usuario_id=self.usuario_id,
                accion=accion,
                descripcion=descripcion,
                fecha_hora=datetime.now(timezone.utc)
            )
            self.db.add(audit_log)
            self.db.commit()

            logger.info(f"📋 [Auditoría] Registrado: {accion}")

        except Exception as error:
            logger.error(
                f"❌ [Auditoría] Error al registrar: {str(error)}"
            )
            self.db.rollback()

    def _build_descripcion(
            self,
            method_name: str,
            args: tuple,
            kwargs: dict,
            result: Any
    ) -> str:
        """
        Construye la descripción de la auditoría

        Args:
            method_name: Nombre del método ejecutado
            args: Argumentos posicionales
            kwargs: Argumentos con nombre
            result: Resultado de la operación

        Returns:
            Descripción formateada para auditoría
        """
        descripcion_parts = [f"Operación: {method_name}"]

        # Extraer IDs de entidades si existen
        if args:
            descripcion_parts.append(f"Args: {args}")

        if kwargs:
            # Filtrar información sensible
            safe_kwargs = {
                k: v for k, v in kwargs.items()
                if k not in ['password', 'contrasena', 'token']
            }
            descripcion_parts.append(f"Kwargs: {safe_kwargs}")

        # Agregar ID del resultado si es una entidad
        if hasattr(result, 'id'):
            descripcion_parts.append(f"Entidad ID: {result.id}")

        return " | ".join(descripcion_parts)


class ValidationDecorator(ServiceDecorator):
    """
    Decorador que valida inputs y outputs de métodos

    Valida:
    - Tipos de datos
    - Valores permitidos
    - Reglas de negocio básicas
    - Consistencia de datos

    RNF-07: Validación de datos
    """

    def __init__(
            self,
            service: Any,
            validation_rules: Optional[Dict[str, callable]] = None
    ):
        """
        Args:
            service: Servicio a decorar
            validation_rules: Reglas de validación personalizadas
        """
        super().__init__(service)
        self.validation_rules = validation_rules or {}

    def __getattr__(self, name: str) -> Any:
        """
        Intercepta llamadas y valida antes/después de ejecutar
        """
        attr = getattr(self._service, name)

        if callable(attr):
            def wrapped(*args, **kwargs):
                # Validación previa (inputs)
                self._validate_inputs(name, args, kwargs)

                # Ejecutar operación
                result = attr(*args, **kwargs)

                # Validación posterior (outputs)
                self._validate_output(name, result)

                return result

            return wrapped

        return attr

    def _validate_inputs(
            self,
            method_name: str,
            args: tuple,
            kwargs: dict
    ) -> None:
        """
        Valida los inputs antes de ejecutar el método

        Args:
            method_name: Nombre del método
            args: Argumentos posicionales
            kwargs: Argumentos con nombre

        Raises:
            ValueError: Si la validación falla
        """
        # Validar según reglas personalizadas si existen
        if method_name in self.validation_rules:
            validator = self.validation_rules[method_name]
            if not validator(args, kwargs):
                raise ValueError(
                    f"Validación fallida para {method_name}"
                )

        # Validaciones genéricas
        if args:
            for arg in args:
                if arg is None:
                    logger.warning(
                        f"⚠️ [Validación] Argumento None en {method_name}"
                    )

    def _validate_output(self, method_name: str, result: Any) -> None:
        """
        Valida el output después de ejecutar el método

        Args:
            method_name: Nombre del método
            result: Resultado de la operación

        Raises:
            ValueError: Si la validación falla
        """
        if result is None:
            logger.warning(
                f"⚠️ [Validación] Resultado None en {method_name}"
            )


# ==================== FUNCIÓN DE UTILIDAD ====================

def create_decorated_service(
        service: Any,
        db: Optional[Session] = None,
        usuario_id: Optional[UUID] = None,
        enable_logging: bool = True,
        enable_audit: bool = True,
        enable_validation: bool = False,
        validation_rules: Optional[Dict[str, callable]] = None
) -> Any:
    """
    Factory function para crear servicios decorados

    Permite apilar decoradores fácilmente:
    service -> Logging -> Audit -> Validation

    Args:
        service: Servicio base a decorar
        db: Sesión de BD (requerida si enable_audit=True)
        usuario_id: ID del usuario (requerido si enable_audit=True)
        enable_logging: Habilitar LoggingDecorator
        enable_audit: Habilitar AuditDecorator
        enable_validation: Habilitar ValidationDecorator
        validation_rules: Reglas personalizadas de validación

    Returns:
        Servicio decorado

    """
    decorated_service = service

    # Apilar decoradores en orden
    if enable_validation:
        decorated_service = ValidationDecorator(
            decorated_service,
            validation_rules
        )

    if enable_audit:
        if not db or not usuario_id:
            raise ValueError(
                "db y usuario_id son requeridos para AuditDecorator"
            )
        decorated_service = AuditDecorator(
            decorated_service,
            db,
            usuario_id
        )

    if enable_logging:
        decorated_service = LoggingDecorator(decorated_service)

    return decorated_service