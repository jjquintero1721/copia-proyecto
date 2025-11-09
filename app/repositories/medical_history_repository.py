"""
Repositorio de Historia Clínica - Capa de acceso a datos
RF-04: Creación automática al registrar mascota
RF-07: Gestión de historias clínicas
"""

from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from app.models.medical_history import MedicalHistory


class MedicalHistoryRepository:
    """
    Repositorio para operaciones sobre historias clínicas
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, medical_history: MedicalHistory) -> MedicalHistory:
        """Crea una nueva historia clínica"""
        self.db.add(medical_history)
        self.db.commit()
        self.db.refresh(medical_history)
        return medical_history

    def get_by_id(self, historia_id: UUID) -> Optional[MedicalHistory]:
        """Obtiene una historia clínica por ID"""
        return self.db.query(MedicalHistory).filter(
            MedicalHistory.id == historia_id
        ).first()

    def get_by_numero(self, numero: str) -> Optional[MedicalHistory]:
        """Obtiene una historia clínica por número"""
        return self.db.query(MedicalHistory).filter(
            MedicalHistory.numero == numero
        ).first()

    def get_by_mascota_id(self, mascota_id: UUID) -> Optional[MedicalHistory]:
        """Obtiene la historia clínica de una mascota"""
        return self.db.query(MedicalHistory).filter(
            MedicalHistory.mascota_id == mascota_id
        ).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[MedicalHistory]:
        """Obtiene todas las historias clínicas"""
        return self.db.query(MedicalHistory).offset(skip).limit(limit).all()

    def update(self, medical_history: MedicalHistory) -> MedicalHistory:
        """Actualiza una historia clínica"""
        self.db.commit()
        self.db.refresh(medical_history)
        return medical_history

    def generate_numero(self, year: int = None) -> str:
        """
        Genera un número único de historia clínica
        Formato: HC-YYYY-XXXX
        """
        if year is None:
            year = datetime.now().year

        # Obtener el último número del año
        last_historia = self.db.query(MedicalHistory).filter(
            MedicalHistory.numero.like(f"HC-{year}-%")
        ).order_by(MedicalHistory.numero.desc()).first()

        if last_historia:
            # Extraer el último número y sumar 1
            last_num = int(last_historia.numero.split("-")[2])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"HC-{year}-{new_num:04d}"