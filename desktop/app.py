"""Nepali Transliterate — cross-platform desktop app (tkinter, stdlib only).

Type romanized Nepali on the left, get live Unicode on the right.
Works on Windows / macOS / Linux with stock Python 3 (no pip needed).

Usage:  python3 desktop/app.py
"""
import os
import platform
import re
import sys
import threading
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk, messagebox

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.nepali_transl import get_transliterator

TR = get_transliterator()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("नेपाली Transliterate")
        self.geometry("720x560")
        self._build()

    @staticmethod
    def _devanagari_font() -> str:
        """Pick the best Devanagari font for this OS.

        Nirmala UI ships with Windows 10/11, Mangal with older Windows,
        Noto/Mukti are common on Linux. Fall back to default UI font.
        """
        try:
            available = set(tkfont.families())
        except Exception:
            available = set()
        for fam in ("Nirmala UI", "Mangal", "Noto Sans Devanagari",
                    "Mukti Narrow", "Lohit Nepali", "Kalimati"):
            if fam in available:
                return fam
        if platform.system() == "Windows":
            return "Nirmala UI"  # stock on Win10/11 even if not enumerated
        return "TkDefaultFont"

    def _build(self):
        pad = {"padx": 10, "pady": 6}
        modebar = ttk.Frame(self)
        modebar.pack(fill="x", **pad)
        ttk.Label(modebar, text="Layout:").pack(side="left")
        self.mode = tk.StringVar(value="roman")
        self._modes = [
            ("roman", "Translit (namaste → नमस्ते)"),
            ("traditional", "Traditional (k → प)"),
            ("traditional-kmn", "Trad-rev (S → क्)"),
            ("romanized", "Romanized (k → क)"),
        ]
        for value, label in self._modes:
            ttk.Radiobutton(modebar, text=label, variable=self.mode,
                            value=value, command=self._update).pack(
                                side="left", padx=4)
        self.google_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(modebar, text="+Google suggestions",
                        variable=self.google_var,
                        command=self._update).pack(side="left", padx=4)
        self.ime_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(modebar, text="⌨️ Typewriter",
                        variable=self.ime_var).pack(side="left", padx=4)
        self._seq = 0
        self._gcache = {}
        self._commit = None  # (roman, nepali) just committed, for Backspace-revert
        self.roman.bind("<space>", lambda e: self._ime_commit(e, " "))
        self.roman.bind("<Return>", lambda e: self._ime_commit(e, "\n"))
        self.roman.bind("<BackSpace>", self._ime_revert)

    ROMAN_TAIL = re.compile(r"[A-Za-z0-9~.*\\/']+$")

    def _ime_active(self):
        return self.ime_var.get() and self.mode.get() == "roman"

    def _at_end(self):
        try:
            return self.roman.compare("insert", "==", "end-1c")
        except tk.TclError:
            return False

    def _ime_commit(self, _evt, sep):
        if not self._ime_active() or not self._at_end():
            return None  # normal key behavior
        before = self.roman.get("1.0", "insert")
        m = self.ROMAN_TAIL.search(before)
        if not m:
            return None
        tail = m.group(0)
        nep = TR.transliterate(tail)
        if not nep:
            return None
        self.roman.delete(f"insert-{len(tail)}c", "insert")
        self.roman.insert("insert", nep + sep)
        self._commit = (tail, nep)
        self._update()
        return "break"

    def _ime_revert(self, _evt):
        if not self._ime_active() or not self._at_end() or not self._commit:
            self._commit = None
            return None
        roman, nep = self._commit
        text = self.roman.get("1.0", "end-1c")
        if text.endswith(nep + " ") or text.endswith(nep + "\n"):
            self.roman.delete(f"end-{len(nep) + 2}c", "end-1c")
            self.roman.insert("end-1c", roman)
            self._commit = None
            self._update()
            return "break"
        self._commit = None
        return None
        self.input_label = ttk.Label(self, text="")
        self.input_label.pack(anchor="w", **pad)
        self.roman = tk.Text(self, height=7, font=("TkDefaultFont", 14))
        self.roman.pack(fill="both", expand=False, **pad)
        self.roman.bind("<<Modified>>", self._on_edit)

        self.sugg_frame = ttk.Frame(self)
        self.sugg_frame.pack(fill="x", **pad)

        ttk.Label(self, text="नेपाली Unicode output:").pack(anchor="w", **pad)
        self.out = tk.Text(self, height=7, wrap="word",
                           font=(self._devanagari_font(), 18))
        self.out.pack(fill="both", expand=True, **pad)

        btns = ttk.Frame(self)
        btns.pack(fill="x", **pad)
        ttk.Button(btns, text="Copy output", command=self._copy).pack(side="left", padx=4)
        ttk.Button(btns, text="Clear", command=self._clear).pack(side="left", padx=4)
        self.status = ttk.Label(btns, text="Offline • by Pradip Gosain",
                                foreground="gray")
        self.status.pack(side="right", padx=4)

    def _set_status(self, msg):
        self.status.config(text=msg)

    def _on_edit(self, _evt=None):
        self.roman.edit_modified(False)
        # Offline engine is ~ms fast: refresh on this keystroke, no waiting.
        self._update()

    _HINTS = {
        "roman": "Roman input (e.g. namaste kasto chha):",
        "traditional": "Traditional keys (k → प, f → ा):",
        "traditional-kmn": "Revised Traditional keys (S → क्, m → ZWNJ):",
        "romanized": "Romanized keys (k → क, a → ा):",
    }

    def _update(self):
        mode = self.mode.get()
        self.input_label.config(text=self._HINTS.get(mode, "Input:"))
        text = self.roman.get("1.0", "end").strip()
        if not text:
            self.out.delete("1.0", "end")
            self._show_suggestions([])
            return
        if mode != "roman":
            # Direct key mapping: no phonetics, no dictionary.
            self.out.delete("1.0", "end")
            self.out.insert("1.0", TR.transliterate(text, mode=mode))
            self._show_suggestions([])
            return
        # Roman mode: render OFFLINE result instantly (never block the UI),
        # then enrich suggestions with Google in a background thread.
        result, suggs = TR.transliterate_with_suggestions(text)
        self.out.delete("1.0", "end")
        self.out.insert("1.0", result)
        self._show_suggestions(suggs)
        if self.google_var.get():
            words = text.split()
            last = words[-1] if words else ""
            if last:
                self._seq += 1
                threading.Thread(target=self._fetch_google,
                                 args=(self._seq, last, list(suggs)),
                                 daemon=True).start()

    def _fetch_google(self, seq, word, base):
        if word in self._gcache:
            cands = self._gcache[word]
        else:
            try:
                from core.google_backend import google_transliterate
                cands = google_transliterate(word, num=3).get(word, [])
            except Exception:
                cands = []
            if len(self._gcache) > 500:
                self._gcache.pop(next(iter(self._gcache)))
            self._gcache[word] = cands
        seen = set(base)
        extra = [c for c in cands if c and c not in seen][:3]
        if extra:
            self.after(0, lambda: self._add_google_suggs(seq, extra))

    def _add_google_suggs(self, seq, extra):
        if seq != self._seq:
            return  # stale: user kept typing
        for s in extra:
            ttk.Button(self.sugg_frame, text="G: " + s,
                       command=lambda v=s: self._apply_suggestion(v)).pack(
                           side="left", padx=3)
        self._set_status("Offline + Google suggestions")

    def _show_suggestions(self, suggs):
        for w in self.sugg_frame.winfo_children():
            w.destroy()
        for s in suggs:
            ttk.Button(self.sugg_frame, text=s,
                       command=lambda v=s: self._apply_suggestion(v)).pack(side="left", padx=3)

    def _apply_suggestion(self, word):
        content = self.roman.get("1.0", "end").strip().split()
        if content:
            content[-1] = word
            self.roman.delete("1.0", "end")
            self.roman.insert("1.0", " ".join(content) + " ")
            self._update()

    def _copy(self):
        text = self.out.get("1.0", "end").strip()
        if not text:
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Copied", "Nepali text copied to clipboard.")

    def _clear(self):
        self.roman.delete("1.0", "end")
        self.out.delete("1.0", "end")
        self._show_suggestions([])


if __name__ == "__main__":
    App().mainloop()
