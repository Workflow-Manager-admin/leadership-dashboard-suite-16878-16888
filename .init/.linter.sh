#!/bin/bash
cd /home/kavia/workspace/code-generation/leadership-dashboard-suite-16878-16888/dashboard_backend

# Create venv if it does not exist
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Upgrade pip and install requirements if needed
pip install --upgrade pip
pip install -r requirements.txt

flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

