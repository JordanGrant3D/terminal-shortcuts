#!/bin/bash
set -e

# Configuration
REPO_URL="https://github.com/JordanGrant3D/terminal-shortcuts.git"
PERMANENT_DIR="$HOME/.local/share/terminal-shortcuts"
LOCAL_BIN="$HOME/.local/bin"
TSHORT_LINK="$LOCAL_BIN/tshort"

echo "🚀 Installing terminal-shortcuts..."

# 1. Create a temporary directory and ensure it gets cleaned up on exit
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

echo "📥 Cloning repository into temporary directory..."
git clone "$REPO_URL" "$TEMP_DIR/terminal-shortcuts"

# 2. Set up the Python virtual environment inside /tmp
echo "🐍 Setting up Python virtual environment..."
cd "$TEMP_DIR/terminal-shortcuts"
python3 -m venv venv

# Upgrade pip and install dependencies if requirements.txt exists
./venv/bin/pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    ./venv/bin/pip install -r requirements.txt
fi

# 3. Move the project to its permanent directory
echo "📂 Moving project to $PERMANENT_DIR..."
mkdir -p "$(dirname "$PERMANENT_DIR")"
rm -rf "$PERMANENT_DIR"
mv "$TEMP_DIR/terminal-shortcuts" "$PERMANENT_DIR"

# 4. Create ~/.local/bin directory if needed
mkdir -p "$LOCAL_BIN"
if [ -L "$TSHORT_LINK" ] || [ -e "$TSHORT_LINK" ]; then
    rm "$TSHORT_LINK"
fi

# 5. Create the wrapper script pointing to main.py in the permanent folder
echo "🔗 Creating command shortcut 'tshort'..."
cat << EOF > "$TSHORT_LINK"
#!/bin/bash
exec "$PERMANENT_DIR/venv/bin/python" "$PERMANENT_DIR/main.py" "\$@"
EOF

# 6. Make the wrapper script executable
chmod +x "$TSHORT_LINK"

echo "✅ Success! 'tshort' has been installed to $TSHORT_LINK"
echo "Make sure $LOCAL_BIN is in your PATH to run it from anywhere."
