seen_torrents = {}
stalled_since = {}
stalled_notified = set()  # id торрентов, по которым уже отправили уведомление о зависании (сбрасывается при появлении пиров/скорости)
initial_snapshot_done = False
completed_reported = set()
