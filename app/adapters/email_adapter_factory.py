"""
Factory Pattern para Adaptadores de Correo Electrónico
RF-06: Notificaciones por correo
Patrón de diseño: Factory Method

Propósito:
Crear instancias de adaptadores de correo según configuración
sin exponer la lógica de creación al cliente

Permite cambiar fácilmente entre proveedores:
- SMTP (por defecto)
- SendGrid
- AWS SES (futuro)
- Otros proveedores (futuro)
"""

import logging
from enum import Enum
from typing import Optional
import os

from app.adapters.email_adapter import EmailAdapter
from app.adapters.smtp_adapter import SMTPAdapter
from app.adapters.sendgrid_adapter import SendGridAdapter

logger = logging.getLogger(__name__)


class EmailProviderType(str, Enum):
    """
    Enumeración de proveedores de correo disponibles
    Principio OCP: Fácil de extender con nuevos proveedores
    """
    SMTP = "smtp"
    SENDGRID = "sendgrid"
    AWS_SES = "aws_ses"  # Futuro
    MAILGUN = "mailgun"  # Futuro


class EmailAdapterFactory:
    """
    Factory para crear adaptadores de correo electrónico
    Patrón Factory Method

    Principio SRP: Una sola responsabilidad - crear adaptadores
    Principio OCP: Abierto para extensión (nuevos proveedores),
                   cerrado para modificación (código existente)
    """

    # Singleton: Una sola instancia de la factory
    _instance: Optional['EmailAdapterFactory'] = None

    def __new__(cls):
        """
        Implementa Singleton Pattern
        Solo una instancia de la factory en toda la aplicación
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    def create_adapter(
        provider_type: Optional[EmailProviderType] = None
    ) -> EmailAdapter:
        """
        Crea y retorna un adaptador de correo según el tipo especificado

        Args:
            provider_type: Tipo de proveedor (si no se especifica, usa EMAIL_PROVIDER env)

        Returns:
            EmailAdapter configurado

        Raises:
            ValueError: Si el proveedor no es válido o no está configurado
        """
        # Determinar proveedor desde parámetro o variable de entorno
        if provider_type is None:
            provider_str = os.getenv("EMAIL_PROVIDER", "smtp").lower()
            try:
                provider_type = EmailProviderType(provider_str)
            except ValueError:
                logger.warning(
                    f"⚠️ Proveedor '{provider_str}' no reconocido. "
                    f"Usando SMTP por defecto"
                )
                provider_type = EmailProviderType.SMTP

        # Factory Method: Crear adaptador según tipo
        if provider_type == EmailProviderType.SMTP:
            return EmailAdapterFactory._create_smtp_adapter()

        if provider_type == EmailProviderType.SENDGRID:
            return EmailAdapterFactory._create_sendgrid_adapter()

        if provider_type == EmailProviderType.AWS_SES:
            raise NotImplementedError(
                "AWS SES adapter no implementado aún. "
                "Usa 'smtp' o 'sendgrid'"
            )

        if provider_type == EmailProviderType.MAILGUN:
            raise NotImplementedError(
                "Mailgun adapter no implementado aún. "
                "Usa 'smtp' o 'sendgrid'"
            )

        raise ValueError(f"Proveedor de correo no válido: {provider_type}")

    @staticmethod
    def _create_smtp_adapter() -> SMTPAdapter:
        """
        Crea y configura un adaptador SMTP
        Principio SRP: Método privado para crear SMTP específicamente
        """
        try:
            adapter = SMTPAdapter()
            logger.info("✉️ Adaptador SMTP creado exitosamente")
            return adapter

        except Exception as error:
            logger.error(f"❌ Error al crear adaptador SMTP: {str(error)}")
            raise ValueError(
                f"No se pudo crear adaptador SMTP. "
                f"Verifica la configuración. Error: {str(error)}"
            )

    @staticmethod
    def _create_sendgrid_adapter() -> SendGridAdapter:
        """
        Crea y configura un adaptador SendGrid
        Principio SRP: Método privado para crear SendGrid específicamente
        """
        try:
            adapter = SendGridAdapter()
            logger.info("✉️ Adaptador SendGrid creado exitosamente")
            return adapter

        except ImportError:
            logger.error(
                "❌ SendGrid no está instalado. "
                "Instala con: pip install sendgrid"
            )
            raise ValueError(
                "SendGrid no disponible. "
                "Instala con: pip install sendgrid"
            )

        except Exception as error:
            logger.error(f"❌ Error al crear adaptador SendGrid: {str(error)}")
            raise ValueError(
                f"No se pudo crear adaptador SendGrid. "
                f"Verifica la configuración. Error: {str(error)}"
            )

    @staticmethod
    def get_available_providers() -> list:
        """
        Retorna lista de proveedores disponibles y configurados

        Returns:
            Lista de nombres de proveedores disponibles
        """
        available = []

        # Verificar SMTP
        try:
            smtp_configured = all([
                os.getenv("SMTP_HOST"),
                os.getenv("SMTP_USER"),
                os.getenv("SMTP_PASSWORD")
            ])
            if smtp_configured:
                available.append("smtp")
        except Exception:
            pass

        # Verificar SendGrid
        try:
            sendgrid_configured = bool(os.getenv("SENDGRID_API_KEY"))
            if sendgrid_configured:
                available.append("sendgrid")
        except Exception:
            pass

        return available

    @staticmethod
    def verify_provider_configuration(
        provider_type: EmailProviderType
    ) -> tuple[bool, Optional[str]]:
        """
        Verifica si un proveedor está correctamente configurado

        Args:
            provider_type: Tipo de proveedor a verificar

        Returns:
            Tuple (is_configured, error_message)
        """
        try:
            adapter = EmailAdapterFactory.create_adapter(provider_type)
            is_connected = adapter.verify_connection()

            if is_connected:
                return True, None

            return False, "No se pudo conectar con el proveedor"

        except Exception as error:
            return False, str(error)


# ==================== FUNCIONES AUXILIARES ====================

def get_email_adapter() -> EmailAdapter:
    """
    Función auxiliar para obtener el adaptador de correo configurado
    Usa Factory para crear la instancia apropiada

    Returns:
        EmailAdapter listo para usar

    Ejemplo:
        adapter = get_email_adapter()
        result = adapter.send_email(message)
    """
    factory = EmailAdapterFactory()
    return factory.create_adapter()


def switch_email_provider(provider_type: EmailProviderType) -> EmailAdapter:
    """
    Cambia dinámicamente el proveedor de correo

    Args:
        provider_type: Nuevo proveedor a usar

    Returns:
        EmailAdapter del nuevo proveedor
    """
    logger.info(f"🔄 Cambiando proveedor de correo a: {provider_type.value}")
    factory = EmailAdapterFactory()
    return factory.create_adapter(provider_type)