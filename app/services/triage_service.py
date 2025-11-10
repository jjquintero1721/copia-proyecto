"""
Servicio de Triage - Lógica de negocio
RF-08: Triage (clasificación de prioridad)
Implementa Chain of Responsibility Pattern
"""

from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from abc import ABC, abstractmethod

from app.models.triage import Triage, TriagePriority, TriageGeneralState
from app.repositories.triage_repository import TriageRepository
from app.repositories.pet_repository import PetRepository
from app.repositories.appointment_repository import AppointmentRepository
from app.schemas.triage_schema import TriageCreate, TriageUpdate


# ==================== CHAIN OF RESPONSIBILITY PATTERN ====================

class TriageHandler(ABC):
    """
    Handler abstracto del Chain of Responsibility
    Define la interfaz para evaluar prioridad de triage
    """

    def __init__(self):
        self._next_handler: Optional[TriageHandler] = None

    def set_next(self, handler: 'TriageHandler') -> 'TriageHandler':
        """Establece el siguiente handler en la cadena"""
        self._next_handler = handler
        return handler

    @abstractmethod
    def handle(self, triage_data: dict) -> Optional[TriagePriority]:
        """
        Evalúa si puede determinar la prioridad
        Si no puede, delega al siguiente handler
        """
        pass

    def _delegate_to_next(self, triage_data: dict) -> Optional[TriagePriority]:
        """Delega al siguiente handler si existe"""
        if self._next_handler:
            return self._next_handler.handle(triage_data)
        return None


class EstadoCriticoHandler(TriageHandler):
    """
    Handler 1: Evalúa si el paciente está en estado crítico
    Si signos vitales críticos o inconsciencia → URGENTE
    """

    def handle(self, triage_data: dict) -> Optional[TriagePriority]:
        estado_general = triage_data.get('estado_general')
        fc = triage_data.get('fc', 0)
        fr = triage_data.get('fr', 0)
        temperatura = triage_data.get('temperatura', 0)

        # Estado crítico o inconsciencia
        if estado_general == TriageGeneralState.CRITICO.value:
            return TriagePriority.URGENTE

        # Signos vitales críticos (valores extremos)
        # FC: perros 60-140, gatos 140-220 (fuera de rango = crítico)
        if fc < 40 or fc > 250:
            return TriagePriority.URGENTE

        # FR: normal 15-30 (fuera de rango extremo = crítico)
        if fr < 8 or fr > 60:
            return TriagePriority.URGENTE

        # Temperatura crítica (hipotermia o hipertermia severa)
        if temperatura < 36.0 or temperatura > 40.5:
            return TriagePriority.URGENTE

        # Si no es crítico, pasar al siguiente handler
        return self._delegate_to_next(triage_data)


class SignosDolorHandler(TriageHandler):
    """
    Handler 2: Evalúa dolor, sangrado y shock
    Si dolor severo, sangrado o shock → URGENTE
    """

    def handle(self, triage_data: dict) -> Optional[TriagePriority]:
        dolor = triage_data.get('dolor', '').lower()
        sangrado = triage_data.get('sangrado', '').lower()
        shock = triage_data.get('shock', '').lower()

        # Dolor severo
        if dolor == 'severo':
            return TriagePriority.URGENTE

        # Presencia de sangrado
        if sangrado == 'si':
            return TriagePriority.URGENTE

        # Presencia de shock
        if shock == 'si':
            return TriagePriority.URGENTE

        # Si no hay signos de urgencia, pasar al siguiente handler
        return self._delegate_to_next(triage_data)


class SignosVitalesHandler(TriageHandler):
    """
    Handler 3: Evalúa signos vitales en rango de alerta
    Evalúa FR, FC, temperatura → ALTA/MEDIA
    """

    def handle(self, triage_data: dict) -> Optional[TriagePriority]:
        fc = triage_data.get('fc', 0)
        fr = triage_data.get('fr', 0)
        temperatura = triage_data.get('temperatura', 0)
        dolor = triage_data.get('dolor', '').lower()
        estado_general = triage_data.get('estado_general', '').lower()

        alertas = 0

        # FC anormal (pero no crítico)
        if fc < 60 or fc > 180:
            alertas += 1

        # FR anormal (pero no crítica)
        if fr < 12 or fr > 40:
            alertas += 1

        # Temperatura anormal (pero no crítica)
        if temperatura < 37.5 or temperatura > 39.5:
            alertas += 1

        # Dolor moderado
        if dolor == 'moderado':
            alertas += 1

        # Estado decaído
        if estado_general == TriageGeneralState.DECAIDO.value:
            alertas += 1

        # Evaluar prioridad según número de alertas
        if alertas >= 3:
            return TriagePriority.ALTA
        elif alertas >= 1:
            return TriagePriority.MEDIA

        # Si no hay alertas, pasar al siguiente handler
        return self._delegate_to_next(triage_data)


class EstadoEstableHandler(TriageHandler):
    """
    Handler 4: Handler por defecto
    Si llega aquí, el paciente está estable → BAJA
    """

    def handle(self, triage_data: dict) -> Optional[TriagePriority]:
        # Si llegamos aquí, no hay signos de urgencia
        return TriagePriority.BAJA


# ==================== SERVICIO PRINCIPAL ====================

class TriageService:
    """
    Servicio de Triage
    Orquesta la lógica de negocio y utiliza el Chain of Responsibility
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = TriageRepository(db)
        self.pet_repository = PetRepository(db)
        self.appointment_repository = AppointmentRepository(db)
        self._setup_chain()

    def _setup_chain(self):
        """Configura la cadena de responsabilidad"""
        self.handler_chain = EstadoCriticoHandler()
        self.handler_chain \
            .set_next(SignosDolorHandler()) \
            .set_next(SignosVitalesHandler()) \
            .set_next(EstadoEstableHandler())

    def _calcular_prioridad(self, triage_data: dict) -> TriagePriority:
        """
        Calcula la prioridad usando el Chain of Responsibility
        """
        return self.handler_chain.handle(triage_data)

    def create_triage(
        self,
        data: TriageCreate,
        usuario_id: UUID
    ) -> Triage:
        """
        Crea un nuevo registro de triage
        Calcula automáticamente la prioridad usando Chain of Responsibility
        """
        # Validar que la mascota existe
        mascota = self.pet_repository.get_by_id(data.mascota_id)
        if not mascota:
            raise ValueError("La mascota no existe")

        # Si se proporciona cita_id, validar que exista y no tenga triage
        if data.cita_id:
            cita = self.appointment_repository.get_by_id(data.cita_id)
            if not cita:
                raise ValueError("La cita no existe")

            # Validar que la cita no tenga ya un triage
            if self.repository.exists_for_cita(data.cita_id):
                raise ValueError("Esta cita ya tiene un triage registrado")

        # Preparar datos para el clasificador
        triage_dict = {
            'estado_general': data.estado_general.value,
            'fc': data.fc,
            'fr': data.fr,
            'temperatura': data.temperatura,
            'dolor': data.dolor.value,
            'sangrado': data.sangrado,
            'shock': data.shock
        }

        # Calcular prioridad automáticamente
        prioridad = self._calcular_prioridad(triage_dict)

        # Validar observaciones críticas (Regla OCL)
        if prioridad == TriagePriority.URGENTE:
            if not data.observaciones or len(data.observaciones) < 10:
                raise ValueError(
                    "Para prioridad URGENTE, las observaciones deben tener al menos 10 caracteres"
                )

        # Crear el triage
        triage = Triage(
            cita_id=data.cita_id,
            mascota_id=data.mascota_id,
            usuario_id=usuario_id,
            estado_general=TriageGeneralState(data.estado_general.value),
            fc=data.fc,
            fr=data.fr,
            temperatura=data.temperatura,
            dolor=data.dolor.value,
            sangrado=data.sangrado,
            shock=data.shock,
            prioridad=prioridad,
            observaciones=data.observaciones
        )

        return self.repository.create(triage)

    def get_triage_by_id(self, triage_id: UUID) -> Optional[Triage]:
        """Obtiene un triage por ID"""
        return self.repository.get_by_id(triage_id)

    def get_triage_by_cita(self, cita_id: UUID) -> Optional[Triage]:
        """Obtiene el triage asociado a una cita"""
        return self.repository.get_by_cita_id(cita_id)

    def get_triages_by_mascota(
        self,
        mascota_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Triage]:
        """Obtiene el historial de triages de una mascota"""
        # Validar que la mascota existe
        mascota = self.pet_repository.get_by_id(mascota_id)
        if not mascota:
            raise ValueError("La mascota no existe")

        return self.repository.get_by_mascota_id(mascota_id, skip, limit)

    def get_all_triages(
        self,
        skip: int = 0,
        limit: int = 100,
        prioridad: Optional[str] = None
    ) -> list[Triage]:
        """Obtiene todos los triages con filtros opcionales"""
        prioridad_enum = None
        if prioridad:
            try:
                prioridad_enum = TriagePriority(prioridad)
            except ValueError:
                raise ValueError(f"Prioridad inválida: {prioridad}")

        return self.repository.get_all(skip, limit, prioridad_enum)

    def get_cola_urgencias(self, limit: int = 50) -> list[Triage]:
        """
        Obtiene la cola de urgencias ordenada por prioridad
        Útil para el personal médico
        """
        return self.repository.get_urgentes_pendientes(limit)

    def update_triage(
        self,
        triage_id: UUID,
        data: TriageUpdate
    ) -> Triage:
        """Actualiza un triage (poco común, pero disponible)"""
        triage = self.repository.get_by_id(triage_id)
        if not triage:
            raise ValueError("El triage no existe")

        # Actualizar campos si se proporcionan
        if data.estado_general:
            triage.estado_general = TriageGeneralState(data.estado_general.value)
        if data.fc is not None:
            triage.fc = data.fc
        if data.fr is not None:
            triage.fr = data.fr
        if data.temperatura is not None:
            triage.temperatura = data.temperatura
        if data.dolor:
            triage.dolor = data.dolor.value
        if data.sangrado:
            triage.sangrado = data.sangrado
        if data.shock:
            triage.shock = data.shock
        if data.observaciones is not None:
            triage.observaciones = data.observaciones

        # Recalcular prioridad si se actualizaron signos vitales
        triage_dict = {
            'estado_general': triage.estado_general.value,
            'fc': triage.fc,
            'fr': triage.fr,
            'temperatura': triage.temperatura,
            'dolor': triage.dolor,
            'sangrado': triage.sangrado,
            'shock': triage.shock
        }
        triage.prioridad = self._calcular_prioridad(triage_dict)

        return self.repository.update(triage)

    def delete_triage(self, triage_id: UUID) -> None:
        """Elimina un triage"""
        triage = self.repository.get_by_id(triage_id)
        if not triage:
            raise ValueError("El triage no existe")

        self.repository.delete(triage)