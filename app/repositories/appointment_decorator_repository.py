"""
Repositorio de Decoradores de Citas
Gestiona la persistencia de decoradores en la base de datos

Patrón Repository: Abstrae el acceso a datos
Principio Single Responsibility: Solo maneja persistencia de decoradores
"""

import logging
from typing import List, Optional, Any
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.appointment_decorator import (
    AppointmentDecorator,
    DecoratorType
)

logger = logging.getLogger(__name__)


class AppointmentDecoratorRepository:
    """
    Repositorio para gestionar decoradores de citas

    Operaciones CRUD sobre appointment_decorators
    Patrón Repository: Separa lógica de negocio de acceso a datos
    """

    def __init__(self, db: Session):
        """
        Args:
            db: Sesión de SQLAlchemy
        """
        self.db = db

    def create(
            self,
            cita_id: UUID,
            tipo_decorador: DecoratorType,
            configuracion: dict,
            creado_por: Optional[UUID] = None
    ) -> AppointmentDecorator:
        """
        Crea un nuevo decorador de cita

        Args:
            cita_id: ID de la cita
            tipo_decorador: Tipo de decorador
            configuracion: Configuración del decorador (JSON)
            creado_por: ID del usuario creador

        Returns:
            Decorador creado
        """
        decorator = AppointmentDecorator(
            cita_id=cita_id,
            tipo_decorador=tipo_decorador,
            configuracion=configuracion,
            activo="activo",
            creado_por=creado_por
        )

        self.db.add(decorator)
        self.db.commit()
        self.db.refresh(decorator)

        logger.info(
            f"✅ Decorador {tipo_decorador.value} creado para cita {cita_id}"
        )

        return decorator

    def get_by_id(self, decorator_id: UUID) -> Optional[AppointmentDecorator]:
        """
        Obtiene un decorador por su ID

        Args:
            decorator_id: ID del decorador

        Returns:
            Decorador encontrado o None
        """
        return self.db.query(AppointmentDecorator).filter(
            AppointmentDecorator.id == decorator_id
        ).first()

    def get_by_cita(
            self,
            cita_id: UUID,
            tipo_decorador: Optional[DecoratorType] = None,
            solo_activos: bool = True
    ) -> list[type[AppointmentDecorator]]:
        """
        Obtiene todos los decoradores de una cita

        Args:
            cita_id: ID de la cita
            tipo_decorador: Filtrar por tipo (opcional)
            solo_activos: Solo decoradores activos

        Returns:
            Lista de decoradores
        """
        query = self.db.query(AppointmentDecorator).filter(
            AppointmentDecorator.cita_id == cita_id
        )

        if tipo_decorador:
            query = query.filter(
                AppointmentDecorator.tipo_decorador == tipo_decorador
            )

        if solo_activos:
            query = query.filter(
                AppointmentDecorator.activo == "activo"
            )

        return query.all()

    def update(
            self,
            decorator_id: UUID,
            configuracion: Optional[dict] = None,
            activo: Optional[str] = None
    ) -> Optional[AppointmentDecorator]:
        """
        Actualiza un decorador existente

        Args:
            decorator_id: ID del decorador
            configuracion: Nueva configuración (opcional)
            activo: Nuevo estado activo/inactivo (opcional)

        Returns:
            Decorador actualizado o None si no existe
        """
        decorator = self.get_by_id(decorator_id)

        if not decorator:
            logger.warning(f"⚠️ Decorador {decorator_id} no encontrado")
            return None

        if configuracion is not None:
            decorator.configuracion = configuracion

        if activo is not None:
            decorator.activo = activo

        self.db.commit()
        self.db.refresh(decorator)

        logger.info(f"✅ Decorador {decorator_id} actualizado")

        return decorator

    def delete(self, decorator_id: UUID) -> bool:
        """
        Elimina un decorador (soft delete - marca como inactivo)

        Args:
            decorator_id: ID del decorador

        Returns:
            True si se eliminó, False si no existía
        """
        decorator = self.get_by_id(decorator_id)

        if not decorator:
            logger.warning(f"⚠️ Decorador {decorator_id} no encontrado")
            return False

        decorator.activo = "inactivo"
        self.db.commit()

        logger.info(f"🗑️ Decorador {decorator_id} eliminado (soft delete)")

        return True

    def hard_delete(self, decorator_id: UUID) -> bool:
        """
        Elimina permanentemente un decorador

        Args:
            decorator_id: ID del decorador

        Returns:
            True si se eliminó, False si no existía
        """
        decorator = self.get_by_id(decorator_id)

        if not decorator:
            logger.warning(f"⚠️ Decorador {decorator_id} no encontrado")
            return False

        self.db.delete(decorator)
        self.db.commit()

        logger.info(f"🗑️ Decorador {decorator_id} eliminado permanentemente")

        return True

    def desactivar_todos_por_cita(
            self,
            cita_id: UUID,
            tipo_decorador: Optional[DecoratorType] = None
    ) -> int:
        """
        Desactiva todos los decoradores de una cita

        Args:
            cita_id: ID de la cita
            tipo_decorador: Filtrar por tipo (opcional)

        Returns:
            Número de decoradores desactivados
        """
        query = self.db.query(AppointmentDecorator).filter(
            AppointmentDecorator.cita_id == cita_id,
            AppointmentDecorator.activo == "activo"
        )

        if tipo_decorador:
            query = query.filter(
                AppointmentDecorator.tipo_decorador == tipo_decorador
            )

        count = query.update(
            {"activo": "inactivo"},
            synchronize_session=False
        )

        self.db.commit()

        logger.info(
            f"🔄 {count} decoradores desactivados para cita {cita_id}"
        )

        return count

    def contar_por_tipo(
            self,
            cita_id: UUID,
            tipo_decorador: DecoratorType
    ) -> int:
        """
        Cuenta decoradores de un tipo específico para una cita

        Args:
            cita_id: ID de la cita
            tipo_decorador: Tipo de decorador

        Returns:
            Número de decoradores de ese tipo
        """
        return self.db.query(AppointmentDecorator).filter(
            AppointmentDecorator.cita_id == cita_id,
            AppointmentDecorator.tipo_decorador == tipo_decorador,
            AppointmentDecorator.activo == "activo"
        ).count()

    def existe_decorador(
            self,
            cita_id: UUID,
            tipo_decorador: DecoratorType
    ) -> bool:
        """
        Verifica si existe un decorador activo de un tipo para una cita

        Args:
            cita_id: ID de la cita
            tipo_decorador: Tipo de decorador

        Returns:
            True si existe, False si no
        """
        return self.contar_por_tipo(cita_id, tipo_decorador) > 0