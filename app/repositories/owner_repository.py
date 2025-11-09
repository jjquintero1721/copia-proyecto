from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from uuid import UUID

from app.models.owner import Owner


# ==================== REPOSITORIO: PROPIETARIO ====================
class OwnerRepository:
    def __init__(self, db: Session):
        # Sesión activa de la base de datos
        self.db = db

    def get_by_id(self, owner_id: UUID) -> Optional[Owner]:
        """
        Busca un propietario por su ID único (UUID)
        """
        return self.db.query(Owner).filter(Owner.id == owner_id).first()

    def get_by_correo(self, correo: str) -> Optional[Owner]:
        """
        Busca un propietario por su correo electrónico
        """
        return self.db.query(Owner).filter(Owner.correo == correo).first()

    def get_by_documento(self, documento: str) -> Optional[Owner]:
        """
        Busca un propietario por su documento de identidad
        """
        return self.db.query(Owner).filter(Owner.documento == documento).first()

    def exists_duplicate(self, correo: str, documento: str) -> bool:
        """
        Verifica si ya existe un propietario con el mismo correo o documento.
        Retorna True si se encuentra duplicado.
        """
        return self.db.query(Owner.id).filter(
            or_(Owner.correo == correo, Owner.documento == documento)
        ).first() is not None

    def create(self, owner: Owner) -> Owner:
        """
        Crea un nuevo propietario en la base de datos.
        Guarda y refresca el objeto después de la inserción.
        """
        self.db.add(owner)
        self.db.commit()
        self.db.refresh(owner)
        return owner
