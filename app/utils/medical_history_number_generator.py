"""
Generador de números de historia clínica
RF-04: Creación automática al registrar mascota
Formato: HC-YYYY-XXXX (ej: HC-2025-0001)
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.medical_history import MedicalHistory


class MedicalHistoryNumberGenerator:
    """
    Generador de números únicos para historias clínicas
    Formato: HC-YYYY-XXXX
    - HC: Prefijo fijo
    - YYYY: Año actual
    - XXXX: Número secuencial de 4 dígitos (reinicia cada año)
    """

    PREFIX = "HC"
    YEAR_LENGTH = 4
    SEQUENCE_LENGTH = 4

    @staticmethod
    def generate(db: Session) -> str:
        """
        Genera el siguiente número de historia clínica disponible

        Args:
            db: Sesión de base de datos

        Returns:
            str: Número de historia clínica con formato HC-YYYY-XXXX

        Example:
            >>> generator = MedicalHistoryNumberGenerator()
            >>> numero = generator.generate(db)
            >>> print(numero)  # HC-2025-0001
        """
        # Obtener año actual
        current_year = datetime.now(timezone.utc).year

        # Buscar el último número del año actual
        ultimo_numero = (
            db.query(MedicalHistory.numero)
            .filter(MedicalHistory.numero.like(f"{MedicalHistoryNumberGenerator.PREFIX}-{current_year}-%"))
            .order_by(MedicalHistory.numero.desc())
            .first()
        )

        if ultimo_numero:
            # Extraer el número secuencial del último registro
            # Formato: HC-2025-0001 -> extraer "0001"
            try:
                ultima_secuencia = int(ultimo_numero[0].split('-')[-1])
                nueva_secuencia = ultima_secuencia + 1
            except (ValueError, IndexError):
                # Si hay error al parsear, empezar desde 1
                nueva_secuencia = 1
        else:
            # No hay registros del año actual, empezar desde 1
            nueva_secuencia = 1

        # Formatear el número con padding de ceros
        numero_formateado = f"{MedicalHistoryNumberGenerator.PREFIX}-{current_year}-{nueva_secuencia:0{MedicalHistoryNumberGenerator.SEQUENCE_LENGTH}d}"

        return numero_formateado

    @staticmethod
    def validate_format(numero: str) -> bool:
        """
        Valida que un número de historia clínica tenga el formato correcto

        Args:
            numero: Número a validar

        Returns:
            bool: True si el formato es válido, False en caso contrario

        Example:
            >>> MedicalHistoryNumberGenerator.validate_format("HC-2025-0001")
            True
            >>> MedicalHistoryNumberGenerator.validate_format("HC-25-001")
            False
        """
        if not numero or not isinstance(numero, str):
            return False

        parts = numero.split('-')

        # Debe tener exactamente 3 partes: HC, YYYY, XXXX
        if len(parts) != 3:
            return False

        prefix, year, sequence = parts

        # Validar prefijo
        if prefix != MedicalHistoryNumberGenerator.PREFIX:
            return False

        # Validar año (4 dígitos)
        if not year.isdigit() or len(year) != MedicalHistoryNumberGenerator.YEAR_LENGTH:
            return False

        # Validar secuencia (4 dígitos)
        if not sequence.isdigit() or len(sequence) != MedicalHistoryNumberGenerator.SEQUENCE_LENGTH:
            return False

        return True

    @staticmethod
    def extract_year(numero: str) -> Optional[int]:
        """
        Extrae el año de un número de historia clínica

        Args:
            numero: Número de historia clínica

        Returns:
            int: Año extraído o None si el formato es inválido

        Example:
            >>> MedicalHistoryNumberGenerator.extract_year("HC-2025-0001")
            2025
        """
        if not MedicalHistoryNumberGenerator.validate_format(numero):
            return None

        try:
            year = int(numero.split('-')[1])
            return year
        except (ValueError, IndexError):
            return None

    @staticmethod
    def extract_sequence(numero: str) -> Optional[int]:
        """
        Extrae el número secuencial de un número de historia clínica

        Args:
            numero: Número de historia clínica

        Returns:
            int: Número secuencial o None si el formato es inválido

        Example:
            >>> MedicalHistoryNumberGenerator.extract_sequence("HC-2025-0001")
            1
        """
        if not MedicalHistoryNumberGenerator.validate_format(numero):
            return None

        try:
            sequence = int(numero.split('-')[2])
            return sequence
        except (ValueError, IndexError):
            return None