# Changelog

All notable changes to AutomatedPastor will be documented in this file.

## [Multi-AI Provider Support] - 2026-01-11 (COMPLETE)

### Added - Phase 7: Polish & Integration
- **Provider Health Monitoring**: Track health status of all AI providers
  - `provider_health` table for status tracking
  - `provider_error_log` table for error history
  - Health check API endpoints
  - Failure count tracking with automatic reset on success
- **Fallback Mechanism**: Automatic fallback when providers fail
  - `generate_with_fallback()` - tries providers in order
  - `get_fallback_chain()` - gets ordered fallback list
  - `get_fallback_chain_by_health()` - health-aware ordering
  - Logging of all fallback attempts
- **Health API Endpoints**:
  - `GET /api/providers/health` - All provider health statuses
  - `GET /api/providers/{id}/health` - Specific provider health
  - `POST /api/providers/{id}/health-check` - Trigger health check

### Added - Phase 6: Provider Settings UI
- **Provider Management UI**: Settings page for configuring AI providers
  - Enable/disable providers
  - Set default provider
  - Configure API keys (encrypted storage)
  - Test provider connections
  - Select default models

### Added - Phase 5: Enhanced Research
- **ResearchAggregator**: Multi-provider research with aggregation
  - Parallel research across multiple providers
  - Result caching for efficiency
  - Semantic deduplication of findings
  - Provider source tracking
- **Research API Endpoints**:
  - `POST /api/research/multi-provider` - Multi-provider research

### Added - Phase 4: Provider Comparison
- **Provider Comparison Module**: Track and compare provider performance
  - Response time tracking
  - Token usage statistics
  - Cost estimation per provider
  - Aggregated statistics
- **Comparison API Endpoints**:
  - `POST /api/comparison/generate` - Generate and compare
  - `GET /api/comparison/stats` - Aggregated statistics
  - `GET /api/comparison/cost-breakdown` - Cost by provider

### Added - Phase 3: Multi-Source Generation
- **Multi-Provider Sermon Generation**: Generate with specific providers
  - `generate_sermon_with_provider()` - Single provider generation
  - `generate_sermon_multi_provider()` - Parallel multi-provider
  - Provider ID stored with each sermon
  - Content source tracking
- **Content Storage Tables**:
  - `content_sources` - Track which AI generated what
  - `generation_outputs` - Multiple outputs per sermon

### Added - Phase 2: Gemini Provider
- **Google Gemini Integration**: Full AI provider implementation
  - GeminiProvider class with API integration
  - Model selection (gemini-pro, gemini-pro-vision)
  - Streaming support
  - Safety settings configuration

### Added - Phase 1: Core Infrastructure
- **Provider Base Classes**: AIProvider abstract base class
  - ProviderStatus enum
  - ProviderModel dataclass
  - ProviderResult dataclass
- **Provider Registry**: Central management of providers
  - Register/unregister providers
  - Get enabled/default providers
  - Run prompts on multiple providers in parallel
- **Claude CLI Provider**: CLI-based Claude integration
- **Claude API Provider**: Direct API-based Claude integration
- **OpenAI Provider**: OpenAI API integration
- **Encryption Module**: Secure API key storage
  - AES-256 encryption with Fernet
  - Per-installation encryption keys

### New API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/providers` | GET | List all AI providers |
| `/api/providers/{id}` | GET | Get provider details |
| `/api/providers/{id}` | PUT | Update provider config |
| `/api/providers/{id}/models` | GET | Get available models |
| `/api/providers/{id}/test` | POST | Test provider connection |
| `/api/providers/health` | GET | All provider health statuses |
| `/api/providers/{id}/health` | GET | Provider health details |
| `/api/providers/{id}/health-check` | POST | Trigger health check |
| `/api/research/multi-provider` | POST | Multi-provider research |
| `/api/comparison/generate` | POST | Generate with comparison |
| `/api/comparison/stats` | GET | Comparison statistics |

### Database Schema Changes
- **New Tables**:
  - `ai_providers` - Provider configuration
  - `content_sources` - Content source tracking
  - `research_items` - Research storage
  - `content_versions` - Version history
  - `generation_outputs` - Multiple AI outputs
  - `content_comments` - Inline commenting
  - `revision_requests` - Revision tracking
  - `provider_metrics` - Performance metrics
  - `provider_health` - Health monitoring
  - `provider_error_log` - Error tracking
  - `sermon_versions` - Provider-specific versions
- **Modified Tables**:
  - `sermons` - Added `provider_id` and `status` columns

### Breaking Changes
- None - fully backwards compatible

### Migration Notes
- Run `python -c "from database import init_db, get_db; conn = get_db(); init_db(conn)"` to create new tables
- Existing sermons will have `provider_id = NULL` (backwards compatible)
- Default provider (claude_cli) is auto-enabled on fresh installs

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
