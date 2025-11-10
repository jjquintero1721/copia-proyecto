"""
Modelo de Mascota - Representa a las mascotas de los propietarios
RF-04: Registro de mascotas
RN06: Mascota vinculada a propietario
RN07: No duplicar nombre+especie por propietario
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.database import Base


class Pet(Base):
    """
    Modelo de Mascota - Representa a las mascotas de los propietarios

    Cada mascota:
    - Pertenece a un propietario
    - Tiene una historia clínica asociada (creada automáticamente)
    - Puede tener microchip único
    - Puede estar activa o inactiva
    """
    # Nombre de la tabla en la base de datos
    __tablename__ = "mascotas"

    # Identificador único de la mascota (UUID autogenerado)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Relación con el propietario (clave foránea hacia la tabla "propietarios")
    # Si el propietario se elimina, también se eliminarán sus mascotas (CASCADE)
    propietario_id = Column(
        UUID(as_uuid=True),
        ForeignKey("propietarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Nombre de la mascota
    nombre = Column(String(120), nullable=False)

    # Especie de la mascota (ej: perro, gato, etc.)
    especie = Column(String(60), nullable=False)

    # Raza de la mascota (opcional)
    raza = Column(String(120), nullable=True)

    # Código o número de microchip único (opcional, con índice)
    microchip = Column(String(60), nullable=True, unique=True, index=True)

    # Fecha de nacimiento de la mascota (opcional)
    fecha_nacimiento = Column(Date, nullable=True)

    # Estado de la mascota (activa o inactiva)
    activo = Column(Boolean, default=True, nullable=False)

    # Fecha de creación del registro
    # CORRECCIÓN: Usar datetime.now(timezone.utc) en lugar de datetime.utcnow()
    fecha_creacion = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Fecha de última actualización del registro
    # CORRECCIÓN: Usar datetime.now(timezone.utc) en lugar de datetime.utcnow()
    fecha_actualizacion = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relación con el modelo Owner: permite acceder a los datos del propietario desde la mascota
    owner = relationship("Owner", backref="mascotas")

    triages = relationship("Triage", back_populates="mascota", cascade="all, delete-orphan")

    # Relación con historia clínica (uno a uno)
    historia_clinica = relationship(
        "MedicalHistory",
        back_populates="mascota",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        """Representación en string del modelo"""
        return f"<Pet {self.nombre} ({self.especie}) - Owner: {self.propietario_id}>"

    def to_dict(self):
        """Convierte la mascota a diccionario"""
        return {
            "id": str(self.id),
            "propietario_id": str(self.propietario_id),
            "nombre": self.nombre,
            "especie": self.especie,
            "raza": self.raza,
            "microchip": self.microchip,
            "fecha_nacimiento": self.fecha_nacimiento.isoformat() if self.fecha_nacimiento else None,
            "activo": self.activo,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "fecha_actualizacion": self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
        }