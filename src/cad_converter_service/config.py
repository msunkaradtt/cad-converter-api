# src/cad_converter_service/config.py
import os
from pathlib import Path

# Get Redis URL from environment variable set in docker-compose
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Base directory for storing uploaded and converted files
# The /app/data path corresponds to the volume mount in docker-compose.yml
DATA_DIR = Path("/app/data")
UPLOAD_DIR = DATA_DIR / "uploads"
CONVERTED_DIR = DATA_DIR / "converted"
TEMP_DIR = DATA_DIR / "temp"

# Create directories if they don't exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CONVERTED_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)