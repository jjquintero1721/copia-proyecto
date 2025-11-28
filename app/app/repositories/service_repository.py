"""
Repositorio de Servicios - Capa de acceso a datos
RF-09: Gestión de servicios ofrecidos
"""

from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from uuid import UUID

from app.models.service import Service


class ServiceRepository:
    """
    Repositorio para operaciones de base de datos sobre servicios
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, service: Service) -> Service:
        """Crea un nuevo servicio"""
        self.db.add(service)
        self.db.commit()
        self.db.refresh(service)
        return service

    def get_by_id(self, service_id: UUID) -> Optional[Service]:
        """Obtiene un servicio por ID"""
        return self.db.query(Service).filter(Service.id == service_id).first()

    def get_by_nombre(self, nombre: str) -> Optional[Service]:
        """Obtiene un servicio por nombre"""
        return self.db.query(Service).filter(Service.nombre == nombre).first()

    def get_all(self, skip: int = 0, limit: int = 100, activo: Optional[bool] = None) -> List[Service]:
        """Obtiene todos los servicios con filtros opcionales"""
        query = self.db.query(Service)

        if activo is not None:
            query = query.filter(Service.activo == activo)

        return query.offset(skip).limit(limit).all()

    def update(self, service: Service) -> Service:
        """Actualiza un servicio existente"""
        self.db.commit()
        self.db.refresh(service)
        return service

    def soft_delete(self, service: Service) -> Service:
        """Desactiva un servicio (borrado lógico)"""
        service.activo = False
        return self.update(service)

    def exists_by_nombre(self, nombre: str, exclude_id: Optional[UUID] = None) -> bool:
        """Verifica si existe un servicio con el nombre dado"""
        query = self.db.query(Service).filter(Service.nombre == nombre)

        if exclude_id:
            query = query.filter(Service.id != exclude_id)

        return query.first() is not None

    def search(self, search_term: str, skip: int = 0, limit: int = 100) -> List[Service]:
        """Busca servicios por nombre o descripción"""
        search_pattern = f"%{search_term}%"
        return self.db.query(Service).filter(
            or_(
                Service.nombre.ilike(search_pattern),
                Service.descripcion.ilike(search_pattern)
            )
        ).offset(skip).limit(limit).all()