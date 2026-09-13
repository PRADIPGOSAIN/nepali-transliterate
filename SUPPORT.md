# Platform & Feature Support — nepali-transl v0.8.2

What the project does, and where each piece runs. Everything below is
verified unless marked *(unverified)*.

## What it does

| Capability | Status | Notes |
|---|---|---|
| Roman transliteration (`namaste` → नमस्ते) | ✅ | Phonetic engine + 6,220-word dictionary; 99.5% on 6,905 real pairs |
| Traditional keyboard mode (`k` → प) | ✅ | 94/94 machine-verified vs m17n `ne-trad.mim` |
| Revised Traditional mode (`S` → क्) | ✅ | 93/93 verified vs Keyman v1.3.1 source |
| Romanized keyboard mode (`k` → क) | ✅ | 94/94 verified vs Keyman v1.0.1 source |
| Live typewriter (space converts, backspace reverts) | ✅ | Web + desktop, roman mode |
| Visual keyboard + 5-lesson pro guide | ✅ | Web app |
| Word suggestions (shortest-first) | ✅ | + optional Google candidates merged in |
| Google Input Tools backend | ✅ opt-in | CLI `--google`, app checkboxes; offline default |
| Preeti → Unicode rescue | ✅ opt-in | Needs `pip install nepali-transl[preeti]` |
| Google benchmark vs our engine | ✅ | `tools/google_bench.py` (online, human-reviewed) |
| System-wide typing, Linux | ✅ | Via fcitx5-m17n / ibus-m17n (same keystrokes) |
| System-wide typing, Windows/macOS/mobile | ⚠️ path ready | `.kmn` generated; compiling in Keyman Developer not yet done |
| Offline guarantee | ✅ | Enforced by test (`test_no_network_imports_in_core`) |

## Where it runs

| Platform | CLI | Web app | Desktop app | System-wide | Needs |
|---|---|---|---|---|---|
| Arch / Manjaro | ✅ | ✅ | ✅ | ✅ fcitx5-m17n | `python tk` |
| Debian / Ubuntu / Mint | ✅ | ✅ | ✅ | ✅ fcitx5-m17n | `python3 python3-tk` |
| Fedora / RHEL | ✅ | ✅ | ✅ | ✅ fcitx5-m17n | `python3 python3-tkinter` |
| openSUSE | ✅ | ✅ | ✅ | ✅ fcitx5-m17n | `python3 python3-tk` |
| Windows 10/11 | ✅ | ✅ | ✅ *(unverified)* | ⚠️ via future `.kmp` | python.org Python |
| macOS | ✅ *(unverified)* | ✅ *(unverified)* | ✅ *(unverified)* | ⚠️ via future `.kmp` | python.org / brew Python |
| Android / iOS | ❌ | ✅ via mobile browser | ❌ | ⚠️ via future `.kmp` | — |

*(unverified)* = code is cross-platform by construction (stdlib only) but
hasn't been launched on that OS yet. If you run it there, please report:
open an issue with OS + Python version + what happened.

## Python versions

Requires 3.8+. Tested on 3.14 (dev machine). No third-party packages
for core features; optionals: `preeti-unicode-converter` (`--preeti`),
nothing else (Google backend uses stdlib `urllib`).

## Known limits (honest list)

- Desktop/web apps are **copy-paste workflow**, not system-wide keystroke
  interception (that needs the OS input framework: fcitx5 / Keyman).
- Dictionary ambiguities exist where one romanization maps to several
  words (`darjeeling` → दार्जीलिङ/दार्जिलिङ); first-listed wins, hand
  entries always beat imports.
- Loanword spellings follow the majority dataset form, not every variant.
- Keyman `.kmn` output hasn't been compiled in Keyman Developer yet.
- No hosted web version; the web tool runs on localhost.
