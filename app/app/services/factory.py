from app.models.owner import Owner
from app.models.pet import Pet
from typing import Optional
from uuid import UUID
from datetime import date


class EntityFactory:
    """
    Patrón Factory Method: centraliza la creación de entidades del dominio,
    garantizando coherencia y encapsulando la lógica de instanciación.
    """

    @staticmethod
    def create_owner(nombre: str, correo: str, documento: str, telefono: Optional[str]) -> Owner:
        """
        Crea una instancia de la entidad Owner (propietario).

        Args:
            nombre: Nombre del propietario.
            correo: Correo electrónico único del propietario.
            documento: Documento de identidad.
            telefono: Teléfono opcional del propietario.

        Returns:
            Instancia de Owner con los valores asignados.
        """
        owner = Owner(
            nombre=nombre,
            correo=correo,
            documento=documento,
            telefono=telefono,
        )
        return owner

    @staticmethod
    def create_pet(
        propietario_id: UUID,
        nombre: str,
        especie: str,
        raza: Optional[str],
        microchip: Optional[str],
        fecha_nacimiento: Optional[date],
    ) -> Pet:
        """
        Crea una instancia de la entidad Pet (mascota).

        Args:
            propietario_id: ID del propietario al que pertenece la mascota.
            nombre: Nombre de la mascota.
            especie: Especie (ej. perro, gato, etc.).
            raza: Raza de la mascota (opcional).
            microchip: Código de microchip (opcional y único).
            fecha_nacimiento: Fecha de nacimiento de la mascota (opcional).

        Returns:
            Instancia de Pet con los valores asignados.
        """
        pet = Pet(
            propietario_id=propietario_id,
            nombre=nombre,
            especie=especie,
            raza=raza,
            microchip=microchip,
            fecha_nacimiento=fecha_nacimiento,
        )
        return pet
