from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import date

from app.services.owner_service import CreateOwnerService
from app.services.pet_service import CreatePetService
from app.services.decorators.service_decorators import AuditDecorator


# ==================== COMANDO: CREACIÓN DE MASCOTA ====================
class CreatePetCommand:
    # Constructor: inicializa los datos necesarios para registrar una mascota
    def __init__(self, db: Session, propietario_id: UUID, nombre: str, especie: str, raza: Optional[str] = None, microchip: Optional[str] = None, fecha_nacimiento: Optional[date] = None):
        self.db = db  # Sesión de base de datos
        self.propietario_id = propietario_id  # ID del propietario asociado
        self.nombre = nombre  # Nombre de la mascota
        self.especie = especie  # Especie (perro, gato, etc.)
        self.raza = raza  # Raza (opcional)
        self.microchip = microchip  # Número de microchip (opcional)
        self.fecha_nacimiento = fecha_nacimiento  # Fecha de nacimiento (opcional)

    # Método principal que ejecuta el comando
    def execute(self):
        # Crea una instancia del servicio responsable de crear mascotas
        service = CreatePetService(
            db=self.db,
            propietario_id=self.propietario_id,
            nombre=self.nombre,
            especie=self.especie,
            raza=self.raza,
            microchip=self.microchip,
            fecha_nacimiento=self.fecha_nacimiento,
        )
        # Aplica el decorador de auditoría y ejecuta la operación
        return AuditDecorator(service).execute()
