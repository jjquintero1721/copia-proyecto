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
        'view_all_appointments': [UserRole.SUPERADMIN, UserRole.VETERINARIO, UserRole.AUXILIAR, UserRole.PROPIETARIO],
        'reschedule_appointment': [UserRole.SUPERADMIN, UserRole.VETERINARIO, UserRole.AUXILIAR, UserRole.PROPIETARIO],
        'cancel_appointment': [UserRole.SUPERADMIN, UserRole.VETERINARIO, UserRole.AUXILIAR, UserRole.PROPIETARIO],
        'confirm_appointment': [UserRole.SUPERADMIN, UserRole.VETERINARIO, UserRole.AUXILIAR],
        'start_appointment': [UserRole.SUPERADMIN, UserRole.VETERINARIO, UserRole.AUXILIAR],
        'complete_appointment': [UserRole.SUPERADMIN, UserRole.VETERINARIO],
    }

    def __init__(
            self,
            real_service: Any,
            current_user: User,
            audit_callback: Optional[Callable] = None
    ):
        """
        Inicializa el proxy de autorización

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

    def get_appointments(
            self,
            fecha: Optional[date] = None,
            veterinario_id: Optional[UUID] = None,
            estado: Optional[AppointmentStatus] = None
    ) -> List[Appointment]:
        """
        Lista citas verificando permisos

        Reglas:
        - Staff puede ver todas las citas
        - Clientes solo pueden ver sus propias citas
        """
        self._verify_permission('view_all_appointments')

        # Si es propietario, usar método con privacidad
        if self._current_user.rol == UserRole.PROPIETARIO:
            # Obtener el ID del propietario desde la relación user->owner
            if not self._current_user.propietario:
                logger.error(f"❌ Usuario propietario {self._current_user.id} no tiene registro de propietario")
                return []

            owner_id = self._current_user.propietario.id
            return self._real_service.get_appointments_for_owner(
                owner_id=owner_id,
                fecha=fecha,
                veterinario_id=veterinario_id,
                estado=estado
            )

        # Staff ve todas las citas sin filtro
        appointments = self._real_service.get_appointments(fecha, veterinario_id, estado)
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
            'appointment_id': str(appointment_id)
        })

        # Establecer usuario_id como usuario actual si no se especifica
        if usuario_id is None:
            usuario_id = self._current_user.id

        # Delegar al servicio real
        return self._real_service.cancel_appointment(appointment_id, usuario_id)

    def confirm_appointment(
            self,
            appointment_id: UUID,
            usuario_id: Optional[UUID] = None
    ) -> Appointment:
        """
        Confirma una cita verificando permisos

        Reglas:
        - Solo staff puede confirmar citas
        """
        self._verify_permission('confirm_appointment')

        # Auditar acción
        self._log_action('confirm_appointment', {
            'appointment_id': str(appointment_id)
        })

        # Establecer usuario_id como usuario actual si no se especifica
        if usuario_id is None:
            usuario_id = self._current_user.id

        # Delegar al servicio real
        return self._real_service.confirm_appointment(appointment_id, usuario_id)

    def start_appointment(
            self,
            appointment_id: UUID,
            usuario_id: Optional[UUID] = None
    ) -> Appointment:
        """
        Inicia una cita verificando permisos

        Reglas:
        - Solo staff (veterinarios y auxiliares) puede iniciar citas
        - La cita debe estar en estado CONFIRMADA
        """
        self._verify_permission('start_appointment')

        # Auditar acción
        self._log_action('start_appointment', {
            'appointment_id': str(appointment_id)
        })

        # Establecer usuario_id como usuario actual si no se especifica
        if usuario_id is None:
            usuario_id = self._current_user.id

        # Delegar al servicio real
        return self._real_service.start_appointment(appointment_id, usuario_id)

    def complete_appointment(
            self,
            appointment_id: UUID,
            notas: Optional[str] = None,
            usuario_id: Optional[UUID] = None
    ) -> Appointment:
        """
        Completa una cita verificando permisos

        Reglas:
        - Solo veterinarios pueden completar citas
        - La cita debe estar en estado EN_PROCESO
        """
        self._verify_permission('complete_appointment')

        # Auditar acción
        self._log_action('complete_appointment', {
            'appointment_id': str(appointment_id),
            'notas_agregadas': notas is not None
        })

        # Establecer usuario_id como usuario actual si no se especifica
        if usuario_id is None:
            usuario_id = self._current_user.id

        # Delegar al servicio real
        return self._real_service.complete_appointment(
            appointment_id, notas, usuario_id
        )

    def check_availability(
            self,
            veterinario_id: UUID,
            fecha_hora: datetime,
            duracion_minutos: int
    ) -> bool:
        """
        Verifica disponibilidad sin restricciones de permisos
        (Consulta de solo lectura)
        """
        return self._real_service.check_availability(
            veterinario_id, fecha_hora, duracion_minutos
        )

    # ==================== Métodos privados de validación ====================

    def _verify_permission(self, operation: str) -> None:
        """
        Verifica si el usuario tiene permiso para ejecutar una operación

        Args:
            operation: Nombre de la operación

        Raises:
            PermissionDeniedException: Si el usuario no tiene permiso
        """
        allowed_roles = self.PERMISSIONS.get(operation, [])

        if self._current_user.rol not in allowed_roles:
            logger.warning(
                f"⚠️ Permiso denegado: {self._current_user.correo} "
                f"({self._current_user.rol.value}) intentó ejecutar {operation}"
            )
            raise PermissionDeniedException(
                f"No tienes permisos para realizar esta acción: {operation}"
            )

        logger.info(
            f"✅ Permiso concedido: {self._current_user.correo} "
            f"puede ejecutar {operation}"
        )

    def _verify_pet_ownership(self, mascota_id: UUID) -> None:
        """
        Verifica que una mascota pertenezca al usuario actual

        Args:
            mascota_id: ID de la mascota

        Raises:
            PermissionDeniedException: Si la mascota no pertenece al usuario
        """
        from app.repositories.pet_repository import PetRepository

        # Obtener repositorio
        pet_repo = PetRepository(self._real_service.db)
        mascota = pet_repo.get_by_id(mascota_id)

        if not mascota:
            raise ValueError("La mascota no existe")

        if mascota.propietario_id != self._current_user.id:
            logger.warning(
                f"⚠️ Usuario {self._current_user.correo} intentó acceder "
                f"a mascota que no le pertenece: {mascota_id}"
            )
            raise PermissionDeniedException(
                "No tienes permisos para realizar acciones sobre esta mascota"
            )

    def _verify_appointment_ownership(self, appointment: Appointment) -> None:
        """
        Verifica que una cita pertenezca al usuario actual
        (La mascota de la cita debe ser del usuario)

        Args:
            appointment: Cita a verificar

        Raises:
            PermissionDeniedException: Si la cita no pertenece al usuario
        """
        if appointment.mascota.propietario_id != self._current_user.id:
            logger.warning(
                f"⚠️ Usuario {self._current_user.correo} intentó acceder "
                f"a cita que no le pertenece: {appointment.id}"
            )
            raise PermissionDeniedException(
                "No tienes permisos para acceder a esta cita"
            )

    def _log_action(self, action: str, details: dict) -> None:
        """
        Registra una acción en el log de auditoría

        Args:
            action: Acción realizada
            details: Detalles de la acción
        """
        if self._audit:
            self._audit(
                usuario=self._current_user,
                accion=action,
                detalles=details,
                timestamp=datetime.now(timezone.utc)
            )

        logger.info(
            f"📝 Acción auditada: {action} por {self._current_user.correo} "
            f"- Detalles: {details}"
        )

    # ==================== Delegación dinámica ====================

    def __getattr__(self, name: str) -> Any:
        """
        Delegación dinámica de métodos no definidos explícitamente
        Permite que el proxy sea transparente para otros métodos del servicio

        Args:
            name: Nombre del método

        Returns:
            Método del servicio real
        """
        return getattr(self._real_service, name)