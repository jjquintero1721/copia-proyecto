"""
Schemas de Mascota - Validación con Pydantic
"""
from pydantic import BaseModel, Field
from typing import Optional, List
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
    color: Optional[str] = Field(None, max_length=60)
    sexo: str = Field(..., min_length=3, max_length=20)
    peso: Optional[float] = None
    microchip: Optional[str] = Field(None, max_length=60)  # Código del microchip (opcional)
    fecha_nacimiento: Optional[date] = None  # Fecha de nacimiento (opcional)


class OwnerSimple(BaseModel):
    """
    Esquema simplificado de propietario para respuestas anidadas
    """
    id: UUID
    nombre: str
    correo: str
    telefono: Optional[str]

    class Config:
        from_attributes = True

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
    color: Optional[str]
    sexo: str
    peso: Optional[float]
    microchip: Optional[str]
    fecha_nacimiento: Optional[date]
    activo: bool  # Indica si la mascota está activa en el sistema
    fecha_creacion: datetime  # Fecha de creación del registro

    class Config:
        # Permite crear instancias del modelo a partir de objetos ORM (como los modelos de SQLAlchemy)
        from_attributes = True


class PetWithOwnerResponse(BaseModel):
    """
    Esquema de respuesta de mascota con información del propietario
    Usado en listados para mostrar relación mascota-propietario
    """
    id: UUID
    nombre: str
    especie: str
    raza: Optional[str]
    color: Optional[str]
    sexo: str
    peso: Optional[float]
    microchip: Optional[str]
    fecha_nacimiento: Optional[date]
    activo: bool
    fecha_creacion: datetime
    owner: OwnerSimple

    class Config:
        from_attributes = True


# ==================== SCHEMA DE SALIDA: LISTA PAGINADA DE MASCOTAS ====================
class PetListResponse(BaseModel):
    """
    Esquema de respuesta para listas paginadas de mascotas
    Incluye datos de paginación y metadatos
    """
    total: int = Field(..., description="Total de mascotas en el sistema")
    page: int = Field(..., description="Página actual")
    page_size: int = Field(..., description="Tamaño de la página")
    total_pages: int = Field(..., description="Total de páginas disponibles")
    pets: List[PetWithOwnerResponse] = Field(..., description="Lista de mascotas")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 50,
                "page": 1,
                "page_size": 10,
                "total_pages": 5,
                "pets": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "nombre": "Max",
                        "especie": "perro",
                        "raza": "Golden Retriever",
                        "microchip": "123456789012345",
                        "fecha_nacimiento": "2020-05-15",
                        "activo": True,
                        "fecha_creacion": "2024-01-15T10:30:00",
                        "propietario": {
                            "id": "123e4567-e89b-12d3-a456-426614174001",
                            "nombre": "Juan Pérez",
                            "correo": "juan@example.com",
                            "telefono": "+573001234567"
                        }
                    }
                ]
            }
        }


# ==================== SCHEMA PARA QUERY PARAMETERS ====================
class PetQueryParams(BaseModel):
    """
    Esquema para validar parámetros de consulta en endpoints
    """
    page: int = Field(1, ge=1, description="Número de página (mínimo 1)")
    page_size: int = Field(
        10,
        ge=1,
        le=100,
        description="Tamaño de página (entre 1 y 100)"
    )
    activo: Optional[bool] = Field(
        True,
        description="Filtrar por estado activo (None = todos)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "page_size": 10,
                "activo": True
            }
        }
