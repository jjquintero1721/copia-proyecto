"""
Schemas - Modelos de validación (Pydantic)
Define la estructura y validación de datos de entrada/salida de la API
"""
from app.schemas.triage_schema import (
    TriageCreate,
    TriageUpdate,
    TriageResponse,
    TriagePriorityEnum,
    TriageGeneralStateEnum,
    DolorEnum
)