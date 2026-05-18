import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / '.env.local'
load_dotenv(dotenv_path=env_path)

GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')
DUFFEL_ACCESS_TOKEN = os.getenv("DUFFEL_ACCESS_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
