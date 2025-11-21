"""
Módulo de Decoradores - Patrón Decorator
Extiende funcionalidades de servicios y citas dinámicamente

Exports:
- ServiceDecorator: Decorador base para servicios
- LoggingDecorator: Logging profesional
- AuditDecorator: Auditoría en BD
- ValidationDecorator: Validación de inputs/outputs
- create_decorated_service: Factory para servicios decorados

- AppointmentDecorator: Decorador base para citas
- RecordatorioDecorator: Recordatorios automáticos
- NotasEspecialesDecorator: Notas especiales
- PrioridadDecorator: Prioridad especial
- cargar_decoradores_de_cita: Carga decoradores de BD
- get_cita_con_decoradores: Obtiene cita completa con decoradores

Relaciona con: RF-05, RF-06, RNF-07
"""

from app.services.decorators.service_decorators import (
    ServiceDecorator,
    LoggingDecorator,
    AuditDecorator,
    ValidationDecorator,
    create_decorated_service
)

from app.services.decorators.appointment_decorators import (
    AppointmentDecorator,
    RecordatorioDecorator,
    NotasEspecialesDecorator,
    PrioridadDecorator,
    cargar_decoradores_de_cita,
    get_cita_con_decoradores
)

__all__ = [
    # Decoradores de servicios
    'ServiceDecorator',
    'LoggingDecorator',
    'AuditDecorator',
    'ValidationDecorator',
    'create_decorated_service',

    # Decoradores de citas
    'AppointmentDecorator',
    'RecordatorioDecorator',
    'NotasEspecialesDecorator',
    'PrioridadDecorator',
    'cargar_decoradores_de_cita',
    'get_cita_con_decoradores'
]