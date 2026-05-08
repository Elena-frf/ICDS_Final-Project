#!/bin/bash

# Automatically start ollama and load phi3:mini model

echo "Checking if Ollama is installed..."
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed"
    echo "Please download and install from https://ollama.ai"
    exit 1
fi

echo "✓ Ollama is installed"

# Check if ollama service is already running
if pgrep -f "ollama serve" > /dev/null; then
    echo "✓ Ollama service is already running (PID: $(pgrep -f 'ollama serve'))"
else
    echo "Starting Ollama service..."
    ollama serve &
    sleep 3
    echo "✓ Ollama service started"
fi

# Check if phi3:mini model exists
echo "Checking phi3:mini model..."
if ollama list | grep -q "phi3:mini"; then
    echo "✓ phi3:mini model exists"
else
    echo "Downloading phi3:mini model (this may take a few minutes on first run)..."
    ollama pull phi3:mini
    echo "✓ phi3:mini model downloaded"
fi

echo ""
echo "====== Setup Complete ======"
echo "You can now start the chat server:"
echo "  cd gui"
echo "  python3 chat_server.py"
