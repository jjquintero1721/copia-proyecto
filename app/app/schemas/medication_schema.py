"""
Schemas de validación para Medicamentos
Pydantic schemas para request/response
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.models.medication import MedicationType, MedicationUnit


# ==================== SCHEMAS DE MEDICAMENTO ====================

class MedicationBase(BaseModel):
    """Schema base de medicamento"""
    nombre: str = Field(..., min_length=3, max_length=200, description="Nombre del medicamento")
    tipo: MedicationType = Field(..., description="Tipo de medicamento")
    descripcion: Optional[str] = Field(None, max_length=500)
    principio_activo: Optional[str] = Field(None, max_length=200)
    concentracion: Optional[str] = Field(None, max_length=100)
    laboratorio: Optional[str] = Field(None, max_length=200)

    stock_actual: int = Field(default=0, ge=0, description="Stock actual")
    stock_minimo: int = Field(default=10, ge=0, description="Stock mínimo para alertas")
    stock_maximo: int = Field(default=1000, gt=0, description="Stock máximo permitido")
    unidad_medida: MedicationUnit = Field(default=MedicationUnit.UNIDADES)

    precio_compra: float = Field(default=0.0, ge=0, description="Precio de compra")
    precio_venta: float = Field(default=0.0, ge=0, description="Precio de venta")

    lote: Optional[str] = Field(None, max_length=100)
    fecha_vencimiento: Optional[datetime] = None
    ubicacion: Optional[str] = Field(None, max_length=100)
    requiere_refrigeracion: bool = Field(default=False)
    controlado: bool = Field(default=False)

    # Campos específicos por tipo
    enfermedad: Optional[str] = Field(None, max_length=200, description="Enfermedad que previene (vacunas)")
    dosis_recomendada: Optional[str] = Field(None, max_length=200)

    @field_validator('stock_actual')
    @classmethod
    def validate_stock_actual(cls, v, info):
        """Validar que el stock actual no exceda el máximo"""
        if 'stock_maximo' in info.data and v > info.data['stock_maximo']:
            raise ValueError('El stock actual no puede exceder el stock máximo')
        return v

    @field_validator('stock_minimo')
    @classmethod
    def validate_stock_minimo(cls, v, info):
        """Validar que el stock mínimo sea menor al máximo"""
        if 'stock_maximo' in info.data and v >= info.data['stock_maximo']:
            raise ValueError('El stock mínimo debe ser menor al stock máximo')
        return v


class MedicationCreate(MedicationBase):
    """Schema para crear medicamento"""
    pass


class MedicationUpdate(BaseModel):
    """Schema para actualizar medicamento"""
    nombre: Optional[str] = Field(None, min_length=3, max_length=200)
    descripcion: Optional[str] = Field(None, max_length=500)
    principio_activo: Optional[str] = Field(None, max_length=200)
    concentracion: Optional[str] = Field(None, max_length=100)
    laboratorio: Optional[str] = Field(None, max_length=200)

    stock_minimo: Optional[int] = Field(None, ge=0)
    stock_maximo: Optional[int] = Field(None, gt=0)
    unidad_medida: Optional[MedicationUnit] = None

    precio_compra: Optional[float] = Field(None, ge=0)
    precio_venta: Optional[float] = Field(None, ge=0)

    lote: Optional[str] = Field(None, max_length=100)
    fecha_vencimiento: Optional[datetime] = None
    ubicacion: Optional[str] = Field(None, max_length=100)
    requiere_refrigeracion: Optional[bool] = None
    controlado: Optional[bool] = None

    enfermedad: Optional[str] = Field(None, max_length=200)
    dosis_recomendada: Optional[str] = Field(None, max_length=200)
    activo: Optional[bool] = None


class MedicationResponse(MedicationBase):
    """Schema de respuesta de medicamento"""
    id: UUID
    activo: bool
    creado_en: datetime
    actualizado_en: datetime
    creado_por: Optional[UUID]
    requiere_reabastecimiento: bool
    porcentaje_stock: float

    class Config:
        from_attributes = True


# ==================== SCHEMAS DE MOVIMIENTO ====================

class InventoryMovementBase(BaseModel):
    """Schema base de movimiento de inventario"""
    medicamento_id: UUID
    tipo: str = Field(..., description="Tipo de movimiento (entrada/salida/ajuste/devolucion/merma)")
    cantidad: int = Field(..., gt=0, description="Cantidad de unidades")
    motivo: str = Field(..., min_length=5, max_length=500, description="Motivo del movimiento")
    referencia: Optional[str] = Field(None, max_length=200, description="Número de referencia")
    observaciones: Optional[str] = None
    costo_unitario: Optional[float] = Field(None, ge=0)

    @field_validator('tipo')
    @classmethod
    def validate_tipo(cls, v):
        """Validar tipo de movimiento"""
        valid_types = ['entrada', 'salida', 'ajuste', 'devolucion', 'merma']
        if v.lower() not in valid_types:
            raise ValueError(f'Tipo de movimiento inválido. Debe ser uno de: {", ".join(valid_types)}')
        return v.lower()


class InventoryMovementCreate(InventoryMovementBase):
    """Schema para crear movimiento de inventario"""
    pass


class InventoryMovementResponse(BaseModel):
    """Schema de respuesta de movimiento"""
    id: UUID
    medicamento_id: UUID
    tipo: str
    cantidad: int
    motivo: str
    referencia: Optional[str]
    observaciones: Optional[str]
    stock_anterior: int
    stock_nuevo: int
    costo_unitario: Optional[float]
    costo_total: Optional[float]
    fecha_movimiento: datetime
    realizado_por: UUID
    consulta_id: Optional[UUID]

    class Config:
        from_attributes = True


# ==================== SCHEMAS DE ALERTA ====================

class LowStockAlert(BaseModel):
    """Schema para alertas de stock bajo"""
    medicamento_id: UUID
    nombre: str
    tipo: MedicationType
    stock_actual: int
    stock_minimo: int
    diferencia: int
    porcentaje_stock: float
    requiere_accion_inmediata: bool

    class Config:
        from_attributes = True