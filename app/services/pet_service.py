"""
Servicio de creación de mascotas - Implementa Template Method Pattern
RF-04: Registro de mascotas con creación automática de historia clínica
RN06: Mascota vinculada a propietario
RN07: No duplicar nombre+especie por propietario
"""

from typing import Optional
from uuid import UUID
from datetime import date

from sqlalchemy.orm import Session

from app.services.base_template import CreateTemplate
from app.services.factory import EntityFactory
from app.repositories.pet_repository import PetRepository
from app.models.pet import Pet
from app.models.medical_history import MedicalHistory
from app.utils.medical_history_number_generator import MedicalHistoryNumberGenerator


class CreatePetService(CreateTemplate):
    """
    Servicio para la creación de mascotas (Pet).
    Implementa el patrón Template Method a través de la clase base CreateTemplate,
    definiendo los pasos específicos para crear una mascota y su historia clínica asociada.
    """

    def __init__(
        self,
        db: Session,
        propietario_id: UUID,
        nombre: str,
        especie: str,
        raza: Optional[str] = None,
        microchip: Optional[str] = None,
        fecha_nacimiento: Optional[date] = None,
    ):
        """
        Inicializa el servicio con los datos necesarios para registrar una mascota.

        Args:
            db: Sesión de base de datos de SQLAlchemy.
            propietario_id: ID del propietario al que pertenece la mascota.
            nombre: Nombre de la mascota.
            especie: Especie (ej. perro, gato, etc.).
            raza: Raza de la mascota (opcional).
            microchip: Código del microchip (opcional, único).
            fecha_nacimiento: Fecha de nacimiento (opcional).
        """
        self.db = db
        self.propietario_id = propietario_id
        self.nombre = nombre
        self.especie = especie
        self.raza = raza
        self.microchip = microchip
        self.fecha_nacimiento = fecha_nacimiento
        self.repo = PetRepository(db)  # Repositorio para operaciones con la entidad Pet

    def validate(self) -> None:
        """
        Paso de validación (Template Method).
        Verifica si ya existe una mascota con el mismo nombre para el propietario
        o si el microchip está duplicado.
        Lanza ValueError si se encuentra un duplicado.
        """
        if self.repo.exists_duplicate(self.propietario_id, self.nombre, self.microchip):
            raise ValueError("Ya existe una mascota con el mismo nombre para el propietario o microchip duplicado")

    def prepare(self) -> Pet:
        """
        Paso de preparación (Template Method).
        Crea la entidad Pet usando la fábrica de entidades (EntityFactory).
        """
        return EntityFactory.create_pet(
            propietario_id=self.propietario_id,
            nombre=self.nombre,
            especie=self.especie,
            raza=self.raza,
            microchip=self.microchip,
            fecha_nacimiento=self.fecha_nacimiento,
        )

    def persist(self, entity: Pet) -> Pet:
        """
        Paso de persistencia (Template Method).
        Guarda la mascota en la base de datos utilizando el repositorio.
        """
        pet = self.repo.create(entity)
        return pet

    def post_process(self, entity: Pet) -> None:
        """
        Paso posterior (Template Method).
        Crea automáticamente una historia clínica (MedicalHistory) asociada
        a la mascota recién creada con número único generado.

        RF-04: Creación automática de historia clínica
        Formato del número: HC-YYYY-XXXX
        """
        # Generar número único para la historia clínica
        numero_historia = MedicalHistoryNumberGenerator.generate(self.db)

        # Crear historia clínica con número generado
        mh = MedicalHistory(
            mascota_id=entity.id,
            numero=numero_historia
        )

        self.db.add(mh)
        self.db.commit()
        self.db.refresh(mh)