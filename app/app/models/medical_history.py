"""
Modelo de Historia Clínica - Actualizado con relación a consultas
RF-04: Creación automática al registrar mascota
RF-07: Gestión de historias clínicas
"""

from sqlalchemy import Column, DateTime, ForeignKey, Text, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.database import Base


class MedicalHistory(Base):
    """
    Modelo de Historia Clínica - Contenedor principal del historial médico de una mascota
    """
    __tablename__ = "historias_clinicas"

    # Identificador único de la historia clínica
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Relación con la mascota (ondelete="CASCADE")
    mascota_id = Column(
        UUID(as_uuid=True),
        ForeignKey("mascotas.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # Una mascota = una historia clínica
        index=True
    )

    # Número de historia clínica (formato: HC-YYYY-XXXX)
    numero = Column(String(20), unique=True, nullable=False, index=True)

    # RN10-1: Campo para soft delete (aunque nunca debería usarse según la regla)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # Notas generales de la historia clínica
    notas = Column(Text, nullable=True)

    # Auditoría
    fecha_creacion = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    fecha_actualizacion = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relaciones
    mascota = relationship("Pet", back_populates="historia_clinica")
    consultas = relationship("Consultation", back_populates="historia_clinica", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<HistoriaClinica {self.numero} - Mascota: {self.mascota_id}>"

    def to_dict(self):
        """Convierte la historia clínica a diccionario"""
        return {
            "id": str(self.id),
            "mascota_id": str(self.mascota_id),
            "numero": self.numero,
            "is_deleted": self.is_deleted,
            "notas": self.notas,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "fecha_actualizacion": self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None,
            "total_consultas": len(self.consultas) if self.consultas else 0
        }