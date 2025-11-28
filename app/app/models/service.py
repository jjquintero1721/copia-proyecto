"""
Modelo de Servicio - Representa los servicios ofrecidos por la clínica
RF-09: Gestión de servicios (consultas, vacunas, cirugías, etc.)
"""

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid

from app.database import Base


class Service(Base):
    """
    Modelo de Servicio ofrecido por la clínica
    """
    __tablename__ = "servicios"

    # Identificador único del servicio
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Nombre del servicio (ej: "Consulta general", "Vacunación", "Cirugía")
    nombre = Column(String(150), nullable=False, unique=True)

    # Descripción detallada del servicio
    descripcion = Column(String(500), nullable=True)

    # Duración estimada del servicio en minutos
    duracion_minutos = Column(Integer, nullable=False, default=30)

    # Costo aproximado del servicio
    costo = Column(Float, nullable=False, default=0.0)

    # Estado del servicio (activo/inactivo)
    activo = Column(Boolean, default=True, nullable=False)

    # Auditoría
    fecha_creacion = Column(
        DateTime(timezone=True),  # ← Agregar timezone=True
        default=lambda: datetime.now(timezone.utc),  # ← Usar lambda y timezone.utc
        nullable=False
    )
    fecha_actualizacion = Column(
        DateTime(timezone=True),  # ← Agregar timezone=True
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)  # ← Usar lambda
    )
    creado_por = Column(UUID(as_uuid=True), nullable=True)

    def __repr__(self):
        return f"<Servicio {self.nombre} - ${self.costo}>"

    def to_dict(self):
        """Convierte el servicio a diccionario"""
        return {
            "id": str(self.id),
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "duracion_minutos": self.duracion_minutos,
            "costo": self.costo,
            "activo": self.activo,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }