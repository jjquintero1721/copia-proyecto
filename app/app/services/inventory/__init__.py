"""
Módulo de Gestión de Inventario
RF-10: Control de medicamentos e insumos médicos

Patrones implementados:
- Abstract Factory: Creación de diferentes tipos de medicamentos
- Observer: Alertas de stock bajo y eventos de inventario
- Facade: Operaciones simplificadas de inventario
- Template Method: Estandarización de procesos CRUD
"""

from .inventory_service import InventoryService
from .inventory_facade import InventoryFacade
from .medication_factory import MedicationAbstractFactory
from .observers import get_gestor_inventario

__all__ = [
    'InventoryService',
    'InventoryFacade',
    'MedicationAbstractFactory',
    'get_gestor_inventario'
]