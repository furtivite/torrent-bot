## Как создать Telegram‑бота для torrent-bot

Этот документ объясняет, как с нуля создать Telegram‑бота и подключить его к этому проекту.

Официальная документация Telegram про ботов: [https://core.telegram.org/bots#3-how-do-i-create-a-bot](https://core.telegram.org/bots#3-how-do-i-create-a-bot)

---

## 1. Создать бота через BotFather

1. Откройте Telegram и найдите пользователя `@BotFather`.
2. Нажмите **Start**.
3. Отправьте команду:

   ```text
   /newbot
   ```

4. Следуйте инструкциям:
   - введите **имя бота** (любой читаемый текст, например `Home Torrent Bot`);
   - введите **username бота** (должен заканчиваться на `bot`, например `home_torrent_pi_bot`).

5. В конце BotFather пришлёт сообщение вида:

   ```text
   Done! Congratulations on your new bot. ...
   Use this token to access the HTTP API:
   1234567890:AA...your_token_here...
   ```

   **Сохраните токен** — он нужен для `BOT_TOKEN`.

> Никогда не коммитьте токен в git и не выкладывайте его публично.

---

## 2. Найти свой Telegram username и chat id

### 2.1. Username

1. Откройте настройки Telegram → **Edit profile / Изменить профиль**.
2. Поле **Username** — это ваш логин, его нужно будет добавить в `ALLOWED_USERNAMES`.
3. Если username пустой, задайте его (он должен быть уникальным).

### 2.2. Chat ID

Самый простой вариант — с помощью служебного бота:

1. В Telegram найдите `@userinfobot` или `@get_id_bot`.
2. Нажмите **Start** и отправьте любое сообщение.
3. Бот пришлёт ответ вида:

   ```text
   Id: 420311639
   ```

   Это и есть ваш `CHAT_ID`.

Альтернатива (если не хотите использовать сторонние боты) — можно временно написать простой скрипт внутри проекта, который выводит `update.effective_chat.id`, но для большинства пользователей `@userinfobot` проще.

---

## 3. Заполнить конфигурацию `/etc/torrent-bot.env`

На сервере (Raspberry Pi), где запущен бот:

1. Откройте (или создайте) файл `/etc/torrent-bot.env`:

   ```bash
   sudo nano /etc/torrent-bot.env
   ```

2. Заполните как минимум эти поля (подставьте свои значения):

   ```bash
   BOT_TOKEN="ВАШ_ТОКЕН_ОТ_BOTFATHER"
   CHAT_ID="ВАШ_CHAT_ID_ЧИСЛОМ"

   # Список разрешённых username через запятую (без @)
   ALLOWED_USERNAMES="yourusername,seconduser"

   # Пути к данным (подстроить под свою систему при необходимости)
   TRACKERS_DIR="/mnt/data/trackers"
   DOWNLOADED_DIR="/mnt/data/downloaded"

   TRANSMISSION_HOST="127.0.0.1"
   TRANSMISSION_PORT="9091"
   TRANSMISSION_USERNAME="transmission_user"
   TRANSMISSION_PASSWORD="transmission_password"

   WEB_UI_URL="https://pi5.local/transmission/web/"
   CERT_FILE_PATH="/mnt/data/certs/caddy-local-root.crt"
   ```

3. Сохраните файл и закройте редактор.

> Этот файл **не должен попадать в репозиторий**. В `.gitignore` уже есть строка `/etc/torrent-bot.env`.

---

## 4. Перезапустить бота

Если бот запущен как systemd‑сервис:

```bash
sudo systemctl daemon-reload        # если менялся unit-файл
sudo systemctl restart torrent-bot.service
sudo systemctl status torrent-bot.service
```

Статус должен быть `active (running)`.

Если хотите запустить вручную:

```bash
cd /opt/torrent-bot
set -a
source /etc/torrent-bot.env
set +a
source /opt/torrent-bot-venv/bin/activate
python -m opt.torrent_bot.app
```

---

## 5. Проверить, что бот работает

1. В Telegram найдите вашего бота по username (например, `@home_torrent_pi_bot`).
2. Нажмите **Start** или отправьте `/start`.
3. Убедитесь, что:
   - бот отвечает на `/start`;
   - кнопки под полем ввода и inline‑меню работают;
   - команды `/space` и `/torrents` возвращают ожидаемые ответы (если Transmission настроен).

Если бот не отвечает:

- проверьте `BOT_TOKEN` и `CHAT_ID` в `/etc/torrent-bot.env`;
- убедитесь, что ваш username есть в `ALLOWED_USERNAMES`;
- посмотрите логи на сервере:

  ```bash
  sudo journalctl -u torrent-bot.service -f
  ```

