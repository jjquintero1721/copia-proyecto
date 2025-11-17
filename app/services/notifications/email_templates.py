"""
Sistema de Plantillas HTML para Correos Electrónicos
RF-06: Notificaciones por correo
Patrón de diseño: Template Method, Strategy

Propósito:
Proporcionar plantillas HTML profesionales y responsivas para:
- Confirmación de citas
- Recordatorios de citas (24h antes)
- Notificaciones de reprogramación
- Notificaciones de cancelación
- Bienvenida de nuevos usuarios

Principio DRY: No repetir código HTML
Principio SRP: Cada plantilla tiene una responsabilidad única
"""

from typing import Dict, Any, Optional
from datetime import datetime
from abc import ABC, abstractmethod


class EmailTemplate(ABC):
    """
    Clase abstracta para plantillas de correo
    Patrón Template Method
    """

    def __init__(self):
        self.brand_name = "Clínica Veterinaria GDCV"
        self.brand_color = "#2563eb"  # Azul principal
        self.support_email = "soporte@gdcv.com"
        self.phone_number = "+57 300 123 4567"

    @abstractmethod
    def get_subject(self, context: Dict[str, Any]) -> str:
        """Retorna el asunto del correo"""
        pass

    @abstractmethod
    def get_body(self, context: Dict[str, Any]) -> str:
        """Retorna el cuerpo HTML del correo"""
        pass

    def render(self, context: Dict[str, Any]) -> Dict[str, str]:
        """
        Renderiza la plantilla completa
        Template Method: Define el esqueleto del algoritmo
        """
        return {
            "subject": self.get_subject(context),
            "body_html": self._wrap_in_layout(self.get_body(context)),
            "body_text": self._generate_text_version(context)
        }

    def _wrap_in_layout(self, content: str) -> str:
        """
        Envuelve el contenido en el layout base
        Principio DRY: Layout común para todos los correos
        """
        return f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.brand_name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333333;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            background-color: {self.brand_color};
            color: #ffffff;
            padding: 30px 20px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .content {{
            padding: 30px 20px;
        }}
        .button {{
            display: inline-block;
            padding: 12px 30px;
            background-color: {self.brand_color};
            color: #ffffff;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
            font-weight: bold;
        }}
        .info-box {{
            background-color: #f8f9fa;
            border-left: 4px solid {self.brand_color};
            padding: 15px;
            margin: 20px 0;
        }}
        .footer {{
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #666666;
        }}
        .footer a {{
            color: {self.brand_color};
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏥 {self.brand_name}</h1>
        </div>
        <div class="content">
            {content}
        </div>
        <div class="footer">
            <p>
                <strong>{self.brand_name}</strong><br>
                📧 {self.support_email} | 📞 {self.phone_number}
            </p>
            <p>
                Este correo fue enviado automáticamente. Por favor no responder.<br>
                Si necesitas ayuda, contáctanos en {self.support_email}
            </p>
        </div>
    </div>
</body>
</html>
"""

    @abstractmethod
    def _generate_text_version(self, context: Dict[str, Any]) -> str:
        """Genera versión en texto plano del correo"""
        pass


class AppointmentConfirmationTemplate(EmailTemplate):
    """
    Plantilla para confirmación de cita agendada
    RF-06: Confirmación de cita
    """

    def get_subject(self, context: Dict[str, Any]) -> str:
        return f"✅ Cita confirmada - {context.get('mascota_nombre', 'Mascota')}"

    def get_body(self, context: Dict[str, Any]) -> str:
        mascota_nombre = context.get("mascota_nombre", "tu mascota")
        propietario_nombre = context.get("propietario_nombre", "Cliente")
        fecha_hora = context.get("fecha_hora", "")
        servicio_nombre = context.get("servicio_nombre", "Consulta")
        veterinario_nombre = context.get("veterinario_nombre", "Dr./Dra.")

        return f"""
            <h2>¡Cita confirmada exitosamente! 🎉</h2>
            <p>Hola <strong>{propietario_nombre}</strong>,</p>
            <p>
                Tu cita para <strong>{mascota_nombre}</strong> ha sido agendada correctamente.
            </p>

            <div class="info-box">
                <h3>📋 Detalles de la cita:</h3>
                <p><strong>🐾 Mascota:</strong> {mascota_nombre}</p>
                <p><strong>🩺 Servicio:</strong> {servicio_nombre}</p>
                <p><strong>👨‍⚕️ Veterinario:</strong> {veterinario_nombre}</p>
                <p><strong>📅 Fecha y hora:</strong> {fecha_hora}</p>
            </div>

            <p>
                <strong>Importante:</strong> Por favor llega 10 minutos antes de tu cita.
                Si necesitas cancelar o reprogramar, hazlo con al menos 4 horas de anticipación.
            </p>

            <p>¡Esperamos verte pronto! 🏥</p>
        """

    def _generate_text_version(self, context: Dict[str, Any]) -> str:
        mascota_nombre = context.get("mascota_nombre", "tu mascota")
        propietario_nombre = context.get("propietario_nombre", "Cliente")
        fecha_hora = context.get("fecha_hora", "")
        servicio_nombre = context.get("servicio_nombre", "Consulta")
        veterinario_nombre = context.get("veterinario_nombre", "Dr./Dra.")

        return f"""
¡Cita confirmada exitosamente!

Hola {propietario_nombre},

Tu cita para {mascota_nombre} ha sido agendada correctamente.

DETALLES DE LA CITA:
- Mascota: {mascota_nombre}
- Servicio: {servicio_nombre}
- Veterinario: {veterinario_nombre}
- Fecha y hora: {fecha_hora}

Importante: Por favor llega 10 minutos antes de tu cita.

{self.brand_name}
{self.support_email} | {self.phone_number}
"""


class AppointmentReminderTemplate(EmailTemplate):
    """
    Plantilla para recordatorio de cita (24h antes)
    RF-06: Recordatorios 24h antes
    """

    def get_subject(self, context: Dict[str, Any]) -> str:
        return f"🔔 Recordatorio de cita mañana - {context.get('mascota_nombre', 'Mascota')}"

    def get_body(self, context: Dict[str, Any]) -> str:
        mascota_nombre = context.get("mascota_nombre", "tu mascota")
        propietario_nombre = context.get("propietario_nombre", "Cliente")
        fecha_hora = context.get("fecha_hora", "")
        servicio_nombre = context.get("servicio_nombre", "Consulta")
        veterinario_nombre = context.get("veterinario_nombre", "Dr./Dra.")

        return f"""
            <h2>🔔 Recordatorio: Cita mañana</h2>
            <p>Hola <strong>{propietario_nombre}</strong>,</p>
            <p>
                Te recordamos que mañana tienes una cita programada para
                <strong>{mascota_nombre}</strong>.
            </p>

            <div class="info-box">
                <h3>📋 Detalles de la cita:</h3>
                <p><strong>🐾 Mascota:</strong> {mascota_nombre}</p>
                <p><strong>🩺 Servicio:</strong> {servicio_nombre}</p>
                <p><strong>👨‍⚕️ Veterinario:</strong> {veterinario_nombre}</p>
                <p><strong>📅 Fecha y hora:</strong> {fecha_hora}</p>
            </div>

            <p>
                <strong>Recomendaciones antes de la cita:</strong>
            </p>
            <ul>
                <li>Llega 10 minutos antes</li>
                <li>Trae la cartilla de vacunación (si aplica)</li>
                <li>Si tu mascota requiere ayuno, no la alimentes 8 horas antes</li>
            </ul>

            <p>
                Si necesitas cancelar o reprogramar, por favor hazlo con anticipación.
            </p>

            <p>¡Te esperamos! 🏥</p>
        """

    def _generate_text_version(self, context: Dict[str, Any]) -> str:
        mascota_nombre = context.get("mascota_nombre", "tu mascota")
        propietario_nombre = context.get("propietario_nombre", "Cliente")
        fecha_hora = context.get("fecha_hora", "")
        servicio_nombre = context.get("servicio_nombre", "Consulta")
        veterinario_nombre = context.get("veterinario_nombre", "Dr./Dra.")

        return f"""
RECORDATORIO: Cita mañana

Hola {propietario_nombre},

Te recordamos que mañana tienes una cita programada para {mascota_nombre}.

DETALLES DE LA CITA:
- Mascota: {mascota_nombre}
- Servicio: {servicio_nombre}
- Veterinario: {veterinario_nombre}
- Fecha y hora: {fecha_hora}

RECOMENDACIONES:
- Llega 10 minutos antes
- Trae la cartilla de vacunación (si aplica)
- Si tu mascota requiere ayuno, no la alimentes 8 horas antes

¡Te esperamos!

{self.brand_name}
{self.support_email} | {self.phone_number}
"""


class AppointmentRescheduleTemplate(EmailTemplate):
    """
    Plantilla para notificación de reprogramación de cita
    RF-06: Notificación de reprogramación
    """

    def get_subject(self, context: Dict[str, Any]) -> str:
        return f"🔄 Cita reprogramada - {context.get('mascota_nombre', 'Mascota')}"

    def get_body(self, context: Dict[str, Any]) -> str:
        mascota_nombre = context.get("mascota_nombre", "tu mascota")
        propietario_nombre = context.get("propietario_nombre", "Cliente")
        fecha_anterior = context.get("fecha_anterior", "")
        fecha_nueva = context.get("fecha_nueva", "")
        servicio_nombre = context.get("servicio_nombre", "Consulta")

        return f"""
            <h2>🔄 Tu cita ha sido reprogramada</h2>
            <p>Hola <strong>{propietario_nombre}</strong>,</p>
            <p>
                La cita de <strong>{mascota_nombre}</strong> ha sido reprogramada.
            </p>

            <div class="info-box">
                <h3>📋 Nueva información:</h3>
                <p><strong>🐾 Mascota:</strong> {mascota_nombre}</p>
                <p><strong>🩺 Servicio:</strong> {servicio_nombre}</p>
                <p><strong>📅 Fecha anterior:</strong> <s>{fecha_anterior}</s></p>
                <p><strong>📅 Nueva fecha:</strong> {fecha_nueva}</p>
            </div>

            <p>
                Por favor confirma que puedes asistir en el nuevo horario.
                Si tienes alguna pregunta, no dudes en contactarnos.
            </p>

            <p>¡Gracias por tu comprensión! 🏥</p>
        """

    def _generate_text_version(self, context: Dict[str, Any]) -> str:
        mascota_nombre = context.get("mascota_nombre", "tu mascota")
        propietario_nombre = context.get("propietario_nombre", "Cliente")
        fecha_anterior = context.get("fecha_anterior", "")
        fecha_nueva = context.get("fecha_nueva", "")

        return f"""
TU CITA HA SIDO REPROGRAMADA

Hola {propietario_nombre},

La cita de {mascota_nombre} ha sido reprogramada.

- Fecha anterior: {fecha_anterior}
- Nueva fecha: {fecha_nueva}

Por favor confirma que puedes asistir en el nuevo horario.

{self.brand_name}
{self.support_email} | {self.phone_number}
"""


class AppointmentCancellationTemplate(EmailTemplate):
    """
    Plantilla para notificación de cancelación de cita
    RF-06: Notificación de cancelación
    """

    def get_subject(self, context: Dict[str, Any]) -> str:
        return f"❌ Cita cancelada - {context.get('mascota_nombre', 'Mascota')}"

    def get_body(self, context: Dict[str, Any]) -> str:
        mascota_nombre = context.get("mascota_nombre", "tu mascota")
        propietario_nombre = context.get("propietario_nombre", "Cliente")
        fecha_hora = context.get("fecha_hora", "")
        cancelacion_tardia = context.get("cancelacion_tardia", False)

        warning_html = ""
        if cancelacion_tardia:
            warning_html = """
                <div style="background-color: #fef2f2; border-left: 4px solid #dc2626; padding: 15px; margin: 20px 0;">
                    <p><strong>⚠️ Cancelación tardía:</strong></p>
                    <p>
                        Esta cita fue cancelada con menos de 4 horas de anticipación.
                        Te recordamos la importancia de cancelar con anticipación.
                    </p>
                </div>
            """

        return f"""
            <h2>❌ Cita cancelada</h2>
            <p>Hola <strong>{propietario_nombre}</strong>,</p>
            <p>
                La cita de <strong>{mascota_nombre}</strong> ha sido cancelada.
            </p>

            <div class="info-box">
                <p><strong>🐾 Mascota:</strong> {mascota_nombre}</p>
                <p><strong>📅 Fecha cancelada:</strong> {fecha_hora}</p>
            </div>

            {warning_html}

            <p>
                Si deseas agendar una nueva cita, puedes contactarnos en cualquier momento.
            </p>

            <p>¡Esperamos verte pronto! 🏥</p>
        """

    def _generate_text_version(self, context: Dict[str, Any]) -> str:
        mascota_nombre = context.get("mascota_nombre", "tu mascota")
        propietario_nombre = context.get("propietario_nombre", "Cliente")
        fecha_hora = context.get("fecha_hora", "")
        cancelacion_tardia = context.get("cancelacion_tardia", False)

        warning_text = ""
        if cancelacion_tardia:
            warning_text = "\n⚠️ CANCELACIÓN TARDÍA: Esta cita fue cancelada con menos de 4 horas de anticipación.\n"

        return f"""
CITA CANCELADA

Hola {propietario_nombre},

La cita de {mascota_nombre} ha sido cancelada.

- Mascota: {mascota_nombre}
- Fecha cancelada: {fecha_hora}
{warning_text}
Si deseas agendar una nueva cita, contáctanos en cualquier momento.

{self.brand_name}
{self.support_email} | {self.phone_number}
"""


# ==================== FUNCIÓN AUXILIAR ====================

def get_email_template(template_name: str) -> EmailTemplate:
    """
    Factory function para obtener plantillas de correo

    Args:
        template_name: Nombre de la plantilla
            - "appointment_confirmation"
            - "appointment_reminder"
            - "appointment_reschedule"
            - "appointment_cancellation"

    Returns:
        EmailTemplate correspondiente

    Raises:
        ValueError: Si la plantilla no existe
    """
    templates = {
        "appointment_confirmation": AppointmentConfirmationTemplate,
        "appointment_reminder": AppointmentReminderTemplate,
        "appointment_reschedule": AppointmentRescheduleTemplate,
        "appointment_cancellation": AppointmentCancellationTemplate
    }

    template_class = templates.get(template_name)
    if not template_class:
        raise ValueError(f"Plantilla '{template_name}' no encontrada")

    return template_class()