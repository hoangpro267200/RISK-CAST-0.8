#!/bin/bash
# RISKCAST Development Server Script (Unix/Linux/Mac)
# Starts both backend and frontend dev servers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting RISKCAST Development Environment${NC}"
echo "=========================================="

# Check if virtual environment exists
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}Virtual environment created${NC}"
fi

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Install Python dependencies if needed
if [ ! -f "venv/.installed" ] && [ ! -f ".venv/.installed" ]; then
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    pip install -r requirements.txt
    if [ -f "requirements-dev.txt" ]; then
        pip install -r requirements-dev.txt
    fi
    touch venv/.installed 2>/dev/null || touch .venv/.installed 2>/dev/null || true
    echo -e "${GREEN}Python dependencies installed${NC}"
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}Node.js not found. Frontend dev server will not start.${NC}"
    echo "Install Node.js from: https://nodejs.org/"
    NODE_AVAILABLE=false
else
    NODE_AVAILABLE=true
fi

# Install npm dependencies if needed
if [ "$NODE_AVAILABLE" = true ] && [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing npm dependencies...${NC}"
    npm install
    echo -e "${GREEN}npm dependencies installed${NC}"
fi

echo ""
echo -e "${BLUE}Starting servers...${NC}"
echo ""

# Start backend server in background
echo -e "${GREEN}Backend:${NC} http://127.0.0.1:8000"
echo -e "${GREEN}API Docs:${NC} http://127.0.0.1:8000/docs"
python dev_run.py &
BACKEND_PID=$!

# Start frontend dev server if Node.js available
if [ "$NODE_AVAILABLE" = true ]; then
    echo -e "${GREEN}Frontend:${NC} http://localhost:3000"
    npm run dev &
    FRONTEND_PID=$!
fi

echo ""
echo -e "${GREEN}Development servers started!${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop all servers${NC}"
echo ""

# Wait for interrupt
trap "echo ''; echo -e '${YELLOW}Stopping servers...${NC}'; kill $BACKEND_PID 2>/dev/null; [ \"$NODE_AVAILABLE\" = true ] && kill $FRONTEND_PID 2>/dev/null; exit" INT TERM

wait

