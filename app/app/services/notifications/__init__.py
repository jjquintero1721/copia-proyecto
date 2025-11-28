"""
Módulo de Notificaciones y Recordatorios Automáticos
RF-06: Notificaciones por correo

Integra:
- Sistema de plantillas HTML
- SchedulerService para tareas programadas
- NotificationService que coordina todo
- Integración con Observer Pattern

Exports:
- get_email_template: Factory para plantillas
- NotificationService: Servicio principal de notificaciones
- SchedulerService: Programación de tareas con APScheduler
- initialize_scheduler: Inicializar scheduler al inicio
- shutdown_scheduler: Detener scheduler al cierre
"""

from app.services.notifications.email_templates import (
    EmailTemplate,
    AppointmentConfirmationTemplate,
    AppointmentReminderTemplate,
    AppointmentRescheduleTemplate,
    AppointmentCancellationTemplate,
    get_email_template
)

from app.services.notifications.scheduler_service import (
    SchedulerService,
    get_scheduler_service,
    initialize_scheduler,
    shutdown_scheduler
)

from app.services.notifications.notification_service import NotificationService

_all_ = [
    # Plantillas
    'EmailTemplate',
    'AppointmentConfirmationTemplate',
    'AppointmentReminderTemplate',
    'AppointmentRescheduleTemplate',
    'AppointmentCancellationTemplate',
    'get_email_template',

    # Scheduler
    'SchedulerService',
    'get_scheduler_service',
    'initialize_scheduler',
    'shutdown_scheduler',

    # Servicio principal
    'NotificationService'
]