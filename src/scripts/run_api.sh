#!/bin/bash
# Load environment variables from .env
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
