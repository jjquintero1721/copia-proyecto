"""
AuthProxy - Patrón Proxy para Autorización
Control de acceso avanzado basado en roles y permisos

Relaciona con: RF-02, RF-03, RN03, RN04, RN05, RNF-01, RNF-07

Principios SOLID aplicados:
- Single Responsibility: Solo maneja autorización
- Open/Closed: Extensible mediante nuevas políticas de permisos
- Dependency Inversion: Depende de abstracciones
"""

import logging
from typing import Optional, List, Any, Callable
from datetime import datetime, date, timezone
from uuid import UUID
from functools import wraps

from app.models.appointment import Appointment, AppointmentStatus
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


class PermissionDeniedException(Exception):
    """Excepción personalizada para permisos denegados"""
    pass


class AuthProxy:
    """
    Proxy que añade control de acceso al servicio de citas

    Verifica permisos antes de ejecutar operaciones según:
    - RN03: Solo Superadmin puede crear usuarios
    - RN04: Veterinarios y Auxiliares no pueden crear usuarios
    - RN05: Control de acceso por roles

    Evita antipatrón: God Object (delegación clara de responsabilidades)
    """

    # Definición de permisos por operación (evita hardcoding en lógica)
    PERMISSIONS = {
        'create_appointment': [UserRole.SUPERADMIN, UserRole.VETERINARIO, UserRole.AUXILIAR, UserRole.PROPIETARIO],
        'view_appointment': [UserRole.SUPERADMIN, UserRole.VETERINARIO, UserRole.AUXILIAR, UserRole.PROPIETARIO],
        'view_all_appointments': [UserRole.SUPERADMIN, UserRole.VETERINARIO, UserRole.AUXILIAR],
        'reschedule_appointment': [UserRole.SUPERADMIN, UserRole.VETERINARIO, UserRole.AUXILIAR, UserRole.PROPIETARIO],
        'cancel_appointment': [UserRole.SUPERADMIN, UserRole.VETERINARIO, UserRole.AUXILIAR, UserRole.PROPIETARIO],
    }

    def __init__(
            self,
            real_service: Any,
            current_user: User,
            audit_callback: Optional[Callable] = None
    ):
        """
        Inicializa el proxies de autorización

        Args:
            real_service: Servicio real de citas (AppointmentService o CacheProxy)
            current_user: Usuario que ejecuta la operación
            audit_callback: Función opcional para auditoría
        """
        self._real_service = real_service
        self._current_user = current_user
        self._audit = audit_callback

        logger.info(f"AuthProxy inicializado para usuario {current_user.correo} ({current_user.rol.value})")

    def create_appointment(
            self,
            appointment_data: Any,
            creado_por: Optional[UUID] = None
    ) -> Appointment:
        """
        Crea una cita verificando permisos

        Reglas:
        - Todos los usuarios autenticados pueden agendar citas
        - Clientes solo pueden agendar para sus propias mascotas
        """
        self._verify_permission('create_appointment')

        # Si es cliente, validar que la mascota le pertenece
        if self._current_user.rol == UserRole.PROPIETARIO:
            self._verify_pet_ownership(appointment_data.mascota_id)

        # Auditar acción
        self._log_action('create_appointment', {
            'mascota_id': str(appointment_data.mascota_id),
            'fecha_hora': appointment_data.fecha_hora.isoformat()
        })

        # Establecer creado_por como usuario actual si no se especifica
        if creado_por is None:
            creado_por = self._current_user.id

        # Delegar al servicio real
        return self._real_service.create_appointment(appointment_data, creado_por)

    def get_appointment_by_id(self, appointment_id: UUID) -> Optional[Appointment]:
        """
        Obtiene una cita verificando permisos

        Reglas:
        - Staff puede ver todas las citas
        - Clientes solo pueden ver sus propias citas
        """
        self._verify_permission('view_appointment')

        # Obtener la cita
        appointment = self._real_service.get_appointment_by_id(appointment_id)

        if appointment is None:
            return None

        # Si es cliente, verificar que la mascota le pertenece
        if self._current_user.rol == UserRole.PROPIETARIO:
            self._verify_appointment_ownership(appointment)

        return appointment

    def get_all_appointments(self, **kwargs) -> List[Appointment]:
        """
        Obtiene todas las citas aplicando filtros según rol

        Reglas:
        - Staff puede ver todas las citas
        - Clientes solo ven citas de sus mascotas
        """
        self._verify_permission('view_all_appointments')

        # Si es cliente, agregar filtro por propietario
        if self._current_user.rol == UserRole.PROPIETARIO:
            # Obtener IDs de mascotas del cliente
            pet_ids = self._get_user_pet_ids()

            # Si no tiene mascotas, retornar lista vacía
            if not pet_ids:
                return []

            # Agregar filtro (solo si no se especificó mascota_id)
            if 'mascota_id' not in kwargs or kwargs['mascota_id'] is None:
                # Filtrar para obtener solo citas de las mascotas del cliente
                all_appointments = self._real_service.get_all_appointments(**kwargs)
                return [apt for apt in all_appointments if apt.mascota_id in pet_ids]

        # Staff puede ver todas
        return self._real_service.get_all_appointments(**kwargs)

    def get_appointments_by_date(
            self,
            fecha: date,
            veterinario_id: Optional[UUID] = None
    ) -> List[Appointment]:
        """
        Obtiene citas por fecha verificando permisos

        Reglas:
        - Staff puede ver citas de cualquier fecha/veterinario
        - Clientes solo ven sus propias citas
        """
        self._verify_permission('view_all_appointments')

        # Obtener citas
        appointments = self._real_service.get_appointments_by_date(fecha, veterinario_id)

        # Si es cliente, filtrar solo sus citas
        if self._current_user.rol == UserRole.PROPIETARIO:
            pet_ids = self._get_user_pet_ids()
            appointments = [apt for apt in appointments if apt.mascota_id in pet_ids]

        return appointments

    def reschedule_appointment(
            self,
            appointment_id: UUID,
            nueva_fecha: datetime,
            usuario_id: Optional[UUID] = None
    ) -> Appointment:
        """
        Reprograma una cita verificando permisos

        Reglas:
        - Staff puede reprogramar cualquier cita
        - Clientes solo pueden reprogramar sus propias citas
        - RN08-3: Reprogramaciones hasta 2 horas antes (validado en servicio)
        """
        self._verify_permission('reschedule_appointment')

        # Verificar propiedad si es cliente
        if self._current_user.rol == UserRole.PROPIETARIO:
            appointment = self._real_service.get_appointment_by_id(appointment_id)
            if appointment:
                self._verify_appointment_ownership(appointment)

        # Auditar acción
        self._log_action('reschedule_appointment', {
            'appointment_id': str(appointment_id),
            'nueva_fecha': nueva_fecha.isoformat()
        })

        # Establecer usuario_id como usuario actual si no se especifica
        if usuario_id is None:
            usuario_id = self._current_user.id

        # Delegar al servicio real
        return self._real_service.reschedule_appointment(
            appointment_id, nueva_fecha, usuario_id
        )

    def cancel_appointment(
            self,
            appointment_id: UUID,
            motivo_cancelacion: str,
            usuario_id: Optional[UUID] = None
    ) -> Appointment:
        """
        Cancela una cita verificando permisos

        Reglas:
        - Staff puede cancelar cualquier cita
        - Clientes solo pueden cancelar sus propias citas
        """
        self._verify_permission('cancel_appointment')

        # Verificar propiedad si es cliente
        if self._current_user.rol == UserRole.PROPIETARIO:
            appointment = self._real_service.get_appointment_by_id(appointment_id)
            if appointment:
                self._verify_appointment_ownership(appointment)

        # Auditar acción
        self._log_action('cancel_appointment', {
            'appointment_id': str(appointment_id),
            'motivo': motivo_cancelacion
        })

        # Establecer usuario_id como usuario actual si no se especifica
        if usuario_id is None:
            usuario_id = self._current_user.id

        # Delegar al servicio real
        return self._real_service.cancel_appointment(
            appointment_id, motivo_cancelacion, usuario_id
        )

    # ==================== MÉTODOS PRIVADOS DE AUTORIZACIÓN ====================

    def _verify_permission(self, operation: str):
        """
        Verifica que el usuario tenga permiso para la operación

        Args:
            operation: Nombre de la operación

        Raises:
            PermissionDeniedException: Si el usuario no tiene permiso
        """
        allowed_roles = self.PERMISSIONS.get(operation, [])

        if self._current_user.rol not in allowed_roles:
            logger.warning(
                f"Permiso denegado: {self._current_user.correo} "
                f"intentó {operation} sin permisos"
            )
            raise PermissionDeniedException(
                f"No tiene permisos para realizar esta operación: {operation}"
            )

    def _verify_pet_ownership(self, mascota_id: UUID):
        """
        Verifica que la mascota pertenezca al usuario actual

        Args:
            mascota_id: ID de la mascota

        Raises:
            PermissionDeniedException: Si la mascota no pertenece al usuario
        """
        # Obtener mascota del servicio real
        pet_ids = self._get_user_pet_ids()

        if mascota_id not in pet_ids:
            logger.warning(
                f"Acceso denegado: {self._current_user.correo} "
                f"intentó acceder a mascota {mascota_id} que no le pertenece"
            )
            raise PermissionDeniedException(
                "No tiene permisos para acceder a esta mascota"
            )

    def _verify_appointment_ownership(self, appointment: Appointment):
        """
        Verifica que la cita pertenezca al usuario actual

        Args:
            appointment: Cita a verificar

        Raises:
            PermissionDeniedException: Si la cita no pertenece al usuario
        """
        pet_ids = self._get_user_pet_ids()

        if appointment.mascota_id not in pet_ids:
            logger.warning(
                f"Acceso denegado: {self._current_user.correo} "
                f"intentó acceder a cita {appointment.id} que no le pertenece"
            )
            raise PermissionDeniedException(
                "No tiene permisos para acceder a esta cita"
            )

    def _get_user_pet_ids(self) -> List[UUID]:
        """
        Obtiene los IDs de las mascotas del usuario actual

        Returns:
            Lista de UUIDs de mascotas del usuario
        """
        # Si el servicio real tiene propietario_id, usamos el repositorio
        # Para evitar circular dependency, accedemos al repositorio directamente
        from app.repositories.pet_repository import PetRepository

        # Obtener sesión de DB del servicio real
        db_session = getattr(self._real_service, 'db', None)

        if db_session is None:
            return []

        pet_repo = PetRepository(db_session)
        pets = pet_repo.get_by_propietario(self._current_user.id)

        return [pet.id for pet in pets]

    def _log_action(self, action: str, details: dict):
        """
        Registra la acción para auditoría

        Args:
            action: Nombre de la acción
            details: Detalles de la acción
        """
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'user_id': str(self._current_user.id),
            'user_email': self._current_user.correo,
            'user_role': self._current_user.rol.value,
            'action': action,
            'details': details
        }

        # Si hay callback de auditoría, usarlo
        if self._audit:
            try:
                self._audit(log_entry)
            except Exception as exc:
                logger.error(f"Error en callback de auditoría: {exc}")

        # Siempre loguear
        logger.info(f"Auditoría: {action} por {self._current_user.correo}")