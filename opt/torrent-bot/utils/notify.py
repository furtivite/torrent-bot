import logging
import time

import requests

from config import BOT_TOKEN, CHAT_ID

log = logging.getLogger("torrent-bot")

# ключ ошибки -> timestamp последней отправки
_error_last_sent = {}

# не чаще раза в час
ERROR_THROTTLE_SECONDS = 3600


def tg_send(text: str) -> None:
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": text},
            timeout=15,
        )
    except Exception as e:
        log.exception("Telegram send failed: %s", e)


def tg_send_error(error_key: str, text: str) -> None:
    now = time.time()
    last_sent = _error_last_sent.get(error_key, 0)

    if now - last_sent < ERROR_THROTTLE_SECONDS:
        log.warning("Suppressed repeated error notification: %s", error_key)
        return

    _error_last_sent[error_key] = now
    tg_send(text)
