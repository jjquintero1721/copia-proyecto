"""
Modelo de Propietario - Representa la tabla de propietarios en la base de datos
RF-04: Vinculación de propietarios con mascotas
RN06: Mascota vinculada a propietario
CORRECCIÓN ARQUITECTURAL: Propietario DEBE tener FK a Usuario
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.database import Base


class Owner(Base):
    """
    Modelo de Propietario - Información del cliente/dueño de mascotas

    Relación 1:1 con User:
    - Cada propietario está vinculado a un usuario del sistema
    - El usuario proporciona autenticación y autorización
    - Esta tabla almacena información adicional del cliente

    RF-01: Registro de usuarios (rol propietario)
    RN06: Mascota vinculada a propietario
    """
    __tablename__ = "propietarios"

    # Identificador único del propietario (UUID autogenerado)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # FK a usuarios (relación 1:1)
    # Cada propietario DEBE estar asociado a un usuario
    usuario_id = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # Relación 1:1
        index=True
    )
    # Relaciones
    mascotas = relationship(
        "Pet",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="select"
    )

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
    fecha_creacion = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Fecha de última actualización (automática al modificar el registro)
    fecha_actualizacion = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # ✅ Relación con User (1:1)
    usuario = relationship("User", back_populates="propietario", uselist=False)

    # Relación con mascotas (1:N)
    # Un propietario puede tener múltiples mascotas
    # NOTA: Pet usa backref="mascotas", así que NO definimos la relación aquí
    # La relación se crea automáticamente por el backref en Pet.owner

    def __repr__(self):
        return f"<Owner {self.nombre} - Usuario: {self.usuario_id}>"

    def to_dict(self):
        """Convierte el propietario a diccionario"""
        return {
            "id": str(self.id),
            "usuario_id": str(self.usuario_id),
            "nombre": self.nombre,
            "correo": self.correo,
            "documento": self.documento,
            "telefono": self.telefono,
            "activo": self.activo,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "fecha_actualizacion": self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
        }