from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from config import (
    CERT_FILE_PATH,
    TRANSMISSION_PASSWORD,
    TRANSMISSION_USERNAME,
    WEB_UI_URL,
)
from telegram_ui import cert_os_keyboard, help_menu_keyboard, home_question_keyboard
from utils.auth import deny_access, is_authorized


def back_to_help_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("⬅️ Назад в помощь", callback_data="help_menu")]]
    )


def cert_instruction_text(os_name: str) -> str:
    if os_name == "macos":
        return (
            "macOS\n\n"
            "1. Сохрани файл сертификата.\n"
            "2. Открой Keychain Access.\n"
            "3. Перетащи сертификат в keychain System.\n"
            "4. Открой сертификат двойным кликом.\n"
            "5. В разделе Trust выбери:\n"
            "   When using this certificate → Always Trust.\n"
            "6. Закрой окно и введи пароль macOS.\n"
            "7. После этого открой:\n"
            f"{WEB_UI_URL}"
        )

    if os_name == "windows":
        return (
            "Windows\n\n"
            "1. Сохрани файл сертификата.\n"
            "2. Дважды кликни по нему.\n"
            "3. Нажми Install Certificate.\n"
            "4. Выбери Local Machine.\n"
            "5. Выбери Place all certificates in the following store.\n"
            "6. Укажи Trusted Root Certification Authorities.\n"
            "7. Заверши импорт.\n"
            "8. После этого открой:\n"
            f"{WEB_UI_URL}"
        )

    return (
        "Linux\n\n"
        "1. Сохрани файл сертификата.\n"
        "2. Добавь его в системное хранилище сертификатов.\n"
        "3. Для Debian/Ubuntu обычно:\n"
        "   sudo cp caddy-local-root.crt /usr/local/share/ca-certificates/\n"
        "   sudo update-ca-certificates\n"
        "4. Перезапусти браузер.\n"
        "5. После этого открой:\n"
        f"{WEB_UI_URL}"
    )


async def handle_help_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return

    if not is_authorized(update):
        await query.answer()
        await deny_access(update)
        return

    data = query.data or ""
    await query.answer()

    if data == "help_menu":
        await query.message.reply_text(
            "Помощь:",
            reply_markup=help_menu_keyboard(),
        )
        return

    if data == "help_web_ui":
        await query.message.reply_text(
            "Ты дома?",
            reply_markup=home_question_keyboard(),
        )
        return

    if data == "webui_home_no":
        await query.message.reply_text(
            "Доступ только из домашней сети.",
            reply_markup=back_to_help_keyboard(),
        )
        return

    if data == "webui_home_yes":
        await query.message.reply_text(
            "WEB UI\n\n"
            f"Ссылка:\n{WEB_UI_URL}\n\n"
            f"Логин:\n{TRANSMISSION_USERNAME}\n\n"
            f"Пароль:\n{TRANSMISSION_PASSWORD}",
            reply_markup=back_to_help_keyboard(),
        )
        return

    if data == "help_cert":
        await query.message.reply_text(
            "Какая у тебя операционная система?",
            reply_markup=cert_os_keyboard(),
        )
        return

    if data in {"cert_windows", "cert_linux", "cert_macos"}:
        os_name = data.split("_", 1)[1]

        if CERT_FILE_PATH.exists():
            await query.message.reply_document(document=str(CERT_FILE_PATH))
        else:
            await query.message.reply_text(
                f"Файл сертификата не найден:\n{CERT_FILE_PATH}"
            )

        await query.message.reply_text(
            cert_instruction_text(os_name),
            reply_markup=back_to_help_keyboard(),
        )
