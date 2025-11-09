"""
Modelo de Usuario - Representa la tabla de usuarios en la base de datos
Roles: superadmin, veterinario, auxiliar, propietario
"""

from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    """Enumeración de roles de usuario"""
    SUPERADMIN = "superadmin"
    VETERINARIO = "veterinario"
    AUXILIAR = "auxiliar"
    PROPIETARIO = "propietario"


class User(Base):
    """
    Modelo de Usuario
    Implementa la entidad Usuario con diferentes roles y permisos
    """
    __tablename__ = "usuarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    nombre = Column(String(100), nullable=False)
    correo = Column(String(150), unique=True, nullable=False, index=True)
    telefono = Column(String(20), nullable=True)
    contrasena_hash = Column(String(255), nullable=False)
    rol = Column(SQLEnum(UserRole), nullable=False)
    activo = Column(Boolean, default=True, nullable=False)

    # Auditoría
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    creado_por = Column(UUID(as_uuid=True), nullable=True)

    def __repr__(self):
        return f"<Usuario {self.nombre} - {self.rol}>"

    def to_dict(self):
        """Convierte el usuario a diccionario (sin contraseña)"""
        return {
            "id": str(self.id),
            "nombre": self.nombre,
            "correo": self.correo,
            "telefono": self.telefono,
            "rol": self.rol.value,
            "activo": self.activo,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }