"""
Módulo de Seguimiento de Pacientes
RF-11: Permitir registrar seguimientos posteriores a consultas o tratamientos

Patrones implementados:
- Builder Pattern: Construcción de citas de seguimiento
- Template Method: Flujo estructurado de creación y completación
- Command Pattern: Auditoría automática de operaciones
"""

from .follow_up_service import FollowUpService

__all__ = [
    'FollowUpService'
]