## Как обновить бота до новой версии

Этот файл описывает типичный сценарий обновления уже установленного бота до новой версии из GitHub.
Предполагается, что бот развёрнут по структуре из `README.md` и `docs/setup-ubuntu-ssh.md`.

---

## 1. Подключиться к серверу

С локальной машины:

```bash
ssh user@your-server
```

Дальше все команды выполняются на сервере.

---

## 2. Обновить код из GitHub

Перейдите в каталог проекта и подтяните последние изменения:

```bash
cd /opt/torrent-bot
git pull
```

Если вы используете не `main`, а другую ветку, укажите её явно:

```bash
git pull origin your-branch
```

---

## 3. Обновить зависимости в виртуальном окружении

Виртуальное окружение создаётся один раз (см. `setup-ubuntu-ssh.md`). Для обновления пакетов:

```bash
source /opt/torrent-bot-venv/bin/activate
pip install -r requirements.txt
deactivate
```

Если появятся новые зависимости (например, для тестов или линтера), они подтянутся автоматически.

---

## 4. Проверить systemd‑юнит (при изменении структуры)

Если вы переходите с старой структуры на новую или переносите код,
убедитесь, что юнит `/etc/systemd/system/torrent-bot.service` указывает на правильные пути.

Рекомендуемый вариант:

```ini
[Service]
Type=simple
User=torrent-bot
WorkingDirectory=/opt/torrent-bot
ExecStart=/opt/torrent-bot-venv/bin/python -m opt.torrent_bot.app
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=/etc/torrent-bot.env
```

После правок:

```bash
sudo systemctl daemon-reload
```

Если структура уже была такой — этот шаг можно пропустить.

---

## 5. Перезапустить сервис бота

После обновления кода и зависимостей перезапустите сервис:

```bash
sudo systemctl restart torrent-bot.service
sudo systemctl status torrent-bot.service
```

Статус должен быть `active (running)`.

---

## 6. Быстрая проверка работы

1. В Telegram отправьте боту:
   - `/start`
   - `/space`
   - `/torrents`
2. Параллельно на сервере посмотрите логи:

   ```bash
   sudo journalctl -u torrent-bot.service -f
   ```

   Убедитесь, что при выполнении команд:
   - нет ошибок подключения к Transmission (если он запущен);
   - нет трейсбеков Python.

Если что‑то идёт не так, сначала смотрите логи `journalctl`, затем при необходимости — внутрь
конфигурации `/etc/torrent-bot.env` и systemd‑юнита.

