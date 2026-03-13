from pathlib import Path


def is_valid_torrent_file(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            data = f.read(32)

        # bencoded torrent начинается с 'd'
        return data.startswith(b"d")

    except Exception:
        return False
