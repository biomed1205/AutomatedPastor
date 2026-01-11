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
- **Test Suite**: 125+ passing tests
  - App tests (12)
  - Database tests (49)
  - Authentication tests (33)
  - Route tests (31)

### In Progress
- Export to Word/PDF (python-docx, WeasyPrint)
- Single-agent sermon generation
- Reference material input (text, files, URLs)

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
