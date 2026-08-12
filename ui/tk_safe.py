"""Safe Tkinter wrapper for VE-embedded dialogs.

VE 2025 runs launchers as blocking scripts.  A ``Tk().mainloop()`` opened
from a launcher can be perceived as a hang: no window appears (or a hidden
one does), the operator kills the process, and the VE model is left in an
undefined state.

This module isolates every Tk lifecycle concern behind two helpers so the
launchers keep a uniform, auditable pattern:

* ``run_dialog(build_dialog)`` -- open a Tk window with a guaranteed
  ``mainloop`` -> ``destroy`` -> ``update_idletasks`` sequence, even on
  exceptions.  The window is brought to the foreground on Windows via
  ``lift`` + ``focus_force`` + ``attributes('-topmost', True)`` and reset
  immediately so it stays interactive.  Returns whatever ``build_dialog``
  stored on the ``DialogHandle``.

* ``HeadlessDialogRunner`` -- record user actions instead of showing a
  window; used by unit tests and by launchers that must run in ``--probe``
  mode.  Same call signature as ``run_dialog``.

Both paths accept a build callable that receives one ``DialogHandle`` and
must attach the widgets it needs to ``handle.root``.  The callable returns
an ``Optional[dict]`` which becomes the ``DialogHandle.result``.

The wrapper does NOT alter widget layout policies; a dialog remains
responsible for its own geometry.  It only fixes the lifecycle.
"""

from __future__ import annotations

import contextlib
import logging
import sys
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


LOGGER = logging.getLogger("ui.tk_safe")


@dataclass
class DialogHandle:
    """State passed to a build callable and returned to the launcher."""

    root: Any = None
    result: Optional[Dict[str, Any]] = None
    closed_by: Optional[str] = None
    error: Optional[str] = None
    events: List[Dict[str, Any]] = field(default_factory=list)


def _bring_to_front_windows(root: Any) -> None:
    """Ensure the dialog is not hidden behind VE on Windows.

    ``-topmost`` is toggled off immediately so the operator can raise other
    windows normally afterwards.
    """

    try:
        root.lift()
        root.focus_force()
        root.attributes("-topmost", True)
        root.after(200, lambda: _safe_call(root.attributes, "-topmost", False))
    except Exception as exc:  # pragma: no cover - purely cosmetic
        LOGGER.debug("tk_safe | bring_to_front failed: %s", exc)


def _safe_call(callable_: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
    """Call ``callable_`` while swallowing Tk errors on already-destroyed roots."""

    try:
        callable_(*args, **kwargs)
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.debug("tk_safe | safe_call swallowed: %s", exc)


def run_dialog(
    build_dialog: Callable[[DialogHandle], Optional[Dict[str, Any]]],
    *,
    title: Optional[str] = None,
    protocol_close_reason: str = "USER_CLOSED_WINDOW",
) -> DialogHandle:
    """Show a Tk dialog with a fail-safe lifecycle.

    Args:
        build_dialog: Callable receiving one ``DialogHandle``.  It must attach
            widgets to ``handle.root`` (already a live ``Tk`` instance) and
            call ``handle.root.quit()`` or ``handle.root.destroy()`` when the
            user completes the interaction.  It may return a dict which will
            populate ``handle.result``.
        title: Optional window title.
        protocol_close_reason: The value assigned to ``handle.closed_by``
            when the operator closes the window via the window-manager button.

    Returns:
        ``DialogHandle`` with ``result``, ``closed_by`` and ``error`` set.

    The wrapper never re-raises: an exception raised by ``build_dialog`` or
    by the widgets is caught, recorded on the handle as ``error``, and the
    root is destroyed cleanly.  Launchers can therefore decide the exit code
    from the handle rather than from a bubbling Tk error.
    """

    handle = DialogHandle()
    try:
        import tkinter as _tk  # local import: launcher may run headless
    except Exception as exc:
        handle.error = "tkinter unavailable: {}".format(exc)
        handle.closed_by = "TK_UNAVAILABLE"
        return handle

    root: Any = None
    try:
        root = _tk.Tk()
    except Exception as exc:
        handle.error = "Tk() failed: {}".format(exc)
        handle.closed_by = "TK_INIT_FAILED"
        return handle

    handle.root = root
    if title is not None:
        _safe_call(root.title, title)

    def _mark_closed_by_wm() -> None:
        handle.closed_by = handle.closed_by or protocol_close_reason
        _safe_call(root.quit)

    _safe_call(root.protocol, "WM_DELETE_WINDOW", _mark_closed_by_wm)

    try:
        result = build_dialog(handle)
        if result is not None:
            handle.result = result
        _bring_to_front_windows(root)
        root.mainloop()
    except Exception:
        handle.error = traceback.format_exc()
        handle.closed_by = handle.closed_by or "BUILD_OR_MAINLOOP_RAISED"
    finally:
        try:
            root.update_idletasks()
        except Exception:
            pass
        try:
            root.destroy()
        except Exception:
            pass

    return handle


class HeadlessDialogRunner:
    """Run a dialog build callable without opening a real Tk window.

    The runner instantiates a stub ``root`` that records every widget-like
    method call.  ``build_dialog`` should not depend on the runtime shape
    of Tk widgets; it must only rely on the ``DialogHandle`` public API.

    Callers may inject predefined ``events`` to simulate a user path:
    a build callable can consume them via ``handle.events``.
    """

    def __init__(self, events: Optional[List[Dict[str, Any]]] = None):
        self._events = list(events or [])

    def run(
        self,
        build_dialog: Callable[[DialogHandle], Optional[Dict[str, Any]]],
    ) -> DialogHandle:
        handle = DialogHandle()
        handle.root = _StubRoot()
        handle.events = list(self._events)
        try:
            result = build_dialog(handle)
            if result is not None:
                handle.result = result
            handle.closed_by = handle.closed_by or "HEADLESS_COMPLETED"
        except Exception:
            handle.error = traceback.format_exc()
            handle.closed_by = handle.closed_by or "HEADLESS_RAISED"
        return handle


class _StubRoot:
    """Minimal Tk-like sink for headless mode; every call is a no-op."""

    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []

    def __getattr__(self, name: str) -> Any:
        def _record(*args: Any, **kwargs: Any) -> Any:
            self.calls.append({"method": name, "args": args, "kwargs": kwargs})
            return None

        return _record


__all__ = ["DialogHandle", "run_dialog", "HeadlessDialogRunner"]
