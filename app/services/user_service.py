"""
Servicio de Usuarios - Lógica de negocio
Implementa patrones: Factory Method, Builder, Template Method
"""

from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from abc import ABC, abstractmethod

from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.security.auth import get_password_hash, verify_password, create_access_token
from app.schemas.user_schema import UserCreate, UserUpdate, UserChangePassword


# ==================== PATRÓN BUILDER ====================
class UserBuilder:
    """
    Builder Pattern - Construcción paso a paso de usuarios
    Facilita la creación de usuarios con validaciones
    """

    def __init__(self):
        self._user = User()

    def set_nombre(self, nombre: str) -> 'UserBuilder':
        self._user.nombre = nombre
        return self

    def set_correo(self, correo: str) -> 'UserBuilder':
        self._user.correo = correo.lower()
        return self

    def set_telefono(self, telefono: Optional[str]) -> 'UserBuilder':
        self._user.telefono = telefono
        return self

    def set_contrasena(self, contrasena: str) -> 'UserBuilder':
        self._user.contrasena_hash = get_password_hash(contrasena)
        return self

    def set_rol(self, rol: UserRole) -> 'UserBuilder':
        self._user.rol = rol
        return self

    def set_activo(self, activo: bool) -> 'UserBuilder':
        self._user.activo = activo
        return self

    def set_creado_por(self, usuario_id: Optional[UUID]) -> 'UserBuilder':
        self._user.creado_por = usuario_id
        return self

    def build(self) -> User:
        """Construye y retorna el usuario"""
        return self._user


# ==================== PATRÓN FACTORY METHOD ====================
class UserFactory(ABC):
    """
    Factory Method Pattern - Fábrica abstracta de usuarios
    """

    @abstractmethod
    def create_user(self, data: UserCreate, creado_por: Optional[UUID] = None) -> User:
        """Método factory para crear usuarios"""
        pass

    def _build_base_user(self, data: UserCreate, creado_por: Optional[UUID]) -> User:
        """Método auxiliar para construir usuario base usando Builder"""
        builder = UserBuilder()
        return (builder
                .set_nombre(data.nombre)
                .set_correo(data.correo)
                .set_telefono(data.telefono)
                .set_contrasena(data.contrasena)
                .set_rol(UserRole(data.rol.value))
                .set_activo(True)
                .set_creado_por(creado_por)
                .build())


class SuperadminFactory(UserFactory):
    """Factory para crear superadministradores"""

    def create_user(self, data: UserCreate, creado_por: Optional[UUID] = None) -> User:
        user = self._build_base_user(data, creado_por)
        user.rol = UserRole.SUPERADMIN
        return user


class VeterinarioFactory(UserFactory):
    """Factory para crear veterinarios"""

    def create_user(self, data: UserCreate, creado_por: Optional[UUID] = None) -> User:
        user = self._build_base_user(data, creado_por)
        user.rol = UserRole.VETERINARIO
        return user


class AuxiliarFactory(UserFactory):
    """Factory para crear auxiliares"""

    def create_user(self, data: UserCreate, creado_por: Optional[UUID] = None) -> User:
        user = self._build_base_user(data, creado_por)
        user.rol = UserRole.AUXILIAR
        return user


class PropietarioFactory(UserFactory):
    """Factory para crear propietarios"""

    def create_user(self, data: UserCreate, creado_por: Optional[UUID] = None) -> User:
        user = self._build_base_user(data, creado_por)
        user.rol = UserRole.PROPIETARIO
        return user


# ==================== PATRÓN TEMPLATE METHOD ====================
class BaseCRUDService(ABC):
    """
    Template Method Pattern - Clase base para servicios CRUD
    Define el esqueleto de operaciones CRUD con pasos personalizables
    """

    def __init__(self, repository: UserRepository):
        self.repository = repository

    def guardar(self, datos: Any) -> Any:
        """Template Method - Define el flujo de guardado"""
        # 1. Validar
        self._validar_datos(datos)

        # 2. Preparar entidad
        entidad = self._preparar_entidad(datos)

        # 3. Guardar
        entidad_guardada = self._persistir(entidad)

        # 4. Post-proceso (notificaciones, auditoría)
        self._post_guardado(entidad_guardada)

        return entidad_guardada

    @abstractmethod
    def _validar_datos(self, datos: Any) -> None:
        """Hook: Validación específica de cada servicio"""
        pass

    @abstractmethod
    def _preparar_entidad(self, datos: Any) -> Any:
        """Hook: Preparación de la entidad"""
        pass

    def _persistir(self, entidad: Any) -> Any:
        """Paso común: Persistir en BD"""
        return self.repository.create(entidad)

    def _post_guardado(self, entidad: Any) -> None:
        """Hook: Acciones después de guardar"""
        pass


# ==================== SERVICIO PRINCIPAL ====================
class UserService(BaseCRUDService):
    """
    Servicio principal de usuarios
    Implementa Template Method y coordina las factories
    """

    def __init__(self, db: Session):
        self.db = db
        repository = UserRepository(db)
        super().__init__(repository)

        # Registro de factories por rol
        self._factories: Dict[str, UserFactory] = {
            UserRole.SUPERADMIN.value: SuperadminFactory(),
            UserRole.VETERINARIO.value: VeterinarioFactory(),
            UserRole.AUXILIAR.value: AuxiliarFactory(),
            UserRole.PROPIETARIO.value: PropietarioFactory()
        }

    def _validar_datos(self, datos: UserCreate) -> None:
        """Validación de datos de usuario"""
        # RN01: Validar correo único
        if self.repository.exists_by_correo(datos.correo):
            raise ValueError(f"El correo {datos.correo} ya está registrado")

    def _preparar_entidad(self, datos: UserCreate, creado_por: Optional[UUID] = None) -> User:
        """Preparación de usuario usando Factory Method"""
        factory = self._factories.get(datos.rol.value)
        if not factory:
            raise ValueError(f"Rol no válido: {datos.rol}")

        return factory.create_user(datos, creado_por)

    def _post_guardado(self, entidad: User) -> None:
        """Post-proceso después de guardar usuario"""
        # Aquí se pueden agregar: notificaciones, auditoría, etc.
        pass

    def create_user(self, user_data: UserCreate, creado_por: Optional[UUID] = None) -> User:
        """Crea un nuevo usuario usando el Template Method"""
        self._validar_datos(user_data)
        user = self._preparar_entidad(user_data, creado_por)
        return self._persistir(user)

    def authenticate(self, correo: str, contrasena: str) -> Optional[tuple[User, str]]:
        """
        Autentica un usuario y genera token JWT
        Retorna: (usuario, token) si es exitoso, None si falla
        """
        user = self.repository.get_by_correo(correo.lower())

        if not user:
            return None

        if not user.activo:
            raise ValueError("Usuario desactivado")

        if not verify_password(contrasena, user.contrasena_hash):
            return None

        # Crear token JWT
        token_data = {
            "sub": user.correo,
            "user_id": str(user.id),
            "rol": user.rol.value
        }
        access_token = create_access_token(token_data)

        return user, access_token

    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Obtiene un usuario por ID"""
        return self.repository.get_by_id(user_id)

    def get_user_by_correo(self, correo: str) -> Optional[User]:
        """Obtiene un usuario por correo"""
        return self.repository.get_by_correo(correo.lower())

    def get_all_users(self, skip: int = 0, limit: int = 100, activo: Optional[bool] = None) -> List[User]:
        """Obtiene todos los usuarios con paginación"""
        return self.repository.get_all(skip, limit, activo)

    def update_user(self, user_id: UUID, user_data: UserUpdate) -> User:
        """Actualiza un usuario existente"""
        user = self.repository.get_by_id(user_id)
        if not user:
            raise ValueError("Usuario no encontrado")

        # Actualizar solo campos proporcionados
        if user_data.nombre is not None:
            user.nombre = user_data.nombre
        if user_data.telefono is not None:
            user.telefono = user_data.telefono
        if user_data.activo is not None:
            user.activo = user_data.activo

        user.fecha_actualizacion = datetime.utcnow()

        return self.repository.update(user)

    def change_password(self, user_id: UUID, password_data: UserChangePassword) -> User:
        """Cambia la contraseña de un usuario"""
        user = self.repository.get_by_id(user_id)
        if not user:
            raise ValueError("Usuario no encontrado")

        # Verificar contraseña actual
        if not verify_password(password_data.contrasena_actual, user.contrasena_hash):
            raise ValueError("Contraseña actual incorrecta")

        # Establecer nueva contraseña
        user.contrasena_hash = get_password_hash(password_data.contrasena_nueva)
        user.fecha_actualizacion = datetime.utcnow()

        return self.repository.update(user)

    def deactivate_user(self, user_id: UUID) -> User:
        """Desactiva un usuario (borrado lógico)"""
        user = self.repository.get_by_id(user_id)
        if not user:
            raise ValueError("Usuario no encontrado")

        return self.repository.soft_delete(user)

    def search_users(self, search_term: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Busca usuarios por nombre o correo"""
        return self.repository.search(search_term, skip, limit)

    def get_users_by_rol(self, rol: str, activo: bool = True) -> List[User]:
        """Obtiene usuarios por rol"""
        try:
            user_role = UserRole(rol)
            return self.repository.get_by_rol(user_role, activo)
        except ValueError:
            raise ValueError(f"Rol no válido: {rol}")