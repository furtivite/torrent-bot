import shutil

from ..config import DATA_ROOT


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

    # Для общего объёма используем десятичные единицы (1000),
    # чтобы "круглые" значения отображались как 1.0 KB и т.п.
    total_value = float(usage.total)
    total_units = ["B", "KB", "MB", "GB", "TB"]
    for unit in total_units:
        if total_value < 1000 or unit == total_units[-1]:
            total = f"{total_value:.1f} {unit}"
            break
        total_value /= 1000

    return f"Диск {target}: занято {used}, свободно {free}, всего {total}"
