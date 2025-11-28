"""
Modelo de Movimiento de Inventario
RF-10: Registro de entradas y salidas de medicamentos
RNF-07: Auditoría completa de movimientos
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum

from app.database import Base


class MovementType(str, enum.Enum):
    """Tipos de movimientos de inventario"""
    ENTRADA = "entrada"  # Compra, donación
    SALIDA = "salida"  # Uso en consulta, venta
    AJUSTE = "ajuste"  # Corrección de inventario
    DEVOLUCION = "devolucion"  # Devolución de proveedor
    MERMA = "merma"  # Producto vencido o dañado


class InventoryMovement(Base):
    """
    Modelo de Movimiento de Inventario
    Registra todas las entradas y salidas para auditoría (RNF-07)
    """
    __tablename__ = "movimientos_inventario"

    # Identificación
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    medicamento_id = Column(UUID(as_uuid=True), ForeignKey('medicamentos.id'), nullable=False)

    # Tipo de movimiento
    tipo = Column(SQLEnum(MovementType), nullable=False)
    cantidad = Column(Integer, nullable=False)

    # Información del movimiento
    motivo = Column(String(500), nullable=False)
    referencia = Column(String(200), nullable=True)  # Número de factura, orden, etc.
    observaciones = Column(Text, nullable=True)

    # Stock antes y después (para auditoría)
    stock_anterior = Column(Integer, nullable=False)
    stock_nuevo = Column(Integer, nullable=False)

    # Información de costos (opcional)
    costo_unitario = Column(Float, nullable=True)
    costo_total = Column(Float, nullable=True)

    # Auditoría
    fecha_movimiento = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    realizado_por = Column(UUID(as_uuid=True), ForeignKey('usuarios.id'), nullable=False)

    # Relación con consulta (si el movimiento es por uso en consulta)
    consulta_id = Column(UUID(as_uuid=True), ForeignKey('consultas.id'), nullable=True)

    # Relaciones
    medicamento = relationship("Medication", back_populates="movimientos")
    usuario = relationship("User", foreign_keys=[realizado_por])

    def __repr__(self):
        return f"<InventoryMovement {self.tipo} - {self.cantidad} unidades - {self.fecha_movimiento}>"