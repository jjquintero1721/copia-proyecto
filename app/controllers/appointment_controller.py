"""
Controlador de Citas
RF-05: Gestión de citas (agendar, reprogramar, cancelar)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime, date

from app.database import get_db
from app.services.appointment.appointment_service import AppointmentService
from app.services.appointment.appointment_facade import AppointmentFacade
from app.schemas.appointment_schema import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
    AppointmentStatusEnum
)
from app.services.proxies import ProxyFactory, PermissionDeniedException
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
    """
    try:
        # PROXY
        appointment_service = ProxyFactory.create_appointment_service_with_cache_and_auth(
            db=db,
            current_user=current_user
        )

        status_filter = AppointmentStatus(estado.value) if estado else None

        appointments = appointment_service.get_all_appointments(
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

    except PermissionDeniedException as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener citas: {str(exc)}"
        )


@router.get("/date/{fecha}", response_model=dict)
async def get_appointments_by_date(
        fecha: date,
        veterinario_id: Optional[UUID] = Query(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    try:
        appointment_service = ProxyFactory.create_appointment_service_with_cache_and_auth(
            db=db,
            current_user=current_user
        )

        appointments = appointment_service.get_appointments_by_date(
            fecha, veterinario_id
        )

        return success_response(
            data={
                "total": len(appointments),
                "citas": [apt.to_dict() for apt in appointments]
            },
            message="Citas obtenidas exitosamente"
        )

    except PermissionDeniedException as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener citas: {str(exc)}"
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
    try:
        # PROXY reemplaza AppointmentService
        appointment_service = ProxyFactory.create_appointment_service_with_cache_and_auth(
            db=db,
            current_user=current_user
        )

        appointment = appointment_service.start_appointment(
            appointment_id,
            current_user.id
        )

        return success_response(
            data=appointment.to_dict(),
            message="Cita iniciada exitosamente"
        )

    except PermissionDeniedException as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc)
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
    try:
        appointment_service = ProxyFactory.create_appointment_service_with_cache_and_auth(
            db=db,
            current_user=current_user
        )

        appointment = appointment_service.complete_appointment(
            appointment_id,
            notas,
            current_user.id
        )

        return success_response(
            data=appointment.to_dict(),
            message="Cita completada exitosamente"
        )

    except PermissionDeniedException as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc)
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
    Obtiene la disponibilidad de un veterinario
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