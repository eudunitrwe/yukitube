"""What the user plays often, kept on this computer, for recommendations
when no Google account is signed in (with one, YouTube's own home feed is
used: see the bridge's "recommend" action).

A video counts as played once it has played for PLAYED_AFTER seconds. The
seeds for recommendations are the videos played most, weighted towards
recent ones; their related videos (from the watch page) are the
recommendations.
"""
import json
import math
import time

PLAYED_AFTER = 30          # seconds of playing before a video counts
HALF_LIFE = 14 * 86400     # a play counts half after two weeks
KEEP = 300                 # videos remembered


class History:
    def __init__(self, settings):
        self.settings = settings
        try:
            self.items = json.loads(str(settings.value("history/plays", "") or "{}"))
        except ValueError:
            self.items = {}
        if not isinstance(self.items, dict):
            self.items = {}

    def _score(self, e, now):
        return e.get("plays", 0) * math.pow(0.5, max(0, now - e.get("last", now)) / HALF_LIFE)

    def add(self, vid, title="", channel=""):
        now = time.time()
        e = self.items.get(vid) or {"plays": 0}
        e["plays"] = e.get("plays", 0) + 1
        e["last"] = now
        if title:
            e["title"] = title
        if channel:
            e["channel"] = channel
        self.items[vid] = e
        if len(self.items) > KEEP:
            keep = sorted(self.items, key=lambda k: self._score(self.items[k], now), reverse=True)[:KEEP]
            self.items = {k: self.items[k] for k in keep}
        self.settings.setValue("history/plays", json.dumps(self.items, separators=(",", ":")))

    def seeds(self, n=3):
        now = time.time()
        return sorted(self.items, key=lambda k: self._score(self.items[k], now), reverse=True)[:n]

    def __len__(self):
        return len(self.items)


def merge(lists, exclude=(), limit=30):
    """Takes turns from each list (one per seed), so no single seed fills
    the strip; duplicates and the excluded ids are left out."""
    seen, out = set(exclude), []
    for i in range(max((len(x) for x in lists), default=0)):
        for lst in lists:
            if i < len(lst) and lst[i]["id"] not in seen:
                seen.add(lst[i]["id"])
                out.append(lst[i])
                if len(out) >= limit:
                    return out
    return out
