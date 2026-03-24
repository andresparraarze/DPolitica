# DPolitica - Political Transparency Platform for Bolivia

DPolitica is a web application for tracking political connections, funding sources, and criminal connections of Bolivian politicians.

## Features

- **Candidate Profiles**: Create and manage profiles for politicians with details on background, political history, and connections
- **Connection Tracking**: Log and verify connections between politicians and organizations (business, criminal, media, government, NGO)
- **Source Management**: Archive news articles, reports, videos, and official documents as sources of information
- **Anonymous Submissions**: Allow users to submit tips and evidence anonymously
- **REST API**: Full API for programmatic access to candidate data

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite (with SQLAlchemy ORM)
- **Frontend**: HTML5, CSS3, JavaScript
- **Styling**: CSS with modern design principles

## Installation

1. Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:

```bash
pip install flask flask-sqlalchemy requests beautifulsoup4
```

3. Run the application:

```bash
python app.py
```

4. Open http://localhost:5000 in your browser.

## Running Tests

```bash
python tests.py
```

## Seeding Sample Data

```bash
python seed_data.py
```

## Project Structure

```
DPolitica/
├── app.py              # Main Flask application
├── models.py           # Database models
├── requirements.txt    # Python dependencies
├── seed_data.py        # Script to populate database with sample data
├── tests.py            # Unit tests
├── templates/          # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── candidates.html
│   ├── candidate.html
│   ├── sources.html
│   └── submit.html
└── static/             # CSS, JS files
    ├── style.css
    └── main.js
```

## API Endpoints

### GET /api/candidates

Return a list of all candidates.

**Query Parameters:**
- `search`: Filter candidates by name

**Response:**
```json
[
  {
    "id": 1,
    "name": "John Doe",
    "party": "MAS",
    "summary": "Background summary...",
    "connection_count": 5
  }
]
```

### POST /api/candidates

Create a new candidate.

**Request Body:**
```json
{
  "name": "Candidate Name",
  "party": "MAS",
  "background_summary": "Brief summary",
  "political_history": "Detailed history",
  "criminal_connections": "Description of connections",
  "funding_sources": "Description of funding"
}
```

**Response:**
```json
{
  "id": 2,
  "name": "Candidate Name",
  "party": "MAS",
  "message": "Candidate created successfully"
}
```

### GET /api/candidates/<id>

Get detailed information about a specific candidate.

**Response:**
```json
{
  "id": 1,
  "name": "John Doe",
  "party": "MAS",
  "background_summary": "...",
  "political_history": "...",
  "criminal_connections": "...",
  "funding_sources": "...",
  "connections": [
    {
      "id": 1,
      "type": "business",
      "description": "...",
      "organization": "Company X"
    }
  ],
  "sources": [
    {
      "url": "https://example.com/article",
      "description": "...",
      "date_added": "2024-01-01T00:00:00"
    }
  ]
}
```

## Database Models

- **Candidate**: Main politician profile
- **Connection**: Links between politicians and organizations
- **Source**: References (articles, reports, etc.)
- **Submission**: User-submitted tips and evidence

## Despliegue en Railway.app

Guía paso a paso para desplegar DPolitica en [Railway](https://railway.app) de forma gratuita.

### Requisitos Previos

- Cuenta en [Railway.app](https://railway.app)
- Repositorio Git con el código de DPolitica

### Paso 1: Crear un Proyecto en Railway

1. Inicia sesión en [Railway](https://railway.app)
2. Haz clic en **"New Project"** → **"Deploy from GitHub Repo"**
3. Conecta tu cuenta de GitHub y selecciona el repositorio
4. Railway detectará automáticamente que es una app Python

### Paso 2: Agregar una Base de Datos PostgreSQL

1. Dentro de tu proyecto, haz clic en **"+ New"** → **"Database"** → **"Add PostgreSQL"**
2. Railway creará una instancia de PostgreSQL y establecerá la variable `DATABASE_URL` automáticamente

### Paso 3: Configurar Variables de Entorno

En la pestaña **"Variables"** de tu servicio, agrega las siguientes variables:

| Variable | Descripción | Ejemplo |
|---|---|---|
| `SECRET_KEY` | Clave secreta para Flask (generar una larga y aleatoria) | `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `ADMIN_PASSWORD` | Contraseña del panel de administración | `mi-contraseña-segura` |
| `FLASK_ENV` | Modo de ejecución | `production` |
| `DATABASE_URL` | URL de PostgreSQL (automática si usas Railway PostgreSQL) | *(se configura sola)* |
| `API_KEY` | Clave para la API REST (opcional) | `python3 -c "import secrets; print(secrets.token_hex(16))"` |

> **⚠️ Importante:** Nunca uses valores por defecto en producción. Genera claves aleatorias con `python3 -c "import secrets; print(secrets.token_hex(32))"`.

### Paso 4: Configurar el Root Directory

Si el directorio `DPolitica/` no está en la raíz del repositorio:

1. Ve a **Settings** → **Root Directory**
2. Establece la ruta como `DPolitica`

### Paso 5: Desplegar

Railway desplegará automáticamente al recibir un push a la rama principal. Puedes verificar el estado en:

- **Dashboard** → tu servicio → **Deployments**
- El endpoint `/health` debe devolver `{"status": "ok"}`

### Archivos de Configuración

| Archivo | Descripción |
|---|---|
| `Procfile` | Define el comando de inicio: `gunicorn app:app` |
| `railway.toml` | Configuración de Railway: health check en `/health` |
| `requirements.txt` | Dependencias de Python incluyendo `gunicorn` y `psycopg2-binary` |

### Desarrollo Local

Para desarrollo local, la app usa SQLite automáticamente cuando `DATABASE_URL` no está definida:

```bash
cd DPolitica
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
# Abrir http://localhost:5000
```

## License

MIT License
