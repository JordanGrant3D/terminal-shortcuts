#!/bin/bash
set -e

# Configuration (must match your install paths)
PROJECT_DIR="$HOME/Documents/terminal-shortcuts"
LOCAL_BIN="$HOME/.local/bin"
TSHORT_LINK="$LOCAL_BIN/tshort"

echo "🗑️ Uninstalling terminal-shortcuts..."

# 1. Remove the shortcut wrapper from ~/.local/bin
if [ -L "$TSHORT_LINK" ] || [ -e "$TSHORT_LINK" ]; then
    rm "$TSHORT_LINK"
    echo "Removed shortcut: $TSHORT_LINK"
else
    echo "Shortcut not found at $TSHORT_LINK, skipping."
fi

# 2. Remove the project directory and virtual environment
if [ -d "$PROJECT_DIR" ]; then
    rm -rf "$PROJECT_DIR"
    echo "Removed project directory: $PROJECT_DIR"
else
    echo "Project directory not found at $PROJECT_DIR, skipping."
fi

echo "✅ Uninstallation complete!"
