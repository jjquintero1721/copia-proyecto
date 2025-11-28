"""
Servicio de Programación de Tareas - SchedulerService
RF-06: Notificaciones por correo - Recordatorios 24h antes
Usa APScheduler para tareas programadas

Funcionalidades:
- Recordatorios automáticos de citas 24h antes
- Verificación periódica de citas próximas
- Limpieza de tareas caducadas
- Gestión de trabajos programados

Requiere instalación: pip install apscheduler
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Importación condicional de APScheduler
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.date import DateTrigger
    from apscheduler.jobstores.memory import MemoryJobStore
    from apscheduler.executors.pool import ThreadPoolExecutor
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    logger.warning(
    )


class SchedulerService:
    """
    Servicio de programación de tareas usando APScheduler
    Patrón Singleton: Una sola instancia del scheduler en toda la aplicación

    Principio SRP: Responsabilidad única de programar y ejecutar tareas
    Principio OCP: Abierto para extensión (nuevos tipos de tareas)
    """

    _instance: Optional['SchedulerService'] = None
    _scheduler: Optional['BackgroundScheduler'] = None

    def __new__(cls):
        """
        Implementa Singleton Pattern
        Solo una instancia del scheduler en toda la aplicación
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Inicializa el scheduler si no está inicializado"""
        if not APSCHEDULER_AVAILABLE:
            logger.error(
            )
            return

        if self._scheduler is None:
            self._initialize_scheduler()

    def _initialize_scheduler(self) -> None:
        """
        Inicializa y configura APScheduler
        Principio SRP: Método privado para configuración
        """
        # Configurar job stores y executors
        jobstores = {
            'default': MemoryJobStore()
        }

        executors = {
            'default': ThreadPoolExecutor(max_workers=10)
        }

        job_defaults = {
            'coalesce': False,  # No fusionar trabajos atrasados
            'max_instances': 3,  # Máximo 3 instancias del mismo trabajo
            'misfire_grace_time': 3600  # 1 hora de gracia para trabajos perdidos
        }

        # Crear scheduler
        self._scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='UTC'
        )

        logger.info("📅 SchedulerService inicializado correctamente")

    def start(self) -> None:
        """
        Inicia el scheduler
        Debe llamarse al iniciar la aplicación
        """
        if not APSCHEDULER_AVAILABLE or self._scheduler is None:
            logger.warning("⚠️ Scheduler no disponible, no se puede iniciar")
            return

        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("✅ Scheduler iniciado exitosamente")

            # Programar verificación periódica de recordatorios
            self._schedule_periodic_reminder_check()

    def shutdown(self) -> None:
        """
        Detiene el scheduler
        Debe llamarse al cerrar la aplicación
        """
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("🛑 Scheduler detenido")

    def _schedule_periodic_reminder_check(self) -> None:
        """
        Programa verificación periódica de recordatorios
        Se ejecuta cada hora para verificar citas que necesitan recordatorio

        Principio: Verificación proactiva en lugar de reactiva
        """
        # Verificar cada hora
        self._scheduler.add_job(
            func=self._check_and_send_reminders,
            trigger=CronTrigger(minute=0),  # Cada hora en punto
            id='periodic_reminder_check',
            name='Verificación periódica de recordatorios',
            replace_existing=True
        )

        logger.info("⏰ Verificación periódica de recordatorios programada")

    def schedule_appointment_reminder(
        self,
        appointment_id: UUID,
        appointment_datetime: datetime,
        notification_hours_before: int = 24
    ) -> Optional[str]:
        """
        Programa un recordatorio para una cita específica

        Args:
            appointment_id: ID de la cita
            appointment_datetime: Fecha y hora de la cita
            notification_hours_before: Horas antes para enviar recordatorio

        Returns:
            Job ID si se programó exitosamente, None si falló
        """
        if not APSCHEDULER_AVAILABLE or self._scheduler is None:
            logger.warning("⚠️ Scheduler no disponible")
            return None

        # Calcular cuándo enviar el recordatorio
        if appointment_datetime.tzinfo is None:
            appointment_datetime = appointment_datetime.replace(tzinfo=timezone.utc)

        reminder_time = appointment_datetime - timedelta(hours=notification_hours_before)
        # No programar si el recordatorio ya pasó
        now = datetime.now(timezone.utc)
        if reminder_time <= now:
            logger.info(
                f"⚠️ Recordatorio para cita {appointment_id} no programado "
                f"(ya pasó la hora de envío)"
            )
            return None

        # ID único para el job
        job_id = f"reminder_appointment_{appointment_id}"

        try:
            # Programar tarea
            self._scheduler.add_job(
                func=self._send_appointment_reminder,
                trigger=DateTrigger(run_date=reminder_time),
                args=[appointment_id],
                id=job_id,
                name=f"Recordatorio cita {appointment_id}",
                replace_existing=True
            )

            logger.info(
                f"📅 Recordatorio programado para cita {appointment_id} "
                f"el {reminder_time.isoformat()}"
            )

            return job_id

        except Exception as schedule_error:
            logger.error(
                f"❌ Error al programar recordatorio: {str(schedule_error)}"
            )
            return None

    def cancel_appointment_reminder(self, appointment_id: UUID) -> bool:
        """
        Cancela el recordatorio de una cita

        Args:
            appointment_id: ID de la cita

        Returns:
            True si se canceló exitosamente
        """
        if not APSCHEDULER_AVAILABLE or self._scheduler is None:
            return False

        job_id = f"reminder_appointment_{appointment_id}"

        try:
            self._scheduler.remove_job(job_id)
            logger.info(f"🗑️ Recordatorio cancelado para cita {appointment_id}")
            return True

        except Exception:
            # El job no existe o ya se ejecutó
            return False

    def reschedule_appointment_reminder(
        self,
        appointment_id: UUID,
        new_appointment_datetime: datetime,
        notification_hours_before: int = 24
    ) -> Optional[str]:
        """
        Reprograma un recordatorio de cita

        Args:
            appointment_id: ID de la cita
            new_appointment_datetime: Nueva fecha y hora de la cita
            notification_hours_before: Horas antes para el recordatorio

        Returns:
            Nuevo job ID si se reprogramó exitosamente
        """
        # Cancelar recordatorio anterior
        self.cancel_appointment_reminder(appointment_id)

        # Programar nuevo recordatorio
        return self.schedule_appointment_reminder(
            appointment_id,
            new_appointment_datetime,
            notification_hours_before
        )

    def _check_and_send_reminders(self) -> None:
        """
        Verifica y envía recordatorios para citas próximas
        Se ejecuta periódicamente (cada hora)

        Principio: Verificación proactiva de recordatorios pendientes
        """
        try:
            logger.info("🔍 Verificando recordatorios pendientes...")

            # Este método se conectará con el servicio de notificaciones
            # para verificar citas que necesitan recordatorio

            from app.database import get_db
            from app.services.notifications.notification_service import NotificationService

            # Obtener sesión de base de datos
            db = next(get_db())

            try:
                notification_service = NotificationService(db)
                sent_count = notification_service.check_and_send_pending_reminders()

                if sent_count > 0:
                    logger.info(f"✅ Se enviaron {sent_count} recordatorios")
                else:
                    logger.info("ℹ️ No hay recordatorios pendientes")

            finally:
                db.close()

        except Exception as check_error:
            logger.error(
                f"❌ Error al verificar recordatorios: {str(check_error)}"
            )

    def _send_appointment_reminder(self, appointment_id: UUID) -> None:
        """
        Envía un recordatorio para una cita específica
        Llamado por APScheduler en el momento programado

        Args:
            appointment_id: ID de la cita
        """
        try:
            logger.info(f"📧 Enviando recordatorio para cita {appointment_id}")

            from app.database import get_db
            from app.services.notifications.notification_service import NotificationService

            # Obtener sesión de base de datos
            db = next(get_db())

            try:
                notification_service = NotificationService(db)
                success = notification_service.send_appointment_reminder(appointment_id)

                if success:
                    logger.info(
                        f"✅ Recordatorio enviado exitosamente para cita {appointment_id}"
                    )
                else:
                    logger.error(
                        f"❌ No se pudo enviar recordatorio para cita {appointment_id}"
                    )

            finally:
                db.close()

        except Exception as send_error:
            logger.error(
                f"❌ Error al enviar recordatorio para cita {appointment_id}: "
                f"{str(send_error)}"
            )

    def get_scheduled_jobs(self) -> List[dict]:
        """
        Obtiene lista de trabajos programados

        Returns:
            Lista de diccionarios con información de los trabajos
        """
        if not APSCHEDULER_AVAILABLE or self._scheduler is None:
            return []

        jobs = []
        for job in self._scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })

        return jobs

    def is_running(self) -> bool:
        """Verifica si el scheduler está en ejecución"""
        if not APSCHEDULER_AVAILABLE or self._scheduler is None:
            return False

        return self._scheduler.running


# ==================== FUNCIONES AUXILIARES ====================

def get_scheduler_service() -> SchedulerService:
    """
    Obtiene la instancia única del SchedulerService (Singleton)

    Returns:
        SchedulerService instance
    """
    return SchedulerService()


def initialize_scheduler() -> None:
    """
    Inicializa e inicia el scheduler
    Debe llamarse al iniciar la aplicación (en main.py startup event)
    """
    scheduler = get_scheduler_service()
    scheduler.start()
    logger.info("✅ Sistema de recordatorios iniciado")


def shutdown_scheduler() -> None:
    """
    Detiene el scheduler
    Debe llamarse al cerrar la aplicación (en main.py shutdown event)
    """
    scheduler = get_scheduler_service()
    scheduler.shutdown()
    logger.info("🛑 Sistema de recordatorios detenido")