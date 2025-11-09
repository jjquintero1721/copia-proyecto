"""
Modelo de Consulta - Representa cada atención médica registrada
RF-07: Gestión de historias clínicas
RN10-2: Cada modificación registra fecha, hora y usuario
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.database import Base


class Consultation(Base):
    """
    Modelo de Consulta - Representa cada registro médico en una historia clínica

    Cada consulta almacena:
    - Motivo de la consulta
    - Anamnesis (historia del paciente)
    - Signos vitales
    - Diagnóstico
    - Tratamiento aplicado
    - Vacunas administradas
    - Observaciones adicionales
    - Versión (para Memento Pattern)
    """
    __tablename__ = "consultas"

    # Identificador único de la consulta
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Relación con historia clínica (ondelete="CASCADE")
    historia_clinica_id = Column(
        UUID(as_uuid=True),
        ForeignKey("historias_clinicas.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Relación con veterinario que realizó la consulta
    veterinario_id = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id"),
        nullable=False,
        index=True
    )

    # Relación con cita (opcional)
    cita_id = Column(
        UUID(as_uuid=True),
        ForeignKey("citas.id"),
        nullable=True,
        index=True
    )

    # Fecha y hora de la consulta
    fecha_hora = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Campos de la consulta
    motivo = Column(String(300), nullable=False)
    anamnesis = Column(Text, nullable=True)  # Historia del paciente
    signos_vitales = Column(Text, nullable=True)  # FC, FR, Temperatura, etc.
    diagnostico = Column(Text, nullable=False)
    tratamiento = Column(Text, nullable=False)
    vacunas = Column(Text, nullable=True)  # Vacunas aplicadas
    observaciones = Column(Text, nullable=True)

    # Versionado (Memento Pattern)
    version = Column(Integer, default=1, nullable=False)

    # Auditoría (RN10-2)
    fecha_creacion = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    fecha_actualizacion = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    creado_por = Column(UUID(as_uuid=True), nullable=False)  # Usuario que creó
    actualizado_por = Column(UUID(as_uuid=True), nullable=True)  # Último usuario que modificó

    # Relaciones
    historia_clinica = relationship("MedicalHistory", back_populates="consultas")
    veterinario = relationship("User", foreign_keys=[veterinario_id])
    cita = relationship("Appointment", back_populates="consultas")

    def __repr__(self):
        return f"<Consulta {self.id} - HC: {self.historia_clinica_id} - v{self.version}>"

    def to_dict(self):
        """Convierte la consulta a diccionario"""
        return {
            "id": str(self.id),
            "historia_clinica_id": str(self.historia_clinica_id),
            "veterinario_id": str(self.veterinario_id),
            "cita_id": str(self.cita_id) if self.cita_id else None,
            "fecha_hora": self.fecha_hora.isoformat() if self.fecha_hora else None,
            "motivo": self.motivo,
            "anamnesis": self.anamnesis,
            "signos_vitales": self.signos_vitales,
            "diagnostico": self.diagnostico,
            "tratamiento": self.tratamiento,
            "vacunas": self.vacunas,
            "observaciones": self.observaciones,
            "version": self.version,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "fecha_actualizacion": self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None,
            "creado_por": str(self.creado_por),
            "actualizado_por": str(self.actualizado_por) if self.actualizado_por else None
        }