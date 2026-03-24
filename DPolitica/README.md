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

## License

MIT License
