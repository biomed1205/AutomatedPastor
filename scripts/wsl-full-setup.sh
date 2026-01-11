#!/bin/bash
# =============================================================================
# AutomatedPastor - Complete WSL Environment Setup
# =============================================================================
# This script installs ALL dependencies needed for the entire project.
# Run this ONCE before launching the 3-agent system.
# =============================================================================

set -e

echo "=============================================="
echo "  AutomatedPastor - Full WSL Setup"
echo "=============================================="
echo ""
echo "This will install everything needed for all 10 phases."
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

# =============================================================================
# 1. SYSTEM PACKAGES
# =============================================================================
echo ""
echo "=== 1. SYSTEM PACKAGES ==="

sudo apt update
sudo apt install -y \
    git \
    curl \
    wget \
    jq \
    perl \
    build-essential \
    software-properties-common

echo "✅ Basic system packages installed"

# =============================================================================
# 2. PYTHON 3.11+
# =============================================================================
echo ""
echo "=== 2. PYTHON ==="

# Check if Python 3.11+ is available
PYTHON_VERSION=$(python3 --version 2>/dev/null | cut -d' ' -f2 | cut -d'.' -f1,2)
if [[ "$PYTHON_VERSION" < "3.11" ]]; then
    echo "Installing Python 3.11..."
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt update
    sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
else
    echo "✅ Python $PYTHON_VERSION already installed"
fi

# Ensure pip is available
sudo apt install -y python3-pip python3-venv

echo "✅ Python setup complete"

# =============================================================================
# 3. WEASYPRINT SYSTEM DEPENDENCIES (for PDF export)
# =============================================================================
echo ""
echo "=== 3. WEASYPRINT DEPENDENCIES (PDF Generation) ==="

sudo apt install -y \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    libcairo2 \
    libcairo2-dev \
    libgirepository1.0-dev \
    gir1.2-pango-1.0 \
    fonts-liberation

echo "✅ WeasyPrint dependencies installed"

# =============================================================================
# 4. NODE.JS AND NPM (for MCP servers)
# =============================================================================
echo ""
echo "=== 4. NODE.JS AND NPM ==="

if ! command -v node &> /dev/null; then
    echo "Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install -y nodejs
else
    echo "✅ Node.js $(node --version) already installed"
fi

echo "✅ Node.js setup complete"

# =============================================================================
# 5. DOCKER
# =============================================================================
echo ""
echo "=== 5. DOCKER ==="

if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    sudo apt install -y docker.io docker-compose
    sudo usermod -aG docker $USER
    echo "⚠️  Docker installed. You may need to log out and back in for group membership."
else
    echo "✅ Docker $(docker --version | cut -d' ' -f3 | tr -d ',') already installed"
fi

# Try to start docker service
sudo service docker start 2>/dev/null || echo "Note: Docker service may need Docker Desktop on Windows"

echo "✅ Docker setup complete"

# =============================================================================
# 6. GITHUB CLI
# =============================================================================
echo ""
echo "=== 6. GITHUB CLI ==="

if ! command -v gh &> /dev/null; then
    echo "Installing GitHub CLI..."
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
    sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
    sudo apt update
    sudo apt install -y gh
else
    echo "✅ GitHub CLI $(gh --version | head -1 | cut -d' ' -f3) already installed"
fi

# Check authentication
if ! gh auth status &> /dev/null; then
    echo ""
    echo "⚠️  GitHub CLI not authenticated. Run: gh auth login"
fi

echo "✅ GitHub CLI setup complete"

# =============================================================================
# 7. CLAUDE CODE CLI
# =============================================================================
echo ""
echo "=== 7. CLAUDE CODE CLI ==="

if ! command -v claude &> /dev/null; then
    echo "Installing Claude Code CLI..."
    npm install -g @anthropic-ai/claude-code
else
    echo "✅ Claude Code $(claude --version 2>/dev/null | head -1) already installed"
fi

echo "✅ Claude Code setup complete"

# =============================================================================
# 8. CREATE WSL-COMPATIBLE PYTHON VENV
# =============================================================================
echo ""
echo "=== 8. PYTHON VIRTUAL ENVIRONMENT ==="

cd /mnt/d/Projects/AutomatedPastor

if [[ ! -d "venv-wsl" ]]; then
    echo "Creating WSL-compatible venv..."
    python3 -m venv venv-wsl
fi

echo "Activating venv and installing dependencies..."
source venv-wsl/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

echo "✅ Python venv-wsl created and packages installed"

# =============================================================================
# 9. FIX GIT WORKTREES FOR WSL
# =============================================================================
echo ""
echo "=== 9. FIX GIT WORKTREES ==="

# Fix pastor-tests
if [[ -d "/mnt/d/Projects/pastor-tests" ]]; then
    echo "gitdir: /mnt/d/Projects/AutomatedPastor/.git/worktrees/pastor-tests" > /mnt/d/Projects/pastor-tests/.git
    # Fix the reverse reference
    if [[ -f "/mnt/d/Projects/AutomatedPastor/.git/worktrees/pastor-tests/gitdir" ]]; then
        echo "/mnt/d/Projects/pastor-tests/.git" > /mnt/d/Projects/AutomatedPastor/.git/worktrees/pastor-tests/gitdir
    fi
    echo "✅ pastor-tests worktree fixed"
fi

# Fix pastor-code
if [[ -d "/mnt/d/Projects/pastor-code" ]]; then
    echo "gitdir: /mnt/d/Projects/AutomatedPastor/.git/worktrees/pastor-code" > /mnt/d/Projects/pastor-code/.git
    # Fix the reverse reference
    if [[ -f "/mnt/d/Projects/AutomatedPastor/.git/worktrees/pastor-code/gitdir" ]]; then
        echo "/mnt/d/Projects/pastor-code/.git" > /mnt/d/Projects/AutomatedPastor/.git/worktrees/pastor-code/gitdir
    fi
    echo "✅ pastor-code worktree fixed"
fi

# =============================================================================
# 10. MCP SERVERS (Optional - installed globally)
# =============================================================================
echo ""
echo "=== 10. MCP SERVERS (Optional) ==="

echo "MCP servers can be installed if needed:"
echo "  npm install -g @anthropic-ai/mcp-server-filesystem"
echo "  npm install -g @anthropic-ai/mcp-server-git"
echo "  npm install -g @anthropic-ai/mcp-server-github"
echo "  npm install -g @anthropic-ai/mcp-server-sqlite"
echo "  npm install -g @anthropic-ai/mcp-server-fetch"
echo ""
echo "Skipping for now - Claude Code has built-in tools that may suffice."

# =============================================================================
# 11. VERIFY INSTALLATION
# =============================================================================
echo ""
echo "=== 11. VERIFICATION ==="

echo ""
echo "Checking installed versions:"
echo "  bash:          $(bash --version | head -1 | cut -d' ' -f4)"
echo "  git:           $(git --version | cut -d' ' -f3)"
echo "  python3:       $(python3 --version | cut -d' ' -f2)"
echo "  pip3:          $(pip3 --version | cut -d' ' -f2)"
echo "  node:          $(node --version 2>/dev/null || echo 'not found')"
echo "  npm:           $(npm --version 2>/dev/null || echo 'not found')"
echo "  docker:        $(docker --version 2>/dev/null | cut -d' ' -f3 | tr -d ',' || echo 'not found')"
echo "  docker-compose:$(docker-compose --version 2>/dev/null | cut -d' ' -f4 || echo 'not found')"
echo "  gh:            $(gh --version 2>/dev/null | head -1 | cut -d' ' -f3 || echo 'not found')"
echo "  claude:        $(claude --version 2>/dev/null | head -1 || echo 'not found')"
echo "  jq:            $(jq --version 2>/dev/null || echo 'not found')"

# =============================================================================
# FINAL SUMMARY
# =============================================================================
echo ""
echo "=============================================="
echo "  SETUP COMPLETE!"
echo "=============================================="
echo ""
echo "Next steps:"
echo ""
echo "1. If Docker was just installed, log out and back in:"
echo "   exit"
echo "   wsl"
echo ""
echo "2. If GitHub CLI needs auth:"
echo "   gh auth login"
echo ""
echo "3. Run the preflight check:"
echo "   cd /mnt/d/Projects/AutomatedPastor"
echo "   ./scripts/wsl-preflight-check.sh"
echo ""
echo "4. Start the agents (3 separate terminals):"
echo ""
echo "   Terminal 1 (PM):"
echo "   cd /mnt/d/Projects/AutomatedPastor"
echo "   source venv-wsl/bin/activate"
echo "   claude"
echo ""
echo "   Terminal 2 (Test Writer):"
echo "   cd /mnt/d/Projects/pastor-tests"
echo "   source ../AutomatedPastor/venv-wsl/bin/activate"
echo "   claude"
echo ""
echo "   Terminal 3 (Code Writer):"
echo "   cd /mnt/d/Projects/pastor-code"
echo "   source ../AutomatedPastor/venv-wsl/bin/activate"
echo "   claude"
echo ""
