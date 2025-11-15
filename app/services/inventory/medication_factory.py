"""
Abstract Factory Pattern - Fábrica de Medicamentos
RF-10: Creación de diferentes tipos de medicamentos
Patrón: Abstract Factory para vacunas, antibióticos, suplementos e insumos
"""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.models.medication import Medication, MedicationType, MedicationUnit
from app.schemas.medication_schema import MedicationCreate


# ==================== PATRÓN ABSTRACT FACTORY ====================

class MedicationFactory(ABC):
    """
    Abstract Factory para crear diferentes tipos de medicamentos
    Cada factory concreta sabe cómo crear un tipo específico de medicamento
    """

    @abstractmethod
    def create_medication(
            self,
            data: MedicationCreate,
            creado_por: Optional[UUID] = None
    ) -> Medication:
        """Método factory abstracto para crear medicamentos"""
        pass

    def _build_base_medication(
            self,
            data: MedicationCreate,
            creado_por: Optional[UUID]
    ) -> Medication:
        """Método auxiliar para construir medicamento base"""
        medication = Medication(
            nombre=data.nombre,
            tipo=data.tipo,
            descripcion=data.descripcion,
            principio_activo=data.principio_activo,
            concentracion=data.concentracion,
            laboratorio=data.laboratorio,
            stock_actual=data.stock_actual,
            stock_minimo=data.stock_minimo,
            stock_maximo=data.stock_maximo,
            unidad_medida=data.unidad_medida,
            precio_compra=data.precio_compra,
            precio_venta=data.precio_venta,
            lote=data.lote,
            fecha_vencimiento=data.fecha_vencimiento,
            ubicacion=data.ubicacion,
            requiere_refrigeracion=data.requiere_refrigeracion,
            controlado=data.controlado,
            enfermedad=data.enfermedad,
            dosis_recomendada=data.dosis_recomendada,
            activo=True,
            creado_por=creado_por
        )
        return medication


class VacunaFactory(MedicationFactory):
    """
    Factory para crear vacunas
    Características especiales:
    - Requieren refrigeración por defecto
    - Tienen enfermedad asociada
    - Unidad típica: ampolletas
    """

    def create_medication(
            self,
            data: MedicationCreate,
            creado_por: Optional[UUID] = None
    ) -> Medication:
        medication = self._build_base_medication(data, creado_por)
        medication.tipo = MedicationType.VACUNA

        # Valores por defecto para vacunas
        if medication.requiere_refrigeracion is None:
            medication.requiere_refrigeracion = True

        if medication.unidad_medida == MedicationUnit.UNIDADES:
            medication.unidad_medida = MedicationUnit.AMPOLLETAS

        # Validación específica de vacunas
        if not medication.enfermedad:
            raise ValueError("Las vacunas deben especificar la enfermedad que previenen")

        return medication


class AntibioticoFactory(MedicationFactory):
    """
    Factory para crear antibióticos
    Características especiales:
    - Generalmente son controlados
    - Requieren principio activo
    - Unidad típica: tabletas o ml
    """

    def create_medication(
            self,
            data: MedicationCreate,
            creado_por: Optional[UUID] = None
    ) -> Medication:
        medication = self._build_base_medication(data, creado_por)
        medication.tipo = MedicationType.ANTIBIOTICO

        # Valores por defecto para antibióticos
        if medication.controlado is None:
            medication.controlado = True

        # Validación específica de antibióticos
        if not medication.principio_activo:
            raise ValueError("Los antibióticos deben especificar el principio activo")

        if not medication.concentracion:
            raise ValueError("Los antibióticos deben especificar la concentración")

        return medication


class SuplementoFactory(MedicationFactory):
    """
    Factory para crear suplementos
    Características especiales:
    - No son controlados
    - Unidad típica: tabletas o cápsulas
    """

    def create_medication(
            self,
            data: MedicationCreate,
            creado_por: Optional[UUID] = None
    ) -> Medication:
        medication = self._build_base_medication(data, creado_por)
        medication.tipo = MedicationType.SUPLEMENTO

        # Valores por defecto para suplementos
        medication.controlado = False

        if medication.unidad_medida == MedicationUnit.UNIDADES:
            medication.unidad_medida = MedicationUnit.CAPSULAS

        return medication


class InsumoClinicoFactory(MedicationFactory):
    """
    Factory para crear insumos clínicos
    Características especiales:
    - No son medicamentos propiamente dichos
    - Ejemplos: gasas, jeringas, guantes
    """

    def create_medication(
            self,
            data: MedicationCreate,
            creado_por: Optional[UUID] = None
    ) -> Medication:
        medication = self._build_base_medication(data, creado_por)
        medication.tipo = MedicationType.INSUMO_CLINICO

        # Valores por defecto para insumos
        medication.controlado = False
        medication.requiere_refrigeracion = False

        # Los insumos no requieren principio activo ni concentración
        medication.principio_activo = None
        medication.concentracion = None

        return medication


# ==================== REGISTRO DE FACTORIES ====================

class MedicationAbstractFactory:
    """
    Factory Manager - Selecciona la factory correcta según el tipo
    Patrón: Simple Factory + Abstract Factory
    """

    def __init__(self):
        self._factories = {
            MedicationType.VACUNA: VacunaFactory(),
            MedicationType.ANTIBIOTICO: AntibioticoFactory(),
            MedicationType.SUPLEMENTO: SuplementoFactory(),
            MedicationType.INSUMO_CLINICO: InsumoClinicoFactory()
        }

    def get_factory(self, tipo: MedicationType) -> MedicationFactory:
        """Obtiene la factory apropiada según el tipo de medicamento"""
        factory = self._factories.get(tipo)
        if not factory:
            raise ValueError(f"Tipo de medicamento no soportado: {tipo}")
        return factory

    def create_medication(
            self,
            data: MedicationCreate,
            creado_por: Optional[UUID] = None
    ) -> Medication:
        """
        Crea un medicamento usando la factory apropiada

        Args:
            data: Datos del medicamento
            creado_por: ID del usuario que crea el medicamento

        Returns:
            Instancia de Medication
        """
        factory = self.get_factory(data.tipo)
        return factory.create_medication(data, creado_por)