"""
Interfaces para el Patrón Proxy
Define contratos que deben cumplir tanto servicios reales como proxies

Principio SOLID aplicado:
- Interface Segregation (I): Interfaces específicas y cohesivas
- Dependency Inversion (D): Dependemos de abstracciones, no de implementaciones concretas
"""

from typing import Protocol, Optional, List, TYPE_CHECKING
from datetime import datetime, date
from uuid import UUID

if TYPE_CHECKING:
    from app.models.appointment import Appointment, AppointmentStatus
    from app.schemas.appointment_schema import AppointmentCreate, AppointmentUpdate


class AppointmentServiceInterface(Protocol):
    """
    Interfaz que define el contrato para servicios de citas

    Permite que tanto AppointmentService como sus Proxies
    implementen la misma interfaz, facilitando la sustitución (Liskov Substitution)
    """

    def create_appointment(
            self,
            appointment_data: 'AppointmentCreate',
            creado_por: Optional[UUID] = None
    ) -> 'Appointment':
        """Crea una nueva cita"""
        ...

    def get_appointment_by_id(self, appointment_id: UUID) -> Optional['Appointment']:
        """Obtiene una cita por ID"""
        ...

    def get_all_appointments(
            self,
            skip: int = 0,
            limit: int = 100,
            estado: Optional['AppointmentStatus'] = None,
            mascota_id: Optional[UUID] = None,
            veterinario_id: Optional[UUID] = None,
            fecha_desde: Optional[datetime] = None,
            fecha_hasta: Optional[datetime] = None
    ) -> List['Appointment']:
        """Obtiene todas las citas con filtros opcionales"""
        ...

    def get_appointments_by_date(
            self,
            fecha: date,
            veterinario_id: Optional[UUID] = None
    ) -> List['Appointment']:
        """Obtiene citas de una fecha específica"""
        ...

    def reschedule_appointment(
            self,
            appointment_id: UUID,
            nueva_fecha: datetime,
            usuario_id: Optional[UUID] = None
    ) -> 'Appointment':
        """Reprograma una cita"""
        ...

    def cancel_appointment(
            self,
            appointment_id: UUID,
            motivo_cancelacion: str,
            usuario_id: Optional[UUID] = None
    ) -> 'Appointment':
        """Cancela una cita"""
        ...