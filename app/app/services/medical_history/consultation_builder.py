"""
Patrón Builder - Construcción paso a paso de consultas
RF-07: Gestión de historias clínicas
Facilita la creación progresiva de consultas con validaciones
"""

from typing import Optional
from uuid import UUID
from datetime import datetime, timezone

from app.models.consultation import Consultation


class ConsultationBuilder:
    """
    Builder Pattern - Construcción paso a paso de consultas médicas

    Permite crear consultas de forma progresiva, garantizando integridad de datos
    """

    def __init__(self):
        self._consultation = Consultation()

    def set_historia_clinica(self, historia_clinica_id: UUID) -> 'ConsultationBuilder':
        """Establece la historia clínica"""
        self._consultation.historia_clinica_id = historia_clinica_id
        return self

    def set_veterinario(self, veterinario_id: UUID) -> 'ConsultationBuilder':
        """Establece el veterinario"""
        self._consultation.veterinario_id = veterinario_id
        return self

    def set_cita(self, cita_id: Optional[UUID]) -> 'ConsultationBuilder':
        """Establece la cita relacionada (opcional)"""
        self._consultation.cita_id = cita_id
        return self

    def set_fecha_hora(self, fecha_hora: Optional[datetime]) -> 'ConsultationBuilder':
        """Establece la fecha y hora de la consulta"""
        if fecha_hora:
            if fecha_hora > datetime.now(timezone.utc):
                raise ValueError("La fecha de consulta no puede ser futura")
            self._consultation.fecha_hora = fecha_hora
        else:
            self._consultation.fecha_hora = datetime.now(timezone.utc)
        return self

    def set_motivo(self, motivo: str) -> 'ConsultationBuilder':
        """Establece el motivo de la consulta"""
        if not motivo or len(motivo.strip()) < 5:
            raise ValueError("El motivo debe tener al menos 5 caracteres")
        self._consultation.motivo = motivo.strip()
        return self

    def set_anamnesis(self, anamnesis: Optional[str]) -> 'ConsultationBuilder':
        """Establece la anamnesis"""
        self._consultation.anamnesis = anamnesis.strip() if anamnesis else None
        return self

    def set_signos_vitales(self, signos_vitales: Optional[str]) -> 'ConsultationBuilder':
        """Establece los signos vitales"""
        self._consultation.signos_vitales = signos_vitales.strip() if signos_vitales else None
        return self

    def set_diagnostico(self, diagnostico: str) -> 'ConsultationBuilder':
        """Establece el diagnóstico"""
        if not diagnostico or len(diagnostico.strip()) < 10:
            raise ValueError("El diagnóstico debe tener al menos 10 caracteres")
        self._consultation.diagnostico = diagnostico.strip()
        return self

    def set_tratamiento(self, tratamiento: str) -> 'ConsultationBuilder':
        """Establece el tratamiento"""
        if not tratamiento or len(tratamiento.strip()) < 5:
            raise ValueError("El tratamiento debe tener al menos 5 caracteres")
        self._consultation.tratamiento = tratamiento.strip()
        return self

    def set_vacunas(self, vacunas: Optional[str]) -> 'ConsultationBuilder':
        """Establece las vacunas administradas"""
        self._consultation.vacunas = vacunas.strip() if vacunas else None
        return self

    def set_observaciones(self, observaciones: Optional[str]) -> 'ConsultationBuilder':
        """Establece las observaciones"""
        self._consultation.observaciones = observaciones.strip() if observaciones else None
        return self

    def set_version(self, version: int) -> 'ConsultationBuilder':
        """Establece la versión (para Memento Pattern)"""
        self._consultation.version = version
        return self

    def set_creado_por(self, creado_por: UUID) -> 'ConsultationBuilder':
        """Establece el usuario creador"""
        self._consultation.creado_por = creado_por
        return self

    def set_actualizado_por(self, actualizado_por: Optional[UUID]) -> 'ConsultationBuilder':
        """Establece el usuario que actualizó"""
        self._consultation.actualizado_por = actualizado_por
        return self

    def build(self) -> Consultation:
        """
        Construye y retorna la consulta

        Raises:
            ValueError: Si faltan campos obligatorios
        """
        # Validar campos obligatorios
        if not self._consultation.historia_clinica_id:
            raise ValueError("La historia clínica es obligatoria")
        if not self._consultation.veterinario_id:
            raise ValueError("El veterinario es obligatorio")
        if not self._consultation.motivo:
            raise ValueError("El motivo es obligatorio")
        if not self._consultation.diagnostico:
            raise ValueError("El diagnóstico es obligatorio")
        if not self._consultation.tratamiento:
            raise ValueError("El tratamiento es obligatorio")
        if not self._consultation.creado_por:
            raise ValueError("El creador es obligatorio")
        if not self._consultation.fecha_hora:
            self._consultation.fecha_hora = datetime.now(timezone.utc)

        return self._consultation

    def reset(self) -> 'ConsultationBuilder':
        """Reinicia el builder"""
        self._consultation = Consultation()
        return self