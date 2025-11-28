"""
Facade Pattern - Fachada de Inventario
Patrón: Facade para simplificar operaciones complejas
Relaciona con: RF-05, RF-07, RF-10, RNF-03 (usabilidad)

El Facade orquestra llamadas a múltiples servicios para completar operaciones complejas como:
- Registrar atención médica con descuento de inventario
- Gestión integral de stock con alertas
- Operaciones batch sobre múltiples medicamentos
"""

from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from app.models.medication import Medication
from app.models.inventory_movement import InventoryMovement
from app.schemas.medication_schema import MedicationCreate, LowStockAlert
from app.services.inventory.inventory_service import InventoryService


class InventoryFacade:
    """
    Facade Pattern - Interfaz simplificada para operaciones complejas de inventario

    Este Facade centraliza y simplifica la interacción con el módulo de inventario,
    facilitando su uso desde otros módulos (como Historias Clínicas o Citas).
    """

    def __init__(self, db: Session):
        self.db = db
        self.inventory_service = InventoryService(db)

    # ==================== OPERACIONES SIMPLIFICADAS ====================

    def registrar_uso_en_consulta(
            self,
            medicamentos_usados: List[Dict[str, Any]],
            consulta_id: UUID,
            usuario_id: UUID
    ) -> List[InventoryMovement]:
        """
        Registra el uso de múltiples medicamentos en una consulta

        Esta operación es usada desde el módulo de Historias Clínicas
        cuando se registra una atención médica.

        Args:
            medicamentos_usados: Lista de dicts con 'medicamento_id' y 'cantidad'
            consulta_id: ID de la consulta
            usuario_id: ID del veterinario

        Returns:
            Lista de movimientos de inventario creados

        Raises:
            ValueError: Si algún medicamento no tiene stock suficiente

        Example:
            medicamentos_usados = [
                {"medicamento_id": uuid1, "cantidad": 2},
                {"medicamento_id": uuid2, "cantidad": 1}
            ]
        """
        movimientos = []

        # Validar disponibilidad de TODOS los medicamentos primero
        for med_data in medicamentos_usados:
            medication = self.inventory_service.get_medication_by_id(med_data['medicamento_id'])
            if not medication:
                raise ValueError(f"Medicamento {med_data['medicamento_id']} no encontrado")

            if medication.stock_actual < med_data['cantidad']:
                raise ValueError(
                    f"Stock insuficiente de {medication.nombre}. "
                    f"Disponible: {medication.stock_actual}, Solicitado: {med_data['cantidad']}"
                )

        # Si todos tienen stock, proceder con los movimientos
        for med_data in medicamentos_usados:
            movement = self.inventory_service.registrar_salida(
                medicamento_id=med_data['medicamento_id'],
                cantidad=med_data['cantidad'],
                motivo=f"Uso en consulta médica (ID: {consulta_id})",
                usuario_id=usuario_id,
                consulta_id=consulta_id
            )
            movimientos.append(movement)

        return movimientos

    def verificar_disponibilidad_medicamentos(
            self,
            medicamentos_requeridos: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Verifica si hay stock disponible para una lista de medicamentos

        Args:
            medicamentos_requeridos: Lista de dicts con 'medicamento_id' y 'cantidad'

        Returns:
            Dict con disponibilidad y detalles de cada medicamento

        Example:
            {
                "disponible": True/False,
                "medicamentos": [
                    {
                        "medicamento_id": uuid,
                        "nombre": "Vacuna Antirrábica",
                        "cantidad_requerida": 2,
                        "stock_actual": 10,
                        "disponible": True
                    }
                ],
                "faltantes": []
            }
        """
        resultado = {
            "disponible": True,
            "medicamentos": [],
            "faltantes": []
        }

        for med_data in medicamentos_requeridos:
            medication = self.inventory_service.get_medication_by_id(med_data['medicamento_id'])

            if not medication:
                resultado["disponible"] = False
                resultado["faltantes"].append({
                    "medicamento_id": med_data['medicamento_id'],
                    "motivo": "No encontrado"
                })
                continue

            disponible = medication.stock_actual >= med_data['cantidad']

            med_info = {
                "medicamento_id": medication.id,
                "nombre": medication.nombre,
                "cantidad_requerida": med_data['cantidad'],
                "stock_actual": medication.stock_actual,
                "disponible": disponible
            }

            resultado["medicamentos"].append(med_info)

            if not disponible:
                resultado["disponible"] = False
                resultado["faltantes"].append({
                    "medicamento_id": medication.id,
                    "nombre": medication.nombre,
                    "cantidad_requerida": med_data['cantidad'],
                    "stock_actual": medication.stock_actual,
                    "faltante": med_data['cantidad'] - medication.stock_actual
                })

        return resultado

    def realizar_compra_masiva(
            self,
            compras: List[Dict[str, Any]],
            usuario_id: UUID,
            proveedor: str,
            numero_factura: str
    ) -> List[InventoryMovement]:
        """
        Registra múltiples entradas de inventario de una compra

        Args:
            compras: Lista de dicts con 'medicamento_id', 'cantidad' y 'costo_unitario'
            usuario_id: ID del usuario que registra la compra
            proveedor: Nombre del proveedor
            numero_factura: Número de factura de la compra

        Returns:
            Lista de movimientos de inventario creados
        """
        movimientos = []

        for compra in compras:
            movement = self.inventory_service.registrar_entrada(
                medicamento_id=compra['medicamento_id'],
                cantidad=compra['cantidad'],
                motivo=f"Compra a proveedor: {proveedor}",
                usuario_id=usuario_id,
                costo_unitario=compra.get('costo_unitario'),
                referencia=numero_factura,
                observaciones=f"Factura: {numero_factura} - Proveedor: {proveedor}"
            )
            movimientos.append(movement)

        return movimientos

    def generar_orden_compra_automatica(self) -> List[Dict[str, Any]]:
        """
        Genera una orden de compra automática para medicamentos con stock bajo

        Returns:
            Lista de medicamentos que requieren compra con cantidades sugeridas
        """
        medications_low_stock = self.inventory_service.get_low_stock_medications()

        orden_compra = []
        for med in medications_low_stock:
            cantidad_sugerida = med.stock_maximo - med.stock_actual

            orden_compra.append({
                "medicamento_id": med.id,
                "nombre": med.nombre,
                "tipo": med.tipo.value,
                "stock_actual": med.stock_actual,
                "stock_minimo": med.stock_minimo,
                "stock_maximo": med.stock_maximo,
                "cantidad_sugerida": cantidad_sugerida,
                "precio_compra": med.precio_compra,
                "costo_total_estimado": cantidad_sugerida * med.precio_compra,
                "prioridad": "URGENTE" if med.stock_actual == 0 else "ALTA"
            })

        return orden_compra

    def obtener_resumen_inventario(self) -> Dict[str, Any]:
        """
        Obtiene un resumen completo del estado del inventario

        Returns:
            Dict con estadísticas y alertas del inventario
        """
        # Obtener todos los medicamentos
        all_medications = self.inventory_service.get_all_medications(limit=1000)

        # Medicamentos con stock bajo
        low_stock = self.inventory_service.get_low_stock_medications()

        # Medicamentos vencidos
        expired = self.inventory_service.get_expired_medications()

        # Estadísticas por tipo
        stats_by_type = self.inventory_service.medication_repo.count_by_tipo()

        # Calcular valor total del inventario
        valor_total = sum(
            med.stock_actual * med.precio_compra
            for med in all_medications
            if med.precio_compra
        )

        resumen = {
            "total_medicamentos": len(all_medications),
            "medicamentos_activos": len([m for m in all_medications if m.activo]),
            "alertas_stock_bajo": len(low_stock),
            "medicamentos_vencidos": len(expired),
            "medicamentos_criticos": len([m for m in low_stock if m.stock_actual == 0]),
            "estadisticas_por_tipo": stats_by_type,
            "valor_total_inventario": round(valor_total, 2),
            "requiere_atencion": len(low_stock) > 0 or len(expired) > 0
        }

        return resumen

    def obtener_dashboard_inventario(self) -> Dict[str, Any]:
        """
        Obtiene datos para el dashboard de inventario

        Returns:
            Dict con datos listos para visualización en dashboard
        """
        resumen = self.obtener_resumen_inventario()
        alertas = self.inventory_service.get_low_stock_alerts()
        vencidos = self.inventory_service.get_expired_medications()

        dashboard = {
            "resumen": resumen,
            "alertas_criticas": [
                alert for alert in alertas
                if alert.requiere_accion_inmediata
            ],
            "alertas_advertencia": [
                alert for alert in alertas
                if not alert.requiere_accion_inmediata
            ],
            "medicamentos_vencidos": [
                {
                    "id": med.id,
                    "nombre": med.nombre,
                    "lote": med.lote,
                    "fecha_vencimiento": med.fecha_vencimiento,
                    "stock_actual": med.stock_actual
                }
                for med in vencidos
            ]
        }

        return dashboard