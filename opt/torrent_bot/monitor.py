import asyncio
import logging
import time

from .config import CHECK_INTERVAL_SECONDS, STALL_MINUTES
from .state import (
    completed_reported,
    seen_torrents,
    stalled_since,
)
from . import state
from .transmission_client import get_client
from .utils.disk import disk_report, format_bytes
from .utils.notify import tg_send, tg_send_error

log = logging.getLogger("torrent-bot")


def torrent_state_label(t) -> str:
    status = getattr(t, "status", "")
    rate_download = getattr(t, "rate_download", 0) or 0

    if status == "downloading":
        if rate_download > 0:
            return "active_downloading"
        return "queued_or_waiting"

    if status in {"download pending", "check pending", "checking"}:
        return "queued_or_waiting"

    if status in {"stopped", "seeding", "seed pending"}:
        return status

    return str(status)


async def monitor_loop() -> None:
    await asyncio.sleep(5)

    while True:
        try:
            client = get_client()
            torrents = client.get_torrents(arguments=[
                "id",
                "name",
                "status",
                "rateDownload",
                "peersConnected",
                "percentDone",
                "eta",
                "isFinished",
            ])

            current_ids = set()

            for t in torrents:
                current_ids.add(t.id)
                prev = seen_torrents.get(t.id)
                state_label = torrent_state_label(t)

                if not state.initial_snapshot_done:
                    seen_torrents[t.id] = state_label
                    if bool(getattr(t, "is_finished", False)):
                        completed_reported.add(t.id)
                    continue

                if prev is None:
                    seen_torrents[t.id] = state_label
                    tg_send(
                        f"➕ Торрент добавлен: {t.name}\n"
                        f"Статус: {t.status}\n"
                        f"Прогресс: {round((t.percent_done or 0) * 100, 1)}%"
                    )
                else:
                    if prev != "active_downloading" and state_label == "active_downloading":
                        tg_send(
                            f"▶️ Скачивание началось: {t.name}\n"
                            f"Скорость: {format_bytes(t.rate_download or 0)}/s"
                        )

                    seen_torrents[t.id] = state_label

                is_finished = bool(getattr(t, "is_finished", False))
                if is_finished and t.id not in completed_reported:
                    completed_reported.add(t.id)
                    tg_send(
                        f"✅ Торрент скачан: {t.name}\n"
                        f"{disk_report()}"
                    )

                peers = getattr(t, "peers_connected", 0) or 0
                rate_download = getattr(t, "rate_download", 0) or 0
                is_downloading = str(getattr(t, "status", "")) == "downloading"
                is_incomplete = not bool(getattr(t, "is_finished", False))

                if is_downloading and is_incomplete and peers == 0 and rate_download == 0:
                    if t.id not in stalled_since:
                        stalled_since[t.id] = time.time()
                    else:
                        stalled_for = time.time() - stalled_since[t.id]
                        if stalled_for >= STALL_MINUTES * 60:
                            tg_send(
                                f"⚠️ Торрент завис без сидов/пиров: {t.name}\n"
                                f"Прогресс: {round((t.percent_done or 0) * 100, 1)}%\n"
                                f"Не качается уже {STALL_MINUTES}+ мин"
                            )
                            stalled_since.pop(t.id, None)
                else:
                    stalled_since.pop(t.id, None)

            removed_ids = set(seen_torrents.keys()) - current_ids
            for torrent_id in removed_ids:
                seen_torrents.pop(torrent_id, None)
                stalled_since.pop(torrent_id, None)
                completed_reported.discard(torrent_id)

            if not state.initial_snapshot_done:
                state.initial_snapshot_done = True

        except Exception as e:
            log.exception("Monitor loop failed: %s", e)
            tg_send_error(
                "monitor_loop_failed",
                "❌ Ошибка работы мониторинга torrent-bot. Подробнее смотри логи на сервере.",
            )

        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
