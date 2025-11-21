"""
Patrón Builder - Construcción paso a paso de historias clínicas
RF-04: Creación automática al registrar mascota
RF-07: Gestión de historias clínicas
RN10-1: Las historias no pueden eliminarse
Facilita la creación progresiva de historias clínicas con validaciones
"""

from typing import Optional
from uuid import UUID

from app.models.medical_history import MedicalHistory


class HistoriaClinicaBuilder:
    """
    Builder Pattern - Construcción paso a paso de historias clínicas

    Permite crear historias clínicas de forma progresiva, garantizando
    integridad de datos y cumplimiento de reglas de negocio.

    Ejemplo de uso:
        builder = HistoriaClinicaBuilder()
        historia = (builder
                   .set_mascota_id(mascota_id)
                   .set_numero("HC-2025-0001")
                   .set_observaciones_generales("Mascota con historial de alergias")
                   .build())
    """

    def __init__(self):
        """Inicializa el builder con una instancia vacía de MedicalHistory"""
        self._historia = MedicalHistory()

    def set_mascota_id(self, mascota_id: UUID) -> 'HistoriaClinicaBuilder':
        """
        Establece el ID de la mascota asociada a la historia clínica

        Args:
            mascota_id: UUID de la mascota

        Returns:
            Self para encadenamiento de métodos

        Raises:
            ValueError: Si mascota_id es None
        """
        if not mascota_id:
            raise ValueError("El ID de la mascota es obligatorio")

        self._historia.mascota_id = mascota_id
        return self

    def set_numero(self, numero: str) -> 'HistoriaClinicaBuilder':
        """
        Establece el número único de la historia clínica

        Args:
            numero: Número de historia clínica (formato: HC-YYYY-XXXX)

        Returns:
            Self para encadenamiento de métodos

        Raises:
            ValueError: Si el número es inválido o está vacío
        """
        if not numero or not isinstance(numero, str):
            raise ValueError("El número de historia clínica es obligatorio")

        numero_limpio = numero.strip()
        if len(numero_limpio) < 5:
            raise ValueError("El número de historia clínica debe tener al menos 5 caracteres")

        self._historia.numero = numero_limpio
        return self

    def set_observaciones_generales(
            self,
            observaciones: Optional[str]
    ) -> 'HistoriaClinicaBuilder':
        """
        Establece las observaciones generales de la historia clínica

        Args:
            observaciones: Notas generales (opcional)

        Returns:
            Self para encadenamiento de métodos

        Raises:
            ValueError: Si las observaciones son muy cortas (menos de 10 caracteres)
        """
        if observaciones:
            observaciones_limpia = observaciones.strip()
            if len(observaciones_limpia) < 10:
                raise ValueError(
                    "Las observaciones deben tener al menos 10 caracteres"
                )
            self._historia.notas = observaciones_limpia
        else:
            self._historia.notas = None

        return self

    def set_is_deleted(self, is_deleted: bool) -> 'HistoriaClinicaBuilder':
        """
        Establece el estado de eliminación lógica (RN10-1)

        Args:
            is_deleted: Estado de eliminación

        Returns:
            Self para encadenamiento de métodos

        Note:
            Según RN10-1, las historias clínicas NO deben eliminarse.
            Este método existe por compatibilidad del modelo, pero no
            debería usarse en operaciones normales.
        """
        self._historia.is_deleted = is_deleted
        return self

    def build(self) -> MedicalHistory:
        """
        Construye y retorna la historia clínica

        Valida que todos los campos obligatorios estén presentes antes
        de retornar la instancia.

        Returns:
            MedicalHistory: Instancia construida y validada

        Raises:
            ValueError: Si falta algún campo obligatorio o hay datos inválidos
        """
        # Validar campos obligatorios
        if not self._historia.mascota_id:
            raise ValueError(
                "La historia clínica debe estar asociada a una mascota"
            )

        if not self._historia.numero:
            raise ValueError(
                "El número de historia clínica es obligatorio"
            )

        # Validar formato del número (HC-YYYY-XXXX)
        if not self._historia.numero.startswith("HC-"):
            raise ValueError(
                "El número de historia clínica debe tener formato HC-YYYY-XXXX"
            )

        # Asegurar que is_deleted esté inicializado (RN10-1)
        if self._historia.is_deleted is None:
            self._historia.is_deleted = False

        return self._historia

    def reset(self) -> 'HistoriaClinicaBuilder':
        """
        Reinicia el builder para construir una nueva historia clínica

        Returns:
            Self para encadenamiento de métodos
        """
        self._historia = MedicalHistory()
        return self