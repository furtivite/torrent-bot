from pathlib import Path

from opt.torrent_bot.utils.torrent_files import is_valid_torrent_file


def test_is_valid_torrent_file_true_for_bencoded_start(tmp_path):
    path = tmp_path / "ok.torrent"
    # bencoded torrent обычно начинается с 'd'
    path.write_bytes(b"d3:foo3:bar")

    assert is_valid_torrent_file(path) is True


def test_is_valid_torrent_file_false_for_non_torrent(tmp_path):
    path = tmp_path / "not.torrent"
    path.write_text("not a torrent")

    assert is_valid_torrent_file(path) is False

