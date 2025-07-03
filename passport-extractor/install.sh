#!/bin/bash

echo "===================================================="
echo "  Passport Data Extractor - Installation (Linux/Mac)"
echo "===================================================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python installation
echo "[1/5] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3 is not installed${NC}"
    echo
    echo "Please install Python 3.8+ using:"
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "  sudo apt-get update && sudo apt-get install python3 python3-pip python3-venv"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  brew install python3"
    fi
    exit 1
fi
python3 --version
echo -e "${GREEN}OK - Python is installed${NC}"

# Check Python version
echo
echo "[2/5] Checking Python version..."
python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"
if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Python 3.8+ is required${NC}"
    echo "Please upgrade your Python installation"
    exit 1
fi
echo -e "${GREEN}OK - Python version is compatible${NC}"

# Check Tesseract installation
echo
echo "[3/5] Checking Tesseract OCR..."
if ! command -v tesseract &> /dev/null; then
    echo -e "${YELLOW}WARNING: Tesseract OCR is not installed${NC}"
    echo
    echo "Please install Tesseract OCR:"
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "  sudo apt-get update"
        echo "  sudo apt-get install tesseract-ocr tesseract-ocr-ara"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  brew install tesseract"
        echo "  brew install tesseract-lang"
    fi
    echo
    read -p "Do you want to install Tesseract now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            sudo apt-get update
            sudo apt-get install -y tesseract-ocr tesseract-ocr-ara
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            if ! command -v brew &> /dev/null; then
                echo -e "${RED}Homebrew is not installed. Please install it first:${NC}"
                echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
                exit 1
            fi
            brew install tesseract
            brew install tesseract-lang
        fi
    else
        read -p "Continue installation anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    tesseract --version | head -n 1
    echo -e "${GREEN}OK - Tesseract is installed${NC}"
fi

# Create virtual environment
echo
echo "[4/5] Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists"
else
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}ERROR: Failed to create virtual environment${NC}"
        echo "Try: sudo apt-get install python3-venv"
        exit 1
    fi
    echo -e "${GREEN}OK - Virtual environment created${NC}"
fi

# Activate virtual environment and install dependencies
echo
echo "[5/5] Installing dependencies..."
echo "This may take a few minutes..."

source venv/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Failed to activate virtual environment${NC}"
    exit 1
fi

# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Failed to install dependencies${NC}"
    echo
    echo "Common issues:"
    echo "- No internet connection"
    echo "- Missing system libraries"
    echo "- Insufficient permissions"
    exit 1
fi

# Create output directories
echo
echo "Creating output directories..."
mkdir -p output/enhanced output/diagnostics output/results
echo -e "${GREEN}OK - Directories created${NC}"

# Make scripts executable
chmod +x run_server.sh
chmod +x tools/*.py
chmod +x tests/*.py

# Create desktop entry for Linux
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo
    read -p "Create desktop shortcut? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cat > ~/Desktop/passport-extractor.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Passport Extractor
Comment=Extract data from passport images
Exec=$PWD/run_server.sh
Icon=scanner
Terminal=true
Categories=Utility;
EOF
        chmod +x ~/Desktop/passport-extractor.desktop
        echo "Desktop shortcut created"
    fi
fi

# Installation complete
echo
echo "===================================================="
echo -e "  ${GREEN}Installation Complete!${NC}"
echo "===================================================="
echo
echo "To start the server:"
echo "  1. Run: ./run_server.sh"
echo "  2. Open browser: http://localhost:5000"
echo
echo "To test extraction:"
echo "  python tests/test_extraction.py"
echo
echo "For help:"
echo "  See docs/USER_GUIDE.md"
echo