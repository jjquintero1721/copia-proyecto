"""
Configuración de la conexión a la base de datos PostgreSQL
Implementa el patrón Singleton para mantener una única instancia de conexión
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv(encoding="latin-1")


class DatabaseConnection:
    """
    Patrón Singleton para la conexión a la base de datos
    Garantiza una única instancia de conexión durante toda la ejecución
    """
    _instance = None
    _engine = None
    _SessionLocal = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        Inicializa la conexión a la base de datos PostgreSQL
        """
        # Obtener configuración desde variables de entorno
        DB_USER = os.getenv("DB_USER", "postgres")
        DB_PASSWORD = os.getenv("DB_PASSWORD", "")
        DB_HOST = os.getenv("DB_HOST", "localhost")
        DB_PORT = os.getenv("DB_PORT", "5432")
        DB_NAME = os.getenv("DB_NAME", "gdcv")

        # URL de conexión para PostgreSQL
        DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

        # Configuración del engine
        engine_config = {
            "pool_pre_ping": True,  # Verificar conexión antes de usar
            "pool_size": 10,  # Tamaño del pool de conexiones
            "max_overflow": 20,  # Conexiones adicionales permitidas
            "pool_recycle": 3600,  # Reciclar conexiones cada hora
            "echo": os.getenv("DEBUG", "False") == "True"  # Log de SQL en modo debug
        }

        # Crear engine con configuración
        self._engine = create_engine(
            DATABASE_URL,
            connect_args={
                "options": "-c client_encoding=UTF8",
                "application_name": "GDCV"
            },
            **engine_config
        )

        # Configurar eventos de PostgreSQL
        self._configure_postgresql_events()

        # Crear SessionLocal para manejo de sesiones
        self._SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self._engine
        )

        print("✅ Conexión a base de datos PostgreSQL establecida")

    def _configure_postgresql_events(self):
        """
        Configura eventos específicos de PostgreSQL para optimización
        """
        @event.listens_for(self._engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """
            Configuración al establecer conexión
            """
            # Configurar timezone a UTC
            cursor = dbapi_conn.cursor()
            # Asegurar codificación UTF-8
            try:
                cursor.execute("SET client_encoding TO 'UTF8'")
            except Exception:
                pass
            cursor.execute("SET TIME ZONE 'UTC'")
            cursor.close()

    def get_engine(self):
        """Retorna el engine de SQLAlchemy"""
        return self._engine

    def get_session(self):
        """Retorna una nueva sesión de base de datos"""
        return self._SessionLocal()

    def close_connection(self):
        """Cierra todas las conexiones del pool"""
        if self._engine:
            self._engine.dispose()
            print("🔌 Conexiones de base de datos cerradas")


# Base para modelos SQLAlchemy
Base = declarative_base()

# Instancia única de la conexión
db_connection = DatabaseConnection()


def get_db():
    """
    Dependency para obtener sesión de base de datos en endpoints
    Se cierra automáticamente después de cada request

    Uso:
        @app.get("/ejemplo")
        def ejemplo(db: Session = Depends(get_db)):
            # usar db aquí
    """
    db = db_connection.get_session()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Inicializa las tablas en la base de datos
    Debe ser llamado después de importar todos los modelos
    """
    Base.metadata.create_all(bind=db_connection.get_engine())
    print("✅ Tablas de base de datos creadas/verificadas")


def drop_all_tables():
    """
    Elimina todas las tablas (solo para desarrollo/testing)
    ⚠️ USAR CON PRECAUCIÓN
    """
    if os.getenv("ENVIRONMENT") != "production":
        Base.metadata.drop_all(bind=db_connection.get_engine())
        print("⚠️ Todas las tablas han sido eliminadas")
    else:
        raise PermissionError("No se puede eliminar tablas en producción")