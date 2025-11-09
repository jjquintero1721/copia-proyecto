"""
Modelo de Mascota - Representa a las mascotas de los propietarios
Reglas: una mascota pertenece a un propietario
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


# ==================== MODELO: MASCOTA ====================
class Pet(Base):
    # Nombre de la tabla en la base de datos
    __tablename__ = "mascotas"

    # Identificador único de la mascota (UUID autogenerado)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Relación con el propietario (clave foránea hacia la tabla "propietarios")
    # Si el propietario se elimina, también se eliminarán sus mascotas (CASCADE)
    propietario_id = Column(UUID(as_uuid=True), ForeignKey("propietarios.id", ondelete="CASCADE"), nullable=False, index=True)

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
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Fecha de última actualización del registro
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relación con el modelo Owner: permite acceder a los datos del propietario desde la mascota
    owner = relationship("Owner", backref="mascotas")
