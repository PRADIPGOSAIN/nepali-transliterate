# Implementation Plan: Nepali Transliterate (`nepali-transl`)

## Overview
Modern successor to `ne-rom-translit` (m17n `.mim`, 2013): the same phonetic
mapping (`k`→क, `kh`→ख, `ksh`→क्ष, `tr`→त्र …) as a zero-dependency Python
engine, plus dictionary autocorrect, word suggestions, a desktop app, an
offline web typing tool, and a Keyman keyboard source for system-wide typing
on Windows/macOS/mobile. 100% of the original `.mim` mapping pairs covered
and verified by tests.

## Architecture Decisions
- **Core engine in stdlib-only Python** (`core/nepali_transl.py`): state machine
  ported from `ne-rom-translit.mim`. No `pip install` needed — friends on
  Windows run it with stock python.org Python. Rationale: widest reach,
  easiest install; deliberately NOT Tauri/Electron/FastAPI (heavy toolchains).
- **Dictionary layer** (`core/dictionary.py`): fixes what pure phonetics cannot
  (`kathmandu`→काठमाडौं, `nepal`→नेपाल), plus trailing-anuswar stems
  (`sangaM`→सँगं) and suggestion wordlist.
- **Keyman `.kmn` generator** (`keyman/gen_kmn.py`): single source of truth is
  the Python mapping tables; the `.kmn` is generated (with `--check` coverage
  gate). Keyman Developer (free/OSS) builds the `.kmp` for system-wide typing.
- **Linux system-wide**: reuse existing `fcitx5-m17n` + `m17n-db` (already the
  user's configured setup) — no new daemon to maintain.
- **Behavioral deltas vs original mim (intentional, documented)**:
  - `rri`/`rree` standalone → ऋ/ॠ (longest-match wins over `r` consonant)
  - `M`/`N` at word start → म/न consonants; mid-word → anusvara ं
  - duplicate dict keys resolved (`ki`→कि; `pani`→पानी)

## Task List

### Phase 1: Foundation — DONE
- [x] Port `.mim` mapping tables to Python (consonants/vowels/matras/signs)
- [x] State-machine word transliterator + file/batch APIs

### Checkpoint: Foundation — DONE (8/8 tests)

### Phase 2: Correctness audit — DONE
- [x] Exhaustive `.mim` pair extraction (101 pairs) vs engine coverage
- [x] 56-case stress test → found & fixed: missing k/g, falsy `''` matra,
      `~a`→ऽ, `\`/`|` halant forms, M/N context rule, `rri` priority,
      dict duplicate keys, stem+anuswar (`sangaM`)
- [x] Locked in as 14-test suite

### Checkpoint: Correctness — DONE (14/14 tests, 56/56 stress cases)

### Phase 3: Apps & packaging — DONE
- [x] CLI (`core/cli.py`), tkinter desktop app, stdlib web server + page
- [x] Keyman `.kmn` generator with coverage check
- [x] `pyproject.toml`, README (Win10 + Linux + Keyman instructions), LICENSE

### Checkpoint: Complete
- [x] Full verification run (below)

## Risks and Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Keyman `.kmn` never compiled in Keyman Developer | Med | Syntax follows documented `any()`/`index()`/`nul` patterns; needs a Windows/Dev-machine build to confirm |
| Dictionary ambiguity (`pani` पानी vs पनि) | Low | Chose पानी (Google-parity); suggestions surface alternatives |
| fcitx5-m17n upstream drift | Low | Engine is independent; Linux IME is reuse, not a fork |

## Phase 4: Dictionary import — DONE
- [x] Searched online: Dakshina (CC-BY-SA, 2 GB tar — rejected), Aksharantar
      (no Nepali), hunspell-ne (Devanagari-only) → chose MIT HF dataset
      `Saugatkafley/Nepali-Roman-Transliteration` (6,905 real pairs)
- [x] `tools/import_pairs.py`: imports only engine blind spots; two-pass
      phonetic-ownership (anu->अनु not अणु); source priority; collisions kept 28
- [x] Result: `core/words_auto.py` with 6,102 entries; **99.5% on 6,905 pairs**
- [x] Case now meaningful: `sangaM`->सँगं vs `sangam`->संगम (mim semantics)
- [x] Preeti bridge via MIT PyPI backend (table not vendored: CC-BY-NC-SA)

### Checkpoint: Dictionary — DONE (19/19 tests)

## Phase 5: Google benchmark — DONE
- Google source is proprietary (nothing to take), but the transliteration
  API endpoint is publicly reachable and alive.
- Built `core/google_backend.py` (online comparison) + `tools/google_bench.py`
  (batched, cached, gitignored; disagreements -> review TSV, never auto-imported).
- Result on 118 hand words: 83 top-1 agree (70%); ours in Google top-5 in 23
  more; remaining 12 divergences mostly ours-wins on standard spelling.
  Edge statement: standard-spelling-first ranking vs Google's literal-first.

### Checkpoint: Benchmark — DONE (20/20 tests)

## Phase 6: Traditional keyboard mode + independence — DONE
- Surveyed GitHub Nepali-typing projects (Keyman MIT keyboards, MSKLC
  installers, macOS bundles, BharatKeyIME, your own ne-trad-ttf repo);
  harvested the authoritative mapping already on disk: m17n `ne-trad.mim`
  (MPP Traditional, LGPL — combinable with GPL-2.0+).
- Built `core/traditional.py`: 94-key direct map (lower/shift/digits/symbols,
  incl. ZWJ/ZWNJ/halant/repha `q`->त्र `[`->र्), wired as `mode=` through
  engine (`transliterate(text, mode)`), CLI (`--layout`), desktop (radio
  toggle), web (toggle + API param, invalid mode falls back to roman).
- `tests/test_traditional.py`: **94/94 machine parity vs installed mim**,
  home/shift/digits/passthrough/mode-difference tests, plus
  `test_no_network_imports_in_core` independence guarantee.

### Checkpoint: Traditional — DONE (20/20 + 7/7 tests)

## Phase 7: Deep GitHub survey — DONE
- Read actual sources: Keyman nepali_traditional.kmn v1.3.1 + nepali_romanized.kmn
  v1.0.1, asheshwor's Windows MSKLC `NP_Romanised`
  layout (parsed LAYOUT table: agrees with Keyman on all base/shift keys except
  backslash, adds AltGr layer), liblekhika mapping.toml (ported one idea:
  word-initial om/aum -> ॐ), BharatKeyIME (same Windows mapping, skipped).
- Key discovery: your Keyman trad is a NEWER revision than m17n trad
  (caps->halant forms, m=ZWNJ, |=ZWJ, [=ृ) — both now supported as modes.
- Built `core/romanized_layout.py` (MPP Romanized, 94 keys) + `TRAD_KMN_MAP`
  (93 keys); vendored kmn sources under tools/reference/ (MIT, your own work).
- Parser subtleties solved: lone-backslash `"\"` form, single-quoted `'"'`
  double-quote key (romanized `"`->`"`, trad-kmn `"`->ू).
- Wired 4 modes through engine/CLI/desktop/web; fixed web handler hardcoding
  traditional; fixed `sombar` mb-conjunct trap via hand dict.

### Checkpoint: Survey — DONE (20/20 + 7/7 + 6/6 tests = 33 green)

## Open Questions
- Push to GitHub as `nepali-transl` successor repo? (recommended next step)
- PyInstaller `.exe` so Windows friends skip Python install?
- Compile `.kmp` in Keyman Developer for system-wide Windows typing?
