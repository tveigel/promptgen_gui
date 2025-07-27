#!/bin/bash
# This script sets up a virtual environment and runs the PromptGen GUI.

# Ensure the script is run from its own directory
cd "$(dirname "$0")"

# Check for Python 3
if ! command -v python3 &> /dev/null
then
    echo "Python 3 could not be found. Please install it to continue."
    exit
fi

VENV_DIR="venv"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv $VENV_DIR
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment."
        exit 1
    fi
fi

# Activate virtual environment and install dependencies
echo "Activating virtual environment and installing dependencies..."
source "$VENV_DIR/bin/activate"
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Failed to install requirements. Please check requirements.txt and your internet connection."
    exit 1
fi

# Launch the application
echo "Launching PromptGen GUI..."
python3 run.py

echo "Application closed."