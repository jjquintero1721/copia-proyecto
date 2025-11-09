from typing import Any
from datetime import datetime


class AuditDecorator:
    """
    Patron Decorator: agrega una capa de auditoría al método execute()
    de un servicio que sigue el patrón Template Method.
    Permite registrar o monitorear el tiempo de ejecución y la entidad afectada.
    """

    def __init__(self, service: Any):
        """
        Inicializa el decorador con el servicio que se desea auditar.

        Args:
            service: instancia del servicio que implementa el método execute()
        """
        self._service = service  # Se guarda una referencia al servicio original

    def execute(self) -> Any:
        """
        Ejecuta el método `execute()` del servicio decorado,
        midiendo su tiempo de ejecución y registrando información de auditoría básica.
        """
        started = datetime.utcnow()  # Marca de tiempo antes de ejecutar
        entity = self._service.execute()  # Ejecuta el servicio original
        finished = datetime.utcnow()  # Marca de tiempo después de ejecutar

        # Auditoría simple (placeholder): muestra tiempo y entidad procesada
        # En un entorno real, esto podría guardarse en una tabla o sistema de logs
        print(
            f"AUDIT: {self._service.__class__.__name__} "
            f"took={(finished - started).total_seconds()}s "
            f"entity={getattr(entity, 'id', None)}"
        )

        return entity  # Retorna la entidad procesada por el servicio original
