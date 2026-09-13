# Complete Linux Guide — Nepali Typing for Absolute Beginners
*By Pradip Gosain. Works on Arch, Debian, Ubuntu, Mint, Fedora, openSUSE
and derivatives. No prior Linux knowledge assumed.*

You will end up able to press **Super+Space** and switch between
English and Nepali anywhere — browser, Word, chat, terminal.

---

## Part 0 — What are we installing? (30 seconds)

| Piece | What it does | Analogy |
|---|---|---|
| This project | Converts roman typing (`namaste`) to Nepali (`नमस्ते`) | Like Google Input Tools, but offline |
| IBus engine (`ibus/`) | Plugs our converter into system Settings | Like adding a Nepali keyboard on a phone |
| fcitx5 / Rime files | Same thing, for KDE-style desktops | Alternative plug, same converter |

You do **not** need to understand any of this to follow the guide.
Just pick **Path A** (try it, 5 minutes) then **Path B** (system-wide).

---

## Part 1 — Open a terminal (if you've never done it)

- **GNOME (Ubuntu, Fedora…):** press `Super` (Windows key), type
  `terminal`, press Enter. Or right-click desktop → *Open in Terminal*.
- **KDE (Kubuntu, Manjaro KDE…):** same, or right-click → *Open Terminal Here*.
- Copy-paste into it with **Ctrl+Shift+V** (plain Ctrl+V won't work here).

Check what you have (copy each line, press Enter after each):

```bash
cat /etc/os-release | head -2
python3 --version
```

You should see your distro name and `Python 3.x`. Any 3.8+ works.

---

## Part 2 — Path A: try it right now (5 minutes, nothing installed)

```bash
git clone https://github.com/PRADIPGOSAIN/nepali-transliterate.git
cd nepali-transliterate
python3 -m core.cli "mero nam pradip ho"
```

Expected output:

```text
मेरो नाम प्रदिप हो
```

If you see `git: command not found`, install git first
(see the table in Part 3), then retry. If you see Nepali text —
**it works.** Now try the visual tools:

```bash
python3 web/app.py
```

Open **http://127.0.0.1:8000** in your browser. You get:
a typing box, a **visual keyboard** (click keys, press real keys and
watch them light up), and a 5-lesson pro course. Tick
**⌨️ Typewriter** and Nepali forms live while you type
(space converts, backspace undoes).

```bash
python3 desktop/app.py
```

Desktop version of the same (needs Tk — Part 3 table if it errors
with `no module named 'tkinter'`).

> Seeing `engine vX.Y.Z` top-right of the web tool is normal — it proves
> which version your server runs. A red banner means: stop the server
> (Ctrl+C in its terminal), `git pull`, start again.

---

## Part 3 — Dependencies per distro (only if something was missing)

| Distro | Python + extras | System input (Path B) |
|---|---|---|
| Arch / Manjaro / EndeavourOS | `sudo pacman -S python tk git` | `sudo pacman -S fcitx5-im fcitx5-m17n m17n-db` **or** `sudo pacman -S ibus python-gobject` |
| Debian / Ubuntu / Mint / Pop!_OS | `sudo apt install python3 python3-tk git` | `sudo apt install fcitx5 fcitx5-m17n m17n-db` **or** `sudo apt install ibus python3-gi` |
| Fedora / RHEL / Rocky | `sudo dnf install python3 python3-tkinter git` | `sudo dnf install fcitx5 fcitx5-m17n m17n-db` **or** `sudo dnf install ibus python3-gobject` |
| openSUSE | `sudo zypper install python3 python3-tk git` | `sudo zypper install fcitx5 fcitx5-m17n m17n-db` **or** `sudo zypper install ibus python3-gobject` |

Type your password when `sudo` asks (nothing appears while you type —
that's normal). Answer `Y` when it asks to proceed.

Which input framework do *you* have? **GNOME → IBus. KDE → usually
fcitx5** (check: if `fcitx5-configtool` opens a window, it's fcitx5).
When in doubt, try the IBus path first — GNOME Settings picks it up
automatically.

---

## Part 4 — Path B1: add Nepali to GNOME Settings (recommended)

1. Install the engine (one command, needs your password):
   ```bash
   cd ~/nepali-transliterate
   sudo ./ibus/install.sh && ibus restart
   ```
   You should see `done. Now run: ibus restart` (already done by `&&`).
2. Open **Settings → Keyboard → Input Sources**, click **+**,
   click the **⋮** (three dots) → **Other**, type `Nepali`,
   select **Nepali Transliterate** → **Add**.
   (If it's missing: log out and back in once, then look again.)
3. Press **Super+Space**. A tiny `N` / `ने` indicator appears top-right.
   Type `namaste` anywhere — you should see नमस्ते forming with a
   candidate list. **Space** commits, **1–5** picks alternates,
   **Backspace** edits, **Esc** cancels.
4. Press Super+Space again → back to English. That's the whole workflow.

## Part 5 — Path B2: KDE / fcitx5 (two options)

**Option 1 — Rime schema with OUR dictionary (recommended):**
Needs the `fcitx5-rime` package too (`sudo pacman -S fcitx5-rime` /
`sudo apt install fcitx5-rime` / `sudo dnf install fcitx5-rime` /
`sudo zypper install fcitx5-rime`).
```bash
mkdir -p ~/.local/share/fcitx5/rime
cp ~/nepali-transliterate/rime/*.yaml ~/.local/share/fcitx5/rime/
```
Open `fcitx5-configtool` → *Input Method* → **+** → uncheck
*Only Show Current Language* → add **Nepali Transliterate** →
*Apply*. Right-click the tray icon → *Restart* (or log out/in).
Switch with **Ctrl+Space** (the usual default; changeable in settings).

**Option 2 — classic m17n (no files needed):**
Install `fcitx5-m17n` + `m17n-db` (Part 3 table), then in
`fcitx5-configtool` add **`m17n_ne_rom-translit`**.
Same keystrokes, smaller built-in dictionary.

> fcitx5 sometimes needs a logout/login (or reboot) the very first
> time before new input methods appear. That's fcitx5, not us.

---

## Part 6 — How to type (the 3 rules that matter)

1. **Type by sound**: `kasto chha` → कस्तो छ.
2. **Double long vowels**: `kaa`→का, `nepaal`→नेपाल, `ma`→म but
   `maa`→मा.
3. **Capitals are retroflexes**: `T`→ट, `D`→ड. `t/`→ट also works.

Special keys: `.`→।, `..`→॥, `ksh`→क्ष, `tr`→त्र, `gyn`→ज्ञ,
digits `0-9`→०-९. Words you type often but spell loosely
(`kathmandu`, `xa` for छ) are auto-corrected from a 6,400-word
dictionary — and anything you pick from the alternates list is
**remembered on your machine** for next time.

Want the Traditional keyboard instead (`k`→प)? Switch the mode
(CLI `--layout traditional`, radio buttons in the apps) and follow
the in-app 5-lesson course.

---

## Part 7 — Troubleshooting (read the symptom)

- **`Input source not listed`** → you skipped the logout/login (Path B),
  or installed for the wrong framework (GNOME needs IBus path,
  KDE needs fcitx5 path).
- **Typing does nothing / English still comes out** → check the
  top-bar/tray indicator is on Nepali, not English. Toggle again.
- **`ibu​s: command not found`** → install ibus (Part 3 table).
- **`No module named 'tkinter'`** → install the Tk row (Part 3 table).
- **`address already in use` (web tool)** → an old server still runs:
  find its terminal, Ctrl+C, or start on another port:
  `python3 web/app.py --port 8001`.
- **Red “server outdated” banner** → terminal running the server:
  Ctrl+C, `git pull`, start again.
- **Words look wrong in one app but right elsewhere** → some apps
  (old X11 programs) need: `GTK_IM_MODULE=ibus QT_IM_MODULE=ibus
  XMODIFIERS=@im=ibus` (for fcitx5 replace `ibus` with `fcitx`).
  Log out/in after setting.
- **Preeti-font documents** (`g]kfn` gibberish) →
  `pip install "nepali-transl[preeti]"`, then
  `python3 -m core.cli --preeti "g]kfn"`.
- **Uninstall IBus engine**: `sudo rm -rf /usr/share/ibus-nepali-transl
  /usr/share/ibus/component/nepali_translit.xml && ibus restart`.

Still stuck? Open an issue at
https://github.com/PRADIPGOSAIN/nepali-transliterate/issues
with: distro (`cat /etc/os-release`), desktop (GNOME/KDE),
`python3 --version`, and what you see.

---

## Part 8 — Cheat sheet (the whole guide on a napkin)

```bash
git clone https://github.com/PRADIPGOSAIN/nepali-transliterate.git
cd nepali-transliterate
python3 -m core.cli "namaste"        # try it
python3 web/app.py                   # learn + type  → :8000
sudo ./ibus/install.sh && ibus restart   # system-wide (GNOME)
# Settings → Keyboard → Input Sources → + → Nepali → Nepali Transliterate
# Super+Space switches EN ↔ NP
```
