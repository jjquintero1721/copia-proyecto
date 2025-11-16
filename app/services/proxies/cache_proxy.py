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
        Inicializa el proxies de caché

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

    def get_appointments_by_date(
            self,
            fecha: date,
            veterinario_id: Optional[UUID] = None
    ) -> List[Appointment]:
        """
        Obtiene citas de una fecha específica usando caché

        Flujo:
        1. Verificar caché
        2. Si existe y es válido, retornar
        3. Si no, consultar servicio real
        4. Almacenar en caché y retornar
        """
        # Generar clave de caché
        cache_key = self._generate_cache_key(fecha, veterinario_id)

        # Intentar obtener del caché
        cached_data = self._get_from_cache(cache_key)

        if cached_data is not None:
            logger.debug(f"Cache HIT para fecha {fecha}")
            return self._deserialize_appointments(cached_data)

        # Cache MISS - consultar servicio real
        logger.debug(f"Cache MISS para fecha {fecha}")
        appointments = self._real_service.get_appointments_by_date(fecha, veterinario_id)

        # Guardar en caché
        self._save_to_cache(cache_key, appointments)

        return appointments

    def invalidate_cache(self, fecha: Optional[date] = None, veterinario_id: Optional[UUID] = None):
        """
        Invalida el caché para una fecha específica o todo el caché

        Se llama cuando:
        - Se crea una nueva cita
        - Se modifica una cita
        - Se cancela una cita

        Args:
            fecha: Fecha específica a invalidar (None = todo)
            veterinario_id: Veterinario específico (None = todos)
        """
        if fecha is None:
            # Invalidar todo el caché
            self._invalidate_all()
            logger.info("Caché completamente invalidado")
        else:
            # Invalidar fecha específica
            cache_key = self._generate_cache_key(fecha, veterinario_id)
            self._delete_from_cache(cache_key)
            logger.info(f"Caché invalidado para fecha {fecha}")

    # ==================== DELEGACIÓN A SERVICIO REAL ====================
    # Estos métodos delegan directamente al servicio real e invalidan caché

    def create_appointment(self, appointment_data: Any, creado_por: Optional[UUID] = None) -> Appointment:
        """Crea cita e invalida caché del día"""
        appointment = self._real_service.create_appointment(appointment_data, creado_por)

        # Invalidar caché del día de la cita
        fecha = appointment.fecha_hora.date()
        self.invalidate_cache(fecha)

        return appointment

    def reschedule_appointment(
            self,
            appointment_id: UUID,
            nueva_fecha: datetime,
            usuario_id: Optional[UUID] = None
    ) -> Appointment:
        """Reprograma cita e invalida caché de ambas fechas"""
        # Obtener cita original para invalidar su fecha
        original = self._real_service.get_appointment_by_id(appointment_id)

        # Reprogramar
        appointment = self._real_service.reschedule_appointment(
            appointment_id, nueva_fecha, usuario_id
        )

        # Invalidar ambas fechas
        if original:
            self.invalidate_cache(original.fecha_hora.date())
        self.invalidate_cache(nueva_fecha.date())

        return appointment

    def cancel_appointment(
            self,
            appointment_id: UUID,
            motivo_cancelacion: str,
            usuario_id: Optional[UUID] = None
    ) -> Appointment:
        """Cancela cita e invalida caché"""
        appointment = self._real_service.cancel_appointment(
            appointment_id, motivo_cancelacion, usuario_id
        )

        # Invalidar caché del día
        fecha = appointment.fecha_hora.date()
        self.invalidate_cache(fecha)

        return appointment

    def get_appointment_by_id(self, appointment_id: UUID) -> Optional[Appointment]:
        """Obtiene cita por ID (sin caché, consulta directa)"""
        return self._real_service.get_appointment_by_id(appointment_id)

    def get_all_appointments(self, **kwargs) -> List[Appointment]:
        """Obtiene todas las citas (sin caché, consulta directa)"""
        return self._real_service.get_all_appointments(**kwargs)

    # ==================== MÉTODOS PRIVADOS DE CACHÉ ====================

    def _generate_cache_key(self, fecha: date, veterinario_id: Optional[UUID] = None) -> str:
        """
        Genera clave única para el caché

        Formato: gdcv:appointments:YYYY-MM-DD[:veterinario_id]
        """
        key = f"{self.CACHE_KEY_PREFIX}{fecha.isoformat()}"

        if veterinario_id:
            key = f"{key}:{str(veterinario_id)}"

        return key

    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Obtiene datos del caché (Redis o memoria)"""
        if self._use_redis:
            return self._get_from_redis(cache_key)
        return self._get_from_memory(cache_key)

    def _save_to_cache(self, cache_key: str, appointments: List[Appointment]):
        """Guarda datos en caché (Redis o memoria)"""
        serialized = self._serialize_appointments(appointments)

        if self._use_redis:
            self._save_to_redis(cache_key, serialized)
        else:
            self._save_to_memory(cache_key, serialized)

    def _delete_from_cache(self, cache_key: str):
        """Elimina entrada del caché"""
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

    # ==================== SERIALIZACIÓN ====================

    def _serialize_appointments(self, appointments: List[Appointment]) -> List[dict]:
        """Serializa lista de citas a diccionarios"""
        return [self._appointment_to_dict(apt) for apt in appointments]

    def _deserialize_appointments(self, data: List[dict]) -> List[Appointment]:
        """
        Deserializa diccionarios a objetos Appointment

        Nota: Retorna objetos simples sin relaciones cargadas
        Para obtener relaciones completas, usar get_appointment_by_id
        """
        appointments = []

        for item in data:
            # Crear objeto Appointment desde dict
            appointment = Appointment(
                id=UUID(item['id']),
                mascota_id=UUID(item['mascota_id']),
                veterinario_id=UUID(item['veterinario_id']),
                servicio_id=UUID(item['servicio_id']),
                fecha_hora=datetime.fromisoformat(item['fecha_hora']),
                motivo=item['motivo'],
                estado=AppointmentStatus(item['estado']),
                creado_por=UUID(item['creado_por']) if item.get('creado_por') else None
            )

            # Establecer timestamps
            appointment.fecha_creacion = datetime.fromisoformat(item['fecha_creacion'])
            appointment.fecha_actualizacion = datetime.fromisoformat(item['fecha_actualizacion'])

            appointments.append(appointment)

        return appointments

    @staticmethod
    def _appointment_to_dict(appointment: Appointment) -> dict:
        """Convierte Appointment a diccionario serializable"""
        return {
            'id': str(appointment.id),
            'mascota_id': str(appointment.mascota_id),
            'veterinario_id': str(appointment.veterinario_id),
            'servicio_id': str(appointment.servicio_id),
            'fecha_hora': appointment.fecha_hora.isoformat(),
            'motivo': appointment.motivo,
            'estado': appointment.estado.value,
            'creado_por': str(appointment.creado_por) if appointment.creado_por else None,
            'fecha_creacion': appointment.fecha_creacion.isoformat(),
            'fecha_actualizacion': appointment.fecha_actualizacion.isoformat()
        }