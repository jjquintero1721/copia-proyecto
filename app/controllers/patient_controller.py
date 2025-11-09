"""
Punto de entrada principal de la aplicación FastAPI
Sistema de Gestión de Clínica Veterinaria (GDCV)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.security.dependencies import require_staff
from app.utils.responses import success_response

from app.schemas.owner_schema import OwnerCreate, OwnerResponse
from app.schemas.pet_schema import PetCreate, PetResponse

from app.commands.patient_commands import CreateOwnerCommand, CreatePetCommand

# Inicializa el enrutador de FastAPI para definir los endpoints relacionados con pacientes
router = APIRouter()


# ==================== ENDPOINT: CREAR PROPIETARIO ====================
@router.post("/owners", response_model=dict, status_code=201)
async def create_owner(
    payload: OwnerCreate,                    # Datos recibidos del cliente (validados con el schema)
    db: Session = Depends(get_db),           # Sesión de base de datos inyectada automáticamente
    current_user = Depends(require_staff),   # Verifica que el usuario actual tenga rol de staff
):
    try:
        # Crea un comando para registrar un nuevo propietario con los datos del payload
        cmd = CreateOwnerCommand(
            db=db,
            nombre=payload.nombre,
            correo=payload.correo,
            documento=payload.documento,
            telefono=payload.telefono,
        )
        # Ejecuta el comando (usa un servicio con decorador de auditoría)
        owner = cmd.execute()

        # Retorna una respuesta de éxito con los datos del propietario creado
        return success_response(
            message="Propietario registrado",
            data=OwnerResponse.model_validate(owner).model_dump(mode="json")
        )

    # Error de validación de datos o regla de negocio
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    # Error inesperado en el servidor o base de datos
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al registrar propietario: {str(exc)}")


# ==================== ENDPOINT: CREAR MASCOTA ====================
@router.post("/pets", response_model=dict, status_code=201)
async def create_pet(
    payload: PetCreate,                      # Datos recibidos del cliente (validados con el schema)
    db: Session = Depends(get_db),           # Sesión de base de datos inyectada automáticamente
    current_user = Depends(require_staff),   # Verifica que el usuario actual tenga rol de staff
):
    try:
        # Crea un comando para registrar una nueva mascota con los datos del payload
        cmd = CreatePetCommand(
            db=db,
            propietario_id=payload.propietario_id,
            nombre=payload.nombre,
            especie=payload.especie,
            raza=payload.raza,
            microchip=payload.microchip,
            fecha_nacimiento=payload.fecha_nacimiento,
        )
        # Ejecuta el comando (usa un servicio con decorador de auditoría)
        pet = cmd.execute()

        # Retorna una respuesta de éxito con los datos de la mascota creada
        return success_response(
            message="Mascota registrada",
            data=PetResponse.model_validate(pet).model_dump(mode="json")
        )

    # Error de validación de datos o regla de negocio
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    # Error inesperado en el servidor o base de datos
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al registrar mascota: {str(exc)}")
