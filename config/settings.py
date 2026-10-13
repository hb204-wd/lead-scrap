import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Exports (gratuits - aucune carte requise)
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

# Google Sheets (optionnel - nécessite GCP payant, désactivé par défaut)
GOOGLE_SHEETS_CREDENTIALS_PATH = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH", "config/google_credentials.json")
GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID")

# Scraping Settings
SCRAPE_DELAY_MIN = int(os.getenv("SCRAPE_DELAY_MIN", 2))
SCRAPE_DELAY_MAX = int(os.getenv("SCRAPE_DELAY_MAX", 5))
MAX_RESULTS = int(os.getenv("MAX_RESULTS", 50))

# User Agent Rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]
