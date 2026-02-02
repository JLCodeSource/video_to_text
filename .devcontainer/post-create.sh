#!/usr/bin/env bash
set -euo pipefail

# Use the project’s make target to install uv, create venv, and sync deps
make install

# Quick sanity output
uv run python -V
# Install beads CLI for issue tracking
echo "Installing beads (bd)..."
if ! command -v bd &> /dev/null; then
    curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash
    
    # Add Go bin to PATH if needed
    if [[ ":$PATH:" != *":$HOME/go/bin:"* ]]; then
        export PATH="$PATH:$HOME/go/bin"
        echo 'export PATH="$PATH:$HOME/go/bin"' >> ~/.bashrc
    fi
    
    # Verify installation
    if command -v bd &> /dev/null; then
        echo "✓ beads installed: $(bd version)"
    else
        echo "⚠ beads installation completed but 'bd' not in PATH. Add \$HOME/go/bin to PATH."
    fi
else
    echo "✓ beads already installed: $(bd version)"
fi
