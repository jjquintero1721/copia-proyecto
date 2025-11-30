"""
Patrón Strategy - Context para gestión de estrategias de exportación
RNF-06: Interoperabilidad - Exportar información en formatos estándar

El Context mantiene una referencia a la estrategia de exportación
y permite cambiarla dinámicamente en tiempo de ejecución.
"""

from typing import Any, Dict, Optional
from io import BytesIO

from app.services.export.export_strategy import IEstrategiaExportacion
from app.services.export.pdf_export_strategy import PDFExportStrategy
from app.services.export.csv_export_strategy import CSVExportStrategy


class ExportContext:
    """
    Context Pattern - Gestiona la estrategia de exportación activa

    Permite cambiar entre diferentes estrategias de exportación
    (PDF, CSV, etc.) sin modificar el código cliente.
    """

    def __init__(self, estrategia: Optional[IEstrategiaExportacion] = None):
        """
        Inicializa el contexto con una estrategia opcional

        Args:
            estrategia: Estrategia de exportación inicial (opcional)
        """
        self._estrategia = estrategia

    def establecer_estrategia(self, estrategia: IEstrategiaExportacion) -> None:
        """
        Cambia la estrategia de exportación en tiempo de ejecución

        Args:
            estrategia: Nueva estrategia a utilizar
        """
        self._estrategia = estrategia

    def exportar(self, datos: Dict[str, Any]) -> BytesIO:
        """
        Ejecuta la exportación usando la estrategia actual

        Args:
            datos: Diccionario con la información a exportar

        Returns:
            BytesIO: Stream con el archivo generado

        Raises:
            ValueError: Si no hay estrategia configurada o datos inválidos
        """
        if self._estrategia is None:
            raise ValueError(
                "No se ha configurado una estrategia de exportación. "
                "Use establecer_estrategia() primero."
            )

        return self._estrategia.exportar(datos)

    def obtener_extension(self) -> str:
        """
        Obtiene la extensión del archivo de la estrategia actual

        Returns:
            str: Extensión del archivo

        Raises:
            ValueError: Si no hay estrategia configurada
        """
        if self._estrategia is None:
            raise ValueError("No hay estrategia configurada")

        return self._estrategia.obtener_extension()

    def obtener_content_type(self) -> str:
        """
        Obtiene el Content-Type de la estrategia actual

        Returns:
            str: Content-Type HTTP

        Raises:
            ValueError: Si no hay estrategia configurada
        """
        if self._estrategia is None:
            raise ValueError("No hay estrategia configurada")

        return self._estrategia.obtener_content_type()

    @staticmethod
    def crear_con_formato(formato: str) -> 'ExportContext':
        """
        Factory Method - Crea un contexto con la estrategia según el formato

        Args:
            formato: Formato deseado ("pdf" o "csv")

        Returns:
            ExportContext: Contexto configurado con la estrategia apropiada

        Raises:
            ValueError: Si el formato no es soportado
        """
        formato_lower = formato.lower().strip()

        if formato_lower == "pdf":
            return ExportContext(PDFExportStrategy())
        elif formato_lower == "csv":
            return ExportContext(CSVExportStrategy())
        else:
            raise ValueError(
                f"Formato '{formato}' no soportado. "
                f"Formatos disponibles: pdf, csv"
            )