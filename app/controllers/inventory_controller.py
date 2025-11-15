"""
Controlador de Inventario - Endpoints REST API
RF-10: Gestión de inventario de medicamentos
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID

from app.database import get_db
from app.security.dependencies import (get_current_active_user, require_staff as verificar_rol_staff )
from app.schemas.medication_schema import (
    MedicationCreate, MedicationUpdate, MedicationResponse,
    InventoryMovementCreate, InventoryMovementResponse,
    LowStockAlert
)
from app.services.inventory.inventory_service import InventoryService
from app.services.inventory.inventory_facade import InventoryFacade
from app.utils.responses import success_response, error_response

router = APIRouter()


# ==================== ENDPOINTS DE MEDICAMENTOS ====================

@router.post("/medications", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_medication(
        medication_data: MedicationCreate,
        db: Session = Depends(get_db),
        current_user=Depends(verificar_rol_staff)
):
    """
    Crea un nuevo medicamento en el inventario

    **RF-10:** Gestión de inventario
    **Abstract Factory:** Usa factory apropiada según tipo
    **Observer:** Notifica si stock bajo

    **Acceso:** Staff (Superadmin, Veterinario, Auxiliar)

    **Tipos de medicamento:**
    - vacuna: Requiere enfermedad y refrigeración
    - antibiotico: Requiere principio activo y concentración
    - suplemento: No controlado
    - insumo_clinico: Insumos médicos (gasas, jeringas, etc.)
    """
    try:
        service = InventoryService(db)
        medication = service.create_medication(medication_data, current_user.id)

        return success_response(
            data=MedicationResponse.model_validate(medication),
            message="Medicamento creado exitosamente"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/medications", response_model=dict)
def get_all_medications(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        tipo: Optional[str] = None,
        solo_bajos_stock: bool = False,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_active_user)):
    """
    Obtiene todos los medicamentos con filtros opcionales

    **Filtros:**
    - tipo: Filtrar por tipo de medicamento
    - solo_bajos_stock: Solo medicamentos con stock <= stock_minimo

    **Acceso:** Todos los usuarios autenticados
    """
    try:
        service = InventoryService(db)
        medications = service.get_all_medications(skip, limit, tipo, solo_bajos_stock)

        return success_response(
            data=[MedicationResponse.model_validate(m) for m in medications],
            message=f"Se encontraron {len(medications)} medicamentos"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/medications/{medication_id}", response_model=dict)
def get_medication(
        medication_id: UUID,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_active_user)
):
    """
    Obtiene un medicamento por ID

    **Acceso:** Todos los usuarios autenticados
    """
    try:
        service = InventoryService(db)
        medication = service.get_medication_by_id(medication_id)

        if not medication:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medicamento no encontrado"
            )

        return success_response(
            data=MedicationResponse.model_validate(medication)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/medications/{medication_id}", response_model=dict)
def update_medication(
        medication_id: UUID,
        medication_data: MedicationUpdate,
        db: Session = Depends(get_db),
        current_user=Depends(verificar_rol_staff)
):
    """
    Actualiza un medicamento existente

    **Acceso:** Staff (Superadmin, Veterinario, Auxiliar)
    """
    try:
        service = InventoryService(db)
        medication = service.update_medication(medication_id, medication_data, current_user.id)

        return success_response(
            data=MedicationResponse.model_validate(medication),
            message="Medicamento actualizado exitosamente"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/medications/{medication_id}", response_model=dict)
def delete_medication(
        medication_id: UUID,
        db: Session = Depends(get_db),
        current_user=Depends(verificar_rol_staff)
):
    """
    Desactiva un medicamento (borrado lógico)

    **Acceso:** Staff (Superadmin, Veterinario, Auxiliar)
    """
    try:
        service = InventoryService(db)
        medication = service.delete_medication(medication_id)

        return success_response(
            message=f"Medicamento {medication.nombre} desactivado exitosamente"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/medications/search/{search_term}", response_model=dict)
def search_medications(
        search_term: str,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_active_user)
):
    """
    Busca medicamentos por nombre, principio activo o descripción

    **Acceso:** Todos los usuarios autenticados
    """
    try:
        service = InventoryService(db)
        medications = service.search_medications(search_term)

        return success_response(
            data=[MedicationResponse.model_validate(m) for m in medications],
            message=f"Se encontraron {len(medications)} resultados"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ==================== ENDPOINTS DE MOVIMIENTOS ====================

@router.post("/movements/entrada", response_model=dict, status_code=status.HTTP_201_CREATED)
def registrar_entrada(
        movement_data: InventoryMovementCreate,
        db: Session = Depends(get_db),
        current_user=Depends(verificar_rol_staff)
):
    """
    Registra una entrada de inventario (compra, donación)

    **RF-10:** Movimientos de inventario
    **Observer:** Notifica actualización de stock

    **Acceso:** Staff (Superadmin, Veterinario, Auxiliar)
    """
    try:
        service = InventoryService(db)
        movement = service.registrar_entrada(
            medicamento_id=movement_data.medicamento_id,
            cantidad=movement_data.cantidad,
            motivo=movement_data.motivo,
            usuario_id=current_user.id,
            costo_unitario=movement_data.costo_unitario,
            referencia=movement_data.referencia,
            observaciones=movement_data.observaciones
        )

        return success_response(
            data=InventoryMovementResponse.model_validate(movement),
            message="Entrada de inventario registrada exitosamente"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/movements/salida", response_model=dict, status_code=status.HTTP_201_CREATED)
def registrar_salida(
        movement_data: InventoryMovementCreate,
        db: Session = Depends(get_db),
        current_user=Depends(verificar_rol_staff)
):
    """
    Registra una salida de inventario (uso en consulta, venta)

    **RF-10:** Movimientos de inventario
    **Observer:** Notifica actualización de stock y alerta si queda bajo

    **Acceso:** Staff (Superadmin, Veterinario, Auxiliar)
    """
    try:
        service = InventoryService(db)
        movement = service.registrar_salida(
            medicamento_id=movement_data.medicamento_id,
            cantidad=movement_data.cantidad,
            motivo=movement_data.motivo,
            usuario_id=current_user.id,
            referencia=movement_data.referencia,
            observaciones=movement_data.observaciones
        )

        return success_response(
            data=InventoryMovementResponse.model_validate(movement),
            message="Salida de inventario registrada exitosamente"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/movements/medication/{medication_id}", response_model=dict)
def get_medication_history(
        medication_id: UUID,
        limit: int = Query(50, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user=Depends(get_current_active_user)
):
    """
    Obtiene el historial de movimientos de un medicamento

    **RNF-07:** Auditoría de movimientos
    **Acceso:** Todos los usuarios autenticados
    """
    try:
        service = InventoryService(db)
        movements = service.get_medication_history(medication_id, limit)

        return success_response(
            data=[InventoryMovementResponse.model_validate(m) for m in movements],
            message=f"Historial de {len(movements)} movimientos"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ==================== ENDPOINTS DE ALERTAS ====================

@router.get("/alerts/low-stock", response_model=dict)
def get_low_stock_alerts(
        db: Session = Depends(get_db),
        current_user=Depends(verificar_rol_staff)
):
    """
    Obtiene alertas de medicamentos con stock bajo

    **RF-10:** Alertas de stock mínimo
    **Observer Pattern:** AlertaBajoStock genera alertas automáticas

    **Acceso:** Staff (Superadmin, Veterinario, Auxiliar)
    """
    try:
        service = InventoryService(db)
        alerts = service.get_low_stock_alerts()

        return success_response(
            data=[alert.model_dump() for alert in alerts],
            message=f"Se encontraron {len(alerts)} alertas de stock bajo"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/alerts/expired", response_model=dict)
def get_expired_medications(
        db: Session = Depends(get_db),
        current_user=Depends(verificar_rol_staff)
):
    """
    Obtiene medicamentos vencidos

    **Observer:** Notifica sobre medicamentos vencidos
    **Acceso:** Staff (Superadmin, Veterinario, Auxiliar)
    """
    try:
        service = InventoryService(db)
        medications = service.get_expired_medications()

        return success_response(
            data=[MedicationResponse.model_validate(m) for m in medications],
            message=f"Se encontraron {len(medications)} medicamentos vencidos"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ==================== ENDPOINTS DEL FACADE ====================

@router.get("/dashboard", response_model=dict)
def get_inventory_dashboard(
        db: Session = Depends(get_db),
        current_user=Depends(verificar_rol_staff)
):
    """
    Obtiene datos para el dashboard de inventario

    **Facade Pattern:** Orquesta múltiples operaciones
    **Acceso:** Staff (Superadmin, Veterinario, Auxiliar)
    """
    try:
        facade = InventoryFacade(db)
        dashboard = facade.obtener_dashboard_inventario()

        return success_response(
            data=dashboard,
            message="Dashboard de inventario generado exitosamente"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/purchase-order", response_model=dict)
def generate_purchase_order(
        db: Session = Depends(get_db),
        current_user=Depends(verificar_rol_staff)
):
    """
    Genera orden de compra automática para medicamentos con stock bajo

    **Facade Pattern:** Simplifica operación compleja
    **Acceso:** Staff (Superadmin, Veterinario, Auxiliar)
    """
    try:
        facade = InventoryFacade(db)
        orden_compra = facade.generar_orden_compra_automatica()

        return success_response(
            data=orden_compra,
            message=f"Orden de compra generada con {len(orden_compra)} medicamentos"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))