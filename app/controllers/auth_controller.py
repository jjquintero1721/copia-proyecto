"""
Controlador de Autenticación
Endpoints: Login y registro de usuarios
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.user_service import UserService
from app.schemas.user_schema import UserCreate, LoginRequest, LoginResponse, UserResponse
from app.utils.responses import success_response, error_response

router = APIRouter()


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(
        user_data: UserCreate,
        db: Session = Depends(get_db)
):
    """
    Registra un nuevo usuario en el sistema

    **Roles disponibles:**
    - superadmin: Acceso total al sistema
    - veterinario: Gestión de historias clínicas, citas, inventario
    - auxiliar: Apoyo en citas y triage
    - propietario: Solo mascotas y citas propias

    **Validaciones:**
    - Correo único (RN01)
    - Contraseña mínimo 8 caracteres, 1 número, 1 mayúscula
    - Teléfono opcional
    """
    try:
        service = UserService(db)
        user = service.create_user(user_data)

        return success_response(
            data=user.to_dict(),
            message="Usuario registrado exitosamente",
            status_code=status.HTTP_201_CREATED
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar usuario: {str(exc)}"
        )


@router.post("/login", response_model=dict)
async def login(
        credentials: LoginRequest,
        db: Session = Depends(get_db)
):
    """
    Autentica un usuario y retorna un token JWT

    **Uso del token:**
    - Incluir en header: `Authorization: Bearer <token>`
    - Válido por 30 minutos (configurable en .env)

    **Respuesta:**
    - access_token: Token JWT
    - token_type: Tipo de token (bearer)
    - usuario: Datos del usuario autenticado
    """
    try:
        service = UserService(db)
        result = service.authenticate(credentials.correo, credentials.contrasena)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user, access_token = result

        return success_response(
            data={
                "access_token": access_token,
                "token_type": "bearer",
                "usuario": user.to_dict()
            },
            message="Login exitoso"
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc)
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el login: {str(exc)}"
        )