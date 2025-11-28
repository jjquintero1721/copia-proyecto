from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.services.base_template import CreateTemplate
from app.services.factory import EntityFactory
from app.repositories.owner_repository import OwnerRepository
from app.models.owner import Owner


class CreateOwnerService(CreateTemplate):
    """
    Servicio de creación de propietarios (Owner).
    Implementa el patrón Template Method heredado de CreateTemplate,
    definiendo los pasos específicos para crear un propietario.
    """

    def __init__(self, db: Session, nombre: str, correo: str, documento: str, telefono: Optional[str] = None):
        """
        Inicializa el servicio con los datos necesarios para crear un propietario.

        Args:
            db: Sesión de base de datos de SQLAlchemy.
            nombre: Nombre del propietario.
            correo: Correo electrónico del propietario.
            documento: Documento de identidad.
            telefono: Número de teléfono opcional.
        """
        self.db = db
        self.nombre = nombre
        self.correo = correo
        self.documento = documento
        self.telefono = telefono
        self.repo = OwnerRepository(db)  # Repositorio para operaciones con la entidad Owner

    def validate(self) -> None:
        """
        Paso de validación (Template Method).
        Verifica que no exista otro propietario con el mismo correo o documento.
        Lanza una excepción si se detecta duplicado.
        """
        if self.repo.exists_duplicate(self.correo, self.documento):
            raise ValueError("Ya existe un propietario con el mismo correo o documento")

    def prepare(self) -> Owner:
        """
        Paso de preparación (Template Method).
        Crea la instancia del propietario usando la fábrica de entidades (EntityFactory).
        """
        return EntityFactory.create_owner(
            nombre=self.nombre,
            correo=self.correo,
            documento=self.documento,
            telefono=self.telefono,
        )

    def persist(self, entity: Owner) -> Owner:
        """
        Paso de persistencia (Template Method).
        Guarda el propietario en la base de datos mediante el repositorio.
        """
        return self.repo.create(entity)
