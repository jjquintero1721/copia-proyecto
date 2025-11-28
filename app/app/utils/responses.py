"""
Respuestas estandarizadas de la API
Cumple con: RNF-03 (Usabilidad), RNF-01 (Mantenibilidad)
"""

from typing import Any, Optional
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime, date, time
from decimal import Decimal
from uuid import UUID
from enum import Enum


def success_response(
        data: Any = None,
        message: str = "Operación exitosa",
        status_code: int = 200
) -> JSONResponse:
    """
    Respuesta exitosa estandarizada

    Args:
        data: Datos a retornar (puede ser objeto Pydantic, lista de Pydantic, dict, etc.)
        message: Mensaje descriptivo de la operación
        status_code: Código HTTP de respuesta (default: 200)

    Returns:
        JSONResponse con formato estandarizado

    Note:
        Esta función convierte automáticamente objetos Pydantic, datetime, UUID, Decimal
        y Enum a formatos JSON serializables.
    """
    # Convertir datos a formato JSON serializable
    serialized_data = _serialize_data(data)

    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": serialized_data
        }
    )


def error_response(
        message: str = "Ha ocurrido un error",
        errors: Optional[Any] = None,
        status_code: int = 400
) -> JSONResponse:
    """
    Respuesta de error estandarizada

    Args:
        message: Mensaje descriptivo del error
        errors: Detalles adicionales del error (opcional)
        status_code: Código HTTP de error (default: 400)

    Returns:
        JSONResponse con formato estandarizado de error
    """
    content = {
        "success": False,
        "message": message
    }

    if errors:
        # Serializar errores si contienen tipos no serializables
        content["errors"] = _serialize_data(errors)

    return JSONResponse(
        status_code=status_code,
        content=content
    )


def _serialize_data(data: Any) -> Any:
    """
    Serializa datos para respuesta JSON de forma recursiva

    Convierte tipos no JSON-serializables a formatos compatibles:
    - BaseModel (Pydantic) → dict
    - datetime/date/time → string ISO format
    - UUID → string
    - Decimal → float
    - Enum → value
    - list → serializa cada elemento
    - dict → serializa cada valor

    Args:
        data: Datos a serializar

    Returns:
        Datos serializables en JSON
    """
    if data is None:
        return None

    # Si es un objeto Pydantic (BaseModel)
    if isinstance(data, BaseModel):
        # Convertir a dict y serializar recursivamente para manejar campos anidados
        return _serialize_data(data.model_dump())

    # Si es datetime, date o time
    if isinstance(data, (datetime, date, time)):
        return data.isoformat()

    # Si es UUID
    if isinstance(data, UUID):
        return str(data)

    # Si es Decimal
    if isinstance(data, Decimal):
        return float(data)

    # Si es Enum
    if isinstance(data, Enum):
        return data.value

    # Si es una lista, serializar cada elemento
    if isinstance(data, list):
        return [_serialize_data(item) for item in data]

    # Si es un diccionario, serializar cada valor
    if isinstance(data, dict):
        return {key: _serialize_data(value) for key, value in data.items()}

    # En otros casos (int, str, float, bool, None), retornar sin modificar
    return data