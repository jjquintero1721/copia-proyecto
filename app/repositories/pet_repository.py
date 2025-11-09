from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.models.pet import Pet


# ==================== REPOSITORIO: MASCOTA ====================
class PetRepository:
    def __init__(self, db: Session):
        # Sesión activa de la base de datos
        self.db = db

    def get_by_id(self, pet_id: UUID) -> Optional[Pet]:
        """
        Busca una mascota por su ID único (UUID)
        """
        return self.db.query(Pet).filter(Pet.id == pet_id).first()

    def get_by_owner_and_name(self, owner_id: UUID, nombre: str) -> Optional[Pet]:
        """
        Busca una mascota por el ID del propietario y su nombre (sin distinguir mayúsculas/minúsculas)
        """
        return (
            self.db.query(Pet)
            .filter(Pet.propietario_id == owner_id, Pet.nombre.ilike(nombre))
            .first()
        )

    def get_by_microchip(self, microchip: str) -> Optional[Pet]:
        """
        Busca una mascota por su número de microchip
        """
        return self.db.query(Pet).filter(Pet.microchip == microchip).first()

    def exists_duplicate(self, owner_id: UUID, nombre: str, microchip: Optional[str]) -> bool:
        """
        Verifica si ya existe una mascota con el mismo nombre para un propietario
        o con el mismo microchip registrado en el sistema.
        Retorna True si se encuentra duplicado.
        """
        if microchip:
            # Verifica duplicado por nombre del propietario o microchip
            return (
                self.db.query(Pet.id)
                .filter(
                    (Pet.propietario_id == owner_id) & (Pet.nombre.ilike(nombre))
                    | (Pet.microchip == microchip)
                )
                .first()
                is not None
            )
        # Verifica duplicado solo por nombre (si no hay microchip)
        return (
            self.db.query(Pet.id)
            .filter(Pet.propietario_id == owner_id, Pet.nombre.ilike(nombre))
            .first()
            is not None
        )

    def create(self, pet: Pet) -> Pet:
        """
        Crea una nueva mascota en la base de datos.
        Guarda y refresca el objeto después de la inserción.
        """
        self.db.add(pet)
        self.db.commit()
        self.db.refresh(pet)
        return pet
