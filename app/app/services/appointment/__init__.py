"""
Módulo de Gestión de Citas
RF-05: Agendar, reprogramar y cancelar citas

Patrones implementados:
- State: Estados de citas
- Strategy: Políticas de agendamiento
- Observer: Notificaciones y auditoría
- Facade: Operaciones simplificadas
- Command: Auditoría de comandos
"""

from .appointment_service import AppointmentService
from .appointment_facade import AppointmentFacade
from .states import AppointmentStateManager
from .strategies import GestorAgendamiento, PoliticaEstandar, PoliticaReprogramacion
from .observers import get_gestor_citas

__all__ = [
    'AppointmentService',
    'AppointmentFacade',
    'AppointmentStateManager',
    'GestorAgendamiento',
    'PoliticaEstandar',
    'PoliticaReprogramacion',
    'get_gestor_citas'
]