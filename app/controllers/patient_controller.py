"""
Controlador de Pacientes (Mascotas y Propietarios)
RF-04: Registro de mascotas

✅ CORRECCIÓN ARQUITECTURAL:
- ELIMINADO endpoint POST /owners
- Los propietarios se crean automáticamente al registrar usuario con rol propietario
- Solo mantiene endpoint para crear mascotas
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.security.dependencies import require_staff
from app.utils.responses import success_response

from app.schemas.pet_schema import PetCreate, PetResponse
from app.commands.patient_commands import CreatePetCommand

router = APIRouter()


# ==================== ENDPOINT: CREAR MASCOTA ====================
@router.post("/pets", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_pet(
    payload: PetCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_staff),
):
    try:
        cmd = CreatePetCommand(
            db=db,
            propietario_id=payload.propietario_id,
            nombre=payload.nombre,
            especie=payload.especie,
            raza=payload.raza,
            microchip=payload.microchip,
            fecha_nacimiento=payload.fecha_nacimiento,
        )

        pet = cmd.execute()

        return success_response(
            message="Mascota registrada exitosamente",
            data=PetResponse.model_validate(pet).model_dump(mode="json"),
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
            detail=f"Error al registrar mascota: {str(exc)}"
        )