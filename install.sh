#!/usr/bin/env bash
# Install script for Hermes Shared Memory Skill (Linux / WSL)
set -euo pipefail

SKILL_DIR="$HOME/.hermes/skills/shared-memory"
SCRIPT_DIR="$SKILL_DIR/scripts"
DB_DIR="$HOME/.hermes/shared-memory"

echo "=== Hermes Shared Memory Skill - Install (Linux/WSL) ==="
echo

# Check for python3
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 is required but not found."
    exit 1
fi

echo "[1/4] Python 3 found: $(python3 --version)"

# Create directories
mkdir -p "$SCRIPT_DIR"
mkdir -p "$DB_DIR"
echo "[2/4] Directories created"

# Copy files (assuming we're running from the repo root)
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cp "$REPO_DIR/scripts/shared_memory.py" "$SCRIPT_DIR/"
chmod +x "$SCRIPT_DIR/shared_memory.py"

if [ -f "$REPO_DIR/SKILL.md" ]; then
    cp "$REPO_DIR/SKILL.md" "$SKILL_DIR/"
fi

echo "[3/4] Files copied to $SKILL_DIR"

# Initialize database
python3 "$SCRIPT_DIR/shared_memory.py" stats >/dev/null 2>&1
echo "[4/4] Database initialized at $DB_DIR/memory.db"

echo
echo "=== Installation complete ==="
echo
echo "Verify with:"
echo "  python3 $SCRIPT_DIR/shared_memory.py stats"
echo
echo "--- Multi-agent setup (Windows + WSL) ---"
echo "To share memory between Windows and WSL, set SHARED_MEMORY_DB"
echo "to a path accessible from both systems, e.g.:"
echo "  export SHARED_MEMORY_DB=/mnt/c/Users/YOUR_USER/hermes-shared-memory/memory.db"
echo
echo "Add this to your ~/.bashrc or ~/.zshrc to make it permanent."
