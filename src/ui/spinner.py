"""Refined circular loading spinner widget for Dastavej Sanghralya.
Renders a smooth, relaxed rotating arc on a Canvas. 100% offline, lightweight, and precise.
"""

import tkinter as tk
import customtkinter as ctk

class LoadingSpinner(ctk.CTkFrame):
    """Rotating circular spinner with relaxed, smooth animation and precise styling."""

    def __init__(
        self,
        parent,
        size: int = 44,
        ring_width: int = 4,
        ring_color: str = "#0071e3",
        track_color: str = "#142138",
        text: str = "",
        text_size: int = 12,
        bg_color: str = "#09101d",
        **kwargs
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.size = size
        self.ring_width = ring_width
        self.ring_color = ring_color
        self.track_color = track_color
        self.angle = 0
        self.is_running = False
        self._timer_id = None
        self._custom_bg = bg_color

        # Centered container
        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.pack(expand=True)

        # Canvas for the spinner with exact integer dimensions
        self.canvas = tk.Canvas(
            self.center_frame,
            width=size,
            height=size,
            highlightthickness=0,
            bd=0,
            bg=self._custom_bg
        )
        self.canvas.pack(pady=(0, 10) if text else 0)

        # Crisp integer arc dimensions with proper margin
        pad = ring_width + 2
        self.box = (pad, pad, size - pad, size - pad)

        # Background track ring
        self.track_arc = self.canvas.create_arc(
            self.box,
            start=0,
            extent=359,
            outline=track_color,
            width=ring_width,
            style="arc"
        )

        # Subtle secondary arc (Soft Glow)
        self.glow_arc = self.canvas.create_arc(
            self.box,
            start=0,
            extent=90,
            outline="#38bdf8",
            width=ring_width,
            style="arc"
        )

        # Foreground spinner arc
        self.spinner_arc = self.canvas.create_arc(
            self.box,
            start=0,
            extent=75,
            outline=ring_color,
            width=ring_width,
            style="arc"
        )

        # Status text with high-contrast font
        self.lbl_text = None
        if text:
            self.lbl_text = ctk.CTkLabel(
                self.center_frame,
                text=text,
                font=ctk.CTkFont(family="Segoe UI", size=text_size, weight="bold"),
                text_color="#ffffff"
            )
            self.lbl_text.pack()

        self._update_canvas_bg()

    def _update_canvas_bg(self):
        try:
            bg = self._custom_bg if self._custom_bg and self._custom_bg != "transparent" else "#09101d"
            self.canvas.configure(bg=bg)
            self.canvas.itemconfig(self.track_arc, outline=self.track_color)
            self.canvas.itemconfig(self.spinner_arc, outline=self.ring_color)
        except Exception:
            pass

    def apply_theme(self, t: dict):
        self.ring_color = t.get("spinner_ring", "#0071e3")
        self.track_color = t.get("spinner_track", "#142138")
        self._custom_bg = t.get("spinner_bg", "#09101d")
        glow_color = t.get("spinner_glow", "#38bdf8")
        text_color = t.get("spinner_text", "#94a3b8")
        try:
            self.canvas.configure(bg=self._custom_bg)
            self.canvas.itemconfig(self.track_arc, outline=self.track_color)
            self.canvas.itemconfig(self.spinner_arc, outline=self.ring_color)
            self.canvas.itemconfig(self.glow_arc, outline=glow_color)
            if self.lbl_text:
                self.lbl_text.configure(text_color=text_color)
        except Exception:
            pass

    def set_text(self, text: str):
        if self.lbl_text:
            self.lbl_text.configure(text=text)

    def start(self):
        """Starts rotating with relaxed animation."""
        if self.is_running:
            return
        self.is_running = True
        self._update_canvas_bg()
        self._animate()

    def stop(self):
        """Stops rotating cleanly."""
        self.is_running = False
        if self._timer_id:
            try:
                self.after_cancel(self._timer_id)
            except Exception:
                pass
            self._timer_id = None

    def _animate(self):
        """Relaxed, smooth animation cycle: 50ms interval, 6-degree steps (120 deg/sec)."""
        if not self.is_running:
            return

        self.angle = (self.angle + 6) % 360
        try:
            self.canvas.itemconfig(self.glow_arc, start=(self.angle - 6) % 360)
            self.canvas.itemconfig(self.spinner_arc, start=self.angle)
            self._timer_id = self.after(50, self._animate)
        except Exception:
            self.is_running = False
