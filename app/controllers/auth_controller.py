"""
Controlador de Autenticación
Endpoints: Login y registro de usuarios
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.services.user_service import UserService
from app.schemas.user_schema import UserCreate, LoginRequest, LoginResponse, UserResponse
from app.utils.responses import success_response, error_response
from app.services.proxies import ProxyFactory


router = APIRouter()
logger = logging.getLogger(__name__)


class DuplicateResourceException(Exception):
    """Excepción para recursos duplicados"""
    pass


class ValidationException(Exception):
    """Excepción para errores de validación"""
    pass

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(
        user_data: UserCreate,
        db: Session = Depends(get_db)
):
    """
    Registra un nuevo usuario en el sistema
    """
    try:
        logger.info(f"📝 Intento de registro: {user_data.correo} (Rol: {user_data.rol.value})")

        service = ProxyFactory.create_user_service_with_auth(db)
        user = service.create_user(user_data)

        logger.info(f"✅ Usuario registrado exitosamente: {user.correo} (ID: {user.id})")

        return success_response(
            data=user.to_dict(),
            message="Usuario registrado exitosamente",
            status_code=status.HTTP_201_CREATED
        )

    except ValueError as exc:
        error_msg = str(exc)
        logger.warning(f"❌ Error de validación en registro: {error_msg}")

        # 409 CONFLICT para duplicados
        if "ya está registrado" in error_msg or "ya existe" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_msg
            )

        #  400 BAD REQUEST para otros errores de validación
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    except IntegrityError as exc:
        """
        IntegrityError (caso raro, ya que validamos antes)
        Pero puede ocurrir por race conditions
        """
        logger.error(f"❌ Error de integridad en registro: {str(exc.orig)}")

        error_msg = str(exc.orig).lower()

        if 'correo' in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El correo ya está registrado"
            )
        elif 'documento' in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El documento ya está registrado"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Recurso duplicado"
            )

    except Exception as exc:
        """
        Cualquier otro error inesperado
        """
        logger.error(f"❌ Error interno en registro: {str(exc)}", exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor. Por favor, contacte al administrador."
        )

@router.post("/login", response_model=dict)
async def login(
        credentials: LoginRequest,
        db: Session = Depends(get_db)
):
    """
    Autentica un usuario y retorna un token JWT
    """
    try:
        logger.info(f"🔑 Intento de login: {credentials.correo}")

        #  USAR PROXY en lugar de servicio directo
        service = ProxyFactory.create_user_service_with_auth(db)
        result = service.authenticate(credentials.correo, credentials.contrasena)

        if not result:
            logger.warning(f"❌ Credenciales incorrectas: {credentials.correo}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user, access_token = result
        logger.info(f"✅ Login exitoso: {user.correo} (Rol: {user.rol.value})")
        return success_response(
            data={
                "access_token": access_token,
                "token_type": "bearer",
                "usuario": user.to_dict()
            },
            message="Login exitoso"
        )

    except ValueError as exc:
        logger.warning(f"❌ Usuario desactivado: {credentials.correo}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc)
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"❌ Error interno en login: {str(exc)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el login: {str(exc)}"
        )