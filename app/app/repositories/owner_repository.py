"""
Repositorio de Propietarios - Actualización con métodos de consulta adicionales
Encapsula las operaciones CRUD sobre el modelo Owner
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import Optional, List, Any
from uuid import UUID

from app.models.owner import Owner


class OwnerRepository:
    """
    Repositorio para operaciones de base de datos sobre propietarios
    Actualizado con métodos de consulta adicionales
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, owner_id: UUID) -> Optional[Owner]:
        """
        Busca un propietario por su ID único (UUID)

        Args:
            owner_id: UUID del propietario

        Returns:
            Owner si existe, None si no
        """
        return (
            self.db.query(Owner)
            .options(joinedload(Owner.mascotas))
            .filter(Owner.id == owner_id)
            .first()
        )

    def get_by_usuario_id(self, usuario_id: UUID) -> Optional[Owner]:
        """
        Busca propietario por ID de usuario

        Args:
            usuario_id: UUID del usuario

        Returns:
            Owner si existe, None si no
        """
        return self.db.query(Owner).filter(Owner.usuario_id == usuario_id).first()

    def get_by_correo(self, correo: str) -> Optional[Owner]:
        """
        Busca un propietario por su correo electrónico

        Args:
            correo: Correo electrónico

        Returns:
            Owner si existe, None si no
        """
        return self.db.query(Owner).filter(Owner.correo == correo).first()

    def get_by_documento(self, documento: str) -> Optional[Owner]:
        """
        Busca un propietario por su documento de identidad

        Args:
            documento: Documento de identidad

        Returns:
            Owner si existe, None si no
        """
        return self.db.query(Owner).filter(Owner.documento == documento).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        activo: Optional[bool] = True
    ) -> list[type[Owner]]:
        """
        Obtiene todos los propietarios con paginación

        Args:
            skip: Número de registros a saltar
            limit: Máximo de registros a retornar
            activo: Filtrar por estado activo (None = todos)

        Returns:
            Lista de propietarios
        """
        query = self.db.query(Owner).options(joinedload(Owner.mascotas))

        if activo is not None:
            query = query.filter(Owner.activo == activo)

        return query.order_by(Owner.fecha_creacion.desc()).offset(skip).limit(limit).all()

    def count_all(self, activo: Optional[bool] = True) -> int:
        """
        Cuenta el total de propietarios

        Args:
            activo: Filtrar por estado activo (None = todos)

        Returns:
            Número total de propietarios
        """
        query = self.db.query(Owner)

        if activo is not None:
            query = query.filter(Owner.activo == activo)

        return query.count()

    def exists_duplicate(
        self,
        correo: str,
        documento: str,
        usuario_id: Optional[UUID] = None
    ) -> bool:
        """
        Verifica si ya existe un propietario con el mismo correo o documento

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

        if usuario_id:
            query = query.filter(Owner.usuario_id != usuario_id)

        return query.first() is not None

    def exists_by_usuario_id(self, usuario_id: UUID) -> bool:
        """
        Verifica si existe propietario para un usuario

        Args:
            usuario_id: UUID del usuario

        Returns:
            True si existe, False si no
        """
        return (
            self.db.query(Owner.id)
            .filter(Owner.usuario_id == usuario_id)
            .first() is not None
        )

    def create(self, owner: Owner) -> Owner:
        """
        Crea un nuevo propietario en la base de datos

        Args:
            owner: Instancia de Owner a crear

        Returns:
            Owner creado y refrescado
        """
        self.db.add(owner)
        self.db.commit()
        self.db.refresh(owner)
        return owner

    def update(self, owner: Owner) -> Owner:
        """
        Actualiza un propietario existente

        Args:
            owner: Instancia de Owner a actualizar

        Returns:
            Owner actualizado
        """
        self.db.commit()
        self.db.refresh(owner)
        return owner

    def delete(self, owner: Owner) -> None:
        """
        Elimina un propietario (borrado físico)

        Args:
            owner: Instancia de Owner a eliminar
        """
        self.db.delete(owner)
        self.db.commit()

    def soft_delete(self, owner: Owner) -> Owner:
        """
        Desactiva un propietario (borrado lógico)

        Args:
            owner: Instancia de Owner a desactivar

        Returns:
            Owner desactivado
        """
        owner.activo = False
        return self.update(owner)