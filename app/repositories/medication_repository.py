"""
Repositorio de Medicamentos - Capa de acceso a datos
RF-10: Operaciones CRUD sobre medicamentos
"""

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone

from app.models.medication import Medication, MedicationType


class MedicationRepository:
    """
    Repositorio para operaciones de base de datos sobre medicamentos
    Principio de Responsabilidad Única: Solo acceso a datos
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, medication: Medication) -> Medication:
        """Crea un nuevo medicamento"""
        self.db.add(medication)
        self.db.commit()
        self.db.refresh(medication)
        return medication

    def get_by_id(self, medication_id: UUID) -> Optional[Medication]:
        """Obtiene un medicamento por ID"""
        return self.db.query(Medication).filter(
            Medication.id == medication_id,
            Medication.activo == True
        ).first()

    def get_by_nombre(self, nombre: str) -> Optional[Medication]:
        """Obtiene un medicamento por nombre"""
        return self.db.query(Medication).filter(
            Medication.nombre == nombre,
            Medication.activo == True
        ).first()

    def get_all(
            self,
            skip: int = 0,
            limit: int = 100,
            tipo: Optional[MedicationType] = None,
            activo: Optional[bool] = True,
            solo_bajos_stock: bool = False
    ) -> List[Medication]:
        """Obtiene todos los medicamentos con filtros opcionales"""
        query = self.db.query(Medication)

        if activo is not None:
            query = query.filter(Medication.activo == activo)

        if tipo:
            query = query.filter(Medication.tipo == tipo)

        if solo_bajos_stock:
            # Filtrar medicamentos con stock <= stock_minimo
            query = query.filter(Medication.stock_actual <= Medication.stock_minimo)

        return query.order_by(Medication.nombre).offset(skip).limit(limit).all()

    def get_low_stock_medications(self) -> List[Medication]:
        """
        Obtiene medicamentos con stock bajo (RF-10)
        Stock actual <= stock mínimo
        """
        return self.db.query(Medication).filter(
            and_(
                Medication.activo == True,
                Medication.stock_actual <= Medication.stock_minimo
            )
        ).order_by(Medication.stock_actual).all()

    def get_expired_medications(self) -> List[Medication]:
        """Obtiene medicamentos vencidos"""
        now = datetime.now(timezone.utc)
        return self.db.query(Medication).filter(
            and_(
                Medication.activo == True,
                Medication.fecha_vencimiento != None,
                Medication.fecha_vencimiento <= now
            )
        ).all()

    def update(self, medication: Medication) -> Medication:
        """Actualiza un medicamento existente"""
        medication.actualizado_en = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(medication)
        return medication

    def update_stock(self, medication_id: UUID, nueva_cantidad: int) -> Medication:
        """
        Actualiza el stock de un medicamento

        Args:
            medication_id: ID del medicamento
            nueva_cantidad: Nueva cantidad en stock

        Returns:
            Medicamento actualizado
        """
        medication = self.get_by_id(medication_id)
        if not medication:
            raise ValueError("Medicamento no encontrado")

        medication.stock_actual = nueva_cantidad
        medication.actualizado_en = datetime.now(timezone.utc)
        return self.update(medication)

    def soft_delete(self, medication: Medication) -> Medication:
        """Desactiva un medicamento (borrado lógico)"""
        medication.activo = False
        return self.update(medication)

    def exists_by_nombre(self, nombre: str, exclude_id: Optional[UUID] = None) -> bool:
        """Verifica si existe un medicamento con el nombre dado"""
        query = self.db.query(Medication).filter(Medication.nombre == nombre)

        if exclude_id:
            query = query.filter(Medication.id != exclude_id)

        return query.first() is not None

    def search(self, search_term: str, skip: int = 0, limit: int = 100) -> List[Medication]:
        """Busca medicamentos por nombre, principio activo o descripción"""
        search_pattern = f"%{search_term}%"
        return self.db.query(Medication).filter(
            and_(
                Medication.activo == True,
                or_(
                    Medication.nombre.ilike(search_pattern),
                    Medication.principio_activo.ilike(search_pattern),
                    Medication.descripcion.ilike(search_pattern)
                )
            )
        ).offset(skip).limit(limit).all()

    def count_by_tipo(self) -> dict:
        """Cuenta medicamentos por tipo"""
        result = {}
        for tipo in MedicationType:
            count = self.db.query(Medication).filter(
                and_(
                    Medication.tipo == tipo,
                    Medication.activo == True
                )
            ).count()
            result[tipo.value] = count
        return result