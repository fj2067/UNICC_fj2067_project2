#!/bin/bash
set -e

# Install from the repo root, using full path to be safe
pip install -r "$(dirname "$0")/requirements.txt"

# Run tests
python -m pytest tests/
