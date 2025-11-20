"""
Servicio de Notificaciones - NotificationService
RF-06: Notificaciones por correo
Integra: EmailAdapter, EmailTemplates, SchedulerService, Observer Pattern

Responsabilidades:
- Enviar notificaciones de citas (confirmación, recordatorio, cancelación, reprogramación)
- Integrar con sistema Observer existente
- Gestionar preferencias de notificaciones por usuario
- Coordinar con SchedulerService para recordatorios automáticos
"""

import logging
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.adapters.email_adapter_factory import get_email_adapter
from app.adapters.email_adapter import EmailMessage, EmailResult
from app.services.notifications.email_templates import get_email_template
from app.repositories.user_repository import UserRepository
from app.repositories.pet_repository import PetRepository
from app.repositories.owner_repository import OwnerRepository
from app.repositories.service_repository import ServiceRepository
from app.repositories.appointment_repository import AppointmentRepository
from app.models.notification_settings import NotificationSettings
from app.models.appointment import Appointment, AppointmentStatus

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Servicio de notificaciones
    Implementa integración entre Observer Pattern, Adapter Pattern y plantillas HTML

    Principio SRP: Responsabilidad única de gestionar notificaciones
    Principio DIP: Depende de abstracciones (EmailAdapter) no de implementaciones
    """

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.pet_repo = PetRepository(db)
        self.owner_repo = OwnerRepository(db)
        self.service_repo = ServiceRepository(db)
        self.appointment_repo = AppointmentRepository(db)

        # Obtener adaptador de correo configurado (Factory Pattern)
        self.email_adapter = get_email_adapter()

        logger.info("📧 NotificationService inicializado")

    MSG_DATE_FORMAT = "%d/%m/%Y %H:%M"

    def send_appointment_confirmation(
        self,
        appointment_id: UUID,
        user_id: Optional[UUID] = None
    ) -> bool:
        """
        Envía confirmación de cita agendada
        RF-06: Confirmación al agendar cita

        Args:
            appointment_id: ID de la cita
            user_id: ID del usuario (opcional, para verificar preferencias)

        Returns:
            True si se envió exitosamente
        """
        try:
            # Obtener datos de la cita
            appointment = self.appointment_repo.get_by_id(appointment_id)
            if not appointment:
                logger.error(f"❌ Cita {appointment_id} no encontrada")
                return False

            # Obtener contexto completo
            context = self._build_appointment_context(appointment)

            # Verificar preferencias del usuario
            if user_id:
                settings = self._get_notification_settings(user_id)
                if settings and not settings.should_send_confirmation():
                    logger.info(
                        f"ℹ️ Usuario {user_id} tiene deshabilitadas "
                        f"las confirmaciones de citas"
                    )
                    return False

            # Obtener plantilla
            template = get_email_template("appointment_confirmation")
            email_content = template.render(context)

            # Construir mensaje
            email_message = EmailMessage(
                to=context["propietario_email"],
                subject=email_content["subject"],
                body_html=email_content["body_html"],
                body_text=email_content["body_text"]
            )

            # Enviar
            result = self.email_adapter.send_email(email_message)

            if result.success:
                logger.info(
                    f"✅ Confirmación enviada para cita {appointment_id} "
                    f"a {context['propietario_email']}"
                )

                # Programar recordatorio automático (24h antes)
                self._schedule_reminder(appointment)

                return True

            logger.error(f"❌ Error al enviar confirmación: {result.error}")
            return False

        except Exception as error:
            logger.error(
                f"❌ Error al enviar confirmación de cita: {str(error)}"
            )
            return False

    def send_appointment_reminder(self, appointment_id: UUID) -> bool:
        """
        Envía recordatorio de cita (24h antes)
        RF-06: Recordatorio 24 horas antes

        Args:
            appointment_id: ID de la cita

        Returns:
            True si se envió exitosamente
        """
        try:
            # Obtener datos de la cita
            appointment = self.appointment_repo.get_by_id(appointment_id)
            if not appointment:
                logger.error(f"❌ Cita {appointment_id} no encontrada")
                return False

            # Verificar que la cita no esté cancelada
            if appointment.estado == AppointmentStatus.CANCELADA:
                logger.info(
                    f"ℹ️ Cita {appointment_id} está cancelada, "
                    f"no se envía recordatorio"
                )
                return False

            # Obtener contexto
            context = self._build_appointment_context(appointment)

            # Verificar preferencias del usuario
            mascota = self.pet_repo.get_by_id(appointment.mascota_id)
            if mascota and mascota.propietario_id:
                propietario = self.owner_repo.get_by_id(mascota.propietario_id)
                if propietario and propietario.usuario_id:
                    settings = self._get_notification_settings(propietario.usuario_id)
                    if settings and not settings.should_send_reminder():
                        logger.info(
                            "ℹ️ Usuario tiene deshabilitados los recordatorios"
                        )
                        return False

            # Obtener plantilla
            template = get_email_template("appointment_reminder")
            email_content = template.render(context)

            # Construir mensaje
            email_message = EmailMessage(
                to=context["propietario_email"],
                subject=email_content["subject"],
                body_html=email_content["body_html"],
                body_text=email_content["body_text"]
            )

            # Enviar
            result = self.email_adapter.send_email(email_message)

            if result.success:
                logger.info(
                    f"✅ Recordatorio enviado para cita {appointment_id} "
                    f"a {context['propietario_email']}"
                )
                return True

            logger.error(f"❌ Error al enviar recordatorio: {result.error}")
            return False

        except Exception as error:
            logger.error(
                f"❌ Error al enviar recordatorio de cita: {str(error)}"
            )
            return False

    def send_appointment_reschedule_notification(
        self,
        appointment_id: UUID,
        fecha_anterior: datetime,
        user_id: Optional[UUID] = None
    ) -> bool:
        """
        Envía notificación de reprogramación de cita
        RF-06: Notificación al reprogramar

        Args:
            appointment_id: ID de la cita
            fecha_anterior: Fecha anterior de la cita
            user_id: ID del usuario (opcional)

        Returns:
            True si se envió exitosamente
        """
        try:
            # Obtener datos de la cita
            appointment = self.appointment_repo.get_by_id(appointment_id)
            if not appointment:
                logger.error(f"❌ Cita {appointment_id} no encontrada")
                return False

            # Verificar preferencias
            if user_id:
                settings = self._get_notification_settings(user_id)
                if settings and not settings.should_send_reschedule_notification():
                    logger.info(
                        f"ℹ️ Usuario {user_id} tiene deshabilitadas "
                        f"las notificaciones de reprogramación"
                    )
                    return False

            # Obtener contexto
            context = self._build_appointment_context(appointment)
            context["fecha_anterior"] = fecha_anterior.strftime(self.MSG_DATE_FORMAT)
            context["fecha_nueva"] = appointment.fecha_hora.strftime(self.MSG_DATE_FORMAT)

            # Obtener plantilla
            template = get_email_template("appointment_reschedule")
            email_content = template.render(context)

            # Construir mensaje
            email_message = EmailMessage(
                to=context["propietario_email"],
                subject=email_content["subject"],
                body_html=email_content["body_html"],
                body_text=email_content["body_text"]
            )

            # Enviar
            result = self.email_adapter.send_email(email_message)

            if result.success:
                logger.info(
                    f"✅ Notificación de reprogramación enviada para cita {appointment_id}"
                )

                # Reprogramar recordatorio (24h antes de la nueva fecha)
                self._reschedule_reminder(appointment)

                return True

            logger.error(f"❌ Error al enviar notificación: {result.error}")
            return False

        except Exception as error:
            logger.error(
                f"❌ Error al enviar notificación de reprogramación: {str(error)}"
            )
            return False

    def send_appointment_cancellation_notification(
        self,
        appointment_id: UUID,
        cancelacion_tardia: bool = False,
        user_id: Optional[UUID] = None
    ) -> bool:
        """
        Envía notificación de cancelación de cita
        RF-06: Notificación al cancelar

        Args:
            appointment_id: ID de la cita
            cancelacion_tardia: Si la cancelación fue tardía (<4h)
            user_id: ID del usuario (opcional)

        Returns:
            True si se envió exitosamente
        """
        try:
            # Obtener datos de la cita
            appointment = self.appointment_repo.get_by_id(appointment_id)
            if not appointment:
                logger.error(f"❌ Cita {appointment_id} no encontrada")
                return False

            # Verificar preferencias
            if user_id:
                settings = self._get_notification_settings(user_id)
                if settings and not settings.should_send_cancellation_notification():
                    logger.info(
                        f"ℹ️ Usuario {user_id} tiene deshabilitadas "
                        f"las notificaciones de cancelación"
                    )
                    return False

            # Obtener contexto
            context = self._build_appointment_context(appointment)
            context["cancelacion_tardia"] = cancelacion_tardia

            # Obtener plantilla
            template = get_email_template("appointment_cancellation")
            email_content = template.render(context)

            # Construir mensaje
            email_message = EmailMessage(
                to=context["propietario_email"],
                subject=email_content["subject"],
                body_html=email_content["body_html"],
                body_text=email_content["body_text"]
            )

            # Enviar
            result = self.email_adapter.send_email(email_message)

            if result.success:
                logger.info(
                    f"✅ Notificación de cancelación enviada para cita {appointment_id}"
                )

                # Cancelar recordatorio programado
                self._cancel_reminder(appointment_id)

                return True

            logger.error(f"❌ Error al enviar notificación: {result.error}")
            return False

        except Exception as error:
            logger.error(
                f"❌ Error al enviar notificación de cancelación: {str(error)}"
            )
            return False

    def check_and_send_pending_reminders(self) -> int:
        """
        Verifica y envía recordatorios pendientes
        Llamado periódicamente por SchedulerService

        Returns:
            Número de recordatorios enviados
        """
        sent_count = 0

        try:
            # Obtener citas que necesitan recordatorio (24h antes)
            now = datetime.now(timezone.utc)
            reminder_window_start = now + timedelta(hours=23, minutes=50)
            reminder_window_end = now + timedelta(hours=24, minutes=10)

            # Buscar citas en ventana de recordatorio
            all_appointments = self.appointment_repo.get_by_date_range(
                fecha_inicio=reminder_window_start,
                fecha_fin=reminder_window_end
            )

            # Filtrar solo las confirmadas
            appointments = [
                apt for apt in all_appointments
                if apt.estado == AppointmentStatus.CONFIRMADA
            ]

            logger.info(
                f"🔍 Encontradas {len(appointments)} citas "
                f"que necesitan recordatorio"
            )

            for appointment in appointments:
                # Verificar si ya se envió recordatorio
                # (esto se podría trackear en una tabla de notificaciones enviadas)

                success = self.send_appointment_reminder(appointment.id)
                if success:
                    sent_count += 1

            return sent_count

        except Exception as error:
            logger.error(
                f"❌ Error al verificar recordatorios pendientes: {str(error)}"
            )
            return sent_count

    def _build_appointment_context(self, appointment: Appointment) -> Dict[str, Any]:
        """
        Construye el contexto completo para las plantillas de correo
        Principio SRP: Método privado para construcción de contexto
        """
        # Obtener mascota
        mascota = self.pet_repo.get_by_id(appointment.mascota_id)

        # Obtener propietario
        propietario = None
        if mascota and mascota.propietario_id:
            propietario = self.owner_repo.get_by_id(mascota.propietario_id)

        # Obtener veterinario
        veterinario = self.user_repo.get_by_id(appointment.veterinario_id)

        # Obtener servicio
        servicio = self.service_repo.get_by_id(appointment.servicio_id)

        return {
            "mascota_nombre": mascota.nombre if mascota else "Mascota",
            "propietario_nombre": propietario.nombre if propietario else "Cliente",
            "propietario_email": propietario.correo if propietario else "",
            "veterinario_nombre": veterinario.nombre if veterinario else "Dr./Dra.",
            "servicio_nombre": servicio.nombre if servicio else "Consulta",
            "fecha_hora": appointment.fecha_hora.strftime("%d/%m/%Y %H:%M"),
            "motivo": appointment.motivo or "No especificado"
        }

    def _get_notification_settings(
        self,
        user_id: UUID
    ) -> Optional[NotificationSettings]:
        """
        Obtiene configuración de notificaciones del usuario
        """
        return (self.db.query(NotificationSettings)
                .filter(NotificationSettings.usuario_id == user_id)
                .first())

    def _schedule_reminder(self, appointment: Appointment) -> None:
        """
        Programa recordatorio automático para una cita
        Integración con SchedulerService
        """
        try:
            from app.services.notifications.scheduler_service import get_scheduler_service

            fecha_hora = appointment.fecha_hora
            if fecha_hora.tzinfo is None:
                fecha_hora = fecha_hora.replace(tzinfo=timezone.utc)

            scheduler = get_scheduler_service()
            scheduler.schedule_appointment_reminder(
                appointment.id,
                appointment.fecha_hora,
                notification_hours_before=24
            )

        except Exception as schedule_error:
            logger.error(
                f"❌ Error al programar recordatorio: {str(schedule_error)}"
            )

    def _reschedule_reminder(self, appointment: Appointment) -> None:
        """
        Reprograma recordatorio para una cita modificada
        """
        try:
            from app.services.notifications.scheduler_service import get_scheduler_service

            scheduler = get_scheduler_service()
            scheduler.reschedule_appointment_reminder(
                appointment.id,
                appointment.fecha_hora,
                notification_hours_before=24
            )

        except Exception as schedule_error:
            logger.error(
                f"❌ Error al reprogramar recordatorio: {str(schedule_error)}"
            )

    def _cancel_reminder(self, appointment_id: UUID) -> None:
        """
        Cancela recordatorio programado para una cita
        """
        try:
            from app.services.notifications.scheduler_service import get_scheduler_service

            scheduler = get_scheduler_service()
            scheduler.cancel_appointment_reminder(appointment_id)

        except Exception as cancel_error:
            logger.error(
                f"❌ Error al cancelar recordatorio: {str(cancel_error)}"
            )