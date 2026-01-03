#!/bin/bash
# Neural Mesh Pipeline Deployment Script
# This script sets up and deploys the neural mesh pipeline

set -e

echo "========================================="
echo "Neural Mesh Pipeline Deployment"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

print_status "Python 3 found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed. Please install pip3."
    exit 1
fi

print_status "pip3 found: $(pip3 --version)"

# Create directory structure
echo ""
echo "Creating directory structure..."
mkdir -p ~/neural-mesh/{src/tests,logs,storage}
print_status "Directories created"

# Copy files to deployment location
echo ""
echo "Copying files..."
cp pipeline_enhanced.py ~/neural-mesh/
cp requirements-termux.txt ~/neural-mesh/
cp README.md ~/neural-mesh/ 2>/dev/null || true
cp IMPLEMENTATION_GUIDE.md ~/neural-mesh/ 2>/dev/null || true
cp QUICK_REFERENCE.md ~/neural-mesh/ 2>/dev/null || true
cp TROUBLESHOOTING.md ~/neural-mesh/ 2>/dev/null || true

if [ -f ".env.example" ]; then
    if [ ! -f "~/neural-mesh/.env" ]; then
        cp .env.example ~/neural-mesh/.env
        print_warning ".env file created from template. Please edit ~/neural-mesh/.env with your API keys."
    fi
fi

print_status "Files copied to ~/neural-mesh/"

# Install dependencies
echo ""
echo "Installing Python dependencies..."
cd ~/neural-mesh
pip3 install -r requirements-termux.txt

print_status "Dependencies installed"

# Check for API key
echo ""
if [ -z "$OPENAI_API_KEY" ]; then
    print_warning "OPENAI_API_KEY environment variable not set."
    print_warning "Please set it by running: export OPENAI_API_KEY='your-key-here'"
    print_warning "Or add it to ~/neural-mesh/.env file"
else
    print_status "OPENAI_API_KEY is set"
fi

# Create systemd service (optional, for Linux)
if command -v systemctl &> /dev/null; then
    echo ""
    read -p "Would you like to create a systemd service for automatic startup? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cat > /tmp/neural-mesh-pipeline.service << EOF
[Unit]
Description=Neural Mesh Pipeline
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/neural-mesh
Environment="OPENAI_API_KEY=$OPENAI_API_KEY"
ExecStart=$(which python3) $HOME/neural-mesh/pipeline_enhanced.py --mode continuous
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        sudo mv /tmp/neural-mesh-pipeline.service /etc/systemd/system/
        sudo systemctl daemon-reload
        sudo systemctl enable neural-mesh-pipeline.service
        print_status "Systemd service created. Start it with: sudo systemctl start neural-mesh-pipeline"
    fi
fi

echo ""
echo "========================================="
print_status "Deployment complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Edit ~/neural-mesh/.env and add your OPENAI_API_KEY"
echo "  2. Run the pipeline:"
echo "     cd ~/neural-mesh"
echo "     python3 pipeline_enhanced.py"
echo ""
echo "For more information, see:"
echo "  - README.md for overview"
echo "  - QUICK_REFERENCE.md for commands"
echo "  - IMPLEMENTATION_GUIDE.md for details"
echo ""
