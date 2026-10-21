"""ffReal (FocusForReal) - a persistent, always-visible task timer for Windows."""

from __future__ import annotations

import math
import os
import sys
import time
import tkinter as tk
import ctypes
from tkinter import messagebox, ttk


APP_NAME = "ffReal"
WINDOW_WIDTH = 360
WINDOW_HEIGHT = 180
SCREEN_MARGIN = 18
CORNER_RADIUS = 28


class FocusForRealApp:
    """Two-state UI: task setup followed by a locked, topmost countdown."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.deadline = 0.0
        self.timer_job: str | None = None
        self.pin_job: str | None = None
        self.is_counting = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0

        self.task_var = tk.StringVar()
        self.hours_var = tk.StringVar(value="1")
        self.minutes_var = tk.StringVar(value="0")
        self.seconds_var = tk.StringVar(value="0")
        self.countdown_var = tk.StringVar(value="01:00:00")

        self.root.title(f"{APP_NAME} — FocusForReal")
        self.root.configure(bg="white")
        self.root.protocol("WM_DELETE_WINDOW", self._handle_close)
        self.root.bind("<Control-Shift-Q>", self._emergency_exit)
        self._set_app_icon()
        self.show_setup()

    def _set_app_icon(self) -> None:
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except tk.TclError:
                pass

    def _clear_window(self) -> None:
        for child in self.root.winfo_children():
            child.destroy()

    def _center_window(self, width: int, height: int) -> None:
        self.root.update_idletasks()
        x = max(0, (self.root.winfo_screenwidth() - width) // 2)
        y = max(0, (self.root.winfo_screenheight() - height) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def show_setup(self) -> None:
        """Show the normal window where a task and duration are entered."""
        self.is_counting = False
        self._cancel_jobs()
        self.root.overrideredirect(False)
        self.root.attributes("-topmost", False)
        self._clear_window_region()
        self.root.resizable(False, False)
        self._clear_window()
        self._center_window(500, 390)

        outer = tk.Frame(self.root, bg="white", padx=34, pady=28)
        outer.pack(fill="both", expand=True)

        tk.Label(
            outer,
            text="FocusForReal",
            bg="white",
            fg="#111111",
            font=("Segoe UI", 22, "bold"),
        ).pack(anchor="w")
        tk.Label(
            outer,
            text="Choose one task. Give it your full attention.",
            bg="white",
            fg="#606060",
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(2, 24))

        tk.Label(
            outer,
            text="What will you focus on?",
            bg="white",
            fg="#111111",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w")
        task_entry = tk.Entry(
            outer,
            textvariable=self.task_var,
            font=("Segoe UI", 12),
            bg="white",
            fg="#111111",
            insertbackground="#111111",
            relief="solid",
            bd=1,
        )
        task_entry.pack(fill="x", ipady=8, pady=(7, 20))

        tk.Label(
            outer,
            text="Timer",
            bg="white",
            fg="#111111",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w")

        duration = tk.Frame(outer, bg="white")
        duration.pack(fill="x", pady=(7, 26))
        self._time_input(duration, "Hours", self.hours_var, 0, 23).pack(side="left")
        self._time_input(duration, "Minutes", self.minutes_var, 0, 59).pack(side="left", padx=16)
        self._time_input(duration, "Seconds", self.seconds_var, 0, 59).pack(side="left")

        start = tk.Button(
            outer,
            text="START FOCUS TIMER",
            command=self.start_timer,
            bg="#111111",
            fg="white",
            activebackground="#333333",
            activeforeground="white",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            cursor="hand2",
            pady=11,
        )
        start.pack(fill="x")
        task_entry.bind("<Return>", lambda _event: self.start_timer())
        task_entry.focus_set()

    def _time_input(
        self,
        parent: tk.Widget,
        label: str,
        variable: tk.StringVar,
        minimum: int,
        maximum: int,
    ) -> tk.Frame:
        frame = tk.Frame(parent, bg="white")
        tk.Label(frame, text=label, bg="white", fg="#606060", font=("Segoe UI", 9)).pack(anchor="w")
        spinbox = ttk.Spinbox(
            frame,
            from_=minimum,
            to=maximum,
            width=8,
            textvariable=variable,
            justify="center",
            font=("Segoe UI", 11),
        )
        spinbox.pack(ipady=5, pady=(4, 0))
        return frame

    def start_timer(self) -> None:
        task = self.task_var.get().strip()
        if not task:
            messagebox.showwarning(APP_NAME, "Write the task you want to focus on.", parent=self.root)
            return

        try:
            hours = int(self.hours_var.get())
            minutes = int(self.minutes_var.get())
            seconds = int(self.seconds_var.get())
        except ValueError:
            messagebox.showwarning(APP_NAME, "Use whole numbers for the timer.", parent=self.root)
            return

        if not (0 <= hours <= 23 and 0 <= minutes <= 59 and 0 <= seconds <= 59):
            messagebox.showwarning(APP_NAME, "Enter a valid time between 1 second and 23:59:59.", parent=self.root)
            return

        total_seconds = hours * 3600 + minutes * 60 + seconds
        if total_seconds <= 0:
            messagebox.showwarning(APP_NAME, "Set the timer to at least one second.", parent=self.root)
            return

        self.deadline = time.monotonic() + total_seconds
        self.is_counting = True
        self.show_countdown(task)

    def show_countdown(self, task: str) -> None:
        """Switch to the borderless popup and pin it above every normal window."""
        self._clear_window()
        self.root.resizable(False, False)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)

        screen_width = self.root.winfo_screenwidth()
        x = max(0, screen_width - WINDOW_WIDTH - SCREEN_MARGIN)
        y = SCREEN_MARGIN
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")
        self.root.update_idletasks()
        self._apply_rounded_corners()

        panel = tk.Frame(
            self.root,
            bg="white",
            highlightthickness=0,
            bd=0,
            padx=22,
            pady=17,
        )
        panel.pack(fill="both", expand=True)

        tk.Label(
            panel,
            text="FOCUS ON",
            bg="white",
            fg="#3f3f3f",
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w")
        tk.Label(
            panel,
            text=task,
            bg="white",
            fg="#3f3f3f",
            font=("Segoe UI", 14, "bold"),
            wraplength=310,
            justify="left",
        ).pack(anchor="w", fill="x", pady=(5, 10))
        tk.Label(
            panel,
            textvariable=self.countdown_var,
            bg="white",
            fg="#3f3f3f",
            font=("Consolas", 24, "bold"),
        ).pack(anchor="w")

        # A borderless window has no title bar, so make the entire popup its
        # drag handle. Bind the labels as well because they cover most of it.
        self._make_draggable(panel)

        self.root.lift()
        self._update_countdown()
        self._keep_pinned()

    def _apply_rounded_corners(self) -> None:
        """Give the native borderless window a genuinely rounded shape."""
        if sys.platform != "win32":
            return
        hwnd = self.root.winfo_id()
        region = ctypes.windll.gdi32.CreateRoundRectRgn(
            0,
            0,
            WINDOW_WIDTH + 1,
            WINDOW_HEIGHT + 1,
            CORNER_RADIUS,
            CORNER_RADIUS,
        )
        if region:
            # Windows owns the region after a successful SetWindowRgn call.
            if not ctypes.windll.user32.SetWindowRgn(hwnd, region, True):
                ctypes.windll.gdi32.DeleteObject(region)

    def _clear_window_region(self) -> None:
        if sys.platform == "win32" and self.root.winfo_exists():
            try:
                ctypes.windll.user32.SetWindowRgn(self.root.winfo_id(), 0, True)
            except (AttributeError, tk.TclError):
                pass

    def _make_draggable(self, widget: tk.Widget) -> None:
        widget.bind("<ButtonPress-1>", self._start_drag)
        widget.bind("<B1-Motion>", self._drag_window)
        widget.configure(cursor="fleur")
        for child in widget.winfo_children():
            self._make_draggable(child)

    def _start_drag(self, event: tk.Event) -> None:
        self.drag_offset_x = event.x_root - self.root.winfo_x()
        self.drag_offset_y = event.y_root - self.root.winfo_y()

    def _drag_window(self, event: tk.Event) -> None:
        x = event.x_root - self.drag_offset_x
        y = event.y_root - self.drag_offset_y

        # Keep the timer reachable even when it is dragged toward an edge.
        max_x = max(0, self.root.winfo_screenwidth() - self.root.winfo_width())
        max_y = max(0, self.root.winfo_screenheight() - self.root.winfo_height())
        x = min(max(0, x), max_x)
        y = min(max(0, y), max_y)
        self.root.geometry(f"+{x}+{y}")

    def _update_countdown(self) -> None:
        if not self.is_counting:
            return

        remaining = max(0, math.ceil(self.deadline - time.monotonic()))
        hours, remainder = divmod(remaining, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.countdown_var.set(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

        if remaining == 0:
            self._timer_finished()
            return
        self.timer_job = self.root.after(200, self._update_countdown)

    def _keep_pinned(self) -> None:
        if not self.is_counting:
            return
        self.root.attributes("-topmost", True)
        self.root.lift()
        self.pin_job = self.root.after(1000, self._keep_pinned)

    def _timer_finished(self) -> None:
        self.is_counting = False
        self._cancel_jobs()
        self.countdown_var.set("00:00:00")
        try:
            import winsound

            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except (ImportError, RuntimeError):
            self.root.bell()

        self.root.overrideredirect(False)
        self.root.attributes("-topmost", True)
        messagebox.showinfo(APP_NAME, "Time is up — focus session complete!", parent=self.root)
        self.show_setup()

    def _cancel_jobs(self) -> None:
        for job in (self.timer_job, self.pin_job):
            if job:
                try:
                    self.root.after_cancel(job)
                except tk.TclError:
                    pass
        self.timer_job = None
        self.pin_job = None

    def _handle_close(self) -> None:
        if self.is_counting:
            return
        self.root.destroy()

    def _emergency_exit(self, _event: tk.Event | None = None) -> None:
        """Development/safety escape: Ctrl+Shift+Q."""
        self.is_counting = False
        self._cancel_jobs()
        self.root.destroy()


def main() -> None:
    if sys.platform != "win32":
        raise SystemExit("ffReal currently supports Windows only.")
    root = tk.Tk()
    FocusForRealApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
