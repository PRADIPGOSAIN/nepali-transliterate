"""Command-line interface: transliterate stdin/files to Nepali Unicode.

Usage:
  python3 -m core.cli "namaste kasto chha"
  echo "namaste" | python3 -m core.cli
  python3 -m core.cli input.txt -o output.txt
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.nepali_transl import get_transliterator


def main(argv=None):
    ap = argparse.ArgumentParser(description="Romanized Nepali -> Unicode Devanagari")
    ap.add_argument("text", nargs="?", help="Text to transliterate (else stdin)")
    ap.add_argument("-o", "--output", help="Write output to file")
    ap.add_argument("--layout", default="roman",
                    choices=("roman", "traditional", "traditional-kmn",
                             "romanized"),
                    help="roman: phonetic transliteration (default); "
                         "traditional: MPP Traditional keys; "
                         "traditional-kmn: revised Traditional (Keyman v1.3.1); "
                         "romanized: MPP Romanized direct keys")
    ap.add_argument("--preeti", action="store_true",
                    help="Convert legacy Preeti encoding instead "
                         "(needs: pip install preeti-unicode-converter)")
    ap.add_argument("--google", action="store_true",
                    help="Use Google Input Tools API instead of the offline "
                         "engine (needs internet; roman text only)")
    ap.add_argument("--cands", metavar="WORD",
                    help="List ranked Devanagari candidates for one word "
                         "with their sources (user/hand/auto/phonetic)")
    ap.add_argument("--learn", nargs=2, metavar=("ROMAN", "DEVANAGARI"),
                    help="Remember ROMAN->DEVANAGARI locally (user lexicon)")
    args = ap.parse_args(argv)

    tr = get_transliterator()
    if args.learn:
        ok = tr.learn(args.learn[0], args.learn[1])
        print("remembered" if ok else "not stored (check inputs)")
        return 0 if ok else 1
    if args.cands:
        for form, source in tr.candidates(args.cands):
            print(f"{form}\t({source})")
        return 0

    if args.text is not None:
        source = args.text
    elif not sys.stdin.isatty():
        source = sys.stdin.read()
    else:
        ap.print_help()
        return 1

    if args.preeti:
        from core.preeti_bridge import preeti_to_unicode
        result = preeti_to_unicode(source)
    elif args.google:
        if args.layout != "roman":
            print("note: --google uses roman transliteration; "
                  "--layout ignored.", file=sys.stderr)
        from core.google_backend import google_sentence
        try:
            result = google_sentence(source)
        except Exception as e:
            print(f"error: Google Input Tools unreachable ({e}); "
                  f"check internet or drop --google for offline mode.",
                  file=sys.stderr)
            return 2
        if not result:
            print("error: Google returned no transliteration.",
                  file=sys.stderr)
            return 2
    else:
        result = get_transliterator().transliterate(source, mode=args.layout)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)
    else:
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
