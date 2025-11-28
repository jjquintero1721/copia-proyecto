"""
Repositorio de Consultas - Capa de acceso a datos
RF-07: Gestión de historias clínicas
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import Optional, List
from uuid import UUID

from app.models.consultation import Consultation
from app.models.medical_history_memento import MedicalHistoryMemento


class ConsultationRepository:
    """
    Repositorio para operaciones CRUD sobre consultas
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, consultation: Consultation) -> Consultation:
        """Crea una nueva consulta"""
        self.db.add(consultation)
        self.db.commit()
        self.db.refresh(consultation)
        return consultation

    def get_by_id(self, consultation_id: UUID) -> Optional[Consultation]:
        """Obtiene una consulta por ID"""
        return self.db.query(Consultation).filter(
            Consultation.id == consultation_id
        ).first()

    def get_by_historia_clinica(
        self,
        historia_clinica_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Consultation]:
        """Obtiene todas las consultas de una historia clínica"""
        return self.db.query(Consultation).filter(
            Consultation.historia_clinica_id == historia_clinica_id
        ).order_by(desc(Consultation.fecha_hora)).offset(skip).limit(limit).all()

    def get_by_veterinario(
        self,
        veterinario_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Consultation]:
        """Obtiene todas las consultas realizadas por un veterinario"""
        return self.db.query(Consultation).filter(
            Consultation.veterinario_id == veterinario_id
        ).order_by(desc(Consultation.fecha_hora)).offset(skip).limit(limit).all()

    def get_by_cita(self, cita_id: UUID) -> Optional[Consultation]:
        """Obtiene la consulta asociada a una cita"""
        return self.db.query(Consultation).filter(
            Consultation.cita_id == cita_id
        ).first()

    def update(self, consultation: Consultation) -> Consultation:
        """Actualiza una consulta existente"""
        self.db.commit()
        self.db.refresh(consultation)
        return consultation

    def count_by_historia_clinica(self, historia_clinica_id: UUID) -> int:
        """Cuenta las consultas de una historia clínica"""
        return self.db.query(Consultation).filter(
            Consultation.historia_clinica_id == historia_clinica_id
        ).count()

    # Métodos para Memento Pattern
    def save_memento(self, memento: MedicalHistoryMemento) -> MedicalHistoryMemento:
        """Guarda un memento (snapshot) de una consulta"""
        self.db.add(memento)
        self.db.commit()
        self.db.refresh(memento)
        return memento

    def get_mementos_by_consulta(
        self,
        consulta_id: UUID,
        skip: int = 0,
        limit: int = 50
    ) -> List[MedicalHistoryMemento]:
        """Obtiene el historial de versiones de una consulta"""
        return self.db.query(MedicalHistoryMemento).filter(
            MedicalHistoryMemento.consulta_id == consulta_id
        ).order_by(desc(MedicalHistoryMemento.version)).offset(skip).limit(limit).all()

    def get_memento_by_version(
        self,
        consulta_id: UUID,
        version: int
    ) -> Optional[MedicalHistoryMemento]:
        """Obtiene una versión específica de una consulta"""
        return self.db.query(MedicalHistoryMemento).filter(
            and_(
                MedicalHistoryMemento.consulta_id == consulta_id,
                MedicalHistoryMemento.version == version
            )
        ).first()