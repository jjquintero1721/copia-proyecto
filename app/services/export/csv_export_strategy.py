"""
Patrón Strategy - Implementación concreta para exportación a CSV
RNF-06: Interoperabilidad - Exportar información en formato CSV

Genera archivos CSV con la historia clínica completa, ideal para
importar en hojas de cálculo o sistemas de análisis de datos.
"""

import csv
from typing import Any, Dict, List
from io import BytesIO, StringIO
from datetime import datetime

from app.services.export.export_strategy import IEstrategiaExportacion


class CSVExportStrategy(IEstrategiaExportacion):
    """
    Concrete Strategy - Exportación a formato CSV

    Genera un archivo CSV con:
    - Información de la mascota y propietario
    - Listado completo de consultas en formato tabular
    - Compatible con Excel, Google Sheets y otras herramientas
    """

    def __init__(self, delimiter: str = ',', quotechar: str = '"'):
        """
        Inicializa la estrategia de exportación CSV

        Args:
            delimiter: Separador de campos (por defecto coma)
            quotechar: Caracter para encerrar campos (por defecto comillas dobles)
        """
        self.delimiter = delimiter
        self.quotechar = quotechar
        self.encoding = 'utf-8-sig'  # UTF-8 con BOM para compatibilidad con Excel

    def exportar(self, datos: Dict[str, Any]) -> BytesIO:
        """
        Exporta la historia clínica a formato CSV

        Args:
            datos: Diccionario con la información completa

        Returns:
            BytesIO: Stream con el CSV generado

        Raises:
            ValueError: Si los datos son inválidos
        """
        # Validar datos
        self.validar_datos(datos)

        # Crear buffer de string
        string_buffer = StringIO()

        # Crear writer CSV
        writer = csv.writer(
            string_buffer,
            delimiter=self.delimiter,
            quotechar=self.quotechar,
            quoting=csv.QUOTE_MINIMAL
        )
        writer.writerow([
            "No. Historia Clínica", "Fecha Generación",
            "Propietario", "Documento", "Teléfono", "Email",
            "Mascota", "Especie", "Raza", "Sexo", "Peso (kg)", "Color", "Fecha Nacimiento"
        ])

        historia = datos["historia_clinica"]
        propietario = datos["propietario"]
        mascota = datos["mascota"]

        writer.writerow([
            historia.get('numero', 'N/A'),
            datetime.now().strftime("%d/%m/%Y %H:%M"),
            propietario.get("nombre_completo", "N/A"),
            propietario.get("numero_documento", "N/A"),
            propietario.get("telefono", "N/A"),
            propietario.get("email", "N/A"),
            mascota.get("nombre", "N/A"),
            mascota.get("especie", "N/A"),
            mascota.get("raza", "N/A"),
            mascota.get("sexo", "N/A"),  # ✅ CAMPO FALTANTE
            mascota.get("peso", "N/A"),  # ✅ CAMPO FALTANTE
            mascota.get("color", "N/A"),  # ✅ CAMPO FALTANTE
            mascota.get("fecha_nacimiento", "N/A")
        ])

        writer.writerow([])

        # Escribir secciones del CSV
        self._escribir_encabezado(writer, datos)
        writer.writerow([])  # Línea en blanco

        self._escribir_informacion_propietario(writer, datos)
        writer.writerow([])  # Línea en blanco

        self._escribir_informacion_mascota(writer, datos)
        writer.writerow([])  # Línea en blanco
        writer.writerow([])  # Línea en blanco

        self._escribir_consultas(writer, datos)

        # Convertir string a bytes
        csv_content = string_buffer.getvalue()
        byte_buffer = BytesIO(csv_content.encode(self.encoding))
        byte_buffer.seek(0)

        return byte_buffer

    def _escribir_encabezado(
            self,
            writer: csv.writer,
            datos: Dict[str, Any]
    ) -> None:
        """Escribe el encabezado del CSV"""
        historia = datos["historia_clinica"]

        writer.writerow(["HISTORIA CLÍNICA VETERINARIA"])
        writer.writerow([
            "No. Historia Clínica:",
            historia.get('numero', 'N/A')
        ])
        writer.writerow([
            "Fecha de generación:",
            datetime.now().strftime("%d/%m/%Y %H:%M")
        ])

    def _escribir_informacion_propietario(
            self,
            writer: csv.writer,
            datos: Dict[str, Any]
    ) -> None:
        """Escribe la información del propietario"""
        propietario = datos["propietario"]

        writer.writerow(["INFORMACIÓN DEL PROPIETARIO"])
        writer.writerow(["Campo", "Valor"])
        writer.writerow(["Nombre Completo", propietario.get("nombre_completo", "N/A")])
        writer.writerow(["Documento", propietario.get("numero_documento", "N/A")])
        writer.writerow(["Teléfono", propietario.get("telefono", "N/A")])
        writer.writerow(["Email", propietario.get("email", "N/A")])
        writer.writerow(["Dirección", propietario.get("direccion", "N/A")])

    def _escribir_informacion_mascota(
            self,
            writer: csv.writer,
            datos: Dict[str, Any]
    ) -> None:
        """Escribe la información de la mascota"""
        mascota = datos["mascota"]

        writer.writerow(["INFORMACIÓN DE LA MASCOTA"])
        writer.writerow(["Campo", "Valor"])
        writer.writerow(["Nombre", mascota.get("nombre", "N/A")])
        writer.writerow(["Especie", mascota.get("especie", "N/A")])
        writer.writerow(["Raza", mascota.get("raza", "N/A")])
        writer.writerow(["Sexo", mascota.get("sexo", "N/A")])
        writer.writerow(["Fecha de Nacimiento", mascota.get("fecha_nacimiento", "N/A")])
        writer.writerow(["Peso (kg)", mascota.get("peso", "N/A")])
        writer.writerow(["Color", mascota.get("color", "N/A")])

    def _escribir_consultas(
            self,
            writer: csv.writer,
            datos: Dict[str, Any]
    ) -> None:
        """Escribe el listado de consultas en formato tabular"""
        consultas = datos["consultas"]

        writer.writerow(["HISTORIAL DE CONSULTAS"])

        if not consultas or len(consultas) == 0:
            writer.writerow(["No hay consultas registradas"])
            return

        # Encabezados de la tabla de consultas
        headers = [
            "No.",
            "Fecha y Hora",
            "Veterinario",
            "Motivo",
            "Anamnesis",
            "Signos Vitales",
            "Diagnóstico",
            "Tratamiento",
            "Vacunas",
            "Observaciones"
        ]
        writer.writerow(headers)

        # Escribir cada consulta como una fila
        for idx, consulta in enumerate(consultas, 1):
            fila = [
                idx,
                consulta.get("fecha_hora", "N/A"),
                consulta.get("veterinario_nombre", "N/A"),
                consulta.get("motivo", "N/A"),
                consulta.get("anamnesis", "N/A"),
                consulta.get("signos_vitales", "N/A"),
                consulta.get("diagnostico", "N/A"),
                consulta.get("tratamiento", "N/A"),
                consulta.get("vacunas_aplicadas", "N/A"),
                consulta.get("observaciones", "N/A")
            ]
            writer.writerow(fila)

        # Pie de página
        writer.writerow([])
        writer.writerow([
            "Documento generado automáticamente por GDCV - "
            "Las historias clínicas no pueden ser eliminadas (RN10-1)"
        ])

    def obtener_extension(self) -> str:
        """Retorna la extensión del archivo CSV"""
        return "csv"

    def obtener_content_type(self) -> str:
        """Retorna el Content-Type para archivos CSV"""
        return "text/csv"