"""
Decoradores de Citas - Patrón Decorator
Extiende funcionalidades de citas dinámicamente

Patrón Decorator aplicado a citas:
- RecordatorioDecorator: Añade recordatorios automáticos
- NotasEspecialesDecorator: Añade notas especiales
- PrioridadDecorator: Marca citas con prioridad especial

RF-05: Gestión de citas
Relaciona con: RF-05, RF-06, RNF-07
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.appointment_decorator import (
    AppointmentDecorator as AppointmentDecoratorModel,
    DecoratorType
)

logger = logging.getLogger(__name__)


class AppointmentDecorator(ABC):
    """
    Decorador abstracto base para citas

    Patrón Decorator: Define la interfaz común para decoradores de citas
    Principio Single Responsibility: Cada decorador añade una funcionalidad específica
    """

    MSG_SESSION = "Sesión de BD requerida para persistir"

    def __init__(self, appointment: Appointment):
        """
        Inicializa el decorador con la cita a decorar

        Args:
            appointment: Cita que será decorada
        """
        self._appointment = appointment

    @abstractmethod
    def get_detalles(self) -> Dict[str, Any]:
        """
        Obtiene los detalles de la cita incluyendo la funcionalidad añadida

        Returns:
            Diccionario con detalles completos de la cita
        """

    def get_appointment(self) -> Appointment:
        """
        Obtiene la cita base sin decoraciones

        Returns:
            Instancia de Appointment
        """
        return self._appointment


class RecordatorioDecorator(AppointmentDecorator):
    """
    Decorador que añade recordatorios automáticos a citas

    Funcionalidades:
    - Recordatorio 24 horas antes
    - Recordatorio 2 horas antes
    - Recordatorio personalizado

    RF-06: Notificaciones automáticas
    RF-05: Gestión de citas
    """

    def __init__(
            self,
            appointment: Appointment,
            recordatorios: Optional[List[Dict[str, Any]]] = None,
            db: Optional[Session] = None
    ):
        """
        Args:
            appointment: Cita a decorar
            recordatorios: Lista de configuraciones de recordatorio
                          Ejemplo: [{"horas_antes": 24}, {"horas_antes": 2}]
            db: Sesión de BD para persistir el decorador
        """
        super().__init__(appointment)
        self.recordatorios = recordatorios or [
            {"horas_antes": 24, "activo": True},
            {"horas_antes": 2, "activo": True}
        ]
        self.db = db

    def get_detalles(self) -> Dict[str, Any]:
        """
        Obtiene detalles de la cita con información de recordatorios

        Returns:
            Dict con detalles de cita + recordatorios
        """
        detalles = {
            "cita_id": str(self._appointment.id),
            "fecha_hora": self._appointment.fecha_hora.isoformat(),
            "estado": self._appointment.estado.value,
            "mascota_id": str(self._appointment.mascota_id),
            "veterinario_id": str(self._appointment.veterinario_id),
            "recordatorios": self._generar_info_recordatorios()
        }

        return detalles

    def _generar_info_recordatorios(self) -> List[Dict[str, Any]]:
        """
        Genera información detallada de los recordatorios

        Returns:
            Lista de recordatorios con sus fechas de envío
        """
        info_recordatorios = []

        for recordatorio in self.recordatorios:
            horas_antes = recordatorio.get("horas_antes", 24)
            fecha_envio = self._appointment.fecha_hora - timedelta(hours=horas_antes)

            info_recordatorios.append({
                "horas_antes": horas_antes,
                "fecha_envio": fecha_envio.isoformat(),
                "activo": recordatorio.get("activo", True),
                "enviado": False  # Se actualizaría al enviar
            })

        return info_recordatorios

    def persistir(self, creado_por: Optional[UUID] = None) -> AppointmentDecoratorModel:
        """
        Persiste el decorador en la base de datos

        Args:
            creado_por: UUID del usuario que crea el decorador

        Returns:
            Instancia del modelo persistido

        Raises:
            ValueError: Si db no está disponible
        """
        if not self.db:
            raise ValueError(self.MSG_SESSION)

        decorator_model = AppointmentDecoratorModel(
            cita_id=self._appointment.id,
            tipo_decorador=DecoratorType.RECORDATORIO,
            configuracion={
                "recordatorios": self.recordatorios
            },
            activo="activo",
            creado_por=creado_por
        )

        self.db.add(decorator_model)
        self.db.commit()
        self.db.refresh(decorator_model)

        logger.info(
            f"📅 [Recordatorio] Decorador persistido para cita {self._appointment.id}"
        )

        return decorator_model


class NotasEspecialesDecorator(AppointmentDecorator):
    """
    Decorador que añade notas especiales a citas

    Funcionalidades:
    - Notas de preparación para el cliente
    - Instrucciones especiales para el veterinario
    - Requisitos especiales (ej: ayuno, traer juguete favorito)

    RF-05: Gestión de citas
    """

    def __init__(
            self,
            appointment: Appointment,
            notas: Dict[str, Any],
            db: Optional[Session] = None
    ):
        """
        Args:
            appointment: Cita a decorar
            notas: Diccionario con notas especiales
                  Ejemplo: {
                      "preparacion_cliente": "Traer certificado de vacunas",
                      "instrucciones_veterinario": "Paciente nervioso",
                      "requisitos": ["ayuno_12h", "traer_historial"]
                  }
            db: Sesión de BD para persistir el decorador
        """
        super().__init__(appointment)
        self.notas = notas
        self.db = db

    def get_detalles(self) -> Dict[str, Any]:
        """
        Obtiene detalles de la cita con notas especiales

        Returns:
            Dict con detalles de cita + notas especiales
        """
        detalles = {
            "cita_id": str(self._appointment.id),
            "fecha_hora": self._appointment.fecha_hora.isoformat(),
            "estado": self._appointment.estado.value,
            "mascota_id": str(self._appointment.mascota_id),
            "veterinario_id": str(self._appointment.veterinario_id),
            "notas_especiales": {
                "preparacion_cliente": self.notas.get("preparacion_cliente"),
                "instrucciones_veterinario": self.notas.get("instrucciones_veterinario"),
                "requisitos": self.notas.get("requisitos", []),
                "observaciones": self.notas.get("observaciones")
            }
        }

        return detalles

    def persistir(self, creado_por: Optional[UUID] = None) -> AppointmentDecoratorModel:
        """
        Persiste el decorador en la base de datos

        Args:
            creado_por: UUID del usuario que crea el decorador

        Returns:
            Instancia del modelo persistido

        Raises:
            ValueError: Si db no está disponible
        """
        if not self.db:
            raise ValueError(self.MSG_SESSION)

        decorator_model = AppointmentDecoratorModel(
            cita_id=self._appointment.id,
            tipo_decorador=DecoratorType.NOTAS_ESPECIALES,
            configuracion={
                "notas": self.notas
            },
            activo="activo",
            creado_por=creado_por
        )

        self.db.add(decorator_model)
        self.db.commit()
        self.db.refresh(decorator_model)

        logger.info(
            f"📝 [Notas Especiales] Decorador persistido para cita {self._appointment.id}"
        )

        return decorator_model


class PrioridadDecorator(AppointmentDecorator):
    """
    Decorador que marca citas con prioridad especial

    Funcionalidades:
    - Niveles de prioridad (alta, media, baja)
    - Razón de la prioridad
    - Alertas visuales en el sistema

    RF-05: Gestión de citas
    """

    PRIORIDADES = ["alta", "media", "baja"]

    def __init__(
            self,
            appointment: Appointment,
            nivel_prioridad: str,
            razon: str,
            db: Optional[Session] = None
    ):
        """
        Args:
            appointment: Cita a decorar
            nivel_prioridad: Nivel de prioridad (alta, media, baja)
            razon: Razón de la prioridad
            db: Sesión de BD para persistir el decorador

        Raises:
            ValueError: Si el nivel de prioridad no es válido
        """
        super().__init__(appointment)

        if nivel_prioridad not in self.PRIORIDADES:
            raise ValueError(
                f"Nivel de prioridad inválido. Debe ser: {', '.join(self.PRIORIDADES)}"
            )

        self.nivel_prioridad = nivel_prioridad
        self.razon = razon
        self.db = db

    def get_detalles(self) -> Dict[str, Any]:
        """
        Obtiene detalles de la cita con información de prioridad

        Returns:
            Dict con detalles de cita + prioridad
        """
        detalles = {
            "cita_id": str(self._appointment.id),
            "fecha_hora": self._appointment.fecha_hora.isoformat(),
            "estado": self._appointment.estado.value,
            "mascota_id": str(self._appointment.mascota_id),
            "veterinario_id": str(self._appointment.veterinario_id),
            "prioridad": {
                "nivel": self.nivel_prioridad,
                "razon": self.razon,
                "alerta": self.nivel_prioridad == "alta",
                "color": self._get_color_prioridad()
            }
        }

        return detalles

    def _get_color_prioridad(self) -> str:
        """
        Obtiene el color asociado al nivel de prioridad

        Returns:
            Color en formato hexadecimal
        """
        colores = {
            "alta": "#FF0000",  # Rojo
            "media": "#FFA500",  # Naranja
            "baja": "#00FF00"  # Verde
        }
        return colores.get(self.nivel_prioridad, "#808080")

    def persistir(self, creado_por: Optional[UUID] = None) -> AppointmentDecoratorModel:
        """
        Persiste el decorador en la base de datos

        Args:
            creado_por: UUID del usuario que crea el decorador

        Returns:
            Instancia del modelo persistido

        Raises:
            ValueError: Si db no está disponible
        """
        if not self.db:
            raise ValueError(self.MSG_SESSION)

        decorator_model = AppointmentDecoratorModel(
            cita_id=self._appointment.id,
            tipo_decorador=DecoratorType.PRIORIDAD,
            configuracion={
                "nivel_prioridad": self.nivel_prioridad,
                "razon": self.razon
            },
            activo="activo",
            creado_por=creado_por
        )

        self.db.add(decorator_model)
        self.db.commit()
        self.db.refresh(decorator_model)

        logger.info(
            f"⚠️ [Prioridad] Decorador persistido para cita {self._appointment.id} "
            f"(nivel: {self.nivel_prioridad})"
        )

        return decorator_model


# ==================== FUNCIONES DE UTILIDAD ====================

def cargar_decoradores_de_cita(
        appointment: Appointment,
        db: Session
) -> List[AppointmentDecorator]:
    """
    Carga todos los decoradores persistidos de una cita

    Args:
        appointment: Cita para la cual cargar decoradores
        db: Sesión de base de datos

    Returns:
        Lista de decoradores aplicados a la cita
    """
    decoradores = []

    # Consultar decoradores persistidos
    decoradores_db = db.query(AppointmentDecoratorModel).filter(
        AppointmentDecoratorModel.cita_id == appointment.id,
        AppointmentDecoratorModel.activo == "activo"
    ).all()

    for decorator_model in decoradores_db:
        if decorator_model.tipo_decorador == DecoratorType.RECORDATORIO:
            decoradores.append(
                RecordatorioDecorator(
                    appointment=appointment,
                    recordatorios=decorator_model.configuracion.get("recordatorios", []),
                    db=db
                )
            )
        elif decorator_model.tipo_decorador == DecoratorType.NOTAS_ESPECIALES:
            decoradores.append(
                NotasEspecialesDecorator(
                    appointment=appointment,
                    notas=decorator_model.configuracion.get("notas", {}),
                    db=db
                )
            )
        elif decorator_model.tipo_decorador == DecoratorType.PRIORIDAD:
            config = decorator_model.configuracion
            decoradores.append(
                PrioridadDecorator(
                    appointment=appointment,
                    nivel_prioridad=config.get("nivel_prioridad", "media"),
                    razon=config.get("razon", ""),
                    db=db
                )
            )

    logger.info(
        f"📦 Cargados {len(decoradores)} decoradores para cita {appointment.id}"
    )

    return decoradores


def get_cita_con_decoradores(
        appointment: Appointment,
        db: Session
) -> Dict[str, Any]:
    """
    Obtiene una cita con todos sus decoradores aplicados

    Args:
        appointment: Cita a obtener
        db: Sesión de base de datos

    Returns:
        Diccionario con información completa de la cita y decoradores
    """
    detalles_base = {
        "id": str(appointment.id),
        "mascota_id": str(appointment.mascota_id),
        "veterinario_id": str(appointment.veterinario_id),
        "servicio_id": str(appointment.servicio_id),
        "fecha_hora": appointment.fecha_hora.isoformat(),
        "estado": appointment.estado.value,
        "motivo": appointment.motivo,
        "notas": appointment.notas
    }

    # Cargar decoradores desde la BD
    decoradores_db = db.query(AppointmentDecoratorModel).filter(
        AppointmentDecoratorModel.cita_id == appointment.id,
        AppointmentDecoratorModel.activo == "activo"
    ).all()

    # Serializar decoradores con metadatos completos
    detalles_decoradores = []
    for decorator_model in decoradores_db:
        decorador_serializado = {
            "id": str(decorator_model.id),
            "cita_id": str(decorator_model.cita_id),
            "tipo_decorador": decorator_model.tipo_decorador.value,  # 'recordatorio', 'notas_especiales', 'prioridad'
            "configuracion": decorator_model.configuracion,
            "activo": decorator_model.activo,
            "fecha_creacion": decorator_model.fecha_creacion.isoformat() if decorator_model.fecha_creacion else None,
            "creado_por": str(decorator_model.creado_por) if decorator_model.creado_por else None
        }
        detalles_decoradores.append(decorador_serializado)

    detalles_base["decoradores"] = detalles_decoradores

    logger.info(
        f"📦 Serializados {len(detalles_decoradores)} decoradores para cita {appointment.id}"
    )

    return detalles_base