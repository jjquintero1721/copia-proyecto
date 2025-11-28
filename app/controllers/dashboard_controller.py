"""
Controlador de Dashboard - Estadísticas según rol
Proporciona datos agregados para el dashboard del sistema

Endpoints:
- GET /dashboard/stats - Obtener estadísticas del dashboard según rol

Principios SOLID:
- Single Responsibility: Solo maneja estadísticas del dashboard
- Open/Closed: Extensible para nuevas métricas
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime, date, timezone

from app.database import get_db
from app.security.dependencies import get_current_active_user
from app.models.user import User, UserRole
from app.utils.responses import success_response

from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.pet_repository import PetRepository
from app.repositories.owner_repository import OwnerRepository
from app.services.inventory.inventory_service import InventoryService

router = APIRouter()


# ==================== HELPER FUNCTIONS ====================

def get_today_date() -> date:
    """Obtiene la fecha de hoy en UTC"""
    return datetime.now(timezone.utc).date()


def get_staff_dashboard_stats(db: Session) -> dict:
    """
    Estadísticas para staff (superadmin, veterinario, auxiliar)

    Returns:
        Dict con estadísticas del día y alertas
    """
    today = get_today_date()

    # Repositorios
    appointment_repo = AppointmentRepository(db)
    inventory_service = InventoryService(db)

    # Citas del día (todas las programadas para hoy)
    from app.services.appointment.appointment_service import AppointmentService
    apt_service = AppointmentService(db)
    citas_hoy = apt_service.get_appointments_by_date(today)

    # Citas programadas (futuras, estado AGENDADA o CONFIRMADA)
    from app.models.appointment import AppointmentStatus
    citas_programadas = appointment_repo.count_by_status([
        AppointmentStatus.AGENDADA,
        AppointmentStatus.CONFIRMADA
    ])

    # Alertas de stock bajo
    alertas_stock = inventory_service.get_low_stock_alerts()
    stock_bajo_count = len(alertas_stock)

    # Notificaciones (por ahora en 0, se implementará después)
    notificaciones_count = 0

    return {
        "citasDelDia": len(citas_hoy),
        "citasProgramadas": citas_programadas,
        "stockBajo": stock_bajo_count,
        "notificaciones": notificaciones_count,
        "citasDetalle": [
            {
                "id": str(cita.id),
                "mascota_nombre": cita.mascota.nombre if cita.mascota else "Sin mascota",
                "propietario_nombre": cita.mascota.propietario.nombre if cita.mascota and cita.mascota.propietario else "Sin propietario",
                "fecha_hora": cita.fecha_hora.isoformat(),
                "estado": cita.estado.value,
                "servicio": cita.servicio.nombre if cita.servicio else "Sin servicio"
            }
            for cita in citas_hoy[:5]  # Máximo 5 citas para el resumen
        ],
        "alertasStock": [
            {
                "medicamento": alert.nombre,
                "stock_actual": alert.stock_actual,
                "stock_minimo": alert.stock_minimo,
                "requiere_accion_inmediata": alert.requiere_accion_inmediata
            }
            for alert in alertas_stock[:5]  # Máximo 5 alertas
        ]
    }


def get_owner_dashboard_stats(db: Session, user: User) -> dict:
    """
    Estadísticas para propietario

    Returns:
        Dict con mascotas y próximas citas del propietario
    """
    # Obtener el propietario asociado al usuario
    owner_repo = OwnerRepository(db)
    owner = owner_repo.get_by_usuario_id(user.id)

    if not owner:
        return {
            "propietario": None,
            "mascotas": [],
            "proximasCitas": [],
            "mensaje": "No se encontró información de propietario"
        }

    # Obtener mascotas del propietario
    pet_repo = PetRepository(db)
    mascotas = pet_repo.get_by_owner_id(owner.id)

    # Obtener próximas citas del propietario
    appointment_repo = AppointmentRepository(db)
    from app.models.appointment import AppointmentStatus

    # IDs de las mascotas
    mascota_ids = [str(mascota.id) for mascota in mascotas]  # si tu repos usa UUID en string

    # Obtener citas futuras de las mascotas
    proximas_citas = []
    if mascota_ids:
        today = datetime.now(timezone.utc)
        for mascota_id in mascota_ids:
            citas = appointment_repo.get_by_mascota(mascota_id)
            # Filtrar solo citas futuras y activas
            citas_futuras = [
                cita for cita in citas
                if cita.fecha_hora >= today and cita.estado in [
                    AppointmentStatus.AGENDADA,
                    AppointmentStatus.CONFIRMADA
                ]
            ]
            proximas_citas.extend(citas_futuras)

    # Ordenar por fecha
    proximas_citas.sort(key=lambda x: x.fecha_hora)

    # Seleccionar una mascota al azar para el saludo (preferir la primera)
    mascota_saludo = mascotas[0] if mascotas else None

    return {
        "propietario": {
            "id": str(owner.id),
            "nombre": owner.nombre,
            "documento": owner.documento
        },
        "mascotas": [
            {
                "id": str(mascota.id),
                "nombre": mascota.nombre,
                "especie": mascota.especie.value,
                "raza": mascota.raza,
                "edad_meses": mascota.calcular_edad_meses() if hasattr(mascota, 'calcular_edad_meses') else None
            }
            for mascota in mascotas
        ],
        "mascotaSaludo": {
            "nombre": mascota_saludo.nombre,
            "especie": mascota_saludo.especie.value
        } if mascota_saludo else None,
        "proximasCitas": [
            {
                "id": str(cita.id),
                "mascota_nombre": cita.mascota.nombre if cita.mascota else "Sin mascota",
                "fecha_hora": cita.fecha_hora.isoformat(),
                "servicio": cita.servicio.nombre if cita.servicio else "Sin servicio",
                "veterinario": cita.veterinario.nombre if cita.veterinario else "Sin veterinario",
                "estado": cita.estado.value
            }
            for cita in proximas_citas[:3]  # Máximo 3 próximas citas
        ]
    }


# ==================== ENDPOINTS ====================

@router.get("/stats", response_model=dict)
async def get_dashboard_stats(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene estadísticas del dashboard según el rol del usuario

    **Roles permitidos:** Todos los usuarios autenticados

    **Respuesta según rol:**
    - **Staff (superadmin, veterinario, auxiliar):** Estadísticas generales de citas, stock, notificaciones
    - **Propietario:** Información de sus mascotas y próximas citas

    **Retorna:**
    ```json
    // Para Staff:
    {
      "rol": "superadmin",
      "stats": {
        "citasDelDia": 1,
        "citasProgramadas": 5,
        "stockBajo": 2,
        "notificaciones": 0,
        "citasDetalle": [...],
        "alertasStock": [...]
      }
    }

    // Para Propietario:
    {
      "rol": "propietario",
      "stats": {
        "propietario": {...},
        "mascotas": [...],
        "mascotaSaludo": {...},
        "proximasCitas": [...]
      }
    }
    ```
    """
    try:
        user_role = current_user.rol

        # Determinar qué estadísticas devolver según el rol
        if user_role in [UserRole.SUPERADMIN, UserRole.VETERINARIO, UserRole.AUXILIAR]:
            stats = get_staff_dashboard_stats(db)
        elif user_role == UserRole.PROPIETARIO:
            stats = get_owner_dashboard_stats(db, current_user)
        else:
            stats = {}

        return success_response(
            data={
                "rol": user_role.value,
                "stats": stats
            },
            message="Estadísticas del dashboard obtenidas exitosamente"
        )

    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas del dashboard: {str(e)}"
        )