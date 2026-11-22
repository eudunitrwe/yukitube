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


def _walk(node, out, limit):
    if len(out) >= limit:
        return
    if isinstance(node, dict):
        vr = node.get("videoRenderer")
        if isinstance(vr, dict) and vr.get("videoId"):
            out.append(
                {
                    "id": vr["videoId"],
                    "title": _text(vr.get("title")),
                    "channel": _text(vr.get("ownerText") or vr.get("longBylineText")),
                    "duration": _text(vr.get("lengthText")) or ("LIVE" if vr.get("badges") else ""),
                    "views": _text(vr.get("shortViewCountText") or vr.get("viewCountText")),
                }
            )
            return
        for v in node.values():
            _walk(v, out, limit)
    elif isinstance(node, list):
        for v in node:
            _walk(v, out, limit)


def parse_results(html, limit=25):
    m = _START.search(html)
    if not m:
        raise ValueError("ytInitialData not found")
    data, _ = json.JSONDecoder().raw_decode(html, m.end())
    out = []
    _walk(data, out, limit)
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
