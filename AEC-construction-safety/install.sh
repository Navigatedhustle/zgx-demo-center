#!/bin/bash

echo "=================================="
echo "Construction Safety Demo Installer"
echo "=================================="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed."
    echo "Please install with: sudo apt-get install python3 python3-pip python3-venv"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install PyTorch with CUDA support
echo ""
echo "Installing PyTorch with CUDA support..."
# --timeout 60 --retries 10: the cu130 nightly wheels are multi-GB and the CDN
# can leave a socket half-open mid-download. Without a timeout pip blocks forever
# (0% CPU, no progress, no error). A hard timeout trips a retry instead of hanging.
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu130 --timeout 60 --retries 10

# Install backend dependencies
echo ""
echo "Installing dependencies..."
cd backend
pip install -r requirements.txt --timeout 60 --retries 10
cd ..

# Download model for offline use via the public HuggingFace repo.
# download_models.sh is the single source of truth for the model fetch
# (yasserrmd/ConstructionSafetyQA-1.2B-V1, public + ungated — no creds needed).
echo ""
echo "Attempting to download model for offline use..."
echo "This will take a few minutes and requires internet (one-time only)..."

bash ./download_models.sh || echo "⚠️  Model download skipped. Demo will use offline responses."

echo ""
echo "=================================="
echo "✅ Installation Complete!"
echo "=================================="
echo ""
echo "To start the demo: ./start_demo.sh"
echo ""
