"""
Servicio de Historias Clínicas - Lógica de negocio principal
RF-07: Gestión de historias clínicas
RN10-1: Las historias no pueden eliminarse
RN10-2: Auditoría de cambios
Implementa patrones: Builder, Memento, Template Method
"""

from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from app.models.consultation import Consultation
from app.models.medical_history import MedicalHistory
from app.models.medical_history_memento import MedicalHistoryMemento
from app.repositories.consultation_repository import ConsultationRepository
from app.repositories.medical_history_repository import MedicalHistoryRepository
from app.schemas.consultation_schema import ConsultationCreate, ConsultationUpdate
from app.services.medical_history.consultation_builder import ConsultationBuilder
from app.services.inventory.inventory_facade import InventoryFacade


class MedicalHistoryService:
    """
    Servicio principal de gestión de historias clínicas y consultas
    Implementa patrones: Builder, Memento, Template Method
    """

    def __init__(self, db: Session):
        self.db = db
        self.consultation_repo = ConsultationRepository(db)
        self.medical_history_repo = MedicalHistoryRepository(db)

    CONSULTA_NOT_FOUND_MSG = "Consulta no encontrado"

    # ==================== CONSULTAS ====================

    def create_consultation(
        self,
        consultation_data: ConsultationCreate,
        creado_por: UUID
    ) -> Consultation:
        """
        Crea una nueva consulta usando Builder Pattern

        Template Method:
        1. Validar datos
        2. Construir entidad con Builder
        3. Persistir
        4. Crear memento inicial

        Args:
            consultation_data: Datos de la consulta
            creado_por: ID del usuario que crea la consulta

        Returns:
            Consultation creada

        Raises:
            ValueError: Si hay errores de validación
        """
        # 1. Validar que la historia clínica exista
        historia = self.medical_history_repo.get_by_id(consultation_data.historia_clinica_id)
        if not historia:
            raise ValueError("La historia clínica no existe")

        # RN10-1: Verificar que la historia no esté eliminada
        if historia.is_deleted:
            raise ValueError("No se puede agregar consultas a una historia eliminada")

        # 2. Construir consulta con Builder Pattern
        builder = ConsultationBuilder()
        consultation = (builder
                       .set_historia_clinica(consultation_data.historia_clinica_id)
                       .set_veterinario(consultation_data.veterinario_id)
                       .set_cita(consultation_data.cita_id)
                       .set_fecha_hora(consultation_data.fecha_hora)
                       .set_motivo(consultation_data.motivo)
                       .set_anamnesis(consultation_data.anamnesis)
                       .set_signos_vitales(consultation_data.signos_vitales)
                       .set_diagnostico(consultation_data.diagnostico)
                       .set_tratamiento(consultation_data.tratamiento)
                       .set_vacunas(consultation_data.vacunas)
                       .set_observaciones(consultation_data.observaciones)
                       .set_version(1)  # Primera versión
                       .set_creado_por(creado_por)
                       .build())

        # 3. Persistir
        consultation = self.consultation_repo.create(consultation)

        # 4. Crear memento inicial (Memento Pattern)
        self._save_memento(consultation, creado_por, "Creación de consulta")

        return consultation

    def update_consultation(
        self,
        consultation_id: UUID,
        update_data: ConsultationUpdate,
        actualizado_por: UUID
    ) -> Consultation:
        """
        Actualiza una consulta existente

        RN10-2: Registra cambios con fecha, hora y usuario
        Memento Pattern: Crea un snapshot antes de actualizar

        Args:
            consultation_id: ID de la consulta
            update_data: Datos a actualizar
            actualizado_por: ID del usuario que actualiza

        Returns:
            Consultation actualizada

        Raises:
            ValueError: Si la consulta no existe
        """
        # Obtener consulta actual
        consultation = self.consultation_repo.get_by_id(consultation_id)
        if not consultation:
            raise ValueError(self.CONSULTA_NOT_FOUND_MSG)

        # Guardar memento antes de actualizar (Memento Pattern)
        nueva_version = consultation.version + 1
        self._save_memento(
            consultation,
            actualizado_por,
            update_data.descripcion_cambio or "Actualización de consulta"
        )

        # Actualizar campos
        update_dict = update_data.model_dump(exclude_unset=True, exclude={'descripcion_cambio'})
        for field, value in update_dict.items():
            if value is not None:
                setattr(consultation, field, value)

        # Actualizar auditoría (RN10-2)
        consultation.version = nueva_version
        consultation.actualizado_por = actualizado_por
        consultation.fecha_actualizacion = datetime.now(timezone.utc)

        return self.consultation_repo.update(consultation)

    def get_consultation_by_id(self, consultation_id: UUID) -> Optional[Consultation]:
        """Obtiene una consulta por ID"""
        return self.consultation_repo.get_by_id(consultation_id)

    def get_consultations_by_historia_clinica(
        self,
        historia_clinica_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Consultation]:
        """Obtiene todas las consultas de una historia clínica"""
        return self.consultation_repo.get_by_historia_clinica(
            historia_clinica_id,
            skip,
            limit
        )

    # ==================== HISTORIA CLÍNICA ====================

    def get_medical_history_complete(
        self,
        historia_clinica_id: UUID,
        include_consultas: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene una historia clínica completa con todas sus consultas

        Args:
            historia_clinica_id: ID de la historia clínica
            include_consultas: Incluir lista de consultas

        Returns:
            Dict con historia clínica y consultas
        """
        historia = self.medical_history_repo.get_by_id(historia_clinica_id)
        if not historia:
            return None

        result = historia.to_dict()

        if include_consultas:
            consultas = self.consultation_repo.get_by_historia_clinica(historia_clinica_id)
            result["consultas"] = [c.to_dict() for c in consultas]

        return result

    def get_medical_history_by_mascota(self, mascota_id: UUID) -> Optional[MedicalHistory]:
        """Obtiene la historia clínica de una mascota"""
        return self.medical_history_repo.get_by_mascota_id(mascota_id)

    # ==================== MEMENTO PATTERN ====================

    def _save_memento(
        self,
        consultation: Consultation,
        usuario_id: UUID,
        descripcion: str
    ) -> MedicalHistoryMemento:
        """
        Guarda un memento (snapshot) de la consulta
        Implementa Memento Pattern
        """
        memento = MedicalHistoryMemento(
            consulta_id=consultation.id,
            version=consultation.version,
            estado={
                "motivo": consultation.motivo,
                "anamnesis": consultation.anamnesis,
                "signos_vitales": consultation.signos_vitales,
                "diagnostico": consultation.diagnostico,
                "tratamiento": consultation.tratamiento,
                "vacunas": consultation.vacunas,
                "observaciones": consultation.observaciones
            },
            creado_por=usuario_id,
            descripcion_cambio=descripcion
        )
        return self.consultation_repo.save_memento(memento)

    def get_consultation_history(
        self,
        consultation_id: UUID,
        skip: int = 0,
        limit: int = 50
    ) -> List[MedicalHistoryMemento]:
        """
        Obtiene el historial de versiones de una consulta
        Implementa Memento Pattern para recuperar estados anteriores
        """
        return self.consultation_repo.get_mementos_by_consulta(
            consultation_id,
            skip,
            limit
        )

    def restore_consultation_version(
        self,
        consultation_id: UUID,
        version: int,
        usuario_id: UUID
    ) -> Consultation:
        """
        Restaura una versión anterior de una consulta
        Implementa Memento Pattern

        Args:
            consultation_id: ID de la consulta
            version: Versión a restaurar
            usuario_id: ID del usuario que restaura

        Returns:
            Consultation restaurada

        Raises:
            ValueError: Si la versión no existe
        """
        # Obtener consulta actual
        consultation = self.consultation_repo.get_by_id(consultation_id)
        if not consultation:
            raise ValueError("Consulta no encontrada")

        # Obtener memento de la versión solicitada
        memento = self.consultation_repo.get_memento_by_version(consultation_id, version)
        if not memento:
            raise ValueError(f"Versión {version} no encontrada")

        # Guardar estado actual antes de restaurar
        nueva_version = consultation.version + 1
        self._save_memento(
            consultation,
            usuario_id,
            f"Restauración desde versión {version}"
        )

        # Restaurar estado
        estado = memento.estado
        consultation.motivo = estado.get("motivo")
        consultation.anamnesis = estado.get("anamnesis")
        consultation.signos_vitales = estado.get("signos_vitales")
        consultation.diagnostico = estado.get("diagnostico")
        consultation.tratamiento = estado.get("tratamiento")
        consultation.vacunas = estado.get("vacunas")
        consultation.observaciones = estado.get("observaciones")

        # Actualizar auditoría
        consultation.version = nueva_version
        consultation.actualizado_por = usuario_id
        consultation.fecha_actualizacion = datetime.now(timezone.utc)

        return self.consultation_repo.update(consultation)

    def completar_consulta_con_medicamentos(
            self,
            consulta_id: UUID,
            medicamentos_usados: List[Dict[str, Any]],
            usuario_id: UUID
    ) -> None:
        """
        Completa una consulta y descuenta medicamentos del inventario
        Integración con módulo de Inventario mediante Facade Pattern
        """
        # Validar que la consulta exista
        consulta = self.consultation_repo.get_by_id(consulta_id)
        if not consulta:
            raise ValueError(self.CONSULTA_NOT_FOUND_MSG)

        # Registrar uso de medicamentos
        if medicamentos_usados:
            inventory_facade = InventoryFacade(self.db)
            movimientos = inventory_facade.registrar_uso_en_consulta(
                medicamentos_usados=medicamentos_usados,
                consulta_id=consulta_id,
                usuario_id=usuario_id
            )