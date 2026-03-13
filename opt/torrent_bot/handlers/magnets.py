from telegram import Update
from telegram.ext import ContextTypes

from ..transmission_client import get_client
from ..utils.auth import deny_access, get_username, is_authorized
from ..utils.notify import tg_send


def looks_like_magnet(text: str) -> bool:
    return text.strip().startswith("magnet:?")


async def handle_magnet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if message is None or message.from_user is None or message.text is None:
        return

    if not is_authorized(update):
        await deny_access(update)
        return

    magnet = message.text.strip()
    if not looks_like_magnet(magnet):
        return

    username = get_username(update)

    try:
        client = get_client()
        client.add_torrent(magnet)
        await message.reply_text("Magnet добавлен.")
        tg_send(f"🧲 Magnet получен от @{username}")
    except Exception as e:
        await message.reply_text(f"Ошибка добавления magnet: {e}")
