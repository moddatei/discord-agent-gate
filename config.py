import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "").strip()
CHANNEL_ID_STR = os.getenv("DISCORD_CHANNEL_ID", "0").strip()
try:
    CHANNEL_ID = int(CHANNEL_ID_STR)
except ValueError:
    CHANNEL_ID = 0

LOCAL_PORT = int(os.getenv("LOCAL_PORT", "9876"))
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "300"))
MENTION = os.getenv("DISCORD_MENTION_ROLE_OR_USER", "").strip()
