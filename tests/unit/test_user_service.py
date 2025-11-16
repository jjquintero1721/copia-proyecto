"""
Tests Unitarios - UserService
==============================
Pruebas esenciales para autenticación y gestión de usuarios.
Cubre: Registro, Login, Roles, Control de Acceso.
"""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.services.user_service import UserService
from app.schemas.user_schema import UserCreate, UserRoleEnum
from app.models.user import User, UserRole


class TestUserService:
    """Tests esenciales para UserService"""

    def test_create_user_success(self):
        """Test: Registrar usuario exitosamente"""

        # Arrange
        mock_db = MagicMock()
        mock_repo = MagicMock()
        mock_repo.exists_by_correo.return_value = False

        user_data = UserCreate(
            nombre="Test User",
            correo="test@example.com",
            telefono="+573001234567",
            contrasena="Password123",
            rol=UserRoleEnum.PROPIETARIO
        )

        expected_user = User(
            id=uuid4(),
            nombre="Test User",
            correo="test@example.com",
            rol=UserRole.PROPIETARIO,
            activo=True
        )

        # Apagar el __init__ real del servicio
        with patch.object(UserService, '__init__', lambda x, y: None):
            service = UserService(mock_db)
            service.repository = mock_repo

            # Agregar factories manualmente
            service._factories = {
                "propietario": MagicMock()
            }

            # Simular factory
            service._factories["propietario"].create_user.return_value = expected_user
            mock_repo.create.return_value = expected_user

            # Act
            result = service.create_user(user_data)

            # Assert
            assert result.correo == "test@example.com"
            mock_repo.exists_by_correo.assert_called_once()

    def test_create_user_duplicate_email(self):
        """Test: Rechazar correo duplicado (RN01)"""

        # Arrange
        mock_db = MagicMock()
        mock_repo = MagicMock()
        mock_repo.exists_by_correo.return_value = True

        user_data = UserCreate(
            nombre="Test User",
            correo="duplicate@example.com",
            telefono="+573001234567",
            contrasena="Password123",
            rol=UserRoleEnum.PROPIETARIO
        )

        with patch.object(UserService, '__init__', lambda x, y: None):
            service = UserService(mock_db)
            service.repository = mock_repo

            # Act & Assert
            with pytest.raises(ValueError, match="correo.*registrado"):
                service.create_user(user_data)

    def test_authenticate_success(self):
        """Test: Login exitoso genera token JWT"""

        # Arrange
        mock_db = MagicMock()
        mock_repo = MagicMock()

        mock_user = User(
            id=uuid4(),
            nombre="Test User",
            correo="test@example.com",
            contrasena_hash="hashed_password",
            rol=UserRole.PROPIETARIO,
            activo=True
        )

        mock_repo.get_by_correo.return_value = mock_user

        with patch.object(UserService, '__init__', lambda x, y: None):
            service = UserService(mock_db)
            service.repository = mock_repo

            with patch('app.services.user_service.verify_password', return_value=True):
                with patch('app.services.user_service.create_access_token', return_value="fake_jwt_token"):
                    # Act
                    result = service.authenticate("test@example.com", "Password123")

                    # Assert
                    assert result is not None
                    user, token = result
                    assert user.correo == "test@example.com"
                    assert token == "fake_jwt_token"

    def test_authenticate_wrong_password(self):
        """Test: Login con contraseña incorrecta retorna None"""

        # Arrange
        mock_db = MagicMock()
        mock_repo = MagicMock()

        mock_user = User(
            id=uuid4(),
            nombre="Test User",
            correo="test@example.com",
            contrasena_hash="hashed_password",
            rol=UserRole.PROPIETARIO,
            activo=True
        )

        mock_repo.get_by_correo.return_value = mock_user

        with patch.object(UserService, '__init__', lambda x, y: None):
            service = UserService(mock_db)
            service.repository = mock_repo

            with patch('app.services.user_service.verify_password', return_value=False):
                # Act
                result = service.authenticate("test@example.com", "WrongPassword")

                # Assert
                assert result is None

    def test_authenticate_inactive_user(self):
        """Test: Usuario inactivo no puede autenticarse"""

        # Arrange
        mock_db = MagicMock()
        mock_repo = MagicMock()

        mock_user = User(
            id=uuid4(),
            nombre="Inactive User",
            correo="inactive@example.com",
            contrasena_hash="hashed_password",
            rol=UserRole.PROPIETARIO,
            activo=False
        )

        mock_repo.get_by_correo.return_value = mock_user

        with patch.object(UserService, '__init__', lambda x, y: None):
            service = UserService(mock_db)
            service.repository = mock_repo

            # Act & Assert
            with pytest.raises(ValueError, match="desactivado"):
                service.authenticate("inactive@example.com", "Password123")

    def test_get_user_by_id_success(self):
        """Test: Obtener usuario por ID"""

        # Arrange
        mock_db = MagicMock()
        mock_repo = MagicMock()

        user_id = uuid4()

        mock_user = User(
            id=user_id,
            nombre="Test User",
            correo="test@example.com",
            rol=UserRole.PROPIETARIO,
            activo=True
        )

        mock_repo.get_by_id.return_value = mock_user

        with patch.object(UserService, '__init__', lambda x, y: None):
            service = UserService(mock_db)
            service.repository = mock_repo

            # Act
            result = service.get_user_by_id(user_id)

            # Assert
            assert result is not None
            assert result.id == user_id
            mock_repo.get_by_id.assert_called_once_with(user_id)

    def test_get_user_by_id_not_found(self):
        """Test: Usuario no encontrado retorna None"""

        # Arrange
        mock_db = MagicMock()
        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = None

        with patch.object(UserService, '__init__', lambda x, y: None):
            service = UserService(mock_db)
            service.repository = mock_repo

            #Se usa uuid4() para crear un ID aleatorio y probar cómo responde el servicio cuando el usuario no existe
            # Act
            result = service.get_user_by_id(uuid4())

            # Assert
            assert result is None