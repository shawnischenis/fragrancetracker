#!/bin/bash
export MONGO_URL="mongodb+srv://shawnchen456_db_user:Fwu7qm1jlkw2AN1R@cluster0.grvnfcf.mongodb.net/?appName=Cluster0"
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
