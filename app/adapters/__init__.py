"""
Módulo de Adaptadores de Correo Electrónico
Patrón Adapter: Provee interfaz única para múltiples proveedores

Exports:
- EmailAdapter: Interfaz abstracta
- SMTPAdapter: Implementación SMTP
- SendGridAdapter: Implementación SendGrid
- EmailAdapterFactory: Factory para crear adaptadores
- get_email_adapter: Función auxiliar
"""

from app.adapters.email_adapter import (
    EmailAdapter,
    EmailMessage,
    EmailResult,
    EmailSendException
)
from app.adapters.smtp_adapter import SMTPAdapter
from app.adapters.sendgrid_adapter import SendGridAdapter
from app.adapters.email_adapter_factory import (
    EmailAdapterFactory,
    EmailProviderType,
    get_email_adapter,
    switch_email_provider
)

__all__ = [
    # Interfaces y clases base
    'EmailAdapter',
    'EmailMessage',
    'EmailResult',
    'EmailSendException',

    # Implementaciones
    'SMTPAdapter',
    'SendGridAdapter',

    # Factory
    'EmailAdapterFactory',
    'EmailProviderType',

    # Funciones auxiliares
    'get_email_adapter',
    'switch_email_provider'
]