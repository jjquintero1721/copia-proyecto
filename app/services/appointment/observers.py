"""
Observer Pattern - Sistema de notificaciones actualizado
RF-06: Notificaciones por correo
RNF-07: Auditoría de acciones

ACTUALIZADO: Integra con NotificationService, EmailAdapter y plantillas HTML
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.appointment import Appointment


class AppointmentObserver(ABC):
    """
    Observador abstracto para eventos de citas
    Patrón Observer: Define la interfaz para observadores
    """

    @abstractmethod
    def actualizar(self, evento: str, cita: Appointment, datos: Dict[str, Any]) -> None:
        """
        Método llamado cuando ocurre un evento en una cita

        Args:
            evento: Tipo de evento (CITA_CREADA, CITA_REPROGRAMADA, etc.)
            cita: Instancia de la cita afectada
            datos: Datos adicionales del evento
        """
        pass


class NotificadorCorreo(AppointmentObserver):
    """
    Observer que envía notificaciones por correo
    RF-06: Notificaciones automáticas

    ACTUALIZADO: Usa NotificationService con EmailAdapter y plantillas HTML
    """

    def __init__(self, db: Session):
        """
        Inicializa el observador con sesión de base de datos

        Args:
            db: Sesión de SQLAlchemy
        """
        self.db = db

    def actualizar(self, evento: str, cita: Appointment, datos: Dict[str, Any]) -> None:
        """
        Envía notificaciones por correo según el evento

        Integración con NotificationService:
        - CITA_CREADA → send_appointment_confirmation
        - CITA_REPROGRAMADA → send_appointment_reschedule_notification
        - CITA_CANCELADA → send_appointment_cancellation_notification
        - RECORDATORIO_CITA → send_appointment_reminder (programado)
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"📧 [NotificadorCorreo] Procesando evento: {evento}")

        # Importar NotificationService
        from app.services.notifications.notification_service import NotificationService

        try:
            notification_service = NotificationService(self.db)
            user_id = datos.get('usuario_id')

            if evento == "CITA_CREADA":
                # Enviar confirmación de cita
                logger.info(f"   → Enviando confirmación de cita {cita.id}")
                success = notification_service.send_appointment_confirmation(
                    appointment_id=cita.id,
                    user_id=user_id
                )

                if success:
                    logger.info("   ✅ Confirmación enviada exitosamente")
                else:
                    logger.warning("   ⚠️ No se pudo enviar confirmación")

            elif evento == "CITA_REPROGRAMADA":
                # Enviar notificación de reprogramación
                logger.info("   → Enviando notificación de reprogramación")
                fecha_anterior = datos.get('fecha_anterior')

                success = notification_service.send_appointment_reschedule_notification(
                    appointment_id=cita.id,
                    fecha_anterior=fecha_anterior,
                    user_id=user_id
                )

                if success:
                    logger.info("   ✅ Notificación de reprogramación enviada")
                else:
                    logger.warning("   ⚠️ No se pudo enviar notificación")

            elif evento == "CITA_CANCELADA":
                # Enviar notificación de cancelación
                logger.info("   → Enviando notificación de cancelación")

                success = notification_service.send_appointment_cancellation_notification(
                    appointment_id=cita.id,
                    cancelacion_tardia=cita.cancelacion_tardia,
                    user_id=user_id
                )

                if success:
                    logger.info("   ✅ Notificación de cancelación enviada")
                else:
                    logger.warning("   ⚠️ No se pudo enviar notificación")

            elif evento == "RECORDATORIO_CITA":
                # Los recordatorios son programados automáticamente
                # por SchedulerService cuando se crea la cita
                logger.info("   ℹ️ Recordatorio programado por SchedulerService")

        except Exception as error:
            logger.error(
                f"   ❌ Error al procesar notificación: {str(error)}"
            )


class RegistroAuditoria(AppointmentObserver):
    """
    Observer que registra auditoría de acciones
    RNF-07: Auditoría completa de operaciones
    """

    def actualizar(self, evento: str, cita: Appointment, datos: Dict[str, Any]) -> None:
        """Registra la acción en el sistema de auditoría"""
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"📋 [Auditoría] Registrando evento: {evento}")
        logger.info(f"   → Cita ID: {cita.id}")
        logger.info(f"   → Fecha/Hora: {datetime.now(timezone.utc)}")
        logger.info(f"   → Usuario: {datos.get('usuario_id', 'Sistema')}")
        logger.info(f"   → Detalles: {datos}")



class MetricasObserver(AppointmentObserver):
    """
    Observer que registra métricas del sistema
    RNF-04: Monitoreo de rendimiento
    """

    def actualizar(self, evento: str, cita: Appointment, datos: Dict[str, Any]) -> None:
        """Registra métricas de uso"""
        import logging
        logger = logging.getLogger(__name__)

        try:
            logger.info(f"📊 [Métricas] Evento: {evento}")


        except Exception as error:
            logger.error(
                f"❌ Error al registrar métricas: {str(error)}"
            )
            # NO propagar el error - solo loggearlo


# ==================== GESTOR DE OBSERVADORES ====================

class GestorCitas:
    """
    Subject del patrón Observer
    Gestiona la lista de observadores y notifica cambios
    """

    def __init__(self, db: Session):
        self.observadores: list[AppointmentObserver] = []
        self.db = db

    def agregar_observador(self, observador: AppointmentObserver) -> None:
        """Agrega un observador a la lista"""
        if observador not in self.observadores:
            self.observadores.append(observador)

    def remover_observador(self, observador: AppointmentObserver) -> None:
        """Remueve un observador de la lista"""
        if observador in self.observadores:
            self.observadores.remove(observador)

    def notificar(self, evento: str, cita: Appointment, datos: Dict[str, Any]) -> None:
        """
        Notifica a todos los observadores sobre un evento

        Args:
            evento: Tipo de evento
            cita: Cita afectada
            datos: Datos adicionales
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"🔔 Notificando evento: {evento} para cita {cita.id}")

        for observador in self.observadores:
            try:
                observador.actualizar(evento, cita, datos)
            except Exception as error:
                logger.error(
                    f"❌ Error en observador {observador.__class__.__name__}: "
                    f"{str(error)}"
                )


# ==================== SINGLETON DEL GESTOR ====================

_gestor_instance: dict[str, GestorCitas] = {}


def get_gestor_citas(db: Session) -> GestorCitas:
    """
    Obtiene o crea una instancia del GestorCitas con los observadores configurados

    Args:
        db: Sesión de base de datos

    Returns:
        GestorCitas configurado con observadores
    """
    # Usar hash de la sesión como key para tener un gestor por sesión
    session_key = str(id(db))

    if session_key not in _gestor_instance:
        # Crear nuevo gestor
        gestor = GestorCitas(db)

        # Agregar observadores
        gestor.agregar_observador(NotificadorCorreo(db))
        gestor.agregar_observador(RegistroAuditoria())
        gestor.agregar_observador(MetricasObserver())

        _gestor_instance[session_key] = gestor

    return _gestor_instance[session_key]