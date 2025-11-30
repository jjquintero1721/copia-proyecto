"""
Patrón Strategy - Implementación concreta para exportación a PDF
RNF-06: Interoperabilidad - Exportar información en formato PDF

Genera documentos PDF profesionales con la historia clínica completa
de una mascota, incluyendo consultas, tratamientos y vacunas.
"""

from typing import Any, Dict
from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, PageBreak, Image
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from app.services.export.export_strategy import IEstrategiaExportacion


class PDFExportStrategy(IEstrategiaExportacion):
    """
    Concrete Strategy - Exportación a formato PDF

    Genera un documento PDF completo y profesional con:
    - Encabezado con información de la clínica
    - Datos del propietario y mascota
    - Listado completo de consultas
    - Pie de página con fecha de generación
    """

    def __init__(self):
        """Inicializa la estrategia de exportación PDF"""
        self.pagesize = A4
        self.styles = getSampleStyleSheet()
        self._crear_estilos_personalizados()

    def _crear_estilos_personalizados(self) -> None:
        """Crea estilos personalizados para el PDF"""
        # Estilo para el título principal
        self.styles.add(ParagraphStyle(
            name='TituloPersonalizado',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Estilo para subtítulos
        self.styles.add(ParagraphStyle(
            name='SubtituloPersonalizado',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#34495E'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))

        # Estilo para texto normal
        self.styles.add(ParagraphStyle(
            name='NormalPersonalizado',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#2C3E50')
        ))

    def exportar(self, datos: Dict[str, Any]) -> BytesIO:
        """
        Exporta la historia clínica a formato PDF

        Args:
            datos: Diccionario con la información completa

        Returns:
            BytesIO: Stream con el PDF generado

        Raises:
            ValueError: Si los datos son inválidos
        """
        # Validar datos
        self.validar_datos(datos)

        # Crear buffer de memoria
        buffer = BytesIO()

        # Crear documento PDF
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.pagesize,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Construir contenido
        elementos = []
        elementos.extend(self._generar_encabezado(datos))
        elementos.append(Spacer(1, 0.3 * inch))
        elementos.extend(self._generar_informacion_propietario(datos))
        elementos.append(Spacer(1, 0.3 * inch))
        elementos.extend(self._generar_informacion_mascota(datos))
        elementos.append(Spacer(1, 0.4 * inch))
        elementos.extend(self._generar_consultas(datos))
        elementos.append(Spacer(1, 0.3 * inch))
        elementos.extend(self._generar_pie_pagina())

        # Construir PDF
        doc.build(elementos)

        # Resetear puntero del buffer
        buffer.seek(0)
        return buffer

    def _generar_encabezado(self, datos: Dict[str, Any]) -> list:
        """Genera el encabezado del PDF"""
        elementos = []

        # Título principal
        titulo = Paragraph(
            "HISTORIA CLÍNICA VETERINARIA",
            self.styles['TituloPersonalizado']
        )
        elementos.append(titulo)

        # Número de historia clínica
        historia = datos["historia_clinica"]
        numero_hc = Paragraph(
            f"<b>No. Historia Clínica:</b> {historia.get('numero', 'N/A')}",
            self.styles['NormalPersonalizado']
        )
        elementos.append(numero_hc)

        # Fecha de generación
        fecha_generacion = datetime.now().strftime("%d/%m/%Y %H:%M")
        fecha_para = Paragraph(
            f"<b>Fecha de generación:</b> {fecha_generacion}",
            self.styles['NormalPersonalizado']
        )
        elementos.append(fecha_para)

        return elementos

    def _generar_informacion_propietario(self, datos: Dict[str, Any]) -> list:
        """Genera la sección de información del propietario"""
        elementos = []
        propietario = datos["propietario"]

        # Subtítulo
        subtitulo = Paragraph(
            "INFORMACIÓN DEL PROPIETARIO",
            self.styles['SubtituloPersonalizado']
        )
        elementos.append(subtitulo)

        # Tabla con datos del propietario
        datos_tabla = [
            ["Nombre Completo:", propietario.get("nombre_completo", "N/A")],
            ["Documento:", propietario.get("numero_documento", "N/A")],
            ["Teléfono:", propietario.get("telefono", "N/A")],
            ["Email:", propietario.get("email", "N/A")],
        ]

        tabla = Table(datos_tabla, colWidths=[2 * inch, 4 * inch])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ECF0F1')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2C3E50')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6)
        ]))

        elementos.append(tabla)
        return elementos

    def _generar_informacion_mascota(self, datos: Dict[str, Any]) -> list:
        """Genera la sección de información de la mascota"""
        elementos = []
        mascota = datos["mascota"]

        # Subtítulo
        subtitulo = Paragraph(
            "INFORMACIÓN DE LA MASCOTA",
            self.styles['SubtituloPersonalizado']
        )
        elementos.append(subtitulo)

        # Tabla con datos de la mascota
        datos_tabla = [
            ["Nombre:", mascota.get("nombre", "N/A")],
            ["Especie:", mascota.get("especie", "N/A")],
            ["Raza:", mascota.get("raza", "N/A")],
            ["Sexo:", mascota.get("sexo", "N/A")],
            ["Fecha de Nacimiento:", mascota.get("fecha_nacimiento", "N/A")],
            ["Peso:", f"{mascota.get("peso", 'N/A')} kg"],
            ["Color:", mascota.get("color", "N/A")]
        ]

        tabla = Table(datos_tabla, colWidths=[2 * inch, 4 * inch])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ECF0F1')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2C3E50')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6)
        ]))

        elementos.append(tabla)
        return elementos

    def _generar_consultas(self, datos: Dict[str, Any]) -> list:
        """Genera la sección de consultas médicas"""
        elementos = []
        consultas = datos["consultas"]

        # Subtítulo
        subtitulo = Paragraph(
            "HISTORIAL DE CONSULTAS",
            self.styles['SubtituloPersonalizado']
        )
        elementos.append(subtitulo)

        if not consultas or len(consultas) == 0:
            elementos.append(Paragraph(
                "No hay consultas registradas",
                self.styles['NormalPersonalizado']
            ))
            return elementos

        # Generar una tabla por cada consulta
        for idx, consulta in enumerate(consultas, 1):
            elementos.append(Spacer(1, 0.2 * inch))

            # Encabezado de la consulta
            encabezado = Paragraph(
                f"<b>Consulta #{idx}</b> - {consulta.get('fecha_hora', 'N/A')}",
                self.styles['SubtituloPersonalizado']
            )
            elementos.append(encabezado)

            # Datos de la consulta
            datos_consulta = [
                ["Veterinario:", consulta.get("veterinario_nombre", "N/A")],
                ["Motivo:", consulta.get("motivo", "N/A")],
                ["Anamnesis:", consulta.get("anamnesis", "N/A")],
                ["Signos Vitales:", consulta.get("signos_vitales", "N/A")],
                ["Diagnóstico:", consulta.get("diagnostico", "N/A")],
                ["Tratamiento:", consulta.get("tratamiento", "N/A")],
                ["Vacunas:", consulta.get("vacunas_aplicadas", "N/A")],
                ["Observaciones:", consulta.get("observaciones", "N/A")]
            ]

            tabla_consulta = Table(datos_consulta, colWidths=[1.5 * inch, 4.5 * inch])
            tabla_consulta.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8F8F5')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2C3E50')),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#A9DFBF')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6)
            ]))

            elementos.append(tabla_consulta)

        return elementos

    def _generar_pie_pagina(self) -> list:
        """Genera el pie de página del documento"""
        elementos = []

        elementos.append(Spacer(1, 0.5 * inch))

        # Línea divisora
        pie_texto = Paragraph(
            "_" * 100,
            self.styles['NormalPersonalizado']
        )
        elementos.append(pie_texto)

        # Texto del pie
        pie_info = Paragraph(
            "<i>Este documento fue generado automáticamente por el Sistema de Gestión de Clínica Veterinaria (GDCV).<br/>"
            "RN10-1: Las historias clínicas no pueden ser eliminadas.<br/>"
            "RN10-2: Cada modificación registra fecha, hora y usuario responsable.</i>",
            self.styles['NormalPersonalizado']
        )
        elementos.append(pie_info)

        return elementos

    def obtener_extension(self) -> str:
        """Retorna la extensión del archivo PDF"""
        return "pdf"

    def obtener_content_type(self) -> str:
        """Retorna el Content-Type para archivos PDF"""
        return "application/pdf"