"""
Modelo de Auditoría - Registro de acciones importantes
RNF-07: Auditoría completa del sistema
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid

from app.database import Base


class AuditLog(Base):
    """
    Modelo de Auditoría - Registra todas las acciones importantes
    """
    __tablename__ = "auditoria"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False, index=True)
    accion = Column(String(100), nullable=False, index=True)
    descripcion = Column(Text, nullable=False)
    fecha_hora = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<AuditLog {self.accion} - {self.usuario_id}>"