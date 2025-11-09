from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.database import Base


# ==================== MODELO: HISTORIA CLÍNICA ====================
class MedicalHistory(Base):
    # Nombre de la tabla en la base de datos
    __tablename__ = "historias_clinicas"

    # Identificador único de la historia clínica (UUID autogenerado)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Relación con la mascota: cada historia pertenece a una mascota
    # ondelete="CASCADE" elimina la historia si se elimina la mascota
    mascota_id = Column(UUID(as_uuid=True), ForeignKey("mascotas.id", ondelete="CASCADE"), nullable=False, index=True)

    # Campo para notas o registros clínicos adicionales (texto libre)
    notas = Column(Text, nullable=True)

    # Fecha de creación de la historia clínica (se asigna automáticamente al crear el registro)
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Fecha de última actualización (se actualiza automáticamente al modificar el registro)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
