"""
Schemas para exportación de historias clínicas
RNF-06: Interoperabilidad - Exportar información en formatos estándar
"""

from pydantic import BaseModel, Field, validator
from typing import Literal


class ExportHistoriaClinicaRequest(BaseModel):
    """
    Schema para solicitud de exportación de historia clínica

    Attributes:
        formato: Formato de exportación ("pdf" o "csv")
    """
    formato: Literal["pdf", "csv"] = Field(
        ...,
        description="Formato de exportación deseado",
        example="pdf"
    )

    @validator('formato')
    def validar_formato(cls, v):
        """Valida que el formato esté en minúsculas"""
        return v.lower().strip()

    class Config:
        json_schema_extra = {
            "example": {
                "formato": "pdf"
            }
        }


class ExportHistoriaClinicaResponse(BaseModel):
    """
    Schema para respuesta de exportación exitosa

    Attributes:
        mensaje: Mensaje de confirmación
        nombre_archivo: Nombre del archivo generado
        formato: Formato del archivo
        content_type: Content-Type HTTP del archivo
        tamanio_bytes: Tamaño del archivo en bytes
    """
    mensaje: str = Field(
        ...,
        description="Mensaje de confirmación",
        example="Historia clínica exportada exitosamente"
    )
    nombre_archivo: str = Field(
        ...,
        description="Nombre del archivo generado",
        example="HC-2024-0001.pdf"
    )
    formato: str = Field(
        ...,
        description="Formato del archivo",
        example="pdf"
    )
    content_type: str = Field(
        ...,
        description="Content-Type HTTP",
        example="application/pdf"
    )
    tamanio_bytes: int = Field(
        ...,
        description="Tamaño del archivo en bytes",
        example=245680
    )

    class Config:
        json_schema_extra = {
            "example": {
                "mensaje": "Historia clínica exportada exitosamente",
                "nombre_archivo": "HC-2024-0001.pdf",
                "formato": "pdf",
                "content_type": "application/pdf",
                "tamanio_bytes": 245680
            }
        }