# Changelog

All notable changes to AutomatedPastor will be documented in this file.

## [Phase 3] - 2026-01-11 (COMPLETE)

### Added
- **Review Panel System**: 7 reviewer personas with custom reviewer support
- **Panel Feedback**: Multi-reviewer feedback with database storage
- **Revision Agent**: Incorporates panel feedback into sermons (31 tests)
- **Feedback Display UI**: Routes and templates for viewing feedback
- **Custom Reviewers**: Create, edit, delete custom reviewer personas

### Technical
- Phase 3: 5/5 items complete
- 644+ tests passing
- Security Scan: Clean

## [Phase 2] - 2026-01-11 (IN PROGRESS)

### Added
- **17 Skill Prompt Files**: Sermon generation skills (homiletics, theology, illustration, etc.)
- **7 Agent Templates**: Orchestrator, researcher, writer, reviewer personas
- **Orchestrator**: Skill invocation, parallel execution, chaining (30 tests)
- **Homiletics Agent**: Sermon structure with forms (deductive, inductive, narrative)
- **Test Suites**:
  - Orchestrator tests (30)
  - Parallel Research tests (23)
  - Homiletics Agent tests (43)
  - E2E Generation tests (42)

### Technical
- Phase 2: 4/6 items complete
- Security Scan: Clean (LOW severity only)

## [Phase 1] - 2026-01-11 (COMPLETE)

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
- **Reference Materials**: Text notes, file upload, URL support with Flask routes
- **File Processing**: PDF, Word document, and text file extraction (pypdf, python-docx)
- **Test Suite**: 272 passing tests
  - App tests (12)
  - Database tests (49)
  - Authentication tests (33)
  - Route tests (31)
  - Export tests (25)
  - Sermon Generator tests (29)
  - CLI Bridge tests (36)
  - Reference Materials tests (32)
  - File Processing tests (25)

### Verified
- Docker build: SUCCESS
- Health endpoint: WORKING

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
