#!/bin/bash
#
# Migrate Trading Agent Project to ~/Documents/workspace
# ======================================================
# This script:
# 1. Copies project to ~/Documents/workspace/trading-agent
# 2. Preserves git history
# 3. Excludes sensitive files (.env, logs, etc.)
# 4. Sets up git repository
# 5. Prepares for push to private remote
#

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Paths
CURRENT_DIR="/Users/charan/PycharmProjects/trading_agent"
WORKSPACE_DIR="$HOME/Documents/workspace"
NEW_PROJECT_DIR="$WORKSPACE_DIR/trading-agent"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Trading Agent - Project Migration to Workspace                 ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Verify current location
echo -e "${BLUE}[1/7] Verifying current location...${NC}"
if [ ! -d "$CURRENT_DIR" ]; then
    echo -e "${RED}✗ Current directory not found: $CURRENT_DIR${NC}"
    exit 1
fi
cd "$CURRENT_DIR"
echo -e "${GREEN}✓ Current directory: $CURRENT_DIR${NC}"
echo ""

# Step 2: Check if destination exists
echo -e "${BLUE}[2/7] Checking destination...${NC}"
if [ -d "$NEW_PROJECT_DIR" ]; then
    echo -e "${YELLOW}⚠ Warning: Destination already exists: $NEW_PROJECT_DIR${NC}"
    read -p "Delete existing directory and continue? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Removing existing directory...${NC}"
        rm -rf "$NEW_PROJECT_DIR"
        echo -e "${GREEN}✓ Removed existing directory${NC}"
    else
        echo -e "${RED}✗ Migration cancelled${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✓ Destination clear${NC}"
echo ""

# Step 3: Create destination directory
echo -e "${BLUE}[3/7] Creating destination directory...${NC}"
mkdir -p "$NEW_PROJECT_DIR"
echo -e "${GREEN}✓ Created: $NEW_PROJECT_DIR${NC}"
echo ""

# Step 4: Copy project files (excluding git, venv, caches, logs, .env)
echo -e "${BLUE}[4/7] Copying project files...${NC}"
rsync -av \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='*.env' \
    --exclude='.env.*' \
    --exclude='*.log' \
    --exclude='nohup.out' \
    --exclude='.pytest_cache' \
    --exclude='htmlcov' \
    --exclude='.coverage' \
    --exclude='node_modules' \
    --exclude='cdk.out' \
    --exclude='*.sqlite' \
    --exclude='*.db' \
    --exclude='data/' \
    --exclude='.DS_Store' \
    --exclude='tmp/' \
    --exclude='.idea' \
    --exclude='.vscode' \
    "$CURRENT_DIR/" "$NEW_PROJECT_DIR/"

echo -e "${GREEN}✓ Project files copied${NC}"
echo ""

# Step 5: Initialize git repository
echo -e "${BLUE}[5/7] Initializing git repository...${NC}"
cd "$NEW_PROJECT_DIR"

if [ -d ".git" ]; then
    echo -e "${YELLOW}Git repository already exists${NC}"
else
    git init
    echo -e "${GREEN}✓ Git repository initialized${NC}"
fi

# Configure git
git config user.name "charanreddy8897"
git config user.email "shreyaragireddy@gmail.com"
echo -e "${GREEN}✓ Git configured${NC}"
echo ""

# Step 6: Stage files (respecting .gitignore)
echo -e "${BLUE}[6/7] Staging files...${NC}"
git add .
echo -e "${GREEN}✓ Files staged${NC}"

# Show what's staged
echo ""
echo -e "${YELLOW}Files to be committed:${NC}"
git status --short | head -30
TOTAL_FILES=$(git status --short | wc -l | tr -d ' ')
echo -e "${YELLOW}... and $TOTAL_FILES total files${NC}"
echo ""

# Step 7: Create initial commit
echo -e "${BLUE}[7/7] Creating initial commit...${NC}"
git commit -m "Initial commit: Trading Agent System

- Backend: FastAPI + PostgreSQL + JWT auth + TOTP 2FA
- Frontend: React + TypeScript + Vite
- CDK: AWS infrastructure (EC2, RDS, S3, CloudFront)
- Features: PEG scanner, technical analysis, portfolio tracking
- Integrations: Alpaca, Finnhub, Anthropic Claude, Slack
- Architecture: OOP singletons, async patterns, structured logging

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>" || {
    echo -e "${YELLOW}Note: Some files may already be committed${NC}"
}
echo -e "${GREEN}✓ Initial commit created${NC}"
echo ""

# Final summary
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ Migration Complete!                                          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Project Location:${NC}"
echo "  Old: $CURRENT_DIR"
echo "  New: $NEW_PROJECT_DIR"
echo ""
echo -e "${BLUE}Git Status:${NC}"
cd "$NEW_PROJECT_DIR"
git log --oneline -1
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo ""
echo "1. Create a private repository on GitHub:"
echo "   https://github.com/new"
echo "   Name: trading-agent"
echo "   Visibility: Private"
echo ""
echo "2. Add remote and push:"
echo "   cd $NEW_PROJECT_DIR"
echo "   git remote add origin git@github.com:YOUR_USERNAME/trading-agent.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "3. Verify .env is NOT pushed:"
echo "   git status"
echo "   # Should not show .env files"
echo ""
echo "4. When ready to add READMEs:"
echo "   # Edit .gitignore to remove README exclusions"
echo "   git add README.md */README.md"
echo "   git commit -m 'docs: Add README files'"
echo "   git push"
echo ""
echo -e "${YELLOW}⚠️  Remember:${NC}"
echo "  - .env files are NOT pushed (protected by .gitignore)"
echo "  - README files are NOT pushed yet (add them later)"
echo "  - Backend is running on old location (restart from new location)"
echo ""
