from types import SimpleNamespace

from opt.torrent_bot.monitor import torrent_state_label


def make_torrent(status: str, rate_download: int | None = 0):
    return SimpleNamespace(status=status, rate_download=rate_download)


def test_torrent_state_label_downloading_active():
    t = make_torrent("downloading", rate_download=1024)
    assert torrent_state_label(t) == "active_downloading"


def test_torrent_state_label_downloading_queued():
    t = make_torrent("downloading", rate_download=0)
    assert torrent_state_label(t) == "queued_or_waiting"


def test_torrent_state_label_pending_states():
    for st in ["download pending", "check pending", "checking"]:
        assert torrent_state_label(make_torrent(st)) == "queued_or_waiting"


def test_torrent_state_label_simple_passthrough():
    for st in ["stopped", "seeding", "seed pending"]:
        assert torrent_state_label(make_torrent(st)) == st


def test_torrent_state_label_unknown_status():
    t = make_torrent("weird-status")
    assert torrent_state_label(t) == "weird-status"

