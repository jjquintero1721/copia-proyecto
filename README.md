# 🏥 Sistema de Gestión de Clínica Veterinaria (GDCV) - Backend

Sistema modular para la gestión integral de una clínica veterinaria, desarrollado con **FastAPI**, **PostgreSQL** y **SQLAlchemy**.

---

## 📋 Tabla de Contenidos

- [Descripción General](#-descripción-general)
- [Tecnologías](#-tecnologías)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Instalación y Configuración](#-instalación-y-configuración)
- [Ejecución](#-ejecución)
- [Arquitectura y Patrones](#-arquitectura-y-patrones)
- [Convenciones de Desarrollo](#-convenciones-de-desarrollo)
- [Módulos del Sistema](#-módulos-del-sistema)
- [Documentación Adicional](#-documentación-adicional)

---

## 📖 Descripción General

El **Sistema GDCV** es una solución backend modular diseñada para optimizar los procesos clínicos y administrativos de una clínica veterinaria. Permite gestionar:

- ✅ Usuarios (propietarios, veterinarios, auxiliares, superadmin)
- 🐾 Mascotas y sus propietarios
- 📅 Citas veterinarias
- 📋 Historias clínicas
- 🩺 Triage y clasificación de prioridad
- 💊 Inventario de medicamentos e insumos
- 🔔 Notificaciones por correo electrónico
- 📊 Servicios ofrecidos por la clínica

---

## 🛠 Tecnologías

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **Python** | 3.10+ | Lenguaje base |
| **FastAPI** | 0.115.5 | Framework web |
| **PostgreSQL** | 14.0+ | Base de datos relacional |
| **SQLAlchemy** | 2.0.36 | ORM |
| **Pydantic** | 2.10.3 | Validación de datos |
| **JWT** | - | Autenticación |
| **Uvicorn** | 0.32.1 | Servidor ASGI |

---

## 📂 Estructura del Proyecto
```
dreamfit-app-backend/
├── .venv/                      # Entorno virtual de Python
├── app/
│   ├── controllers/            # 🎮 Endpoints y rutas HTTP
│   │   └── __init__.py
│   ├── models/                 # 🗄️ Modelos de base de datos (SQLAlchemy)
│   │   └── __init__.py
│   ├── repositories/           # 📦 Capa de acceso a datos (CRUD)
│   │   └── __init__.py
│   ├── schemas/                # ✅ Validaciones (Pydantic)
│   │   └── __init__.py
│   ├── security/               # 🔒 Autenticación, JWT, permisos
│   │   ├── __init__.py
│   │   └── auth.py
│   ├── services/               # 🧠 Lógica de negocio
│   │   └── __init__.py
│   ├── utils/                  # 🔧 Funciones auxiliares
│   │   ├── __init__.py
│   │   ├── constants.py
│   │   └── responses.py
│   ├── database.py             # 🔌 Conexión a PostgreSQL (Singleton)
│   ├── main.py                 # 🚀 Punto de entrada FastAPI
│   └── __init__.py
├── .env.example                # Plantilla de variables de entorno
├── .gitignore                  # Archivos ignorados por Git
├── requirements.txt            # Dependencias del proyecto
└── README.md                   # Documentación principal
```

### 📁 Responsabilidad de cada Directorio

| Directorio | Responsabilidad |
|------------|-----------------|
| `controllers/` | Recibe peticiones HTTP, valida datos y llama a servicios |
| `models/` | Define las tablas de la BD usando SQLAlchemy ORM |
| `repositories/` | Operaciones CRUD directas sobre los modelos |
| `schemas/` | Validación de entrada/salida con Pydantic |
| `services/` | Lógica de negocio, reglas, coordinación entre repositorios |
| `security/` | Autenticación JWT, encriptación, control de acceso |
| `utils/` | Funciones auxiliares, constantes, utilidades |

---

## ⚙️ Instalación y Configuración

### 1️⃣ Clonar el Repositorio
```bash
git clone https://github.com/tu-organizacion/dreamfit-app-backend.git
cd dreamfit-app-backend
```

### 2️⃣ Crear Entorno Virtual
```bash
python -m venv .venv
```

**Activar el entorno virtual:**

- **Windows:**
```bash
  .venv\Scripts\activate
```

- **Linux/Mac:**
```bash
  source .venv/bin/activate
```

### 3️⃣ Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4️⃣ Configurar Variables de Entorno

Copiar el archivo de ejemplo:
```bash
cp .env.example .env
```

Editar `.env` con tus credenciales:
```env
# Database Configuration - PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=tu_contraseña
DB_NAME=gdcv

# Application Configuration
APP_NAME="Sistema de Gestión de Clínica Veterinaria"
APP_VERSION="1.0.0"
DEBUG=True
API_PREFIX=/api/v1

# Security
SECRET_KEY=genera-una-clave-secreta-segura
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Email Configuration (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASSWORD=tu-contraseña-de-aplicacion
SMTP_FROM=noreply@gdcv.com
SMTP_FROM_NAME=Clínica Veterinaria GDCV
```

### 5️⃣ Crear Base de Datos

Conectarse a PostgreSQL y crear la base de datos:

```sql
-- Usando psql
psql -U postgres

-- Crear la base de datos
CREATE DATABASE gdcv;

-- Crear usuario (opcional)
CREATE USER gdcv_user WITH PASSWORD 'tu_contraseña';

-- Otorgar privilegios
GRANT ALL PRIVILEGES ON DATABASE gdcv TO gdcv_user;

-- Salir de psql
\q
```

**O usando comandos directos:**

```bash
# Crear base de datos
createdb -U postgres gdcv

# Verificar que se creó correctamente
psql -U postgres -l
```

---

## 🚀 Ejecución

### Ejecutar el Servidor de Desarrollo
```bash
uvicorn app.main:app --reload
```

**Opciones:**
- `--reload`: Reinicio automático al detectar cambios
- `--host 0.0.0.0`: Acceso desde cualquier IP
- `--port 8000`: Puerto personalizado

### Verificar que Funciona

Abre tu navegador en:

- **API activa:** http://localhost:8000
- **Documentación interactiva:** http://localhost:8000/api/docs
- **ReDoc:** http://localhost:8000/api/redoc

### Verificar Conexión a PostgreSQL

Puedes verificar que la aplicación se conecte correctamente a PostgreSQL revisando los logs en la terminal al iniciar el servidor:

```
✅ Conexión a base de datos PostgreSQL establecida
```

---

## 🏗 Arquitectura y Patrones

El proyecto implementa los siguientes **patrones de diseño**:

| Patrón | Aplicación | Archivo/Módulo |
|--------|------------|----------------|
| **Singleton** | Conexión única a BD | `app/database.py` |
| **Factory Method** | Creación de entidades | `services/` |
| **Observer** | Notificaciones por eventos | `services/` (futuro) |
| **Strategy** | Políticas de agendamiento | `services/` (futuro) |
| **Memento** | Versionado de historias clínicas | `models/` (futuro) |
| **Adapter** | Proveedores de correo | `security/` (futuro) |
| **Proxy** | Control de acceso | `security/` (futuro) |

Consulta el documento [PMV_Análisis_y_Diseño.pdf](/mnt/project/PMV_Análisis_y_Diseño.pdf) para más detalles.

---

## 📝 Convenciones de Desarrollo

### 🌿 Nomenclatura de Ramas (Git Flow)
```
main                          # Rama principal (producción)
develop                       # Rama de desarrollo
feature/<modulo>              # Nueva funcionalidad
fix/<modulo>                  # Corrección de errores
hotfix/<descripcion>          # Corrección urgente en producción
refactor/<modulo>             # Refactorización de código
```

**Ejemplos:**
```
feature/pacientes
feature/citas
feature/inventario
fix/citas-validacion
hotfix/seguridad-jwt
refactor/base-de-datos
```

### 💬 Convención de Commits

Usamos **Conventional Commits**:
```
<tipo>(<módulo>): <descripción>

[cuerpo opcional]
[footer opcional]
```

**Tipos:**
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Cambios en documentación
- `style`: Formato, espacios (sin cambios de lógica)
- `refactor`: Refactorización
- `test`: Agregar o modificar tests
- `chore`: Tareas de mantenimiento

**Ejemplos:**
```bash
git commit -m "feat(pacientes): agregar endpoint para registrar mascota"
git commit -m "fix(citas): corregir validación de horarios"
git commit -m "docs(readme): actualizar instrucciones de instalación"
```

### 📦 Flujo de Trabajo

1. **Crear rama** desde `develop`:
```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/mi-modulo
```

2. **Desarrollar** el módulo siguiendo la arquitectura

3. **Commit** frecuente con mensajes claros

4. **Push** a remoto:
```bash
   git push origin feature/mi-modulo
```

5. **Pull Request** a `develop` para revisión

6. **Merge** después de aprobación

---

## 🧩 Módulos del Sistema

### Módulos Principales

1. **Autenticación y Usuarios** (`feature/usuarios`)
   - Registro, login, gestión de roles
   - Control de acceso basado en roles

2. **Propietarios y Mascotas** (`feature/pacientes`)
   - Registro de propietarios
   - Registro de mascotas
   - Validación de duplicados

3. **Gestión de Citas** (`feature/citas`)
   - Agendar, reprogramar, cancelar
   - Validación de horarios
   - Políticas de anticipación

4. **Historias Clínicas** (`feature/historias`)
   - Consultas y procedimientos
   - Versionado de historias
   - Auditoría de cambios

5. **Triage** (`feature/triage`)
   - Clasificación de prioridad
   - Registro de signos vitales

6. **Inventario** (`feature/inventario`)
   - Control de medicamentos
   - Alertas de stock mínimo
   - Movimientos de inventario

7. **Servicios** (`feature/servicios`)
   - Catálogo de servicios
   - Gestión de costos y duración

8. **Notificaciones** (`feature/notificaciones`)
   - Envío de correos
   - Recordatorios de citas
   - Confirmaciones

### Crear un Nuevo Módulo

**Ejemplo: Módulo de Pacientes**

1. Crear rama:
```bash
   git checkout -b feature/pacientes
```

2. Crear archivos necesarios:
```
   app/
   ├── controllers/
   │   └── patient_controller.py
   ├── models/
   │   └── patient.py
   ├── repositories/
   │   └── patient_repository.py
   ├── schemas/
   │   └── patient_schema.py
   └── services/
       └── patient_service.py
```

3. Implementar siguiendo la arquitectura en capas

4. Registrar rutas en `main.py`:
```python
   from app.controllers import patient_controller
   
   app.include_router(
       patient_controller.router,
       prefix="/api/v1/patients",
       tags=["Pacientes"]
   )
```

5. Probar con la documentación interactiva

6. Commit y push:
```bash
   git add .
   git commit -m "feat(pacientes): implementar CRUD completo"
   git push origin feature/pacientes
```

7. Crear Pull Request a `develop`

---

## 📚 Documentación Adicional

### Enlaces Importantes

- **Confluence:** [Espacio GDCV](https://cue-team-proyectonuclear4to.atlassian.net/wiki/spaces/GDCV/overview)
- **Jira:** [Proyecto GDCV](https://cue-team-proyectonuclear4to.atlassian.net/jira)
- **Requisitos Funcionales:** [Ver en Confluence](https://cue-team-proyectonuclear4to.atlassian.net/wiki/spaces/GDCV/pages/1703937)
- **Diagramas:** [Ver en Confluence](https://cue-team-proyectonuclear4to.atlassian.net/wiki/spaces/GDCV/pages/7536651)

### Documentos del Proyecto

- [Análisis y Diseño](/mnt/project/PMV_Análisis_y_Diseño.pdf)
- Requisitos Funcionales y No Funcionales
- Reglas de Negocio
- Diagramas UML (Clases, Secuencia, Casos de Uso)

---

## 🔧 Gestión de Base de Datos PostgreSQL

### Comandos Útiles

```bash
# Conectarse a PostgreSQL
psql -U postgres -d gdcv

# Listar tablas
\dt

# Ver estructura de una tabla
\d nombre_tabla

# Listar bases de datos
\l

# Cambiar de base de datos
\c nombre_base_datos

# Ejecutar script SQL
psql -U postgres -d gdcv -f script.sql

# Backup de la base de datos
pg_dump -U postgres gdcv > backup.sql

# Restaurar backup
psql -U postgres -d gdcv < backup.sql

# Salir de psql
\q
```

### Migraciones (Futuro)

Se recomienda usar **Alembic** para gestionar migraciones de base de datos:

```bash
# Instalar Alembic
pip install alembic

# Inicializar Alembic
alembic init alembic

# Crear migración
alembic revision --autogenerate -m "descripción del cambio"

# Aplicar migraciones
alembic upgrade head

# Revertir última migración
alembic downgrade -1
```

---

## 🧪 Testing
```bash
# Ejecutar tests
pytest

# Con cobertura
pytest --cov=app

# Tests específicos
pytest tests/test_patients.py
```

---

## 👥 Equipo de Desarrollo

- **Arias Lemus, Isabella**
- **Eguis Muñoz, Susana**
- **Giraldo Espinosa, Maria Victoria**
- **Quintero Velásquez, Juan José**

---

## 📄 Licencia

Este proyecto es parte del curso de **Análisis y Diseño de Sistemas** de la Universidad Alexander von Humboldt.

---

## 🆘 Soporte

Para dudas o problemas:

1. Revisar la documentación en Confluence
2. Consultar con el equipo en el canal de desarrollo
3. Crear un issue en Jira

---

## 📌 Notas Importantes sobre PostgreSQL

### Ventajas de PostgreSQL para este Proyecto

- ✅ **ACID Compliant**: Garantiza integridad de datos críticos (historias clínicas, citas)
- ✅ **Tipos de datos avanzados**: JSON, Arrays, UUID nativos
- ✅ **Rendimiento**: Mejor manejo de consultas complejas y concurrencia
- ✅ **Extensibilidad**: Soporte para extensiones como PostGIS (si se necesita geolocalización)
- ✅ **Auditoría**: Triggers y funciones para logging automático
- ✅ **Open Source**: Sin costos de licenciamiento
- ✅ **Compatibilidad**: Excelente integración con SQLAlchemy

### Diferencias con MySQL

Si vienes de MySQL, ten en cuenta:

- PostgreSQL usa `SERIAL` en lugar de `AUTO_INCREMENT`
- Los tipos `TEXT` no tienen límite de tamaño (no necesitas especificar longitud)
- Case-sensitive por defecto en nombres de tablas y columnas
- Mejor manejo de transacciones y bloqueos
- Sintaxis ligeramente diferente en algunas funciones

---

**¡Gracias por contribuir al Sistema GDCV! 🐾**
