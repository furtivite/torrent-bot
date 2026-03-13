import types

import pytest

from opt.torrent_bot.utils.disk import disk_report, format_bytes


def test_format_bytes_basic():
    assert format_bytes(0) == "0.0 B"
    assert format_bytes(1023) == "1023.0 B"
    assert format_bytes(1024) == "1.0 KB"
    assert format_bytes(1024 * 1024) == "1.0 MB"


def test_disk_report_uses_custom_path_when_provided(monkeypatch, tmp_path):
    fake_path = tmp_path

    def fake_disk_usage(path):
        # возвращаем объект с полями как у shutil.disk_usage
        return types.SimpleNamespace(total=1000, used=400, free=600)

    monkeypatch.setattr("opt.torrent_bot.utils.disk.shutil.disk_usage", fake_disk_usage)

    text = disk_report(str(fake_path))
    assert "Диск" in text
    assert "занято 400.0 B" in text
    assert "свободно 600.0 B" in text
    assert "всего 1.0 KB" in text

