from abc import ABC, abstractmethod
from typing import Any


class CreateTemplate(ABC):
    """
    Template Method para operaciones de creación.
    Define un flujo estandarizado que las subclases deben seguir:
    1. validate()      -> Validar los datos antes de crear.
    2. prepare()       -> Construir o inicializar la entidad.
    3. persist()       -> Guardar la entidad en el repositorio o base de datos.
    4. post_process()  -> (Opcional) Ejecutar acciones posteriores, como auditoría o notificaciones.
    """

    def execute(self) -> Any:
        """
        Método principal que define el flujo de ejecución del Template Method.
        Llama a los pasos definidos en orden, garantizando una estructura común.
        """
        self.validate()  # Paso 1: validar datos antes de proceder
        entity = self.prepare()  # Paso 2: construir la entidad
        saved = self.persist(entity)  # Paso 3: guardar en el repositorio
        self.post_process(saved)  # Paso 4 (opcional): realizar acciones adicionales
        return saved  # Retorna la entidad creada o persistida

    @abstractmethod
    def validate(self) -> None:
        """Validaciones previas antes de crear la entidad"""
        ...

    @abstractmethod
    def prepare(self) -> Any:
        """Construcción o inicialización de la entidad"""
        ...

    @abstractmethod
    def persist(self, entity: Any) -> Any:
        """Guardar la entidad en el repositorio o base de datos"""
        ...

    def post_process(self, entity: Any) -> None:
        """
        Hook opcional que puede ser sobrescrito.
        Se ejecuta después de guardar la entidad (por ejemplo, para registrar auditorías).
        """
        return None
