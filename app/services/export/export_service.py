"""
Service Layer - Servicio de exportación de historias clínicas
RNF-06: Interoperabilidad - Exportar información en formatos estándar
RF-07: Gestión de historias clínicas

Orquesta la lógica de negocio para exportar historias clínicas
utilizando el patrón Strategy.
"""

from typing import Dict, Any, Tuple
from uuid import UUID
from io import BytesIO
from sqlalchemy.orm import Session

from app.services.export.export_context import ExportContext
from app.repositories.medical_history_repository import MedicalHistoryRepository
from app.repositories.pet_repository import PetRepository
from app.repositories.owner_repository import OwnerRepository
from app.repositories.consultation_repository import ConsultationRepository
from app.repositories.user_repository import UserRepository


class ExportService:
    """
    Service Layer - Servicio de exportación de historias clínicas

    Responsabilidades:
    - Recopilar datos completos de la historia clínica
    - Aplicar la estrategia de exportación seleccionada
    - Generar el archivo en el formato solicitado
    """

    def __init__(self, db: Session):
        """
        Inicializa el servicio de exportación

        Args:
            db: Sesión de base de datos SQLAlchemy
        """
        self.db = db
        self.medical_history_repo = MedicalHistoryRepository(db)
        self.pet_repo = PetRepository(db)
        self.owner_repo = OwnerRepository(db)
        self.consultation_repo = ConsultationRepository(db)
        self.user_repo = UserRepository(db)

    def exportar_historia_clinica(
            self,
            historia_clinica_id: UUID,
            formato: str,
            usuario_solicitante_id: UUID
    ) -> Tuple[BytesIO, str, str]:
        """
        Exporta una historia clínica en el formato especificado

        Args:
            historia_clinica_id: ID de la historia clínica a exportar
            formato: Formato deseado ("pdf" o "csv")
            usuario_solicitante_id: ID del usuario que solicita la exportación

        Returns:
            Tuple[BytesIO, str, str]: (archivo, nombre_archivo, content_type)

        Raises:
            ValueError: Si la historia clínica no existe o formato inválido
            PermissionError: Si el usuario no tiene permisos
        """
        # 1. Validar permisos del usuario
        self._validar_permisos_exportacion(usuario_solicitante_id)

        # 2. Recopilar datos completos
        datos = self._recopilar_datos_completos(historia_clinica_id)

        # 3. Crear contexto con la estrategia apropiada
        context = ExportContext.crear_con_formato(formato)

        # 4. Ejecutar exportación
        archivo = context.exportar(datos)

        # 5. Generar nombre del archivo
        numero_hc = datos["historia_clinica"]["numero"]
        extension = context.obtener_extension()
        nombre_archivo = f"{numero_hc}.{extension}"

        # 6. Obtener content type
        content_type = context.obtener_content_type()

        # 7. Registrar en auditoría (RNF-07)
        self._registrar_auditoria_exportacion(
            historia_clinica_id,
            usuario_solicitante_id,
            formato
        )

        return archivo, nombre_archivo, content_type

    def _validar_permisos_exportacion(self, usuario_id: UUID) -> None:
        """
        Valida que el usuario tenga permisos para exportar historias clínicas

        Args:
            usuario_id: ID del usuario

        Raises:
            ValueError: Si el usuario no existe
            PermissionError: Si el usuario no tiene permisos
        """
        usuario = self.user_repo.get_by_id(usuario_id)

        if not usuario:
            raise ValueError(
                f"Usuario con ID {usuario_id} no encontrado"
            )

        # Roles permitidos para exportar: SUPERADMIN, VETERINARIO, AUXILIAR
        roles_permitidos = ["SUPERADMIN", "VETERINARIO", "AUXILIAR","PROPIETARIO"]

        rol = str(usuario.rol).upper().replace("USERROLE.", "").strip()

        if rol not in roles_permitidos:
            raise PermissionError(
                f"El rol '{usuario.rol}' no tiene permisos para exportar "
                f"historias clínicas. Roles permitidos: {', '.join(roles_permitidos)}"
            )

    def _recopilar_datos_completos(
            self,
            historia_clinica_id: UUID
    ) -> Dict[str, Any]:
        """
        Recopila todos los datos necesarios para la exportación

        Args:
            historia_clinica_id: ID de la historia clínica

        Returns:
            Dict con estructura:
            {
                "historia_clinica": {...},
                "mascota": {...},
                "propietario": {...},
                "consultas": [...]
            }

        Raises:
            ValueError: Si la historia clínica no existe
        """
        # 1. Obtener historia clínica
        historia = self.medical_history_repo.get_by_id(historia_clinica_id)

        if not historia:
            raise ValueError(
                f"Historia clínica con ID {historia_clinica_id} no encontrada"
            )

        # RN10-1: Verificar que no esté marcada como eliminada
        if historia.is_deleted:
            raise ValueError(
                f"La historia clínica {historia.numero} está marcada como eliminada "
                f"y no puede ser exportada"
            )

        # 2. Obtener mascota
        mascota = self.pet_repo.get_by_id(historia.mascota_id)

        if not mascota:
            raise ValueError(
                "Mascota asociada a la historia clínica no encontrada"
            )

        # 3. Obtener propietario
        propietario = self.owner_repo.get_by_id(mascota.propietario_id)

        if not propietario:
            raise ValueError(
                "Propietario de la mascota no encontrado"
            )

        # 4. Obtener consultas
        consultas = self.consultation_repo.get_by_historia_clinica_id(
            historia_clinica_id
        )

        # 5. Enriquecer consultas con nombre del veterinario
        consultas_enriquecidas = []
        for consulta in consultas:
            veterinario = self.user_repo.get_by_id(consulta.veterinario_id)

            consulta_dict = {
                "id": str(consulta.id),
                "fecha_hora": consulta.fecha_hora.strftime("%d/%m/%Y %H:%M"),
                "veterinario_id": str(consulta.veterinario_id),
                "veterinario_nombre": veterinario.nombre if veterinario else "N/A",
                "motivo": consulta.motivo,
                "anamnesis": consulta.anamnesis or "N/A",
                "signos_vitales": consulta.signos_vitales or "N/A",
                "diagnostico": consulta.diagnostico or "N/A",
                "tratamiento": consulta.tratamiento or "N/A",
                "vacunas_aplicadas": consulta.vacunas or "N/A",
                "observaciones": consulta.observaciones or "N/A"
            }
            consultas_enriquecidas.append(consulta_dict)

        # 6. Construir estructura de datos
        datos = {
            "historia_clinica": {
                "id": str(historia.id),
                "numero": historia.numero,
                "notas": historia.notas or "",
                "fecha_creacion": historia.fecha_creacion.strftime("%d/%m/%Y"),
                "fecha_actualizacion": historia.fecha_actualizacion.strftime(
                    "%d/%m/%Y") if historia.fecha_actualizacion else "N/A"
            },
            "mascota": {
                "id": str(mascota.id),
                "nombre": mascota.nombre,
                "especie": mascota.especie,
                "raza": mascota.raza or "N/A",
                "sexo": mascota.sexo or "N/A",
                "fecha_nacimiento": mascota.fecha_nacimiento.strftime(
                    "%d/%m/%Y") if mascota.fecha_nacimiento else "N/A",
                "peso": mascota.peso if mascota.peso else "N/A",
                "color": mascota.color or "N/A"

            },
            "propietario": {
                "id": str(propietario.id),
                "nombre_completo": propietario.nombre,
                "numero_documento": propietario.documento,
                "telefono": propietario.telefono,
                "email": propietario.correo,
            },
            "consultas": consultas_enriquecidas
        }

        return datos

    def _registrar_auditoria_exportacion(
            self,
            historia_clinica_id: UUID,
            usuario_id: UUID,
            formato: str
    ) -> None:
        """
        Registra la exportación en el log de auditoría

        Args:
            historia_clinica_id: ID de la historia clínica exportada
            usuario_id: ID del usuario que exportó
            formato: Formato de exportación utilizado

        Note:
            RNF-07: El sistema debe registrar toda acción importante
        """
        from app.utils.audit_logger import AuditLogger

        AuditLogger.log_action(
            db=self.db,
            usuario_id=usuario_id,
            accion="EXPORTAR_HISTORIA_CLINICA",
            descripcion={
                "entidad": "HistoriaClinica",
                "entidad_id": str(historia_clinica_id),
                "detalles": {
                    "formato": formato,
                    "usuario": str(usuario_id),
                }
            }
        )