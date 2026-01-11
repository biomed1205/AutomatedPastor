# AutomatedPastor - Claude Code Instructions

## Project Goal
Build a sermon generation web app for Katie at University UMC, Baton Rouge.

## CRITICAL RULES
- **TDD**: Write tests FIRST, then code to pass them
- **NO MOCKS**: Use real database, real files, real CLI
- Commit after every test file and every implementation file
- Run security checks on every commit
- Update documentation on every commit

## Tech Stack
- Python 3.11 + Flask + Flask-SocketIO
- SQLite (no mocks - use real DB with `:memory:` for tests)
- Claude CLI bridge (subprocess)
- Docker (port 8787)
- Alpine.js for frontend

## Test Requirements
- Minimum 80% coverage
- No mocks - real implementations only
- Tests must pass before proceeding
- Test naming: `test_should_[behavior]_when_[condition]`

## Development Workflow
1. Write failing tests → `git commit -m "test: add tests for [feature]"`
2. Write code → `git commit -m "feat: implement [feature]"`
3. Security scan → `git commit -m "security: patch [issue]"` (if needed)
4. Update docs → `git commit -m "docs: update [file]"` (if needed)

## Sermon Requirements
- Length: 2,000-2,500 words (15 minutes)
- Theology: Wesleyan/United Methodist
- Structure: Clear 3-point outline
- Scripture: Primary focus, deep engagement
- Illustrations: Contemporary, NOT personal/family anecdotes
- Application: Concrete, actionable takeaways
- Tone: Intellectually rigorous yet accessible

## Context
- Church: University UMC, Baton Rouge, LA
- Pastor: Katie (43yo female senior pastor)
- Congregation: "Purple" politically - diverse, welcoming, averse to political sermons
- Post-2024 UMC (remaining in denomination)

## What to Avoid
- Over-reliance on personal stories
- Rambling or unstructured content
- Abstract philosophy without application
- Political partisanship of any kind
- Mock objects in tests
