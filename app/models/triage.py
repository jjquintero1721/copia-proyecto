"""
Modelo de Triage - Representa la clasificación de prioridad de atención
RF-08: Triage (clasificación de prioridad)
Implementa Chain of Responsibility Pattern para determinar prioridad
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum

from app.database import Base


class TriagePriority(str, enum.Enum):
    """
    Enumeración de prioridades de triage
    Relaciona con RF-08 y patrón Chain of Responsibility
    """
    URGENTE = "urgente"  # Atención inmediata
    ALTA = "alta"  # Atención prioritaria
    MEDIA = "media"  # Atención normal
    BAJA = "baja"  # Puede esperar


class TriageGeneralState(str, enum.Enum):
    """
    Enumeración de estados generales del paciente
    """
    CRITICO = "critico"  # Estado crítico
    DECAIDO = "decaido"  # Decaído/débil
    ALERTA = "alerta"  # Alerta y consciente
    ESTABLE = "estable"  # Estado estable


class Triage(Base):
    """
    Modelo de Triage veterinario
    Implementa el patrón Chain of Responsibility para clasificación automática
    """
    __tablename__ = "triages"

    # Identificador único del triage
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Relación con cita (opcional - un triage puede existir sin cita confirmada)
    cita_id = Column(
        UUID(as_uuid=True),
        ForeignKey("citas.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Relación con mascota (obligatorio)
    mascota_id = Column(
        UUID(as_uuid=True),
        ForeignKey("mascotas.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Usuario que registra el triage (veterinario o auxiliar)
    usuario_id = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id"),
        nullable=False,
        index=True
    )

    # Estado general del paciente
    estado_general = Column(
        SQLEnum(TriageGeneralState),
        nullable=False,
        index=True
    )

    # Signos vitales - Frecuencia Cardíaca (latidos por minuto)
    fc = Column(Integer, nullable=False)

    # Signos vitales - Frecuencia Respiratoria (respiraciones por minuto)
    fr = Column(Integer, nullable=False)

    # Signos vitales - Temperatura (grados Celsius)
    temperatura = Column(Float, nullable=False)

    # Evaluación de dolor (ausente, leve, moderado, severo)
    dolor = Column(String(50), nullable=False)

    # Presencia de sangrado (Si/No)
    sangrado = Column(String(2), nullable=False)

    # Presencia de shock (Si/No)
    shock = Column(String(2), nullable=False)

    # Prioridad calculada (Chain of Responsibility)
    prioridad = Column(
        SQLEnum(TriagePriority),
        nullable=False,
        index=True
    )

    # Observaciones adicionales
    observaciones = Column(Text, nullable=True)

    # Auditoría
    fecha_creacion = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relaciones
    cita = relationship("Appointment", foreign_keys=[cita_id], back_populates="triage")
    mascota = relationship("Pet", back_populates="triages")
    usuario = relationship("User", foreign_keys=[usuario_id])

    def to_dict(self) -> dict:

        # Datos básicos del triage
        triage_data = {
            "id": str(self.id),
            "cita_id": str(self.cita_id) if self.cita_id else None,
            "mascota_id": str(self.mascota_id),
            "usuario_id": str(self.usuario_id),
            "estado_general": self.estado_general.value,
            "fc": self.fc,
            "fr": self.fr,
            "temperatura": self.temperatura,
            "dolor": self.dolor,
            "sangrado": self.sangrado,
            "shock": self.shock,
            "prioridad": self.prioridad.value,
            "observaciones": self.observaciones,
            "fecha_creacion": self.fecha_creacion.isoformat()
        }

        # ✅ NUEVO: Incluir datos de la mascota si la relación está cargada
        if self.mascota:
            # Calcular edad si tiene fecha de nacimiento
            edad = None
            if self.mascota.fecha_nacimiento:
                today = datetime.now(timezone.utc).date()
                edad = today.year - self.mascota.fecha_nacimiento.year
                # Ajustar si aún no ha cumplido años este año
                if (today.month, today.day) < (self.mascota.fecha_nacimiento.month, self.mascota.fecha_nacimiento.day):
                    edad -= 1

            triage_data["mascota"] = {
                "id": str(self.mascota.id),
                "nombre": self.mascota.nombre,
                "especie": self.mascota.especie,
                "raza": self.mascota.raza,
                "microchip": self.mascota.microchip,
                "edad": edad,
                "fecha_nacimiento": self.mascota.fecha_nacimiento.isoformat() if self.mascota.fecha_nacimiento else None
            }

            # ✅ CRÍTICO: Incluir datos del propietario si están cargados
            # Pet tiene la relación 'owner' con Owner
            if hasattr(self.mascota, 'owner') and self.mascota.owner:
                triage_data["mascota"]["propietario"] = {
                    "id": str(self.mascota.owner.id),
                    "nombre": self.mascota.owner.nombre,
                    "apellido": self.mascota.owner.apellido if hasattr(self.mascota.owner, 'apellido') else "",
                    "telefono": self.mascota.owner.telefono,
                    "correo": self.mascota.owner.correo
                }
            else:
                # Si no está cargado, poner valores por defecto
                triage_data["mascota"]["propietario"] = {
                    "id": str(self.mascota.propietario_id) if self.mascota.propietario_id else None,
                    "nombre": "No disponible",
                    "apellido": "",
                    "telefono": "No disponible",
                    "correo": "No disponible"
                }
        else:
            # Si mascota no está cargada, poner valores por defecto
            triage_data["mascota"] = {
                "id": str(self.mascota_id),
                "nombre": "No disponible",
                "especie": "No disponible",
                "raza": None,
                "microchip": None,
                "edad": None,
                "fecha_nacimiento": None,
                "propietario": {
                    "id": None,
                    "nombre": "No disponible",
                    "apellido": "",
                    "telefono": "No disponible",
                    "correo": "No disponible"
                }
            }

            # ✅ NUEVO: Incluir datos del usuario que registró el triage (si está cargado)
        if self.usuario:
            triage_data["registrado_por"] = {
                "id": str(self.usuario.id),
                "nombre": self.usuario.nombre,
                "correo": self.usuario.correo,
                "rol": self.usuario.rol.value if hasattr(self.usuario, 'rol') else None
            }
        else:
            triage_data["registrado_por"] = {
                "id": str(self.usuario_id),
                "nombre": "No disponible",
                "correo": "No disponible",
                "rol": None
            }

        return triage_data




    def __repr__(self):
        return f"<Triage(id={self.id}, mascota_id={self.mascota_id}, prioridad={self.prioridad})>"