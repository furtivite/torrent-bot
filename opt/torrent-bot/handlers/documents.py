import os
import time

from telegram import Update
from telegram.ext import ContextTypes

from config import DOWNLOADED_DIR, TRACKERS_DIR
from transmission_client import get_client
from utils.auth import deny_access, get_username, is_authorized
from utils.notify import tg_send
from utils.torrent_files import is_valid_torrent_file
from utils.torrent_layout import read_torrent_layout, torrent_already_downloaded


# Защита от спама файлами:
# username -> timestamp последней успешной/неуспешной попытки
_last_upload_attempt = {}

# Минимальная пауза между загрузками одного пользователя
UPLOAD_COOLDOWN_SECONDS = 5

# Лимит размера .torrent файла
MAX_TORRENT_FILE_SIZE_BYTES = 2 * 1024 * 1024  # 2 MB

# Защита от torrent bomb
MAX_TORRENT_FILES = 5000
MAX_TORRENT_TOTAL_SIZE_BYTES = 10 * 1024 * 1024 * 1024 * 1024  # 10 TB
MAX_PATH_LENGTH = 512
MAX_PATH_DEPTH = 20


def torrent_name_already_exists(name: str) -> bool:
    client = get_client()
    torrents = client.get_torrents(arguments=["id", "name"])
    normalized = name.strip().lower()

    for t in torrents:
        existing_name = str(getattr(t, "name", "")).strip().lower()
        if existing_name == normalized:
            return True

    return False


def is_upload_rate_limited(username: str) -> int:
    now = int(time.time())
    last_time = _last_upload_attempt.get(username, 0)
    delta = now - last_time

    if delta < UPLOAD_COOLDOWN_SECONDS:
        return UPLOAD_COOLDOWN_SECONDS - delta

    _last_upload_attempt[username] = now
    return 0


def inspect_torrent_layout_safety(torrent_name: str, files: list[tuple]) -> tuple[bool, str]:
    if not torrent_name or len(torrent_name) > 255:
        return False, "Некорректное имя торрента."

    if len(files) > MAX_TORRENT_FILES:
        return False, f"Torrent отклонён: слишком много файлов ({len(files)})."

    total_size = 0

    for rel_path, expected_size in files:
        rel_path_str = str(rel_path)

        if len(rel_path_str) > MAX_PATH_LENGTH:
            return False, f"Torrent отклонён: слишком длинный путь ({rel_path_str[:120]}...)."

        parts = rel_path.parts
        if len(parts) > MAX_PATH_DEPTH:
            return False, f"Torrent отклонён: слишком глубокая вложенность пути ({rel_path_str[:120]}...)."

        for part in parts:
            if part in {"..", ".", ""}:
                return False, "Torrent отклонён: найден небезопасный путь."
            if len(part) > 255:
                return False, f"Torrent отклонён: слишком длинное имя файла/папки ({part[:120]}...)."

        if expected_size < 0:
            return False, "Torrent отклонён: найден отрицательный размер файла."

        total_size += int(expected_size)

        if total_size > MAX_TORRENT_TOTAL_SIZE_BYTES:
            return False, "Torrent отклонён: суммарный размер данных слишком большой."

    return True, ""


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if message is None or message.document is None or message.from_user is None:
        return

    if not is_authorized(update):
        await deny_access(update)
        return

    username = get_username(update)

    wait_seconds = is_upload_rate_limited(username)
    if wait_seconds > 0:
        await message.reply_text(
            f"Слишком часто. Подожди {wait_seconds} сек. перед следующей загрузкой torrent-файла."
        )
        return

    filename = message.document.file_name or "uploaded.torrent"
    safe_name = os.path.basename(filename)
    temp_path = TRACKERS_DIR / f".uploading_{int(time.time())}_{safe_name}"
    final_path = TRACKERS_DIR / safe_name

    if final_path.exists():
        await message.reply_text(f"Торрент {safe_name} уже есть.")
        return

    file_size = int(getattr(message.document, "file_size", 0) or 0)
    if file_size > MAX_TORRENT_FILE_SIZE_BYTES:
        await message.reply_text(
            f"Торрент {safe_name} отклонён: файл слишком большой ({file_size} байт)."
        )
        tg_send(f"🛡 Отклонён слишком большой torrent от @{username}: {safe_name} ({file_size} bytes)")
        return

    try:
        try:
            tg_file = await context.bot.get_file(message.document.file_id)
            await tg_file.download_to_drive(custom_path=str(temp_path))
        except Exception as e:
            temp_path.unlink(missing_ok=True)
            await message.reply_text(f"Ошибка: не удалось скачать файл {safe_name} из Telegram.")
            tg_send(f"❌ Ошибка скачивания torrent от @{username}: {safe_name}: {type(e).__name__}: {e}")
            return

        try:
            actual_size = temp_path.stat().st_size
            if actual_size > MAX_TORRENT_FILE_SIZE_BYTES:
                temp_path.unlink(missing_ok=True)
                await message.reply_text(
                    f"Торрент {safe_name} отклонён: файл слишком большой ({actual_size} байт)."
                )
                tg_send(f"🛡 Отклонён слишком большой torrent от @{username}: {safe_name} ({actual_size} bytes)")
                return
        except Exception as e:
            temp_path.unlink(missing_ok=True)
            await message.reply_text(f"Ошибка: не удалось проверить размер файла {safe_name}.")
            tg_send(f"❌ Ошибка проверки размера torrent от @{username}: {safe_name}: {type(e).__name__}: {e}")
            return

        try:
            if not is_valid_torrent_file(temp_path):
                temp_path.unlink(missing_ok=True)
                await message.reply_text(f"Файл {safe_name} удалён: это не torrent.")
                tg_send(f"🗑 Удалён невалидный файл от @{username}: {safe_name}")
                return
        except Exception as e:
            temp_path.unlink(missing_ok=True)
            await message.reply_text(f"Ошибка: не удалось проверить, что файл {safe_name} является torrent.")
            tg_send(f"❌ Ошибка валидации torrent от @{username}: {safe_name}: {type(e).__name__}: {e}")
            return

        try:
            torrent_name, files = read_torrent_layout(temp_path)
        except Exception as e:
            temp_path.unlink(missing_ok=True)
            await message.reply_text(f"Ошибка: не удалось прочитать содержимое torrent-файла {safe_name}.")
            tg_send(f"❌ Ошибка чтения метаданных torrent от @{username}: {safe_name}: {type(e).__name__}: {e}")
            return

        is_safe, safety_reason = inspect_torrent_layout_safety(torrent_name, files)
        if not is_safe:
            temp_path.unlink(missing_ok=True)
            await message.reply_text(f"Файл {safe_name} отклонён. {safety_reason}")
            tg_send(f"🛡 Torrent bomb / unsafe torrent отклонён от @{username}: {safe_name}: {safety_reason}")
            return

        try:
            already_downloaded, downloaded_name = torrent_already_downloaded(temp_path, DOWNLOADED_DIR)
        except Exception as e:
            temp_path.unlink(missing_ok=True)
            await message.reply_text(f"Ошибка: не удалось проверить, скачан ли торрент {safe_name} ранее.")
            tg_send(f"❌ Ошибка проверки downloaded для @{username}: {safe_name}: {type(e).__name__}: {e}")
            return

        if already_downloaded:
            temp_path.unlink(missing_ok=True)
            await message.reply_text(f"Торрент {safe_name} уже скачан: {downloaded_name}")
            return

        if final_path.exists():
            temp_path.unlink(missing_ok=True)
            await message.reply_text(f"Торрент {safe_name} уже есть.")
            return

        try:
            if torrent_name_already_exists(torrent_name):
                temp_path.unlink(missing_ok=True)
                await message.reply_text(f"Торрент {safe_name} уже добавлен в Transmission.")
                return
        except Exception as e:
            temp_path.unlink(missing_ok=True)
            await message.reply_text(f"Ошибка: не удалось проверить наличие торрента {safe_name} в Transmission.")
            tg_send(f"❌ Ошибка проверки Transmission для @{username}: {safe_name}: {type(e).__name__}: {e}")
            return

        try:
            temp_path.rename(final_path)
        except Exception as e:
            temp_path.unlink(missing_ok=True)
            await message.reply_text(f"Ошибка: не удалось сохранить торрент {safe_name} в папку trackers.")
            tg_send(f"❌ Ошибка сохранения torrent от @{username}: {safe_name}: {type(e).__name__}: {e}")
            return

        await message.reply_text(f"Torrent сохранён: {safe_name}")
        tg_send(f"📥 Торрент получен от @{username}: {safe_name}")

    except Exception as e:
        temp_path.unlink(missing_ok=True)
        await message.reply_text(f"Неожиданная ошибка обработки файла {safe_name}: {type(e).__name__}: {e}")
        tg_send(f"❌ Неожиданная ошибка handle_document у @{username}: {safe_name}: {type(e).__name__}: {e}")
