"""
Repositorio de Movimientos de Inventario - Capa de acceso a datos
RF-10: Registro de movimientos de inventario
RNF-07: Auditoría completa
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date

from app.models.inventory_movement import InventoryMovement, MovementType


class InventoryMovementRepository:
    """
    Repositorio para operaciones de base de datos sobre movimientos de inventario
    Principio de Responsabilidad Única: Solo acceso a datos de movimientos
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, movement: InventoryMovement) -> InventoryMovement:
        """Crea un nuevo movimiento de inventario"""
        self.db.add(movement)
        self.db.commit()
        self.db.refresh(movement)
        return movement

    def get_by_id(self, movement_id: UUID) -> Optional[InventoryMovement]:
        """Obtiene un movimiento por ID"""
        return self.db.query(InventoryMovement).filter(
            InventoryMovement.id == movement_id
        ).first()

    def get_all(
            self,
            skip: int = 0,
            limit: int = 100,
            medicamento_id: Optional[UUID] = None,
            tipo: Optional[MovementType] = None,
            fecha_desde: Optional[datetime] = None,
            fecha_hasta: Optional[datetime] = None
    ) -> List[InventoryMovement]:
        """Obtiene todos los movimientos con filtros opcionales"""
        query = self.db.query(InventoryMovement).options(
            joinedload(InventoryMovement.medicamento),
            joinedload(InventoryMovement.usuario)
        )

        if medicamento_id:
            query = query.filter(InventoryMovement.medicamento_id == medicamento_id)

        if tipo:
            query = query.filter(InventoryMovement.tipo == tipo)

        if fecha_desde:
            query = query.filter(InventoryMovement.fecha_movimiento >= fecha_desde)

        if fecha_hasta:
            query = query.filter(InventoryMovement.fecha_movimiento <= fecha_hasta)

        return query.order_by(desc(InventoryMovement.fecha_movimiento)).offset(skip).limit(limit).all()

    def get_by_medication(
            self,
            medicamento_id: UUID,
            limit: int = 50
    ) -> List[InventoryMovement]:
        """Obtiene el historial de movimientos de un medicamento específico"""
        return self.db.query(InventoryMovement).filter(
            InventoryMovement.medicamento_id == medicamento_id
        ).order_by(desc(InventoryMovement.fecha_movimiento)).limit(limit).all()

    def get_movements_by_date_range(
            self,
            fecha_inicio: date,
            fecha_fin: date,
            tipo: Optional[MovementType] = None
    ) -> List[InventoryMovement]:
        """Obtiene movimientos en un rango de fechas"""
        query = self.db.query(InventoryMovement).filter(
            and_(
                InventoryMovement.fecha_movimiento >= fecha_inicio,
                InventoryMovement.fecha_movimiento <= fecha_fin
            )
        )

        if tipo:
            query = query.filter(InventoryMovement.tipo == tipo)

        return query.order_by(desc(InventoryMovement.fecha_movimiento)).all()

    def get_by_user(self, usuario_id: UUID, limit: int = 100) -> List[InventoryMovement]:
        """Obtiene movimientos realizados por un usuario"""
        return self.db.query(InventoryMovement).filter(
            InventoryMovement.realizado_por == usuario_id
        ).order_by(desc(InventoryMovement.fecha_movimiento)).limit(limit).all()

    def get_total_movements_by_type(self, medicamento_id: UUID) -> dict:
        """Obtiene el total de movimientos por tipo para un medicamento"""
        result = {}
        for tipo in MovementType:
            total = self.db.query(InventoryMovement).filter(
                and_(
                    InventoryMovement.medicamento_id == medicamento_id,
                    InventoryMovement.tipo == tipo
                )
            ).count()
            result[tipo.value] = total
        return result