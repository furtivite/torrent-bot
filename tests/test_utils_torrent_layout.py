from pathlib import Path

import bencodepy

from opt.torrent_bot.utils.torrent_layout import (
    read_torrent_layout,
    torrent_already_downloaded,
)


def make_single_file_torrent(path: Path, name: str, size: int):
    meta = {
        b"info": {
            b"name": name.encode(),
            b"length": size,
        }
    }
    path.write_bytes(bencodepy.encode(meta))


def make_multi_file_torrent(path: Path, name: str, files: list[tuple[str, int]]):
    meta_files = []
    for rel, length in files:
        meta_files.append(
            {
                b"path": [p.encode() for p in Path(rel).parts],
                b"length": length,
            }
        )

    meta = {
        b"info": {
            b"name": name.encode(),
            b"files": meta_files,
        }
    }
    path.write_bytes(bencodepy.encode(meta))


def test_read_torrent_layout_single_file(tmp_path):
    torrent_path = tmp_path / "single.torrent"
    make_single_file_torrent(torrent_path, "movie.mkv", 1234)

    name, files = read_torrent_layout(torrent_path)
    assert name == "movie.mkv"
    assert files == [(Path("movie.mkv"), 1234)]


def test_read_torrent_layout_multi_file(tmp_path):
    torrent_path = tmp_path / "multi.torrent"
    make_multi_file_torrent(
        torrent_path,
        "MyTorrent",
        [
            ("Season1/ep1.mkv", 10),
            ("Season1/ep2.mkv", 20),
        ],
    )

    name, files = read_torrent_layout(torrent_path)
    assert name == "MyTorrent"
    assert (Path("MyTorrent") / "Season1" / "ep1.mkv", 10) in files
    assert (Path("MyTorrent") / "Season1" / "ep2.mkv", 20) in files


def test_torrent_already_downloaded_single_file(tmp_path):
    torrent_path = tmp_path / "single.torrent"
    make_single_file_torrent(torrent_path, "file.bin", 5)

    downloaded_dir = tmp_path / "downloaded"
    downloaded_dir.mkdir()

    target = downloaded_dir / "file.bin"
    target.write_bytes(b"x" * 5)

    exists, name = torrent_already_downloaded(torrent_path, downloaded_dir)
    assert exists is True
    assert name == "file.bin"


def test_torrent_already_downloaded_multi_file(tmp_path):
    torrent_path = tmp_path / "multi.torrent"
    make_multi_file_torrent(
        torrent_path,
        "MyTorrent",
        [
            ("Season1/ep1.mkv", 3),
            ("Season1/ep2.mkv", 4),
        ],
    )

    downloaded_dir = tmp_path / "downloaded"
    # создаём папку корня multi‑file торрента
    root = downloaded_dir / "MyTorrent"
    root.mkdir(parents=True)
    (root / "Season1").mkdir(exist_ok=True)

    (root / "Season1" / "ep1.mkv").write_bytes(b"a" * 3)
    (root / "Season1" / "ep2.mkv").write_bytes(b"b" * 4)

    exists, name = torrent_already_downloaded(torrent_path, downloaded_dir)
    assert exists is True
    assert name == "MyTorrent"

