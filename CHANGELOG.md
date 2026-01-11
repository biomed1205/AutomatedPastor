# Changelog

All notable changes to AutomatedPastor will be documented in this file.

## [Phase 1] - 2026-01-11 (In Progress)

### Added
- **Flask Application**: Basic web application with health endpoint
- **Docker Support**: Dockerfile, docker-compose.yml, .dockerignore
- **Database Schema**: SQLite with 12 tables for sermons, illustrations, themes, etc.
- **Authentication**: Password protection with bcrypt hashing
- **CLI Bridge**: Subprocess-based integration with Claude Code CLI
- **Basic UI**:
  - Dashboard page
  - Sermons list view
  - Create/Edit/View/Delete sermon functionality
  - API endpoints for JSON responses
- **Export**: Word (python-docx) and PDF (reportlab) export functionality
- **Sermon Generation**: Single-agent sermon generation with Claude CLI integration
- **Test Suite**: 215 passing tests
  - App tests (12)
  - Database tests (49)
  - Authentication tests (33)
  - Route tests (31)
  - Export tests (25)
  - Sermon Generator tests (29)
  - CLI Bridge tests (36)

### In Progress
- Reference material input (29 tests written, implementation in progress)
- File processing for PDFs/Word docs (25 tests written, implementation pending)
- Docker build verification

### Technical
- Test Coverage: 96%+
- Security Scan: Clean (LOW severity subprocess warnings only)
- All tests passing

## Development Notes

### TDD Workflow
- Tests written before implementation
- No mocks - real database, real files
- Minimum 80% coverage required

### Commit Convention
- `feat:` - New features
- `test:` - Test additions
- `docs:` - Documentation
- `fix:` - Bug fixes
- `security:` - Security patches
