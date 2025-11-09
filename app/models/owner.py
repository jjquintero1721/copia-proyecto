from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.database import Base


# ==================== MODELO: PROPIETARIO ====================
class Owner(Base):
    # Nombre de la tabla en la base de datos
    __tablename__ = "propietarios"

    # Identificador único del propietario (UUID autogenerado)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Nombre completo del propietario
    nombre = Column(String(120), nullable=False)

    # Correo electrónico (único y con índice para búsqueda rápida)
    correo = Column(String(150), nullable=False, unique=True, index=True)

    # Documento de identificación (único y con índice)
    documento = Column(String(50), nullable=False, unique=True, index=True)

    # Teléfono de contacto (opcional)
    telefono = Column(String(20), nullable=True)

    # Estado del propietario (activo/inactivo)
    activo = Column(Boolean, default=True, nullable=False)

    # Fecha de creación del registro (automática)
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Fecha de última actualización (automática al modificar el registro)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
