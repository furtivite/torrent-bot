import shutil

from config import DATA_ROOT


def format_bytes(size: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size)

    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}"
        value /= 1024

    return f"{size} B"


def disk_report(path: str | bytes | None = None) -> str:
    """
    Отчёт по диску. По умолчанию использует DATA_ROOT из конфигурации.
    """
    target = DATA_ROOT if path is None else path
    usage = shutil.disk_usage(target)

    used = format_bytes(usage.used)
    free = format_bytes(usage.free)
    total = format_bytes(usage.total)

    return f"Диск {target}: занято {used}, свободно {free}, всего {total}"
