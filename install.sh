#!/bin/bash
set -e

# Configuration
REPO_URL="https://github.com/JordanGrant3D/terminal-shortcuts.git"
PROJECT_DIR="$HOME/Documents/terminal-shortcuts"
LOCAL_BIN="$HOME/.local/bin"
TSHORT_LINK="$LOCAL_BIN/tshort"

echo "🚀 Installing terminal-shortcuts..."

# 1. Clone or update the repository
if [ -d "$PROJECT_DIR" ]; then
    echo "📁 Project directory already exists. Pulling latest changes..."
    git -C "$PROJECT_DIR" pull
else
    echo "📥 Cloning repository into $PROJECT_DIR..."
    git clone "$REPO_URL" "$PROJECT_DIR"
fi

# 2. Set up the Python virtual environment
echo "🐍 Setting up Python virtual environment..."
cd "$PROJECT_DIR"
python3 -m venv venv

# Upgrade pip and install dependencies if you have a requirements.txt
./venv/bin/pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    ./venv/bin/pip install -r requirements.txt
fi

# 3. Create ~/.local/bin directory if needed
mkdir -p "$LOCAL_BIN"
if [ -L "$TSHORT_LINK" ] || [ -e "$TSHORT_LINK" ]; then
    rm "$TSHORT_LINK"
fi

# 4. Create the wrapper script pointing to main.py
echo "🔗 Creating command shortcut 'tshort'..."
cat << EOF > "$TSHORT_LINK"
#!/bin/bash
exec "$PROJECT_DIR/venv/bin/python" "$PROJECT_DIR/main.py" "\$@"
EOF

# 5. Make the wrapper script executable
chmod +x "$TSHORT_LINK"

echo "✅ Success! 'tshort' has been installed to $TSHORT_LINK"
echo "Make sure $LOCAL_BIN is in your PATH to run it from anywhere."
