"""Desktop GUI tests (skipped when no display is available).

Drives the tkinter UI programmatically: typing, mode switching, IME
commit/revert, suggestions, forms. Uses update() pumping instead of
mainloop() so the suite stays non-interactive and fast.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    import tkinter as tk
    _probe = tk.Tk()
    _probe.destroy()
    HAS_DISPLAY = True
except Exception:
    HAS_DISPLAY = False


def _make_app():
    from desktop.app import App
    app = App()
    app.update()
    return app


def test_launch_builds_all_widgets():
    if not HAS_DISPLAY:
        print("  (skip: no display)")
        return
    app = _make_app()
    try:
        for attr in ("roman", "out", "sugg_frame", "forms_frame",
                     "input_label", "status", "mode"):
            assert hasattr(app, attr), attr
        assert app.mode.get() == "roman"
    finally:
        app.destroy()


def test_typing_updates_output():
    if not HAS_DISPLAY:
        print("  (skip: no display)")
        return
    app = _make_app()
    try:
        app.roman.insert("1.0", "namaste")
        app.update()
        assert "नमस्ते" in app.out.get("1.0", "end"), app.out.get("1.0", "end")
    finally:
        app.destroy()


def test_mode_switch_changes_output():
    if not HAS_DISPLAY:
        print("  (skip: no display)")
        return
    app = _make_app()
    try:
        app.roman.insert("1.0", "k")
        app.mode.set("traditional")
        app._update()
        app.update()
        assert "प" in app.out.get("1.0", "end")
        app.mode.set("romanized")
        app._update()
        app.update()
        assert "क" in app.out.get("1.0", "end")
    finally:
        app.destroy()


def test_ime_commit_and_revert():
    if not HAS_DISPLAY:
        print("  (skip: no display)")
        return
    app = _make_app()
    try:
        app.ime_var.set(True)
        for ch in "namaste":
            app.roman.insert("end-1c", ch)
        app.update()
        app.roman.focus_force()
        app.update()
        # real key events through the binding chain (not direct calls)
        app.event_generate("<space>")
        app.update()
        app.update()
        assert "नमस्ते " in app.roman.get("1.0", "end"), \
            repr(app.roman.get("1.0", "end"))
        app.event_generate("<BackSpace>")
        app.update()
        app.update()
        assert "namaste" in app.roman.get("1.0", "end"), \
            repr(app.roman.get("1.0", "end"))
    finally:
        app.destroy()


def test_suggestions_and_forms_shown():
    if not HAS_DISPLAY:
        print("  (skip: no display)")
        return
    app = _make_app()
    try:
        app.roman.insert("1.0", "nam")
        app.update()
        assert app.sugg_frame.winfo_children(), "no suggestion buttons"
        assert app.forms_frame.winfo_children(), "no form buttons"
    finally:
        app.destroy()


def run_all():
    tests = [test_launch_builds_all_widgets, test_typing_updates_output,
             test_mode_switch_changes_output, test_ime_commit_and_revert,
             test_suggestions_and_forms_shown]
    passed, failed = 0, 0
    for fn in tests:
        try:
            fn()
            print(f"  PASS {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL {fn.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
