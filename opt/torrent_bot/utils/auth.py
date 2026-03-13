from telegram import ReplyKeyboardRemove, Update

from config import ALLOWED_USERNAMES


def get_username(update: Update) -> str:
    if update.effective_user is None or update.effective_user.username is None:
        return ""
    return update.effective_user.username


def is_authorized(update: Update) -> bool:
    username = get_username(update)
    return username in ALLOWED_USERNAMES


async def deny_access(update: Update) -> None:
    target = update.effective_message
    if target is not None:
        await target.reply_text(
            "Доступ закрыт.",
            reply_markup=ReplyKeyboardRemove(),
        )
