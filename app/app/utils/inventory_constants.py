"""
Constantes del módulo de Inventario
RF-10: Gestión de inventario
"""


# Tipos de medicamentos (Abstract Factory)
class MedicationTypes:
    VACUNA = "vacuna"
    ANTIBIOTICO = "antibiotico"
    SUPLEMENTO = "suplemento"
    INSUMO_CLINICO = "insumo_clinico"


# Tipos de movimientos de inventario
class MovementTypes:
    ENTRADA = "entrada"  # Compra, donación
    SALIDA = "salida"  # Uso en consulta, venta
    AJUSTE = "ajuste"  # Corrección de inventario
    DEVOLUCION = "devolucion"  # Devolución de proveedor
    MERMA = "merma"  # Producto vencido o dañado


# Unidades de medida
class MedicationUnits:
    MILIGRAMOS = "mg"
    GRAMOS = "g"
    MILILITROS = "ml"
    LITROS = "l"
    TABLETAS = "tabletas"
    CAPSULAS = "capsulas"
    AMPOLLETAS = "ampolletas"
    UNIDADES = "unidades"


# Eventos de inventario para Observer Pattern
class InventoryEvents:
    MEDICAMENTO_CREADO = "MEDICAMENTO_CREADO"
    MEDICAMENTO_ACTUALIZADO = "MEDICAMENTO_ACTUALIZADO"
    MEDICAMENTO_DESACTIVADO = "MEDICAMENTO_DESACTIVADO"
    STOCK_BAJO = "STOCK_BAJO"
    STOCK_CRITICO = "STOCK_CRITICO"
    STOCK_ACTUALIZADO = "STOCK_ACTUALIZADO"
    STOCK_AJUSTADO = "STOCK_AJUSTADO"
    MEDICAMENTO_VENCIDO = "MEDICAMENTO_VENCIDO"
    PROXIMO_VENCIMIENTO = "PROXIMO_VENCIMIENTO"