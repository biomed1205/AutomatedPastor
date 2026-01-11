#!/bin/bash
# WSL Pre-flight Check for AutomatedPastor 3-Agent System
# Run this script in WSL to verify everything is ready

echo "=============================================="
echo "  AutomatedPastor WSL Environment Check"
echo "=============================================="
echo ""

PASS=0
FAIL=0

check() {
    local name="$1"
    local cmd="$2"
    printf "%-40s" "Checking $name..."
    if eval "$cmd" > /dev/null 2>&1; then
        echo "✅ OK"
        PASS=$((PASS + 1))
    else
        echo "❌ FAILED"
        FAIL=$((FAIL + 1))
    fi
}

check_output() {
    local name="$1"
    local cmd="$2"
    printf "%-40s" "Checking $name..."
    local result=$(eval "$cmd" 2>/dev/null)
    if [[ -n "$result" ]]; then
        echo "✅ $result"
        PASS=$((PASS + 1))
    else
        echo "❌ FAILED"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== 1. BASIC TOOLS ==="
check_output "bash version" "bash --version | head -1 | cut -d' ' -f4"
check_output "git version" "git --version | cut -d' ' -f3"
check "jq installed" "which jq"
check "curl installed" "which curl"
check "perl installed" "which perl"
check "sed installed" "which sed"
check "awk installed" "which awk"
echo ""

echo "=== 2. CLAUDE CODE CLI ==="
check "claude command exists" "which claude"
check_output "claude version" "claude --version 2>/dev/null | head -1"
echo ""

echo "=== 3. GITHUB CLI ==="
check "gh command exists" "which gh"
check_output "gh version" "gh --version | head -1 | cut -d' ' -f3"
printf "%-40s" "Checking gh authentication..."
if gh auth status > /dev/null 2>&1; then
    echo "✅ Authenticated"
    PASS=$((PASS + 1))
else
    echo "❌ NOT AUTHENTICATED - run 'gh auth login'"
    FAIL=$((FAIL + 1))
fi
echo ""

echo "=== 4. PYTHON ==="
check "python3 exists" "which python3"
check_output "python3 version" "python3 --version | cut -d' ' -f2"
check "pip3 exists" "which pip3"
echo ""

echo "=== 5. PROJECT DIRECTORIES ==="
check "Main repo accessible" "test -d /mnt/d/Projects/AutomatedPastor"
check "Test worktree accessible" "test -d /mnt/d/Projects/pastor-tests"
check "Code worktree accessible" "test -d /mnt/d/Projects/pastor-code"
check "venv exists" "test -d /mnt/d/Projects/AutomatedPastor/venv"
echo ""

echo "=== 6. GIT CONFIGURATION ==="
cd /mnt/d/Projects/AutomatedPastor
check_output "Current branch" "git branch --show-current"
check "Git remote configured" "git remote get-url origin"
printf "%-40s" "Checking git push access..."
if git ls-remote origin > /dev/null 2>&1; then
    echo "✅ Can reach remote"
    PASS=$((PASS + 1))
else
    echo "❌ Cannot reach remote"
    FAIL=$((FAIL + 1))
fi
echo ""

echo "=== 7. WORKTREE STATUS ==="
printf "%-40s" "pastor-tests branch..."
cd /mnt/d/Projects/pastor-tests
BRANCH=$(git branch --show-current)
if [[ "$BRANCH" == "tests-branch" ]]; then
    echo "✅ tests-branch"
    PASS=$((PASS + 1))
else
    echo "❌ Wrong branch: $BRANCH"
    FAIL=$((FAIL + 1))
fi

printf "%-40s" "pastor-code branch..."
cd /mnt/d/Projects/pastor-code
BRANCH=$(git branch --show-current)
if [[ "$BRANCH" == "code-branch" ]]; then
    echo "✅ code-branch"
    PASS=$((PASS + 1))
else
    echo "❌ Wrong branch: $BRANCH"
    FAIL=$((FAIL + 1))
fi
echo ""

echo "=== 8. GITHUB ISSUES ==="
cd /mnt/d/Projects/AutomatedPastor
printf "%-40s" "Checking Issue #1 exists..."
if gh issue view 1 > /dev/null 2>&1; then
    echo "✅ Issue #1 exists"
    PASS=$((PASS + 1))
else
    echo "❌ Issue #1 not found"
    FAIL=$((FAIL + 1))
fi

printf "%-40s" "Checking Issue #1 labels..."
LABELS=$(gh issue view 1 --json labels -q '.labels[].name' 2>/dev/null | tr '\n' ' ')
if [[ "$LABELS" == *"agent:test-writer"* ]] && [[ "$LABELS" == *"status:waiting"* ]]; then
    echo "✅ Correct labels"
    PASS=$((PASS + 1))
else
    echo "⚠️  Labels: $LABELS"
    FAIL=$((FAIL + 1))
fi
echo ""

echo "=== 9. PYTHON DEPENDENCIES ==="
cd /mnt/d/Projects/AutomatedPastor
printf "%-40s" "Activating venv and checking deps..."
if source venv-wsl/bin/activate 2>/dev/null; then
    if python -c "import flask; import pytest; import bandit" 2>/dev/null; then
        echo "✅ flask, pytest, bandit available"
        PASS=$((PASS + 1))
    else
        echo "❌ Missing Python deps - run wsl-full-setup.sh"
        FAIL=$((FAIL + 1))
    fi
    deactivate 2>/dev/null || true
elif source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null; then
    if python -c "import flask; import pytest" 2>/dev/null; then
        echo "⚠️  Using Windows venv (may have issues)"
        PASS=$((PASS + 1))
    else
        echo "❌ Missing Python deps"
        FAIL=$((FAIL + 1))
    fi
    deactivate 2>/dev/null || true
else
    echo "❌ No venv found - run wsl-full-setup.sh"
    FAIL=$((FAIL + 1))
fi
echo ""

echo "=== 10. DOCKER ==="
printf "%-40s" "Checking docker..."
if command -v docker &> /dev/null; then
    echo "✅ $(docker --version | cut -d' ' -f3 | tr -d ',')"
    PASS=$((PASS + 1))
else
    echo "❌ Docker not installed"
    FAIL=$((FAIL + 1))
fi

printf "%-40s" "Checking docker-compose..."
if command -v docker-compose &> /dev/null; then
    echo "✅ $(docker-compose --version | cut -d' ' -f4 2>/dev/null || docker-compose --version)"
    PASS=$((PASS + 1))
else
    echo "⚠️  docker-compose not installed (needed for Phase 1)"
    FAIL=$((FAIL + 1))
fi

printf "%-40s" "Checking docker daemon..."
if docker ps &> /dev/null; then
    echo "✅ Docker daemon running"
    PASS=$((PASS + 1))
else
    echo "⚠️  Docker daemon not running (start Docker Desktop or: sudo service docker start)"
    FAIL=$((FAIL + 1))
fi
echo ""

echo "=== 11. WEASYPRINT DEPS (PDF Export) ==="
printf "%-40s" "Checking pango library..."
if ldconfig -p 2>/dev/null | grep -q pango || dpkg -l | grep -q libpango; then
    echo "✅ pango available"
    PASS=$((PASS + 1))
else
    echo "⚠️  pango may be missing (needed for PDF export)"
    FAIL=$((FAIL + 1))
fi
echo ""

echo "=== 12. RALPH-LOOP PLUGIN ==="
printf "%-40s" "Checking ralph-loop availability..."
# This is harder to test directly, but we can check if the hook file exists
if [[ -f ~/.claude/plugins/marketplaces/claude-plugins-official/plugins/ralph-loop/hooks/stop-hook.sh ]]; then
    echo "✅ Plugin files exist"
    PASS=$((PASS + 1))
else
    echo "⚠️  Plugin may not be installed - check with: claude then /ralph-loop help"
    FAIL=$((FAIL + 1))
fi
echo ""

echo "=============================================="
echo "  RESULTS: $PASS passed, $FAIL failed"
echo "=============================================="
echo ""

if [[ $FAIL -eq 0 ]]; then
    echo "🚀 All checks passed! Ready to launch."
    echo ""
    echo "Next steps:"
    echo "  1. Open 3 WSL terminals"
    echo "  2. In each, run: cd /mnt/d/Projects/[directory]"
    echo "  3. Launch claude in each terminal"
    echo "  4. Paste the /ralph-loop prompts from agents/*.md"
else
    echo "⚠️  Some checks failed. Fix issues before launching."
    echo ""
    echo "Common fixes:"
    echo "  - gh not authenticated: gh auth login"
    echo "  - claude not found: npm install -g @anthropic-ai/claude-code"
    echo "  - jq not found: sudo apt install jq"
fi
