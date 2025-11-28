"""
Controlador de Pacientes (Mascotas y Propietarios) - ACTUALIZADO
RF-04: Registro de mascotas
NUEVOS ENDPOINTS: Consulta de mascotas y propietarios

Endpoints:
- POST /pets - Crear mascota
- GET /pets - Obtener todas las mascotas (paginado)
- GET /pets/dogs - Obtener todos los perros (paginado)
- GET /pets/cats - Obtener todos los gatos (paginado)
- GET /pets/owner/{owner_id} - Obtener mascotas por propietario
- GET /owners - Obtener todos los propietarios (paginado)
- GET /owners/{owner_id} - Obtener propietario específico con sus mascotas
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
import math

from app.database import get_db
from app.security.dependencies import require_staff, get_current_active_user
from app.utils.responses import success_response

from app.schemas.pet_schema import (
    PetCreate,
    PetResponse,
    PetWithOwnerResponse,
    PetListResponse
)
from app.schemas.owner_schema import (
    OwnerWithPetsResponse,
    OwnerListResponse
)
from app.commands.patient_commands import CreatePetCommand
from app.repositories.pet_repository import PetRepository
from app.repositories.owner_repository import OwnerRepository

router = APIRouter()


# ==================== ENDPOINTS DE MASCOTAS ====================
MSG_NO_PAG = "Número de página (mínimo 1)"
MSG_TAM_PAG = "Tamaño de página (1-100)"
MSG_ESTADO = "Filtrar por estado activo"


@router.post("/pets", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_pet(
    payload: PetCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff),
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
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar mascota: {str(exc)}"
        ) from exc


@router.get("/pets", response_model=dict, status_code=status.HTTP_200_OK)
async def get_all_pets(
    page: int = Query(1, ge=1, description=MSG_NO_PAG),
    page_size: int = Query(10, ge=1, le=100, description=MSG_TAM_PAG),
    activo: Optional[bool] = Query(True, description=MSG_ESTADO),
    db: Session = Depends(get_db),
    current_user=Depends(require_staff),
):

    try:
        pet_repo = PetRepository(db)

        # Calcular skip para paginación
        skip = (page - 1) * page_size

        # Obtener mascotas y total
        pets = pet_repo.get_all(skip=skip, limit=page_size, activo=activo)
        total = pet_repo.count_all(activo=activo)

        # Calcular total de páginas
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        # Construir respuesta
        response_data = PetListResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            pets=[PetWithOwnerResponse.model_validate(pet) for pet in pets]
        )

        return success_response(
            message="Mascotas obtenidas exitosamente",
            data=response_data.model_dump(mode="json"),
            status_code=status.HTTP_200_OK
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener mascotas: {str(exc)}"
        ) from exc


@router.get("/pets/dogs", response_model=dict, status_code=status.HTTP_200_OK)
async def get_all_dogs(
    page: int = Query(1, ge=1, description=MSG_NO_PAG),
    page_size: int = Query(10, ge=1, le=100, description=MSG_TAM_PAG),
    activo: Optional[bool] = Query(True, description=MSG_ESTADO),
    db: Session = Depends(get_db),
    current_user=Depends(require_staff),
):

    try:
        pet_repo = PetRepository(db)

        skip = (page - 1) * page_size

        dogs = pet_repo.get_by_species("perro", skip=skip, limit=page_size, activo=activo)
        total = pet_repo.count_by_species("perro", activo=activo)

        total_pages = math.ceil(total / page_size) if total > 0 else 1

        response_data = PetListResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            pets=[PetWithOwnerResponse.model_validate(dog) for dog in dogs]
        )

        return success_response(
            message="Perros obtenidos exitosamente",
            data=response_data.model_dump(mode="json"),
            status_code=status.HTTP_200_OK
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener perros: {str(exc)}"
        ) from exc


@router.get("/pets/cats", response_model=dict, status_code=status.HTTP_200_OK)
async def get_all_cats(
    page: int = Query(1, ge=1, description=MSG_NO_PAG),
    page_size: int = Query(10, ge=1, le=100, description=MSG_TAM_PAG),
    activo: Optional[bool] = Query(True, description=MSG_ESTADO),
    db: Session = Depends(get_db),
    current_user=Depends(require_staff),
):

    try:
        pet_repo = PetRepository(db)

        skip = (page - 1) * page_size

        cats = pet_repo.get_by_species("gato", skip=skip, limit=page_size, activo=activo)
        total = pet_repo.count_by_species("gato", activo=activo)

        total_pages = math.ceil(total / page_size) if total > 0 else 1

        response_data = PetListResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            pets=[PetWithOwnerResponse.model_validate(cat) for cat in cats]
        )

        return success_response(
            message="Gatos obtenidos exitosamente",
            data=response_data.model_dump(mode="json"),
            status_code=status.HTTP_200_OK
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener gatos: {str(exc)}"
        ) from exc


@router.get("/pets/owner/{owner_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def get_pets_by_owner(
    owner_id: UUID = Path(..., description="ID del propietario"),
    page: int = Query(1, ge=1, description=MSG_NO_PAG),
    page_size: int = Query(10, ge=1, le=100, description=MSG_TAM_PAG),
    activo: Optional[bool] = Query(True, description=MSG_ESTADO),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):

    try:
        owner_repo = OwnerRepository(db)
        pet_repo = PetRepository(db)

        # Verificar que el propietario existe
        owner = owner_repo.get_by_id(owner_id)
        if not owner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Propietario no encontrado"
            )

        # Si es propietario, solo puede ver sus propias mascotas
        if current_user.rol.value == "propietario":
            owner_of_user = owner_repo.get_by_usuario_id(current_user.id)
            if not owner_of_user or owner_of_user.id != owner_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permisos para ver las mascotas de otro propietario"
                )

        skip = (page - 1) * page_size

        pets = pet_repo.get_by_owner_id(owner_id, skip=skip, limit=page_size, activo=activo)
        total = pet_repo.count_by_owner(owner_id, activo=activo)

        total_pages = math.ceil(total / page_size) if total > 0 else 1

        response_data = PetListResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            pets=[PetWithOwnerResponse.model_validate(pet) for pet in pets]
        )

        return success_response(
            message=f"Mascotas del propietario {owner.nombre} obtenidas exitosamente",
            data=response_data.model_dump(mode="json"),
            status_code=status.HTTP_200_OK
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener mascotas del propietario: {str(exc)}"
        ) from exc


# ==================== ENDPOINTS DE PROPIETARIOS ====================

@router.get("/owners", response_model=dict, status_code=status.HTTP_200_OK)
async def get_all_owners(
    page: int = Query(1, ge=1, description=MSG_NO_PAG),
    page_size: int = Query(10, ge=1, le=100, description=MSG_TAM_PAG),
    activo: Optional[bool] = Query(True, description=MSG_ESTADO),
    db: Session = Depends(get_db),
    current_user=Depends(require_staff),
):

    try:
        owner_repo = OwnerRepository(db)

        skip = (page - 1) * page_size

        owners = owner_repo.get_all(skip=skip, limit=page_size, activo=activo)
        total = owner_repo.count_all(activo=activo)

        total_pages = math.ceil(total / page_size) if total > 0 else 1

        response_data = OwnerListResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            owners=[OwnerWithPetsResponse.model_validate(owner) for owner in owners]
        )

        return success_response(
            message="Propietarios obtenidos exitosamente",
            data=response_data.model_dump(mode="json"),
            status_code=status.HTTP_200_OK
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener propietarios: {str(exc)}"
        ) from exc


@router.get("/owners/me", response_model=dict, status_code=status.HTTP_200_OK)
async def get_my_owner_profile(
        db: Session = Depends(get_db),
        current_user=Depends(get_current_active_user),
):
    """
    Obtiene el registro de propietario del usuario autenticado

    **Requiere:** Token JWT válido
    **Acceso:** Cualquier usuario autenticado (especialmente propietarios)

    **Comportamiento:**
    - Si el usuario tiene un registro de propietario, lo retorna con sus mascotas
    - Si el usuario no tiene registro de propietario, retorna 404
    - Los usuarios staff también pueden usar este endpoint

    Returns:
        OwnerWithPetsResponse: Datos del propietario con sus mascotas
    """
    try:
        owner_repo = OwnerRepository(db)

        # Buscar el propietario por usuario_id
        owner = owner_repo.get_by_usuario_id(current_user.id)

        if not owner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró un registro de propietario para este usuario"
            )

        # Cargar las mascotas del propietario (si hay relación cargada)
        if not owner.mascotas:
            # Si no se cargó la relación, hacer una consulta explícita
            owner = owner_repo.get_by_id(owner.id)

        return success_response(
            message="Perfil de propietario obtenido exitosamente",
            data=OwnerWithPetsResponse.model_validate(owner).model_dump(mode="json"),
            status_code=status.HTTP_200_OK
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener perfil de propietario: {str(exc)}"
        ) from exc


@router.get("/owners/{owner_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def get_owner_by_id(
    owner_id: UUID = Path(..., description="ID del propietario"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):

    try:
        owner_repo = OwnerRepository(db)

        owner = owner_repo.get_by_id(owner_id)

        if not owner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Propietario no encontrado"
            )

        # Si es propietario, solo puede ver su propia información
        if current_user.rol.value == "propietario":
            owner_of_user = owner_repo.get_by_usuario_id(current_user.id)
            if not owner_of_user or owner_of_user.id != owner_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permisos para ver la información de otro propietario"
                )

        return success_response(
            message="Propietario obtenido exitosamente",
            data=OwnerWithPetsResponse.model_validate(owner).model_dump(mode="json"),
            status_code=status.HTTP_200_OK
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener propietario: {str(exc)}"
        ) from exc