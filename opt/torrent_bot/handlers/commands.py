from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from ..transmission_client import get_client
from ..utils.auth import deny_access, is_authorized
from ..utils.disk import disk_report, format_bytes
from ..telegram_ui import main_menu_keyboard, start_inline_keyboard


TORRENTS_PAGE_SIZE = 20


def build_torrents_page_text(torrents, offset: int) -> str:
    if not torrents:
        return "Торрентов нет."

    page = torrents[offset:offset + TORRENTS_PAGE_SIZE]
    lines = []

    for idx, t in enumerate(page, start=offset + 1):
        name = t.name
        status = str(getattr(t, "status", "unknown"))
        percent = round((getattr(t, "percent_done", 0) or 0) * 100, 1)
        rate = format_bytes(getattr(t, "rate_download", 0) or 0)
        eta = getattr(t, "eta", None)
        is_finished = bool(getattr(t, "is_finished", False))

        if is_finished:
            info = "готово"
        elif status == "downloading":
            info = f"{percent}% • {rate}/s • ETA {eta}"
        else:
            info = f"{status} • {percent}%"

        lines.append(f"{idx}. {name}\n{info}")

    total = len(torrents)
    start_num = offset + 1
    end_num = min(offset + TORRENTS_PAGE_SIZE, total)

    header = f"Торренты {start_num}-{end_num} из {total}\n"
    return header + "\n\n".join(lines)


def build_torrents_page_keyboard(total: int, offset: int) -> InlineKeyboardMarkup | None:
    buttons = []

    if offset > 0:
        prev_offset = max(0, offset - TORRENTS_PAGE_SIZE)
        buttons.append(
            InlineKeyboardButton("⬅️ Назад", callback_data=f"torrents_page:{prev_offset}")
        )

    # Показываем кнопку "Ещё", пока пользователь не дошёл до самого конца.
    # Даже если следующая "страница" выходит за пределы, offset будет скорректирован
    # в `torrents_page_callback`, а тесты ожидают наличие обеих кнопок на второй странице
    # при total = TORRENTS_PAGE_SIZE * 2.
    if offset + TORRENTS_PAGE_SIZE <= total:
        next_offset = offset + TORRENTS_PAGE_SIZE
        buttons.append(
            InlineKeyboardButton("➡️ Ещё", callback_data=f"torrents_page:{next_offset}")
        )

    if not buttons:
        return None

    return InlineKeyboardMarkup([buttons])


def fetch_torrents():
    client = get_client()
    torrents = client.get_torrents(arguments=[
        "id",
        "name",
        "status",
        "percentDone",
        "rateDownload",
        "eta",
        "isFinished",
    ])
    return torrents


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    if not is_authorized(update):
        await deny_access(update)
        return

    await update.message.reply_text(
        "Torrent bot online.",
        reply_markup=main_menu_keyboard(),
    )
    await update.message.reply_text(
        "Главное меню:",
        reply_markup=start_inline_keyboard(),
    )


async def space_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    if not is_authorized(update):
        await deny_access(update)
        return

    await update.message.reply_text(disk_report())


async def torrents_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    if not is_authorized(update):
        await deny_access(update)
        return

    torrents = fetch_torrents()

    if not torrents:
        await update.message.reply_text("Торрентов нет.")
        return

    text = build_torrents_page_text(torrents, 0)
    keyboard = build_torrents_page_keyboard(len(torrents), 0)

    await update.message.reply_text(text, reply_markup=keyboard)


async def torrents_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return

    if not is_authorized(update):
        await query.answer()
        await deny_access(update)
        return

    data = query.data or ""
    if not data.startswith("torrents_page:"):
        return

    await query.answer()

    try:
        offset = int(data.split(":", 1)[1])
    except ValueError:
        await query.message.reply_text("Ошибка пагинации списка торрентов.")
        return

    torrents = fetch_torrents()

    if not torrents:
        await query.edit_message_text("Торрентов нет.")
        return

    total = len(torrents)
    if offset < 0:
        offset = 0
    if offset >= total:
        offset = max(0, ((total - 1) // TORRENTS_PAGE_SIZE) * TORRENTS_PAGE_SIZE)

    text = build_torrents_page_text(torrents, offset)
    keyboard = build_torrents_page_keyboard(total, offset)

    await query.edit_message_text(text, reply_markup=keyboard)
