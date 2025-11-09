"""
Repositorio de Usuarios - Capa de acceso a datos
Encapsula las operaciones CRUD sobre el modelo User
"""

from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from uuid import UUID

from app.models.user import User, UserRole


class UserRepository:
    """
    Repositorio para operaciones de base de datos sobre usuarios
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, user: User) -> User:
        """Crea un nuevo usuario en la base de datos"""
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Obtiene un usuario por su ID"""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_correo(self, correo: str) -> Optional[User]:
        """Obtiene un usuario por su correo electrónico"""
        return self.db.query(User).filter(User.correo == correo).first()

    def get_all(self, skip: int = 0, limit: int = 100, activo: Optional[bool] = None) -> List[User]:
        """Obtiene todos los usuarios con paginación"""
        query = self.db.query(User)

        if activo is not None:
            query = query.filter(User.activo == activo)

        return query.offset(skip).limit(limit).all()

    def get_by_rol(self, rol: UserRole, activo: bool = True) -> List[User]:
        """Obtiene usuarios por rol"""
        query = self.db.query(User).filter(User.rol == rol)

        if activo:
            query = query.filter(User.activo == activo)

        return query.all()

    def update(self, user: User) -> User:
        """Actualiza un usuario existente"""
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user: User) -> None:
        """Elimina un usuario (borrado físico - no recomendado en producción)"""
        self.db.delete(user)
        self.db.commit()

    def soft_delete(self, user: User) -> User:
        """Desactiva un usuario (borrado lógico)"""
        user.activo = False
        return self.update(user)

    def exists_by_correo(self, correo: str, exclude_id: Optional[UUID] = None) -> bool:
        """Verifica si existe un usuario con el correo dado"""
        query = self.db.query(User).filter(User.correo == correo)

        if exclude_id:
            query = query.filter(User.id != exclude_id)

        return query.first() is not None

    def count_all(self) -> int:
        """Cuenta todos los usuarios"""
        return self.db.query(User).count()

    def count_by_rol(self, rol: UserRole) -> int:
        """Cuenta usuarios por rol"""
        return self.db.query(User).filter(User.rol == rol).count()

    def search(self, search_term: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Busca usuarios por nombre o correo"""
        search_pattern = f"%{search_term}%"
        return self.db.query(User).filter(
            or_(
                User.nombre.ilike(search_pattern),
                User.correo.ilike(search_pattern)
            )
        ).offset(skip).limit(limit).all()