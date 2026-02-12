import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
ROBOTEVENTS_TOKEN = os.getenv("ROBOTEVENTS_TOKEN")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

if not ROBOTEVENTS_TOKEN:
    raise RuntimeError("ROBOTEVENTS_TOKEN is not set")