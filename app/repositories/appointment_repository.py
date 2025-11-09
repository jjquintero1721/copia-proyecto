"""
Repositorio de Citas - Capa de acceso a datos
RF-05: Gestión de citas
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta, timezone

from app.models.appointment import Appointment, AppointmentStatus


class AppointmentRepository:
    """
    Repositorio para operaciones de base de datos sobre citas
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, appointment: Appointment) -> Appointment:
        """Crea una nueva cita"""
        self.db.add(appointment)
        self.db.commit()
        self.db.refresh(appointment)
        return appointment

    def get_by_id(self, appointment_id: UUID) -> Optional[Appointment]:
        """Obtiene una cita por ID"""
        return self.db.query(Appointment).filter(Appointment.id == appointment_id).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        estado: Optional[AppointmentStatus] = None,
        mascota_id: Optional[UUID] = None,
        veterinario_id: Optional[UUID] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None
    ) -> List[Appointment]:
        """Obtiene todas las citas con filtros opcionales"""
        query = self.db.query(Appointment)

        if estado:
            query = query.filter(Appointment.estado == estado)

        if mascota_id:
            query = query.filter(Appointment.mascota_id == mascota_id)

        if veterinario_id:
            query = query.filter(Appointment.veterinario_id == veterinario_id)

        if fecha_desde:
            query = query.filter(Appointment.fecha_hora >= fecha_desde)

        if fecha_hasta:
            query = query.filter(Appointment.fecha_hora <= fecha_hasta)

        return query.order_by(Appointment.fecha_hora).offset(skip).limit(limit).all()

    def get_by_date_range(
        self,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        veterinario_id: Optional[UUID] = None
    ) -> List[Appointment]:
        """
        Obtiene citas en un rango de fechas
        Útil para validar disponibilidad de horarios
        """
        query = self.db.query(Appointment).filter(
            and_(
                Appointment.fecha_hora >= fecha_inicio,
                Appointment.fecha_hora <= fecha_fin,
                Appointment.estado.in_([
                    AppointmentStatus.AGENDADA,
                    AppointmentStatus.CONFIRMADA,
                    AppointmentStatus.EN_PROCESO
                ])
            )
        )

        if veterinario_id:
            query = query.filter(Appointment.veterinario_id == veterinario_id)

        return query.all()

    def check_availability(
        self,
        veterinario_id: UUID,
        fecha_hora: datetime,
        duracion_minutos: int,
        exclude_appointment_id: Optional[UUID] = None
    ) -> bool:
        """
        Verifica si un horario está disponible para un veterinario
        RN08: Validación de horarios ocupados
        """
        fecha_fin = fecha_hora + timedelta(minutes=duracion_minutos)

        query = self.db.query(Appointment).filter(
            and_(
                Appointment.veterinario_id == veterinario_id,
                Appointment.estado.in_([
                    AppointmentStatus.AGENDADA,
                    AppointmentStatus.CONFIRMADA,
                    AppointmentStatus.EN_PROCESO
                ]),
                or_(
                    # La nueva cita empieza durante una cita existente
                    and_(
                        Appointment.fecha_hora <= fecha_hora,
                        Appointment.fecha_hora > fecha_hora - timedelta(minutes=duracion_minutos)
                    ),
                    # La nueva cita termina durante una cita existente
                    and_(
                        Appointment.fecha_hora >= fecha_hora,
                        Appointment.fecha_hora < fecha_fin
                    )
                )
            )
        )

        if exclude_appointment_id:
            query = query.filter(Appointment.id != exclude_appointment_id)

        conflicting = query.first()
        return conflicting is None

    def update(self, appointment: Appointment) -> Appointment:
        """Actualiza una cita existente"""
        self.db.commit()
        self.db.refresh(appointment)
        return appointment

    def get_upcoming_appointments(
        self,
        hours_ahead: int = 24,
        skip: int = 0,
        limit: int = 100
    ) -> List[Appointment]:
        """
        Obtiene citas próximas para recordatorios
        RF-06: Notificaciones por correo
        """
        now = datetime.now(timezone.utc)
        target_time = now + timedelta(hours=hours_ahead)

        return self.db.query(Appointment).filter(
            and_(
                Appointment.fecha_hora >= now,
                Appointment.fecha_hora <= target_time,
                Appointment.estado.in_([
                    AppointmentStatus.AGENDADA,
                    AppointmentStatus.CONFIRMADA
                ])
            )
        ).offset(skip).limit(limit).all()

    def count_by_status(self, estado: AppointmentStatus) -> int:
        """Cuenta citas por estado"""
        return self.db.query(Appointment).filter(Appointment.estado == estado).count()

    def count_by_date_range(self, fecha_inicio: datetime, fecha_fin: datetime) -> int:
        """Cuenta citas en un rango de fechas"""
        return self.db.query(Appointment).filter(
            and_(
                Appointment.fecha_hora >= fecha_inicio,
                Appointment.fecha_hora <= fecha_fin
            )
        ).count()