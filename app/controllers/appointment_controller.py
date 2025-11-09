"""
Controlador de Citas
RF-05: Gestión de citas (agendar, reprogramar, cancelar)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.database import get_db
from app.services.appointment.appointment_service import AppointmentService
from app.services.appointment.appointment_facade import AppointmentFacade
from app.schemas.appointment_schema import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
    AppointmentStatusEnum
)
from app.models.user import User
from app.models.appointment import AppointmentStatus
from app.security.dependencies import (
    get_current_active_user,
    require_staff
)
from app.utils.responses import success_response
from app.commands.appointment_commands import (
    CreateAppointmentCommand,
    RescheduleAppointmentCommand,
    CancelAppointmentCommand,
    ConfirmAppointmentCommand
)

router = APIRouter()


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_appointment(
        appointment_data: AppointmentCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """
    Agenda una nueva cita

    **Requiere:** Token JWT válido
    **Acceso:** Staff (Superadmin, Veterinario, Auxiliar)

    **RF-05:** Gestión de citas
    **RN08-1:** Anticipación mínima de 4 horas

    **Validaciones:**
    - Mascota, veterinario y servicio deben existir
    - Anticipación mínima de 4 horas
    - Veterinario debe estar disponible en el horario
    """
    try:
        cmd = CreateAppointmentCommand(
            db=db,
            mascota_id=appointment_data.mascota_id,
            veterinario_id=appointment_data.veterinario_id,
            servicio_id=appointment_data.servicio_id,
            fecha_hora=appointment_data.fecha_hora,
            motivo=appointment_data.motivo,
            usuario_id=current_user.id
        )

        result = cmd.execute()

        return success_response(
            data=result,
            message="Cita agendada exitosamente",
            status_code=status.HTTP_201_CREATED
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al agendar cita: {str(exc)}"
        )


@router.get("/", response_model=dict)
async def list_appointments(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        estado: Optional[AppointmentStatusEnum] = None,
        mascota_id: Optional[UUID] = None,
        veterinario_id: Optional[UUID] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Lista todas las citas con filtros opcionales

    **Requiere:** Token JWT válido
    **Acceso:**
    - Staff: Puede ver todas las citas
    - Propietario: Solo puede ver citas de sus mascotas (implementar filtro)

    **Filtros:**
    - estado: Estado de la cita
    - mascota_id: ID de la mascota
    - veterinario_id: ID del veterinario
    - fecha_desde: Desde fecha
    - fecha_hasta: Hasta fecha
    """
    try:
        service = AppointmentService(db)

        # Convertir enum a AppointmentStatus si está presente
        status_filter = AppointmentStatus(estado.value) if estado else None

        appointments = service.get_all_appointments(
            skip=skip,
            limit=limit,
            estado=status_filter,
            mascota_id=mascota_id,
            veterinario_id=veterinario_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta
        )

        return success_response(
            data={
                "total": len(appointments),
                "citas": [a.to_dict() for a in appointments]
            },
            message="Lista de citas"
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener citas: {str(exc)}"
        )


@router.get("/{appointment_id}", response_model=dict)
async def get_appointment(
        appointment_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene una cita por ID

    **Requiere:** Token JWT válido
    **Acceso:** Usuario autenticado (con validación de permisos)
    """
    try:
        service = AppointmentService(db)
        appointment = service.get_appointment_by_id(appointment_id)

        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cita no encontrada"
            )

        return success_response(
            data=appointment.to_dict(),
            message="Cita encontrada"
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener cita: {str(exc)}"
        )


@router.put("/{appointment_id}/reschedule", response_model=dict)
async def reschedule_appointment(
        appointment_id: UUID,
        update_data: AppointmentUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """
    Reprograma una cita existente

    **Requiere:** Token JWT válido
    **Acceso:** Staff (Superadmin, Veterinario, Auxiliar)

    **RN08-3:** Reprogramaciones solo hasta 2 horas antes

    **Validaciones:**
    - Anticipación mínima de 2 horas
    - Nuevo horario debe estar disponible
    - Solo citas AGENDADAS o CONFIRMADAS pueden reprogramarse
    """
    try:
        cmd = RescheduleAppointmentCommand(
            db=db,
            appointment_id=appointment_id,
            nueva_fecha=update_data.fecha_hora,
            usuario_id=current_user.id
        )

        result = cmd.execute()

        return success_response(
            data=result,
            message="Cita reprogramada exitosamente"
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al reprogramar cita: {str(exc)}"
        )


@router.post("/{appointment_id}/confirm", response_model=dict)
async def confirm_appointment(
        appointment_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """
    Confirma una cita

    **Requiere:** Token JWT válido
    **Acceso:** Staff (Superadmin, Veterinario, Auxiliar)

    **Transición:** AGENDADA → CONFIRMADA
    """
    try:
        cmd = ConfirmAppointmentCommand(
            db=db,
            appointment_id=appointment_id,
            usuario_id=current_user.id
        )

        result = cmd.execute()

        return success_response(
            data=result,
            message="Cita confirmada exitosamente"
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al confirmar cita: {str(exc)}"
        )


@router.delete("/{appointment_id}", response_model=dict)
async def cancel_appointment(
        appointment_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """
    Cancela una cita

    **Requiere:** Token JWT válido
    **Acceso:** Staff (Superadmin, Veterinario, Auxiliar)

    **RN08-2:** Cancelaciones con menos de 4 horas se registran como tardías

    **Transiciones permitidas:** AGENDADA/CONFIRMADA → CANCELADA
    """
    try:
        cmd = CancelAppointmentCommand(
            db=db,
            appointment_id=appointment_id,
            usuario_id=current_user.id
        )

        result = cmd.execute()

        return success_response(
            data=result,
            message=result["mensaje"]
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cancelar cita: {str(exc)}"
        )


@router.post("/{appointment_id}/start", response_model=dict)
async def start_appointment(
        appointment_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """
    Inicia una cita (cambiar a estado EN_PROCESO)

    **Requiere:** Token JWT válido
    **Acceso:** Staff (Superadmin, Veterinario, Auxiliar)

    **Transición:** CONFIRMADA → EN_PROCESO
    """
    try:
        service = AppointmentService(db)
        appointment = service.start_appointment(appointment_id, current_user.id)

        return success_response(
            data=appointment.to_dict(),
            message="Cita iniciada exitosamente"
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al iniciar cita: {str(exc)}"
        )


@router.post("/{appointment_id}/complete", response_model=dict)
async def complete_appointment(
        appointment_id: UUID,
        notas: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """
    Completa una cita (cambiar a estado COMPLETADA)

    **Requiere:** Token JWT válido
    **Acceso:** Staff (Superadmin, Veterinario, Auxiliar)

    **Transición:** EN_PROCESO → COMPLETADA
    """
    try:
        service = AppointmentService(db)
        appointment = service.complete_appointment(
            appointment_id,
            notas,
            current_user.id
        )

        return success_response(
            data=appointment.to_dict(),
            message="Cita completada exitosamente"
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al completar cita: {str(exc)}"
        )


@router.get("/availability/{veterinario_id}", response_model=dict)
async def get_veterinarian_availability(
        veterinario_id: UUID,
        fecha: datetime,
        duracion_minutos: int = Query(30, gt=0, le=480),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene la disponibilidad de un veterinario en una fecha específica

    **Requiere:** Token JWT válido
    **Acceso:** Cualquier usuario autenticado

    **Parámetros:**
    - veterinario_id: ID del veterinario
    - fecha: Fecha a consultar
    - duracion_minutos: Duración estimada de la cita (default: 30 min)

    **Retorna:** Horarios disponibles en intervalos de 30 minutos
    """
    try:
        facade = AppointmentFacade(db)
        result = facade.obtener_disponibilidad_veterinario(
            veterinario_id,
            fecha,
            duracion_minutos
        )

        return success_response(
            data=result,
            message="Disponibilidad del veterinario"
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener disponibilidad: {str(exc)}"
        )