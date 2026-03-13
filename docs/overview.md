## Обзор архитектуры

Этот проект — Telegram‑бот, управляющий уже существующим Transmission BitTorrent‑сервером.

### Основные компоненты

- `app.py`
  - точка входа;
  - создаёт `Application` из `python-telegram-bot` v20+;
  - регистрирует все хендлеры (`CommandHandler`, `CallbackQueryHandler`, `MessageHandler`);
  - запускает бота (`run_polling`).

- `config.py`
  - читает переменные окружения (фактически из `/etc/torrent-bot.env`);
  - предоставляет готовые константы:
    - `BOT_TOKEN`, `CHAT_ID`, `ALLOWED_USERNAMES`;
    - `DATA_ROOT`, `TRACKERS_DIR`, `DOWNLOADED_DIR`;
    - `TRANSMISSION_HOST`, `TRANSMISSION_PORT`, `TRANSMISSION_USERNAME`, `TRANSMISSION_PASSWORD`;
    - `WEB_UI_URL`, `CERT_FILE_PATH`;
    - `CHECK_INTERVAL_SECONDS`, `STALL_MINUTES`.

- `transmission_client.py`
  - создаёт клиента `transmission_rpc.Client` с заданными host/port/credentials;
  - используется в хендлерах и мониторинге.

- `monitor.py`
  - в фоне отслеживает состояние торрентов;
  - реагирует на события:
    - добавление торрента;
    - начало скачивания;
    - завершение скачивания;
    - длительное отсутствие пиров/сидов (stall);
  - шлёт уведомления в Telegram через `utils.notify.tg_send` / `tg_send_error`.

- `state.py`
  - небольшое хранилище in‑memory состояния мониторинга:
    - `seen_torrents`, `stalled_since`, `completed_reported`, `initial_snapshot_done`.

- `telegram_ui.py`
  - определяет текст кнопок и все клавиатуры:
    - главное меню (`ReplyKeyboardMarkup`);
    - inline‑меню для `/start`;
    - меню помощи, выбор ОС, действия над торрентами.

- `handlers/`
  - `commands.py`:
    - `/start`, `/help`, `/space`, `/torrents`;
    - вывод свободного места на диске (через `utils.disk.disk_report`);
    - постраничный список торрентов c inline‑кнопками.
  - `documents.py`:
    - обработка загруженных `.torrent`‑файлов;
    - защита от спама (cooldown по пользователю);
    - проверка размера файла;
    - валидация `.torrent` и структуры торрента;
    - проверка уже скачанных торрентов и дубликатов в Transmission;
    - безопасное перемещение в `TRACKERS_DIR`.
  - `magnets.py`:
    - приём magnet‑ссылок;
    - добавление торрента в Transmission через `add_torrent`.
  - `buttons.py`:
    - обработка текстовых кнопок главного меню (ReplyKeyboard);
    - делегирует в соответствующие команды / подсказки.
  - `help_menu.py`:
    - inline‑меню помощи;
    - выдача Web UI URL и учётных данных;
    - выдача сертификата (`CERT_FILE_PATH`) и инструкций для Windows/Linux/macOS.

- `utils/`
  - `auth.py`:
    - авторизация по username на основе `ALLOWED_USERNAMES`;
    - выдаёт пользователю «Доступ закрыт.» и убирает клавиатуру при отказе.
  - `disk.py`:
    - форматирование байтов в читаемый вид;
    - `disk_report()` — краткий отчёт о диске, по умолчанию по `DATA_ROOT`.
  - `notify.py`:
    - отправка сообщений в Telegram по токену/чат‑ID напрямую через HTTP;
    - троттлинг одинаковых ошибок.
  - `torrent_files.py`:
    - быстрая проверка, что файл выглядит как bencoded `.torrent`.
  - `torrent_layout.py`:
    - разбор `.torrent` через `bencodepy`;
    - построение списка файлов торрента;
    - проверка, скачан ли торрент уже в `DOWNLOADED_DIR`.

### Без Transmission

Этот код **не** разворачивает Transmission:

- установка и конфигурация Transmission (daemon / контейнер) выполняется вручную;
- нужно отдельно настроить:
  - RPC (host, port, user, password);
  - директории загрузки;
  - watch‑директорию для `.torrent` (`TRACKERS_DIR`).

---

## Поток обработки `.torrent` файла

1. Пользователь отправляет `.torrent` боту в Telegram.
2. `handlers/documents.py`:
   - проверяет авторизацию;
   - ограничивает частоту загрузок;
   - скачивает файл во временный путь в `TRACKERS_DIR`;
   - проверяет размер и тип файла;
   - читает структуру торрента (`read_torrent_layout`);
   - проверяет безопасность структуры (`inspect_torrent_layout_safety`);
   - проверяет, не скачан ли торрент ранее (`torrent_already_downloaded`);
   - проверяет дубликаты по имени в Transmission;
   - переносит `.torrent` в финальный путь в `TRACKERS_DIR`.
3. Transmission, настроенный отдельно, подхватывает файл из watch‑директории.

---

## Поток обработки magnet‑ссылки

1. Пользователь присылает `magnet:?…` текстом.
2. `handlers/magnets.py`:
   - проверяет авторизацию;
   - валидирует, что текст «похож» на magnet;
   - вызывает `transmission_client.get_client().add_torrent(magnet)`.

---

## Мониторинг и уведомления

- Функция `monitor_loop()`:
  - запускается при инициализации приложения;
  - периодически опрашивает торренты через Transmission RPC;
  - отслеживает:
    - новые торренты;
    - начало скачивания;
    - завершение скачивания;
    - долгий простой без пиров;
  - отправляет уведомления в Telegram через `utils.notify`.

---

## Безопасность

- Авторизация — только по whitelisted username.
- Все пути и директории берутся из конфигурации (`/etc/torrent-bot.env` → `config.py`).
- Обработка `.torrent` защищена от:
  - path traversal;
  - слишком длинных путей/имён;
  - чрезмерного количества файлов / суммарного размера.
- Бот не раскрывает чувствительную информацию неавторизованным пользователям.

