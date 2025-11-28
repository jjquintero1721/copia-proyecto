"""
Repositorios - Capa de acceso a datos
Cada repositorio encapsula las operaciones CRUD sobre los modelos
"""
from app.repositories.triage_repository import TriageRepository
from app.repositories.medication_repository import MedicationRepository
from app.repositories.inventory_movement_repository import InventoryMovementRepository
from app.repositories.notification_settings_repository import NotificationSettingsRepository  # ← NUEVO

__all__ = [
    'NotificationSettingsRepository'  # ← NUEVO
]