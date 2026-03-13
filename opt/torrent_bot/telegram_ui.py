from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup


# Тексты кнопок главного меню
START_BUTTON = "🚀 Start"
SPACE_BUTTON = "💾 Место на диске"
TORRENTS_BUTTON = "📋 Торренты"
MAGNET_BUTTON = "🧲 Добавить magnet"
HELP_BUTTON = "ℹ️ Помощь"
RESTART_TRANSMISSION_BUTTON = "🔄 Перезапустить Transmission"

# Тексты и callback_data для inline‑кнопок
INLINE_SPACE_BUTTON = "💾 Место на диске"
INLINE_TORRENTS_BUTTON = "📋 Торренты"
INLINE_MAGNET_BUTTON = "🧲 Добавить magnet"
INLINE_HELP_BUTTON = "ℹ️ Помощь"

HELP_WEB_UI_BUTTON = "🌐 WEB UI"
HELP_CERT_BUTTON = "🔐 Добавить сертификат"

YES_BUTTON = "Да"
NO_BUTTON = "Нет"

CERT_WINDOWS_BUTTON = "Windows"
CERT_LINUX_BUTTON = "Linux"
CERT_MACOS_BUTTON = "macOS"

TORRENT_RESUME_BUTTON = "▶️ Resume"
TORRENT_PAUSE_BUTTON = "⏸ Pause"
TORRENT_DELETE_BUTTON = "❌ Delete"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [START_BUTTON, SPACE_BUTTON],
        [TORRENTS_BUTTON, MAGNET_BUTTON],
        [HELP_BUTTON],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        is_persistent=True,
    )


def start_inline_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(INLINE_SPACE_BUTTON, callback_data="space"),
            InlineKeyboardButton(INLINE_TORRENTS_BUTTON, callback_data="torrents"),
        ],
        [
            InlineKeyboardButton(INLINE_MAGNET_BUTTON, callback_data="add_magnet"),
            InlineKeyboardButton(INLINE_HELP_BUTTON, callback_data="help_menu"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def help_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(HELP_WEB_UI_BUTTON, callback_data="help_web_ui"),
            InlineKeyboardButton(HELP_CERT_BUTTON, callback_data="help_cert"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def home_question_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(YES_BUTTON, callback_data="webui_home_yes"),
            InlineKeyboardButton(NO_BUTTON, callback_data="webui_home_no"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def cert_os_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(CERT_WINDOWS_BUTTON, callback_data="cert_windows"),
            InlineKeyboardButton(CERT_LINUX_BUTTON, callback_data="cert_linux"),
            InlineKeyboardButton(CERT_MACOS_BUTTON, callback_data="cert_macos"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def torrent_actions_keyboard(torrent_id: int, is_paused: bool = False) -> InlineKeyboardMarkup:
    pause_resume_label = TORRENT_RESUME_BUTTON if is_paused else TORRENT_PAUSE_BUTTON
    pause_resume_action = "resume" if is_paused else "pause"

    keyboard = [
        [
            InlineKeyboardButton(
                pause_resume_label,
                callback_data=f"{pause_resume_action}:{torrent_id}",
            ),
            InlineKeyboardButton(
                TORRENT_DELETE_BUTTON,
                callback_data=f"delete:{torrent_id}",
            ),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
