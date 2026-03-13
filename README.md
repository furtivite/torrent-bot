## Torrent Bot для Transmission

Самостоятельно хостящийся Telegram‑бот для управления Transmission BitTorrent‑сервером на домашнем сервере (например, Raspberry Pi с Ubuntu).

Бот:

- принимает `.torrent`‑файлы и magnet‑ссылки из Telegram;
- проверяет безопасность торрентов (torrent bombs, path traversal, размер и т.п.);
- кладёт `.torrent` в watch‑директорию Transmission;
- показывает список торрентов с пагинацией и управлением (пауза/возобновить/удалить);
- присылает уведомления о прогрессе и завершении;
- показывает использование диска;
- показывает URL и учётные данные Web UI Transmission;
- выдаёт инструкции по установке HTTPS‑сертификата.

> ВАЖНО: **сам Transmission и сервис скачивания файлов НЕ входят в этот репозиторий**.  
> Этот проект — только Telegram‑бот и обёртка вокруг уже настроенного Transmission.

---

## Архитектура

Основной код живёт в `opt/torrent-bot/`:

- `app.py` — точка входа, регистрация хендлеров.
- `config.py` — загрузка конфигурации из `/etc/torrent-bot.env`.
- `monitor.py` — фоновой мониторинг Transmission и уведомления.
- `transmission_client.py` — обёртка над `transmission-rpc`.
- `state.py` — простое хранение состояния мониторинга.
- `handlers/` — Telegram‑хендлеры команд, документов, кнопок и magnet‑ссылок.
- `utils/` — утилиты (аутентификация, диск, уведомления, работа с `.torrent` и т.п.).
- `telegram_ui.py` — клавиатуры и кнопки Telegram.

Подробнее см. в `docs/overview.md`.

---

## Требования

- Ubuntu (или другой Linux, пример ниже для Ubuntu).
- Python 3.12.
- Сервис Transmission уже установлен и настроен:
  - запущен `transmission-daemon` или Transmission в контейнере;
  - включён RPC‑доступ (host, port, user, password);
  - настроена watch‑директория для `.torrent`‑файлов.
- Доступ по SSH к серверу.

---

## Безопасность

- Бот работает только с пользователями из `ALLOWED_USERNAMES` (whitelist по username).
- Валидация `.torrent`‑файлов и их структуры защищает от:
  - path traversal внутри архива;
  - аномально длинных путей и имён;
  - слишком большого количества файлов и суммарного размера (torrent bombs).
- Все файловые операции используют пути из конфигурации (`DATA_ROOT`, `TRACKERS_DIR`, `DOWNLOADED_DIR` и т.п.).
- При ошибках:
  - пользователю показывается короткое сообщение на русском;
  - детали логируются отдельно.

---

## Быстрый старт (пример для Ubuntu + SSH)

### 1. Подключение к серверу

```bash
ssh user@your-server
```

Дальше все команды выполняются на сервере.

### 2. Клонирование репозитория

```bash
cd /opt
sudo git clone https://github.com/your-user/torrent-bot-project.git
sudo chown -R "$USER":"$USER" torrent-bot-project
cd torrent-bot-project
```

### 3. Создать виртуальное окружение и установить зависимости

```bash
python3.12 -m venv /opt/torrent-bot-venv
source /opt/torrent-bot-venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

deactivate
```

> Если файла `requirements.txt` нет, установите вручную:
>
> ```bash
> pip install python-telegram-bot~=20.0 transmission-rpc requests bencodepy
> ```

### 4. Настроить окружение `/etc/torrent-bot.env`

Создайте файл (от root, но без коммита в Git):

```bash
sudo tee /etc/torrent-bot.env > /dev/null <<'ENV'
BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN_HERE"
CHAT_ID="YOUR_TELEGRAM_CHAT_ID_HERE"

ALLOWED_USERNAMES="user1,user2"

# Базовый каталог данных (по умолчанию /mnt/data)
DATA_ROOT="/mnt/data"

# Директория для .torrent файлов (watch-dir Transmission)
TRACKERS_DIR="/mnt/data/trackers"

TRANSMISSION_HOST="127.0.0.1"
TRANSMISSION_PORT="9091"
TRANSMISSION_USERNAME="your-transmission-username"
TRANSMISSION_PASSWORD="your-transmission-password"

DOWNLOADED_DIR="/mnt/data/downloaded"
WEB_UI_URL="https://your-hostname-or-ip/transmission/web/"
CERT_FILE_PATH="/mnt/data/certs/caddy-local-root.crt"
ENV
```

Проверьте пример значений в `etc/torrent-bot.env.example`.

### 5. Проверка ручным запуском

```bash
cd /opt/torrent-bot-project/opt/torrent-bot
source /opt/torrent-bot-venv/bin/activate

BOT_TOKEN=... CHAT_ID=... ALLOWED_USERNAMES=... \
TRANSMISSION_HOST=... TRANSMISSION_PORT=... \
TRANSMISSION_USERNAME=... TRANSMISSION_PASSWORD=... \
TRACKERS_DIR=... DOWNLOADED_DIR=... WEB_UI_URL=... CERT_FILE_PATH=... \
python app.py
```

Удобнее просто экспортировать переменные из `/etc/torrent-bot.env` через systemd (см. ниже), но для отладки можно задавать вручную.

Отправьте боту `/start` из Telegram и убедитесь, что он отвечает и видит Transmission.

---

## Установка как systemd‑сервис

Пример unit‑файла уже лежит в `etc/systemd/system/torrent-bot.service`.  
Установите его в systemd:

```bash
sudo cp etc/systemd/system/torrent-bot.service /etc/systemd/system/torrent-bot.service
sudo systemctl daemon-reload
sudo systemctl enable torrent-bot.service
sudo systemctl start torrent-bot.service
sudo systemctl status torrent-bot.service
```

Убедитесь, что в `torrent-bot.service` указаны:

- корректный путь до virtualenv (`/opt/torrent-bot-venv/bin/python`);
- корректный путь к `app.py` внутри репозитория, например:

  ```ini
  WorkingDirectory=/opt/torrent-bot-project/opt/torrent-bot
  ExecStart=/opt/torrent-bot-venv/bin/python app.py
  ```

- путь к файлу `/etc/torrent-bot.env` через `EnvironmentFile=/etc/torrent-bot.env`.

---

## Безопасность и ограничения

- Бот настроен для **личного использования** и работает только с пользователями из `ALLOWED_USERNAMES`.
- Все пути и директории берутся из переменных окружения (`DATA_ROOT`, `TRACKERS_DIR`, `DOWNLOADED_DIR` и т.п.).
- Валидация `.torrent`‑файлов и структуры торрента защищает от:
  - слишком больших метаданных и количества файлов;
  - path traversal внутри торрента;
  - чрезмерно больших файлов.
- При любых ошибках:
  - пользователю показывается короткое сообщение на русском;
  - подробности логируются через существующий логгер / Telegram‑уведомления.

---

## Известные ограничения

- Бот рассчитан на **личное использование** и не предназначен для публичных многопользовательских сценариев.
- Авторизация привязана к списку `ALLOWED_USERNAMES`; поддержка сложных ролей и прав доступа не реализована.
- Бот зависит от доступности Transmission (RPC). При недоступности Transmission часть функций (список торрентов, управление, magnet‑ссылки) будет недоступна.

---

## Дополнительно

- Более подробное описание архитектуры и потоков данных: `docs/overview.md`.
- Чек‑лист для развёртывания и отладки: `docs/setup-ubuntu-ssh.md`.
- Требования к настройке Transmission: `docs/transmission-requirements.md`.

---

## Тесты

Тесты пишутся на `pytest`.

Запуск из корня репозитория:

```bash
pytest
```

GitHub Actions автоматически запускает тесты для всех коммитов и pull request‑ов в основные ветки.

---

## Участие в разработке

- Правила и рекомендации: см. `CONTRIBUTING.md`.
- Для багов используйте шаблон issue «Bug report».
- Для предложений по новым функциям — шаблон «Feature request».
- Для PR действует простой чек‑лист (описание изменений, зачем они нужны, запуск тестов).

---

## История проекта

- **Март 2026** — начальная версия бота для личного домашнего использования:
  - управление Transmission через Telegram;
  - базовая валидация `.torrent`‑файлов и защита от опасных торрентов;
  - уведомления о состоянии торрентов и диска;
  - интеграция с systemd и конфигурация через `/etc/torrent-bot.env`.
  - добавлена документация и правила для AI‑агентов в `.cursor/`.

- **Тесты**:
  - добавлены базовые pytest‑тесты для утилит (`utils`) и части логики безопасности торрентов;
  - запуск: из корня проекта выполнить `pytest`.

