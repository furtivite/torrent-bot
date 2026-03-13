from telegram import Update
from telegram.ext import ContextTypes

from handlers.commands import space_cmd, torrents_cmd
from telegram_ui import (
    HELP_BUTTON,
    MAGNET_BUTTON,
    RESTART_TRANSMISSION_BUTTON,
    SPACE_BUTTON,
    START_BUTTON,
    TORRENTS_BUTTON,
    help_menu_keyboard,
    main_menu_keyboard,
    start_inline_keyboard,
)
from transmission_client import get_client
from utils.auth import deny_access, is_authorized


async def help_cmd(update, context):
    if update.message:
        await update.message.reply_text(
            "Помощь:",
            reply_markup=help_menu_keyboard(),
        )

async def handle_menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.message.text is None:
        return

    if not is_authorized(update):
        await deny_access(update)
        return

    text = update.message.text.strip()

    if text == START_BUTTON:
        await update.message.reply_text(
            "Главное меню:",
            reply_markup=start_inline_keyboard(),
        )
        return

    if text == SPACE_BUTTON:
        await space_cmd(update, context)
        return

    if text == TORRENTS_BUTTON:
        await torrents_cmd(update, context)
        return

    if text == MAGNET_BUTTON:
        await update.message.reply_text("Пришли magnet-ссылку одним сообщением.")
        return

    if text == RESTART_TRANSMISSION_BUTTON:
        try:
            client = get_client()
            client.session_stats()
            await update.message.reply_text("Transmission доступен. Кнопку перезапуска подключим следующим шагом.")
        except Exception as e:
            await update.message.reply_text(f"Ошибка доступа к Transmission: {e}")
        return

    if text == HELP_BUTTON:
        await help_cmd(update, context)
