"""
Schemas de Mascota - Validación con Pydantic
"""
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import date, datetime


# ==================== SCHEMA DE ENTRADA: CREAR MASCOTA ====================
class PetCreate(BaseModel):
    """
    Esquema de validación para la creación de una mascota.
    Define los campos requeridos y opcionales que el cliente debe enviar.
    """
    propietario_id: UUID  # ID del propietario al que pertenece la mascota
    nombre: str = Field(..., min_length=2, max_length=120)  # Nombre de la mascota (obligatorio)
    especie: str = Field(..., min_length=2, max_length=60)  # Especie (perro, gato, etc.)
    raza: Optional[str] = Field(None, max_length=120)  # Raza de la mascota (opcional)
    microchip: Optional[str] = Field(None, max_length=60)  # Código del microchip (opcional)
    fecha_nacimiento: Optional[date] = None  # Fecha de nacimiento (opcional)


# ==================== SCHEMA DE SALIDA: RESPUESTA MASCOTA ====================
class PetResponse(BaseModel):
    """
    Esquema de respuesta que representa los datos de una mascota.
    Se utiliza para devolver información detallada al cliente.
    """
    id: UUID  # Identificador único de la mascota
    propietario_id: UUID  # ID del propietario asociado
    nombre: str
    especie: str
    raza: Optional[str]
    microchip: Optional[str]
    fecha_nacimiento: Optional[date]
    activo: bool  # Indica si la mascota está activa en el sistema
    fecha_creacion: datetime  # Fecha de creación del registro

    class Config:
        # Permite crear instancias del modelo a partir de objetos ORM (como los modelos de SQLAlchemy)
        from_attributes = True
