# AutomatedPastor Launch Guide

**Quick-start guide for launching the 3-agent autonomous build system.**

---

## Pre-Flight Checklist

Run these commands in **Git Bash** to verify everything is ready:

```bash
cd D:/Projects/AutomatedPastor

# 1. Verify tools
claude --version          # Should show Claude Code CLI version
gh auth status            # Should show "Logged in to github.com"
git --version             # Should show git version
python --version          # Should show Python 3.11+

# 2. Verify repo structure
ls -la ../pastor-tests    # Test Writer worktree
ls -la ../pastor-code     # Code Writer worktree
git worktree list         # Should show all 3 directories

# 3. Verify GitHub issue exists
gh issue list             # Should show Issue #1

# 4. Verify venv and dependencies
source venv/Scripts/activate
python -c "import flask; import pytest; print('Dependencies OK')"

# 5. Verify ralph-loop is available
# In Claude Code, type:
/ralph-loop help
```

---

## Launch Sequence

### Step 1: Open 3 Git Bash Terminals

Arrange them so you can see all three at once.

### Step 2: Launch Project Manager (Terminal 1)

```bash
cd D:/Projects/AutomatedPastor
source venv/Scripts/activate
git checkout develop
git pull origin develop
```

Then start Claude Code and paste the PM prompt:
```bash
claude
```

Once in Claude Code, copy the entire `/ralph-loop "..."` command from `agents/pm_prompt.md` and paste it.

**Or use the shorthand:**
```
/ralph-loop "$(cat agents/pm_prompt.md | grep -A 5000 'ralph-loop "')"
```

### Step 3: Launch Test Writer (Terminal 2)

```bash
cd D:/Projects/pastor-tests
source ../AutomatedPastor/venv/Scripts/activate
git checkout tests-branch
git pull origin tests-branch
```

Then start Claude Code:
```bash
claude
```

Copy the `/ralph-loop "..."` command from `agents/test_writer_prompt.md`.

### Step 4: Launch Code Writer (Terminal 3)

```bash
cd D:/Projects/pastor-code
source ../AutomatedPastor/venv/Scripts/activate
git checkout code-branch
git pull origin code-branch
```

Then start Claude Code:
```bash
claude
```

Copy the `/ralph-loop "..."` command from `agents/code_writer_prompt.md`.

---

## What Happens Next

Once all 3 agents are running:

1. **Test Writer** will detect Issue #1 and start writing tests
2. **Test Writer** creates a PM review issue when done
3. **PM** reviews the tests, approves, creates Code Writer issue
4. **Code Writer** implements the code to pass tests
5. **Code Writer** creates a PM review issue when done
6. **PM** reviews implementation, approves, creates next Test Writer issue
7. **Cycle repeats** for all features in all 10 phases
8. **PM outputs** `<promise>PROJECT_COMPLETE</promise>` when done

---

## Monitoring Progress

### GitHub Issues Dashboard
```bash
# Watch issues in real-time
watch -n 30 'gh issue list --state all | head -20'
```

### Git Commits
```bash
# Watch commits across all branches
watch -n 10 'git log --oneline --all -20'
```

### Test Results
```bash
# In AutomatedPastor directory
watch -n 60 'pytest --tb=short 2>&1 | tail -20'
```

---

## Stopping the Agents

### Graceful Stop
Press `Ctrl+C` in each terminal. The ralph-loop should handle graceful shutdown.

### Emergency Stop
Close the terminal windows.

### Cancel Ralph Loop
In any Claude Code session:
```
/cancel-ralph
```

---

## Troubleshooting

### Agent Not Picking Up Work

```bash
# Check issue labels
gh issue list --label "agent:test-writer" --label "status:waiting"
gh issue list --label "agent:code-writer" --label "status:waiting"
gh issue list --label "agent:pm-review" --label "status:waiting"

# Check for stuck in-progress issues
gh issue list --label "status:in-progress"
```

### Git Push Fails

```bash
# Re-authenticate if needed
gh auth login

# Force push (careful!)
git push origin BRANCH_NAME --force-with-lease
```

### Tests Not Found

```bash
# Make sure tests are on the correct branch
cd ../pastor-code
git fetch origin tests-branch
git merge origin/tests-branch
```

### Coverage Too Low

The Code Writer may need to simplify the implementation or the PM may need to request more tests.

### Security Scan Fails

Check the bandit output and fix the issues. Common fixes:
- SQL injection → Use parameterized queries
- Hardcoded secrets → Use environment variables

---

## Recovery Procedures

### Restart Fresh

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
  --body '## Feature
Create Flask application with /health endpoint.

## Acceptance Criteria
- Test that Flask app can be created with create_app()
- Test GET /health returns HTTP 200
- Test response body is JSON: {"status": "healthy"}
- Test that app can be configured with custom config dict

## Files to Create
- tests/unit/test_app.py

## Technical Notes
- Use real Flask test client (NO MOCKS)
- Tests should FAIL initially (no implementation yet)
- See tests/conftest.py for shared fixtures'
```

### Sync Branches

```bash
cd D:/Projects/AutomatedPastor
git checkout develop
git fetch --all
git merge origin/tests-branch --no-edit || true
git merge origin/code-branch --no-edit || true
git push origin develop
```

---

## Success Criteria

The project is complete when:

- [ ] All 10 phases marked `[x]` in PROJECT_PLAN.md
- [ ] All tests pass: `pytest --cov=. --cov-fail-under=80`
- [ ] Security scan clean: `bandit -r . -x ./tests,./venv`
- [ ] Docker builds: `docker-compose build`
- [ ] Health endpoint works: `curl http://localhost:8787/health`
- [ ] PM has output `<promise>PROJECT_COMPLETE</promise>`
- [ ] `PROJECT_COMPLETE` file exists in repo root

---

## Estimated Timeline

| Phase | Est. Time | Features |
|-------|-----------|----------|
| 1 | 2-3 hours | Foundation, Flask, Docker |
| 2 | 3-4 hours | Skills, Multi-agent |
| 3 | 2-3 hours | Review Panel |
| 4 | 3-4 hours | Green Room Chat |
| 5 | 2-3 hours | Series Planner |
| 6 | 2-3 hours | Collaboration |
| 7 | 2-3 hours | Archive |
| 8 | 2-3 hours | Enhanced Features |
| 9 | 3-4 hours | UI/UX Design |
| 10 | 1-2 hours | Polish |
| **Total** | **22-32 hours** | Full application |

*Times are estimates and depend on complexity and rework cycles.*

---

## Notes

- **Windows Users:** All commands assume Git Bash, not PowerShell/CMD
- **Network:** Requires internet for GitHub API calls
- **Resources:** Each Claude Code instance uses API credits
- **Parallelism:** All 3 agents run simultaneously but coordinate via issues
