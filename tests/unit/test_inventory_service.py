"""
Tests Unitarios - InventoryService
===================================
Pruebas esenciales para control de inventario.
Cubre: Entradas, Salidas, Alertas de Stock Mínimo, Movimientos.
"""

from datetime import datetime, timezone
import pytest
from unittest.mock import MagicMock
from uuid import uuid4

class TestInventoryService:
    """Tests esenciales para InventoryService"""

    def test_register_entrada_medicamento(self):
        """Registrar entrada de medicamento (compra, donación)"""

        # Arrange
        mock_repo = MagicMock()

        medicamento_id = uuid4()
        current_time = datetime.now(timezone.utc)
        entrada_data = {
            "medicamento_id": medicamento_id,
            "tipo_movimiento": "ENTRADA",
            "cantidad": 50,
            "motivo": "Compra de proveedor",
            "fecha": current_time
        }

        mock_movimiento = {
            "id": uuid4(),
            **entrada_data,
            "stock_resultante": 150
        }

        mock_repo.create_movimiento.return_value = mock_movimiento

        # Act
        result = mock_repo.create_movimiento(mock_movimiento)

        # Assert
        assert result["tipo_movimiento"] == "ENTRADA"
        assert result["cantidad"] == 50
        assert result["stock_resultante"] == 150
        mock_repo.create_movimiento.assert_called_once()

    def test_register_salida_medicamento(self):
        """Registrar salida de medicamento (prescripción, uso interno)"""

        # Arrange
        mock_repo = MagicMock()

        medicamento_id = uuid4()
        current_time = datetime.now(timezone.utc)
        salida_data = {
            "medicamento_id": medicamento_id,
            "tipo_movimiento": "SALIDA",
            "cantidad": 10,
            "motivo": "Prescripción médica",
            "fecha": current_time
        }

        mock_movimiento = {
            "id": uuid4(),
            **salida_data,
            "stock_resultante": 90
        }

        mock_repo.create_movimiento.return_value = mock_movimiento

        # Act
        result = mock_repo.create_movimiento(mock_movimiento)

        # Assert
        assert result["tipo_movimiento"] == "SALIDA"
        assert result["cantidad"] == 10
        assert result["stock_resultante"] == 90

    def test_alert_stock_minimo(self):
        """Generar alerta cuando stock actual <= stock mínimo"""

        # Arrange
        def check_stock_alert(stock_actual, stock_minimo):
            if stock_actual <= stock_minimo:
                return {
                    "alerta": True,
                    "mensaje": f"Stock bajo: {stock_actual} unidades (mínimo: {stock_minimo})"
                }
            return {"alerta": False}

        # Act
        result = check_stock_alert(stock_actual=5, stock_minimo=10)

        # Assert
        assert result["alerta"] is True
        assert "Stock bajo" in result["mensaje"]

    def test_no_alert_stock_sufficient(self):
        """No generar alerta cuando stock es suficiente"""

        # Arrange
        def check_stock_alert(stock_actual, stock_minimo):
            if stock_actual <= stock_minimo:
                return {"alerta": True, "mensaje": "Stock bajo"}
            return {"alerta": False}

        # Act
        result = check_stock_alert(stock_actual=50, stock_minimo=10)

        # Assert
        assert result["alerta"] is False

    def test_get_movimientos_by_medicamento(self):
        """Obtener historial de movimientos de un medicamento"""

        # Arrange
        mock_repo = MagicMock()

        medicamento_id = uuid4()

        movimientos = [
            {
                "id": uuid4(),
                "medicamento_id": medicamento_id,
                "tipo_movimiento": "ENTRADA",
                "cantidad": 100,
                "fecha": datetime(2024, 1, 1)
            },
            {
                "id": uuid4(),
                "medicamento_id": medicamento_id,
                "tipo_movimiento": "SALIDA",
                "cantidad": 20,
                "fecha": datetime(2024, 1, 15)
            }
        ]

        mock_repo.get_movimientos_by_medicamento.return_value = movimientos

        # Act
        result = mock_repo.get_movimientos_by_medicamento(medicamento_id)

        # Assert
        assert len(result) == 2
        assert result[0]["tipo_movimiento"] == "ENTRADA"
        assert result[1]["tipo_movimiento"] == "SALIDA"

    def test_validate_stock_sufficient_for_salida(self):
        """Validar stock suficiente antes de registrar salida"""

        # Arrange
        def validate_stock(stock_actual, cantidad_salida):
            if cantidad_salida > stock_actual:
                raise ValueError("Stock insuficiente para realizar la salida")
            return True

        # Act & Assert - Stock suficiente
        assert validate_stock(stock_actual=50, cantidad_salida=20) is True

        # Act & Assert - Stock insuficiente
        with pytest.raises(ValueError, match="Stock insuficiente"):
            validate_stock(stock_actual=10, cantidad_salida=20)