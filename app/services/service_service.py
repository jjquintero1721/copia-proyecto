"""
Servicio de Servicios Ofrecidos - Lógica de negocio
RF-09: Gestión de servicios (consultas, vacunas, cirugías, etc.)
"""

from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone

from app.models.service import Service
from app.repositories.service_repository import ServiceRepository
from app.schemas.service_schema import ServiceCreate, ServiceUpdate


class ServiceService:
    """
    Servicio para gestión de servicios ofrecidos por la clínica
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = ServiceRepository(db)

    def create_service(
        self,
        service_data: ServiceCreate,
        creado_por: Optional[UUID] = None
    ) -> Service:
        """
        Crea un nuevo servicio

        Args:
            service_data: Datos del servicio
            creado_por: ID del usuario que crea el servicio

        Returns:
            Service creado

        Raises:
            ValueError: Si el nombre ya existe
        """
        # Validar nombre único
        if self.repository.exists_by_nombre(service_data.nombre):
            raise ValueError(f"Ya existe un servicio con el nombre '{service_data.nombre}'")

        # Crear servicio
        service = Service(
            nombre=service_data.nombre,
            descripcion=service_data.descripcion,
            duracion_minutos=service_data.duracion_minutos,
            costo=service_data.costo,
            creado_por=creado_por
        )

        return self.repository.create(service)

    def get_service_by_id(self, service_id: UUID) -> Optional[Service]:
        """Obtiene un servicio por ID"""
        return self.repository.get_by_id(service_id)

    def get_all_services(
        self,
        skip: int = 0,
        limit: int = 100,
        activo: Optional[bool] = None
    ) -> List[Service]:
        """
        Obtiene todos los servicios con filtros opcionales

        Args:
            skip: Registros a omitir (paginación)
            limit: Límite de registros
            activo: Filtrar por estado activo/inactivo

        Returns:
            Lista de servicios
        """
        return self.repository.get_all(skip, limit, activo)

    def get_active_services(self, skip: int = 0, limit: int = 100) -> List[Service]:
        """Obtiene solo servicios activos (para agendar citas)"""
        return self.repository.get_all(skip, limit, activo=True)

    def update_service(
        self,
        service_id: UUID,
        service_data: ServiceUpdate
    ) -> Service:
        """
        Actualiza un servicio existente

        Args:
            service_id: ID del servicio
            service_data: Datos a actualizar

        Returns:
            Service actualizado

        Raises:
            ValueError: Si el servicio no existe o el nombre está duplicado
        """
        service = self.repository.get_by_id(service_id)
        if not service:
            raise ValueError("Servicio no encontrado")

        # Validar nombre único si se está cambiando
        if service_data.nombre and service_data.nombre != service.nombre:
            if self.repository.exists_by_nombre(service_data.nombre, exclude_id=service_id):
                raise ValueError(f"Ya existe un servicio con el nombre '{service_data.nombre}'")

        # Actualizar campos
        if service_data.nombre is not None:
            service.nombre = service_data.nombre
        if service_data.descripcion is not None:
            service.descripcion = service_data.descripcion
        if service_data.duracion_minutos is not None:
            service.duracion_minutos = service_data.duracion_minutos
        if service_data.costo is not None:
            service.costo = service_data.costo
        if service_data.activo is not None:
            service.activo = service_data.activo

        service.fecha_actualizacion = datetime.now(timezone.utc)

        return self.repository.update(service)

    def deactivate_service(self, service_id: UUID) -> Service:
        """
        Desactiva un servicio (borrado lógico)
        Los servicios inactivos no aparecen disponibles para agendar citas

        Args:
            service_id: ID del servicio

        Returns:
            Service desactivado

        Raises:
            ValueError: Si el servicio no existe
        """
        service = self.repository.get_by_id(service_id)
        if not service:
            raise ValueError("Servicio no encontrado")

        return self.repository.soft_delete(service)

    def search_services(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Service]:
        """
        Busca servicios por nombre o descripción

        Args:
            search_term: Término de búsqueda
            skip: Registros a omitir
            limit: Límite de registros

        Returns:
            Lista de servicios encontrados
        """
        return self.repository.search(search_term, skip, limit)

    def activate_service(self, service_id: UUID) -> Service:
        """
        Activa un servicio previamente desactivado

        Args:
            service_id: UUID del servicio a activar

        Returns:
            Service: Servicio activado

        Raises:
            ValueError: Si el servicio no existe

        **RF-09:** Gestión de servicios ofrecidos
        **Regla de negocio:** Solo usuarios con rol staff pueden activar servicios
        """
        # Buscar servicio
        service = self.repository.get_by_id(service_id)

        if not service:
            raise ValueError(f"Servicio con ID {service_id} no encontrado")

        # Activar servicio
        service.activo = True

        # Actualizar en base de datos
        return self.repository.update(service)
