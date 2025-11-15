"""
Modelo de Medicamento/Insumo
RF-10: Gestión de inventario de medicamentos
Implementa Abstract Factory para diferentes tipos de medicamentos
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum

from app.database import Base


class MedicationType(str, enum.Enum):
    """Tipos de medicamentos según Abstract Factory Pattern"""
    VACUNA = "vacuna"
    ANTIBIOTICO = "antibiotico"
    SUPLEMENTO = "suplemento"
    INSUMO_CLINICO = "insumo_clinico"


class MedicationUnit(str, enum.Enum):
    """Unidades de medida para medicamentos"""
    MILIGRAMOS = "mg"
    GRAMOS = "g"
    MILILITROS = "ml"
    LITROS = "l"
    TABLETAS = "tabletas"
    CAPSULAS = "capsulas"
    AMPOLLETAS = "ampolletas"
    UNIDADES = "unidades"


class Medication(Base):
    """
    Modelo de Medicamento/Insumo
    Soporta diferentes tipos mediante Abstract Factory
    """
    __tablename__ = "medicamentos"

    # Identificación
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(200), nullable=False, unique=True)
    tipo = Column(SQLEnum(MedicationType), nullable=False)

    # Información del medicamento
    descripcion = Column(String(500), nullable=True)
    principio_activo = Column(String(200), nullable=True)  # Para medicamentos farmacológicos
    concentracion = Column(String(100), nullable=True)  # Ej: "500mg/5ml"
    laboratorio = Column(String(200), nullable=True)

    # Inventario
    stock_actual = Column(Integer, nullable=False, default=0)
    stock_minimo = Column(Integer, nullable=False, default=10)
    stock_maximo = Column(Integer, nullable=False, default=1000)
    unidad_medida = Column(SQLEnum(MedicationUnit), nullable=False, default=MedicationUnit.UNIDADES)

    # Precios
    precio_compra = Column(Float, nullable=False, default=0.0)
    precio_venta = Column(Float, nullable=False, default=0.0)

    # Información adicional
    lote = Column(String(100), nullable=True)
    fecha_vencimiento = Column(DateTime(timezone=True), nullable=True)
    ubicacion = Column(String(100), nullable=True)  # Ubicación física en la clínica
    requiere_refrigeracion = Column(Boolean, default=False)
    controlado = Column(Boolean, default=False)  # Medicamento controlado

    # Información específica por tipo
    enfermedad = Column(String(200), nullable=True)  # Para vacunas
    dosis_recomendada = Column(String(200), nullable=True)

    # Estado y auditoría
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    actualizado_en = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                            onupdate=lambda: datetime.now(timezone.utc))
    creado_por = Column(UUID(as_uuid=True), ForeignKey('usuarios.id'), nullable=True)

    # Relaciones
    movimientos = relationship("InventoryMovement", back_populates="medicamento", lazy="select")

    def __repr__(self):
        return f"<Medication {self.nombre} - Stock: {self.stock_actual}/{self.stock_minimo}>"

    @property
    def requiere_reabastecimiento(self) -> bool:
        """Verifica si el stock está por debajo del mínimo"""
        return self.stock_actual <= self.stock_minimo

    @property
    def porcentaje_stock(self) -> float:
        """Calcula el porcentaje de stock actual respecto al máximo"""
        if self.stock_maximo == 0:
            return 0.0
        return (self.stock_actual / self.stock_maximo) * 100