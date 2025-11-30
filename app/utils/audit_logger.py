"""
Utilidad para registro de auditoría
RNF-07: Auditoría - Registrar toda acción importante
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
import json


class AuditLogger:
    """
    Utilidad para registrar acciones en el log de auditoría,
    guardando todo dentro de `descripcion` como JSON.
    """

    @staticmethod
    def log_action(
        db: Session,
        usuario_id: UUID,
        accion: str,
        descripcion: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Registra una acción en el log de auditoría.

        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario que realizó la acción
            accion: Nombre del evento
            descripcion: Datos adicionales (JSON)
        """
        # Convertir UUID a str en el diccionario completo
        if descripcion:
            for key, value in descripcion.items():
                if isinstance(value, UUID):
                    descripcion[key] = str(value)

        descripcion_json = json.dumps(descripcion or {}, ensure_ascii=False)

        log_entry = AuditLog(
            usuario_id=usuario_id,
            accion=accion,
            descripcion=descripcion_json,
            fecha_hora=datetime.now(timezone.utc)
        )

        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)

        return log_entry
