## Развёртывание на Ubuntu по SSH

Этот документ дополняет `README.md` и показывает типичный сценарий установки на Ubuntu‑сервер с доступом по SSH.

> Transmission (daemon / контейнер) и его каталоги загрузки настраиваются **отдельно** и не входят в этот репозиторий.

---

## 1. Подключение к серверу

С локальной машины:

```bash
ssh user@your-server
```

Дальше все команды выполняются на сервере.

---

## 2. Подготовка каталогов данных

Создайте базовую структуру (пример):

```bash
sudo mkdir -p /mnt/data/trackers
sudo mkdir -p /mnt/data/downloaded
sudo mkdir -p /mnt/data/certs
sudo chown -R "$USER":"$USER" /mnt/data
```

Убедитесь, что Transmission настроен так, чтобы:

- watch‑директория указывала на `/mnt/data/trackers`;
- каталог загрузок совпадал с `DOWNLOADED_DIR` (например, `/mnt/data/downloaded`).

---

## 3. Установка Python и git

```bash
sudo apt update
sudo apt install -y python3.12 python3.12-venv git
```

---

## 4. Клонирование репозитория

```bash
cd /opt
sudo git clone https://github.com/your-user/torrent-bot.git
sudo chown -R "$USER":"$USER" torrent-bot
cd torrent-bot
```

---

## 5. Виртуальное окружение и зависимости

Рекомендуется создать виртуальное окружение один раз и выполнять установку зависимостей от имени
того пользователя, который будет разворачивать код (не от root).

```bash
python3.12 -m venv /opt/torrent-bot-venv
source /opt/torrent-bot-venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt  # или см. README.md для ручной установки

deactivate
```

---

## 6. Конфигурация `/etc/torrent-bot.env`

Создайте файл конфигурации:

```bash
sudo tee /etc/torrent-bot.env > /dev/null <<'ENV'
BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN_HERE"
CHAT_ID="YOUR_TELEGRAM_CHAT_ID_HERE"

ALLOWED_USERNAMES="user1,user2"

DATA_ROOT="/mnt/data"
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

Пример значений можно посмотреть в `etc/torrent-bot.env.example`.

---

## 7. Проверка в интерактивном режиме

```bash
cd /opt/torrent-bot
source /opt/torrent-bot-venv/bin/activate

set -a
source /etc/torrent-bot.env
set +a

python -m opt.torrent_bot.app
```

Проверьте:

- бот отвечает на `/start` от whitelisted пользователя;
- команда `/space` показывает состояние диска;
- команда `/torrents` показывает список торрентов (если они есть);
- загрузка `.torrent` попадает в `TRACKERS_DIR` и подхватывается Transmission.

Остановите бота (Ctrl+C) после проверки.

---

## 8. Установка systemd‑сервиса

Создайте unit‑файл:

```bash
sudo tee /etc/systemd/system/torrent-bot.service > /dev/null <<'UNIT'
[Unit]
Description=Telegram Torrent Bot
After=network-online.target transmission-daemon.service
Wants=network-online.target
Requires=transmission-daemon.service
RequiresMountsFor=/mnt/data

[Service]
Type=simple
Restart=always
RestartSec=5
User=torrent-bot
WorkingDirectory=/opt/torrent-bot
ExecStart=/opt/torrent-bot-venv/bin/python -m opt.torrent_bot.app
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=/etc/torrent-bot.env

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable torrent-bot.service
sudo systemctl start torrent-bot.service
sudo systemctl status torrent-bot.service
```

---

## 9. Настройка сертификата (CERT_FILE_PATH)

Бот может отправлять файл корневого сертификата пользователю по запросу в меню помощи, если он
настроен в `CERT_FILE_PATH`. Это удобно, когда HTTPS‑терминация (например, через Caddy/nginx)
использует самоподписанный или частный корневой сертификат.

1. Скопируйте файл корневого сертификата в каталог, указанный в `CERT_FILE_PATH`, например
   (пути `/mnt/data/...` ниже — только пример, вы можете выбрать свою структуру каталогов):

   ```bash
   sudo cp /path/to/your-root-ca.crt /mnt/data/certs/caddy-local-root.crt
   sudo chown "$USER":"$USER" /mnt/data/certs/caddy-local-root.crt
   ```

2. Убедитесь, что путь в `/etc/torrent-bot.env` совпадает:

   ```bash
   CERT_FILE_PATH="/mnt/data/certs/caddy-local-root.crt"
   ```

3. В Telegram откройте раздел помощи бота:
   - нажмите «ℹ️ Помощь» → «🔐 Добавить сертификат»;
   - выберите вашу ОС (Windows / Linux / macOS);
   - бот пришлёт файл сертификата и инструкции по установке.

> Обратите внимание: сам HTTPS‑reverse‑proxy (Caddy, nginx и т.п.) настраивается отдельно от этого
> проекта. Бот лишь выдаёт файл корневого сертификата и текстовые инструкции.

---

## 10. Создание отдельного пользователя для сервиса

Для повышения безопасности рекомендуется запускать сервис не от root, а от отдельного системного
пользователя, у которого есть доступ только к нужным каталогам.

Пример:

```bash
sudo useradd --system --home /opt/torrent-bot --shell /usr/sbin/nologin torrent-bot

# Дать пользователю доступ к коду бота
sudo chown -R torrent-bot:torrent-bot /opt/torrent-bot

# Убедиться, что у torrent-bot есть права на TRACKERS_DIR и DOWNLOADED_DIR
# (ниже пример, конкретные пути берутся из /etc/torrent-bot.env):
sudo chown -R torrent-bot:torrent-bot /mnt/data/trackers /mnt/data/downloaded
```

Обратите внимание: если Transmission запущен под другим пользователем, возможно, потребуется
использовать общую группу и более точную настройку прав. В этом случае не меняйте владельца
каталогов Transmission, а настройте права доступа так, чтобы и Transmission, и `torrent-bot`
имели нужные разрешения.

---

## 11. Обновление бота из GitHub по SSH

1. На локальной машине:

   ```bash
   git push origin main  # или ваша основная ветка
   ```

2. На сервере по SSH:

   ```bash
   ssh user@your-server

   cd /opt/torrent-bot
   git pull

   source /opt/torrent-bot-venv/bin/activate
   pip install -r requirements.txt
   deactivate

   sudo systemctl daemon-reload
   sudo systemctl restart torrent-bot.service
   sudo systemctl status torrent-bot.service
   ```

---

## 12. Напоминание о границах проекта

- Этот репозиторий:
  - **не устанавливает и не настраивает Transmission**;
  - не создаёт и не управляет торрент‑трекерами;
  - не занимается внешним доступом к Web UI (reverse proxy, HTTPS и т.п.).
- Все эти задачи решаются отдельными сервисами/конфигурациями, а бот лишь:
  - передаёт `.torrent` и magnet‑ссылки в уже работающий Transmission;
  - показывает состояние торрентов;
  - уведомляет о прогрессе и состоянии диска.

