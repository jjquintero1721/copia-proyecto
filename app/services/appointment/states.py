"""
State Pattern - Gestión de estados de citas
RF-05: Estados de citas (agendada, confirmada, en_proceso, completada, cancelada)
RN08-3: Control de transiciones de estado
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.models.appointment import Appointment, AppointmentStatus


class AppointmentState(ABC):
    """
    Clase abstracta para estados de cita
    Cada estado define qué transiciones son permitidas
    """

    @abstractmethod
    def confirmar(self, cita: Appointment) -> None:
        """Confirmar la cita"""
        pass

    @abstractmethod
    def cancelar(self, cita: Appointment) -> None:
        """Cancelar la cita"""
        pass

    @abstractmethod
    def iniciar(self, cita: Appointment) -> None:
        """Iniciar atención (cambiar a en_proceso)"""
        pass

    @abstractmethod
    def finalizar(self, cita: Appointment) -> None:
        """Finalizar atención (cambiar a completada)"""
        pass

    @abstractmethod
    def reprogramar(self, cita: Appointment, nueva_fecha: datetime) -> None:
        """Reprogramar la cita"""
        pass

    def _ensure_timezone_aware(self, dt: datetime) -> datetime:
        """
        Asegura que un datetime tenga información de timezone.
        Si no la tiene, asume UTC.

        Args:
            dt: datetime a verificar

        Returns:
            datetime con timezone UTC

        Raises:
            ValueError: Si dt es None
        """
        if dt is None:
            raise ValueError("Datetime no puede ser None")

        if dt.tzinfo is None:
            # Si no tiene timezone, asumimos UTC
            return dt.replace(tzinfo=timezone.utc)

        return dt

    def _validar_anticipacion_cancelacion(self, cita: Appointment) -> bool:
        """
        RN08-2: Cancelaciones con menos de 4 horas deben registrarse como "cancelación tardía"
        """
        now = datetime.now(timezone.utc)
        fecha_hora_aware = self._ensure_timezone_aware(cita.fecha_hora)
        diferencia = fecha_hora_aware - now
        return diferencia < timedelta(hours=4)

    def _validar_anticipacion_reprogramacion(self, cita: Appointment) -> bool:
        """
        RN08-3: Reprogramaciones solo se permiten hasta 2 horas antes
        """
        now = datetime.now(timezone.utc)
        fecha_hora_aware = self._ensure_timezone_aware(cita.fecha_hora)
        diferencia = fecha_hora_aware - now
        return diferencia >= timedelta(hours=2)


class AgendadaState(AppointmentState):
    """Estado: Cita Agendada"""

    def confirmar(self, cita: Appointment) -> None:
        cita.estado = AppointmentStatus.CONFIRMADA

    def cancelar(self, cita: Appointment) -> None:
        if self._validar_anticipacion_cancelacion(cita):
            cita.estado = AppointmentStatus.CANCELADA_TARDIA
            cita.cancelacion_tardia = True
        else:
            cita.estado = AppointmentStatus.CANCELADA

    def iniciar(self, cita: Appointment) -> None:
        raise ValueError("No se puede iniciar una cita sin confirmar")

    def finalizar(self, cita: Appointment) -> None:
        raise ValueError("No se puede finalizar una cita que no ha iniciado")

    def reprogramar(self, cita: Appointment, nueva_fecha: datetime) -> None:
        if not self._validar_anticipacion_reprogramacion(cita):
            raise ValueError("Solo se permite reprogramar hasta 2 horas antes de la cita")
        cita.fecha_hora = nueva_fecha


class ConfirmadaState(AppointmentState):
    """Estado: Cita Confirmada"""

    def confirmar(self, cita: Appointment) -> None:
        raise ValueError("La cita ya está confirmada")

    def cancelar(self, cita: Appointment) -> None:
        if self._validar_anticipacion_cancelacion(cita):
            cita.estado = AppointmentStatus.CANCELADA_TARDIA
            cita.cancelacion_tardia = True
        else:
            cita.estado = AppointmentStatus.CANCELADA

    def iniciar(self, cita: Appointment) -> None:
        cita.estado = AppointmentStatus.EN_PROCESO

    def finalizar(self, cita: Appointment) -> None:
        raise ValueError("No se puede finalizar una cita que no ha iniciado")

    def reprogramar(self, cita: Appointment, nueva_fecha: datetime) -> None:
        if not self._validar_anticipacion_reprogramacion(cita):
            raise ValueError("Solo se permite reprogramar hasta 2 horas antes de la cita")
        cita.fecha_hora = nueva_fecha


class EnProcesoState(AppointmentState):
    """Estado: Cita En Proceso"""

    def confirmar(self, cita: Appointment) -> None:
        raise ValueError("La cita ya está en proceso")

    def cancelar(self, cita: Appointment) -> None:
        raise ValueError("No se puede cancelar una cita en proceso")

    def iniciar(self, cita: Appointment) -> None:
        raise ValueError("La cita ya está en proceso")

    def finalizar(self, cita: Appointment) -> None:
        cita.estado = AppointmentStatus.COMPLETADA

    def reprogramar(self, cita: Appointment, nueva_fecha: datetime) -> None:
        raise ValueError("No se puede reprogramar una cita en proceso")


class CompletadaState(AppointmentState):
    """Estado: Cita Completada"""

    def confirmar(self, cita: Appointment) -> None:
        raise ValueError("La cita ya fue completada")

    def cancelar(self, cita: Appointment) -> None:
        raise ValueError("No se puede cancelar una cita completada")

    def iniciar(self, cita: Appointment) -> None:
        raise ValueError("La cita ya fue completada")

    def finalizar(self, cita: Appointment) -> None:
        raise ValueError("La cita ya está finalizada")

    def reprogramar(self, cita: Appointment, nueva_fecha: datetime) -> None:
        raise ValueError("No se puede reprogramar una cita completada")


class CanceladaState(AppointmentState):
    """Estado: Cita Cancelada"""

    def confirmar(self, cita: Appointment) -> None:
        raise ValueError("No se puede confirmar una cita cancelada")

    def cancelar(self, cita: Appointment) -> None:
        raise ValueError("La cita ya está cancelada")

    def iniciar(self, cita: Appointment) -> None:
        raise ValueError("No se puede iniciar una cita cancelada")

    def finalizar(self, cita: Appointment) -> None:
        raise ValueError("No se puede finalizar una cita cancelada")

    def reprogramar(self, cita: Appointment, nueva_fecha: datetime) -> None:
        raise ValueError("No se puede reprogramar una cita cancelada. Debe crear una nueva cita")


class AppointmentStateManager:
    """
    Gestor de estados - Context del patrón State
    Coordina las transiciones entre estados
    """

    _states = {
        AppointmentStatus.AGENDADA: AgendadaState(),
        AppointmentStatus.CONFIRMADA: ConfirmadaState(),
        AppointmentStatus.EN_PROCESO: EnProcesoState(),
        AppointmentStatus.COMPLETADA: CompletadaState(),
        AppointmentStatus.CANCELADA: CanceladaState(),
        AppointmentStatus.CANCELADA_TARDIA: CanceladaState(),
    }

    @classmethod
    def get_state(cls, estado: AppointmentStatus) -> AppointmentState:
        """Obtiene el estado correspondiente"""
        return cls._states[estado]

    @classmethod
    def confirmar(cls, cita: Appointment) -> None:
        """Confirmar cita"""
        state = cls.get_state(cita.estado)
        state.confirmar(cita)

    @classmethod
    def cancelar(cls, cita: Appointment) -> None:
        """Cancelar cita"""
        state = cls.get_state(cita.estado)
        state.cancelar(cita)

    @classmethod
    def iniciar(cls, cita: Appointment) -> None:
        """Iniciar atención"""
        state = cls.get_state(cita.estado)
        state.iniciar(cita)

    @classmethod
    def finalizar(cls, cita: Appointment) -> None:
        """Finalizar atención"""
        state = cls.get_state(cita.estado)
        state.finalizar(cita)

    @classmethod
    def reprogramar(cls, cita: Appointment, nueva_fecha: datetime) -> None:
        """Reprogramar cita"""
        state = cls.get_state(cita.estado)
        state.reprogramar(cita, nueva_fecha)