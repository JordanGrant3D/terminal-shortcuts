#!/bin/bash
set -e

# Configuration
LOCAL_BIN="$HOME/.local/bin"
TSHORT_LINK="$LOCAL_BIN/tshort"

echo "🗑️ Uninstalling terminal-shortcuts..."

# Remove only the shortcut wrapper from ~/.local/bin
if [ -L "$TSHORT_LINK" ] || [ -e "$TSHORT_LINK" ]; then
    rm "$TSHORT_LINK"
    echo "Removed shortcut: $TSHORT_LINK"
else
    echo "Shortcut not found at $TSHORT_LINK, skipping."
fi

echo "✅ Uninstallation complete! :("
