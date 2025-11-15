"""
Punto de entrada principal de la aplicación FastAPI
Sistema de Gestión de Clínica Veterinaria (GDCV)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
from sqlalchemy import text
import app.models  # asegura registro de modelos

# Cargar variables de entorno
load_dotenv(encoding="latin-1")

# Crear instancia de FastAPI
app = FastAPI(
    title=os.getenv("APP_NAME", "Sistema GDCV"),
    description="API para la Gestión de Clínica Veterinaria - Backend modular con FastAPI",
    version=os.getenv("APP_VERSION", "1.0.0"),
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configurar CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Importar controladores
from app.controllers import (
user_controller,
service_controller,
triage_controller,
auth_controller,
patient_controller,
medical_history_controller,
appointment_controller,
inventory_controller,
)

# Registrar rutas
app.include_router(
    auth_controller.router,
    prefix="/api/v1/auth",
    tags=["Autenticación"]
)

app.include_router(
    user_controller.router,
    prefix="/api/v1/users",
    tags=["Usuarios"]
)

app.include_router(
    patient_controller.router,
    prefix="/api/v1/patients",
    tags=["Pacientes"]
)

# Registrar rutas de servicios
app.include_router(
    service_controller.router,
    prefix="/api/v1/services",
    tags=["Servicios"]
)

# Registrar rutas de citas
app.include_router(
    appointment_controller.router,
    prefix="/api/v1/appointments",
    tags=["Citas"]
)

app.include_router(
    medical_history_controller.router,
    prefix="/api/v1/medical-history",
    tags=["Historias Clínicas"]
)

app.include_router(
    triage_controller.router,
    prefix="/api/v1/triage",
    tags=["Triage"]
)

app.include_router(
    inventory_controller.router,
    prefix="/api/v1/inventory",
    tags=["Inventario"]
)

# Endpoint raíz
@app.get("/")
async def root():
    """
    Endpoint raíz para verificar que la API está activa
    """
    return JSONResponse(
        content={
            "message": "API GDCV activa",
            "status": "running",
            "version": os.getenv("APP_VERSION", "1.0.0"),
            "documentation": "/api/docs",
            "modules": ["Autenticación", "Usuarios"]
        }
    )


# Health DB endpoint
@app.get("/health/db")
async def health_db_check():
    try:
        from app.database import db_connection
        engine = db_connection.get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return JSONResponse(content={"status": "healthy", "database": "connected"})
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "unhealthy", "database": "error", "detail": str(e)})

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Endpoint para verificar el estado de salud de la aplicación
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "GDCV Backend",
            "version": os.getenv("APP_VERSION", "1.0.0")
        }
    )


# Event handlers
@app.on_event("startup")
async def startup_event():
    """
    Acciones a ejecutar al iniciar la aplicación
    """
    print("🚀 Iniciando Sistema GDCV...")
    print("📚 Documentación disponible en: /api/docs")

    # Crear tablas en la base de datos
    from app.database import init_db
    init_db()
    print("✅ Tablas de base de datos inicializadas")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Acciones a ejecutar al detener la aplicación
    """
    print("🛑 Deteniendo Sistema GDCV...")
    # Cerrar conexiones de base de datos
    from app.database import db_connection
    db_connection.close_connection()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )