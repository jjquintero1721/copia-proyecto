"""
Sistema de Plantillas HTML para Correos Electrónicos (Minimalista Cute - SVG inline)
- Mantiene compatibilidad con implementaciones previas.
- Reemplaza emojis por SVG inline (Gmail-safe).
- Mejora compatibilidad visual: botones y badges consistentes.
- No cambia nombres de clases/funciones ni la factory get_email_template.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from abc import ABC, abstractmethod


def _svg_huellita(size: int = 28, fill: str = "#2563eb") -> str:
    """SVG minimalista de huella (mascota)"""
    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style="display:inline-block; vertical-align:middle;">
      <path d="M7.5 6.5C8.328 6.5 9 5.828 9 5s-.672-1.5-1.5-1.5S6 4.172 6 5s.672 1.5 1.5 1.5z" fill="{fill}"/>
      <path d="M11.5 4.5C12.328 4.5 13 3.828 13 3s-.672-1.5-1.5-1.5S10 2.172 10 3s.672 1.5 1.5 1.5z" fill="{fill}"/>
      <path d="M16.5 6.5C17.328 6.5 18 5.828 18 5s-.672-1.5-1.5-1.5S15 4.172 15 5s.672 1.5 1.5 1.5z" fill="{fill}"/>
      <path d="M12 13.5c-1.657 0-3 1.567-3 3.5 0 1.933 1.343 3.5 3 3.5s3-1.567 3-3.5c0-1.933-1.343-3.5-3-3.5z" fill="{fill}"/>
    </svg>
    """


def _svg_estetoscopio(size: int = 18, fill: str = "#2563eb") -> str:
    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style="display:inline-block; vertical-align:middle;">
      <path d="M20 6a2 2 0 0 0-2 2v3a4 4 0 1 1-8 0V8" stroke="{fill}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
      <path d="M6 18v2a2 2 0 0 0 2 2h0" stroke="{fill}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="19" cy="7" r="1.6" fill="{fill}"/>
    </svg>
    """


def _svg_calendario(size: int = 18, fill: str = "#2563eb") -> str:
    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style="display:inline-block; vertical-align:middle;">
      <rect x="3" y="5" width="18" height="16" rx="2" stroke="{fill}" stroke-width="1.6" fill="none"/>
      <path d="M16 3v4M8 3v4" stroke="{fill}" stroke-width="1.6" stroke-linecap="round"/>
      <path d="M3 11h18" stroke="{fill}" stroke-width="1.6" stroke-linecap="round"/>
    </svg>
    """


def _svg_check(size: int = 20, fill: str = "#10b981") -> str:
    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style="display:inline-block; vertical-align:middle;">
      <circle cx="12" cy="12" r="10" fill="{fill}" />
      <path d="M9 12.5l1.8 1.8L15 10" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
    </svg>
    """


def _svg_x(size: int = 20, fill: str = "#ef4444") -> str:
    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style="display:inline-block; vertical-align:middle;">
      <circle cx="12" cy="12" r="10" fill="{fill}" />
      <path d="M8 8l8 8M16 8l-8 8" stroke="#fff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    """


class EmailTemplate(ABC):
    """
    Clase abstracta para plantillas de correo (Template Method)
    Mantiene la misma API que antes: get_subject, get_body, render, _generate_text_version.
    """

    def __init__(self):
        self.brand_name = "Clínica Veterinaria GDCV"
        self.brand_color = "#2563eb"  # Azul principal
        self.support_email = "soporte@gdcv.com"
        self.phone_number = "+57 300 123 4567"

    MSG_MASCOTA = "tu mascota"
    MSG_DOCTORA = "Dr./Dra."

    @abstractmethod
    def get_subject(self, context: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    def get_body(self, context: Dict[str, Any]) -> str:
        pass

    def render(self, context: Dict[str, Any]) -> Dict[str, str]:
        """
        Retorna dict con keys: subject, body_html, body_text
        """
        subject = self.get_subject(context)
        body_html = self._wrap_in_layout(self.get_body(context))
        body_text = self._generate_text_version(context)
        return {
            "subject": subject,
            "body_html": body_html,
            "body_text": body_text
        }

    def _wrap_in_layout(self, content: str) -> str:
        """
        Layout principal para todas las plantillas.
        Mantengo estilos en head y también uso estilos inline en elementos clave
        para mejorar compatibilidad en clientes como Gmail.
        """
        return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{self.brand_name}</title>
<style>
  body,html {{ margin:0; padding:0; width:100%; background:#f6f8fb; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color:#333; }}
  .email-wrapper {{ width:100%; padding:24px 0; display:flex; justify-content:center; }}
  .email-card {{ width:100%; max-width:640px; background:#fff; border-radius:12px; box-shadow:0 6px 20px rgba(16,24,40,0.06); overflow:hidden; }}
  .header {{ background: {self.brand_color}; color:#fff; padding:20px 24px; text-align:center; }}
  .brand-title {{ font-size:20px; font-weight:700; margin:0; }}
  .subhead {{ font-size:13px; opacity:0.95; margin-top:6px; }}

  .content {{ padding:22px 24px; font-size:15px; line-height:1.6; color:#444; }}
  .hero {{ display:flex; align-items:center; gap:14px; margin-bottom:14px; }}
  .badge {{ width:56px; height:56px; border-radius:12px; display:flex; align-items:center; justify-content:center; background:#f3f6fb; }}

  .info-box {{ background:#f8fafc; border-left:4px solid {self.brand_color}; padding:14px; margin:14px 0; border-radius:8px; }}
  .info-row {{ display:flex; gap:10px; align-items:center; margin:8px 0; font-size:14px; color:#111827; }}
  .muted {{ color:#6b7280; font-size:13px; }}

  .cta {{ display:inline-block; padding:10px 16px; border-radius:8px; text-decoration:none; color:#fff; background:{self.brand_color}; font-weight:600; }}

  .footer {{ background:#f3f4f6; padding:16px 18px; text-align:center; font-size:13px; color:#6b7280; }}

  @media (max-width:480px) {{
    .content {{ padding:18px; font-size:15px; }}
    .header {{ padding:18px; }}
  }}
</style>
</head>
<body>
  <div class="email-wrapper">
    <div class="email-card">
      <div class="header" style="background:{self.brand_color};">
        <div class="brand-title">🏥 {self.brand_name}</div>
        <div class="subhead" style="margin-top:6px; font-size:13px;">Cuidado con cariño · {self.support_email}</div>
      </div>

      <div class="content">
        {content}
      </div>

      <div class="footer">
        <p style="margin:0;">{self.brand_name} · <a href="mailto:{self.support_email}" style="color:{self.brand_color}; text-decoration:none;">{self.support_email}</a></p>
        <p class="muted" style="margin:6px 0 0 0;">Teléfono: {self.phone_number} · Este correo es automático. No respondas directamente.</p>
      </div>
    </div>
  </div>
</body>
</html>"""

    @abstractmethod
    def _generate_text_version(self, context: Dict[str, Any]) -> str:
        pass


# -------------------- Plantillas específicas --------------------


class AppointmentConfirmationTemplate(EmailTemplate):
    """
    Plantilla para confirmación de cita agendada (SVG minimalista)
    """

    def get_subject(self, context: Dict[str, Any]) -> str:
        return f"✅ Cita confirmada - {context.get('mascota_nombre', 'Mascota')}"

    def get_body(self, context: Dict[str, Any]) -> str:
        mascota_nombre = context.get("mascota_nombre", self.MSG_MASCOTA)
        propietario_nombre = context.get("propietario_nombre", "Cliente")
        fecha_hora = context.get("fecha_hora", "")
        servicio_nombre = context.get("servicio_nombre", "Consulta")
        veterinario_nombre = context.get("veterinario_nombre", self.MSG_DOCTORA)

        # Badge con SVG check minimalista + contenido con íconos SVG inline
        return f"""
          <div class="hero" style="margin-bottom:16px;">
            <div class="badge" style="background:#e6f7ef;">
              {_svg_check(size=32, fill='#10b981')}
            </div>
            <div>
              <h2 style="margin:0 0 6px 0; font-size:18px;">¡Tu cita está confirmada!</h2>
              <p class="muted" style="margin:0;">Gracias por confiar en nosotros, <strong>{propietario_nombre}</strong>.</p>
            </div>
          </div>

          <div class="info-box" style="margin-top:6px;">
            <h3 style="margin:0 0 8px 0; font-size:15px;">Detalles de la cita</h3>

            <div class="info-row" style="margin-top:10px;">
              {_svg_huellita(size=18, fill='#2563eb')}
              <div style="font-size:14px;"><strong>Mascota:</strong>&nbsp;{mascota_nombre}</div>
            </div>

            <div class="info-row">
              {_svg_estetoscopio(size=18, fill='#2563eb')}
              <div style="font-size:14px;"><strong>Servicio:</strong>&nbsp;{servicio_nombre}</div>
            </div>

            <div class="info-row">
              <span style="width:18px;height:18px;display:inline-block;vertical-align:middle;">{_svg_huellita(size=0)}</span>
              <div style="font-size:14px;"><strong>Veterinario:</strong>&nbsp;{veterinario_nombre}</div>
            </div>

            <div class="info-row">
              {_svg_calendario(size=18, fill='#2563eb')}
              <div style="font-size:14px;"><strong>Fecha y hora:</strong>&nbsp;{fecha_hora}</div>
            </div>
          </div>

          <p style="margin-top:12px; color:#374151;">Por favor llega 10 minutos antes. Si necesitas cambiar la cita, puedes hacerlo desde tu cuenta o contactarnos.</p>

          <a href="#" class="cta" style="display:inline-block; margin-top:10px;">Ver cita</a>
        """

    def _generate_text_version(self, context: Dict[str, Any]) -> str:
        mascota_nombre = context.get("mascota_nombre", self.MSG_MASCOTA)
        propietario_nombre = context.get("propietario_nombre", "Cliente")
        fecha_hora = context.get("fecha_hora", "")
        servicio_nombre = context.get("servicio_nombre", "Consulta")
        veterinario_nombre = context.get("veterinario_nombre", self.MSG_DOCTORA)

        return f"""¡Tu cita está confirmada!

Hola {propietario_nombre},

Tu cita para {mascota_nombre} ha sido confirmada.

DETALLES:
- Mascota: {mascota_nombre}
- Servicio: {servicio_nombre}
- Veterinario: {veterinario_nombre}
- Fecha y hora: {fecha_hora}

Por favor llega 10 minutos antes.

{self.brand_name}
{self.support_email} | {self.phone_number}
"""


class AppointmentReminderTemplate(EmailTemplate):
    """
    Recordatorio 24h antes (SVG minimalista)
    """

    def get_subject(self, context: Dict[str, Any]) -> str:
        return f"🔔 Recordatorio: tu cita es mañana - {context.get('mascota_nombre', 'Mascota')}"

    def get_body(self, context: Dict[str, Any]) -> str:
        mascota_nombre = context.get("mascota_nombre", self.MSG_MASCOTA)
        propietario_nombre = context.get("propietario_nombre", "Cliente")
        fecha_hora = context.get("fecha_hora", "")
        servicio_nombre = context.get("servicio_nombre", "Consulta")
        veterinario_nombre = context.get("veterinario_nombre", self.MSG_DOCTORA)

        return f"""
          <div class="hero" style="margin-bottom:12px;">
            <div class="badge" style="background:#fff7ed;">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                <path d="M12 6v6l4 2" stroke="#f59e0b" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
                <circle cx="12" cy="12" r="9" stroke="#f59e0b" stroke-width="1.6" fill="none"/>
              </svg>
            </div>
            <div>
              <h2 style="margin:0 0 6px 0; font-size:18px;">Recordatorio: Cita mañana</h2>
              <p class="muted" style="margin:0;">Hola <strong>{propietario_nombre}</strong>, te esperamos mañana.</p>
            </div>
          </div>

          <div class="info-box">
            <h3 style="margin:0 0 8px 0; font-size:15px;">Detalles</h3>

            <div class="info-row" style="margin-top:10px;">
              {_svg_huellita(size=18, fill='#2563eb')}
              <div style="font-size:14px;"><strong>Mascota:</strong>&nbsp;{mascota_nombre}</div>
            </div>

            <div class="info-row">
              {_svg_estetoscopio(size=18, fill='#2563eb')}
              <div style="font-size:14px;"><strong>Servicio:</strong>&nbsp;{servicio_nombre}</div>
            </div>

            <div class="info-row">
              {_svg_calendario(size=18, fill='#2563eb')}
              <div style="font-size:14px;"><strong>Fecha y hora:</strong>&nbsp;{fecha_hora}</div>
            </div>
          </div>

          <p style="margin-top:10px;"><strong>Recomendaciones:</strong></p>
          <ul style="margin-top:6px; padding-left:18px;">
            <li>Llega 10 minutos antes</li>
            <li>Trae cartilla de vacunación si aplica</li>
            <li>Si requiere ayuno, no alimentes 8 horas antes</li>
          </ul>

          <a href="#" class="cta" style="display:inline-block; margin-top:10px;">Ver instrucciones</a>
        """

    def _generate_text_version(self, context: Dict[str, Any]) -> str:
        mascota_nombre = context.get("mascota_nombre", self.MSG_MASCOTA)
        propietario_nombre = context.get("propietario_nombre", "Cliente")
        fecha_hora = context.get("fecha_hora", "")

        return f"""Recordatorio: Cita mañana

Hola {propietario_nombre},

Te recordamos la cita de {mascota_nombre}.

DETALLES:
- Mascota: {mascota_nombre}
- Fecha y hora: {fecha_hora}

Recomendaciones:
- Llega 10 minutos antes
- Trae cartilla de vacunación si aplica
- Si requiere ayuno, no alimentes 8 horas antes

{self.brand_name}
{self.support_email} | {self.phone_number}
"""


class AppointmentRescheduleTemplate(EmailTemplate):
    """
    Notificación de reprogramación (SVG minimalista)
    """

    def get_subject(self, context: Dict[str, Any]) -> str:
        return f"🔄 Cita reprogramada - {context.get('mascota_nombre', 'Mascota')}"

    def get_body(self, context: Dict[str, Any]) -> str:
        mascota_nombre = context.get("mascota_nombre", self.MSG_MASCOTA)
        propietario_nombre = context.get("propietario_nombre", "Cliente")
        fecha_anterior = context.get("fecha_anterior", "")
        fecha_nueva = context.get("fecha_nueva", "")
        servicio_nombre = context.get("servicio_nombre", "Consulta")

        return f"""
          <div class="hero" style="margin-bottom:12px;">
            <div class="badge" style="background:#eef2ff;">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                <path d="M21 12a9 9 0 1 0-2.6 6.02L21 21" stroke="#7c3aed" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M21 7v5h-5" stroke="#7c3aed" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div>
              <h2 style="margin:0 0 6px 0; font-size:18px;">Cita reprogramada</h2>
              <p class="muted" style="margin:0;">Hola <strong>{propietario_nombre}</strong>, hemos modificado tu cita.</p>
            </div>
          </div>

          <div class="info-box">
            <h3 style="margin:0 0 8px 0; font-size:15px;">Nueva información</h3>

            <div class="info-row" style="margin-top:10px;">
              {_svg_huellita(size=18, fill='#2563eb')}
              <div style="font-size:14px;"><strong>Mascota:</strong>&nbsp;{mascota_nombre}</div>
            </div>

            <div class="info-row">
              {_svg_calendario(size=18, fill='#2563eb')}
              <div style="font-size:14px;"><strong>Fecha anterior:</strong>&nbsp;<s>{fecha_anterior}</s></div>
            </div>

            <div class="info-row">
              {_svg_calendario(size=18, fill='#2563eb')}
              <div style="font-size:14px;"><strong>Nueva fecha:</strong>&nbsp;{fecha_nueva}</div>
            </div>
          </div>

          <p style="margin-top:10px;">Por favor confirma que puedes asistir en el nuevo horario. Si necesitas ayuda, contáctanos.</p>

          <a href="#" class="cta" style="display:inline-block; margin-top:10px;">Confirmar asistencia</a>
        """

    def _generate_text_version(self, context: Dict[str, Any]) -> str:
        mascota_nombre = context.get("mascota_nombre", self.MSG_MASCOTA)
        propietario_nombre = context.get("propietario_nombre", "Cliente")
        fecha_anterior = context.get("fecha_anterior", "")
        fecha_nueva = context.get("fecha_nueva", "")

        return f"""Tu cita ha sido reprogramada

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
    Notificación de cancelación (SVG minimalista)
    """

    def get_subject(self, context: Dict[str, Any]) -> str:
        return f"❌ Cita cancelada - {context.get('mascota_nombre', 'Mascota')}"

    def get_body(self, context: Dict[str, Any]) -> str:
        mascota_nombre = context.get("mascota_nombre", self.MSG_MASCOTA)
        propietario_nombre = context.get("propietario_nombre", "Cliente")
        fecha_hora = context.get("fecha_hora", "")
        cancelacion_tardia = context.get("cancelacion_tardia", False)

        warning_html = ""
        if cancelacion_tardia:
            warning_html = """
              <div style="background:#fff1f2; border-left:4px solid #ef4444; padding:12px; margin:12px 0; border-radius:6px;">
                <p style="margin:0; color:#7f1d1d;"><strong>⚠️ Cancelación tardía:</strong> Esta cancelación ocurrió con menos de 4 horas de anticipación.</p>
              </div>
            """

        return f"""
          <div class="hero" style="margin-bottom:12px;">
            <div class="badge" style="background:#fff1f0;">
              {_svg_x(size=32, fill='#ef4444')}
            </div>
            <div>
              <h2 style="margin:0 0 6px 0; font-size:18px;">Cita cancelada</h2>
              <p class="muted" style="margin:0;">Hola <strong>{propietario_nombre}</strong>, la cita ha sido cancelada.</p>
            </div>
          </div>

          <div class="info-box">
            <div class="info-row" style="margin-top:6px;">
              {_svg_huellita(size=18, fill='#2563eb')}
              <div style="font-size:14px;"><strong>Mascota:</strong>&nbsp;{mascota_nombre}</div>
            </div>

            <div class="info-row">
              {_svg_calendario(size=18, fill='#2563eb')}
              <div style="font-size:14px;"><strong>Fecha cancelada:</strong>&nbsp;{fecha_hora}</div>
            </div>
          </div>

          {warning_html}

          <p style="margin-top:10px;">Si deseas agendar una nueva cita, estamos para ayudarte.</p>

          <a href="#" class="cta" style="display:inline-block; margin-top:10px;">Agendar nueva cita</a>
        """

    def _generate_text_version(self, context: Dict[str, Any]) -> str:
        mascota_nombre = context.get("mascota_nombre", self.MSG_MASCOTA)
        propietario_nombre = context.get("propietario_nombre", "Cliente")
        fecha_hora = context.get("fecha_hora", "")
        cancelacion_tardia = context.get("cancelacion_tardia", False)

        warning_text = ""
        if cancelacion_tardia:
            warning_text = "\n⚠️ CANCELACIÓN TARDÍA: Esta cancelación ocurrió con menos de 4 horas de anticipación.\n"

        return f"""Cita cancelada

Hola {propietario_nombre},

La cita de {mascota_nombre} ha sido cancelada.
- Fecha cancelada: {fecha_hora}
{warning_text}
Si deseas agendar una nueva cita, contáctanos.

{self.brand_name}
{self.support_email} | {self.phone_number}
"""


# -------------------- Plantillas adicionales (no invasivas) --------------------


class AppointmentStartedTemplate(EmailTemplate):
    """
    Notificación: la cita ha sido iniciada
    """

    def get_subject(self, context: Dict[str, Any]) -> str:
        return f"▶️ Cita iniciada - {context.get('mascota_nombre', 'Mascota')}"

    def get_body(self, context: Dict[str, Any]) -> str:
        mascota_nombre = context.get("mascota_nombre", self.MSG_MASCOTA)
        propietario_nombre = context.get("propietario_nombre", "Cliente")
        fecha_hora = context.get("fecha_hora", "")
        veterinario_nombre = context.get("veterinario_nombre", self.MSG_DOCTORA)

        return f"""
          <div class="hero" style="margin-bottom:12px;">
            <div class="badge" style="background:#ecfeff;">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                <path d="M5 12h14" stroke="#06b6d4" stroke-width="1.6" stroke-linecap="round"/>
                <path d="M12 5v14" stroke="#06b6d4" stroke-width="1.6" stroke-linecap="round"/>
              </svg>
            </div>
            <div>
              <h2 style="margin:0 0 6px 0; font-size:18px;">Tu cita ha comenzado</h2>
              <p class="muted" style="margin:0;">Hola <strong>{propietario_nombre}</strong>, la atención ha comenzado.</p>
            </div>
          </div>

          <div class="info-box">
            <div class="info-row" style="margin-top:6px;">
              {_svg_huellita(size=18, fill='#2563eb')}
              <div style="font-size:14px;"><strong>Mascota:</strong>&nbsp;{mascota_nombre}</div>
            </div>
            <div class="info-row">
              {_svg_calendario(size=18, fill='#2563eb')}
              <div style="font-size:14px;"><strong>Hora:</strong>&nbsp;{fecha_hora}</div>
            </div>
          </div>
        """

    def _generate_text_version(self, context: Dict[str, Any]) -> str:
        mascota_nombre = context.get("mascota_nombre", self.MSG_MASCOTA)
        propietario_nombre = context.get("propietario_nombre", "Cliente")
        fecha_hora = context.get("fecha_hora", "")

        return f"""Cita iniciada

Hola {propietario_nombre},

La atención para {mascota_nombre} ha comenzado a las {fecha_hora}.

{self.brand_name}
{self.support_email} | {self.phone_number}
"""


class AppointmentCompletedTemplate(EmailTemplate):
    """
    Notificación: la cita fue completada
    """

    def get_subject(self, context: Dict[str, Any]) -> str:
        return f"✅ Cita completada - {context.get('mascota_nombre', 'Mascota')}"

    def get_body(self, context: Dict[str, Any]) -> str:
        mascota_nombre = context.get("mascota_nombre", self.MSG_MASCOTA)
        propietario_nombre = context.get("propietario_nombre", "Cliente")
        fecha_hora = context.get("fecha_hora", "")
        resumen = context.get("resumen", context.get("motivo", "Consulta completada"))

        return f"""
          <div class="hero" style="margin-bottom:12px;">
            <div class="badge" style="background:#ecfdf5;">
              {_svg_check(size=32, fill='#10b981')}
            </div>
            <div>
              <h2 style="margin:0 0 6px 0; font-size:18px;">Cita completada</h2>
              <p class="muted" style="margin:0;">Hola <strong>{propietario_nombre}</strong>, la atención ha finalizado.</p>
            </div>
          </div>

          <div class="info-box">
            <div class="info-row" style="margin-top:6px;">
              {_svg_huellita(size=18, fill='#2563eb')}
              <div style="font-size:14px;"><strong>Mascota:</strong>&nbsp;{mascota_nombre}</div>
            </div>

            <div class="info-row" style="margin-top:6px;">
              {_svg_calendario(size=18, fill='#2563eb')}
              <div style="font-size:14px;"><strong>Fecha:</strong>&nbsp;{fecha_hora}</div>
            </div>

            <div style="margin-top:8px; font-size:14px;"><strong>Resumen:</strong>&nbsp;{resumen}</div>
          </div>

          <p style="margin-top:10px;">Si lo deseas, puedes solicitar el historial o próximas recomendaciones desde tu cuenta.</p>

          <a href="#" class="cta" style="display:inline-block; margin-top:10px;">Ver historial</a>
        """

    def _generate_text_version(self, context: Dict[str, Any]) -> str:
        mascota_nombre = context.get("mascota_nombre", self.MSG_MASCOTA)
        propietario_nombre = context.get("propietario_nombre", "Cliente")
        fecha_hora = context.get("fecha_hora", "")
        resumen = context.get("resumen", context.get("motivo", "Consulta completada"))

        return f"""Cita completada

Hola {propietario_nombre},

La atención de {mascota_nombre} ha finalizado.
Fecha: {fecha_hora}
Resumen: {resumen}

{self.brand_name}
{self.support_email} | {self.phone_number}
"""


# ==================== FUNCIÓN AUXILIAR / FACTORY ====================

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
        # Plantillas originales (mantener exactamente las keys para compatibilidad)
        "appointment_confirmation": AppointmentConfirmationTemplate,
        "appointment_reminder": AppointmentReminderTemplate,
        "appointment_reschedule": AppointmentRescheduleTemplate,
        "appointment_cancellation": AppointmentCancellationTemplate,

        # Plantillas adicionales (opcionalmente utilizadas)
        "appointment_started": AppointmentStartedTemplate,
        "appointment_completed": AppointmentCompletedTemplate,
    }

    template_class = templates.get(template_name)
    if not template_class:
        raise ValueError(f"Plantilla '{template_name}' no encontrada")

    return template_class()