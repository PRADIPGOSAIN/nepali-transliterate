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
from core.nepali_transl import NepaliTransliterator, get_transliterator

HERE = os.path.dirname(os.path.abspath(__file__))
TR = get_transliterator()


class Handler(BaseHTTPRequestHandler):
    server_version = "NepaliTransl/0.1"

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
                self._send(200, f.read())
        elif path == "/api/health":
            self._send(200, b'{"ok": true}', "application/json")
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
            if mode not in NepaliTransliterator.MODES + ("google",):
                mode = "roman"
            error = ""
            ours = ""
            if mode == "google":
                # Online Google backend + offline ours side-by-side.
                ours, _ = TR.transliterate_with_suggestions(text)
                try:
                    from core.google_backend import google_sentence
                    result = google_sentence(text)
                    if not result:
                        error = "Google returned no transliteration."
                        result = ours
                except Exception as e:
                    error = f"Google unreachable ({e}). Showing offline result."
                    result = ours
                suggestions = []
            elif mode != "roman":
                result, suggestions = TR.transliterate(text, mode=mode), []
            else:
                result, suggestions = TR.transliterate_with_suggestions(text)
            payload = json.dumps(
                {"result": result, "suggestions": suggestions, "mode": mode,
                 "ours": ours, "error": error},
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
