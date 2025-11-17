"""
Patrón Adapter - Interfaz abstracta para proveedores de correo
RF-06: Notificaciones por correo
Patrón de diseño: Adapter Pattern

Propósito:
Proveer una interfaz única (IServicioCorreo) usada por NotificationService
mientras que adaptadores específicos traducen las llamadas a clientes concretos
(SMTP, SendGrid, AWS SES, etc.)

Este patrón permite:
- Cambiar de proveedor sin tocar la lógica del dominio
- Facilitar pruebas (mockear el adapter)
- Migrar de SMTP a servicios cloud sin cambios en el negocio
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class EmailMessage:
    """
    Estructura de datos para representar un mensaje de correo
    Principio SRP: Una sola responsabilidad - representar datos de email
    """
    to: str  # Destinatario principal
    subject: str  # Asunto del correo
    body_html: str  # Cuerpo del mensaje en HTML
    body_text: Optional[str] = None  # Cuerpo alternativo en texto plano
    from_email: Optional[str] = None  # Remitente (si difiere del configurado)
    from_name: Optional[str] = None  # Nombre del remitente
    cc: Optional[List[str]] = None  # Con copia
    bcc: Optional[List[str]] = None  # Con copia oculta
    attachments: Optional[List[Dict[str, Any]]] = None  # Archivos adjuntos
    reply_to: Optional[str] = None  # Correo de respuesta
    headers: Optional[Dict[str, str]] = None  # Headers adicionales

    def validate(self) -> bool:
        """
        Valida que el mensaje tenga los campos mínimos requeridos
        RN09: Validar email válido
        """
        if not self.to or not self.subject:
            return False

        # Validar formato de email (básico)
        import re
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_pattern, self.to):
            return False

        # Debe tener al menos un body
        if not self.body_html and not self.body_text:
            return False

        return True


@dataclass
class EmailResult:
    """
    Resultado del envío de un correo
    Principio ISP: Interfaz segregada para resultados de envío
    """
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    provider: Optional[str] = None
    sent_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resultado a diccionario"""
        return {
            "success": self.success,
            "message_id": self.message_id,
            "error": self.error,
            "provider": self.provider,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None
        }


class EmailAdapter(ABC):
    """
    Interfaz abstracta para adaptadores de correo electrónico
    Patrón Adapter - Define el contrato que todos los adaptadores deben seguir

    Principio OCP (Open/Closed):
    - Abierto para extensión: Se pueden agregar nuevos adaptadores
    - Cerrado para modificación: No se modifica el código existente

    Principio DIP (Dependency Inversion):
    - Las clases de alto nivel dependen de esta abstracción
    - Las implementaciones concretas implementan esta interfaz
    """

    @abstractmethod
    def send_email(self, message: EmailMessage) -> EmailResult:
        """
        Envía un correo electrónico

        Args:
            message: Mensaje de correo a enviar

        Returns:
            EmailResult con el resultado del envío

        Raises:
            EmailSendException: Si ocurre un error al enviar
        """
        pass

    @abstractmethod
    def send_bulk_emails(self, messages: List[EmailMessage]) -> List[EmailResult]:
        """
        Envía múltiples correos electrónicos
        Útil para envíos masivos optimizados

        Args:
            messages: Lista de mensajes a enviar

        Returns:
            Lista de EmailResult con los resultados
        """
        pass

    @abstractmethod
    def verify_connection(self) -> bool:
        """
        Verifica que la conexión con el proveedor funciona correctamente
        Útil para health checks y validación de configuración

        Returns:
            True si la conexión es exitosa, False en caso contrario
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Retorna el nombre del proveedor
        Útil para logging y auditoría

        Returns:
            Nombre del proveedor (ej: "SMTP", "SendGrid", "AWS SES")
        """
        pass


class EmailSendException(Exception):
    """
    Excepción personalizada para errores de envío de correo
    Principio SRP: Manejo específico de errores de email
    """

    def __init__(self, message: str, provider: Optional[str] = None, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.provider = provider
        self.original_error = original_error

    def __str__(self):
        base_msg = super().__str__()
        if self.provider:
            return f"[{self.provider}] {base_msg}"
        return base_msg