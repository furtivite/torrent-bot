from pathlib import Path

from opt.torrent_bot.handlers.documents import (
    MAX_PATH_DEPTH,
    MAX_PATH_LENGTH,
    MAX_TORRENT_FILES,
    MAX_TORRENT_TOTAL_SIZE_BYTES,
    inspect_torrent_layout_safety,
)


def test_inspect_torrent_layout_safety_ok_for_reasonable_layout():
    files = [
        (Path("dir/file1.bin"), 10),
        (Path("dir/sub/file2.bin"), 20),
    ]

    is_safe, reason = inspect_torrent_layout_safety("MyTorrent", files)
    assert is_safe is True
    assert reason == ""


def test_inspect_torrent_layout_safety_rejects_too_many_files():
    files = [(Path(f"f{i}"), 1) for i in range(MAX_TORRENT_FILES + 1)]
    is_safe, reason = inspect_torrent_layout_safety("Torrent", files)
    assert is_safe is False
    assert "слишком много файлов" in reason


def test_inspect_torrent_layout_safety_rejects_path_traversal():
    files = [(Path("../etc/passwd"), 1)]
    is_safe, reason = inspect_torrent_layout_safety("Torrent", files)
    assert is_safe is False
    assert "небезопасный путь" in reason


def test_inspect_torrent_layout_safety_rejects_too_long_path():
    long_component = "a" * (MAX_PATH_LENGTH + 1)
    files = [(Path(long_component), 1)]
    is_safe, reason = inspect_torrent_layout_safety("Torrent", files)
    assert is_safe is False
    assert "слишком длинный путь" in reason


def test_inspect_torrent_layout_safety_rejects_too_deep_path():
    deep_parts = [f"dir{i}" for i in range(MAX_PATH_DEPTH + 1)]
    files = [(Path(*deep_parts), 1)]
    is_safe, reason = inspect_torrent_layout_safety("Torrent", files)
    assert is_safe is False
    assert "слишком глубокая вложенность" in reason


def test_inspect_torrent_layout_safety_rejects_negative_size():
    files = [(Path("dir/file.bin"), -1)]
    is_safe, reason = inspect_torrent_layout_safety("Torrent", files)
    assert is_safe is False
    assert "отрицательный размер" in reason


def test_inspect_torrent_layout_safety_rejects_total_size_too_big():
    big_size = (MAX_TORRENT_TOTAL_SIZE_BYTES // 2) + 1
    files = [
        (Path("file1.bin"), big_size),
        (Path("file2.bin"), big_size),
    ]
    is_safe, reason = inspect_torrent_layout_safety("Torrent", files)
    assert is_safe is False
    assert "суммарный размер данных слишком большой" in reason

