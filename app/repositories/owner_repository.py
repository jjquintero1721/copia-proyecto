"""
Repositorio de Propietarios - Capa de acceso a datos
Encapsula las operaciones CRUD sobre el modelo Owner
CORRECCIÓN ARQUITECTURAL: Métodos para buscar por usuario_id
"""

from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from uuid import UUID

from app.models.owner import Owner


class OwnerRepository:
    """
    Repositorio para operaciones de base de datos sobre propietarios

    Incluye métodos para trabajar con usuario_id
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, owner_id: UUID) -> Optional[Owner]:
        """Busca un propietario por su ID único (UUID)"""
        return self.db.query(Owner).filter(Owner.id == owner_id).first()

    def get_by_usuario_id(self, usuario_id: UUID) -> Optional[Owner]:
        """
        Busca propietario por ID de usuario

        Permite encontrar el propietario asociado a un usuario

        Args:
            usuario_id: UUID del usuario

        Returns:
            Owner si existe, None si no
        """
        return self.db.query(Owner).filter(Owner.usuario_id == usuario_id).first()

    def get_by_correo(self, correo: str) -> Optional[Owner]:
        """Busca un propietario por su correo electrónico"""
        return self.db.query(Owner).filter(Owner.correo == correo).first()

    def get_by_documento(self, documento: str) -> Optional[Owner]:
        """Busca un propietario por su documento de identidad"""
        return self.db.query(Owner).filter(Owner.documento == documento).first()

    def exists_duplicate(self, correo: str, documento: str, usuario_id: Optional[UUID] = None) -> bool:
        """
        Verifica si ya existe un propietario con el mismo correo o documento.

        Excluir el propietario del usuario actual

        Args:
            correo: Correo a verificar
            documento: Documento a verificar
            usuario_id: ID del usuario a excluir de la búsqueda (opcional)

        Returns:
            True si se encuentra duplicado, False si no
        """
        query = self.db.query(Owner.id).filter(
            or_(Owner.correo == correo, Owner.documento == documento)
        )

        # Si se proporciona usuario_id, excluir ese propietario
        if usuario_id:
            query = query.filter(Owner.usuario_id != usuario_id)

        return query.first() is not None

    def exists_by_usuario_id(self, usuario_id: UUID) -> bool:
        """
        Verifica si existe propietario para un usuario

        Útil para validar antes de crear un Owner

        Args:
            usuario_id: UUID del usuario

        Returns:
            True si existe, False si no
        """
        return self.db.query(Owner.id).filter(Owner.usuario_id == usuario_id).first() is not None

    def create(self, owner: Owner) -> Owner:
        """
        Crea un nuevo propietario en la base de datos.
        Guarda y refresca el objeto después de la inserción.
        """
        self.db.add(owner)
        self.db.commit()
        self.db.refresh(owner)
        return owner

    def update(self, owner: Owner) -> Owner:
        """Actualiza un propietario existente"""
        self.db.commit()
        self.db.refresh(owner)
        return owner

    def delete(self, owner: Owner) -> None:
        """Elimina un propietario (borrado físico)"""
        self.db.delete(owner)
        self.db.commit()

    def soft_delete(self, owner: Owner) -> Owner:
        """Desactiva un propietario (borrado lógico)"""
        owner.activo = False
        return self.update(owner)