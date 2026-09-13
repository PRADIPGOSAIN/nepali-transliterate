# नेपाली Transliterate

![License: GPL-2.0-or-later](https://img.shields.io/badge/License-GPL--2.0--or--later-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![Tests](https://img.shields.io/badge/tests-39%20passing-brightgreen.svg)
![No dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)

**Offline Nepali typing toolkit with roman transliteration, traditional
keyboard layouts, and Linux system-wide input support.** By **Pradip Gosain**.

Phonetic transliteration (`namaste` → नमस्ते), three direct keyboard
layouts, a visual keyboard for learning, desktop + web apps, a 6,220-word
dictionary, candidate ranking with personal learning, Keyman sources,
and a Preeti rescue bridge.

No accounts. No cloud. No tracking. Your keystrokes never leave your
machine. Windows/macOS/mobile system-wide input: in development
(see [Platform support](SUPPORT.md)).

## Contents

- [Run it in 60 seconds](#run-it-in-60-seconds)
- [Install (any distro, Windows, macOS)](#install)
- [Four input modes](#four-input-modes)
- [Typing reference](#typing-reference)
- [Learn like a pro](#learn-like-a-pro)
- [System-wide typing](#system-wide-typing)
- [Dictionary & data](#dictionary--data)
- [Google Input Tools — integrated](#google-input-tools--integrated)
- [Preeti rescue](#preeti-rescue)
- [Project layout & tests](#project-layout--tests)
- [License](#license)
- [Platform support](SUPPORT.md)

## Run it in 60 seconds

```bash
git clone https://github.com/PRADIPGOSAIN/nepali-transliterate.git
cd nepali-transliterate

python3 -m core.cli "mero nam pradip gosai ho"
# मेरो नाम प्रदिप गोसाई हो

python3 web/app.py        # typing tool + visual keyboard → http://127.0.0.1:8000
python3 desktop/app.py    # desktop app (needs Tk, see Install)
```

> **Want Nepali to appear while you type?** Tick **⌨️ Typewriter**
> in the web tool (or desktop app): type `gosai`, see
> `gosai → गोसाई` live under the box, hit **space** and the word
> converts in place. **Backspace** right after converts it back to
> roman so you can fix it. Wrong word? The one-click suggestions fix it.

Requirements: Python 3.8+. CLI and web app need nothing else —
no `pip install`, no virtualenv, no internet.

## Install

### Linux — any distro

| Distro | Command |
|---|---|
| Arch / Manjaro / EndeavourOS | `sudo pacman -S python tk` |
| Debian / Ubuntu / Mint / Pop!_OS | `sudo apt install python3 python3-tk` |
| Fedora / RHEL / Rocky | `sudo dnf install python3 python3-tkinter` |
| openSUSE | `sudo zypper install python3 python3-tk` |

(`tk` is only needed for the desktop app; CLI and web run on Python alone.
Verify with `python3 --version`.)

### Windows 10 / 11

1. Install Python 3 from [python.org](https://www.python.org/downloads/)
   (tick **Add python.exe to PATH**).
2. Download this repo (green **Code** button → **Download ZIP**), extract it.
3. Open a terminal in the folder and run `python desktop\app.py`
   (or `python -m core.cli "namaste"`).

No admin rights, no reboot, no keyboard-layout install.

### macOS

```bash
brew install python tk
# …then the same git clone + python3 commands as Linux
```
(The python.org macOS package already includes Tk.)

## Four input modes

One engine, four ways to type — every interface (CLI `--layout`,
desktop radio buttons, web toggle, API `mode`) supports all of them.

| Mode | You type | You get | Who it's for |
|---|---|---|---|
| `roman` (default) | `namaste` — English phonetics | नमस्ते | Everyone with an English keyboard |
| `traditional` | `gfdLGL` — MPP Traditional keys | नामीद्दी | Trained Traditional-layout typists |
| `traditional-kmn` | `S` — revised Traditional keys | क् (classic gives ङ्क) | Keyman v1.3.1 users |
| `romanized` | `kA` — MPP Romanized keys | कआ | Windows Romanized-layout users |

```bash
python3 -m core.cli "timi kasto chhau"                # → तिमी कस्तो छौ
python3 -m core.cli --layout traditional "k6gf"       # → प६ना
python3 -m core.cli --layout traditional-kmn "S"      # → क्
python3 -m core.cli --layout romanized "kA"           # → कआ
```

Direct modes (`traditional`, `traditional-kmn`, `romanized`) map each
key 1:1 — no phonetics, no dictionary:
- `traditional` = MPP classic, ported from m17n `ne-trad.mim` and
  **machine-verified 94/94** against the installed file.
- `traditional-kmn` / `romanized` = Keyman v1.3.1 / v1.0.1 tables,
  **machine-verified** against vendored sources (`tools/reference/`).
  One known upstream difference is documented in code: the `\` key
  (Keyman ॐ/ः vs Windows-MSKLC literal `\`/`|`).

## Typing reference

**Roman mode** — long vowels are doubled; capitals give retroflexes:

| Type | Get | Type | Get | Type | Get |
|---|---|---|---|---|---|
| `aa` | आ | `kh` | ख | `ksh` | क्ष |
| `ii` / `ee` | ई | `chh` | छ | `tr` | त्र |
| `uu` / `oo` | ऊ | `T` / `Th` | ट / ठ | `gyn` / `jn` | ज्ञ |
| `e` `ai` `o` `au` | ए ऐ ओ औ | `D` / `Dh` | ड / ढ | `sh` / `Sh` / `s` | श ष स |
| `t/` `d/` `n/` | ट ड ण | `ng` | ङ | `rri` | ऋ |
| `.` / `..` | । / ॥ | `~a` | ऽ | `0`–`9` | ०–९ |

Word-start `om` / `aum` → ॐ (mid-word stays split: `sombar` → सोमबार).

**Traditional mode** — home row `a s d f` → ब क म ा,
`j k l ;` → व प ि स; vowels `f`→ा `l`→ि `'`→ु `"`→ू `]`→े;
shift capitals give compounds (`Q`→त्त `T`→ट्ट `I`→क्ष `!`→ज्ञ);
`\` is halant ्, `[` is repha र्.

## Learn like a pro

Open the web tool and use the **visual keyboard**: all three direct
layouts, a Shift-layer toggle, click-to-type, and keys that light up
as you press your physical keyboard.

Five-lesson path (also shown in the app):

1. **Home row** — `a s d f` → ब क म ा, `j k l ;` → व प ि स.
   Drills: `n f d` → लाम, `k d` → पम, `h f g f d` → जानाम.
2. **Vowels** — `f`→ा `l`→ि `'`→ु `"`→ू `]`→े `c`→अ `A`→आ.
3. **Shift layer** — `Q`→त्त `T`→ट्ट `I`→क्ष `!`→ज्ञ `$`→द्ध.
4. **Conjuncts** — `k \ q` → क्त, `[` starts repha words.
5. **Words** — `gfdLGL` → नामीद्दी, then roman mode:
   `namaste` → नमस्ते. Type a little every day for a week —
   that alone makes you fluent.

## System-wide typing

Type directly into Word, browsers, chat — any application:

- **Linux** — install fcitx5 + m17n for your distro (table above uses
  `fcitx5 fcitx5-m17n m17n-db` on Debian/Fedora/SUSE,
  `fcitx5-im fcitx5-m17n m17n-db` on Arch), then in
  `fcitx5-configtool` add **`m17n_ne_rom-translit`**
  (uncheck “Only Show Current Language” to find it). Restart fcitx5.
  Same keystrokes as this project's roman mode. (`ibus` + `ibus-m17n`
  works too.)
- **Windows / macOS / Android / iOS** — via Keyman (free, open source):
  `python3 keyman/gen_kmn.py` regenerates `keyman/nepali_translit.kmn`
  from this project's mapping; open it in
  [Keyman Developer](https://keyman.com/developer), build the `.kmp`,
  install it. (Compiling still needs to be done on a machine with
  Keyman Developer — see Open work below.)

## Dictionary & data

- **119 hand-curated corrections** (`core/dictionary.py`) — the common
  words phonetics alone misspells (`sarkar`→सरकार, `dhanyabad`→धन्यवाद).
  Always win.
- **6,102 imported corrections** (`core/words_auto.py`, generated) —
  only pairs the engine can't derive, taken from real human romanizations
  ([Nepali-Roman-Transliteration](https://huggingface.co/datasets/Saugatkafley/Nepali-Roman-Transliteration),
  MIT). Regenerate: `python3 tools/import_pairs.py nep_valid.json nep_test.json`.
- **Ranked candidates + personal learning** — every word offers all its
  forms with sources (`user > hand > auto > phonetic`); the phonetic
  form is always present. Picking a non-top form teaches your install
  (`~/.config/nepali-transliterate/user.json`, never uploaded).
  CLI: `python3 -m core.cli --cands nam`.
- **Honest accuracy, not inflated**: the dictionary *memorizes* its
  training pairs (99.5% recall there). On never-seen pairs (seeded
  50/50 split, `python3 tools/eval_split.py`) phonetic rules score
  **~11% top-1 overall, ~14% on frequent words** — ambiguous spellings
  keep every candidate instead of guessing wrong.
- Suggestions while typing, shortest-first ranked.

## Google Input Tools — merged into suggestions

Google's engine is proprietary, but its candidates ride along **inside
the normal flow** (offline engine stays instant and default):

- Desktop + web: tick **+Google suggestions** — Google's top candidates
  for your current word appear after ours (marked `G:` on desktop).
  Output itself is always instant offline; Google loads in the background,
  stale replies are discarded, repeat words are cached, failures are silent.
- CLI one-shot: `python3 -m core.cli --google "timi kasto chhau"`
  (needs internet; clear error when offline). No API keys, no signup.

Benchmark mode (gentle + cached, disagreements human-reviewed only):

```bash
python3 tools/google_bench.py --limit 200
```

Last measured on 118 common words: **83 exact top-1 matches (70%)**;
our form sits in Google's top-5 in 23 more cases. The rest are mostly
our wins on standard spelling (`didi`→दिदी not दिदि, `kahaa`→कहाँ
not कहा). Edge: **standard-spelling-first ranking**.

## Preeti rescue

Millions of legacy documents are stuck in the Preeti fake-font encoding
(`g]kfn` displaying as नेपाल). Convert them:

```bash
pip install "nepali-transl[preeti]"
python3 -m core.cli --preeti "g]kfn"   # → नेपाल
```

The table isn't vendored (upstream is CC-BY-NC-SA); the MIT
`preeti-unicode-converter` package is the backend.

## Project layout & tests

```
core/nepali_transl.py  transliteration engine (roman mode)
core/traditional.py    Traditional + Trad-rev direct maps
core/romanized_layout.py  MPP Romanized direct map
core/dictionary.py     hand corrections (119, always win)
core/words_auto.py     imported corrections (6,102, generated)
core/preeti_bridge.py  optional Preeti bridge (needs pip extra)
core/google_backend.py online Google comparison (explicit opt-in)
core/cli.py            CLI (4 modes + --preeti)
keyman/                .kmn generator + output (system-wide path)
tools/                 pair importer, Google bench, kmn references
web/                   offline typing tool + visual keyboard + guide
desktop/               tkinter app (4 modes, zero dependencies)
tests/                 33 tests, stdlib only
```

```bash
python3 tests/test_transliterate.py   # 26 — engine, dict, candidates, Preeti, Google
python3 tests/test_traditional.py     # 7 — incl. 94/94 m17n parity
python3 tests/test_layouts.py         # 6 — incl. Keyman-source parity
```

## Open work

- Compile `.kmp` in Keyman Developer and attach to a GitHub Release.
- Windows `.exe` (PyInstaller) for friends without Python.
- `pip install nepali-transl` via PyPI publish.
- Desktop launch + clipboard check on Wayland.

## License

GPL-2.0-or-later. See [LICENSE](LICENSE) and [NOTICE](NOTICE) for
third-party attributions. By Pradip Gosain.
