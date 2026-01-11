# AutomatedPastor

A sermon generation web application for University UMC, Baton Rouge.

## Features (Phase 1 - In Progress)

### Completed
- Flask web application with health endpoint
- Docker containerization (Dockerfile, docker-compose.yml)
- SQLite database with full schema (12 tables)
- Password authentication with bcrypt
- CLI bridge to Claude Code
- Basic UI for sermon CRUD operations
  - Dashboard
  - Create/Edit/View/Delete sermons
  - Sermons list
  - API endpoints

### In Progress
- Export to Word/PDF
- Single-agent sermon generation
- Reference material input

## Quick Start

### Prerequisites
- Python 3.11+
- Docker (optional)

### Local Development
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

### Docker
```bash
# Build and run with docker-compose
docker-compose up -d

# Check health
curl http://localhost:8787/health
```

## Environment Variables
- `APP_PASSWORD` - Hashed password for authentication
- `FLASK_ENV` - Set to `production` for production mode

## API Endpoints

### Health Check
- `GET /health` - Returns `{"status": "healthy"}`

### Sermons
- `GET /` - Dashboard
- `GET /sermons` - List all sermons
- `GET /sermon/<id>` - View sermon
- `GET /sermon/new` - Create sermon form
- `POST /sermon` - Create new sermon
- `GET /sermon/<id>/edit` - Edit sermon form
- `POST /sermon/<id>` - Update sermon
- `POST /sermon/<id>/delete` - Delete sermon
- `GET /api/sermons` - JSON list of sermons
- `GET /api/sermon/<id>` - JSON sermon details

## Testing
```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=. --cov-fail-under=80
```

## Project Structure
```
AutomatedPastor/
├── app.py              # Flask application
├── auth.py             # Authentication module
├── cli_bridge.py       # Claude Code CLI bridge
├── database.py         # Database operations
├── Dockerfile          # Container configuration
├── docker-compose.yml  # Container orchestration
├── requirements.txt    # Python dependencies
└── tests/              # Test suite
    └── unit/           # Unit tests
```

## Development Workflow
This project uses a 3-agent TDD workflow:
1. Test Writer creates tests first
2. Code Writer implements to pass tests
3. PM reviews and manages workflow

## License
Private - University UMC, Baton Rouge
