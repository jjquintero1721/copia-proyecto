"""
CacheProxy - Patrón Proxy para Caché
Almacena en caché las citas del día, reduciendo consultas repetitivas a BD

Relaciona con: RF-05, RNF-04 (Rendimiento)

Principios SOLID aplicados:
- Single Responsibility: Solo maneja caché de citas
- Open/Closed: Extensible sin modificar código existente
- Dependency Inversion: Depende de la interfaz, no de implementación concreta
"""

import json
import logging
from typing import Optional, List, Any
from datetime import datetime, date, timezone, timedelta
from uuid import UUID

from app.models.appointment import Appointment, AppointmentStatus

logger = logging.getLogger(__name__)


class CacheProxy:
    """
    Proxy que añade capacidad de caché al servicio de citas

    Estrategia de caché:
    1. Intenta usar Redis si está disponible
    2. Fallback a caché en memoria si Redis no está disponible
    3. TTL configurable (por defecto 5 minutos)

    Evita antipatrón: Hardcoding (configuración mediante parámetros)
    """

    # Configuración de caché (evita hardcoding)
    DEFAULT_TTL_SECONDS = 300  # 5 minutos
    CACHE_KEY_PREFIX = "gdcv:appointments:"

    def __init__(
            self,
            real_service: Any,
            redis_client: Optional[Any] = None,
            ttl_seconds: int = DEFAULT_TTL_SECONDS
    ):
        """
        Inicializa el proxy de caché

        Args:
            real_service: Servicio real de citas (AppointmentService)
            redis_client: Cliente de Redis (opcional)
            ttl_seconds: Tiempo de vida del caché en segundos
        """
        self._real_service = real_service
        self._redis = redis_client
        self._ttl = ttl_seconds

        # Caché en memoria como fallback (evita God Object usando dict simple)
        self._memory_cache: dict[str, dict] = {}

        # Determinar estrategia de caché
        self._use_redis = redis_client is not None

        if self._use_redis:
            logger.info("CacheProxy inicializado con Redis")
        else:
            logger.info("CacheProxy inicializado con caché en memoria")

    # ==================== Métodos con caché ====================

    def get_appointments_by_date(
            self,
            fecha: date,
            veterinario_id: Optional[UUID] = None
    ) -> List[Appointment]:
        """Obtiene citas usando caché"""

        # Generar clave de caché
        cache_key = self._generate_cache_key(fecha, veterinario_id)

        logger.info(f"🔍 Buscando en caché: {cache_key}")

        # Intentar obtener del caché
        cached_data = self._get_from_cache(cache_key)

        if cached_data is not None:
            logger.info(f"✅ Cache HIT para {cache_key}")
            appointments = self._deserialize_appointments(cached_data)
            return appointments

        logger.info(f"❌ Cache MISS para {cache_key} - consultando BD")

        # Cache miss - consultar servicio real
        appointments = self._real_service.get_appointments_by_date(
            fecha, veterinario_id
        )

        # Guardar en caché
        self._save_to_cache(cache_key, self._serialize_appointments(appointments))

        return appointments

    def get_appointment_by_id(self, appointment_id: UUID) -> Optional[Appointment]:
        """
        Obtiene una cita por ID (sin caché, ya que se modifica frecuentemente)
        Delegación directa al servicio real
        """
        return self._real_service.get_appointment_by_id(appointment_id)

    def get_appointments(
            self,
            fecha: Optional[date] = None,
            veterinario_id: Optional[UUID] = None,
            estado: Optional[AppointmentStatus] = None
    ) -> List[Appointment]:
        """
        Obtiene citas con filtros (usa caché solo para fecha específica)
        """
        # Solo usar caché si se especifica fecha
        if fecha is not None:
            return self.get_appointments_by_date(fecha, veterinario_id)

        # Sin fecha específica, consultar directamente
        return self._real_service.get_appointments(fecha, veterinario_id, estado)

    # ==================== Métodos que invalidan caché ====================

    def create_appointment(
            self,
            appointment_data: Any,
            creado_por: Optional[UUID] = None
    ) -> Appointment:
        """
        Crea una cita e invalida el caché del día correspondiente
        """
        # Delegar al servicio real
        appointment = self._real_service.create_appointment(appointment_data, creado_por)

        # Invalidar caché del día de la cita
        self._invalidate_date_cache(appointment.fecha_hora.date())

        logger.info(f"Cita creada: {appointment.id}, caché invalidado")
        return appointment

    def reschedule_appointment(
            self,
            appointment_id: UUID,
            nueva_fecha: datetime,
            usuario_id: Optional[UUID] = None
    ) -> Appointment:
        """
        Reprograma una cita e invalida caché de fechas involucradas
        """
        # Obtener cita original para saber su fecha anterior
        original_appointment = self._real_service.get_appointment_by_id(appointment_id)

        if original_appointment:
            fecha_original = original_appointment.fecha_hora.date()
        else:
            fecha_original = None

        # Delegar al servicio real
        appointment = self._real_service.reschedule_appointment(
            appointment_id, nueva_fecha, usuario_id
        )

        # Invalidar caché de ambas fechas
        if fecha_original:
            self._invalidate_date_cache(fecha_original)

        self._invalidate_date_cache(nueva_fecha.date())

        logger.info(f"Cita {appointment_id} reprogramada, caché invalidado")
        return appointment

    def cancel_appointment(
            self,
            appointment_id: UUID,
            usuario_id: Optional[UUID] = None
    ) -> Appointment:
        """
        Cancela una cita e invalida el caché del día correspondiente
        """
        # Obtener cita para saber su fecha
        original_appointment = self._real_service.get_appointment_by_id(appointment_id)

        # Delegar al servicio real
        appointment = self._real_service.cancel_appointment(appointment_id, usuario_id)

        # Invalidar caché del día
        if original_appointment:
            self._invalidate_date_cache(original_appointment.fecha_hora.date())

        logger.info(f"Cita {appointment_id} cancelada, caché invalidado")
        return appointment

    def confirm_appointment(
            self,
            appointment_id: UUID,
            usuario_id: Optional[UUID] = None
    ) -> Appointment:
        """
        Confirma una cita e invalida el caché del día correspondiente
        """
        # Obtener cita para saber su fecha
        original_appointment = self._real_service.get_appointment_by_id(appointment_id)

        # Delegar al servicio real
        appointment = self._real_service.confirm_appointment(appointment_id, usuario_id)

        # Invalidar caché del día
        if original_appointment:
            self._invalidate_date_cache(original_appointment.fecha_hora.date())

        logger.info(f"Cita {appointment_id} confirmada, caché invalidado")
        return appointment

    def start_appointment(
            self,
            appointment_id: UUID,
            usuario_id: Optional[UUID] = None
    ) -> Appointment:
        """
        Inicia una cita e invalida el caché del día correspondiente
        """
        # Obtener cita para saber su fecha
        original_appointment = self._real_service.get_appointment_by_id(appointment_id)

        # Delegar al servicio real
        appointment = self._real_service.start_appointment(appointment_id, usuario_id)

        # Invalidar caché del día
        if original_appointment:
            self._invalidate_date_cache(original_appointment.fecha_hora.date())

        logger.info(f"Cita {appointment_id} iniciada, caché invalidado")
        return appointment

    def complete_appointment(
            self,
            appointment_id: UUID,
            notas: Optional[str] = None,
            usuario_id: Optional[UUID] = None
    ) -> Appointment:
        """
        Completa una cita e invalida el caché del día correspondiente
        """
        # Obtener cita para saber su fecha
        original_appointment = self._real_service.get_appointment_by_id(appointment_id)

        # Delegar al servicio real
        appointment = self._real_service.complete_appointment(
            appointment_id, notas, usuario_id
        )

        # Invalidar caché del día
        if original_appointment:
            self._invalidate_date_cache(original_appointment.fecha_hora.date())

        logger.info(f"Cita {appointment_id} completada, caché invalidado")
        return appointment

    def check_availability(
            self,
            veterinario_id: UUID,
            fecha_hora: datetime,
            duracion_minutos: int
    ) -> bool:
        """
        Verifica disponibilidad (sin caché, necesita datos en tiempo real)
        """
        return self._real_service.check_availability(
            veterinario_id, fecha_hora, duracion_minutos
        )

    # ==================== Métodos privados de caché ====================

    def _generate_cache_key(
            self,
            fecha: date,
            veterinario_id: Optional[UUID] = None
    ) -> str:
        """Genera una clave única para el caché"""
        fecha_str = fecha.strftime("%Y-%m-%d")

        if veterinario_id:
            return f"{self.CACHE_KEY_PREFIX}{fecha_str}:vet:{veterinario_id}"

        return f"{self.CACHE_KEY_PREFIX}{fecha_str}:all"

    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Obtiene datos del caché (Redis o memoria)"""
        if self._use_redis:
            return self._get_from_redis(cache_key)

        return self._get_from_memory(cache_key)

    def _save_to_cache(self, cache_key: str, data: Any):
        """Guarda datos en el caché (Redis o memoria)"""
        if self._use_redis:
            self._save_to_redis(cache_key, data)
        else:
            self._save_to_memory(cache_key, data)

    def _serialize_appointments(self, appointments: List[Appointment]) -> List[dict]:
        """Serializa citas a diccionarios para almacenar en caché"""
        return [apt.to_dict() for apt in appointments]

    def _deserialize_appointments(self, data: List[dict]) -> List[Appointment]:
        """
        Deserializa citas desde diccionarios
        NOTA: Esto retorna objetos Mock, no instancias completas de Appointment
        Para uso en producción, considera hidratar desde BD
        """
        # Crear objetos Appointment simulados desde los datos en caché
        from app.models.appointment import Appointment as AppointmentModel

        appointments = []
        for apt_data in data:
            # Reconstruir el objeto básico
            apt = AppointmentModel()
            for key, value in apt_data.items():
                setattr(apt, key, value)
            appointments.append(apt)

        return appointments

    def _invalidate_date_cache(self, fecha: date):
        """Invalida el caché de una fecha específica"""
        # Invalidar caché general del día
        cache_key_all = self._generate_cache_key(fecha, None)
        self._invalidate_cache(cache_key_all)

        # En producción, también deberías invalidar cachés específicos por veterinario
        # Para simplificar, invalidamos todo el patrón de esa fecha
        if self._use_redis:
            try:
                fecha_str = fecha.strftime("%Y-%m-%d")
                pattern = f"{self.CACHE_KEY_PREFIX}{fecha_str}:*"
                keys = self._redis.keys(pattern)
                if keys:
                    self._redis.delete(*keys)
                    logger.info(f"Caché invalidado para fecha {fecha_str}: {len(keys)} claves")
            except Exception as exc:
                logger.warning(f"Error invalidando Redis para fecha {fecha}: {exc}")

    def _invalidate_cache(self, cache_key: str):
        """Elimina una clave específica del caché"""
        if self._use_redis:
            try:
                self._redis.delete(cache_key)
            except Exception as exc:
                logger.warning(f"Error eliminando de Redis: {exc}")
        else:
            self._memory_cache.pop(cache_key, None)

    def _invalidate_all(self):
        """Invalida todo el caché"""
        if self._use_redis:
            try:
                # Buscar todas las claves con el prefijo
                pattern = f"{self.CACHE_KEY_PREFIX}*"
                keys = self._redis.keys(pattern)
                if keys:
                    self._redis.delete(*keys)
            except Exception as exc:
                logger.warning(f"Error invalidando Redis: {exc}")
        else:
            self._memory_cache.clear()

    # ==================== REDIS ====================

    def _get_from_redis(self, cache_key: str) -> Optional[Any]:
        """Obtiene datos de Redis"""
        try:
            data = self._redis.get(cache_key)
            if data:
                return json.loads(data)
            return None
        except Exception as exc:
            logger.warning(f"Error obteniendo de Redis: {exc}")
            return None

    def _save_to_redis(self, cache_key: str, data: Any):
        """Guarda datos en Redis con TTL"""
        try:
            serialized = json.dumps(data)
            self._redis.setex(cache_key, self._ttl, serialized)
        except Exception as exc:
            logger.warning(f"Error guardando en Redis: {exc}")

    # ==================== MEMORIA ====================

    def _get_from_memory(self, cache_key: str) -> Optional[Any]:
        """Obtiene datos de caché en memoria"""
        entry = self._memory_cache.get(cache_key)

        if entry is None:
            return None

        # Verificar si expiró
        now = datetime.now(timezone.utc)
        if now > entry['expires_at']:
            # Expiró, eliminar
            del self._memory_cache[cache_key]
            return None

        return entry['data']

    def _save_to_memory(self, cache_key: str, data: Any):
        """Guarda datos en caché de memoria con TTL"""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=self._ttl)

        self._memory_cache[cache_key] = {
            'data': data,
            'expires_at': expires_at
        }

    # ==================== Delegación dinámica ====================

    def __getattr__(self, name: str) -> Any:
        """
        Delegación dinámica de métodos no definidos explícitamente
        Permite que el proxy sea transparente para otros métodos del servicio

        Args:
            name: Nombre del método o atributo

        Returns:
            Método o atributo del servicio real
        """
        return getattr(self._real_service, name)