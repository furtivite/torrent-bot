import types

import pytest

from opt.torrent_bot.handlers import magnets


class DummyMessage:
    def __init__(self, text="magnet:?xt=urn:btih:abc"):
        self.text = text
        self.from_user = types.SimpleNamespace(username="user1")
        self.replies = []

    async def reply_text(self, text):
        self.replies.append(text)


class DummyUpdate:
    def __init__(self, text="magnet:?xt=urn:btih:abc", username="user1"):
        self.message = DummyMessage(text=text)
        self.effective_user = types.SimpleNamespace(username=username)


class DummyContext:
    bot = None


@pytest.mark.anyio
async def test_handle_magnet_success(monkeypatch):
    calls = {}

    async def fake_deny_access(update):
        calls["denied"] = True

    def fake_is_authorized(update):
        return True

    def fake_get_username(update):
        return "user1"

    class DummyClient:
        def __init__(self):
            self.magnets = []

        def add_torrent(self, magnet):
            self.magnets.append(magnet)

    client = DummyClient()

    def fake_get_client():
        return client

    sent_notifications = []

    def fake_tg_send(text: str):
        sent_notifications.append(text)

    monkeypatch.setattr(magnets, "is_authorized", fake_is_authorized)
    monkeypatch.setattr(magnets, "deny_access", fake_deny_access)
    monkeypatch.setattr(magnets, "get_username", fake_get_username)
    monkeypatch.setattr(magnets, "get_client", fake_get_client)
    monkeypatch.setattr(magnets, "tg_send", fake_tg_send)

    update = DummyUpdate()
    context = DummyContext()

    await magnets.handle_magnet(update, context)

    assert "denied" not in calls
    assert client.magnets == ["magnet:?xt=urn:btih:abc"]
    assert update.message.replies == ["Magnet добавлен."]
    assert any("🧲 Magnet получен от @user1" in t for t in sent_notifications)


@pytest.mark.anyio
async def test_handle_magnet_error_from_transmission(monkeypatch):
    async def fake_deny_access(update):
        pass

    def fake_is_authorized(update):
        return True

    def fake_get_username(update):
        return "user1"

    class DummyClient:
        def add_torrent(self, magnet):
            raise RuntimeError("boom")

    def fake_get_client():
        return DummyClient()

    monkeypatch.setattr(magnets, "is_authorized", fake_is_authorized)
    monkeypatch.setattr(magnets, "deny_access", fake_deny_access)
    monkeypatch.setattr(magnets, "get_username", fake_get_username)
    monkeypatch.setattr(magnets, "get_client", fake_get_client)

    update = DummyUpdate()
    context = DummyContext()

    await magnets.handle_magnet(update, context)

    assert len(update.message.replies) == 1
    assert "Ошибка добавления magnet:" in update.message.replies[0]

