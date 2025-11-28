from sqlalchemy.orm import Session, joinedload
from typing import Optional, List, Any
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
                    ((Pet.propietario_id == owner_id) & Pet.nombre.ilike(nombre)) |
                    (Pet.microchip == microchip)
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

    def get_all(
            self,
            skip: int = 0,
            limit: int = 100,
            activo: Optional[bool] = True
    ) -> list[type[Pet]]:
        """
        Obtiene todas las mascotas con paginación

        Args:
            skip: Número de registros a saltar
            limit: Máximo de registros a retornar
            activo: Filtrar por estado activo (None = todos)

        Returns:
            Lista de mascotas
        """
        query = self.db.query(Pet).options(joinedload(Pet.owner))

        if activo is not None:
            query = query.filter(Pet.activo == activo)

        return query.order_by(Pet.fecha_creacion.desc()).offset(skip).limit(limit).all()

    def get_by_species(
            self,
            especie: str,
            skip: int = 0,
            limit: int = 100,
            activo: Optional[bool] = True
    ) -> list[type[Pet]]:
        """
        Obtiene mascotas filtradas por especie

        Args:
            especie: Especie a filtrar (ej: "perro", "gato")
            skip: Número de registros a saltar
            limit: Máximo de registros a retornar
            activo: Filtrar por estado activo (None = todos)

        Returns:
            Lista de mascotas de la especie especificada
        """
        query = (
            self.db.query(Pet)
            .options(joinedload(Pet.owner))
            .filter(Pet.especie.ilike(especie))
        )

        if activo is not None:
            query = query.filter(Pet.activo == activo)

        return query.order_by(Pet.fecha_creacion.desc()).offset(skip).limit(limit).all()

    def get_by_owner_id(
            self,
            owner_id: UUID,
            skip: int = 0,
            limit: int = 100,
            activo: Optional[bool] = True
    ) -> List[Pet]:
        """
        Obtiene todas las mascotas de un propietario específico

        Args:
            owner_id: UUID del propietario
            skip: Número de registros a saltar
            limit: Máximo de registros a retornar
            activo: Filtrar por estado activo (None = todos)

        Returns:
            Lista de mascotas del propietario
        """
        query = (
            self.db.query(Pet)
            .filter(Pet.propietario_id == owner_id)
        )

        if activo is not None:
            query = query.filter(Pet.activo == activo)

        return query.order_by(Pet.fecha_creacion.desc()).offset(skip).limit(limit).all()

    def count_all(self, activo: Optional[bool] = True) -> int:
        """
        Cuenta el total de mascotas

        Args:
            activo: Filtrar por estado activo (None = todos)

        Returns:
            Número total de mascotas
        """
        query = self.db.query(Pet)

        if activo is not None:
            query = query.filter(Pet.activo == activo)

        return query.count()

    def count_by_species(self, especie: str, activo: Optional[bool] = True) -> int:
        """
        Cuenta mascotas por especie

        Args:
            especie: Especie a contar
            activo: Filtrar por estado activo (None = todos)

        Returns:
            Número de mascotas de esa especie
        """
        query = self.db.query(Pet).filter(Pet.especie.ilike(especie))

        if activo is not None:
            query = query.filter(Pet.activo == activo)

        return query.count()

    def count_by_owner(self, owner_id: UUID, activo: Optional[bool] = True) -> int:
        """
        Cuenta mascotas de un propietario

        Args:
            owner_id: UUID del propietario
            activo: Filtrar por estado activo (None = todos)

        Returns:
            Número de mascotas del propietario
        """
        query = self.db.query(Pet).filter(Pet.propietario_id == owner_id)

        if activo is not None:
            query = query.filter(Pet.activo == activo)

        return query.count()

    def create(self, pet: Pet) -> Pet:
        """
        Crea una nueva mascota en la base de datos.
        Guarda y refresca el objeto después de la inserción.
        """
        self.db.add(pet)
        self.db.commit()
        self.db.refresh(pet)
        return pet

    def update(self, pet: Pet) -> Pet:
        """
        Actualiza una mascota existente

        Args:
            pet: Instancia de Pet a actualizar

        Returns:
            Pet actualizada
        """
        self.db.commit()
        self.db.refresh(pet)
        return pet

    def delete(self, pet: Pet) -> None:
        """
        Elimina una mascota (borrado físico)

        Args:
            pet: Instancia de Pet a eliminar
        """
        self.db.delete(pet)
        self.db.commit()

    def soft_delete(self, pet: Pet) -> Pet:
        """
        Desactiva una mascota (borrado lógico)

        Args:
            pet: Instancia de Pet a desactivar

        Returns:
            Pet desactivada
        """
        pet.activo = False
        return self.update(pet)