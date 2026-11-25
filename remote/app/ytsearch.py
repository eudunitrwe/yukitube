"""YouTube search without an API key: fetch the results page and read ytInitialData."""
import json
import re
import urllib.parse
import urllib.request

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0 Safari/537.36"
)
_START = re.compile(r"(?:var\s+ytInitialData|window\[\"ytInitialData\"\])\s*=\s*")


def _text(node):
    if not node:
        return ""
    if isinstance(node, str):
        return node
    if "simpleText" in node:
        return node["simpleText"]
    return "".join(r.get("text", "") for r in node.get("runs", []))


def _first(node, key):
    """The first value under `key` anywhere inside node."""
    if isinstance(node, dict):
        if key in node:
            return node[key]
        node = list(node.values())
    if isinstance(node, list):
        for v in node:
            r = _first(v, key)
            if r is not None:
                return r
    return None


def _lockup(lv):
    """A video in YouTube's newer layout (home feed, related videos)."""
    if lv.get("contentType") != "LOCKUP_CONTENT_TYPE_VIDEO" or not lv.get("contentId"):
        return None
    md = (lv.get("metadata") or {}).get("lockupMetadataViewModel") or {}
    rows = ((md.get("metadata") or {}).get("contentMetadataViewModel") or {}).get("metadataRows") or []
    parts = [[(p.get("text") or {}).get("content", "") for p in r.get("metadataParts") or []] for r in rows]
    badge = _first(lv.get("contentImage"), "thumbnailBadgeViewModel") or {}
    return {
        "id": lv["contentId"],
        "title": (md.get("title") or {}).get("content", ""),
        "channel": parts[0][0] if parts and parts[0] else "",
        "duration": badge.get("text", ""),
        "views": parts[1][0] if len(parts) > 1 and parts[1] else "",
    }


# Ads and Shorts are never offered.
_SKIP = ("adSlotRenderer", "promotedSparklesWebRenderer", "reelShelfRenderer", "richShelfRenderer",
         "shortsLockupViewModel", "reelItemRenderer")


def _walk(node, out, limit):
    if len(out) >= limit:
        return
    if isinstance(node, dict):
        vr = node.get("videoRenderer") or node.get("compactVideoRenderer")
        if isinstance(vr, dict) and vr.get("videoId"):
            out.append(
                {
                    "id": vr["videoId"],
                    "title": _text(vr.get("title")),
                    "channel": _text(vr.get("ownerText") or vr.get("longBylineText") or vr.get("shortBylineText")),
                    "duration": _text(vr.get("lengthText")) or ("LIVE" if vr.get("badges") else ""),
                    "views": _text(vr.get("shortViewCountText") or vr.get("viewCountText")),
                }
            )
            return
        lv = node.get("lockupViewModel")
        if isinstance(lv, dict):
            it = _lockup(lv)
            if it:
                out.append(it)
            return
        for k, v in node.items():
            if k not in _SKIP:
                _walk(v, out, limit)
    elif isinstance(node, list):
        for v in node:
            _walk(v, out, limit)


def initial_data(html):
    """The page's ytInitialData, as a dict."""
    m = _START.search(html)
    if not m:
        raise ValueError("ytInitialData not found")
    return json.JSONDecoder().raw_decode(html, m.end())[0]


def parse_videos(html, limit=25):
    """The videos on any YouTube page: results, the home feed, a watch
    page's related videos. Duplicates are left out."""
    out = []
    _walk(initial_data(html), out, limit * 2)
    seen, uniq = set(), []
    for it in out:
        if it["id"] not in seen:
            seen.add(it["id"])
            uniq.append(it)
    return uniq[:limit]


def parse_mix(html, limit=25):
    """The videos of the YouTube Mix on a watch page opened with
    list=RD<id>: the automatic playlist of songs like that one."""
    out = []

    def walk(n):
        if len(out) >= limit:
            return
        if isinstance(n, dict):
            pv = n.get("playlistPanelVideoRenderer")
            if isinstance(pv, dict) and pv.get("videoId"):
                out.append({
                    "id": pv["videoId"],
                    "title": _text(pv.get("title")),
                    "channel": _text(pv.get("shortBylineText") or pv.get("longBylineText")),
                    "duration": _text(pv.get("lengthText")),
                    "views": "",
                })
                return
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)

    walk(initial_data(html))
    return out


def parse_results(html, limit=25):
    out = []
    _walk(initial_data(html), out, limit)
    return out


def search(query, limit=25, timeout=10):
    url = "https://www.youtube.com/results?" + urllib.parse.urlencode(
        {"search_query": query, "hl": "en", "sp": "EgIQAQ%3D%3D"}, safe="%"
    )
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": _UA,
            "Accept-Language": "en-US,en;q=0.8",
            # skip the EU cookie consent interstitial
            "Cookie": "SOCS=CAI; CONSENT=YES+",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        html = r.read().decode("utf-8", "replace")
    return parse_results(html, limit)


if __name__ == "__main__":
    import sys

    for it in search(" ".join(sys.argv[1:]) or "synthwave"):
        print(it["id"], it["duration"], "|", it["title"], "|", it["channel"])
