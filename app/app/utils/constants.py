"""
Constantes del sistema
"""

# Roles de usuario
class UserRoles:
    SUPERADMIN = "superadmin"
    VETERINARIO = "veterinario"
    AUXILIAR = "auxiliar"
    PROPIETARIO = "propietario"


# Estados de citas
class AppointmentStatus:
    AGENDADA = "agendada"
    CONFIRMADA = "confirmada"
    EN_PROCESO = "en_proceso"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"
    CANCELADA_TARDIA = "cancelada_tardia"


# Niveles de prioridad (Triage)
class PriorityLevel:
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


# Especies permitidas
class Species:
    PERRO = "perro"
    GATO = "gato"


# Tipos de eventos para notificaciones
class NotificationEvents:
    CITA_CREADA = "CITA_CREADA"
    CITA_CONFIRMADA = "CITA_CONFIRMADA"
    CITA_REPROGRAMADA = "CITA_REPROGRAMADA"
    CITA_CANCELADA = "CITA_CANCELADA"
    RECORDATORIO_CITA = "RECORDATORIO_CITA"
    USUARIO_CREADO = "USUARIO_CREADO"
    MASCOTA_REGISTRADA = "MASCOTA_REGISTRADA"