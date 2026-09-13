"""Google Input Tools backend (optional, online-only) + benchmark/mining tools.

THE SOURCE ITSELF is proprietary — Google never open-sourced Input Tools.
What IS publicly reachable is the transliteration API endpoint that the
Chrome extension / web tools call:

    https://inputtools.google.com/request?text=<text>&itc=ne-t-i0-und&num=<n>

This module wraps it for two legitimate local uses:
  1. Live backend comparison: `google_transliterate()` lets you check what
     Google returns for a word (needs internet).
  2. QA benchmark: compare OUR engine against Google's top candidate and
     review disagreements by hand (tools/google_bench.py).

Fair-use note: hammering Google's endpoint to clone its dictionary likely
violates Google's ToS. This tool queries gently (batched, cached, small
samples) for evaluation. Anything that ends up in OUR dictionary must be
human-reviewed first — see tools/google_bench.py review output.
"""
import json
import time
import urllib.parse
import urllib.request
from typing import Dict, List

API_URL = "https://inputtools.google.com/request"
ITC_NEPALI = "ne-t-i0-und"


def google_transliterate(text: str, num: int = 5,
                         timeout: int = 15) -> Dict[str, List[str]]:
    """Return {token: [candidates...]} from Google Input Tools API.

    Raises URLError on network failure. Empty dict for empty input.
    """
    if not text or not text.strip():
        return {}
    params = urllib.parse.urlencode(
        {"text": text, "itc": ITC_NEPALI, "num": num})
    req = urllib.request.Request(
        f"{API_URL}?{params}",
        headers={"User-Agent": "nepali-transl-qa/0.3"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    if not payload or payload[0] != "SUCCESS":
        raise RuntimeError(f"Google API error: {payload!r:.200}")
    out = {}
    for entry in payload[1]:
        token, cands = entry[0], entry[1]
        out[token] = cands
    return out


def google_top(text: str) -> str:
    """Single best Google transliteration for a word ("" if none)."""
    res = google_transliterate(text, num=1)
    cands = res.get(text, [])
    return cands[0] if cands else ""


if __name__ == "__main__":
    import sys
    for word in sys.argv[1:] or ["namaste", "kathmandu"]:
        cands = google_transliterate(word).get(word, [])
        print(f"{word:15} -> {cands[0] if cands else '?'}  (alts: {cands[1:3]})")
        time.sleep(0.2)
