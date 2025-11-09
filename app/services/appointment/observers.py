"""
Observer Pattern - Sistema de notificaciones y auditoría para citas
RF-06: Notificaciones por correo
RNF-07: Auditoría de acciones
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime, timezone
from uuid import UUID

from app.models.appointment import Appointment


class AppointmentObserver(ABC):
    """
    Observador abstracto para eventos de citas
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
    """

    def actualizar(self, evento: str, cita: Appointment, datos: Dict[str, Any]) -> None:
        """Envía notificaciones por correo según el evento"""
        print(f"📧 [NotificadorCorreo] Enviando correo para evento: {evento}")

        # Aquí se integraría con el servicio de correo (EmailService/Adapter)
        # Por ahora solo registramos en consola

        if evento == "CITA_CREADA":
            print(f"   → Confirmación de cita para {cita.mascota_id}")
            print(f"   → Fecha: {cita.fecha_hora}")

        elif evento == "CITA_REPROGRAMADA":
            print(f"   → Notificación de reprogramación")
            print(f"   → Nueva fecha: {cita.fecha_hora}")

        elif evento == "CITA_CANCELADA":
            if cita.cancelacion_tardia:
                print(f"   → Notificación de cancelación tardía")
            else:
                print(f"   → Notificación de cancelación")

        elif evento == "RECORDATORIO_CITA":
            print(f"   → Recordatorio de cita para mañana")


class RegistroAuditoria(AppointmentObserver):
    """
    Observer que registra auditoría de acciones
    RNF-07: Auditoría completa de operaciones
    """

    def actualizar(self, evento: str, cita: Appointment, datos: Dict[str, Any]) -> None:
        """Registra la acción en el sistema de auditoría"""
        print(f"📋 [Auditoría] Registrando evento: {evento}")
        print(f"   → Cita ID: {cita.id}")
        print(f"   → Fecha/Hora: {datetime.now(timezone.utc)}")
        print(f"   → Usuario: {datos.get('usuario_id', 'Sistema')}")
        print(f"   → Detalles: {datos}")

        # Aquí se guardaría en una tabla de auditoría
        # audit_record = AuditLog(
        #     entidad="Cita",
        #     entidad_id=cita.id,
        #     accion=evento,
        #     usuario_id=datos.get('usuario_id'),
        #     detalles=json.dumps(datos),
        #     fecha=datetime.utcnow()
        # )


class MetricasObserver(AppointmentObserver):
    """
    Observer que registra métricas del sistema
    RNF-04: Monitoreo de rendimiento
    """

    def actualizar(self, evento: str, cita: Appointment, datos: Dict[str, Any]) -> None:
        """Registra métricas de uso"""
        print(f"📊 [Métricas] Evento: {evento}")

        # Aquí se enviarían métricas a un sistema de monitoreo
        # (ej: Prometheus, CloudWatch, etc.)


class GestorCitas:
    """
    Subject del patrón Observer
    Gestiona la lista de observadores y notifica eventos
    """

    def __init__(self):
        self._observadores: List[AppointmentObserver] = []

    def agregar_observador(self, observador: AppointmentObserver) -> None:
        """Agrega un observador a la lista"""
        if observador not in self._observadores:
            self._observadores.append(observador)

    def eliminar_observador(self, observador: AppointmentObserver) -> None:
        """Elimina un observador de la lista"""
        if observador in self._observadores:
            self._observadores.remove(observador)

    def notificar(self, evento: str, cita: Appointment, **datos) -> None:
        """
        Notifica a todos los observadores sobre un evento

        Args:
            evento: Tipo de evento (CITA_CREADA, etc.)
            cita: Cita afectada
            **datos: Datos adicionales del evento
        """
        for observador in self._observadores:
            observador.actualizar(evento, cita, datos)


# Instancia global del gestor (Singleton pattern)
_gestor_citas_instance = None


def get_gestor_citas() -> GestorCitas:
    """
    Obtiene la instancia única del GestorCitas (Singleton)
    """
    global _gestor_citas_instance
    if _gestor_citas_instance is None:
        _gestor_citas_instance = GestorCitas()

        # Registrar observadores por defecto
        _gestor_citas_instance.agregar_observador(NotificadorCorreo())
        _gestor_citas_instance.agregar_observador(RegistroAuditoria())
        _gestor_citas_instance.agregar_observador(MetricasObserver())

    return _gestor_citas_instance