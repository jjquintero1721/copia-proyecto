"""
Comandos de Citas - Patrón Command
RF-05: Gestión de citas
RNF-07: Auditoría de acciones

VERSIÓN CORREGIDA - Con integración correcta del Observer Pattern
"""

from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timezone

from app.models.appointment import Appointment
from app.services.appointment.appointment_facade import AppointmentFacade


class AppointmentCommand(ABC):
    """
    Comando abstracto para operaciones de citas
    Patrón Command: Encapsula una operación como un objeto
    """

    @abstractmethod
    def execute(self) -> Dict[str, Any]:
        """Ejecuta el comando y retorna el resultado"""
        pass

    def registrar_auditoria(self, appointment: Appointment) -> None:
        """Registra la acción en auditoría"""
        # Implementar registro de auditoría
        pass


class CreateAppointmentCommand(AppointmentCommand):
    """
    Comando para crear una nueva cita
    Integra: Facade, Observer, Auditoría
    """

    def __init__(
        self,
        db: Session,
        mascota_id: UUID,
        veterinario_id: UUID,
        servicio_id: UUID,
        fecha_hora: datetime,
        motivo: str,
        usuario_id: UUID
    ):
        self.db = db
        self.mascota_id = mascota_id
        self.veterinario_id = veterinario_id
        self.servicio_id = servicio_id
        self.fecha_hora = fecha_hora
        self.motivo = motivo
        self.usuario_id = usuario_id
        self.facade = AppointmentFacade(db)

    def execute(self) -> Dict[str, Any]:
        """
        Ejecuta la creación de la cita

        Returns:
            Dict con los datos de la cita creada

        Raises:
            ValueError: Si hay error de validación
            Exception: Si hay error en la creación
        """
        try:
            # 1. Crear cita usando Facade Pattern
            appointment = self.facade.schedule_appointment(
                mascota_id=self.mascota_id,
                veterinario_id=self.veterinario_id,
                servicio_id=self.servicio_id,
                fecha_hora=self.fecha_hora,
                motivo=self.motivo,
                creado_por=self.usuario_id
            )

            # 2. Notificar a observers (Observer Pattern)
            # ✅ CORRECCIÓN: Importar y usar correctamente
            from app.services.appointment.observers import get_gestor_citas

            gestor = get_gestor_citas(self.db)  # ✅ Pasar sesión de BD

            # ✅ CORRECCIÓN: Datos en diccionario, no como kwargs
            gestor.notificar(
                "CITA_CREADA",
                appointment,
                {
                    "usuario_id": self.usuario_id,
                    "accion": "crear_cita",
                    "fecha": appointment.fecha_hora,
                    "mascota_id": self.mascota_id
                }
            )

            # 3. Registrar auditoría (Command Pattern)
            self.registrar_auditoria(appointment)

            # 4. Retornar resultado
            return {
                "id": str(appointment.id),
                "mascota_id": str(appointment.mascota_id),
                "veterinario_id": str(appointment.veterinario_id),
                "servicio_id": str(appointment.servicio_id),
                "fecha_hora": appointment.fecha_hora.isoformat(),
                "estado": appointment.estado.value,
                "motivo": appointment.motivo,
                "cancelacion_tardia": appointment.cancelacion_tardia,
                "fecha_creacion": appointment.fecha_creacion.isoformat()
            }

        except ValueError as val_error:
            # Re-lanzar errores de validación
            raise val_error
        except Exception as error:
            # Capturar y propagar otros errores
            raise Exception(f"Error al agendar cita: {str(error)}")


class RescheduleAppointmentCommand(AppointmentCommand):
    """
    Comando para reprogramar una cita
    RN08-3: Solo hasta 2 horas antes
    """

    def __init__(
        self,
        db: Session,
        appointment_id: UUID,
        nueva_fecha: datetime,
        usuario_id: UUID
    ):
        self.db = db
        self.appointment_id = appointment_id
        self.nueva_fecha = nueva_fecha
        self.usuario_id = usuario_id
        self.facade = AppointmentFacade(db)

    def execute(self) -> Dict[str, Any]:
        """
        Ejecuta la reprogramación de la cita

        Returns:
            Dict con los datos de la cita reprogramada

        Raises:
            ValueError: Si no se puede reprogramar
        """
        try:
            # 1. Obtener fecha anterior para notificación
            appointment_anterior = self.facade.service.get_appointment_by_id(
                self.appointment_id
            )

            if not appointment_anterior:
                raise ValueError("Cita no encontrada")

            fecha_anterior = appointment_anterior.fecha_hora

            # 2. Reprogramar usando Facade
            appointment = self.facade.reschedule_appointment(
                appointment_id=self.appointment_id,
                nueva_fecha=self.nueva_fecha,
                usuario_id=self.usuario_id
            )

            # 3. Notificar a observers
            # ✅ CORRECCIÓN: Usar correctamente
            from app.services.appointment.observers import get_gestor_citas

            gestor = get_gestor_citas(self.db)

            gestor.notificar(
                "CITA_REPROGRAMADA",
                appointment,
                {
                    "usuario_id": self.usuario_id,
                    "fecha_anterior": fecha_anterior,
                    "fecha_nueva": appointment.fecha_hora,
                    "accion": "reprogramar_cita"
                }
            )

            # 4. Registrar auditoría
            self.registrar_auditoria(appointment)

            # 5. Retornar resultado
            return {
                "id": str(appointment.id),
                "fecha_hora": appointment.fecha_hora.isoformat(),
                "estado": appointment.estado.value,
                "fecha_anterior": fecha_anterior.isoformat()
            }

        except ValueError as val_error:
            raise val_error
        except Exception as error:
            raise Exception(f"Error al reprogramar cita: {str(error)}")


class CancelAppointmentCommand(AppointmentCommand):
    """
    Comando para cancelar una cita
    RN08-2: Cancelación tardía si es <4h antes
    """

    def __init__(
        self,
        db: Session,
        appointment_id: UUID,
        usuario_id: UUID,
        motivo_cancelacion: Optional[str] = None
    ):
        self.db = db
        self.appointment_id = appointment_id
        self.usuario_id = usuario_id
        self.motivo_cancelacion = motivo_cancelacion
        self.facade = AppointmentFacade(db)

    def execute(self) -> Dict[str, Any]:
        """
        Ejecuta la cancelación de la cita

        Returns:
            Dict con los datos de la cita cancelada
        """
        try:
            # 1. Cancelar usando Facade
            appointment = self.facade.cancel_appointment(
                appointment_id=self.appointment_id,
                usuario_id=self.usuario_id
            )

            # 2. Notificar a observers
            # ✅ CORRECCIÓN: Usar correctamente
            from app.services.appointment.observers import get_gestor_citas

            gestor = get_gestor_citas(self.db)

            gestor.notificar(
                "CITA_CANCELADA",
                appointment,
                {
                    "usuario_id": self.usuario_id,
                    "motivo_cancelacion": self.motivo_cancelacion,
                    "cancelacion_tardia": appointment.cancelacion_tardia,
                    "accion": "cancelar_cita",
                    "fecha_cita": appointment.fecha_hora
                }
            )

            # 3. Registrar auditoría
            self.registrar_auditoria(appointment)

            # 4. Retornar resultado
            return {
                "id": str(appointment.id),
                "estado": appointment.estado.value,
                "cancelacion_tardia": appointment.cancelacion_tardia,
                "mensaje": (
                    "Cita cancelada (cancelación tardía)"
                    if appointment.cancelacion_tardia
                    else "Cita cancelada exitosamente"
                )
            }

        except ValueError as val_error:
            raise val_error
        except Exception as error:
            raise Exception(f"Error al cancelar cita: {str(error)}")


class ConfirmAppointmentCommand(AppointmentCommand):
    """
    Comando para confirmar una cita
    Estado: AGENDADA → CONFIRMADA
    """

    def __init__(
        self,
        db: Session,
        appointment_id: UUID,
        usuario_id: UUID
    ):
        self.db = db
        self.appointment_id = appointment_id
        self.usuario_id = usuario_id
        self.facade = AppointmentFacade(db)

    def execute(self) -> Dict[str, Any]:
        """
        Ejecuta la confirmación de la cita

        Returns:
            Dict con los datos de la cita confirmada
        """
        try:
            # 1. Confirmar usando Facade
            appointment = self.facade.confirm_appointment(
                appointment_id=self.appointment_id,
                usuario_id=self.usuario_id
            )

            # 2. Registrar auditoría
            self.registrar_auditoria(appointment)

            # 3. Retornar resultado
            return {
                "id": str(appointment.id),
                "estado": appointment.estado.value,
                "mensaje": "Cita confirmada exitosamente"
            }

        except ValueError as val_error:
            raise val_error
        except Exception as error:
            raise Exception(f"Error al confirmar cita: {str(error)}")


class CompleteAppointmentCommand(AppointmentCommand):
    """
    Comando para completar una cita
    Estado: EN_PROCESO → COMPLETADA
    """

    def __init__(
        self,
        db: Session,
        appointment_id: UUID,
        usuario_id: UUID,
        notas: Optional[str] = None
    ):
        self.db = db
        self.appointment_id = appointment_id
        self.usuario_id = usuario_id
        self.notas = notas
        self.facade = AppointmentFacade(db)

    def execute(self) -> Dict[str, Any]:
        """
        Ejecuta la finalización de la cita

        Returns:
            Dict con los datos de la cita completada
        """
        try:
            # 1. Completar usando Facade
            appointment = self.facade.complete_appointment(
                appointment_id=self.appointment_id,
                usuario_id=self.usuario_id
            )

            # 2. Actualizar notas si se proporcionaron
            if self.notas:
                appointment.notas = self.notas
                self.db.commit()
                self.db.refresh(appointment)

            # 3. Registrar auditoría
            self.registrar_auditoria(appointment)

            # 4. Retornar resultado
            return {
                "id": str(appointment.id),
                "estado": appointment.estado.value,
                "notas": appointment.notas,
                "mensaje": "Cita completada exitosamente"
            }

        except ValueError as val_error:
            raise val_error
        except Exception as error:
            raise Exception(f"Error al completar cita: {str(error)}")


class InitiateAppointmentCommand(AppointmentCommand):
    """
    Comando para iniciar una cita
    Estado: CONFIRMADA → EN_PROCESO
    """

    def __init__(
        self,
        db: Session,
        appointment_id: UUID,
        usuario_id: UUID
    ):
        self.db = db
        self.appointment_id = appointment_id
        self.usuario_id = usuario_id
        self.facade = AppointmentFacade(db)

    def execute(self) -> Dict[str, Any]:
        """
        Ejecuta el inicio de la cita

        Returns:
            Dict con los datos de la cita iniciada
        """
        try:
            # 1. Iniciar usando Facade
            appointment = self.facade.initiate_appointment(
                appointment_id=self.appointment_id,
                usuario_id=self.usuario_id
            )

            # 2. Registrar auditoría
            self.registrar_auditoria(appointment)

            # 3. Retornar resultado
            return {
                "id": str(appointment.id),
                "estado": appointment.estado.value,
                "mensaje": "Cita iniciada exitosamente"
            }

        except ValueError as val_error:
            raise val_error
        except Exception as error:
            raise Exception(f"Error al iniciar cita: {str(error)}")