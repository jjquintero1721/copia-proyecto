"""
Controlador de Citas
RF-05: Gestión de citas (agendar, reprogramar, cancelar)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from datetime import datetime, date

from app.database import get_db
from app.services.appointment.appointment_service import AppointmentService
from app.services.appointment.appointment_facade import AppointmentFacade
from app.schemas.appointment_schema import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
    AppointmentStatusEnum,
    AppointmentPrivateResponse
)
from app.services.proxies import ProxyFactory, PermissionDeniedException, AuthProxy
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
from app.services.decorators import (
    RecordatorioDecorator,
    NotasEspecialesDecorator,
    PrioridadDecorator
)
from app.repositories.appointment_decorator_repository import (
    AppointmentDecoratorRepository
)
from app.models.appointment_decorator import DecoratorType
from app.schemas.appointment_decorator_schema import PrioridadCreate

router = APIRouter()

MSG_CITA_NO_ENCONTRADA = "Cita no encontrada"

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


@router.get(
    "/",
    response_model=Union[List[AppointmentResponse], List[AppointmentPrivateResponse]],
    summary="Listar citas",
    description="""
    Lista todas las citas con filtros opcionales.

    **Permisos:**
    - Superadmin, Veterinario, Auxiliar: Ven TODAS las citas con información completa  
    - Propietario: Ve TODAS las citas PERO con privacidad:  
      * Sus propias citas: información completa  
      * Citas de otros: solo información mínima ("Cita agendada")

    **Filtros disponibles:**
    - fecha: Filtrar por fecha específica  
    - veterinario_id: Filtrar por veterinario  
    - estado: Filtrar por estado (agendada, confirmada, etc.)  
    """
)
async def list_appointments(
        fecha: Optional[date] = Query(None, description="Fecha para filtrar citas"),
        veterinario_id: Optional[UUID] = Query(None, description="ID del veterinario"),
        estado: Optional[str] = Query(None, description="Estado de la cita"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Lista citas con privacidad según el rol del usuario.
    El AuthProxy se encarga de aplicar la lógica de acceso.
    """
    try:
        # Servicio base
        appointment_service = AppointmentService(db)

        # Proxy con lógica de autenticación/privacidad
        auth_proxy = AuthProxy(
            real_service=appointment_service,
            current_user=current_user
        )

        # El proxy ya filtra según rol y devuelve el tipo correcto de schema
        appointments = auth_proxy.get_appointments(
            fecha=fecha,
            veterinario_id=veterinario_id,
            estado=estado
        )

        return appointments

    except PermissionDeniedException as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc)
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar citas: {str(exc)}"
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
                "citas": [apt.to_dict_with_relations() for apt in appointments]
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


@router.post("/{appointment_id}/decoradores/recordatorio", response_model=dict)
async def add_recordatorio_decorator(
        appointment_id: UUID,
        recordatorios: List[Dict[str, Any]],
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """
    Añade decorador de recordatorios a una cita

    **Requiere**: Token JWT válido
    **Acceso**: Staff
    """
    try:
        appointment_service = AppointmentService(db)
        appointment = appointment_service.get_appointment_by_id(appointment_id)

        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MSG_CITA_NO_ENCONTRADA
            )

        # Crear y persistir decorador
        decorator = RecordatorioDecorator(
            appointment=appointment,
            recordatorios=recordatorios,
            db=db
        )

        decorator_model = decorator.persistir(creado_por=current_user.id)

        return success_response(
            data=decorator.get_detalles(),
            message="Recordatorios añadidos exitosamente"
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )


@router.post("/{appointment_id}/decoradores/notas", response_model=dict)
async def add_notas_decorator(
        appointment_id: UUID,
        notas: Dict[str, Any],
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """
    Añade decorador de notas especiales a una cita

    **Requiere**: Token JWT válido
    **Acceso**: Staff
    """
    try:
        appointment_service = AppointmentService(db)
        appointment = appointment_service.get_appointment_by_id(appointment_id)

        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MSG_CITA_NO_ENCONTRADA
            )

        decorator = NotasEspecialesDecorator(
            appointment=appointment,
            notas=notas,
            db=db
        )

        decorator_model = decorator.persistir(creado_por=current_user.id)

        return success_response(
            data=decorator.get_detalles(),
            message="Notas especiales añadidas exitosamente"
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )


@router.post("/{appointment_id}/decoradores/prioridad", response_model=dict)
async def add_prioridad_decorator(
        appointment_id: UUID,
        data: PrioridadCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """
    Añade decorador de prioridad a una cita

    **Requiere**: Token JWT válido
    **Acceso**: Staff
    """
    try:
        appointment_service = AppointmentService(db)
        appointment = appointment_service.get_appointment_by_id(appointment_id)

        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MSG_CITA_NO_ENCONTRADA
            )

        decorator = PrioridadDecorator(
            appointment=appointment,
            nivel_prioridad=data.nivel_prioridad,
            razon=data.razon,
            db=db
        )

        decorator_model = decorator.persistir(creado_por=current_user.id)

        return success_response(
            data=decorator.get_detalles(),
            message=f"Prioridad {data.nivel_prioridad} asignada exitosamente"
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )


@router.get("/{appointment_id}/decoradores", response_model=dict)
async def get_appointment_decorators(
        appointment_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """
    Obtiene todos los decoradores de una cita

    **Requiere**: Token JWT válido
    **Acceso**: Staff
    """
    try:
        from app.services.decorators import get_cita_con_decoradores

        appointment_service = AppointmentService(db)
        appointment = appointment_service.get_appointment_by_id(appointment_id)

        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MSG_CITA_NO_ENCONTRADA
            )

        cita_completa = get_cita_con_decoradores(appointment, db)

        return success_response(
            data=cita_completa,
            message="Decoradores obtenidos exitosamente"
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )


@router.delete("/{appointment_id}/decoradores/{decorator_id}", response_model=dict)
async def remove_decorator(
        appointment_id: UUID,
        decorator_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """
    Elimina un decorador de una cita

    **Requiere**: Token JWT válido
    **Acceso**: Staff
    """
    try:
        decorator_repo = AppointmentDecoratorRepository(db)

        success = decorator_repo.delete(decorator_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Decorador no encontrado"
            )

        return success_response(
            data={"decorator_id": str(decorator_id)},
            message="Decorador eliminado exitosamente"
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar decorador: {str(exc)}"
        )