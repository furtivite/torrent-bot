from types import SimpleNamespace

from opt.torrent_bot.utils import auth


def make_update(username: str | None):
    user = SimpleNamespace(username=username)
    return SimpleNamespace(effective_user=user)


def test_is_authorized_true_when_in_whitelist(monkeypatch):
    monkeypatch.setattr(auth, "ALLOWED_USERNAMES", {"user1", "user2"})
    update = make_update("user1")
    assert auth.is_authorized(update) is True


def test_is_authorized_false_when_not_in_whitelist(monkeypatch):
    monkeypatch.setattr(auth, "ALLOWED_USERNAMES", {"user1", "user2"})
    update = make_update("other")
    assert auth.is_authorized(update) is False


def test_get_username_handles_missing_username():
    update = make_update(None)
    assert auth.get_username(update) == ""

