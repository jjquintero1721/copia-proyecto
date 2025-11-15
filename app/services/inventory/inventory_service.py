"""
Servicio de Inventario - Lógica de negocio principal
RF-10: Gestión de inventario de medicamentos
Implementa patrones: Abstract Factory, Observer, Template Method
"""

from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone, timedelta

from app.models.medication import Medication
from app.models.inventory_movement import InventoryMovement, MovementType
from app.repositories.medication_repository import MedicationRepository
from app.repositories.inventory_movement_repository import InventoryMovementRepository
from app.schemas.medication_schema import (
    MedicationCreate, MedicationUpdate, LowStockAlert
)
from app.services.inventory.medication_factory import MedicationAbstractFactory
from app.services.inventory.observers import get_gestor_inventario


class InventoryService:
    """
    Servicio principal de gestión de inventario
    Implementa patrones: Factory, Observer, Template Method
    """

    MEDICATION_NOT_FOUND_MSG = "Medicamento no encontrado"

    def __init__(self, db: Session):
        self.db = db
        self.medication_repo = MedicationRepository(db)
        self.movement_repo = InventoryMovementRepository(db)
        self.factory = MedicationAbstractFactory()
        self.gestor = get_gestor_inventario()

    # ==================== GESTIÓN DE MEDICAMENTOS ====================

    def create_medication(
            self,
            medication_data: MedicationCreate,
            creado_por: Optional[UUID] = None
    ) -> Medication:
        """
        Crea un nuevo medicamento usando Abstract Factory Pattern

        Template Method:
        1. Validar datos
        2. Crear con factory apropiada
        3. Persistir
        4. Notificar observadores

        Args:
            medication_data: Datos del medicamento
            creado_por: ID del usuario que crea el medicamento

        Returns:
            Medicamento creado

        Raises:
            ValueError: Si hay errores de validación
        """
        # 1. Validar que no exista otro medicamento con el mismo nombre
        if self.medication_repo.exists_by_nombre(medication_data.nombre):
            raise ValueError(f"Ya existe un medicamento con el nombre: {medication_data.nombre}")

        # 2. Crear medicamento usando Abstract Factory
        medication = self.factory.create_medication(medication_data, creado_por)

        # 3. Persistir en base de datos
        medication = self.medication_repo.create(medication)

        # 4. Notificar a observadores
        self.gestor.notificar(
            "MEDICAMENTO_CREADO",
            medication,
            usuario_id=creado_por,
            accion="Creación de medicamento"
        )

        # 5. Verificar si requiere reabastecimiento
        if medication.requiere_reabastecimiento:
            self.gestor.notificar("STOCK_BAJO", medication, usuario_id=creado_por)

        return medication

    def get_medication_by_id(self, medication_id: UUID) -> Optional[Medication]:
        """Obtiene un medicamento por ID"""
        return self.medication_repo.get_by_id(medication_id)

    def get_all_medications(
            self,
            skip: int = 0,
            limit: int = 100,
            tipo: Optional[str] = None,
            solo_bajos_stock: bool = False
    ) -> List[Medication]:
        """Obtiene todos los medicamentos con filtros opcionales"""
        return self.medication_repo.get_all(
            skip=skip,
            limit=limit,
            tipo=tipo,
            solo_bajos_stock=solo_bajos_stock
        )

    def update_medication(
            self,
            medication_id: UUID,
            medication_data: MedicationUpdate,
            usuario_id: Optional[UUID] = None
    ) -> Medication:
        """
        Actualiza un medicamento existente

        Args:
            medication_id: ID del medicamento
            medication_data: Datos a actualizar
            usuario_id: ID del usuario que actualiza

        Returns:
            Medicamento actualizado
        """
        medication = self.medication_repo.get_by_id(medication_id)
        if not medication:
            raise ValueError(self.MEDICATION_NOT_FOUND_MSG)

        # Validar nombre único si se está cambiando
        if medication_data.nombre and medication_data.nombre != medication.nombre:
            if self.medication_repo.exists_by_nombre(medication_data.nombre, exclude_id=medication_id):
                raise ValueError(f"Ya existe un medicamento con el nombre: {medication_data.nombre}")

        # Actualizar campos
        update_fields = medication_data.model_dump(exclude_unset=True)
        for field, value in update_fields.items():
            setattr(medication, field, value)

        medication = self.medication_repo.update(medication)

        # Notificar actualización
        self.gestor.notificar(
            "MEDICAMENTO_ACTUALIZADO",
            medication,
            usuario_id=usuario_id,
            cambios=update_fields
        )

        return medication

    def delete_medication(self, medication_id: UUID) -> Medication:
        """Desactiva un medicamento (borrado lógico)"""
        medication = self.medication_repo.get_by_id(medication_id)
        if not medication:
            raise ValueError(self.MEDICATION_NOT_FOUND_MSG)

        medication = self.medication_repo.soft_delete(medication)

        self.gestor.notificar(
            "MEDICAMENTO_DESACTIVADO",
            medication
        )

        return medication

    # ==================== MOVIMIENTOS DE INVENTARIO ====================

    def registrar_entrada(
            self,
            medicamento_id: UUID,
            cantidad: int,
            motivo: str,
            usuario_id: UUID,
            costo_unitario: Optional[float] = None,
            referencia: Optional[str] = None,
            observaciones: Optional[str] = None
    ) -> InventoryMovement:
        """
        Registra una entrada de inventario (compra, donación)

        RF-10: Movimientos de inventario

        Args:
            medicamento_id: ID del medicamento
            cantidad: Cantidad a ingresar
            motivo: Motivo del movimiento
            usuario_id: ID del usuario que realiza el movimiento
            costo_unitario: Costo por unidad (opcional)
            referencia: Número de factura u orden (opcional)
            observaciones: Observaciones adicionales (opcional)

        Returns:
            Movimiento de inventario creado
        """
        medication = self.medication_repo.get_by_id(medicamento_id)
        if not medication:
            raise ValueError(self.MEDICATION_NOT_FOUND_MSG)

        # Guardar stock anterior
        stock_anterior = medication.stock_actual

        # Calcular nuevo stock
        nuevo_stock = stock_anterior + cantidad

        # Validar que no exceda el máximo
        if nuevo_stock > medication.stock_maximo:
            raise ValueError(
                f"La cantidad excede el stock máximo permitido. "
                f"Máximo: {medication.stock_maximo}, Nuevo total: {nuevo_stock}"
            )

        # Actualizar stock
        medication.stock_actual = nuevo_stock
        medication = self.medication_repo.update(medication)

        # Crear movimiento
        movement = InventoryMovement(
            medicamento_id=medicamento_id,
            tipo=MovementType.ENTRADA,
            cantidad=cantidad,
            motivo=motivo,
            referencia=referencia,
            observaciones=observaciones,
            stock_anterior=stock_anterior,
            stock_nuevo=nuevo_stock,
            costo_unitario=costo_unitario,
            costo_total=costo_unitario * cantidad if costo_unitario else None,
            realizado_por=usuario_id
        )

        movement = self.movement_repo.create(movement)

        # Notificar observadores
        self.gestor.notificar(
            "STOCK_ACTUALIZADO",
            medication,
            usuario_id=usuario_id,
            tipo_movimiento="entrada",
            cantidad=cantidad,
            stock_anterior=stock_anterior,
            stock_nuevo=nuevo_stock
        )

        return movement

    def registrar_salida(
            self,
            medicamento_id: UUID,
            cantidad: int,
            motivo: str,
            usuario_id: UUID,
            consulta_id: Optional[UUID] = None,
            referencia: Optional[str] = None,
            observaciones: Optional[str] = None
    ) -> InventoryMovement:
        """
        Registra una salida de inventario (uso en consulta, venta)

        RF-10: Movimientos de inventario
        Facade Pattern: Se usa desde AppointmentFacade al registrar atención

        Args:
            medicamento_id: ID del medicamento
            cantidad: Cantidad a retirar
            motivo: Motivo del movimiento
            usuario_id: ID del usuario que realiza el movimiento
            consulta_id: ID de la consulta relacionada (opcional)
            referencia: Número de referencia (opcional)
            observaciones: Observaciones adicionales (opcional)

        Returns:
            Movimiento de inventario creado
        """
        medication = self.medication_repo.get_by_id(medicamento_id)
        if not medication:
            raise ValueError(self.MEDICATION_NOT_FOUND_MSG)

        # Guardar stock anterior
        stock_anterior = medication.stock_actual

        # Validar que haya suficiente stock
        if stock_anterior < cantidad:
            raise ValueError(
                f"Stock insuficiente. Disponible: {stock_anterior}, Solicitado: {cantidad}"
            )

        # Calcular nuevo stock
        nuevo_stock = stock_anterior - cantidad

        # Actualizar stock
        medication.stock_actual = nuevo_stock
        medication = self.medication_repo.update(medication)

        # Crear movimiento
        movement = InventoryMovement(
            medicamento_id=medicamento_id,
            tipo=MovementType.SALIDA,
            cantidad=cantidad,
            motivo=motivo,
            referencia=referencia,
            observaciones=observaciones,
            stock_anterior=stock_anterior,
            stock_nuevo=nuevo_stock,
            realizado_por=usuario_id,
            consulta_id=consulta_id
        )

        movement = self.movement_repo.create(movement)

        # Notificar observadores
        self.gestor.notificar(
            "STOCK_ACTUALIZADO",
            medication,
            usuario_id=usuario_id,
            tipo_movimiento="salida",
            cantidad=cantidad,
            stock_anterior=stock_anterior,
            stock_nuevo=nuevo_stock
        )

        # Verificar si el stock quedó bajo
        if medication.requiere_reabastecimiento:
            if medication.stock_actual == 0:
                self.gestor.notificar("STOCK_CRITICO", medication, usuario_id=usuario_id)
            else:
                self.gestor.notificar("STOCK_BAJO", medication, usuario_id=usuario_id)

        return movement

    def ajustar_stock(
            self,
            medicamento_id: UUID,
            nueva_cantidad: int,
            motivo: str,
            usuario_id: UUID,
            observaciones: Optional[str] = None
    ) -> InventoryMovement:
        """
        Ajusta el stock de un medicamento (corrección de inventario)

        Args:
            medicamento_id: ID del medicamento
            nueva_cantidad: Nueva cantidad en stock
            motivo: Motivo del ajuste
            usuario_id: ID del usuario que realiza el ajuste
            observaciones: Observaciones adicionales

        Returns:
            Movimiento de inventario creado
        """
        medication = self.medication_repo.get_by_id(medicamento_id)
        if not medication:
            raise ValueError(self.MEDICATION_NOT_FOUND_MSG)

        stock_anterior = medication.stock_actual
        diferencia = nueva_cantidad - stock_anterior

        # Actualizar stock
        medication.stock_actual = nueva_cantidad
        medication = self.medication_repo.update(medication)

        # Crear movimiento
        movement = InventoryMovement(
            medicamento_id=medicamento_id,
            tipo=MovementType.AJUSTE,
            cantidad=abs(diferencia),
            motivo=motivo,
            observaciones=observaciones,
            stock_anterior=stock_anterior,
            stock_nuevo=nueva_cantidad,
            realizado_por=usuario_id
        )

        movement = self.movement_repo.create(movement)

        # Notificar observadores
        self.gestor.notificar(
            "STOCK_AJUSTADO",
            medication,
            usuario_id=usuario_id,
            stock_anterior=stock_anterior,
            stock_nuevo=nueva_cantidad,
            diferencia=diferencia
        )

        return movement

    # ==================== ALERTAS Y REPORTES ====================

    def get_low_stock_medications(self) -> List[Medication]:
        """
        Obtiene medicamentos con stock bajo
        RF-10: Alertas de stock mínimo
        """
        return self.medication_repo.get_low_stock_medications()

    def get_low_stock_alerts(self) -> List[LowStockAlert]:
        """Genera alertas detalladas de medicamentos con stock bajo"""
        medications = self.get_low_stock_medications()

        alerts = []
        for med in medications:
            alert = LowStockAlert(
                medicamento_id=med.id,
                nombre=med.nombre,
                tipo=med.tipo,
                stock_actual=med.stock_actual,
                stock_minimo=med.stock_minimo,
                diferencia=med.stock_minimo - med.stock_actual,
                porcentaje_stock=med.porcentaje_stock,
                requiere_accion_inmediata=med.stock_actual == 0
            )
            alerts.append(alert)

        return alerts

    def get_expired_medications(self) -> List[Medication]:
        """Obtiene medicamentos vencidos"""
        medications = self.medication_repo.get_expired_medications()

        # Notificar sobre medicamentos vencidos
        for med in medications:
            self.gestor.notificar("MEDICAMENTO_VENCIDO", med)

        return medications

    def get_medication_history(
            self,
            medicamento_id: UUID,
            limit: int = 50
    ) -> List[InventoryMovement]:
        """Obtiene el historial de movimientos de un medicamento"""
        return self.movement_repo.get_by_medication(medicamento_id, limit)

    def search_medications(self, search_term: str) -> List[Medication]:
        """Busca medicamentos por nombre, principio activo o descripción"""
        return self.medication_repo.search(search_term)