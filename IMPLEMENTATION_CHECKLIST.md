# AutomatedPastor Implementation Checklist

This checklist is derived from ONE_SHOT_GUIDE.md. Check off items as completed.

---

## Step 1: Initialize Repository

### 1.1 Git Setup
- [x] Initialize git repository (`git init`)
- [x] Create main branch (`git checkout -b main`)

### 1.2 Directory Structure
- [x] Create `tests/unit/` directory
- [x] Create `tests/integration/` directory
- [x] Create `tests/e2e/` directory
- [x] Create `agents/` directory
- [x] Create `prompts/system_prompts/` directory
- [x] Create `prompts/templates/` directory
- [x] Create `skills/sermon/` directory
- [x] Create `skills/dev/` directory
- [x] Create `static/css/` directory
- [x] Create `static/js/` directory
- [x] Create `templates/` directory
- [x] Create `data/` directory
- [x] Create `uploads/` directory
- [x] Create `exports/` directory
- [x] Create `database/` directory
- [x] Create `.github/workflows/` directory
- [x] Create `.claude/` directory

### 1.3 Configuration Files
- [x] Create `.gitignore` with Python/project exclusions
- [x] Verify `requirements.txt` exists with production deps (Flask, Flask-SocketIO, python-docx, bcrypt, Werkzeug)
- [x] Verify `requirements-dev.txt` exists with dev deps (pytest, pytest-cov, bandit, safety)

### 1.4 Test Infrastructure
- [x] Create `tests/conftest.py` with shared fixtures (NO MOCKS - real DB, real files)
- [x] Create `tests/__init__.py`
- [x] Create `tests/unit/__init__.py`
- [x] Create `tests/integration/__init__.py`
- [x] Create `tests/e2e/__init__.py`

### 1.5 Python Environment
- [x] Create Python virtual environment (`python -m venv venv`)
- [x] Activate virtual environment
- [x] Install production dependencies (`pip install -r requirements.txt`)
- [x] Install dev dependencies (`pip install -r requirements-dev.txt`)

### 1.6 Initial Commit & GitHub
- [x] Stage all files (`git add .`)
- [x] Make initial commit (`git commit -m "chore: initialize project structure with test infrastructure"`)
- [x] Create GitHub repository (`gh repo create AutomatedPastor --public --source=. --push`)
- [x] Create develop branch (`git checkout -b develop`)
- [x] Push develop branch (`git push -u origin develop`)

---

## Step 2: Set Up Git Worktrees

### 2.1 Create Worktrees
- [x] Navigate to parent directory (`cd ..`)
- [x] Create worktree for Test Writer (`git worktree add ../pastor-tests tests-branch`)
- [x] Create worktree for Code Writer (`git worktree add ../pastor-code code-branch`)

### 2.2 Push New Branches
- [x] Navigate back to AutomatedPastor (`cd AutomatedPastor`)
- [x] Push tests-branch (`git push -u origin tests-branch`)
- [x] Push code-branch (`git push -u origin code-branch`)

### 2.3 Verify Structure
- [x] Confirm `D:/Projects/AutomatedPastor/` exists (PM works here, on develop)
- [x] Confirm `D:/Projects/pastor-tests/` exists (Test Writer, on tests-branch)
- [x] Confirm `D:/Projects/pastor-code/` exists (Code Writer, on code-branch)

---

## Step 3: Create GitHub Labels

### 3.1 Agent Assignment Labels
- [x] Create label `agent:test-writer` (color: 1d76db, desc: "Assigned to Test Writer")
- [x] Create label `agent:code-writer` (color: 0e8a16, desc: "Assigned to Code Writer")
- [x] Create label `agent:pm-review` (color: d93f0b, desc: "Ready for PM review")

### 3.2 Status Labels
- [x] Create label `status:waiting` (color: fbca04, desc: "Waiting to be picked up")
- [x] Create label `status:in-progress` (color: 6f42c1, desc: "Currently being worked")
- [x] Create label `status:rework` (color: b60205, desc: "Needs rework")

### 3.3 Work Type Labels
- [x] Create label `type:tests` (color: c5def5, desc: "Test writing work")
- [x] Create label `type:implementation` (color: bfd4f2, desc: "Code implementation work")

### 3.4 Phase Labels
- [x] Create label `phase:1` (color: c5def5)
- [x] Create label `phase:2` (color: c5def5)
- [x] Create label `phase:3` (color: c5def5)
- [x] Create label `phase:4` (color: c5def5)
- [x] Create label `phase:5` (color: c5def5)
- [x] Create label `phase:6` (color: c5def5)
- [x] Create label `phase:7` (color: c5def5)
- [x] Create label `phase:8` (color: c5def5)
- [x] Create label `phase:9` (color: c5def5)
- [x] Create label `phase:10` (color: c5def5)

---

## Step 4: Bootstrap First Issue

- [x] Create first GitHub issue for Test Writer:
  - Title: "Write tests for Flask app with health endpoint"
  - Labels: `agent:test-writer`, `status:waiting`, `type:tests`, `phase:1`
  - Body: Feature description, acceptance criteria, files to create
  - **Issue #1 created:** https://github.com/biomed1205/AutomatedPastor/issues/1

---

## Step 5: Create Agent Prompt Files (Optional but Recommended)

### 5.1 Project Manager Prompt
- [x] Create `agents/pm_prompt.md` with PM instructions

### 5.2 Test Writer Prompt
- [x] Create `agents/test_writer_prompt.md` with Test Writer instructions

### 5.3 Code Writer Prompt
- [x] Create `agents/code_writer_prompt.md` with Code Writer instructions

---

## Step 6: Launch Agents (Manual Step - 3 Terminals)

### Terminal 1: Project Manager
- [ ] Open Git Bash terminal
- [ ] Navigate to `D:/Projects/AutomatedPastor`
- [ ] Activate venv: `source venv/Scripts/activate`
- [ ] Launch PM with `/ralph-loop` command

### Terminal 2: Test Writer
- [ ] Open Git Bash terminal
- [ ] Navigate to `D:/Projects/pastor-tests`
- [ ] Activate venv: `source ../AutomatedPastor/venv/Scripts/activate`
- [ ] Launch Test Writer with `/ralph-loop` command

### Terminal 3: Code Writer
- [ ] Open Git Bash terminal
- [ ] Navigate to `D:/Projects/pastor-code`
- [ ] Activate venv: `source ../AutomatedPastor/venv/Scripts/activate`
- [ ] Launch Code Writer with `/ralph-loop` command

---

## Completion Criteria

- [ ] All 10 phases marked `[x]` in PROJECT_PLAN.md
- [ ] All tests pass: `pytest --cov=. --cov-fail-under=80`
- [ ] Security scan clean: `bandit -r . -x ./tests,./venv`
- [ ] Docker builds: `docker-compose build`
- [ ] Health endpoint works: `curl http://localhost:8787/health`
- [ ] PM has output `<promise>PROJECT_COMPLETE</promise>`
- [ ] `PROJECT_COMPLETE` file exists in repo root

---

## Progress Tracking

| Step | Status | Date Completed |
|------|--------|----------------|
| Step 1: Initialize Repository | **COMPLETE** | 2026-01-10 |
| Step 2: Set Up Git Worktrees | **COMPLETE** | 2026-01-10 |
| Step 3: Create GitHub Labels | **COMPLETE** | 2026-01-10 |
| Step 4: Bootstrap First Issue | **COMPLETE** | 2026-01-10 |
| Step 5: Create Agent Prompts | **COMPLETE** | 2026-01-10 |
| Step 6: Launch Agents | Not Started | |
| Project Complete | Not Started | |

---

## Notes

- **Windows Users:** Run all commands in Git Bash (not PowerShell or CMD)
- **TDD Rule:** Write tests FIRST, then code to pass them
- **NO MOCKS:** Use real database, real files, real CLI
- **Commit Strategy:** Commit after every test file and every implementation file

## Blockers

None currently.
