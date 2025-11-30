"""
Patrón Strategy - Interface para estrategias de exportación
RNF-06: Interoperabilidad - Exportar información en formatos estándar (PDF, CSV)
RF-07: Gestión de historias clínicas

Este módulo define la interfaz que todas las estrategias de exportación
deben implementar, permitiendo intercambiar algoritmos de exportación
de forma dinámica.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
from io import BytesIO


class IEstrategiaExportacion(ABC):
    """
    Interface Strategy - Define el contrato que deben cumplir todas
    las estrategias de exportación de historias clínicas.

    Permite exportar historias clínicas en diferentes formatos
    sin modificar el código cliente.
    """

    @abstractmethod
    def exportar(self, datos: Dict[str, Any]) -> BytesIO:
        """
        Exporta los datos de la historia clínica al formato específico

        Args:
            datos: Diccionario con la información de la historia clínica
                  Estructura esperada:
                  {
                      "historia_clinica": {...},
                      "mascota": {...},
                      "propietario": {...},
                      "consultas": [...]
                  }

        Returns:
            BytesIO: Stream de bytes con el archivo generado

        Raises:
            ValueError: Si los datos son inválidos o incompletos
        """
        pass

    @abstractmethod
    def obtener_extension(self) -> str:
        """
        Retorna la extensión del archivo generado

        Returns:
            str: Extensión del archivo (ej: "pdf", "csv")
        """
        pass

    @abstractmethod
    def obtener_content_type(self) -> str:
        """
        Retorna el Content-Type HTTP del archivo generado

        Returns:
            str: Content-Type (ej: "application/pdf", "text/csv")
        """
        pass

    def validar_datos(self, datos: Dict[str, Any]) -> None:
        """
        Valida que los datos contengan la información mínima requerida

        Args:
            datos: Diccionario con la información a exportar

        Raises:
            ValueError: Si faltan campos obligatorios
        """
        campos_requeridos = [
            "historia_clinica",
            "mascota",
            "propietario",
            "consultas"
        ]

        for campo in campos_requeridos:
            if campo not in datos or datos[campo] is None:
                raise ValueError(
                    f"Campo obligatorio '{campo}' no encontrado en los datos"
                )

        # Validar que la historia clínica tenga ID
        if "id" not in datos["historia_clinica"]:
            raise ValueError(
                "La historia clínica debe tener un ID válido"
            )