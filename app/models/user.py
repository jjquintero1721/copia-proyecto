"""
Modelo de Usuario - Representa la tabla de usuarios en la base de datos
Roles: superadmin, veterinario, auxiliar, propietario
CORRECCIÓN ARQUITECTURAL: Relación 1:1 con Owner cuando rol=propietario
"""

from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
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
    Modelo de Usuario - Autenticación y autorización

    Implementa la entidad Usuario con diferentes roles y permisos.

    Relación con Owner:
    - Si rol = PROPIETARIO → debe existir un registro en tabla propietarios
    - Relación 1:1 (un usuario propietario = un registro de propietario)

    RF-01: Registro de usuarios
    RF-02: Gestión de usuarios internos
    RF-03: Inicio de sesión
    """
    __tablename__ = "usuarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    nombre = Column(String(100), nullable=False)
    correo = Column(String(150), unique=True, nullable=False, index=True)
    telefono = Column(String(20), nullable=True)
    contrasena_hash = Column(String(255), nullable=False)
    rol = Column(SQLEnum(UserRole), nullable=False)
    activo = Column(Boolean, default=True, nullable=False)

    veterinario_encargado_id = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="ID del veterinario encargado de este auxiliar (solo si rol=auxiliar)"
    )

    # Auditoría
    fecha_creacion = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    fecha_actualizacion = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    creado_por = Column(UUID(as_uuid=True), nullable=True)

    # Relación 1:1 con Owner (solo si rol = propietario)
    propietario = relationship(
        "Owner",
        back_populates="usuario",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # Relación N:1 - Auxiliar pertenece a un Veterinario
    veterinario_encargado = relationship(
        "User",
        remote_side=[id],
        foreign_keys=[veterinario_encargado_id],
        back_populates="auxiliares_a_cargo",
        uselist=False
    )

    # Relación 1:N - Veterinario tiene muchos auxiliares
    auxiliares_a_cargo = relationship(
        "User",
        foreign_keys=[veterinario_encargado_id],
        back_populates="veterinario_encargado",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Usuario {self.nombre} - {self.rol}>"

    def to_dict(self):
        """Convierte el usuario a diccionario (sin contraseña)"""
        user_dict = {
            "id": str(self.id),
            "nombre": self.nombre,
            "correo": self.correo,
            "telefono": self.telefono,
            "rol": self.rol.value,
            "activo": self.activo,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }

        # Incluir info del propietario si existe
        if self.propietario:
            user_dict["propietario_id"] = str(self.propietario.id)
            user_dict["documento"] = self.propietario.documento

            # Incluir info del veterinario encargado si el usuario es auxiliar
            if self.rol == UserRole.AUXILIAR and self.veterinario_encargado:
                user_dict["veterinario_encargado"] = {
                    "id": str(self.veterinario_encargado.id),
                    "nombre": self.veterinario_encargado.nombre,
                    "correo": self.veterinario_encargado.correo
                }

            # Incluir lista de auxiliares si el usuario es veterinario
            if self.rol == UserRole.VETERINARIO and self.auxiliares_a_cargo:
                user_dict["auxiliares_a_cargo"] = [
                    {
                        "id": str(aux.id),
                        "nombre": aux.nombre,
                        "correo": aux.correo,
                        "activo": aux.activo
                    }
                    for aux in self.auxiliares_a_cargo
                ]

        return user_dict