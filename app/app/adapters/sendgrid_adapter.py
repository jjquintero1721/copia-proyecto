"""
Adaptador SendGrid - Implementación cloud del patrón Adapter
RF-06: Notificaciones por correo
Implementa envío de correos usando SendGrid API

SendGrid es un servicio cloud de envío de correos masivos con:
- Alta tasa de entrega
- Análisis detallados
- Validación de emails
- Plantillas prediseñadas
- API REST moderna

Requiere instalación: pip install sendgrid
"""

import logging
from typing import List, Optional
from datetime import datetime, timezone
import os

from app.adapters.email_adapter import (
    EmailAdapter,
    EmailMessage,
    EmailResult,
    EmailSendException
)

logger = logging.getLogger(__name__)

# Importación condicional de SendGrid
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import (
        Mail,
        Email,
        To,
        Content,
        Attachment,
        FileContent,
        FileName,
        FileType,
        Disposition
    )
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    logger.warning(
        "⚠️ SendGrid no está instalado. "
        "Instala con: pip install sendgrid"
    )


class SendGridAdapter(EmailAdapter):
    """
    Adaptador SendGrid - Implementación usando SendGrid API v3
    Patrón Adapter: Adapta la API de SendGrid a nuestro sistema

    Configuración mediante variables de entorno:
    - SENDGRID_API_KEY: API Key de SendGrid
    - SENDGRID_FROM_EMAIL: Correo remitente verificado
    - SENDGRID_FROM_NAME: Nombre del remitente

    Ventajas sobre SMTP:
    - Mayor tasa de entrega
    - Análisis de estadísticas
    - Mejor rendimiento en envíos masivos
    - Sin límites de envío por conexión
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ):
        """
        Inicializa el adaptador SendGrid

        Args:
            api_key: API Key de SendGrid
            from_email: Correo remitente verificado en SendGrid
            from_name: Nombre del remitente
        """
        if not SENDGRID_AVAILABLE:
            raise ImportError(
                "SendGrid no está disponible. "
                "Instala con: pip install sendgrid"
            )

        self.api_key = api_key or os.getenv("SENDGRID_API_KEY")
        self.from_email = from_email or os.getenv("SENDGRID_FROM_EMAIL")
        self.from_name = from_name or os.getenv("SENDGRID_FROM_NAME", "Sistema GDCV")

        self._validate_configuration()

        # Crear cliente SendGrid
        self.client = SendGridAPIClient(self.api_key)

        logger.info("✉️ SendGridAdapter inicializado correctamente")

    def _validate_configuration(self) -> None:
        """
        Valida que la configuración de SendGrid sea correcta
        Principio Fail Fast
        """
        if not self.api_key:
            raise ValueError(
                "API Key de SendGrid no configurada. "
                "Verifica la variable SENDGRID_API_KEY"
            )

        if not self.from_email:
            raise ValueError(
                "Email remitente no configurado. "
                "Verifica la variable SENDGRID_FROM_EMAIL"
            )

    def send_email(self, message: EmailMessage) -> EmailResult:
        """
        Envía un correo electrónico usando SendGrid API

        Args:
            message: Mensaje de correo a enviar

        Returns:
            EmailResult con el resultado del envío
        """
        # Validar mensaje
        if not message.validate():
            return EmailResult(
                success=False,
                error="Mensaje de correo inválido",
                provider=self.get_provider_name()
            )

        try:
            # Construir mensaje SendGrid
            sg_message = self._build_sendgrid_message(message)

            # Enviar usando API
            response = self.client.send(sg_message)

            # SendGrid retorna 202 Accepted para envíos exitosos
            if response.status_code in [200, 201, 202]:
                logger.info(f"✅ Correo enviado exitosamente a {message.to}")

                return EmailResult(
                    success=True,
                    message_id=response.headers.get("X-Message-Id"),
                    provider=self.get_provider_name(),
                    sent_at=datetime.now(timezone.utc)
                )

            # Otro código de estado
            error_msg = f"SendGrid retornó código {response.status_code}: {response.body}"
            logger.error(f"❌ {error_msg}")

            return EmailResult(
                success=False,
                error=error_msg,
                provider=self.get_provider_name()
            )

        except Exception as error:
            error_msg = f"Error al enviar correo con SendGrid: {str(error)}"
            logger.error(f"❌ {error_msg}")

            return EmailResult(
                success=False,
                error=error_msg,
                provider=self.get_provider_name()
            )

    def send_bulk_emails(self, messages: List[EmailMessage]) -> List[EmailResult]:
        """
        Envía múltiples correos usando SendGrid
        SendGrid optimiza automáticamente los envíos masivos

        Args:
            messages: Lista de mensajes a enviar

        Returns:
            Lista de EmailResult con los resultados
        """
        results = []

        if not messages:
            return results

        logger.info(f"📧 Iniciando envío masivo de {len(messages)} correos con SendGrid")

        for message in messages:
            result = self.send_email(message)
            results.append(result)

        successful = sum(1 for r in results if r.success)
        logger.info(
            f"📊 Envío masivo completado: "
            f"{successful}/{len(messages)} exitosos"
        )

        return results

    def verify_connection(self) -> bool:
        """
        Verifica que la API Key de SendGrid sea válida

        Returns:
            True si la API Key funciona
        """
        try:
            # Endpoint de verificación de SendGrid
            response = self.client.client.api_keys._(self.api_key.split('.')[-1]).get()

            if response.status_code == 200:
                logger.info("✅ Conexión con SendGrid verificada exitosamente")
                return True

            logger.warning(f"⚠️ SendGrid retornó código {response.status_code}")
            return False

        except Exception as error:
            logger.error(f"❌ Error al verificar conexión SendGrid: {str(error)}")
            return False

    def get_provider_name(self) -> str:
        """Retorna el nombre del proveedor"""
        return "SendGrid"

    def _build_sendgrid_message(self, message: EmailMessage) -> Mail:
        """
        Construye un mensaje Mail de SendGrid desde EmailMessage
        SRP: esta función solo orquesta, delega pasos complejos
        """
        from_email = self._build_from_email(message)
        to_email = To(message.to)
        content = self._build_main_content(message)

        sg_message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=message.subject,
            html_content=content,
        )

        self._add_optional_contents(sg_message, message)
        self._add_recipients(sg_message, message)
        self._add_headers(sg_message, message)
        self._add_attachments_if_any(sg_message, message)

        return sg_message

    def _build_from_email(self, message: EmailMessage) -> Email:
        return Email(
            message.from_email or self.from_email,
            message.from_name or self.from_name
        )

    def _build_main_content(self, message: EmailMessage) -> Content:
        body = message.body_html or message.body_text
        return Content("text/html", body)

    def _add_optional_contents(self, sg_message: Mail, message: EmailMessage):
        if message.body_text and message.body_html:
            sg_message.add_content(Content("text/plain", message.body_text))

        if message.reply_to:
            sg_message.reply_to = Email(message.reply_to)

    def _add_recipients(self, sg_message: Mail, message: EmailMessage):
        if message.cc:
            for cc in message.cc:
                sg_message.add_cc(cc)

        if message.bcc:
            for bcc in message.bcc:
                sg_message.add_bcc(bcc)

    def _add_headers(self, sg_message: Mail, message: EmailMessage):
        if message.headers:
            for key, value in message.headers.items():
                sg_message.add_header(key, value)

    def _add_attachments_if_any(self, sg_message: Mail, message: EmailMessage):
        if message.attachments:
            for attachment in message.attachments:
                self._add_attachment(sg_message, attachment)

    def _add_attachment(self, sg_message: Mail, attachment: dict) -> None:
        """
        Añade un archivo adjunto al mensaje de SendGrid
        """
        try:
            sg_attachment = Attachment()
            sg_attachment.file_content = FileContent(attachment.get("content_base64", ""))
            sg_attachment.file_name = FileName(attachment.get("filename", "file"))
            sg_attachment.file_type = FileType(attachment.get("content_type", "application/octet-stream"))
            sg_attachment.disposition = Disposition("attachment")

            sg_message.add_attachment(sg_attachment)

        except Exception as attach_error:
            logger.warning(f"⚠️ No se pudo adjuntar archivo: {str(attach_error)}")