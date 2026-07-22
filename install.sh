#!/bin/bash
echo "========================================"
echo "  MathModel Toolkit - One-Click Install"
echo "========================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python not found. Install Python 3.10+"
    exit 1
fi
echo "[OK] Python found"

# Install
echo "Installing dependencies..."
pip install -e . -q
pip install -e ".[pdf,optimization,timeseries]" -q

# Copy env
if [ ! -f .env ]; then
    cp api/.env.example .env
    echo "[INFO] Created .env — add your DeepSeek key (optional)"
else
    echo "[OK] .env exists"
fi

echo ""
echo "========================================"
echo "  Installation Complete!"
echo "========================================"
echo ""
echo "  1. Put problems in problems/ folder"
echo "  2. Run: python start.py"
echo ""
echo "  Optional: Edit .env for AI analysis"
echo "========================================"
