#!/bin/bash

# Detect the operating system
OS=$(uname -s 2>/dev/null || ver)

echo "Setting up virtual environment..."

# Create and activate the virtual environment
if [[ "$OS" == "Darwin" || "$OS" == "Linux" || "$OS" == "MINGW"* ]]; then
  # Unix-like systems
  python3 -m venv .venv
  source .venv/bin/activate
elif [[ "$OS" == "Windows_NT" ]]; then
  # Windows
  python -m venv .venv
  .venv\Scripts\activate
else
  echo "Unsupported operating system: $OS"
  exit 1
fi

# Install dependencies
pip install pytest-playwright

echo "Setup complete. Virtual environment is ready."