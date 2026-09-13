# नेपाली Transliterate (`nepali-transl`)

Modern successor to [`ne-rom-translit`](https://github.com/sapradhan/ne-rom-translit)
(m17n `.mim`, 2013). Same phonetic mapping you already use
(`k`→क, `kh`→ख, `ksh`→क्ष, `tr`→त्र …), plus:

- **Dictionary autocorrect (~6,250 words: ~150 hand + 6,102 imported)** —
  `kathmandu`→काठमाडौं,
  `bhairahechha`→भइरहेछ, `namaskar`→नमस्कार … imported from
  real human romanizations
  ([Saugatkafley/Nepali-Roman-Transliteration](https://huggingface.co/datasets/Saugatkafley/Nepali-Roman-Transliteration),
  MIT), keeping only pairs the phonetic engine can't derive.
  Measured coverage: **99.5% on 6,905 real typed pairs**.
- **Word suggestions** while typing (shortest-first ranked)
- **Zero-dependency** — pure Python 3 stdlib (no pip needed)
- **Cross-platform** — Windows 10/11, macOS, Linux, web

## Quick start (any OS)

```bash
git clone https://github.com/PRADIPGOSAIN/nepali-transliterate.git
cd nepali-transliterate

# 1. CLI — four modes
python3 -m core.cli "namaste kasto chha"
# -> नमस्ते कस्तो छ  (roman: phonetic transliteration)
python3 -m core.cli --layout traditional "gfdLGL"
# -> नामीद्दी  (traditional MPP keys: g=न f=ा d=म L=ी G=द्द)
python3 -m core.cli --layout traditional-kmn "S"
# -> क्  (revised Traditional: explicit half-forms, Keyman v1.3.1)
python3 -m core.cli --layout romanized "kA"
# -> कआ  (MPP Romanized direct keys: k=क A=आ)

# Legacy Preeti documents -> Unicode (optional extra)
pip install "nepali-transl[preeti]"
python3 -m core.cli --preeti "g]kfn"
# -> नेपाल

# 2. Desktop app (double-click friendly on Windows)
python3 desktop/app.py

# 3. Web typing tool
python3 web/app.py
# open http://127.0.0.1:8000
```

## Install on any distro / OS

**You need:** Python 3.8+ (check: `python3 --version`).
CLI + web app need *only* that. The desktop app additionally needs Tk:

| Distro | Python + Tk in one line |
|---|---|
| Arch / Manjaro / EndeavourOS | `sudo pacman -S python tk` |
| Debian / Ubuntu / Mint / Pop!_OS | `sudo apt install python3 python3-tk` |
| Fedora / RHEL / Rocky | `sudo dnf install python3 python3-tkinter` |
| openSUSE | `sudo zypper install python3 python3-tk` |

Then on **any** of them:

```bash
git clone https://github.com/PRADIPGOSAIN/nepali-transliterate.git
cd nepali-transliterate
python3 -m core.cli "namaste kasto chha"  # CLI, works everywhere
python3 web/app.py                        # web typing + visual keyboard
python3 desktop/app.py                    # desktop app (needs Tk line above)
```

**System-wide typing on Linux** (type directly into any app, any distro):

```bash
# Arch
sudo pacman -S fcitx5-im fcitx5-m17n m17n-db
# Debian/Ubuntu/Mint
sudo apt install fcitx5 fcitx5-m17n m17n-db
# Fedora
sudo dnf install fcitx5 fcitx5-m17n m17n-db
# openSUSE
sudo zypper install fcitx5 fcitx5-m17n m17n-db
```

Then open `fcitx5-configtool` → Input Method → **+** → uncheck
“Only Show Current Language” → add `m17n_ne_rom-translit`
(same keystrokes as this project's roman mode). Log out/in once.
Alternative framework: `ibus` + `ibus-m17n` (same method name).

## Windows 10/11 for friends (easiest)

1. Install Python 3 from python.org (tick **“Add python to PATH”**).
2. Download this repo as ZIP (green **Code** button → Download ZIP), extract.
3. Double-click `desktop/app.py` — or run `python desktop/app.py`.
4. Pick a layout (Translit / Traditional / Trad-rev / Romanized),
   type on the left, copy Unicode from the right.

No admin rights, no keyboard-layout install, no reboot needed.
For system-wide typing (directly into Word etc.), build the Keyman
`.kmp` as described above — same keystrokes everywhere.

## macOS

```bash
brew install python tk   # or install python.org macOS package (Tk included)
git clone https://github.com/PRADIPGOSAIN/nepali-transliterate.git
cd nepali-transliterate && python3 desktop/app.py
```

## Typing reference (roman mode)

| Roman | Nepali | Roman | Nepali |
|---|---|---|---|
| aa | आ | kh | ख |
| ii/ee | ई | chh | छ |
| uu/oo | ऊ | ksh | क्ष |
| e/ai/o/au | ए/ऐ/ओ/औ | tr | त्र |
| T/Th/D/Dh | ट/ठ/ड/ढ | gyn/jn | ज्ञ |
| sh/Sh/s | श/ष/स | ng | ङ |
| . | । | 0-9 | ०-९ |

Long vowels: double them (`kaa`→का, `saano`→सानो).
Retroflex alternative: `t/`→ट, `th/`→ठ, `d/`→ड, `dh/`→ढ, `n/`→ण.
Full stop: `.`→।, `..`→॥. Avagraha: `~a`→ऽ.
Word-start `om`/`aum` → ॐ.

## Learn like a pro (Traditional layout)

Open the web tool (`python3 web/app.py`) — it has an interactive
**visual keyboard**: all three direct layouts, Shift layer toggle,
click-to-type, and keys that light up as you press your real keyboard.

5-lesson path (also shown in the app):

1. **Home row** — left `a s d f` → ब क म ा, right `j k l ;` → व प ि स.
   Drills: `n f d` → लाम, `k d` → पम, `h f g f d` → जानाम.
2. **Vowels** — `f`→ा `l`→ि `'`→ु `"`→ू `]`→े `c`→अ `A`→आ.
3. **Shift layer** — capitals give compounds: `Q`→त्त `T`→ट्ट
   `I`→क्ष `!`→ज्ञ `$`→द्ध.
4. **Conjuncts** — `\` is halant ् (`k \ q` → क्त), `[` is repha र्.
5. **Words** — `gfdLGL` → नामीद्दी. Then graduate to roman mode:
   `namaste` → नमस्ते. Type daily sentences for a week — that is the
   whole secret: short daily practice beats weekend marathons.

## System-wide typing (type directly into any app)

**Linux (fcitx5/ibus, system-wide):** install `fcitx5-m17n` + `m17n-db`
(Arch: `pacman -S fcitx5-m17n m17n-db`), then enable
`m17n_ne_rom-translit` in fcitx5-config — same mapping as this engine.

**Windows / macOS / Android / iOS (system-wide):** build the Keyman keyboard:

```bash
python3 keyman/gen_kmn.py          # regenerates keyman/nepali_translit.kmn
```

Then open `keyman/nepali_translit.kmn` in
[Keyman Developer](https://keyman.com/developer) (free, open source),
build the `.kmp` package, and install it — double-click on Windows.
Same keystrokes as the Linux setup, in every application.

## Layout

```
core/nepali_transl.py  engine (state machine ported from ne-rom-translit.mim)
core/dictionary.py     hand-curated corrections (always win)
core/words_auto.py     6,100+ imported corrections (regenerate: tools/import_pairs.py)
core/preeti_bridge.py  optional Preeti->Unicode bridge (needs pip extra)
core/cli.py            CLI entry point (incl. --preeti mode)
keyman/gen_kmn.py      generates keyman/nepali_translit.kmn (Win/Mac/mobile)
tests/                 test suite (python3 tests/test_transliterate.py)
web/                   offline web typing tool (stdlib http.server)
desktop/               tkinter desktop app (stdlib, Windows-friendly)
tasks/plan.md          implementation plan
```

## Tests

```bash
python3 tests/test_transliterate.py   # 20 tests, stdlib only
python3 tests/test_traditional.py     # 7 tests (incl. 94/94 parity with m17n)
python3 tests/test_layouts.py         # 6 tests (parity with Keyman sources)
# (Preeti + Google tests auto-skip when their optional backends are absent)
```

## Four input modes, one independent offline tool

| Mode | You type | You get | For whom |
|---|---|---|---|
| **roman** (default) | `namaste` (phonetics) | नमस्ते | English-keyboard users |
| **traditional** | `gfdLGL` (MPP Traditional keys) | नामीद्दी | classic Traditional typists |
| **traditional-kmn** | `S` (revised Traditional) | क् (classic: ङ्क) | Keyman v1.3.1 users |
| **romanized** | `kA` (MPP Romanized keys) | कआ | Windows Romanized-layout users |

- `traditional` = MPP classic (`k`→प, `f`→ा, `q`→त्र, `[`→र्), ported 1:1
  from m17n `ne-trad.mim` — **94/94 machine-verified** (`test_parity_with_mim`).
- `traditional-kmn` + `romanized` = your Keyman v1.3.1/v1.0.1 tables,
  **machine-verified** against vendored sources (`tools/reference/*.kmn`).
  Known source difference documented in code: `\\` key (kmn ॐ/ः vs
  Windows-MSKLC literal `\`/`|` which keeps ॐ/ः on the ISO key).
- Word-start `om`/`aum` → ॐ (`sombar` still → सोमबार).
- No network in any mode — enforced by `test_no_network_imports_in_core`
  (only the explicit Google module may use the network).


## Regenerating the dictionary

```bash
# fetch pair files, then:
python3 tools/import_pairs.py nep_valid.json nep_test.json
# -> rewrites core/words_auto.py (hand entries in dictionary.py untouched)
```

## Benchmarking against Google Input Tools

Google's source is proprietary, but its transliteration API endpoint is
publicly reachable, so we measure against it (online-only, gentle + cached):

```bash
python3 tools/google_bench.py --limit 200   # hand-dict words
python3 tools/google_bench.py --from-auto 500
# -> tools/google_review.tsv : disagreements for HUMAN review only.
#    Nothing is imported automatically.
```

Last measured (118 hand words): **83 exact top-1 matches (70%)**;
of the 35 disagreements, **our form is in Google's top-5 in 23 cases**.
The remaining divergences are mostly ours-wins on standard spelling
(`didi`→दिदी not दिदि, `kahaa`→कहाँ not कहा, `birgunj`→वीरगञ्ज).
Our edge: **standard-spelling-first ranking**; Google ranks literal
phonetics first. Cache/review files are gitignored, not shipped.


## Migrating legacy Preeti documents

Preeti was the pre-Unicode Nepali font; old files render as ASCII gibberish
without it. Convert them losslessly:

```bash
pip install "nepali-transl[preeti]"
python3 -m core.cli --preeti "g]kfn"   # -> नेपाल
```

The table itself is not vendored (upstream is CC-BY-NC-SA, incompatible with
GPL); the MIT `preeti-unicode-converter` package is the backend. `detect_preeti()`
heuristically spots Preeti text for file-picker UIs.


## License

GPL-2.0-or-later (same lineage as the original m17n contribution).
