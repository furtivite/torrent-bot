import os
from pathlib import Path


def _is_testing() -> bool:
    """
    Определяет, запущен ли код под pytest.

    В тестах мы не хотим падать при отсутствии боевых переменных окружения,
    поэтому подставляем безопасные значения по умолчанию.
    """

    return "PYTEST_CURRENT_TEST" in os.environ


def _get_required_env(name: str, test_default: str) -> str:
    """
    Получить обязательную переменную окружения.

    - В обычном режиме (прод) выбрасывает RuntimeError, если переменная не задана.
    - В тестах (pytest) возвращает test_default, если переменная не задана.
    """

    value = os.environ.get(name)
    if value is not None:
        return value

    if _is_testing():
        return test_default

    raise RuntimeError(f"Required environment variable {name} is not set")


BOT_TOKEN = _get_required_env("BOT_TOKEN", "TEST_BOT_TOKEN")
CHAT_ID = int(_get_required_env("CHAT_ID", "0"))

ALLOWED_USERNAMES = set(
    u.strip().lstrip("@")
    for u in _get_required_env("ALLOWED_USERNAMES", "").split(",")
    if u.strip()
)

# Базовый каталог данных, по умолчанию /mnt/data
DATA_ROOT = Path(os.environ.get("DATA_ROOT", "/mnt/data"))

TRACKERS_DIR = Path(
    os.environ.get("TRACKERS_DIR")
    or (DATA_ROOT / "trackers")
    if _is_testing()
    else _get_required_env("TRACKERS_DIR", str(DATA_ROOT / "trackers"))
)
DOWNLOADED_DIR = Path(
    os.environ.get("DOWNLOADED_DIR", str(DATA_ROOT / "downloaded"))
)

TRANSMISSION_HOST = _get_required_env("TRANSMISSION_HOST", "localhost")
TRANSMISSION_PORT = int(_get_required_env("TRANSMISSION_PORT", "9091"))
TRANSMISSION_USERNAME = _get_required_env("TRANSMISSION_USERNAME", "user")
TRANSMISSION_PASSWORD = _get_required_env("TRANSMISSION_PASSWORD", "pass")

WEB_UI_URL = _get_required_env("WEB_UI_URL", "http://localhost:9091")
# Путь к корневому сертификату опционален; по умолчанию используем типовой каталог.
CERT_FILE_PATH = Path(
    os.environ.get("CERT_FILE_PATH", "/mnt/data/certs/caddy-local-root.crt")
)

CHECK_INTERVAL_SECONDS = 60
STALL_MINUTES = 30
