"""
Modelo de Memento - Patrón Memento para versionado de historias clínicas
RN10-1: Las historias no pueden eliminarse
RN10-2: Registro de cambios con fecha, hora y usuario
RNF-07: Auditoría
RNF-08: Recuperación
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.database import Base


class MedicalHistoryMemento(Base):
    """
    Patrón Memento - Almacena snapshots de consultas para versionado

    Permite:
    - Mantener historial de versiones
    - Recuperar estados anteriores
    - Auditoría de cambios
    - Cumplir con RN10-1 (no eliminación)
    """
    __tablename__ = "historias_clinicas_mementos"

    # Identificador único del memento
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Relación con la consulta original
    consulta_id = Column(
        UUID(as_uuid=True),
        ForeignKey("consultas.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Versión guardada
    version = Column(Integer, nullable=False)

    # Estado guardado (JSON con todos los datos de la consulta)
    estado = Column(JSON, nullable=False)

    # Auditoría
    fecha_creacion = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    creado_por = Column(UUID(as_uuid=True), nullable=False)
    descripcion_cambio = Column(String(500), nullable=True)  # Descripción del cambio realizado

    # Relación
    consulta = relationship("Consultation", foreign_keys=[consulta_id])

    def __repr__(self):
        return f"<Memento {self.id} - Consulta: {self.consulta_id} - v{self.version}>"

    def to_dict(self):
        """Convierte el memento a diccionario"""
        return {
            "id": str(self.id),
            "consulta_id": str(self.consulta_id),
            "version": self.version,
            "estado": self.estado,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "creado_por": str(self.creado_por),
            "descripcion_cambio": self.descripcion_cambio
        }