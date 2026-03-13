#!/opt/torrent-bot-venv/bin/python
import asyncio
import logging

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from .config import BOT_TOKEN, TRACKERS_DIR
from .handlers.buttons import handle_menu_button, handle_start_inline_button, help_cmd
from .handlers.commands import (
    space_cmd,
    start_cmd,
    torrents_cmd,
    torrents_page_callback,
)
from .handlers.documents import handle_document
from .handlers.help_menu import handle_help_callbacks
from .handlers.magnets import handle_magnet
from .monitor import monitor_loop
from .utils.notify import tg_send


logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("torrent-bot")


async def post_init(app: Application) -> None:
    asyncio.create_task(monitor_loop())
    tg_send("🤖 Torrent bot запущен.")


def main():
    TRACKERS_DIR.mkdir(parents=True, exist_ok=True)

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("space", space_cmd))
    app.add_handler(CommandHandler("torrents", torrents_cmd))

    app.add_handler(
        CallbackQueryHandler(
            handle_start_inline_button,
            pattern=r"^(space|torrents|add_magnet|help_menu)$",
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            torrents_page_callback,
            pattern=r"^torrents_page:\d+$",
        )
    )
    app.add_handler(CallbackQueryHandler(handle_help_callbacks))

    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^magnet:\?"), handle_magnet))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_button))

    app.run_polling(close_loop=False)


if __name__ == "__main__":
    main()
