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
from app.schemas.follow_up_schema import (
    FollowUpCreate,
    FollowUpResponse,
    FollowUpListResponse,
    FollowUpCompletionCreate
)
from app.schemas.notification_settings_schema import (
    NotificationSettingsCreate,
    NotificationSettingsUpdate,
    NotificationSettingsResponse,
    EmailProviderInfoResponse,
    EmailTestRequest,
    EmailTestResponse
)
from app.schemas.appointment_decorator_schema import PrioridadCreate

__all__ = [
    'NotificationSettingsCreate',
    'NotificationSettingsUpdate',
    'NotificationSettingsResponse',
    'EmailProviderInfoResponse',
    'EmailTestRequest',
    'EmailTestResponse',
    'TriageCreate',
    'TriageUpdate',
    'TriageResponse',
    'TriagePriorityEnum',
    'TriageGeneralStateEnum',
    'DolorEnum',
    'FollowUpCreate',
    'FollowUpResponse',
    'FollowUpListResponse',
    'FollowUpCompletionCreate',
    'PrioridadCreate'
]