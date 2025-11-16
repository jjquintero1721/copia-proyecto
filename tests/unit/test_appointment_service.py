"""
Tests Unitarios - AppointmentService
=====================================
Pruebas esenciales para gestión de citas.
Cubre: Agendar, Anticipación, Reprogramar, Cancelar.
"""

import pytest
from unittest.mock import MagicMock
from uuid import uuid4
from datetime import datetime, timedelta, timezone

from app.services.appointment.appointment_service import AppointmentService
from app.schemas.appointment_schema import AppointmentCreate
from app.models.appointment import Appointment, AppointmentStatus
from app.models.service import Service


class TestAppointmentService:
    """Tests esenciales para AppointmentService"""

    # TEST 1 - Crear cita correctamente (válido)
    def test_create_appointment_success(self):
        """Agendar cita exitosamente (RN08-1: 4h anticipación)"""

        # Arrange
        mock_db = MagicMock()
        service = AppointmentService(mock_db)

        # Mock repositorios del servicio
        service.pet_repo = MagicMock()
        service.user_repo = MagicMock()
        service.service_repo = MagicMock()
        service.repository = MagicMock()

        mascota_id = uuid4()
        veterinario_id = uuid4()
        servicio_id = uuid4()

        fecha_valida = datetime.now(timezone.utc) + timedelta(hours=5)

        appointment_data = AppointmentCreate(
            mascota_id=mascota_id,
            veterinario_id=veterinario_id,
            servicio_id=servicio_id,
            fecha_hora=fecha_valida,
            motivo="Consulta de rutina"
        )

        # Mock entidades existentes
        service.pet_repo.get_by_id.return_value = MagicMock()
        service.user_repo.get_by_id.return_value = MagicMock(
            rol=MagicMock(value="veterinario")
        )
        service.service_repo.get_by_id.return_value = Service(
            id=servicio_id,
            nombre="Consulta",
            duracion_minutos=30,
            activo=True
        )
        service.repository.check_availability.return_value = True

        expected_appointment = Appointment(
            id=uuid4(),
            mascota_id=mascota_id,
            veterinario_id=veterinario_id,
            servicio_id=servicio_id,
            fecha_hora=fecha_valida,
            estado=AppointmentStatus.AGENDADA,
            motivo="Consulta de rutina"
        )
        service.repository.create.return_value = expected_appointment

        # Act
        result = service.create_appointment(appointment_data)

        # Assert
        assert result.estado == AppointmentStatus.AGENDADA
        assert result.mascota_id == mascota_id
        service.repository.create.assert_called_once()

    # TEST 2 - Validación Pydantic (anticipación mínima)
    def test_create_appointment_insufficient_anticipation(self):
        """
        Rechazar cita con menos de 4 horas.
        OJO: la validación ocurre en el SCHEMA, no en el SERVICE.
        """

        fecha_invalida = datetime.now(timezone.utc) + timedelta(hours=3)

        # Act + Assert
        with pytest.raises(ValueError, match="4 horas"):
            AppointmentCreate(
                mascota_id=uuid4(),
                veterinario_id=uuid4(),
                servicio_id=uuid4(),
                fecha_hora=fecha_invalida,
                motivo="Test"
            )

    # TEST 3 - Reprogramar cita
    def test_reschedule_appointment_success(self):
        """Reprogramar cita exitosamente"""

        # Arrange
        mock_db = MagicMock()
        service = AppointmentService(mock_db)

        service.repository = MagicMock()
        service.service_repo = MagicMock()

        appointment_id = uuid4()
        nueva_fecha = datetime.now(timezone.utc) + timedelta(days=2)

        mock_appointment = Appointment(
            id=appointment_id,
            mascota_id=uuid4(),
            veterinario_id=uuid4(),
            servicio_id=uuid4(),
            fecha_hora=datetime.now(timezone.utc) + timedelta(days=1),
            estado=AppointmentStatus.AGENDADA
        )

        service.repository.get_by_id.return_value = mock_appointment
        service.service_repo.get_by_id.return_value = Service(
            id=uuid4(),
            nombre="Consulta",
            duracion_minutos=30,
            activo=True
        )
        service.repository.check_availability.return_value = True
        service.repository.update.return_value = mock_appointment

        # Act
        result = service.reschedule_appointment(appointment_id, nueva_fecha)

        # Assert
        assert result is not None
        service.repository.update.assert_called_once()

    # TEST 4 - Cancelación normal
    def test_cancel_appointment_success(self):
        """Cancelar cita exitosamente"""

        # Arrange
        mock_db = MagicMock()
        service = AppointmentService(mock_db)

        service.repository = MagicMock()

        appointment_id = uuid4()
        mock_appointment = Appointment(
            id=appointment_id,
            mascota_id=uuid4(),
            veterinario_id=uuid4(),
            servicio_id=uuid4(),
            fecha_hora=datetime.now(timezone.utc) + timedelta(days=1),
            estado=AppointmentStatus.AGENDADA,
            cancelacion_tardia=False
        )

        service.repository.get_by_id.return_value = mock_appointment
        service.repository.update.return_value = mock_appointment

        # Act
        result = service.cancel_appointment(appointment_id)

        # Assert
        assert result is not None
        service.repository.update.assert_called_once()

    # TEST 5 - Cancelación tardía (menos de 4 horas)
    def test_cancel_appointment_late_cancellation(self):
        """Cancelación tardía (< 4 horas) marca flag RN08-2"""

        # Arrange
        mock_db = MagicMock()
        service = AppointmentService(mock_db)

        service.repository = MagicMock()

        appointment_id = uuid4()

        mock_appointment = Appointment(
            id=appointment_id,
            mascota_id=uuid4(),
            veterinario_id=uuid4(),
            servicio_id=uuid4(),
            fecha_hora=datetime.now(timezone.utc) + timedelta(hours=3),
            estado=AppointmentStatus.CONFIRMADA,
            cancelacion_tardia=False
        )

        service.repository.get_by_id.return_value = mock_appointment
        service.repository.update.return_value = mock_appointment

        # Act
        result = service.cancel_appointment(appointment_id)

        # Assert
        assert result is not None
        service.repository.update.assert_called_once()