# AutomatedPastor: Sermon Generation System

## Project Overview

A locally-hosted web application that generates theologically sound, well-structured 15-minute sermons for a United Methodist pastor. The system uses multiple specialized AI agents to research, write, and refine sermons that address specific congregational feedback.

---

## Development Methodology

### Ralph Wiggum Autonomous Loop Pattern

This project will be built using the **Ralph Wiggum pattern** - an autonomous loop where Claude iteratively works on the codebase until completion criteria are met. Each iteration builds on previous work by reading updated files and test results.

**Key Principle:** "Iteration beats perfection" - The prompt stays the same, but the codebase changes.

### Three-Agent Team Pattern

We use a **Project Manager + Two Developer** workflow:

```
                    ┌─────────────────────────┐
                    │    PROJECT MANAGER      │
                    │    (Claude Agent 1)     │
                    ├─────────────────────────┤
                    │ - Breaks phases → tasks │
                    │ - Assigns to agents     │
                    │ - Reviews completions   │
                    │ - Approves/rejects work │
                    │ - Manages transitions   │
                    └───────────┬─────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │ assigns         │          assigns│
              ▼                 │                 ▼
┌─────────────────────┐         │   ┌─────────────────────┐
│   TEST WRITER       │         │   │   CODE WRITER       │
│   (Claude Agent 2)  │         │   │   (Claude Agent 3)  │
├─────────────────────┤         │   ├─────────────────────┤
│ - Writes tests FIRST│         │   │ - Writes code to    │
│ - No implementation │         │   │   pass tests        │
│ - Reports to PM     │         │   │ - No mocks allowed  │
│ - Clears context    │         │   │ - Reports to PM     │
│   after each issue  │         │   │ - Clears context    │
└─────────────────────┘         │   │   after each issue  │
              │                 │   └─────────────────────┘
              │                 │                 │
              └────────────►────┴────◄────────────┘
                          ▼
                  ┌───────────────┐
                  │  SHARED GIT   │
                  │  REPOSITORY   │
                  │    +          │
                  │ GITHUB ISSUES │
                  └───────────────┘
```

**Workflow:**
1. PM reads PROJECT_PLAN.md, breaks current phase into specific tasks
2. PM creates GitHub Issue assigned to Test Writer
3. Test Writer writes tests, commits, closes issue, notifies PM
4. PM reviews tests - if good, creates issue for Code Writer
5. Code Writer implements, commits, closes issue, notifies PM
6. PM reviews implementation - if tests pass, moves to next task
7. If work rejected, PM creates rework issue with feedback
8. At phase end, PM tests all features, approves phase transition
9. Repeat until all 10 phases complete
10. PM marks project complete - all agents exit

**Context Management:**
- Each agent clears context (`/clear`) after completing each issue
- Keeps token usage low
- Fresh context for each new task

**Idle Behavior:**
- When no work available, agent waits 5 minutes
- Checks for new issues every 5 minutes
- Only exits when PM signals PROJECT_COMPLETE

### Git Worktree Strategy

Use git worktrees for parallel Claude agents:
```bash
# Main development
git worktree add ../pastor-tests tests-branch
git worktree add ../pastor-code code-branch

# Terminal 1: Test Writer
cd ../pastor-tests && claude

# Terminal 2: Code Writer
cd ../pastor-code && claude
```

### Phase Gate Reviews

At the end of each phase:
1. Claude enters **Plan Mode**
2. Reviews what was accomplished vs. objectives
3. Verifies tests pass and coverage is adequate
4. Updates documentation (self-updating MD files)
5. Adjusts remaining plan if needed
6. Only proceeds to next phase after review passes

---

## Docker Configuration

**Port:** `8787` (uncommon, avoids conflicts with 3000, 5000, 8080)

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    nodejs npm \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8787

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8787/health || exit 1

# Run application
CMD ["python", "app.py"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  automated-pastor:
    build: .
    ports:
      - "8787:8787"
    volumes:
      - ./database:/app/database
      - ./exports:/app/exports
      - ./uploads:/app/uploads
    environment:
      - FLASK_ENV=production
      - APP_PASSWORD=${APP_PASSWORD}
    restart: unless-stopped

volumes:
  database:
  exports:
  uploads:
```

**Commands:**
```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f

# Rebuild after changes
docker-compose up -d --build
```

---

## Testing Strategy (TDD - No Mocks)

### Test Structure
```
tests/
├── unit/
│   ├── test_cli_bridge.py
│   ├── test_database.py
│   ├── test_auth.py
│   └── test_skills/
│       ├── test_sermon_craft.py
│       ├── test_biblical_exegesis.py
│       └── ...
├── integration/
│   ├── test_sermon_generation.py
│   ├── test_panel_chat.py
│   ├── test_archive.py
│   └── test_collaboration.py
├── e2e/
│   ├── test_full_workflow.py
│   ├── test_ui_flows.py
│   └── test_export.py
└── conftest.py  # Fixtures (real DB, real CLI)
```

### Coverage Requirements
- **Minimum:** 80% coverage
- **Target:** 90%+ coverage
- **Critical paths:** 100% coverage (auth, CLI bridge, data persistence)

### Test Commands
```bash
# Run all tests
pytest --cov=app --cov-report=html

# Run with verbose output
pytest -v --tb=short

# Run specific test file
pytest tests/unit/test_auth.py

# Watch mode during development
pytest-watch
```

### No Mocks Policy
- Use **real SQLite database** (in-memory for speed)
- Use **real file system** (temp directories)
- Use **real Claude CLI** (with test prompts)
- Integration tests hit **actual endpoints**

---

## Security Skill

A dedicated `/security-check` skill runs at each commit to:

1. **Dependency Scanning**
   - Check for known vulnerabilities (safety, pip-audit)
   - Verify no outdated packages with CVEs

2. **Code Analysis**
   - SQL injection detection
   - XSS vulnerability scanning
   - Path traversal checks
   - Secrets detection (API keys, passwords in code)

3. **Authentication Review**
   - Password hashing verification (bcrypt)
   - Session management audit
   - CSRF protection check

4. **Input Validation**
   - File upload security
   - User input sanitization
   - URL parameter validation

5. **Auto-Patching**
   - When issues found, automatically generate fixes
   - Commit security patches with clear messages

```bash
# Security check hook (runs on pre-commit)
#!/bin/bash
echo "Running security scan..."
bandit -r app/ -f json -o security-report.json
safety check
pip-audit

if [ $? -ne 0 ]; then
    echo "Security issues found. Running auto-patch..."
    claude -p "Fix security issues in security-report.json"
fi
```

---

## Self-Updating Documentation

All markdown files automatically update as code changes:

### Files That Auto-Update
- `README.md` - Project overview, setup instructions
- `CLAUDE.md` - AI instructions, updated with learnings
- `API.md` - Endpoint documentation
- `ARCHITECTURE.md` - System design, updated with changes
- `CHANGELOG.md` - Auto-generated from commits
- `progress.txt` - Ralph Wiggum iteration log

### Update Triggers
- After each successful test run
- After each git commit
- When new features are added
- When API changes occur

### Update Mechanism
```python
# In hooks/post-commit
def update_docs():
    """Auto-update documentation based on code changes."""
    # Extract docstrings → API.md
    # Analyze structure → ARCHITECTURE.md
    # Parse commits → CHANGELOG.md
    # Update CLAUDE.md with new patterns learned
```

---

## MCP Servers Required

Install these MCP servers before starting:

```bash
# 1. File System MCP (for file operations)
npx @anthropic/mcp-server-filesystem

# 2. Git MCP (for version control)
npx @anthropic/mcp-server-git

# 3. GitHub MCP (for PR/issue management)
npx @anthropic/mcp-server-github

# 4. SQLite MCP (for database operations)
npx @anthropic/mcp-server-sqlite

# 5. Fetch MCP (for web research during sermon prep)
npx @anthropic/mcp-server-fetch
```

### MCP Configuration (~/.claude/mcp_servers.json)
```json
{
  "servers": {
    "filesystem": {
      "command": "npx",
      "args": ["@anthropic/mcp-server-filesystem", "/path/to/AutomatedPastor"]
    },
    "git": {
      "command": "npx",
      "args": ["@anthropic/mcp-server-git"]
    },
    "github": {
      "command": "npx",
      "args": ["@anthropic/mcp-server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "sqlite": {
      "command": "npx",
      "args": ["@anthropic/mcp-server-sqlite", "--db", "./database/sermons.db"]
    }
  }
}
```

---

## Git & GitHub Best Practices

### Commit Strategy
```
Phase Work:
1. Write tests → commit: "test: add tests for [feature]"
2. Write code → commit: "feat: implement [feature]"
3. Security check → commit: "security: patch [issue]"
4. Docs update → commit: "docs: update [file]"
```

### Branch Strategy
```
main
├── develop
│   ├── feature/phase-1-foundation
│   ├── feature/phase-2-skills
│   ├── feature/phase-3-panel
│   └── ...
└── release/v1.0
```

### PR Template
```markdown
## Summary
[Auto-generated from commits]

## Tests
- [ ] All tests pass
- [ ] Coverage >= 80%
- [ ] Security scan clean

## Documentation
- [ ] README updated
- [ ] API docs updated
- [ ] CHANGELOG updated
```

### GitHub Actions (CI/CD)
```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements-dev.txt
      - name: Run tests
        run: pytest --cov=app --cov-fail-under=80
      - name: Security scan
        run: bandit -r app/ && safety check
      - name: Build Docker
        run: docker build -t automated-pastor .
```

---

## Context

**Church:** University United Methodist Church, Baton Rouge, LA
**Pastor:** Katie - 43-year-old female senior pastor, married, mother of 3 (13f, 11m, 7m)
**Theology:** Wesleyan (Quadrilateral: Scripture primary, then Tradition, Reason, Experience)
**Political Climate:** "Purple" congregation - politically diverse, welcoming, but strongly averse to political content in sermons

### Congregational Feedback to Address (from survey)
1. **More Structure** - Clear outline format ("First... Second... Third...")
2. **More Scripture** - Deeper biblical engagement, less personal anecdotes
3. **Practical Application** - Tangible takeaways for daily life
4. **Intellectual Rigor** - Appropriate for university town context

---

## System Architecture

### Tech Stack (Recommended)

```
Frontend:  HTML/CSS/JavaScript (Alpine.js for reactivity)
           Design via `/frontend-design` skill for polished, production-grade UI
Backend:   Python + Flask + Flask-SocketIO (for real-time updates)
Database:  SQLite (simple, no setup required)
AI:        Claude Code CLI (uses your Max subscription - no extra cost!)
Export:    python-docx (Word), WeasyPrint (PDF)
Auth:      Simple password protection (bcrypt)
```

**Architecture: Web UI ↔ Claude Code CLI Bridge**

```
┌─────────────────┐     HTTP/WebSocket      ┌─────────────────┐
│   Web Browser   │ ◄──────────────────────► │  Flask Backend  │
│   (Wife uses)   │                          │   (Python)      │
└─────────────────┘                          └────────┬────────┘
                                                      │
                                                      │ subprocess
                                                      │ (claude -p "prompt")
                                                      ▼
                                             ┌─────────────────┐
                                             │ Claude Code CLI │
                                             │ (Max sub used)  │
                                             └─────────────────┘
```

**How it works:**
1. Wife opens web browser to `localhost:5000`
2. Enters sermon details in friendly form
3. Flask backend constructs the prompt
4. Backend spawns `claude -p "prompt"` subprocess
5. Output streams back via WebSocket (real-time progress)
6. Final sermon displayed in browser

**Why this stack:**
- Uses existing Claude Max subscription - **no additional API costs**
- Clean web UI that wife can use easily
- Real-time streaming shows progress as Claude generates
- SQLite requires zero configuration
- Can run with a simple `python app.py` command

### Project Structure

```
AutomatedPastor/
├── app.py                    # Main Flask application
├── cli_bridge.py             # Claude Code CLI subprocess handler
├── config.py                 # Configuration (settings, defaults)
├── auth.py                   # Simple password authentication
├── requirements.txt          # Python dependencies (production)
├── requirements-dev.txt      # Python dependencies (testing/dev)
├── .env                      # Secrets (git-ignored)
├── .env.example              # Template for .env file
│
├── Dockerfile                # Container definition
├── docker-compose.yml        # Container orchestration
├── .dockerignore             # Files to exclude from container
│
├── .github/
│   ├── workflows/
│   │   ├── ci.yml           # Continuous integration
│   │   └── cd.yml           # Continuous deployment
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── ISSUE_TEMPLATE.md
│
├── .claude/
│   └── settings.json        # Claude Code project settings
│
├── database/
│   └── sermons.db           # SQLite database (auto-created)
│
├── tests/                    # Test suite (TDD, no mocks)
│   ├── conftest.py          # Shared fixtures
│   ├── unit/
│   │   ├── test_cli_bridge.py
│   │   ├── test_database.py
│   │   ├── test_auth.py
│   │   └── test_skills/
│   ├── integration/
│   │   ├── test_sermon_generation.py
│   │   ├── test_panel_chat.py
│   │   └── test_archive.py
│   └── e2e/
│       ├── test_full_workflow.py
│       └── test_ui_flows.py
│
├── agents/
│   ├── __init__.py
│   ├── orchestrator.py      # Coordinates all agents
│   ├── biblical_research.py
│   ├── theology.py
│   ├── illustrations.py
│   ├── humor.py
│   ├── homiletics.py
│   └── review_panel.py
│
├── prompts/
│   ├── system_prompts/
│   │   ├── biblical_research.md
│   │   ├── theology.md
│   │   ├── illustrations.md
│   │   ├── humor.md
│   │   ├── homiletics.md
│   │   └── reviewers/
│   │       ├── adam_hamilton.md
│   │       ├── will_willimon.md
│   │       ├── jorge_acevedo.md
│   │       ├── matt_miofsky.md
│   │       ├── barbara_brown_taylor.md
│   │       ├── fleming_rutledge.md
│   │       └── nadia_bolz_weber.md
│   └── templates/
│       ├── sermon_template.md
│       └── outline_template.md
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
│
├── templates/
│   ├── base.html
│   ├── index.html           # Dashboard
│   ├── create.html          # Sermon creation wizard
│   ├── sermon.html          # View/edit sermon
│   ├── archive.html         # Sermon archive
│   ├── green_room.html      # Panel chat
│   └── history.html         # Past sermons
│
├── data/
│   ├── lectionary.json
│   ├── church_calendar.json
│   └── umc_context.md
│
├── skills/
│   ├── sermon/              # 17 sermon skills
│   │   └── ... (see skills section)
│   └── dev/                 # 3 development skills
│       ├── security_check.md
│       ├── update_docs.md
│       └── phase_review.md
│
├── uploads/                  # User-uploaded reference materials
├── exports/                  # Generated sermon files
│
├── CLAUDE.md                 # AI project instructions
├── README.md                 # Project documentation (auto-updated)
├── API.md                    # API documentation (auto-updated)
├── ARCHITECTURE.md           # System design (auto-updated)
├── CHANGELOG.md              # Version history (auto-updated)
├── progress.txt              # Ralph Wiggum iteration log
│
└── ONE_SHOT_GUIDE.md         # How to build this project autonomously
```

---

## Database Schema

```sql
-- Sermons table
CREATE TABLE sermons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    scripture TEXT NOT NULL,
    theme TEXT,
    main_point TEXT,
    liturgical_season TEXT,
    special_occasion TEXT,

    -- Generated content
    manuscript TEXT,
    outline TEXT,

    -- Metadata
    word_count INTEGER,
    estimated_minutes REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    preached_on DATE,

    -- Research data (JSON)
    research_data TEXT,
    review_feedback TEXT
);

-- Illustrations used (to avoid repetition)
CREATE TABLE illustrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sermon_id INTEGER,
    type TEXT,  -- 'story', 'quote', 'statistic', 'humor'
    content TEXT,
    source TEXT,
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sermon_id) REFERENCES sermons(id)
);

-- Scripture passages used
CREATE TABLE scriptures_used (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sermon_id INTEGER,
    reference TEXT,  -- e.g., "John 3:16-17"
    translation TEXT,
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sermon_id) REFERENCES sermons(id)
);

-- Themes/topics tracking
CREATE TABLE themes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sermon_id INTEGER,
    theme TEXT,
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sermon_id) REFERENCES sermons(id)
);

-- Custom reviewers (user-added panel members)
CREATE TABLE custom_reviewers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    focus_area TEXT,
    style_notes TEXT,  -- AI-researched or user-provided description
    is_default BOOLEAN DEFAULT FALSE,  -- Include by default in new sermons
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Track which reviewers were used per sermon
CREATE TABLE sermon_reviewers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sermon_id INTEGER,
    reviewer_name TEXT,
    is_custom BOOLEAN DEFAULT FALSE,
    feedback TEXT,  -- Store their specific feedback
    FOREIGN KEY (sermon_id) REFERENCES sermons(id)
);

-- Reference materials attached to sermons
CREATE TABLE reference_materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sermon_id INTEGER,
    type TEXT,  -- 'text_notes', 'file', 'url'
    title TEXT,
    content TEXT,  -- For text notes, stores the text; for files, stores path
    file_path TEXT,  -- Path to uploaded file
    url TEXT,  -- For web links
    usage_mode TEXT,  -- 'background', 'source', 'constraint'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sermon_id) REFERENCES sermons(id)
);

-- Sermon series
CREATE TABLE sermon_series (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    theme TEXT,
    planned_weeks INTEGER,
    narrative_arc TEXT,  -- JSON: stages of the series arc
    recurring_imagery TEXT,
    series_illustration TEXT,
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Link sermons to series
ALTER TABLE sermons ADD COLUMN series_id INTEGER REFERENCES sermon_series(id);
ALTER TABLE sermons ADD COLUMN series_week INTEGER;

-- Archive confirmation and post-sermon notes
ALTER TABLE sermons ADD COLUMN confirmed_preached BOOLEAN DEFAULT FALSE;
ALTER TABLE sermons ADD COLUMN post_sermon_notes TEXT;
ALTER TABLE sermons ADD COLUMN service_times TEXT;  -- e.g., "9:00 AM, 11:00 AM"

-- Panel chat sessions
CREATE TABLE chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sermon_id INTEGER,  -- Optional link to sermon
    title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sermon_id) REFERENCES sermons(id)
);

-- Chat messages
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    sender TEXT,  -- 'Katie' or panelist name
    message TEXT,
    mentioned_panelists TEXT,  -- JSON array of who was @mentioned
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
);

-- Collaboration/sharing
CREATE TABLE share_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sermon_id INTEGER,
    share_token TEXT UNIQUE,
    password_hash TEXT,  -- Optional password protection
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sermon_id) REFERENCES sermons(id)
);

-- Review comments from collaborators
CREATE TABLE review_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sermon_id INTEGER,
    reviewer_name TEXT,
    comment_text TEXT,
    highlight_start INTEGER,  -- Character position
    highlight_end INTEGER,
    suggestion TEXT,  -- Suggested replacement text
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sermon_id) REFERENCES sermons(id)
);
```

---

## Agent System Design

### 1. Orchestrator Agent
Coordinates the sermon generation workflow:
1. Receives input (scripture, title, theme, main point)
2. Dispatches research agents in parallel
3. Compiles research into sermon draft
4. Sends to review panel
5. Incorporates feedback
6. Produces final manuscript + outline

### 2. Biblical Research Agent
**Purpose:** Deep scriptural analysis

**Researches:**
- Historical context (who, when, where, why)
- Literary context (genre, structure, placement in book)
- Original language insights (Hebrew/Greek key words)
- Cross-references and parallel passages
- Major scholarly interpretations

### 3. Theology Agent
**Purpose:** Ensure Wesleyan theological accuracy

**Checks:**
- Alignment with Wesleyan Quadrilateral (Scripture, Tradition, Reason, Experience)
- UMC doctrinal standards
- Grace theology (prevenient, justifying, sanctifying)
- Social holiness emphasis
- Avoids theological errors

### 4. Illustrations Agent
**Purpose:** Find compelling contemporary examples (NOT personal anecdotes)

**Critical Constraint: POLITICALLY NEUTRAL**
The congregation is "purple" politically - welcoming and open but strongly averse to political sermons. All illustrations must be non-partisan and avoid politically divisive topics.

**Finds:**
- Universal human experiences (family, work, relationships, grief, joy)
- Literary references (novels, poetry, films)
- Historical examples (non-politically-charged)
- Scientific discoveries and nature
- Cultural touchpoints relevant to Baton Rouge/university context
- Stories from church history and saints
- Sports, arts, community events
- Cross-cultural examples that unite rather than divide

**Avoids:**
- Current political figures or controversies
- Hot-button social issues framed politically
- Examples that could be seen as partisan
- News stories that are politically charged
- Anything that would make half the congregation uncomfortable

### 5. Humor Agent
**Purpose:** Add appropriate levity

**Provides:**
- Self-deprecating humor (pastoral, not personal family)
- Observational humor about universal experiences
- Gentle wit that opens hearts
- Avoids: sarcasm, political jokes, divisive humor

### 6. Homiletics Agent
**Purpose:** Structure and delivery

**Creates:**
- Clear three-point outline structure
- Strong opening hook
- Smooth transitions
- Memorable phrases
- Concrete application points
- Strong conclusion with call to action
- Delivery notes (pause, emphasis, etc.)

### 7. Review Panel Agents
Seven pre-configured voices (user can select which to use per sermon):

| Reviewer | Focus Area |
|----------|------------|
| **Adam Hamilton** | Practical application, accessibility, Methodist identity |
| **Will Willimon** | Theological depth, intellectual rigor, prophetic edge |
| **Jorge Acevedo** | Evangelistic invitation, grace emphasis, transformation |
| **Matt Miofsky** | Contemporary relevance, clarity, engagement |
| **Barbara Brown Taylor** | Language beauty, imagery, poetic expression |
| **Fleming Rutledge** | Biblical fidelity, theological substance, avoiding anecdote trap |
| **Nadia Bolz-Weber** | Authenticity, inclusion, connecting with the struggling |

**Customizable Panel Selection:**
- Multi-select checkboxes to choose which reviewers to include for each sermon
- "Add Custom Reviewer" option - enter any preacher's name and their focus area
- Custom reviewers are researched via web search to understand their preaching style
- User can save custom reviewers to their personal panel for reuse
- Default selection remembered but can be changed per sermon

---

## Sermon Generation Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INPUT                               │
│  Scripture | Title | Theme | Main Point | (Optional fields) │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  PARALLEL RESEARCH PHASE                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Biblical │ │ Theology │ │ Illustr. │ │  Humor   │       │
│  │ Research │ │  Agent   │ │  Agent   │ │  Agent   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   HOMILETICS AGENT                          │
│         Structures research into sermon draft               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    REVIEW PANEL                             │
│  Each reviewer provides specific feedback on their focus    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   REVISION AGENT                            │
│         Incorporates feedback into final draft              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      OUTPUT                                 │
│         Full Manuscript + Condensed Pulpit Outline          │
└─────────────────────────────────────────────────────────────┘
```

---

## Claude Code Skills

Custom skills that get invoked during sermon generation. Each skill is a specialized prompt that Claude Code can call.

### Core Sermon Skills

| Skill | Purpose | When Invoked |
|-------|---------|--------------|
| `/public-speaking` | Optimize text for oral delivery - rhythm, pauses, emphasis, breath marks | Final manuscript polish |
| `/engaging-writing` | Add hooks, tension, narrative arc, attention-keeping techniques | Draft creation |
| `/sermon-craft` | Apply homiletical best practices - introduction, body, conclusion patterns | Structure phase |
| `/humor-writing` | Craft appropriate humor - timing, self-deprecation, universal observations | Illustration phase |
| `/illustration-finder` | Find and adapt stories, quotes, examples for specific themes | Research phase |

### Theological Skills

| Skill | Purpose | When Invoked |
|-------|---------|--------------|
| `/wesleyan-lens` | Apply Wesleyan Quadrilateral, grace theology, social holiness | Theology check |
| `/biblical-exegesis` | Deep scripture study - historical, literary, linguistic context | Research phase |
| `/application-bridge` | Connect ancient text to modern daily life with concrete steps | Application section |

### Context-Aware Skills

| Skill | Purpose | When Invoked |
|-------|---------|--------------|
| `/purple-church` | Ensure political neutrality, find unifying rather than divisive angles | Throughout |
| `/university-town` | Add intellectual rigor, scholarly references appropriate for academic audience | Throughout |
| `/liturgical-fit` | Adapt tone/content to Advent, Lent, Easter, Ordinary Time, etc. | Initial setup |

### Specialized Writing Skills

| Skill | Purpose | When Invoked |
|-------|---------|--------------|
| `/memorable-phrases` | Craft sticky phrases, alliteration, parallel structure, quotable lines | Polish phase |
| `/transition-craft` | Write smooth transitions between points, "bridges" in the sermon | Structure phase |
| `/call-to-action` | Create compelling, specific invitations to response | Conclusion |
| `/opening-hook` | Craft attention-grabbing first 30 seconds | Introduction |
| `/storytelling` | Narrative structure within illustrations - setup, tension, resolution, meaning | Illustration phase |

### Pastoral Skills

| Skill | Purpose | When Invoked |
|-------|---------|--------------|
| `/pastoral-care` | Sensitivity to grief, crisis, trauma; words of comfort; acknowledge congregational pain | Throughout when topic warrants |

### Development Skills (Meta)

| Skill | Purpose | When Invoked |
|-------|---------|--------------|
| `/security-check` | Scan for vulnerabilities, secrets, injection risks; auto-patch issues | Every commit (pre-commit hook) |
| `/update-docs` | Auto-update README, API.md, ARCHITECTURE.md, CHANGELOG.md | After each commit |
| `/phase-review` | Enter plan mode, review phase completion, adjust remaining plan | End of each implementation phase |

### Skill Files Structure

```
skills/
├── sermon/                     # Sermon-specific skills (17)
│   ├── public_speaking.md
│   ├── engaging_writing.md
│   ├── sermon_craft.md
│   ├── humor_writing.md
│   ├── illustration_finder.md
│   ├── storytelling.md
│   ├── wesleyan_lens.md
│   ├── biblical_exegesis.md
│   ├── application_bridge.md
│   ├── purple_church.md
│   ├── university_town.md
│   ├── liturgical_fit.md
│   ├── memorable_phrases.md
│   ├── transition_craft.md
│   ├── call_to_action.md
│   ├── opening_hook.md
│   └── pastoral_care.md
│
└── dev/                        # Development skills (3)
    ├── security_check.md       # Vulnerability scanning & patching
    ├── update_docs.md          # Auto-update documentation
    └── phase_review.md         # Phase completion review
```

### Skill Invocation Flow

```
User Input
    │
    ▼
/liturgical-fit ──► Establish season context
    │
    ▼
/biblical-exegesis + /illustration-finder ──► Research (parallel)
    │
    ▼
/storytelling ──► Structure illustrations with narrative arc
    │
    ▼
/wesleyan-lens ──► Theology check
    │
    ▼
/pastoral-care ──► Add sensitivity where topic warrants (grief, crisis, etc.)
    │
    ▼
/sermon-craft + /engaging-writing ──► Draft structure
    │
    ▼
/opening-hook ──► Craft introduction
    │
    ▼
/transition-craft + /application-bridge ──► Build body
    │
    ▼
/humor-writing ──► Add levity points
    │
    ▼
/call-to-action ──► Write conclusion
    │
    ▼
/purple-church + /university-town ──► Context review
    │
    ▼
/memorable-phrases + /public-speaking ──► Final polish
    │
    ▼
Review Panel Feedback
    │
    ▼
Final Sermon
```

---

## Key Configuration Files

### CLAUDE.md (Project Instructions)
```markdown
# AutomatedPastor Project

This project generates sermons for Rev. [Pastor Name] at University UMC, Baton Rouge.

## Sermon Requirements
- Length: 2,000-2,500 words (15 minutes)
- Theology: Wesleyan/United Methodist
- Structure: Clear 3-point outline
- Scripture: Primary focus, deep engagement
- Illustrations: Contemporary, NOT personal/family anecdotes
- Application: Concrete, actionable takeaways
- Tone: Intellectually rigorous yet accessible

## Context
- University town congregation
- Post-2024 UMC (remaining in denomination)
- Liturgical tradition with contemporary elements

## What to Avoid
- Over-reliance on personal stories
- Rambling or unstructured content
- Abstract philosophy without application
- Political partisanship
```

### umc_context.md (Church-Specific Context)
Contains:
- Church history and identity
- Congregation demographics
- Recent sermon series
- Ongoing church initiatives
- Local Baton Rouge context
- LSU/university connections

---

## Special Features

### Panel Chat Room ("The Green Room")

An interactive chat interface where Katie can brainstorm with the preacher panel as if they're in a group chat together.

**How it works:**
```
┌─────────────────────────────────────────────────────────────────┐
│  🎙️ The Green Room - Panel Discussion                    [?]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Katie: I'm thinking about preaching on John 15 - the vine     │
│  and branches. Any thoughts on approaching this for a          │
│  congregation that's been through a lot of loss this year?     │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 🟢 Adam Hamilton                                         │   │
│  │ Katie, I'd lean into the "abide" language here. When     │   │
│  │ people are grieving, they need permission to just BE     │   │
│  │ connected to Christ without feeling like they have to    │   │
│  │ produce fruit right now. The vine does the work...       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 🟣 Barbara Brown Taylor                                  │   │
│  │ There's something beautiful about the pruning image      │   │
│  │ too - not as punishment, but as tender care. A good      │   │
│  │ gardener prunes what they love. Loss can be reframed     │   │
│  │ as God's careful attention, not abandonment...           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 🔵 Fleming Rutledge                                      │   │
│  │ Don't skip verse 6 though - "thrown into the fire."      │   │
│  │ Your congregation needs to hear the weight of that       │   │
│  │ warning before the comfort lands. The Gospel has edges.  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  [@] Adam  Barbara  Fleming  Jorge  Matt  Nadia  Will          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Type your message... @Nadia what do you think?          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                            [Send] [Save Chat]   │
└─────────────────────────────────────────────────────────────────┘
```

**Features:**
- **@ Mentions:** Tag specific panelists to get only their response
  - `@Adam` - Just Adam Hamilton responds
  - `@women` - Barbara, Fleming, and Nadia respond
  - `@UMC` - Adam, Will, Jorge, Matt respond
  - No @ = everyone responds (or a random 3-4)
- **Persona Accuracy:** Each panelist responds in their authentic voice/style
- **Context Awareness:** Panel knows about University UMC, Katie's context, survey feedback
- **Save & Export:** Save chat transcripts to reference during sermon writing
- **Import to Sermon:** Pull insights from chat directly into sermon draft
- **Custom Panelists:** Add custom reviewers to the chat room too

**Use Cases:**
1. **Early brainstorming:** "What angle should I take on this passage?"
2. **Stuck on a section:** "I can't figure out the application - help?"
3. **Feedback on draft:** Paste a paragraph and ask for reactions
4. **Illustration check:** "Is this story too political? Too personal?"
5. **Theological sanity check:** "Am I saying this correctly?"

### Sermon Series Planner

Plan multi-week sermon series with connected themes and narrative arc.

**Features:**
- Create series with title, theme, duration (4-8 weeks typical)
- Visual timeline showing each week's scripture and focus
- Auto-suggest complementary passages based on theme
- Track narrative arc across series (setup → development → climax → resolution)
- Link individual sermons to their series
- Series-level illustrations that can be referenced across weeks
- "Previously on..." recap suggestions for continuity

**Series Planning View:**
```
┌─────────────────────────────────────────────────────────────────┐
│  📚 Series: "Rooted" (6 weeks on Spiritual Foundations)        │
├─────────────────────────────────────────────────────────────────┤
│  Week 1: John 15:1-8    - "Connected to the Vine"    [✓ Done]  │
│  Week 2: Psalm 1        - "Planted by Water"         [► Draft] │
│  Week 3: Colossians 2   - "Rooted in Christ"         [○ Plan]  │
│  Week 4: Ephesians 3    - "Rooted in Love"           [○ Plan]  │
│  Week 5: Matthew 13     - "Roots in Good Soil"       [○ Plan]  │
│  Week 6: Jeremiah 17    - "Tree by the Stream"       [○ Plan]  │
├─────────────────────────────────────────────────────────────────┤
│  Series Arc: Introduction → Foundation → Testing → Growth      │
│  Recurring Image: Tree growing through seasons                 │
│  Series Illustration: The oak tree in the church courtyard     │
└─────────────────────────────────────────────────────────────────┘
```

### Reference Material Input

During sermon preparation, Katie can provide her own research, notes, and materials to guide the AI.

**Input Options:**
```
┌─────────────────────────────────────────────────────────────────┐
│  📎 Supporting Materials for "Connected to the Vine"           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📝 Your Notes & Research                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ I've been thinking about the imagery of pruning. My     │   │
│  │ grandmother was a master gardener and she always said   │   │
│  │ "you have to cut back to grow forward." Also, I found   │   │
│  │ this great commentary by N.T. Wright on the "abide"     │   │
│  │ language - it's about remaining, not striving...        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  📁 Attached Files                                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ✓ NT_Wright_John15_Commentary.pdf        [View] [Remove]│   │
│  │ ✓ Congregation_Prayer_Requests.docx      [View] [Remove]│   │
│  │ ✓ Previous_Sermon_Vine_2019.docx         [View] [Remove]│   │
│  │                                                         │   │
│  │  [+ Add Files]  Supports: PDF, DOCX, TXT, MD            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  🔗 Web Links to Include                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ https://www.workingpreacher.org/john-15                 │   │
│  │ [+ Add Link]                                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ⚙️ How to use these materials:                                 │
│  ○ As background context (AI reads but doesn't quote)          │
│  ● As source material (AI can incorporate/reference)           │
│  ○ As constraints (AI must address these points)               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Features:**
- **Text Notes:** Free-form text area for Katie's own thoughts, research, ideas
- **File Attachments:** Upload PDFs, Word docs, text files as reference
- **Web Links:** Paste URLs to articles/commentaries for AI to consider
- **Usage Mode:** Control how AI uses the materials:
  - Background context (inform but don't quote)
  - Source material (can incorporate directly)
  - Constraints (must address specific points)
- **Previous Sermons:** Attach past sermons on same topic to avoid repetition

### Sermon Archive

Complete historical record of every sermon preached, with all associated materials.

**Archive View:**
```
┌─────────────────────────────────────────────────────────────────┐
│  📚 Sermon Archive                           [Search] [Filter]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  2026                                                           │
│  ├─ January                                                     │
│  │   ├─ Jan 12 ✓ "New Beginnings" - Isaiah 43:18-19            │
│  │   │          Series: New Year, New Life (Week 2)            │
│  │   │          [Manuscript] [Outline] [Research] [Audio]       │
│  │   │                                                          │
│  │   ├─ Jan 5  ✓ "Fresh Start" - 2 Cor 5:17                    │
│  │   │          Series: New Year, New Life (Week 1)            │
│  │   │          [Manuscript] [Outline] [Research]               │
│  │                                                              │
│  2025                                                           │
│  ├─ December                                                    │
│  │   ├─ Dec 29 ✓ "The Light Shines" - John 1:1-14              │
│  │   ├─ Dec 24 ✓ "Christmas Eve: Emmanuel" - Matthew 1:23      │
│  │   ├─ Dec 22 ✓ "Advent 4: Mary's Yes" - Luke 1:26-38         │
│  │   ...                                                        │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  Stats: 156 sermons archived | 12 series | 89 unique passages  │
└─────────────────────────────────────────────────────────────────┘
```

**Archive Entry Detail:**
```
┌─────────────────────────────────────────────────────────────────┐
│  📜 "Connected to the Vine"                                     │
│  Preached: Sunday, March 15, 2026 | 9:00 AM & 11:00 AM         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Scripture: John 15:1-8                                         │
│  Theme: Abiding in Christ                                       │
│  Series: Rooted (Week 1 of 6)                                   │
│  Liturgical Season: Lent 4                                      │
│                                                                 │
│  📄 Documents                                                    │
│  ├─ Final Manuscript (2,847 words, ~17 min)     [View] [Export]│
│  ├─ Pulpit Outline                              [View] [Export]│
│  ├─ Research Notes                              [View]         │
│  └─ Panel Chat Transcript                       [View]         │
│                                                                 │
│  📎 Reference Materials Used                                    │
│  ├─ NT_Wright_John15_Commentary.pdf                            │
│  ├─ Working Preacher article (link)                            │
│  └─ Katie's handwritten notes                                  │
│                                                                 │
│  👥 Review Panel Feedback                                       │
│  ├─ Adam Hamilton: "Strong application section..."             │
│  ├─ Fleming Rutledge: "Good balance of comfort and challenge"  │
│  └─ [View All Feedback]                                        │
│                                                                 │
│  📊 Metadata                                                    │
│  ├─ Illustrations: Garden story, Augustine quote, LSU example  │
│  ├─ Key phrases: "Abide means remain", "The vine does the work"│
│  └─ Cross-references: Psalm 1, Jeremiah 17:7-8                 │
│                                                                 │
│  ✏️ Post-Sermon Notes                                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Good response to the pruning section. Several people    │   │
│  │ mentioned it spoke to their grief. The humor about the  │   │
│  │ houseplant landed well. Next time: slow down on the     │   │
│  │ Greek word explanation.                                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                            [Save Notes]         │
│                                                                 │
│  Status: ✓ Confirmed Preached    [Edit] [Duplicate] [Delete]   │
└─────────────────────────────────────────────────────────────────┘
```

**Archive Features:**
- **Confirm Preached:** Mark sermon as actually delivered on specific date
- **Full History:** Every sermon going back indefinitely
- **All Materials:** Manuscript, outline, research, files, panel feedback
- **Post-Sermon Notes:** Add reflections on what worked/didn't
- **Search:** Find by scripture, theme, date, keyword, series
- **Statistics:** Track passages used, themes covered, series completed
- **Export:** Backup entire archive or individual sermons
- **Duplicate:** Copy a past sermon as starting point for revision

### Collaboration & Feedback System

Share sermon drafts with staff or spouse for input before finalizing.

**Features:**
- **Share Link:** Generate a private link to share draft with reviewers
- **Inline Comments:** Reviewers can highlight text and leave comments
- **Suggestion Mode:** Reviewers can propose edits (like Google Docs)
- **Review Status:** Track who has reviewed and their overall feedback
- **Version History:** See changes between drafts
- **No Account Required:** Reviewers just need the link + optional password

**Collaboration View:**
```
┌─────────────────────────────────────────────────────────────────┐
│  👥 Sharing: "Connected to the Vine" (Draft 2)                 │
├─────────────────────────────────────────────────────────────────┤
│  Share Link: localhost:5000/review/abc123                      │
│  Password: [optional]                    [Copy Link]           │
├─────────────────────────────────────────────────────────────────┤
│  Reviewers:                                                    │
│  ✓ Sarah (Associate Pastor) - "Great structure, love the      │
│    opening hook. Question about the illustration on p2."       │
│  ✓ Mark (Spouse) - "This feels really strong. The ending      │
│    gave me chills."                                            │
│  ○ Pending: Music Director                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## User Interface

### Create Sermon Page (Wizard Flow)

**Step 1: Scripture Selection**
- Option A: Pick from Revised Common Lectionary (shows upcoming Sundays)
- Option B: Enter scripture manually
- Shows preview of selected passage

**Step 2: Sermon Details**
- Title (optional - can be generated)
- Theme (dropdown + custom)
- Main Point (one sentence)
- Liturgical Season (auto-detected from date)
- Special Occasion (dropdown: Baptism, Communion, etc.)

**Step 3: Select Review Panel**
- Multi-select checkboxes for built-in reviewers (7 pre-configured)
- Each reviewer shows name + focus area + toggle
- "Add Custom Reviewer" button opens modal:
  - Name field (e.g., "Fred Craddock")
  - Focus area (e.g., "Inductive preaching, storytelling")
  - Option to save to personal panel for future use
- Quick preset buttons: "All", "UMC Only", "Women Only", "Clear"
- Remembers last selection as default

**Step 4: Review & Generate**
- Summary of inputs
- "Generate Sermon" button
- Progress indicator showing agent activity

**Step 5: Review & Edit**
- Side-by-side: Manuscript | Outline
- Inline editing capability
- Regenerate sections
- Export options (Word, PDF, Print)

---

## Implementation Phases

### Phase 1: Foundation (Core Application)
- [x] Set up Flask project structure with WebSocket support
- [x] Create Dockerfile for containerization
- [x] Create docker-compose.yml for orchestration
- [x] Create .dockerignore file
- [x] Create SQLite database schema (all tables)
- [x] Build basic UI (create, view, list sermons)
- [x] Implement CLI bridge to Claude Code
- [x] Implement single-agent sermon generation
- [x] Add simple password authentication
- [x] Add export to Word/PDF
- [x] Reference material input (text notes, file upload, URLs)
- [x] File processing for PDFs and Word docs
- [x] Verify Docker build and health endpoint work

### Phase 2: Skills & Multi-Agent System
- [x] Create all 17 skill prompt files
- [x] Create agent prompt templates
- [x] Implement orchestrator with skill invocation
- [x] Build parallel research agents
- [x] Integrate Homiletics agent for structure
- [x] Test end-to-end generation

### Phase 3: Review Panel
- [x] Create 7 reviewer persona prompts
- [x] Implement panel feedback system
- [x] Build revision agent
- [x] Add feedback display in UI
- [x] Custom reviewer support

### Phase 4: The Green Room (Panel Chat)
- [x] Build chat UI interface
- [x] Implement @ mention parsing
- [x] Create group shortcuts (@women, @UMC)
- [x] Persona-aware response generation
- [x] Chat history saving/export
- [x] Import insights to sermon draft

### Phase 5: Sermon Series Planner
- [x] Database schema for series
- [x] Series creation wizard
- [x] Visual timeline view
- [x] Passage suggestion engine
- [x] Link sermons to series
- [x] Series arc tracking

### Phase 6: Collaboration System
- [x] Generate shareable links
- [x] Reviewer comment system
- [x] Inline suggestion mode
- [x] Version history tracking
- [x] Review status dashboard

### Phase 7: Sermon Archive
- [x] Archive list view with year/month organization
- [x] Archive detail view with all materials
- [x] Confirm preached functionality
- [x] Post-sermon notes
- [x] Search and filter
- [x] Statistics dashboard
- [x] Full archive export/backup

### Phase 8: Enhanced Features
- [x] Lectionary calendar integration
- [x] Illustration deduplication
- [x] Theme/scripture usage tracking
- [x] Church context awareness
- [x] Previous sermon detection (warn if topic recently preached)

### Phase 9: UI/UX Design
- [x] Use `/frontend-design` skill for entire app look/feel
- [x] Design system: colors, typography, spacing, components
- [x] Warm, inviting aesthetic appropriate for pastoral tool
- [x] Clean, uncluttered interface for focus during sermon prep
- [x] Mobile-responsive design
- [x] Accessibility considerations

### Phase 10: Polish
- [x] Practice timing feature
- [ ] User preferences/settings
- [ ] Documentation and help
- [ ] run.bat one-click startup

---

## ONE_SHOT_GUIDE.md - Autonomous Build Instructions

This guide explains how to build the entire AutomatedPastor project autonomously using the Ralph Wiggum pattern and dual-Claude TDD workflow.

### Prerequisites

Before starting, ensure you have:

```bash
# 1. Claude Code installed
npm install -g @anthropic/claude-code

# 2. Ralph Wiggum plugin
/plugin install ralph-wiggum@claude-plugins-official

# 3. Git configured
git config --global user.name "Your Name"
git config --global user.email "your@email.com"

# 4. GitHub CLI authenticated
gh auth login

# 5. MCP servers installed
npx @anthropic/mcp-server-filesystem
npx @anthropic/mcp-server-git
npx @anthropic/mcp-server-github
npx @anthropic/mcp-server-sqlite

# 6. Docker installed and running
docker --version

# 7. Python 3.11+
python --version
```

### Step 1: Initialize Repository

```bash
# Create GitHub repo
gh repo create AutomatedPastor --public --clone
cd AutomatedPastor

# Initialize project
git checkout -b develop
mkdir -p {tests/unit,tests/integration,tests/e2e,agents,prompts,skills,static,templates,data,uploads,exports}

# Copy this plan as the starting point
cp path/to/this/plan.md ./PROJECT_PLAN.md

# Create initial CLAUDE.md
cat > CLAUDE.md << 'EOF'
# AutomatedPastor - Claude Code Instructions

## Project Goal
Build a sermon generation web app for Katie at University UMC, Baton Rouge.

## CRITICAL RULES
- TDD: Write tests FIRST, then code to pass them
- NO MOCKS: Use real database, real files, real CLI
- Commit after every test file and every implementation file
- Run security checks on every commit
- Update documentation on every commit
- At phase end: enter plan mode, review, adjust

## Development Workflow
1. Write failing tests → `git commit -m "test: add tests for [feature]"`
2. Write code → `git commit -m "feat: implement [feature]"`
3. Security scan → `git commit -m "security: patch [issue]"`
4. Update docs → `git commit -m "docs: update [file]"`

## Tech Stack
- Python 3.11 + Flask + Flask-SocketIO
- SQLite (no mocks - use real DB)
- Claude CLI bridge (subprocess)
- Docker (port 8787)
- Alpine.js for frontend

## Test Requirements
- Minimum 80% coverage
- No mocks - real implementations only
- Tests must pass before proceeding

## Completion Markers
Use these in prompts:
- <promise>PHASE_1_COMPLETE</promise>
- <promise>PHASE_2_COMPLETE</promise>
- etc.
EOF

# Initial commit
git add .
git commit -m "chore: initialize project structure"
git push -u origin develop
```

### Step 2: Set Up Git Worktrees for Dual-Claude

```bash
# From AutomatedPastor directory
cd ..

# Create worktree for Test Writer
git worktree add ./pastor-tests -b tests-branch
cd pastor-tests

# Create worktree for Code Writer
cd ../AutomatedPastor
git worktree add ../pastor-code -b code-branch
```

### Step 2.5: GitHub Issues as Coordination Queue

Use GitHub Issues as a work queue so all 3 agents can run simultaneously but coordinate through issue creation/assignment.

**Label Setup:**
```bash
# Create labels for agent coordination
gh label create "agent:test-writer" --color "1d76db" --description "Work for Test Writer agent"
gh label create "agent:code-writer" --color "0e8a16" --description "Work for Code Writer agent"
gh label create "agent:pm-review" --color "d93f0b" --description "Ready for PM to review"
gh label create "status:waiting" --color "fbca04" --description "Waiting to be picked up"
gh label create "status:in-progress" --color "6f42c1" --description "Currently being worked"
gh label create "status:rework" --color "b60205" --description "Rejected - needs rework"
gh label create "phase:1" --color "c5def5" --description "Phase 1 work"
gh label create "phase:2" --color "bfd4f2" --description "Phase 2 work"
gh label create "phase:3" --color "d4c5f9" --description "Phase 3 work"
gh label create "phase:4" --color "f9d0c4" --description "Phase 4 work"
gh label create "phase:5" --color "fef2c0" --description "Phase 5 work"
gh label create "phase:6" --color "c2e0c6" --description "Phase 6 work"
gh label create "phase:7" --color "bfdadc" --description "Phase 7 work"
gh label create "phase:8" --color "d4c5f9" --description "Phase 8 work"
gh label create "phase:9" --color "f9d0c4" --description "Phase 9 work"
gh label create "phase:10" --color "fef2c0" --description "Phase 10 work"
```

**Issue Templates:**

```markdown
# .github/ISSUE_TEMPLATE/test-work.md
---
name: Test Work
about: Work item for Test Writer agent
labels: agent:test-writer, status:waiting
---

## Feature to Test
[Feature name from PROJECT_PLAN.md]

## Acceptance Criteria
- [ ] Tests cover happy path
- [ ] Tests cover edge cases
- [ ] Tests cover error handling
- [ ] No mocks used
- [ ] Committed to tests-branch

## Dependencies
- Depends on: #[issue number] (if any)

## When Complete
Create issue for Code Writer: "Implement [feature]"
```

```markdown
# .github/ISSUE_TEMPLATE/code-work.md
---
name: Code Work
about: Work item for Code Writer agent
labels: agent:code-writer, status:waiting
---

## Feature to Implement
[Feature name]

## Tests to Pass
See tests in: `tests/[path]`

## Acceptance Criteria
- [ ] All related tests pass
- [ ] Security scan clean
- [ ] Committed to code-branch

## Dependencies
- Depends on: #[issue number] (tests must be committed first)

## When Complete
Create issue for Reviewer: "Review [feature]"
```

**Coordination Flow:**

```
┌─────────────────────────────────────────────────────────────────────┐
│                    GITHUB ISSUES QUEUE                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. PM bootstraps Phase 1:                                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Issue #1: "Write tests for CLI bridge"                       │   │
│  │ Labels: agent:test-writer, phase:1, status:waiting           │   │
│  │ Body: "Requirements: subprocess handling, streaming output"  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                           │                                         │
│                           ▼                                         │
│  2. Test Writer picks up, writes tests, closes #1, creates:         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Issue #2: "PM Review: Tests for CLI bridge"                  │   │
│  │ Labels: agent:pm-review, phase:1, status:waiting             │   │
│  │ Body: "Tests committed in abc123. Ready for review."         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                           │                                         │
│                           ▼                                         │
│  3. PM reviews tests, approves, creates:                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Issue #3: "Implement CLI bridge"                             │   │
│  │ Labels: agent:code-writer, phase:1, status:waiting           │   │
│  │ Body: "Make tests in tests/unit/test_cli.py pass."           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                           │                                         │
│                           ▼                                         │
│  4. Code Writer picks up, implements, closes #3, creates:           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Issue #4: "PM Review: Implementation of CLI bridge"          │   │
│  │ Labels: agent:pm-review, phase:1, status:waiting             │   │
│  │ Body: "Code committed. All tests pass. Security clean."      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                           │                                         │
│                           ▼                                         │
│  5. PM reviews implementation:                                      │
│     ✓ Approved → Creates next test-writer issue for next feature   │
│     ✗ Rejected → Creates rework issue with feedback                │
│                                                                     │
│  ... cycle continues until all features in phase complete ...       │
│                                                                     │
│  6. PM merges, transitions to next phase, creates first issue       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Agent Polling Logic:**

Each agent runs in a Ralph Wiggum loop:
1. Polls for issues with their label + status:waiting
2. If no issues, waits 5 minutes (`sleep 300`), then retries
3. If issue found, marks as status:in-progress, works on it
4. When done, closes issue, creates pm-review issue
5. Clears context (`/clear`) to keep tokens low
6. Returns to polling
7. Only exits when PM outputs PROJECT_COMPLETE

### Step 3: Configure Claude Hooks

Create `.claude/settings.json` in each worktree:

```json
{
  "permissions": {
    "allow": [
      "Bash(pytest:*)",
      "Bash(git:*)",
      "Bash(docker:*)",
      "Edit",
      "Write",
      "Read"
    ]
  },
  "hooks": {
    "preCommit": "pytest --cov=app --cov-fail-under=80 && bandit -r app/"
  }
}
```

### Step 4: Launch Project Manager (Terminal 1)

```bash
cd AutomatedPastor

# Start Ralph Wiggum loop for Project Manager
/ralph-loop "You are the PROJECT MANAGER for AutomatedPastor.

YOUR JOB: Break phases into tasks, assign work, review completions, manage the entire project lifecycle.

## ON FIRST RUN - BOOTSTRAP
1. Read PROJECT_PLAN.md to understand all 10 phases
2. For Phase 1, break it into discrete tasks (each task = one test file + one implementation)
3. Create first GitHub issue for Test Writer:
   \`gh issue create --title 'Write tests for [specific feature]' --label 'agent:test-writer' --label 'status:waiting' --label 'phase:1' --body 'Requirements: [specific acceptance criteria from plan]'\`

## EVERY ITERATION - POLL FOR COMPLETED WORK
Check for work ready for your review:
\`\`\`bash
gh issue list --label 'agent:pm-review' --label 'status:waiting' --json number,title,body
\`\`\`

If no issues found:
- Wait 5 minutes: \`sleep 300\`
- Output: 'PM waiting for completed work...'
- Loop continues

When completed work found:
1. Mark as in-progress: \`gh issue edit [NUMBER] --remove-label 'status:waiting' --add-label 'status:in-progress'\`
2. Pull latest code: \`git pull origin tests-branch code-branch\`
3. Review the work:
   - Run tests: \`pytest --cov=app -v\`
   - Check coverage >= 80%
   - Run security scan: \`bandit -r app/\`
   - Verify the feature works as specified

4. IF WORK APPROVED:
   - Close issue with approval: \`gh issue close [NUMBER] --comment 'APPROVED. Good work.'\`
   - Determine next task:
     - If Test Writer finished tests → Create issue for Code Writer
     - If Code Writer finished code → Check if more tasks in phase
   - Create next appropriate issue

5. IF WORK REJECTED:
   - Add 'status:rework' label
   - Comment with specific feedback on what's wrong
   - Create rework issue for same agent:
     \`gh issue create --title 'REWORK: [original title]' --label 'agent:[test-writer or code-writer]' --label 'status:waiting' --body 'Previous work rejected. Issues: [specific problems]. Fix and resubmit.'\`

## PHASE TRANSITION
When all tasks in a phase pass review:
1. Merge branches: \`git checkout develop && git merge tests-branch && git merge code-branch && git push\`
2. Run full test suite: \`pytest --cov=app\`
3. Test features manually if needed
4. Update PROJECT_PLAN.md: Mark phase complete with [x]
5. Commit: \`git commit -am 'docs: Phase N complete'\`
6. Create first issue for next phase

## PROJECT COMPLETION
When all 10 phases complete:
1. Merge to main: \`git checkout main && git merge develop && git push\`
2. Build and test Docker: \`docker-compose up -d && curl localhost:8787/health\`
3. Update PROJECT_PLAN.md: Mark entire project complete
4. Output: <promise>PROJECT_COMPLETE</promise>

ALL THREE AGENTS EXIT ONLY WHEN YOU OUTPUT PROJECT_COMPLETE.
" --max-iterations 500
```

### Step 5: Launch Test Writer (Terminal 2)

```bash
cd pastor-tests

# Start Ralph Wiggum loop for Test Writer
/ralph-loop "You are the TEST WRITER for AutomatedPastor.

YOUR SOLE JOB: Write failing tests. Do NOT write implementation code.

## EVERY ITERATION - POLL FOR WORK
Check for work assigned to you:
\`\`\`bash
gh issue list --label 'agent:test-writer' --label 'status:waiting' --json number,title,body
\`\`\`

If no issues found:
- Wait 5 minutes: \`sleep 300\`
- Output: 'Test Writer waiting for assignment...'
- Loop continues

When issue found:
1. Mark as in-progress: \`gh issue edit [NUMBER] --remove-label 'status:waiting' --add-label 'status:in-progress'\`
2. Read the issue body for requirements
3. Write comprehensive tests:
   - Happy path tests
   - Edge case tests
   - Error handling tests
   - NO MOCKS - use real SQLite (in-memory), real files
4. Run tests to confirm they FAIL (no implementation yet): \`pytest tests/[file] -v\`
5. Commit: \`git add . && git commit -m 'test: [feature from issue title]'\`
6. Push: \`git push origin tests-branch\`
7. Close your issue: \`gh issue close [NUMBER]\`
8. Create issue for PM to review:
   \`gh issue create --title 'PM Review: Tests for [feature]' --label 'agent:pm-review' --label 'status:waiting' --body 'Tests committed in [SHA]. Ready for PM review. Original issue: #[NUMBER]'\`
9. CLEAR CONTEXT: \`/clear\`
10. Return to polling

## RULES
- Minimum 80% coverage per feature
- Descriptive test names: test_should_[behavior]_when_[condition]
- Tests must be runnable and fail correctly
- Clear context after each issue to keep tokens low

## EXIT CONDITION
Only exit when you see PROJECT_COMPLETE in a PM issue or PROJECT_PLAN.md shows all phases complete.
Output: <promise>TEST_WRITER_DONE</promise>
" --max-iterations 300
```

### Step 6: Launch Code Writer (Terminal 3)

```bash
cd pastor-code

# Start Ralph Wiggum loop for Code Writer
/ralph-loop "You are the CODE WRITER for AutomatedPastor.

YOUR SOLE JOB: Write code to make failing tests pass. Do NOT write tests.

## EVERY ITERATION - POLL FOR WORK
Check for work assigned to you:
\`\`\`bash
gh issue list --label 'agent:code-writer' --label 'status:waiting' --json number,title,body
\`\`\`

If no issues found:
- Wait 5 minutes: \`sleep 300\`
- Output: 'Code Writer waiting for assignment...'
- Loop continues

When issue found:
1. Mark as in-progress: \`gh issue edit [NUMBER] --remove-label 'status:waiting' --add-label 'status:in-progress'\`
2. Pull latest tests: \`git pull origin tests-branch\`
3. Run tests to see what's failing: \`pytest -v --tb=short\`
4. Write MINIMAL code to make tests pass:
   - NO MOCKS - real implementations only
   - Follow existing patterns in codebase
   - Just enough code to pass tests, no more
5. Run tests until ALL pass: \`pytest -v\`
6. Run security scan: \`bandit -r app/\`
7. Fix any security issues
8. Commit: \`git add . && git commit -m 'feat: [feature from issue title]'\`
9. Push: \`git push origin code-branch\`
10. Close your issue: \`gh issue close [NUMBER]\`
11. Create issue for PM to review:
    \`gh issue create --title 'PM Review: Implementation of [feature]' --label 'agent:pm-review' --label 'status:waiting' --body 'Code committed in [SHA]. All tests pass. Security scan clean. Ready for PM review.'\`
12. CLEAR CONTEXT: \`/clear\`
13. Return to polling

## RULES
- Write minimal code - just enough to pass tests
- Security scan must be clean
- No mocks - real database, real files
- Clear context after each issue to keep tokens low

## EXIT CONDITION
Only exit when you see PROJECT_COMPLETE in a PM issue or PROJECT_PLAN.md shows all phases complete.
Output: <promise>CODE_WRITER_DONE</promise>
" --max-iterations 300
```

### Step 7: Monitor Progress

```bash
# Watch test results
watch -n 30 'cd pastor-tests && pytest --tb=short'

# Watch coverage
watch -n 60 'pytest --cov=app --cov-report=term-missing'

# Watch commits
watch -n 10 'git log --oneline -20'

# Watch progress.txt
tail -f progress.txt
```

### Step 8: Manual Intervention Points

The autonomous process will pause and ask for input when:

1. **Ambiguous requirements** - Clarify in PROJECT_PLAN.md
2. **Test failures after 5 iterations** - Review and provide guidance
3. **Security vulnerabilities found** - Approve patches
4. **Phase review fails** - Provide direction
5. **API/design decisions** - Confirm approach

### Cost Estimation

Based on typical Ralph Wiggum runs:

| Phase | Est. Iterations | Est. Cost |
|-------|-----------------|-----------|
| 1. Foundation | 30-40 | $15-25 |
| 2. Skills | 40-50 | $20-30 |
| 3. Panel | 30-40 | $15-25 |
| 4. Green Room | 40-50 | $20-30 |
| 5. Series Planner | 30-40 | $15-25 |
| 6. Collaboration | 30-40 | $15-25 |
| 7. Archive | 20-30 | $10-20 |
| 8. Enhanced | 30-40 | $15-25 |
| 9. UI/UX Design | 40-50 | $20-30 |
| 10. Polish | 20-30 | $10-20 |
| **TOTAL** | **310-410** | **$155-255** |

### Troubleshooting

**Tests won't pass after many iterations:**
```bash
/cancel-ralph  # Stop the loop
# Review progress.txt for stuck points
# Provide specific guidance in CLAUDE.md
# Restart with lower --max-iterations
```

**Agents out of sync:**
```bash
# Force sync
cd pastor-code
git fetch origin tests-branch
git reset --hard origin/tests-branch
```

**Cost running high:**
```bash
/cancel-ralph
# Reduce scope, complete fewer features per phase
# Restart with --max-iterations 20
```

### Success Criteria

The project is complete when:

- [ ] All 10 phases marked complete in PROJECT_PLAN.md
- [ ] All tests pass with >= 80% coverage
- [ ] Security scan is clean
- [ ] Docker builds and runs successfully
- [ ] Web UI accessible at localhost:8787
- [ ] Can generate a complete sermon end-to-end
- [ ] All documentation is current and accurate

---

## Verification Plan

After implementation, test by:

1. **Generate Test Sermon**
   - Input: John 3:16, Theme: "God's Love", Main Point: "We are loved unconditionally"
   - Verify output has clear structure, scripture focus, practical application

2. **Check Survey Concerns Addressed**
   - ✓ Has clear outline structure?
   - ✓ Scripture-focused, not anecdote-heavy?
   - ✓ Includes practical application?
   - ✓ Appropriate intellectual depth?

3. **Review Panel Feedback**
   - Verify each reviewer provides distinct, relevant feedback
   - Confirm feedback is incorporated in final draft

4. **Export and Timing**
   - Export to Word, verify formatting
   - Read aloud, confirm ~15 minutes

---

## Configuration (Confirmed)

| Setting | Value |
|---------|-------|
| **AI Access** | Claude Code CLI (uses Max subscription - no extra cost) |
| **Authentication** | Simple shared password: `TEJS4me` (bcrypt hashed in .env) |
| **Pastor's Name** | Katie (used for personal references in sermons) |
| **Streaming** | Real-time output via WebSocket |
| **Docker Port** | 8787 |

## Remaining Questions (Optional - Can Configure Later)

1. **Church-Specific Details:** Any specific ministries, programs, or ongoing initiatives at University UMC that should be referenced in sermons?

2. **Password:** What password would you like for the web interface? (Can be set during installation)
