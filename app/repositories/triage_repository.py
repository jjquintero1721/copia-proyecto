"""
Repositorio de Triage - Capa de acceso a datos
RF-08: Triage (clasificación de prioridad)
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from app.models.triage import Triage, TriagePriority
from app.models.pet import Pet   # ⭐ REQUERIDO PARA joinedload


class TriageRepository:
    """
    Repositorio para operaciones de base de datos sobre triages
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, triage: Triage) -> Triage:
        """Crea un nuevo registro de triage"""
        self.db.add(triage)
        self.db.commit()
        self.db.refresh(triage)
        return triage

    def get_by_id(self, triage_id: UUID) -> Optional[Triage]:
        """Obtiene un triage por ID"""
        return self.db.query(Triage).filter(Triage.id == triage_id).first()

    def get_by_cita_id(self, cita_id: UUID) -> Optional[Triage]:
        """Obtiene el triage asociado a una cita"""
        return self.db.query(Triage).filter(Triage.cita_id == cita_id).first()

    def get_by_mascota_id(
        self,
        mascota_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Triage]:
        """Obtiene todos los triages de una mascota"""
        return (
            self.db.query(Triage).options(
                joinedload(Triage.mascota).joinedload(Pet.owner),
                joinedload(Triage.usuario)
            )
            .filter(Triage.mascota_id == mascota_id)
            .order_by(desc(Triage.fecha_creacion))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        prioridad: Optional[TriagePriority] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None
    ) -> List[Triage]:
        """Obtiene todos los triages con filtros opcionales"""
        query = self.db.query(Triage).options(
            joinedload(Triage.mascota).joinedload(Pet.owner),  # ✅ relaciones completas
            joinedload(Triage.usuario)
        )

        if prioridad:
            query = query.filter(Triage.prioridad == prioridad)

        if fecha_desde:
            query = query.filter(Triage.fecha_creacion >= fecha_desde)

        if fecha_hasta:
            query = query.filter(Triage.fecha_creacion <= fecha_hasta)

        return (
            query
            .order_by(desc(Triage.fecha_creacion))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_urgentes_pendientes(self, limit: int = 50) -> List[Triage]:
        """
        Obtiene triages urgentes/altos que están pendientes de atención
        Útil para mostrar cola de prioridades en la interfaz
        """
        return (
            self.db.query(Triage)
            .filter(Triage.prioridad.in_([TriagePriority.URGENTE, TriagePriority.ALTA]))
            .order_by(
                Triage.prioridad.desc(),
                Triage.fecha_creacion
            )
            .limit(limit)
            .all()
        )

    def update(self, triage: Triage) -> Triage:
        """Actualiza un triage existente"""
        self.db.commit()
        self.db.refresh(triage)
        return triage

    def delete(self, triage: Triage) -> None:
        """Elimina un triage (borrado físico)"""
        self.db.delete(triage)
        self.db.commit()

    def count_by_prioridad(self, prioridad: TriagePriority) -> int:
        """Cuenta cuántos triages hay con una prioridad específica"""
        return (
            self.db.query(Triage)
            .filter(Triage.prioridad == prioridad)
            .count()
        )

    def exists_for_cita(self, cita_id: UUID) -> bool:
        """Verifica si ya existe un triage para una cita"""
        return (
            self.db.query(Triage)
            .filter(Triage.cita_id == cita_id)
            .first()
        ) is not None
