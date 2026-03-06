import tkinter as tk
from tkinter import filedialog
import subprocess
import os
import requests
import json
import threading
import math
import time

# --- Core Settings ---
from secrets import NVIDIA_API_KEY as API_KEY

INVOKE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
RUST_BINARY = os.path.join(os.getcwd(), "target/release/ai_image_detector")

# --- Color Palette ---
BG_DARK    = "#080C14"
BG_PANEL   = "#0D1421"
BG_CARD    = "#111927"
ACCENT     = "#00FFD1"
ACCENT2    = "#0066FF"
DANGER     = "#FF3864"
SUCCESS    = "#00FFD1"
TEXT_MAIN  = "#E0F0FF"
TEXT_DIM   = "#4A6080"
TEXT_MID   = "#7A9BC0"
GRID_LINE  = "#0D2235"

class ScannerCanvas(tk.Canvas):
    """Animated scanner / radar widget."""
    def __init__(self, parent, size=220, **kwargs):
        super().__init__(parent, width=size, height=size,
                         bg=BG_DARK, highlightthickness=0, **kwargs)
        self.size = size
        self.cx = size // 2
        self.cy = size // 2
        self.angle = 0
        self.scanning = False
        self.result = None  
        self._draw_base()
        self._animate()

    def _draw_base(self):
        self.delete("base")
        cx, cy, r = self.cx, self.cy, self.size // 2 - 10
        # Rings
        for i in range(1, 5):
            ri = r * i // 4
            col = "#0D2235" if i < 4 else "#0D3050"
            self.create_oval(cx-ri, cy-ri, cx+ri, cy+ri,
                             outline=col, width=1, tags="base")
        # Cross hairs
        self.create_line(cx - r, cy, cx + r, cy, fill=GRID_LINE, width=1, tags="base")
        self.create_line(cx, cy - r, cx, cy + r, fill=GRID_LINE, width=1, tags="base")
        # Center dot
        self.create_oval(cx-3, cy-3, cx+3, cy+3,
                         fill=ACCENT, outline="", tags="base")

    def _animate(self):
        self.delete("sweep")
        cx, cy, r = self.cx, self.cy, self.size // 2 - 10

        if self.scanning:
            # Sweep arc
            a_deg = self.angle
            x1 = cx + r * math.cos(math.radians(a_deg))
            y1 = cy + r * math.sin(math.radians(a_deg))
            self.create_line(cx, cy, x1, y1,
                             fill=ACCENT, width=2, tags="sweep")
            # Fading trail
            for trail in range(1, 30):
                ta = a_deg - trail * 3
                alpha_hex = format(max(0, 255 - trail * 9), '02x')
                tx = cx + r * math.cos(math.radians(ta))
                ty = cy + r * math.sin(math.radians(ta))
                col = f"#00{alpha_hex}{'ff' if trail < 15 else 'd1'}"
                try:
                    self.create_line(cx, cy, tx, ty,
                                     fill=col, width=1, tags="sweep")
                except Exception:
                    pass
            self.angle = (self.angle + 4) % 360

        elif self.result == "REAL":
            # Green checkmark circle
            self.create_oval(cx-50, cy-50, cx+50, cy+50,
                             outline=SUCCESS, width=3, tags="sweep")
            self.create_text(cx, cy, text="✓", font=("Helvetica", 36, "bold"),
                             fill=SUCCESS, tags="sweep")

        elif self.result == "FAKE":
            # Red X circle
            self.create_oval(cx-50, cy-50, cx+50, cy+50,
                             outline=DANGER, width=3, tags="sweep")
            self.create_text(cx, cy, text="✕", font=("Helvetica", 36, "bold"),
                             fill=DANGER, tags="sweep")

        self.after(40, self._animate)

    def start_scan(self):
        self.scanning = True
        self.result = None

    def stop_scan(self, result=None):
        self.scanning = False
        self.result = result


class DetectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DEEPFAKE DETECTOR")
        self.root.geometry("620x760")
        self.root.configure(bg=BG_DARK)
        self.root.resizable(False, False)

        self._build_ui()
        self._draw_grid()

    # ── UI Construction ──────────────────────────────────────────────

    def _build_ui(self):
        # Background canvas for grid
        self.bg_canvas = tk.Canvas(self.root, bg=BG_DARK,
                                   highlightthickness=0,
                                   width=620, height=760)
        self.bg_canvas.place(x=0, y=0)

        # ── Header ──
        hdr = tk.Frame(self.root, bg=BG_DARK)
        hdr.place(x=0, y=0, width=620, height=70)

        tk.Label(hdr, text="DEEPFAKE", font=("Courier", 22, "bold"),
                 fg=ACCENT, bg=BG_DARK).place(x=30, y=14)
        tk.Label(hdr, text="DETECTOR", font=("Courier", 22, "bold"),
                 fg=TEXT_MAIN, bg=BG_DARK).place(x=170, y=14)
        tk.Label(hdr, text="v2.0 · AI FORENSICS",
                 font=("Courier", 9), fg=TEXT_DIM, bg=BG_DARK).place(x=31, y=46)

        # Top-right status pill
        self.status_pill = tk.Label(hdr, text="● READY",
                                    font=("Courier", 9, "bold"),
                                    fg=ACCENT, bg=BG_PANEL,
                                    padx=10, pady=4)
        self.status_pill.place(x=490, y=22)

        # Separator line
        sep = tk.Canvas(self.root, bg=BG_DARK, highlightthickness=0,
                        width=620, height=2)
        sep.place(x=0, y=68)
        sep.create_line(0, 1, 620, 1, fill=ACCENT2, width=1)

        # ── Scanner Section ──
        scan_frame = tk.Frame(self.root, bg=BG_DARK)
        scan_frame.place(x=0, y=78, width=620, height=250)

        self.scanner = ScannerCanvas(scan_frame, size=220)
        self.scanner.place(x=200, y=15)

        # Labels around scanner
        tk.Label(scan_frame, text="SCAN ENGINE",
                 font=("Courier", 8), fg=TEXT_DIM, bg=BG_DARK).place(x=225, y=240)

        # ── File Button ──
        btn_frame = tk.Frame(self.root, bg=BG_DARK)
        btn_frame.place(x=0, y=326, width=620, height=60)

        self.btn = tk.Button(btn_frame,
                             text="◈  SELECT IMAGE  ◈",
                             font=("Courier", 13, "bold"),
                             fg=BG_DARK, bg=ACCENT,
                             activebackground="#00CCB0",
                             activeforeground=BG_DARK,
                             bd=0, cursor="hand2",
                             command=self.start,
                             padx=24, pady=10)
        self.btn.place(relx=0.5, rely=0.5, anchor="center")

        # ── Stats Panel ──
        stats_frame = tk.Frame(self.root, bg=BG_PANEL,
                               highlightbackground=ACCENT2,
                               highlightthickness=1)
        stats_frame.place(x=20, y=400, width=580, height=70)

        tk.Label(stats_frame, text="C00 VARIANCE",
                 font=("Courier", 8), fg=TEXT_DIM, bg=BG_PANEL).place(x=30, y=10)
        self.c00_val = tk.Label(stats_frame, text="—",
                                font=("Courier", 22, "bold"),
                                fg=ACCENT, bg=BG_PANEL)
        self.c00_val.place(x=30, y=28)

        tk.Label(stats_frame, text="C11 VARIANCE",
                 font=("Courier", 8), fg=TEXT_DIM, bg=BG_PANEL).place(x=220, y=10)
        self.c11_val = tk.Label(stats_frame, text="—",
                                font=("Courier", 22, "bold"),
                                fg=ACCENT, bg=BG_PANEL)
        self.c11_val.place(x=220, y=28)

        tk.Label(stats_frame, text="THRESHOLD",
                 font=("Courier", 8), fg=TEXT_DIM, bg=BG_PANEL).place(x=410, y=10)
        tk.Label(stats_frame, text="25.00",
                 font=("Courier", 22, "bold"),
                 fg=TEXT_MID, bg=BG_PANEL).place(x=410, y=28)

        # ── Verdict Banner ──
        self.verdict_frame = tk.Frame(self.root, bg=BG_DARK)
        self.verdict_frame.place(x=20, y=484, width=580, height=60)

        self.verdict_label = tk.Label(self.verdict_frame,
                                      text="AWAITING ANALYSIS",
                                      font=("Courier", 18, "bold"),
                                      fg=TEXT_DIM, bg=BG_DARK)
        self.verdict_label.place(relx=0.5, rely=0.5, anchor="center")

        # ── Log Panel ──
        log_outer = tk.Frame(self.root, bg=BG_PANEL,
                             highlightbackground=GRID_LINE,
                             highlightthickness=1)
        log_outer.place(x=20, y=556, width=580, height=180)

        tk.Label(log_outer, text="SYSTEM LOG",
                 font=("Courier", 8, "bold"), fg=TEXT_DIM, bg=BG_PANEL).place(x=10, y=8)

        self.log_text = tk.Text(log_outer,
                                font=("Courier", 9),
                                fg=ACCENT, bg=BG_PANEL,
                                insertbackground=ACCENT,
                                selectbackground=ACCENT2,
                                bd=0, padx=10, pady=4,
                                wrap=tk.WORD,
                                state="disabled")
        self.log_text.place(x=0, y=26, width=580, height=150)

        # Tag colors
        self.log_text.tag_configure("info",    foreground=TEXT_MID)
        self.log_text.tag_configure("success", foreground=SUCCESS)
        self.log_text.tag_configure("error",   foreground=DANGER)
        self.log_text.tag_configure("warn",    foreground="#FFB800")
        self.log_text.tag_configure("accent",  foreground=ACCENT)

    def _draw_grid(self):
        c = self.bg_canvas
        for x in range(0, 620, 30):
            c.create_line(x, 0, x, 760, fill=GRID_LINE, width=1)
        for y in range(0, 760, 30):
            c.create_line(0, y, 620, y, fill=GRID_LINE, width=1)

    # ── Logging ─────────────────────────────────────────────────────

    def log(self, text, tag="info"):
        self.log_text.configure(state="normal")
        prefix = "> "
        self.log_text.insert(tk.END, prefix + text + "\n", tag)
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")
        self.root.update_idletasks()

    def _set_status(self, text, color=ACCENT):
        self.status_pill.configure(text=f"● {text}", fg=color)

    def _set_verdict(self, text, color):
        self.verdict_label.configure(text=text, fg=color)

    # ── Main Flow ────────────────────────────────────────────────────

    def start(self):
        path = filedialog.askopenfilename(
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.tif *.tiff"),
                       ("All files", "*.*")])
        if path:
            self.log_text.configure(state="normal")
            self.log_text.delete(1.0, tk.END)
            self.log_text.configure(state="disabled")
            self.c00_val.configure(text="—", fg=ACCENT)
            self.c11_val.configure(text="—", fg=ACCENT)
            self._set_verdict("ANALYZING…", TEXT_MID)
            self._set_status("SCANNING", "#FFB800")
            self.scanner.start_scan()
            threading.Thread(target=self.process,
                             args=(path,), daemon=True).start()

    def process(self, img_path):
        try:
            self.log(f"Loading: {os.path.basename(img_path)}", "accent")

            # Rust binary check
            self.log("Checking Rust binary…")
            if not os.path.exists(RUST_BINARY):
                self.log("Rust binary not found!", "error")
                self._finalize("ERROR", DANGER)
                return

            self.log(f"Running Rust analyzer…", "info")
            proc = subprocess.run([RUST_BINARY, img_path],
                                  capture_output=True, text=True, timeout=10)

            stats = proc.stdout.strip().split(',')
            if len(stats) < 3:
                self.log("Unexpected Rust output.", "error")
                self._finalize("ERROR", DANGER)
                return

            c00, c11 = float(stats[0]), float(stats[2])
            self.root.after(0, lambda: self.c00_val.configure(
                text=f"{c00:.2f}",
                fg=SUCCESS if c00 >= 25 else DANGER))
            self.root.after(0, lambda: self.c11_val.configure(
                text=f"{c11:.2f}",
                fg=SUCCESS if c11 >= 25 else DANGER))
            self.log(f"C00={c00:.2f}  C11={c11:.2f}", "accent")
# --- Advanced Math Logic (Symmetry Check) ---
            diff = abs(c00 - c11)
            is_high_variance = (c00 > 25.0 and c11 > 25.0)
            is_suspiciously_uniform = (diff < 10.0) # فرق أقل من 10 يعني ضجيج اصطناعي

            self.log("Connecting to AI model…")
            
            # 1. تحديث الـ Prompt بالقواعد المتقدمة
            prompt = (f"Stats: C00={c00}, C11={c11}, Difference={diff:.2f}. "
                      "CRITICAL RULES: "
                      "1) If values < 25 -> FAKE (Too smooth). "
                      "2) If values > 25 BUT Difference < 10 -> FAKE (Artificial uniform noise). "
                      "3) If values > 25 AND Difference > 10 -> REAL (Natural chaotic noise). "
                      "Based on the rules, answer in exactly 1 word: REAL or FAKE.")
            
            headers = {"Authorization": f"Bearer {API_KEY}"}
            payload = {
                "model": "meta/llama-3.1-8b-instruct",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 10,
                "temperature": 0.0 # روبوتي صارم
            }

            try:
                resp = requests.post(INVOKE_URL, headers=headers, json=payload, timeout=15)
                if resp.status_code == 200:
                    ai_result = resp.json()['choices'][0]['message']['content'].strip().upper()
                    
                    # 2. الفيتو الرياضي (Math Override) لحماية النظام من خداع AI
                    if is_high_variance and is_suspiciously_uniform and "REAL" in ai_result:
                        self.log("AI fooled by artificial grain. Overriding...", "warn")
                        ai_result = "FAKE"
                    elif is_high_variance and not is_suspiciously_uniform and "FAKE" in ai_result:
                        self.log("AI misclassified natural noise. Overriding...", "warn")
                        ai_result = "REAL"
                    elif not is_high_variance and "REAL" in ai_result:
                        self.log("AI misclassified smooth texture. Overriding...", "warn")
                        ai_result = "FAKE"

                    self.log(f"AI decision: {ai_result}", "success" if "REAL" in ai_result else "error")
                        
                    verdict = "REAL" if "REAL" in ai_result else "FAKE"
                    self._finalize(verdict)
                    return
            except Exception:
                self.log("Network unstable — using local logic.", "warn")

            # --- الخطة البديلة (Local Fallback) بالمنطق المتقدم ---
            if not is_high_variance:
                self.log("Local verdict: FAKE (Low variance — texture too smooth.)", "error")
                self._finalize("FAKE")
            elif is_high_variance and is_suspiciously_uniform:
                self.log(f"Local verdict: FAKE (Noise too uniform, Diff={diff:.2f})", "error")
                self._finalize("FAKE")
            else:
                self.log(f"Local verdict: REAL (Natural chaotic noise, Diff={diff:.2f})", "success")
                self._finalize("REAL")
        except Exception as e:
            self.log(f"Fatal: {str(e)}", "error")
            self._finalize("ERROR", DANGER)

    def _finalize(self, verdict, color=None):
        if color is None:
            color = SUCCESS if verdict == "REAL" else DANGER
        self.scanner.stop_scan(result=verdict if verdict in ("REAL","FAKE") else None)
        label_map = {
            "REAL":  "✓  AUTHENTIC IMAGE",
            "FAKE":  "✕  AI GENERATED",
            "ERROR": "⚠  ANALYSIS FAILED",
        }
        self.root.after(0, lambda: self._set_verdict(
            label_map.get(verdict, verdict), color))
        self.root.after(0, lambda: self._set_status(
            "COMPLETE" if verdict != "ERROR" else "ERROR", color))


if __name__ == "__main__":
    root = tk.Tk()
    app = DetectorApp(root)
    root.mainloop() 