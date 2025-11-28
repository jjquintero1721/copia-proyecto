"""
Utilidades para manejo de timezone
Asegura consistencia en el manejo de datetime con timezone en todo el proyecto

IMPORTANTE: Usar estas funciones en todo el código para evitar errores
de naive vs aware datetimes
"""

from datetime import datetime, timezone, timedelta
from typing import Optional


def now_utc() -> datetime:
    """
    Obtiene la fecha y hora actual en UTC con timezone

    USAR ESTA FUNCIÓN en lugar de datetime.utcnow() (obsoleto)

    Returns:
        datetime con timezone UTC

    Example:
        >>> from app.utils.datetime_helpers import now_utc
        >>> current_time = now_utc()
        >>> print(current_time.tzinfo)  # <UTC>
    """
    return datetime.now(timezone.utc)


def ensure_timezone_aware(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Asegura que un datetime tenga información de timezone.
    Si no la tiene, asume UTC.

    Args:
        dt: datetime a verificar (puede ser None)

    Returns:
        datetime con timezone UTC, o None si dt es None

    Example:
        >>> from datetime import datetime
        >>> naive_dt = datetime(2025, 11, 17, 12, 0, 0)
        >>> aware_dt = ensure_timezone_aware(naive_dt)
        >>> print(aware_dt.tzinfo)  # <UTC>
    """
    if dt is None:
        return None

    if dt.tzinfo is None:
        # Si no tiene timezone, asumimos UTC
        return dt.replace(tzinfo=timezone.utc)

    return dt


def to_utc(dt: datetime) -> datetime:
    """
    Convierte un datetime a UTC

    Args:
        dt: datetime a convertir

    Returns:
        datetime en UTC con timezone

    Raises:
        ValueError: Si dt es None

    Example:
        >>> from datetime import datetime, timezone
        >>> local_dt = datetime(2025, 11, 17, 12, 0, 0, tzinfo=timezone.utc)
        >>> utc_dt = to_utc(local_dt)
        >>> print(utc_dt.tzinfo)  # <UTC>
    """
    if dt is None:
        raise ValueError("datetime no puede ser None")

    # Asegurar que tenga timezone
    dt_aware = ensure_timezone_aware(dt)

    # Convertir a UTC
    return dt_aware.astimezone(timezone.utc)


def is_timezone_aware(dt: datetime) -> bool:
    """
    Verifica si un datetime tiene información de timezone

    Args:
        dt: datetime a verificar

    Returns:
        True si tiene timezone, False si no

    Example:
        >>> from datetime import datetime, timezone
        >>> naive_dt = datetime(2025, 11, 17, 12, 0, 0)
        >>> aware_dt = datetime(2025, 11, 17, 12, 0, 0, tzinfo=timezone.utc)
        >>> print(is_timezone_aware(naive_dt))  # False
        >>> print(is_timezone_aware(aware_dt))  # True
    """
    if dt is None:
        return False
    return dt.tzinfo is not None


def datetime_diff_hours(dt1: datetime, dt2: datetime) -> float:
    """
    Calcula la diferencia en horas entre dos datetimes
    Normaliza timezone antes de calcular

    Args:
        dt1: datetime inicial
        dt2: datetime final

    Returns:
        Diferencia en horas (puede ser negativa)

    Example:
        >>> from datetime import datetime, timezone, timedelta
        >>> dt1 = datetime.now(timezone.utc)
        >>> dt2 = dt1 + timedelta(hours=5)
        >>> diff = datetime_diff_hours(dt1, dt2)
        >>> print(diff)  # 5.0
    """
    dt1_aware = ensure_timezone_aware(dt1)
    dt2_aware = ensure_timezone_aware(dt2)

    diff = dt2_aware - dt1_aware
    return diff.total_seconds() / 3600


def is_future(dt: datetime, reference: Optional[datetime] = None) -> bool:
    """
    Verifica si un datetime está en el futuro

    Args:
        dt: datetime a verificar
        reference: datetime de referencia (por defecto: ahora)

    Returns:
        True si dt está en el futuro, False si no

    Example:
        >>> from datetime import datetime, timezone, timedelta
        >>> future_dt = datetime.now(timezone.utc) + timedelta(days=1)
        >>> print(is_future(future_dt))  # True
    """
    if reference is None:
        reference = now_utc()

    dt_aware = ensure_timezone_aware(dt)
    ref_aware = ensure_timezone_aware(reference)

    return dt_aware > ref_aware


def is_past(dt: datetime, reference: Optional[datetime] = None) -> bool:
    """
    Verifica si un datetime está en el pasado

    Args:
        dt: datetime a verificar
        reference: datetime de referencia (por defecto: ahora)

    Returns:
        True si dt está en el pasado, False si no

    Example:
        >>> from datetime import datetime, timezone, timedelta
        >>> past_dt = datetime.now(timezone.utc) - timedelta(days=1)
        >>> print(is_past(past_dt))  # True
    """
    if reference is None:
        reference = now_utc()

    dt_aware = ensure_timezone_aware(dt)
    ref_aware = ensure_timezone_aware(reference)

    return dt_aware < ref_aware


def add_hours(dt: datetime, hours: int) -> datetime:
    """
    Suma horas a un datetime manteniendo timezone

    Args:
        dt: datetime base
        hours: horas a sumar (puede ser negativo)

    Returns:
        datetime con las horas sumadas

    Example:
        >>> from datetime import datetime, timezone
        >>> dt = datetime(2025, 11, 17, 12, 0, 0, tzinfo=timezone.utc)
        >>> new_dt = add_hours(dt, 5)
        >>> print(new_dt.hour)  # 17
    """
    dt_aware = ensure_timezone_aware(dt)
    return dt_aware + timedelta(hours=hours)


def add_days(dt: datetime, days: int) -> datetime:
    """
    Suma días a un datetime manteniendo timezone

    Args:
        dt: datetime base
        days: días a sumar (puede ser negativo)

    Returns:
        datetime con los días sumados

    Example:
        >>> from datetime import datetime, timezone
        >>> dt = datetime(2025, 11, 17, 12, 0, 0, tzinfo=timezone.utc)
        >>> new_dt = add_days(dt, 7)
        >>> print(new_dt.day)  # 24
    """
    dt_aware = ensure_timezone_aware(dt)
    return dt_aware + timedelta(days=days)


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S %Z") -> str:
    """
    Formatea un datetime a string

    Args:
        dt: datetime a formatear
        format_str: formato de salida

    Returns:
        String formateado

    Example:
        >>> from datetime import datetime, timezone
        >>> dt = datetime(2025, 11, 17, 12, 0, 0, tzinfo=timezone.utc)
        >>> formatted = format_datetime(dt)
        >>> print(formatted)  # "2025-11-17 12:00:00 UTC"
    """
    dt_aware = ensure_timezone_aware(dt)
    return dt_aware.strftime(format_str)


def parse_datetime_safe(dt_str: str) -> Optional[datetime]:
    """
    Parsea un string a datetime de forma segura
    Asegura que el resultado sea timezone-aware

    Args:
        dt_str: string con formato ISO 8601

    Returns:
        datetime con timezone, o None si falla el parseo

    Example:
        >>> dt = parse_datetime_safe("2025-11-17T12:00:00Z")
        >>> print(dt.tzinfo)  # <UTC>
    """
    try:
        # Intentar parsear con timezone
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return ensure_timezone_aware(dt)
    except (ValueError, AttributeError):
        return None


# Alias para compatibilidad
utcnow = now_utc  # Para código legacy que use utcnow()