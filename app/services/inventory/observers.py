"""
Observer Pattern - Sistema de alertas de inventario
RF-10: Alertas de stock bajo
RNF-07: Auditoría de eventos
Patrón: Observer para notificar cuando el stock alcanza el mínimo
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime, timezone
from uuid import UUID

from app.models.medication import Medication


# ==================== PATRÓN OBSERVER ====================

class InventoryObserver(ABC):
    """
    Observador abstracto para eventos de inventario
    """

    @abstractmethod
    def actualizar(self, evento: str, medication: Medication, datos: Dict[str, Any]) -> None:
        """
        Método llamado cuando ocurre un evento en el inventario

        Args:
            evento: Tipo de evento (STOCK_BAJO, MEDICAMENTO_VENCIDO, etc.)
            medication: Medicamento afectado
            datos: Datos adicionales del evento
        """
        pass


class AlertaBajoStock(InventoryObserver):
    """
    Observer que genera alertas cuando el stock alcanza el mínimo
    RF-10: Alertas de stock mínimo

    Este observer se activa cuando:
    - El stock actual es <= stock mínimo
    - Se realiza un movimiento que deja el stock bajo
    """

    def actualizar(self, evento: str, medication: Medication, datos: Dict[str, Any]) -> None:
        """Genera alerta de stock bajo"""

        if evento == "STOCK_BAJO":
            self._generar_alerta_stock_bajo(medication, datos)
        elif evento == "STOCK_CRITICO":
            self._generar_alerta_critica(medication, datos)
        elif evento == "STOCK_ACTUALIZADO":
            self._verificar_stock(medication, datos)

    def _generar_alerta_stock_bajo(self, medication: Medication, _datos: Dict[str, Any]) -> None:
        """Genera alerta cuando el stock está bajo"""
        print(f"⚠️  [ALERTA STOCK BAJO] {medication.nombre}")
        print(f"   → Stock actual: {medication.stock_actual} {medication.unidad_medida.value}")
        print(f"   → Stock mínimo: {medication.stock_minimo} {medication.unidad_medida.value}")
        print(f"   → Tipo: {medication.tipo.value}")
        print("   → Requiere reabastecimiento URGENTE")

        # En producción, aquí se enviaría:
        # 1. Email a administradores
        # 2. Notificación push
        # 3. Registro en tabla de alertas
        # 4. Webhook a sistema de compras

    def _generar_alerta_critica(self, medication: Medication, _datos: Dict[str, Any]) -> None:
        """Genera alerta crítica cuando el stock es 0 o muy bajo"""
        print(f"🚨 [ALERTA CRÍTICA] {medication.nombre} - STOCK AGOTADO O CRÍTICO")
        print(f"   → Stock actual: {medication.stock_actual}")
        print("   → Se requiere compra INMEDIATA")
        print(f"   → Tipo: {medication.tipo.value}")

        if medication.stock_actual == 0:
            print("   → ⚠️  MEDICAMENTO AGOTADO - Sin existencias")

    def _verificar_stock(self, medication: Medication, datos: Dict[str, Any]) -> None:
        """Verifica el nivel de stock después de una actualización"""
        if medication.stock_actual <= medication.stock_minimo:
            if medication.stock_actual == 0:
                self._generar_alerta_critica(medication, datos)
            else:
                self._generar_alerta_stock_bajo(medication, datos)


class RegistroAuditoriaInventario(InventoryObserver):
    """
    Observer que registra auditoría de eventos de inventario
    RNF-07: Auditoría completa de operaciones
    """

    def actualizar(self, evento: str, medication: Medication, datos: Dict[str, Any]) -> None:
        """Registra eventos en el sistema de auditoría"""
        print(f"📋 [Auditoría Inventario] Evento: {evento}")
        print(f"   → Medicamento: {medication.nombre} (ID: {medication.id})")
        print(f"   → Fecha/Hora: {datetime.now(timezone.utc)}")
        print(f"   → Usuario: {datos.get('usuario_id', 'Sistema')}")
        print(f"   → Stock actual: {medication.stock_actual}")
        print(f"   → Detalles: {datos}")

        # En producción, aquí se guardaría en tabla de auditoría
        # audit_record = InventoryAuditLog(
        #     entidad="Medicamento",
        #     entidad_id=medication.id,
        #     evento=evento,
        #     usuario_id=datos.get('usuario_id'),
        #     detalles=json.dumps(datos),
        #     fecha=datetime.utcnow()
        # )


class NotificadorVencimiento(InventoryObserver):
    """
    Observer que notifica cuando un medicamento está próximo a vencer
    """

    def actualizar(self, evento: str, medication: Medication, datos: Dict[str, Any]) -> None:
        """Notifica sobre vencimientos"""
        if evento == "PROXIMO_VENCIMIENTO":
            print(f"📅 [Vencimiento Próximo] {medication.nombre}")
            print(f"   → Fecha de vencimiento: {medication.fecha_vencimiento}")
            print(f"   → Lote: {medication.lote}")
            print(f"   → Stock: {medication.stock_actual}")

        elif evento == "MEDICAMENTO_VENCIDO":
            print(f"❌ [Medicamento Vencido] {medication.nombre}")
            print(f"   → Fecha de vencimiento: {medication.fecha_vencimiento}")
            print(f"   → Lote: {medication.lote}")
            print("   → Acción requerida: Retirar del inventario")


class MetricasInventario(InventoryObserver):
    """
    Observer que registra métricas del inventario
    RNF-04: Monitoreo de rendimiento
    """

    def actualizar(self, evento: str, medication: Medication, datos: Dict[str, Any]) -> None:
        """Registra métricas de uso del inventario"""
        print(f"📊 [Métricas Inventario] Evento: {evento}")
        print(f"   → Medicamento: {medication.nombre}")
        print(f"   → Tipo: {medication.tipo.value}")

        # En producción, enviar métricas a sistema de monitoreo
        # (ej: Prometheus, CloudWatch, Datadog, etc.)
        # metrics.gauge('inventory.stock_level', medication.stock_actual)
        # metrics.gauge('inventory.stock_percentage', medication.porcentaje_stock)


# ==================== GESTOR DE INVENTARIO (SUBJECT) ====================

class GestorInventario:
    """
    Subject del patrón Observer
    Gestiona la lista de observadores y notifica eventos de inventario
    """

    def __init__(self):
        self._observadores: List[InventoryObserver] = []

    def agregar_observador(self, observador: InventoryObserver) -> None:
        """Agrega un observador a la lista"""
        if observador not in self._observadores:
            self._observadores.append(observador)

    def eliminar_observador(self, observador: InventoryObserver) -> None:
        """Elimina un observador de la lista"""
        if observador in self._observadores:
            self._observadores.remove(observador)

    def notificar(self, evento: str, medication: Medication, **datos) -> None:
        """
        Notifica a todos los observadores sobre un evento

        Args:
            evento: Tipo de evento (STOCK_BAJO, STOCK_ACTUALIZADO, etc.)
            medication: Medicamento afectado
            **datos: Datos adicionales del evento
        """
        for observador in self._observadores:
            observador.actualizar(evento, medication, datos)


# ==================== SINGLETON DEL GESTOR ====================

_gestor_inventario_instance = None


def get_gestor_inventario() -> GestorInventario:
    """
    Obtiene la instancia única del GestorInventario (Singleton)

    Returns:
        Instancia global del gestor de inventario
    """
    global _gestor_inventario_instance
    if _gestor_inventario_instance is None:
        _gestor_inventario_instance = GestorInventario()

        # Registrar observadores por defecto
        _gestor_inventario_instance.agregar_observador(AlertaBajoStock())
        _gestor_inventario_instance.agregar_observador(RegistroAuditoriaInventario())
        _gestor_inventario_instance.agregar_observador(NotificadorVencimiento())
        _gestor_inventario_instance.agregar_observador(MetricasInventario())

    return _gestor_inventario_instance