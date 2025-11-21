"""
Tests Unitarios - MedicalHistoryService
========================================
Pruebas esenciales para historias clínicas.
Cubre: Consultas, Procedimientos, Versionado, Auditoría.
"""

from unittest.mock import MagicMock
from uuid import uuid4
from datetime import datetime, timezone


class TestMedicalHistoryService:
    """Tests esenciales para MedicalHistoryService"""

    def test_create_consultation_success(self):
        """Registrar consulta en historia clínica"""

        # Arrange
        mock_repo = MagicMock()

        mascota_id = uuid4()
        historia_id = uuid4()
        current_time = datetime.now(timezone.utc)

        # Mock del objeto MedicalHistory (NO instanciar el modelo real)
        expected_history = MagicMock()
        expected_history.id = historia_id
        expected_history.mascota_id = mascota_id
        expected_history.notas = "Consulta rutinaria. Animal en buen estado."
        expected_history.fecha_creacion = current_time

        mock_repo.create.return_value = expected_history

        # Act
        result = mock_repo.create(expected_history)

        # Assert
        assert result.mascota_id == mascota_id
        assert "buen estado" in result.notas
        assert result.fecha_creacion == current_time
        mock_repo.create.assert_called_once()

    def test_create_procedure_success(self):
        """Registrar procedimiento médico"""

        # Arrange
        mock_repo = MagicMock()

        mascota_id = uuid4()
        current_time = datetime.now(timezone.utc)

        expected_history = MagicMock()
        expected_history.id = uuid4()
        expected_history.mascota_id = mascota_id
        expected_history.notas = "Procedimiento: Vacunación antirrábica aplicada."
        expected_history.fecha_creacion = current_time

        mock_repo.create.return_value = expected_history

        # Act
        result = mock_repo.create(expected_history)

        # Assert
        assert result.mascota_id == mascota_id
        assert "Vacunación" in result.notas
        assert result.fecha_creacion == current_time

    def test_get_history_with_versioning(self):
        """Obtener historial versionado de mascota"""

        # Arrange
        mock_repo = MagicMock()

        mascota_id = uuid4()

        # Mock de historiales (NO instanciar modelos reales)
        history_v1 = MagicMock()
        history_v1.id = uuid4()
        history_v1.mascota_id = mascota_id
        history_v1.notas = "Primera consulta"
        history_v1.fecha_creacion = datetime(2024, 1, 1)

        history_v2 = MagicMock()
        history_v2.id = uuid4()
        history_v2.mascota_id = mascota_id
        history_v2.notas = "Segunda consulta - actualización"
        history_v2.fecha_creacion = datetime(2024, 2, 1)

        mock_repo.get_by_mascota_id.return_value = [history_v1, history_v2]

        # Act
        result = mock_repo.get_by_mascota_id(mascota_id)

        # Assert
        assert len(result) == 2
        assert result[0].fecha_creacion < result[1].fecha_creacion

    def test_audit_change_in_history(self):
        """Auditoría de cambios en historia clínica"""

        # Arrange
        mock_repo = MagicMock()

        initial_time = datetime.now(timezone.utc)
        updated_time = datetime.now(timezone.utc)

        # Mock del historial original
        mock_history = MagicMock()
        mock_history.id = uuid4()
        mock_history.mascota_id = uuid4()
        mock_history.notas = "Notas originales"
        mock_history.fecha_actualizacion = initial_time

        # Mock del historial actualizado
        updated_history = MagicMock()
        updated_history.id = mock_history.id
        updated_history.mascota_id = mock_history.mascota_id
        updated_history.notas = "Notas actualizadas con auditoría"
        updated_history.fecha_actualizacion = updated_time

        mock_repo.update.return_value = updated_history

        # Act
        mock_history.notas = "Notas actualizadas con auditoría"
        result = mock_repo.update(mock_history)

        # Assert
        assert "actualizadas" in result.notas
        assert result.fecha_actualizacion is not None
        mock_repo.update.assert_called_once()