#!/bin/bash

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install packages from requirements.txt
pip install -r requirements.txt

echo "Virtual environment setup complete!"