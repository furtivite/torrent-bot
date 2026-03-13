import os
from pathlib import Path


BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = int(os.environ["CHAT_ID"])

ALLOWED_USERNAMES = set(
    u.strip().lstrip("@")
    for u in os.environ["ALLOWED_USERNAMES"].split(",")
    if u.strip()
)

# Базовый каталог данных, по умолчанию /mnt/data
DATA_ROOT = Path(os.environ.get("DATA_ROOT", "/mnt/data"))

TRACKERS_DIR = Path(os.environ["TRACKERS_DIR"])
DOWNLOADED_DIR = Path(os.environ.get("DOWNLOADED_DIR", str(DATA_ROOT / "downloaded")))

TRANSMISSION_HOST = os.environ["TRANSMISSION_HOST"]
TRANSMISSION_PORT = int(os.environ["TRANSMISSION_PORT"])
TRANSMISSION_USERNAME = os.environ["TRANSMISSION_USERNAME"]
TRANSMISSION_PASSWORD = os.environ["TRANSMISSION_PASSWORD"]

WEB_UI_URL = os.environ["WEB_UI_URL"]
# Путь к корневому сертификату опционален; по умолчанию используем типовой каталог.
CERT_FILE_PATH = Path(os.environ.get("CERT_FILE_PATH", "/mnt/data/certs/caddy-local-root.crt"))

CHECK_INTERVAL_SECONDS = 60
STALL_MINUTES = 30
