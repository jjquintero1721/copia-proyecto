"""
Adaptador SMTP - Implementación concreta del patrón Adapter
RF-06: Notificaciones por correo
Implementa envío de correos usando SMTP (Simple Mail Transfer Protocol)

Este adaptador permite enviar correos usando servidores SMTP como:
- Gmail SMTP
- Outlook/Office365 SMTP
- SendGrid SMTP
- Servidor SMTP personalizado
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
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


class SMTPAdapter(EmailAdapter):
    """
    Adaptador SMTP - Implementación usando smtplib
    Patrón Adapter: Adapta la interfaz SMTP estándar a nuestro sistema

    Configuración mediante variables de entorno:
    - SMTP_HOST: Servidor SMTP
    - SMTP_PORT: Puerto SMTP (587 para TLS, 465 para SSL)
    - SMTP_USER: Usuario SMTP
    - SMTP_PASSWORD: Contraseña SMTP
    - SMTP_FROM: Correo remitente
    - SMTP_FROM_NAME: Nombre del remitente
    - SMTP_USE_TLS: Usar TLS (por defecto True)
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        use_tls: bool = True,
        timeout: int = 30
    ):
        """
        Inicializa el adaptador SMTP

        Principio DIP: Los parámetros se pueden inyectar
        o tomar desde variables de entorno
        """
        self.host = host or os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.port = port or int(os.getenv("SMTP_PORT", "587"))
        self.username = username or os.getenv("SMTP_USER")
        self.password = password or os.getenv("SMTP_PASSWORD")
        self.from_email = from_email or os.getenv("SMTP_FROM")
        self.from_name = from_name or os.getenv("SMTP_FROM_NAME", "Sistema GDCV")
        self.use_tls = use_tls
        self.timeout = timeout

        # Validar configuración mínima
        self._validate_configuration()

        logger.info(
            f"✉️ SMTPAdapter inicializado - Host: {self.host}:{self.port}"
        )

    def _validate_configuration(self) -> None:
        """
        Valida que la configuración SMTP sea correcta
        Principio Fail Fast: Fallar temprano si la configuración es inválida
        """
        if not all([self.host, self.port, self.username,
                    self.password, self.from_email]):
            raise ValueError(
                "Configuración SMTP incompleta. Verifica las variables de entorno: "
                "SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM"
            )

    def send_email(self, message: EmailMessage) -> EmailResult:
        """
        Envía un correo electrónico usando SMTP

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
            # Construir mensaje MIME
            mime_message = self._build_mime_message(message)

            # Enviar usando SMTP
            self._send_via_smtp(mime_message)

            logger.info(f"✅ Correo enviado exitosamente a {message.to}")

            return EmailResult(
                success=True,
                message_id=mime_message.get("Message-ID"),
                provider=self.get_provider_name(),
                sent_at=datetime.now(timezone.utc)
            )

        except smtplib.SMTPException as smtp_error:
            error_msg = f"Error SMTP al enviar correo: {str(smtp_error)}"
            logger.error(f"❌ {error_msg}")
            return EmailResult(
                success=False,
                error=error_msg,
                provider=self.get_provider_name()
            )

        except Exception as general_error:
            error_msg = f"Error inesperado al enviar correo: {str(general_error)}"
            logger.error(f"❌ {error_msg}")
            return EmailResult(
                success=False,
                error=error_msg,
                provider=self.get_provider_name()
            )

    def send_bulk_emails(self, messages: List[EmailMessage]) -> List[EmailResult]:
        """
        Envía múltiples correos usando SMTP
        Optimizado: Reutiliza la conexión SMTP para todos los envíos

        Args:
            messages: Lista de mensajes a enviar

        Returns:
            Lista de EmailResult con los resultados
        """
        results = []

        if not messages:
            return results

        # Optimización: Crear una sola conexión SMTP para todos los envíos
        try:
            server = self._create_smtp_connection()

            for message in messages:
                try:
                    if not message.validate():
                        results.append(EmailResult(
                            success=False,
                            error="Mensaje inválido",
                            provider=self.get_provider_name()
                        ))
                        continue

                    mime_message = self._build_mime_message(message)
                    server.send_message(mime_message)

                    results.append(EmailResult(
                        success=True,
                        message_id=mime_message.get("Message-ID"),
                        provider=self.get_provider_name(),
                        sent_at=datetime.now(timezone.utc)
                    ))

                    logger.info(f"✅ Correo enviado a {message.to}")

                except Exception as email_error:
                    error_msg = f"Error al enviar a {message.to}: {str(email_error)}"
                    logger.error(f"❌ {error_msg}")
                    results.append(EmailResult(
                        success=False,
                        error=error_msg,
                        provider=self.get_provider_name()
                    ))

            server.quit()
            logger.info(f"📧 Envío masivo completado: {len(messages)} correos procesados")

        except Exception as connection_error:
            error_msg = f"Error de conexión SMTP: {str(connection_error)}"
            logger.error(f"❌ {error_msg}")

            # Marcar todos los mensajes como fallidos
            for _ in messages:
                results.append(EmailResult(
                    success=False,
                    error=error_msg,
                    provider=self.get_provider_name()
                ))

        return results

    def verify_connection(self) -> bool:
        """
        Verifica que la conexión SMTP funcione correctamente

        Returns:
            True si la conexión es exitosa
        """
        try:
            server = self._create_smtp_connection()
            server.quit()
            logger.info("✅ Conexión SMTP verificada exitosamente")
            return True

        except Exception as error:
            logger.error(f"❌ Error al verificar conexión SMTP: {str(error)}")
            return False

    def get_provider_name(self) -> str:
        """Retorna el nombre del proveedor"""
        return "SMTP"

    def _build_mime_message(self, message: EmailMessage) -> MIMEMultipart:
        """
        Construye un mensaje MIME desde EmailMessage
        Principio SRP: Responsabilidad única de construir MIME
        """
        mime_message = MIMEMultipart("alternative")

        # Headers básicos
        mime_message["From"] = (f"{message.from_name or self.from_name} "
                                f"<{message.from_email or self.from_email}>")
        mime_message["To"] = message.to
        mime_message["Subject"] = message.subject

        # Headers opcionales
        if message.reply_to:
            mime_message["Reply-To"] = message.reply_to

        if message.cc:
            mime_message["Cc"] = ", ".join(message.cc)

        if message.headers:
            for key, value in message.headers.items():
                mime_message[key] = value

        # Cuerpo del mensaje
        if message.body_text:
            mime_message.attach(MIMEText(message.body_text, "plain", "utf-8"))

        if message.body_html:
            mime_message.attach(MIMEText(message.body_html, "html", "utf-8"))

        # Archivos adjuntos (si existen)
        if message.attachments:
            for attachment in message.attachments:
                self._attach_file(mime_message, attachment)

        return mime_message

    def _attach_file(
        self,
        mime_message: MIMEMultipart,
        attachment: dict
    ) -> None:
        """
        Adjunta un archivo al mensaje MIME
        """
        try:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.get("content", b""))
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {attachment.get('filename', 'file')}"
            )
            mime_message.attach(part)

        except Exception as attach_error:
            logger.warning(f"⚠️ No se pudo adjuntar archivo: {str(attach_error)}")

    def _create_smtp_connection(self):
        """
        Crea y autentica una conexión SMTP
        Principio SRP: Responsabilidad única de crear conexión
        """
        if self.use_tls:
            server = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(self.host, self.port, timeout=self.timeout)

        server.login(self.username, self.password)
        return server

    def _send_via_smtp(self, mime_message: MIMEMultipart) -> None:
        """
        Envía el mensaje MIME usando SMTP
        Principio SRP: Responsabilidad única de enviar
        """
        server = self._create_smtp_connection()
        server.send_message(mime_message)
        server.quit()