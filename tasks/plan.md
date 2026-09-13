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

## Phase 8: Publish + learn-like-a-pro — DONE (v0.5.0)
- Authorship set to Pradip Gosain across project files.
- Full GPL-2.0 LICENSE, NOTICE attribution file, version single-sourced
  (0.5.0), complete .gitignore.
- Visual keyboard: /api/layouts endpoint (3 maps + QWERTY rows/shift rows),
  interactive web keyboard (layout tabs, Shift toggle, click-to-type,
  live key-highlight on physical keypress).
- 5-lesson pro guide in web UI + README drills.
- Distro matrix (Arch/Debian/Fedora/openSUSE python+tk + fcitx5-m17n lines),
  Windows ZIP path, macOS path.
- GitHub: https://github.com/PRADIPGOSAIN/nepali-transliterate (public),
  main pushed, tag v0.5.0 pushed. Fresh-clone verified: 20+7+6 green.

### Checkpoint: Publish — DONE

## Phase 9: Google backend integration — DONE (v0.6.0)
- `google_sentence()` one-request helper in core/google_backend.py.
- CLI `--google` (clear offline error, exit 2), desktop Google mode with
  status line + offline fallback dialog, web Google mode showing
  Google-vs-ours side-by-side (+ hardened non-string JSON inputs).
- Network-safe tests (skip offline): backend + CLI. 21/21 green.

### Checkpoint: Google — DONE

## Phase 10: Kill the lag, merge Google in — DONE (v0.7.0)
- Problem: Google mode fired a blocking network request per keystroke
  (desktop froze on the UI thread; web showed stale/flickering output).
- Fix: offline output renders instantly ALWAYS; Google candidates merge
  into suggestions only — web (checkbox + seq guard + abort in-flight +
  adaptive 500ms debounce + server cache), desktop (checkbox + daemon
  worker thread + seq guard + session cache + status line).
- Removed the separate laggy Google output mode; CLI --google stays.
- Measured: plain 0.012s, first Google 0.6s, cached repeat 0.009s.

### Checkpoint: Speed — DONE (22+7+6 = 35 green)

## Phase 11: Live typewriter (IME) mode — DONE (v0.8.0)
- Request: see Nepali forming in real time while typing, fix mid-word.
- Web: ⌨️ Typewriter toggle — live `roman → nepali` strip under the box,
  SPACE/ENTER commits the word in place, Backspace reverts to roman,
  suggestion click commits. Zero-debounce live fetch (~11ms localhost).
- Desktop: same bindings in tkinter (commit/revert, roman mode).
- Fixed real user words: nam→नाम, gosai→गोसाई, gosain→गोसाईं.
- JS validated with node --check; API commit flow verified by curl.

### Checkpoint: Typewriter — DONE (23+7+6 = 36 green)

## Phase 12: Honest eval + candidates architecture — DONE (v0.9.0)
- Data hunt: nep_train.json (2.4M rows, 99.7% IndicCorp) downloaded+analyzed;
  Dakshina rejected (2GB, CC-BY-SA); liblekhika autocorrect (19 rules, one
  idea already covered). Bulk import rejected: bloat + noise, no frequencies.
- `tools/eval_split.py`: seeded 50/50 held-out eval. Phonetics ≈11% top-1
  (14% frequent words); dict memorizes (99.5% train recall). Published as-is.
- `candidates()` API: user > hand > auto > phonetic, phonetic always present,
  case-safe, top()==transliterate() invariant proven over 631 words.
- Local user lexicon (~/.config, NEPALI_TRANSL_HOME-overridable, learn API);
  non-top picks auto-learn in web/desktop; CLI --cands/--learn.
- README honesty pass (headline, numbers, limits).

### Checkpoint: Candidates — DONE (26+7+6 = 39 green)

## Phase 13: Big Roman data + fuzzy matching — DONE (v0.10.0)
- Surveyed dataset collections (IOST-ASCOL, PemaRG), Nepali-Flow suite,
  Sabdakosh (MIT), pratt778 engine (studied, ideas reimplemented+credited),
  LTK/CTRC layouts (already covered by our verified maps).
- Nepali-Flow-Roman 307k rows (CC-BY-4.0): token frequencies -> cross-check
  vs Sabdakosh 123k headwords -> ~70 confident colloquial hand entries
  (x-family, haru, malai, hunxa...), 4,396 suggestion keys (English out).
- Vowel-collapse + deschwa fuzzy alternates (never top-1: ki/anu lesson).
- Single-truth ranking refactor; top()==transliterate() over 631 words.

### Checkpoint: Roman data — DONE (28+7+6 = 41 green)

## Phase 14: Deep bug hunt — DONE (v0.10.1)
- 6,000-input fuzz: zero crashes; nasty unicode/long inputs sane.
- Invariant top()==transliterate() over 1,714 words (found+fixed:
  candidates() phrase contract + case-safe phonetics).
- Full source re-read. Fixed: dead imports/vars/params, dead matra
  branch (documented), web race on IME commit, clearAll gaps, clipboard
  fallback, version single-sourcing (page gets it from server),
  desktop Google thread throttle + version footer, bench/eval lexicon
  isolation, softer Google assertions, tmpdir cleanup, full exports.
- Content bug: lesson `k \ q` -> प्त्र, not क्त (now `s \ t`).
- Keyman .kmn now COMPILES with kmc 18 (fixed: &LANGUAGE removal,
  space-separated context, explicit combo rules replacing rejected
  any()+index() second-position form, nul removal). 26KB .kmx, 0 errors.
- 74 hand entries spot-checked vs Sabdakosh (36 headwords + 38 valid
  inflections, no wrong spellings found).

### Checkpoint: Bug hunt — DONE (29+7+6 = 42 green)

## Phase 15: Essay readiness — DONE (v0.11.0)
- Wrote a real nibedan letter through the engine; fixed every systematic
  failure it exposed (was ~40 wrong words, now reads correctly).
- Punctuation-stripped dict lookup (kathmandu, -> काठमाडौं,) incl. a
  same-session discovery: glued newline tokens broke lookup (fixed by
  whitespace-preserving split).
- Decimal dots (15.50 -> १५.५०), email/URL/ACRONYM preservation,
  productive suffix composition (timilai -> तिमीलाई), 60 official words.
- Idempotence + 7KB-doc performance tests. Honest eval ticked 10.7->11.6%.

### Checkpoint: Essays — DONE (37+7+6 = 50 green)

## Still open (needs your machines)
- PyInstaller `.exe` on a Windows box for friends without Python.
- Compile `.kmp` in Keyman Developer for system-wide typing.
- Desktop GUI launch + Wayland clipboard check on your KDE session.
- PyPI publish (`pip install nepali-transl`).
