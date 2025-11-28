"""
Schemas de Propietario - Con respuestas de lista y paginación
Validación con Pydantic para endpoints de consulta
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from uuid import UUID
from datetime import datetime


# ==================== SCHEMA DE MASCOTA SIMPLIFICADO ====================
class PetSimple(BaseModel):
    """
    Esquema simplificado de mascota para respuestas anidadas
    """
    id: UUID
    nombre: str
    especie: str
    raza: Optional[str]
    activo: bool

    class Config:
        from_attributes = True


# ==================== SCHEMA DE SALIDA: RESPUESTA PROPIETARIO ====================
class OwnerResponse(BaseModel):
    """
    Esquema de respuesta que representa los datos de un propietario
    """
    id: UUID
    usuario_id: UUID
    nombre: str
    correo: EmailStr
    documento: str
    telefono: Optional[str]
    activo: bool
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== SCHEMA DE SALIDA: PROPIETARIO CON MASCOTAS ====================
class OwnerWithPetsResponse(BaseModel):
    """
    Esquema de respuesta de propietario con sus mascotas
    Usado en consultas detalladas
    """
    id: UUID
    usuario_id: Optional[UUID] = None
    nombre: str
    correo: EmailStr
    documento: str
    telefono: Optional[str]
    activo: bool
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime]
    mascotas: List[PetSimple] = Field(default_factory=list)

    class Config:
        from_attributes = True


# ==================== SCHEMA DE SALIDA: LISTA PAGINADA DE PROPIETARIOS ====================
class OwnerListResponse(BaseModel):
    """
    Esquema de respuesta para listas paginadas de propietarios
    Incluye datos de paginación y metadatos
    """
    total: int = Field(..., description="Total de propietarios en el sistema")
    page: int = Field(..., description="Página actual")
    page_size: int = Field(..., description="Tamaño de la página")
    total_pages: int = Field(..., description="Total de páginas disponibles")
    owners: List[OwnerWithPetsResponse] = Field(..., description="Lista de propietarios")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 25,
                "page": 1,
                "page_size": 10,
                "total_pages": 3,
                "owners": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174001",
                        "usuario_id": "123e4567-e89b-12d3-a456-426614174002",
                        "nombre": "Juan Pérez",
                        "correo": "juan@example.com",
                        "documento": "1234567890",
                        "telefono": "+573001234567",
                        "activo": True,
                        "fecha_creacion": "2024-01-15T10:30:00",
                        "fecha_actualizacion": None,
                        "mascotas": [
                            {
                                "id": "123e4567-e89b-12d3-a456-426614174000",
                                "nombre": "Max",
                                "especie": "perro",
                                "raza": "Golden Retriever",
                                "activo": True
                            }
                        ]
                    }
                ]
            }
        }