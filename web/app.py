"""Zero-dependency web server for Nepali transliteration.

Runs on Windows/Mac/Linux with only Python 3 stdlib.
Usage:  python3 web/app.py [--port 8000]
Then open http://localhost:8000 in a browser.
"""
import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core import __version__ as ENGINE_VERSION
from core.nepali_transl import NepaliTransliterator, get_transliterator

HERE = os.path.dirname(os.path.abspath(__file__))
TR = get_transliterator()

# In-memory Google suggestion cache (per server process, bounded).
_GCACHE = {}
_GCACHE_MAX = 500


def _google_suggest_word(word):
    """Google candidates for one romanized word; [] on any failure."""
    if not word:
        return []
    hit = _GCACHE.get(word)
    if hit is not None:
        return hit
    try:
        from core.google_backend import google_transliterate
        cands = google_transliterate(word, num=3).get(word, [])
    except Exception:
        cands = []
    if len(_GCACHE) >= _GCACHE_MAX:
        _GCACHE.pop(next(iter(_GCACHE)))
    _GCACHE[word] = cands
    return cands


def merge_suggestions(base, extra, limit=8):
    """Append Google candidates after ours, de-duplicated."""
    seen = set(base)
    merged = list(base)
    for c in extra:
        if c and c not in seen:
            seen.add(c)
            merged.append(c)
        if len(merged) >= limit:
            break
    return merged


class Handler(BaseHTTPRequestHandler):
    server_version = "NepaliTransl/" + ENGINE_VERSION

    def _send(self, code, body: bytes, ctype="text/html; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            with open(os.path.join(HERE, "index.html"), "rb") as f:
                page = f.read().replace(
                    b"__ENGINE_VERSION__",
                    ENGINE_VERSION.encode("ascii"))
            self._send(200, page)
        elif path == "/api/health":
            self._send(200, json.dumps(
                {"ok": True, "version": ENGINE_VERSION}).encode(),
                "application/json")
        elif path == "/api/layouts":
            from core.traditional import (TRAD_MAP, TRAD_KMN_MAP,
                                          LAYOUT_NAME, LAYOUT_KMN_NAME,
                                          LAYOUT_SOURCE, LAYOUT_KMN_SOURCE)
            from core.romanized_layout import (ROMANIZED_MAP, LAYOUT_NAME as
                                               ROM_LNAME, LAYOUT_SOURCE as
                                               ROM_SRC)
            payload = json.dumps({
                "rows": [
                    list("1234567890-="),
                    list("qwertyuiop[]\\"),
                    list("asdfghjkl;'"),
                    list("`zxcvbnm,./"),
                ],
                "shift_rows": [
                    list("!@#$%^&*()_+"),
                    list("QWERTYUIOP{}|"),
                    list('ASDFGHJKL:"'),
                    list("~ZXCVBNM<>?"),
                ],
                "layouts": {
                    "traditional": {"name": LAYOUT_NAME,
                                    "source": LAYOUT_SOURCE,
                                    "map": TRAD_MAP},
                    "traditional-kmn": {"name": LAYOUT_KMN_NAME,
                                         "source": LAYOUT_KMN_SOURCE,
                                         "map": TRAD_KMN_MAP},
                    "romanized": {"name": ROM_LNAME,
                                   "source": ROM_SRC,
                                   "map": ROMANIZED_MAP},
                },
            }, ensure_ascii=False).encode("utf-8")
            self._send(200, payload, "application/json; charset=utf-8")
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/learn":
            # Remember a user's explicit choice locally (never leaves disk).
            length = int(self.headers.get("Content-Length", 0))
            try:
                data = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                data = {}
            roman = data.get("roman", "")
            devanagari = data.get("devanagari", "")
            if not isinstance(roman, str):
                roman = ""
            if not isinstance(devanagari, str):
                devanagari = ""
            ok = TR.learn(roman, devanagari)
            self._send(200, json.dumps({"ok": ok}).encode(),
                       "application/json")
            return
        if path == "/api/transliterate":
            length = int(self.headers.get("Content-Length", 0))
            try:
                data = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                data = {}
            text = data.get("text", "")
            if not isinstance(text, str):
                text = ""
            mode = data.get("mode", "roman")
            if mode not in NepaliTransliterator.MODES:
                mode = "roman"
            want_google = bool(data.get("google_suggest"))
            if mode != "roman":
                result, suggestions, forms = TR.transliterate(text, mode=mode), [], []
            else:
                result, suggestions = TR.transliterate_with_suggestions(text)
                if want_google:
                    # Google candidates MERGED into suggestions (opt-in,
                    # cached); failures stay silent, offline first.
                    words = text.split()
                    last = words[-1] if words else ""
                    suggestions = merge_suggestions(
                        suggestions, _google_suggest_word(last))
                # Ranked Devanagari forms for the last word:
                # [user-learned, hand, auto, phonetic] with sources.
                words = text.split()
                last = words[-1] if words else ""
                forms = [{"form": f, "source": s, "roman": last}
                         for f, s in TR.candidates(last)[:5]] if last else []
            payload = json.dumps(
                {"result": result, "suggestions": suggestions, "mode": mode,
                 "forms": forms},
                ensure_ascii=False,
            ).encode("utf-8")
            self._send(200, payload, "application/json; charset=utf-8")
        else:
            self._send(404, b"not found", "text/plain")

    def log_message(self, fmt, *args):
        sys.stderr.write("  %s\n" % (fmt % args))


def main():
    ap = argparse.ArgumentParser(description="Nepali transliteration web server")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()
    srv = HTTPServer((args.host, args.port), Handler)
    print(f"Nepali Transliterate running at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
