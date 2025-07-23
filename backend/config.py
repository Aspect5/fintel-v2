# backend/config.py

import os
from pathlib import Path
from dotenv import load_dotenv

# --- Centralized Configuration Loading ---
# This file is the single source of truth for all backend configuration.
# It ensures that environment variables are loaded exactly once, at the very beginning.

# Load the .env file from the directory where this script resides.
dotenv_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=dotenv_path)

# --- API Keys & Settings ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
FRED_API_KEY = os.getenv("FRED_API_KEY")
BASE_URL = os.getenv("BASE_URL")
