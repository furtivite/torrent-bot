from types import SimpleNamespace

from telegram import InlineKeyboardMarkup

from opt.torrent_bot.handlers.commands import (
    TORRENTS_PAGE_SIZE,
    build_torrents_page_keyboard,
    build_torrents_page_text,
)


class DummyTorrent:
    def __init__(
        self,
        name: str,
        status: str = "downloading",
        percent_done: float = 0.5,
        rate_download: int = 1024,
        eta: int | None = 60,
        is_finished: bool = False,
    ):
        self.name = name
        self.status = status
        self.percent_done = percent_done
        self.rate_download = rate_download
        self.eta = eta
        self.is_finished = is_finished


def test_build_torrents_page_text_empty():
    assert build_torrents_page_text([], 0) == "Торрентов нет."


def test_build_torrents_page_text_single():
    torrents = [DummyTorrent("Ubuntu ISO", percent_done=1.0, rate_download=0, eta=None, is_finished=True)]
    text = build_torrents_page_text(torrents, 0)
    assert "Торренты 1-1 из 1" in text
    assert "Ubuntu ISO" in text
    assert "готово" in text


def test_build_torrents_page_text_multiple_pages():
    torrents = [DummyTorrent(f"Torrent {i}") for i in range(TORRENTS_PAGE_SIZE + 5)]

    first_page = build_torrents_page_text(torrents, 0)
    assert f"Торренты 1-{TORRENTS_PAGE_SIZE} из {TORRENTS_PAGE_SIZE + 5}" in first_page

    second_page = build_torrents_page_text(torrents, TORRENTS_PAGE_SIZE)
    assert f"Торренты {TORRENTS_PAGE_SIZE + 1}-{TORRENTS_PAGE_SIZE + 5} из {TORRENTS_PAGE_SIZE + 5}" in second_page


def test_build_torrents_page_keyboard_no_buttons_when_single_page():
    total = 5
    kb = build_torrents_page_keyboard(total, 0)
    assert kb is None


def test_build_torrents_page_keyboard_prev_next():
    total = TORRENTS_PAGE_SIZE * 2
    kb_middle = build_torrents_page_keyboard(total, TORRENTS_PAGE_SIZE)
    assert isinstance(kb_middle, InlineKeyboardMarkup)
    buttons = kb_middle.inline_keyboard[0]
    labels = {btn.text for btn in buttons}
    assert "⬅️ Назад" in labels
    assert "➡️ Ещё" in labels

