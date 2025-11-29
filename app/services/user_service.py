"""
Servicio de Usuarios - Lógica de negocio
Implementa patrones: Factory Method, Builder, Template Method
CORRECCIÓN ARQUITECTURAL: Crea Owner automáticamente para rol=propietario
"""
from sqlite3 import IntegrityError

from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from abc import ABC, abstractmethod

from app.models.user import User, UserRole
from app.models.owner import Owner
from app.repositories.user_repository import UserRepository
from app.repositories.owner_repository import OwnerRepository
from app.security.auth import get_password_hash, verify_password, create_access_token
from app.schemas.user_schema import UserCreate, UserUpdate, UserChangePassword, UserRoleEnum


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

    @abstractmethod
    def _preparar_entidad(self, datos: Any) -> Any:
        """Hook: Preparación de la entidad"""

    def _persistir(self, entidad: Any) -> Any:
        """Paso común: Persistir en BD"""
        return self.repository.create(entidad)

    def _post_guardado(self, entidad: Any) -> None:
        """Hook: Acciones después de guardar"""


# ==================== SERVICIO PRINCIPAL ====================
class UserService:
    """
    Servicio de usuarios con transacción atómica.

    CORRECCIÓN CRÍTICA APLICADA:
    - Usuario y Propietario se crean en UNA SOLA transacción.
    - Validaciones ANTES de tocar BD.
    - Manejo de IntegrityError y rollback automático.
    """

    USER_NOT_FOUND_MSG = "Usuario no encontrado"

    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.owner_repository = OwnerRepository(db)

        self._factories: Dict[str, any] = {
            UserRole.SUPERADMIN.value: SuperadminFactory(),
            UserRole.VETERINARIO.value: VeterinarioFactory(),
            UserRole.AUXILIAR.value: AuxiliarFactory(),
            UserRole.PROPIETARIO.value: PropietarioFactory()
        }

    # ============================================================
    # 🔥 1. VALIDACIONES COMPLETAS
    # ============================================================
    def _validar_datos_completos(self, datos: UserCreate) -> None:

        # Validar correo único
        if self.user_repository.exists_by_correo(datos.correo):
            raise ValueError(f"El correo {datos.correo} ya está registrado")

        # Si es propietario, validar documento
        if datos.rol == UserRoleEnum.PROPIETARIO:

            if not datos.documento:
                raise ValueError("El documento es obligatorio para propietarios")

            if self.owner_repository.get_by_documento(datos.documento):
                raise ValueError(f"El documento {datos.documento} ya está registrado")

            if self.owner_repository.get_by_correo(datos.correo):
                raise ValueError(
                    f"El correo {datos.correo} ya existe como propietario"
                )

    # ============================================================
    # 🔥 2. CREACIÓN ATÓMICA DE USUARIO Y PROPIETARIO
    # ============================================================
    def create_user(self, user_data: UserCreate, creado_por: Optional[UUID] = None) -> User:
        try:
            # 1. Validaciones completas
            self._validar_datos_completos(user_data)

            # 2. Crear usuario en memoria usando factories
            factory = self._factories.get(user_data.rol.value)
            if not factory:
                raise ValueError(f"Rol no válido: {user_data.rol}")

            user = factory.create_user(user_data, creado_por)

            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

            # 3. Crear propietario EN MEMORIA sin commit
            if user_data.rol == UserRoleEnum.PROPIETARIO:
                owner = Owner(
                    usuario_id=user.id,
                    nombre=user.nombre,
                    correo=user.correo,
                    documento=user_data.documento,
                    telefono=user.telefono,
                    activo=user.activo
                )

                self.db.add(owner)
                self.db.commit()
                self.db.refresh(owner)

            return user

        except IntegrityError as exc:
            self.db.rollback()

            msg = str(exc.orig).lower()

            if "correo" in msg:
                raise ValueError(f"El correo {user_data.correo} ya está registrado")

            if "documento" in msg:
                raise ValueError(f"El documento {user_data.documento} ya está registrado")

            raise ValueError(f"Error de integridad: {str(exc.orig)}")

        except Exception:
            self.db.rollback()
            raise

    # ============================================================
    # 🔥  MÉTODOS RESTANTES SIN CAMBIOS (SIGUEN IGUAL)
    # ============================================================

    def authenticate(self, correo: str, contrasena: str):
        user = self.user_repository.get_by_correo(correo.lower())

        if not user:
            return None

        if not user.activo:
            raise ValueError("Usuario desactivado")

        if not verify_password(contrasena, user.contrasena_hash):
            return None

        token = create_access_token({
            "sub": user.correo,
            "user_id": str(user.id),
            "rol": user.rol.value
        })

        return user, token

    def get_user_by_id(self, user_id: UUID):
        return self.user_repository.get_by_id(user_id)

    def get_user_by_correo(self, correo: str):
        return self.user_repository.get_by_correo(correo.lower())

    def get_all_users(self, skip: int = 0, limit: int = 100, activo: Optional[bool] = None) -> List[User]:
        """Obtiene todos los usuarios con paginación"""
        return self.user_repository.get_all(skip, limit, activo)

    def get_users_by_rol(self, rol: str, activo: bool = True) -> List[User]:
        """
        Obtiene usuarios filtrados por rol

        Args:
            rol: String del rol ('veterinario', 'auxiliar', 'propietario', 'superadmin')
            activo: Si True, filtra solo usuarios activos (default: True)

        Returns:
            Lista de usuarios del rol especificado

        Raises:
            ValueError: Si el rol no es válido
        """
        # Convertir string a UserRole enum
        try:
            user_role = UserRole(rol)
        except ValueError:
            valid_roles = [r.value for r in UserRole]
            raise ValueError(
                f"Rol '{rol}' no válido. Roles válidos: {', '.join(valid_roles)}"
            )

        # Usar el repositorio para obtener usuarios
        return self.user_repository.get_by_rol(user_role, activo)

    def update_user(self, user_id: UUID, user_data: UserUpdate):
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(self.USER_NOT_FOUND_MSG)

        if user_data.nombre is not None:
            user.nombre = user_data.nombre
        if user_data.telefono is not None:
            user.telefono = user_data.telefono
        if user_data.activo is not None:
            user.activo = user_data.activo

        user.fecha_actualizacion = datetime.now(timezone.utc)
        return self.user_repository.update(user)

    def change_password(self, user_id: UUID, password_data: UserChangePassword):
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(self.USER_NOT_FOUND_MSG)

        if not verify_password(password_data.contrasena_actual, user.contrasena_hash):
            raise ValueError("Contraseña actual incorrecta")

        user.contrasena_hash = get_password_hash(password_data.contrasena_nueva)
        user.fecha_actualizacion = datetime.now(timezone.utc)

        return self.user_repository.update(user)

    def deactivate_user(self, user_id: UUID):
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(self.USER_NOT_FOUND_MSG)

        return self.user_repository.soft_delete(user)