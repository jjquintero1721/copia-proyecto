"""
Controladores - Endpoints y rutas HTTP
Cada controlador maneja las peticiones HTTP para un módulo específico
"""
from app.controllers import triage_controller
from app.controllers import inventory_controller

from app.controllers import notification_settings_controller  # ← NUEVO

__all__ = [
    'triage_controller',
    'inventory_controller',
    'notification_settings_controller'  # ← NUEVO
]