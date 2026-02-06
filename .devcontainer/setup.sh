#!/bin/bash
set -e

echo "🚀 Setting up development environment..."

# Install Node dependencies
echo "📦 Installing Node.js dependencies..."
npm ci

# Create Python virtual environment
echo "🐍 Setting up Python virtual environment..."
if [ -d ".dev.venv" ]; then
    echo "⚠️  Python virtual environment already exists. Skipping creation."
else
    python3 -m venv .dev.venv
fi

# Activate Python virtual environment
source .dev.venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r .devcontainer/requirements.txt
pip install pre-commit

# Install Ruby gems (for bash coverage reporting)
echo "💎 Installing Ruby gems..."
gem install --user-install bashcov simplecov-cobertura

# Add gem bin directory to PATH in shell rc files
GEM_BIN_PATH="$HOME/.local/share/gem/ruby/3.2.0/bin"
for rc_file in "$HOME/.bashrc" "$HOME/.zshrc"; do
    if [ -f "$rc_file" ]; then
        if ! grep -q "$GEM_BIN_PATH" "$rc_file"; then
            echo "export PATH=\"$GEM_BIN_PATH:\$PATH\"" >> "$rc_file"
            echo "  Added gem bin to PATH in $(basename $rc_file)"
        fi
    fi
done

# Also export for current session
export PATH="$GEM_BIN_PATH:$PATH"

# Setup pre-commit hooks (using absolute path)
echo "🪝 Installing pre-commit hooks..."
git config --unset-all core.hooksPath || true
pre-commit install --install-hooks
pre-commit install --hook-type pre-push

# Make scripts executable
echo "🔧 Making scripts executable..."
find .github/actions -path '*/tests/*.sh' -type f -exec chmod +x {} \; 2>/dev/null || true
find .github/actions -path '*/scripts/*.sh' -type f -exec chmod +x {} \; 2>/dev/null || true
chmod +x scripts/*.sh 2>/dev/null || true

echo "✅ Development environment ready!"
echo ""
echo "Quick start:"
echo "  npm test                  # Run all tests"
echo "  npm run test:coverage     # Run tests with coverage"
echo "  .dev.venv/bin/pre-commit run --all-files # Run all hooks"
echo ""
echo "Note: Python venv (.dev.venv) is auto-activated in new terminals"
