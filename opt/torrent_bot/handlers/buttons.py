from telegram import Update
from telegram.ext import ContextTypes

from .commands import (
    build_torrents_page_keyboard,
    build_torrents_page_text,
    fetch_torrents,
    space_cmd,
    torrents_cmd,
)
from ..telegram_ui import (
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
from ..transmission_client import get_client
from ..utils.auth import deny_access, is_authorized
from ..utils.disk import disk_report


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


async def handle_start_inline_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return

    if not is_authorized(update):
        await query.answer()
        await deny_access(update)
        return

    data = (query.data or "").strip()
    await query.answer()

    if data == "space":
        await query.message.reply_text(disk_report())
        return

    if data == "torrents":
        torrents = fetch_torrents()
        if not torrents:
            await query.message.reply_text("Торрентов нет.")
            return

        text = build_torrents_page_text(torrents, 0)
        keyboard = build_torrents_page_keyboard(len(torrents), 0)
        await query.message.reply_text(text, reply_markup=keyboard)
        return

    if data == "add_magnet":
        await query.message.reply_text("Пришли magnet-ссылку одним сообщением.")
        return

    if data == "help_menu":
        await query.message.reply_text(
            "Помощь:",
            reply_markup=help_menu_keyboard(),
        )
        return
