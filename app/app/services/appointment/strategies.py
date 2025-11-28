"""
Strategy Pattern - Políticas de agendamiento y validación
RN08-*: Reglas de anticipación y cancelación
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Optional


class AgendamientoStrategy(ABC):
    """
    Estrategia abstracta para políticas de agendamiento
    Permite cambiar reglas de validación sin modificar la lógica principal
    """

    @abstractmethod
    def validar_anticipacion(self, fecha_hora: datetime) -> bool:
        """Valida si la fecha cumple con la anticipación mínima"""
        pass

    @abstractmethod
    def obtener_mensaje_error(self) -> str:
        """Retorna el mensaje de error apropiado"""
        pass


class PoliticaEstandar(AgendamientoStrategy):
    """
    RN08-1: Las citas deben programarse con al menos 4 horas de anticipación
    """
    ANTICIPACION_MINIMA = timedelta(hours=4)

    def validar_anticipacion(self, fecha_hora: datetime) -> bool:
        now = datetime.now(timezone.utc)
        return fecha_hora >= now + self.ANTICIPACION_MINIMA

    def obtener_mensaje_error(self) -> str:
        return "La cita debe programarse con al menos 4 horas de anticipación"


class PoliticaReprogramacion(AgendamientoStrategy):
    """
    RN08-3: Reprogramaciones solo se permiten hasta 2 horas antes
    """
    ANTICIPACION_MINIMA = timedelta(hours=2)

    def validar_anticipacion(self, fecha_hora: datetime) -> bool:
        now = datetime.now(timezone.utc)
        return fecha_hora >= now + self.ANTICIPACION_MINIMA

    def obtener_mensaje_error(self) -> str:
        return "La reprogramación debe hacerse con al menos 2 horas de anticipación"


class PoliticaUrgencia(AgendamientoStrategy):
    """
    Política especial para casos de urgencia (opcional)
    Permite agendar con menos anticipación
    """
    ANTICIPACION_MINIMA = timedelta(hours=1)

    def validar_anticipacion(self, fecha_hora: datetime) -> bool:
        now = datetime.now(timezone.utc)
        return fecha_hora >= now + self.ANTICIPACION_MINIMA

    def obtener_mensaje_error(self) -> str:
        return "Las citas de urgencia requieren al menos 1 hora de anticipación"


class GestorAgendamiento:
    """
    Context del patrón Strategy
    Usa la estrategia apropiada según el tipo de operación
    """

    def __init__(self, estrategia: AgendamientoStrategy):
        self._estrategia = estrategia

    def set_estrategia(self, estrategia: AgendamientoStrategy) -> None:
        """Cambia la estrategia de validación"""
        self._estrategia = estrategia

    def validar(self, fecha_hora: datetime) -> tuple[bool, Optional[str]]:
        """
        Valida la fecha según la estrategia actual

        Returns:
            tuple: (es_valido, mensaje_error)
        """
        es_valido = self._estrategia.validar_anticipacion(fecha_hora)
        mensaje_error = None if es_valido else self._estrategia.obtener_mensaje_error()
        return es_valido, mensaje_error