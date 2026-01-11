# ONE_SHOT_GUIDE - Autonomous Build with Ralph Wiggum

Build AutomatedPastor using 3 Claude agents coordinated via GitHub Issues, powered by Ralph Wiggum loops.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    3-AGENT RALPH WIGGUM SYSTEM                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Terminal 1: PROJECT MANAGER (AutomatedPastor/)                │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ /ralph-loop "PM prompt..." --max-iterations 500         │   │
│   │   - Creates issues for Test Writer                      │   │
│   │   - Reviews completed work                              │   │
│   │   - Manages phase transitions                           │   │
│   │   - Outputs <promise>PROJECT_COMPLETE</promise>         │   │
│   └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│              ┌───────────────┴───────────────┐                  │
│              ▼                               ▼                  │
│   Terminal 2: TEST WRITER        Terminal 3: CODE WRITER        │
│   (pastor-tests/)                (pastor-code/)                 │
│   ┌──────────────────────┐      ┌──────────────────────┐       │
│   │ /ralph-loop "..."    │      │ /ralph-loop "..."    │       │
│   │  - Polls for work    │      │  - Polls for work    │       │
│   │  - Writes tests      │      │  - Implements code   │       │
│   │  - NO implementation │      │  - NO new tests      │       │
│   └──────────────────────┘      └──────────────────────┘       │
│              │                               │                  │
│              └───────────────┬───────────────┘                  │
│                              ▼                                  │
│                    GitHub Issues Queue                          │
│                    (Coordination layer)                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

**Windows Users:** Run all commands in **Git Bash** (not PowerShell or CMD).

```bash
# Verify all tools are installed
claude --version          # Claude Code CLI
gh auth status            # GitHub CLI (must be authenticated)
git --version             # Git
python --version          # Python 3.11+
docker --version          # Docker (optional, for final deployment)
```

---

## Step 1: Initialize Repository

```bash
cd D:/Projects/AutomatedPastor

# Initialize git if not already done
git init
git checkout -b main

# Create complete directory structure
mkdir -p tests/unit tests/integration tests/e2e
mkdir -p agents prompts/system_prompts prompts/templates
mkdir -p skills/sermon skills/dev
mkdir -p static/css static/js templates data
mkdir -p uploads exports database
mkdir -p .github/workflows .claude

# Create .gitignore
cat > .gitignore << 'EOF'
__pycache__/
*.pyc
.env
database/*.db
uploads/*
exports/*
.claude/
venv/
node_modules/
PROJECT_COMPLETE
*.egg-info/
dist/
build/
.pytest_cache/
htmlcov/
.coverage
EOF

# Create requirements.txt
cat > requirements.txt << 'EOF'
Flask==3.0.0
Flask-SocketIO==5.3.6
python-docx==1.0.0
bcrypt==4.1.2
Werkzeug==3.0.1
python-engineio==4.8.1
python-socketio==5.10.0
EOF

# Create requirements-dev.txt
cat > requirements-dev.txt << 'EOF'
pytest==7.4.3
pytest-cov==4.1.0
bandit==1.7.6
safety==2.3.5
EOF

# Create test fixtures (conftest.py)
cat > tests/conftest.py << 'EOF'
"""Shared test fixtures - NO MOCKS, real implementations only."""
import pytest
import tempfile
import sqlite3
import os

@pytest.fixture
def db_connection():
    """Real in-memory SQLite database for testing."""
    conn = sqlite3.connect(':memory:')
    yield conn
    conn.close()

@pytest.fixture
def temp_dir():
    """Real temporary directory for file operation tests."""
    with tempfile.TemporaryDirectory() as d:
        yield d

@pytest.fixture
def app_config(temp_dir):
    """Test configuration with real paths."""
    return {
        'DATABASE': ':memory:',
        'UPLOAD_FOLDER': os.path.join(temp_dir, 'uploads'),
        'EXPORT_FOLDER': os.path.join(temp_dir, 'exports'),
        'TESTING': True
    }
EOF

# Create empty __init__.py files
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py
touch tests/e2e/__init__.py

# Create Python virtual environment and install dependencies
python -m venv venv
source venv/Scripts/activate  # Windows Git Bash
pip install -r requirements.txt -r requirements-dev.txt

# Initial commit
git add .
git commit -m "chore: initialize project structure with test infrastructure"

# Create GitHub repo and push
gh repo create AutomatedPastor --public --source=. --push

# Create and push develop branch
git checkout -b develop
git push -u origin develop
```

---

## Step 2: Set Up Git Worktrees

Each agent works in its own directory to avoid conflicts:

```bash
# From D:/Projects/AutomatedPastor
cd ..

# Create worktree for Test Writer
git -C AutomatedPastor worktree add ./pastor-tests -b tests-branch

# Create worktree for Code Writer
git -C AutomatedPastor worktree add ./pastor-code -b code-branch

# Push the new branches
cd AutomatedPastor
git push -u origin tests-branch
git push -u origin code-branch

# Verify structure
ls -la ..
# Should show:
# AutomatedPastor/   (PM works here, on develop)
# pastor-tests/      (Test Writer works here, on tests-branch)
# pastor-code/       (Code Writer works here, on code-branch)
```

---

## Step 3: Create GitHub Labels

```bash
cd D:/Projects/AutomatedPastor

# Agent assignment labels
gh label create "agent:test-writer" --color "1d76db" --description "Assigned to Test Writer"
gh label create "agent:code-writer" --color "0e8a16" --description "Assigned to Code Writer"
gh label create "agent:pm-review" --color "d93f0b" --description "Ready for PM review"

# Status labels
gh label create "status:waiting" --color "fbca04" --description "Waiting to be picked up"
gh label create "status:in-progress" --color "6f42c1" --description "Currently being worked"
gh label create "status:rework" --color "b60205" --description "Needs rework"

# Work type labels
gh label create "type:tests" --color "c5def5" --description "Test writing work"
gh label create "type:implementation" --color "bfd4f2" --description "Code implementation work"

# Phase labels (1-10)
for i in 1 2 3 4 5 6 7 8 9 10; do
  gh label create "phase:$i" --color "c5def5" --description "Phase $i work"
done
```

---

## Step 4: Bootstrap First Issue

Create the first work item to kick off the cycle:

```bash
gh issue create \
  --title "Write tests for Flask app with health endpoint" \
  --label "agent:test-writer" \
  --label "status:waiting" \
  --label "type:tests" \
  --label "phase:1" \
  --body "## Feature
Create Flask application with /health endpoint.

## Acceptance Criteria
- Test that Flask app can be created and configured
- Test GET /health returns HTTP 200
- Test response body is JSON: {\"status\": \"healthy\"}
- Test that app runs on port 8787

## Files to Create
- tests/unit/test_app.py

## Notes
- Use real Flask test client (NO MOCKS)
- Tests should FAIL initially (no implementation yet)
- See tests/conftest.py for shared fixtures"
```

---

## Step 5: Launch All Three Agents

Open **3 separate Git Bash terminals** and run one agent in each.

### Terminal 1 - Project Manager

```bash
cd D:/Projects/AutomatedPastor
source venv/Scripts/activate

/ralph-loop "You are the PROJECT MANAGER for AutomatedPastor.

## YOUR ROLE
- Break PROJECT_PLAN.md phases into discrete tasks
- Create GitHub Issues to assign work to Test Writer and Code Writer
- Review completed work and approve/reject
- Manage phase transitions
- Signal project completion

## EVERY ITERATION

### Step 1: Check for work to review
\`\`\`bash
gh issue list --label 'agent:pm-review' --label 'status:waiting' --json number,title,body,labels
\`\`\`

### Step 2: If review work found
Mark it in-progress:
\`\`\`bash
gh issue edit [NUMBER] --remove-label 'status:waiting' --add-label 'status:in-progress'
\`\`\`

Pull latest code:
\`\`\`bash
git fetch origin tests-branch code-branch
git checkout develop
git merge origin/tests-branch --no-edit || true
git merge origin/code-branch --no-edit || true
\`\`\`

**IMPORTANT: Determine the type of review:**

**If reviewing TEST WRITER work (has label 'type:tests'):**
- Tests are EXPECTED to fail (no implementation yet)
- Check that test files exist and are syntactically correct
- Verify tests cover the acceptance criteria from the original issue
- Verify NO MOCKS are used (real database, real files)
- Run: \`python -m py_compile tests/[path].py\` to check syntax
- If tests look correct → APPROVE
- Create Code Writer issue to implement the feature

**If reviewing CODE WRITER work (has label 'type:implementation'):**
- Run tests: \`pytest -v\`
- ALL tests must PASS
- Check coverage: \`pytest --cov=. --cov-fail-under=80\`
- Run security scan: \`bandit -r . -x ./tests,./venv\`
- If all pass → APPROVE
- Check PROJECT_PLAN.md for next task in current phase

**APPROVE workflow:**
\`\`\`bash
gh issue close [NUMBER] --comment 'APPROVED. Good work.'
\`\`\`
Then create the next appropriate issue (see Step 3).

**REJECT workflow:**
\`\`\`bash
gh issue close [NUMBER] --comment 'REJECTED: [specific problems found]'
gh issue create --title 'REWORK: [original title]' \\
  --label 'agent:[test-writer or code-writer]' \\
  --label 'status:waiting' \\
  --label 'status:rework' \\
  --label '[type:tests or type:implementation]' \\
  --body 'Previous work rejected. Issues: [specific problems]. Fix and resubmit.'
\`\`\`

### Step 3: If no review work, check if new work needed
\`\`\`bash
gh issue list --label 'agent:test-writer' --label 'status:waiting' --json number
gh issue list --label 'agent:code-writer' --label 'status:waiting' --json number
\`\`\`

If BOTH are empty, create the next task from PROJECT_PLAN.md:
- Find the current phase (first phase with unchecked items)
- Find the first unchecked \`- [ ]\` item
- Create a test-writer issue for that feature:
\`\`\`bash
gh issue create --title 'Write tests for [feature]' \\
  --label 'agent:test-writer' \\
  --label 'status:waiting' \\
  --label 'type:tests' \\
  --label 'phase:[N]' \\
  --body '## Feature
[Feature description from PROJECT_PLAN.md]

## Acceptance Criteria
- Test [specific behavior 1]
- Test [specific behavior 2]
- Test error handling

## Files to Create
- tests/[appropriate path]/test_[feature].py'
\`\`\`

### Step 4: Phase Transitions
When ALL items in a phase are checked off in PROJECT_PLAN.md:
1. Merge to develop: Already done during reviews
2. Run full test suite: \`pytest --cov=. -v\`
3. Update PROJECT_PLAN.md: Change \`- [ ]\` to \`- [x]\` for completed items
4. Commit: \`git add PROJECT_PLAN.md && git commit -m 'docs: Phase N complete' && git push\`
5. Create first issue for next phase

### Step 5: Project Completion
When ALL 10 phases are complete:
1. Merge to main: \`git checkout main && git merge develop && git push\`
2. Test Docker: \`docker-compose build && docker-compose up -d\`
3. Verify health: \`curl http://localhost:8787/health\`
4. Create marker: \`touch PROJECT_COMPLETE\`
5. Output: <promise>PROJECT_COMPLETE</promise>

## RULES
- Do ONE review or create ONE issue per iteration, then let the loop continue
- Be specific in issue descriptions with file paths and acceptance criteria
- Always reference PROJECT_PLAN.md for current phase status
- Test Writer reviews: Tests SHOULD fail (that's correct!)
- Code Writer reviews: Tests MUST pass
" --max-iterations 500
```

### Terminal 2 - Test Writer

```bash
cd D:/Projects/pastor-tests
source ../AutomatedPastor/venv/Scripts/activate

/ralph-loop "You are the TEST WRITER for AutomatedPastor.

## YOUR ROLE
Write failing tests. You must NEVER write implementation code.

## EVERY ITERATION

### Step 1: Check for assigned work
\`\`\`bash
gh issue list --label 'agent:test-writer' --label 'status:waiting' --json number,title,body
\`\`\`

### Step 2: If no work found
Output 'Test Writer: No work available, waiting...' and exit this iteration.

### Step 3: If work found
Note the issue NUMBER from the output.

**A. Claim the issue:**
\`\`\`bash
gh issue edit [NUMBER] --remove-label 'status:waiting' --add-label 'status:in-progress'
\`\`\`

**B. Parse the issue body for:**
- Feature to test
- Acceptance criteria
- Files to create

**C. Write comprehensive tests:**
- Happy path tests (normal operation)
- Edge case tests (boundary conditions)
- Error handling tests (invalid input, failures)
- Use descriptive names: \`test_should_[behavior]_when_[condition]\`

**CRITICAL - NO MOCKS:**
- Use real SQLite: \`sqlite3.connect(':memory:')\`
- Use real temp files: \`tempfile.TemporaryDirectory()\`
- Use real Flask test client: \`app.test_client()\`
- Import fixtures from conftest.py

**D. Verify tests are syntactically correct:**
\`\`\`bash
python -m py_compile tests/[path]/test_[feature].py
\`\`\`

**E. Run tests (they SHOULD fail - no implementation yet):**
\`\`\`bash
pytest tests/[path]/test_[feature].py -v
\`\`\`
Failures are EXPECTED and CORRECT at this stage.

**F. Commit and push:**
\`\`\`bash
git add .
git commit -m 'test: add tests for [feature from issue title]'
git push origin tests-branch
\`\`\`

**G. Close your issue:**
\`\`\`bash
gh issue close [NUMBER]
\`\`\`

**H. Create PM review issue:**
\`\`\`bash
gh issue create --title 'PM Review: Tests for [feature]' \\
  --label 'agent:pm-review' \\
  --label 'status:waiting' \\
  --label 'type:tests' \\
  --body 'Tests committed to tests-branch.

## What was done
- Created test file: tests/[path]/test_[feature].py
- Tests cover: [list what is tested]
- Tests use real implementations (no mocks)

## Expected status
Tests FAIL because implementation does not exist yet. This is correct.

Ready for PM review. Original issue: #[NUMBER]'
\`\`\`

**I. Exit this iteration** (Ralph Wiggum will loop back)

## RULES
- Write tests ONLY - never write implementation code
- Minimum 3 tests per feature
- NO MOCKS - real database, real files, real Flask client
- Test names: \`test_should_[behavior]_when_[condition]\`
- Tests SHOULD fail initially - that proves they test real behavior
" --max-iterations 300
```

### Terminal 3 - Code Writer

```bash
cd D:/Projects/pastor-code
source ../AutomatedPastor/venv/Scripts/activate

/ralph-loop "You are the CODE WRITER for AutomatedPastor.

## YOUR ROLE
Write code to make failing tests pass. You must NEVER write new tests.

## EVERY ITERATION

### Step 1: Check for assigned work
\`\`\`bash
gh issue list --label 'agent:code-writer' --label 'status:waiting' --json number,title,body
\`\`\`

### Step 2: If no work found
Output 'Code Writer: No work available, waiting...' and exit this iteration.

### Step 3: If work found
Note the issue NUMBER from the output.

**A. Claim the issue:**
\`\`\`bash
gh issue edit [NUMBER] --remove-label 'status:waiting' --add-label 'status:in-progress'
\`\`\`

**B. Merge latest tests into your branch:**
\`\`\`bash
git fetch origin tests-branch
git merge origin/tests-branch --no-edit -m 'Merge latest tests from tests-branch'
\`\`\`

**C. Run tests to see what's failing:**
\`\`\`bash
pytest -v --tb=short
\`\`\`
Review the failures to understand what needs implementing.

**D. Write MINIMAL code to pass tests:**
- Just enough code to make tests pass - no more
- NO MOCKS - real implementations only
- Follow existing patterns in the codebase
- Keep it simple and clean

**E. Run tests until ALL pass:**
\`\`\`bash
pytest -v
\`\`\`
Iterate on your code until all tests are green.

**F. Check coverage:**
\`\`\`bash
pytest --cov=. --cov-report=term-missing
\`\`\`
Aim for 80%+ coverage.

**G. Run security scan:**
\`\`\`bash
bandit -r . -x ./tests,./venv || echo 'Security issues found - fix them'
\`\`\`
Fix any security issues before proceeding.

**H. Commit and push:**
\`\`\`bash
git add .
git commit -m 'feat: implement [feature from issue title]'
git push origin code-branch
\`\`\`

**I. Close your issue:**
\`\`\`bash
gh issue close [NUMBER]
\`\`\`

**J. Create PM review issue:**
\`\`\`bash
gh issue create --title 'PM Review: Implementation of [feature]' \\
  --label 'agent:pm-review' \\
  --label 'status:waiting' \\
  --label 'type:implementation' \\
  --body 'Code committed to code-branch.

## What was done
- Implemented: [feature description]
- Files created/modified: [list files]

## Test results
- All tests: PASSING
- Coverage: [X]%
- Security scan: CLEAN

Ready for PM review. Original issue: #[NUMBER]'
\`\`\`

**K. Exit this iteration** (Ralph Wiggum will loop back)

## RULES
- Write code ONLY - never write new tests
- MINIMAL code - just enough to pass tests
- NO MOCKS - real database, real files, real implementations
- Security scan must be clean before submitting
" --max-iterations 300
```

---

## Step 6: Monitor Progress

In a **4th terminal** (optional):

```bash
cd D:/Projects/AutomatedPastor

# Watch GitHub Issues
watch -n 30 'gh issue list --state all | head -20'

# Watch commits across all branches
watch -n 10 'git log --oneline --all -20'

# Watch for completion
while [ ! -f PROJECT_COMPLETE ]; do
    echo "Project running... $(date)"
    gh issue list --state open
    sleep 60
done
echo "PROJECT COMPLETE!"
```

---

## How the Cycle Works

```
1. Bootstrap issue exists: "Write tests for Flask app"
   └─► agent:test-writer, status:waiting

2. Test Writer picks up issue
   ├─► Marks status:in-progress
   ├─► Writes test_app.py (tests FAIL - no implementation)
   ├─► Commits to tests-branch
   ├─► Creates "PM Review: Tests for Flask app"
   └─► agent:pm-review, status:waiting, type:tests

3. PM reviews Test Writer's work
   ├─► Sees type:tests label → expects tests to FAIL
   ├─► Verifies tests exist and are syntactically correct
   ├─► APPROVES
   ├─► Creates "Implement Flask app with health endpoint"
   └─► agent:code-writer, status:waiting, type:implementation

4. Code Writer picks up issue
   ├─► Marks status:in-progress
   ├─► Merges tests-branch into code-branch
   ├─► Writes app.py to make tests PASS
   ├─► Commits to code-branch
   ├─► Creates "PM Review: Implementation of Flask app"
   └─► agent:pm-review, status:waiting, type:implementation

5. PM reviews Code Writer's work
   ├─► Sees type:implementation label → expects tests to PASS
   ├─► Runs pytest → ALL GREEN
   ├─► Checks coverage → 80%+
   ├─► APPROVES
   ├─► Checks PROJECT_PLAN.md for next task
   └─► Creates next test-writer issue

6. Cycle repeats until all phases complete

7. PM outputs <promise>PROJECT_COMPLETE</promise>
   └─► All Ralph Wiggum loops exit
```

---

## Troubleshooting

### Stop all agents
Press `Ctrl+C` in each terminal, or:
```bash
# Ralph Wiggum should handle graceful shutdown
# If needed, close the terminal windows
```

### Restart fresh
```bash
cd D:/Projects/AutomatedPastor

# Close all open issues
gh issue list --state open --json number -q '.[].number' | xargs -I {} gh issue close {} --comment "Resetting"

# Remove completion marker
rm -f PROJECT_COMPLETE

# Re-create bootstrap issue
gh issue create \
  --title "Write tests for Flask app with health endpoint" \
  --label "agent:test-writer" \
  --label "status:waiting" \
  --label "type:tests" \
  --label "phase:1" \
  --body "[same body as Step 4]"
```

### Agent stuck / not finding work
```bash
# Check issue labels
gh issue list --label "agent:test-writer" --state open
gh issue list --label "agent:code-writer" --state open
gh issue list --label "agent:pm-review" --state open

# Verify status labels
gh issue view [NUMBER] --json labels
```

### Git conflicts
```bash
cd D:/Projects/AutomatedPastor
git checkout develop
git fetch --all
git merge origin/tests-branch --no-edit
git merge origin/code-branch --no-edit
git push
```

### Tests failing unexpectedly
```bash
# Activate venv first
source venv/Scripts/activate

# Run with verbose output
pytest -v --tb=long

# Check for import issues
python -c "import app"
```

---

## Completion Criteria

The project is complete when:

- [ ] All 10 phases marked `[x]` in PROJECT_PLAN.md
- [ ] All tests pass: `pytest --cov=. --cov-fail-under=80`
- [ ] Security scan clean: `bandit -r . -x ./tests,./venv`
- [ ] Docker builds: `docker-compose build`
- [ ] Health endpoint works: `curl http://localhost:8787/health`
- [ ] PM has output `<promise>PROJECT_COMPLETE</promise>`
- [ ] `PROJECT_COMPLETE` file exists in repo root
