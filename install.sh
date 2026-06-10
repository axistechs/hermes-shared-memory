#!/usr/bin/env bash
# Install script for Hermes Shared Memory Skill
set -euo pipefail

SKILL_DIR="$HOME/.hermes/skills/shared-memory"
SCRIPT_DIR="$SKILL_DIR/scripts"
DB_DIR="$HOME/.hermes/shared-memory"

echo "=== Hermes Shared Memory Skill - Install ==="
echo

# Check for python3
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 is required but not found."
    echo "Install Python 3 and try again."
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
echo "Add SHARED_MEMORY_DB env var to customize DB location:"
echo "  export SHARED_MEMORY_DB=/path/to/custom/memory.db"
