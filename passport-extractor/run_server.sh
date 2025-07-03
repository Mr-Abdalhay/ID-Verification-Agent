#!/bin/bash

echo "===================================================="
echo "  Passport Data Extractor - Server"
echo "===================================================="
echo

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}ERROR: Virtual environment not found${NC}"
    echo "Please run ./install.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Failed to activate virtual environment${NC}"
    exit 1
fi

# Check if dependencies are installed
python -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Dependencies not installed${NC}"
    echo "Please run ./install.sh first"
    exit 1
fi

# Start the server
echo "Starting server..."
echo
echo -e "${GREEN}Server will be available at:${NC}"
echo "  http://localhost:5000"
echo
echo "Press Ctrl+C to stop the server"
echo

cd src
python app.py