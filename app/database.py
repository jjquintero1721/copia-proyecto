"""
Configuración de la conexión a la base de datos PostgreSQL
Implementa el patrón Singleton para mantener una única instancia de conexión
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
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
    _session_local = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        Inicializa la conexión a la base de datos PostgreSQL
        """

        # Render usa exclusivamente DATABASE_URL
        DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

        if not DATABASE_URL:
            # Fallback a variables sueltas (útil para local o setups previos)
            DB_USER = os.getenv("DB_USER", "postgres").strip()
            DB_PASSWORD = os.getenv("DB_PASSWORD", "").strip()
            DB_HOST = os.getenv("DB_HOST", "localhost").strip()
            DB_PORT = os.getenv("DB_PORT", "5432").strip()
            DB_NAME = os.getenv("DB_NAME", "gdcv").strip()

            # Si DB_PORT no es un número, ignorarlo (dejamos que postgresql use 5432 por defecto)
            if DB_PORT == "" or not DB_PORT.isdigit():
                DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
            else:
                DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

            print("ℹ️ Usando DATABASE_URL construido desde variables sueltas:", DATABASE_URL)
        else:
            print("ℹ️ Usando DATABASE_URL desde el entorno.")

            # Validación final
        if not DATABASE_URL:
            raise ValueError(
                "❌ ERROR: La variable de entorno DATABASE_URL no está definida y no se pudo construir desde DB_*")

        # Configuración del engine
        engine_config = {
            "pool_pre_ping": True,
            "pool_size": 10,
            "max_overflow": 20,
            "pool_recycle": 3600,
            "echo": os.getenv("DEBUG", "False") == "True"
        }

        self._engine = create_engine(
            DATABASE_URL,
            connect_args={"application_name": "GDCV"},
            **engine_config
        )

        self._configure_postgresql_events()

        self._session_local = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self._engine
        )

        print("✅ Conexión a base de datos PostgreSQL establecida")

    def _configure_postgresql_events(self):
        @event.listens_for(self._engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            try:
                cursor.execute("SET client_encoding TO 'UTF8'")
            except Exception:
                pass
            cursor.execute("SET TIME ZONE 'UTC'")
            cursor.close()

    def get_engine(self):
        return self._engine

    def get_session(self):
        return self._session_local()

    def close_connection(self):
        if self._engine:
            self._engine.dispose()
            print("🔌 Conexiones de base de datos cerradas")


Base = declarative_base()
db_connection = DatabaseConnection()


def get_db():
    db = db_connection.get_session()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=db_connection.get_engine())
    print("✅ Tablas de base de datos creadas/verificadas")


def drop_all_tables():
    if os.getenv("ENVIRONMENT") != "production":
        Base.metadata.drop_all(bind=db_connection.get_engine())
        print("⚠️ Todas las tablas han sido eliminadas")
    else:
        raise PermissionError("No se puede eliminar tablas en producción")
