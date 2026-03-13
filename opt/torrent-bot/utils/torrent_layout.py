from pathlib import Path

import bencodepy


def _decode(value):
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, list):
        return [_decode(v) for v in value]
    if isinstance(value, dict):
        return {_decode(k): _decode(v) for k, v in value.items()}
    return value


def read_torrent_layout(torrent_path: Path):
    raw = torrent_path.read_bytes()
    meta = bencodepy.decode(raw)
    meta = _decode(meta)

    info = meta["info"]
    torrent_name = info["name"]

    files = []

    # multi-file torrent
    if "files" in info:
        for item in info["files"]:
            rel_parts = item["path"]
            rel_path = Path(torrent_name).joinpath(*rel_parts)
            length = int(item["length"])
            files.append((rel_path, length))
    else:
        # single-file torrent
        rel_path = Path(torrent_name)
        length = int(info["length"])
        files.append((rel_path, length))

    return torrent_name, files


def torrent_already_downloaded(torrent_path: Path, downloaded_dir: Path):
    torrent_name, files = read_torrent_layout(torrent_path)

    # Для multi-file торрента проверяем наличие корневой папки
    root_path = downloaded_dir / torrent_name

    # Если single-file torrent, root_path — это файл.
    # Для multi-file root_path должен быть каталог.
    if len(files) > 1 and not root_path.is_dir():
        return False, torrent_name

    if len(files) == 1:
        single_target = downloaded_dir / files[0][0]
        if not single_target.exists():
            return False, torrent_name

    for rel_path, expected_size in files:
        full_path = downloaded_dir / rel_path
        if not full_path.exists():
            return False, torrent_name
        if full_path.is_file():
            actual_size = full_path.stat().st_size
            if actual_size != expected_size:
                return False, torrent_name

    return True, torrent_name
