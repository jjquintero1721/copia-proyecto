"""
Modelo de Cita - Representa las citas veterinarias
RF-05: Gestión de citas (agendar, reprogramar, cancelar)
Implementa State Pattern para gestión de estados
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum

from app.database import Base


class AppointmentStatus(str, enum.Enum):
    """
    Enumeración de estados de cita (State Pattern)
    Relaciona con RF-05 y RN08-*
    """
    AGENDADA = "agendada"
    CONFIRMADA = "confirmada"
    EN_PROCESO = "en_proceso"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"
    CANCELADA_TARDIA = "cancelada_tardia"


class Appointment(Base):
    """
    Modelo de Cita veterinaria
    Implementa patrón State para gestión de estados
    """
    __tablename__ = "citas"

    # Identificador único de la cita
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Relaciones
    mascota_id = Column(UUID(as_uuid=True), ForeignKey("mascotas.id", ondelete="CASCADE"),
                       nullable=False, index=True)
    veterinario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"),
                           nullable=False, index=True)
    servicio_id = Column(UUID(as_uuid=True), ForeignKey("servicios.id"),
                        nullable=False, index=True)

    # Relación con consultas
    consultas = relationship("Consultation", back_populates="cita")

    # Fecha y hora de la cita
    fecha_hora = Column(DateTime(timezone=True), nullable=False, index=True)

    # Estado de la cita (State Pattern)
    estado = Column(SQLEnum(AppointmentStatus), nullable=False,
                   default=AppointmentStatus.AGENDADA, index=True)

    # Motivo de la cita
    motivo = Column(Text, nullable=True)

    # Indica si fue cancelación tardía (RN08-2)
    cancelacion_tardia = Column(Boolean, default=False, nullable=False)

    # Notas adicionales
    notas = Column(Text, nullable=True)

    # Auditoría
    fecha_creacion = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    fecha_actualizacion = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    creado_por = Column(UUID(as_uuid=True), nullable=True)

    # Relationships
    mascota = relationship("Pet", backref="citas")
    veterinario = relationship("User", foreign_keys=[veterinario_id], backref="citas_veterinario")
    servicio = relationship("Service", backref="citas")
    triage = relationship("Triage", back_populates="cita", uselist=False)

    def __repr__(self):
        return f"<Cita {self.fecha_hora} - {self.estado.value}>"

    @staticmethod
    def _ensure_timezone_aware(dt: datetime) -> datetime | None:
        """
        Asegura que un datetime tenga información de timezone.
        Si no la tiene, asume UTC.

        Args:
            dt: datetime a verificar

        Returns:
            datetime con timezone
        """
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    def get_fecha_hora_aware(self) -> datetime:
        """
        Obtiene fecha_hora asegurando que sea timezone-aware

        Returns:
            datetime con timezone UTC
        """
        return self._ensure_timezone_aware(self.fecha_hora)

    def to_dict(self):
        """Convierte la cita a diccionario"""

        fecha_hora_aware = self._ensure_timezone_aware(self.fecha_hora)
        fecha_creacion_aware = self._ensure_timezone_aware(self.fecha_creacion)
        return {
            "id": str(self.id),
            "mascota_id": str(self.mascota_id),
            "veterinario_id": str(self.veterinario_id),
            "servicio_id": str(self.servicio_id),
            "fecha_hora": fecha_hora_aware.isoformat() if fecha_hora_aware else None,
            "estado": self.estado.value,
            "motivo": self.motivo,
            "cancelacion_tardia": self.cancelacion_tardia,
            "notas": self.notas,
            "fecha_creacion": fecha_creacion_aware.isoformat() if fecha_creacion_aware else None
        }

    def to_dict_with_relations(self):
        """
        Convierte el appointment a diccionario incluyendo información de relaciones
        Útil para endpoints que necesitan mostrar información completa
        """
        result = {
            'id': str(self.id),
            'mascota_id': str(self.mascota_id),
            'veterinario_id': str(self.veterinario_id),
            'servicio_id': str(self.servicio_id),
            'fecha_hora': self.fecha_hora.isoformat(),
            'motivo': self.motivo,
            'estado': self.estado.value,
            'cancelacion_tardia': self.cancelacion_tardia,
            'notas': self.notas,
            'creado_por': str(self.creado_por) if self.creado_por else None,
            'fecha_creacion': self.fecha_creacion.isoformat(),
            'fecha_actualizacion': self.fecha_actualizacion.isoformat()
        }

        # Agregar información de mascota si está cargada
        if self.mascota:
            result["mascota"] = {
                "id": str(self.mascota.id),
                "nombre": self.mascota.nombre,
                "especie": self.mascota.especie,
                "raza": self.mascota.raza if hasattr(self.mascota, 'raza') else None
            }

        else:
            # Si la mascota no está cargada, al menos incluir valores por defecto
            result["mascota"] = {
                "id": str(self.mascota_id),
                "nombre": "Mascota",  # Valor por defecto
                "especie": None,
                "raza": None
            }

        if self.mascota and hasattr(self.mascota, 'owner') and self.mascota.owner:
            result["propietario"] = {
                "id": str(self.mascota.owner.id),
                "nombre": self.mascota.owner.nombre,
                "correo": self.mascota.owner.correo if hasattr(self.mascota.owner, 'correo') else None,
                "telefono": self.mascota.owner.telefono if hasattr(self.mascota.owner, 'telefono') else None
            }
        else:
            # Si no está cargado el propietario, dejar como None o valor por defecto
            result["propietario"] = None

            # ✅ CORRECCIÓN: Incluir información del veterinario si está cargado
        if self.veterinario:
            result["veterinario"] = {
                "id": str(self.veterinario.id),
                "nombre": self.veterinario.nombre,
                "correo": self.veterinario.correo if hasattr(self.veterinario, 'correo') else None
            }
        else:
            # Si el veterinario no está cargado, al menos incluir valores por defecto
            result["veterinario"] = {
                "id": str(self.veterinario_id),
                "nombre": "Dr(a). Sin asignar",  # Valor por defecto
                "correo": None
            }

            # ✅ CORRECCIÓN: Incluir información del servicio si está cargado
        if self.servicio:
            result["servicio"] = {
                "id": str(self.servicio.id),
                "nombre": self.servicio.nombre,
                "duracion_minutos": self.servicio.duracion_minutos if hasattr(self.servicio,
                                                                              'duracion_minutos') else None,
                "costo": float(self.servicio.costo) if hasattr(self.servicio, 'costo') else None
            }
        else:
            # Si el servicio no está cargado, al menos incluir valores por defecto
            result["servicio"] = {
                "id": str(self.servicio_id),
                "nombre": "Servicio",  # Valor por defecto
                "duracion_minutos": None,
                "costo": None
            }

        return result

        return base_dict