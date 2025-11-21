"""
Modelo de Decoradores de Citas - Persiste decoradores aplicados a citas
Patrón Decorator: Almacena las extensiones dinámicas de citas
RF-05: Gestión de citas
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum

from app.database import Base


class DecoratorType(str, enum.Enum):
    """
    Tipos de decoradores que se pueden aplicar a una cita
    """
    RECORDATORIO = "recordatorio"
    NOTAS_ESPECIALES = "notas_especiales"
    PRIORIDAD = "prioridad"


class AppointmentDecorator(Base):
    """
    Modelo que persiste los decoradores aplicados a citas

    Patrón Decorator: Permite agregar dinámicamente características
    a las citas sin modificar su estructura base

    RF-05: Gestión de citas con extensiones
    """
    __tablename__ = "appointment_decorators"

    # Identificador único
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Relación con la cita
    cita_id = Column(
        UUID(as_uuid=True),
        ForeignKey("citas.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Tipo de decorador
    tipo_decorador = Column(
        SQLEnum(DecoratorType),
        nullable=False,
        index=True
    )

    # Configuración del decorador (JSON flexible)
    configuracion = Column(JSONB, nullable=False, default=dict)

    # Estado activo/inactivo
    activo = Column(String(20), nullable=False, default="activo")

    # Auditoría
    fecha_creacion = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    fecha_actualizacion = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    creado_por = Column(UUID(as_uuid=True), nullable=True)

    # Relaciones
    cita = relationship("Appointment", backref="decoradores")

    def __repr__(self):
        return f"<AppointmentDecorator {self.tipo_decorador.value} - Cita: {self.cita_id}>"