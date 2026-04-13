import tkinter as tk
from tkinter import filedialog
import subprocess
import os
import threading
import math
import json
import google.generativeai as genai
from PIL import Image, ExifTags

RUST_BINARY = os.path.join(os.getcwd(), "target/release/ai_image_detector")
CONFIG_FILE = 'config.json'


BG_DARK    = "#05080F" 
BG_PANEL   = "#0D1421"
BG_CARD    = "#151F32"
ACCENT     = "#00FFD1"
ACCENT_DIM = "#00B393"
ACCENT2    = "#0066FF"
DANGER     = "#FF3864"
DANGER_DIM = "#CC2D50"
SUCCESS    = "#00FFD1"
TEXT_MAIN  = "#E0F0FF"
TEXT_DIM   = "#4A6080"
TEXT_MID   = "#7A9BC0"
GRID_LINE  = "#0D2235"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            return json.load(file)
    return {"gemini_api_key": ""}

def save_config(gemini_key, window):
    config = {"gemini_api_key": gemini_key}
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file, indent=4)
    if window:
        window.destroy()

class ScannerCanvas(tk.Canvas):
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
        # رسم دوائر الرادار
        for i in range(1, 5):
            ri = r * i // 4
            col = "#0D2235" if i < 4 else "#1A3A5A"
            width = 2 if i == 4 else 1
            self.create_oval(cx-ri, cy-ri, cx+ri, cy+ri, outline=col, width=width, tags="base")
        
        # خطوط متقاطعة
        self.create_line(cx - r, cy, cx + r, cy, fill=GRID_LINE, width=1, tags="base")
        self.create_line(cx, cy - r, cx, cy + r, fill=GRID_LINE, width=1, tags="base")
        self.create_oval(cx-3, cy-3, cx+3, cy+3, fill=ACCENT, outline="", tags="base")

    def _animate(self):
        self.delete("sweep")
        cx, cy, r = self.cx, self.cy, self.size // 2 - 10
        if self.scanning:
            a_deg = self.angle
            x1 = cx + r * math.cos(math.radians(a_deg))
            y1 = cy + r * math.sin(math.radians(a_deg))
            self.create_line(cx, cy, x1, y1, fill=ACCENT, width=2, tags="sweep")
            
            for trail in range(1, 30):
                ta = a_deg - trail * 3
                alpha_hex = format(max(0, 255 - trail * 9), '02x')
                tx = cx + r * math.cos(math.radians(ta))
                ty = cy + r * math.sin(math.radians(ta))
                col = f"#00{alpha_hex}{'ff' if trail < 15 else 'd1'}"
                try:
                    self.create_line(cx, cy, tx, ty, fill=col, width=1, tags="sweep")
                except Exception:
                    pass
            self.angle = (self.angle + 4) % 360
        elif self.result == "REAL":
            self.create_oval(cx-50, cy-50, cx+50, cy+50, outline=SUCCESS, width=3, tags="sweep")
            self.create_text(cx, cy, text="✓", font=("Courier", 40, "bold"), fill=SUCCESS, tags="sweep")
        elif self.result == "FAKE":
            self.create_oval(cx-50, cy-50, cx+50, cy+50, outline=DANGER, width=3, tags="sweep")
            self.create_text(cx, cy, text="✕", font=("Courier", 40, "bold"), fill=DANGER, tags="sweep")
        self.after(35, self._animate)

    def start_scan(self):
        self.scanning = True
        self.result = None

    def stop_scan(self, result=None):
        self.scanning = False
        self.result = result

class DetectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI-SHIELD | DEEPFAKE DETECTOR")
        self.root.geometry("620x760")
        self.root.configure(bg=BG_DARK)
        self.root.resizable(False, False)
        self._build_ui()
        self._draw_grid()

    def _build_ui(self):
        self.bg_canvas = tk.Canvas(self.root, bg=BG_DARK, highlightthickness=0, width=620, height=760)
        self.bg_canvas.place(x=0, y=0)
        
        # --- Header ---
        hdr = tk.Frame(self.root, bg=BG_DARK)
        hdr.place(x=0, y=0, width=620, height=70)
        tk.Label(hdr, text="AI", font=("Courier", 24, "bold"), fg=ACCENT, bg=BG_DARK).place(x=30, y=12)
        tk.Label(hdr, text="-SHIELD", font=("Courier", 24, "bold"), fg=TEXT_MAIN, bg=BG_DARK).place(x=70, y=12)
        tk.Label(hdr, text="v3.0 · HYBRID FORENSICS", font=("Courier", 9), fg=TEXT_DIM, bg=BG_DARK).place(x=32, y=46)
        
        # API Button with Hover
        self.settings_btn = tk.Button(hdr, text="⚙️ API", font=("Courier", 9, "bold"), 
                                      fg=BG_DARK, bg=TEXT_DIM, activebackground=ACCENT, 
                                      bd=0, cursor="hand2", command=self.open_settings, padx=8, pady=2)
        self.settings_btn.place(x=420, y=22)
        self.settings_btn.bind("<Enter>", lambda e: self.settings_btn.config(bg=ACCENT, fg=BG_DARK))
        self.settings_btn.bind("<Leave>", lambda e: self.settings_btn.config(bg=TEXT_DIM, fg=BG_DARK))

        self.status_pill = tk.Label(hdr, text="● READY", font=("Courier", 9, "bold"), fg=ACCENT, bg=BG_PANEL, padx=10, pady=4)
        self.status_pill.place(x=490, y=22)
        
        sep = tk.Canvas(self.root, bg=BG_DARK, highlightthickness=0, width=620, height=2)
        sep.place(x=0, y=68)
        sep.create_line(0, 1, 620, 1, fill=GRID_LINE, width=1)
        
        # --- Scanner Area ---
        scan_frame = tk.Frame(self.root, bg=BG_DARK)
        scan_frame.place(x=0, y=78, width=620, height=250)
        
        # Frame for Radar
        radar_border = tk.Frame(scan_frame, bg=BG_PANEL, bd=1, relief="solid")
        radar_border.place(x=195, y=10, width=230, height=230)
        self.scanner = ScannerCanvas(radar_border, size=220)
        self.scanner.place(x=4, y=4)
        
        tk.Label(scan_frame, text="CORE ANALYSIS ENGINE", font=("Courier", 8), fg=TEXT_DIM, bg=BG_DARK).place(x=235, y=245)
        
        # --- Main Button ---
        btn_frame = tk.Frame(self.root, bg=BG_DARK)
        btn_frame.place(x=0, y=340, width=620, height=60)
        self.btn = tk.Button(btn_frame, text="◈  SELECT IMAGE  ◈", font=("Courier", 14, "bold"), 
                             fg=BG_DARK, bg=ACCENT, activebackground=ACCENT_DIM, activeforeground=BG_DARK, 
                             bd=0, cursor="hand2", command=self.start, padx=30, pady=12)
        self.btn.place(relx=0.5, rely=0.5, anchor="center")
        self.btn.bind("<Enter>", lambda e: self.btn.config(bg=TEXT_MAIN))
        self.btn.bind("<Leave>", lambda e: self.btn.config(bg=ACCENT))

        # --- Stats Area ---
        stats_frame = tk.Frame(self.root, bg=BG_PANEL, highlightbackground=GRID_LINE, highlightthickness=1)
        stats_frame.place(x=20, y=420, width=580, height=70)
        tk.Label(stats_frame, text="C00 VARIANCE", font=("Courier", 8), fg=TEXT_DIM, bg=BG_PANEL).place(x=30, y=10)
        self.c00_val = tk.Label(stats_frame, text="—", font=("Courier", 22, "bold"), fg=ACCENT, bg=BG_PANEL)
        self.c00_val.place(x=30, y=28)
        tk.Label(stats_frame, text="C11 VARIANCE", font=("Courier", 8), fg=TEXT_DIM, bg=BG_PANEL).place(x=220, y=10)
        self.c11_val = tk.Label(stats_frame, text="—", font=("Courier", 22, "bold"), fg=ACCENT, bg=BG_PANEL)
        self.c11_val.place(x=220, y=28)
        tk.Label(stats_frame, text="THRESHOLD", font=("Courier", 8), fg=TEXT_DIM, bg=BG_PANEL).place(x=410, y=10)
        tk.Label(stats_frame, text="25.00", font=("Courier", 22, "bold"), fg=TEXT_MID, bg=BG_PANEL).place(x=410, y=28)
        
        # --- Verdict Label ---
        self.verdict_frame = tk.Frame(self.root, bg=BG_DARK)
        self.verdict_frame.place(x=20, y=500, width=580, height=40)
        self.verdict_label = tk.Label(self.verdict_frame, text="AWAITING ANALYSIS", font=("Courier", 18, "bold"), fg=TEXT_DIM, bg=BG_DARK)
        self.verdict_label.place(relx=0.5, rely=0.5, anchor="center")
        
        log_outer = tk.Frame(self.root, bg=BG_CARD, highlightbackground=GRID_LINE, highlightthickness=1)
        log_outer.place(x=20, y=550, width=580, height=190)
        tk.Label(log_outer, text="TERMINAL LOG", font=("Courier", 8, "bold"), fg=TEXT_DIM, bg=BG_CARD).place(x=10, y=5)
        self.log_text = tk.Text(log_outer, font=("Courier", 9), fg=ACCENT, bg=BG_CARD, insertbackground=ACCENT, 
                                selectbackground=ACCENT2, bd=0, padx=10, pady=4, wrap=tk.WORD, state="disabled")
        self.log_text.place(x=0, y=25, width=580, height=160)
        
        self.log_text.tag_configure("info",    foreground=TEXT_MID)
        self.log_text.tag_configure("success", foreground=SUCCESS)
        self.log_text.tag_configure("error",   foreground=DANGER)
        self.log_text.tag_configure("warn",    foreground="#FFB800")
        self.log_text.tag_configure("accent",  foreground=ACCENT)

    def _draw_grid(self):
        c = self.bg_canvas
        for x in range(0, 620, 40):
            c.create_line(x, 0, x, 760, fill=BG_PANEL, width=1)
        for y in range(0, 760, 40):
            c.create_line(0, y, 620, y, fill=BG_PANEL, width=1)

    def open_settings(self):
        settings_win = tk.Toplevel(self.root)
        settings_win.title("API SETTINGS")
        settings_win.geometry("460x200")
        
        settings_win.configure(bg=BG_DARK)
        settings_win.resizable(False, False)
        settings_win.transient(self.root)
        settings_win.grab_set()

        current_config = load_config()

        tk.Label(settings_win, text="GEMINI API KEY:", font=("Courier", 10, "bold"), fg=TEXT_MAIN, bg=BG_DARK).pack(anchor="w", padx=20, pady=(20, 5))
        gemini_entry = tk.Entry(settings_win, width=45, show="*", bg=BG_CARD, fg=ACCENT, insertbackground=ACCENT, bd=1, relief="solid", font=("Courier", 10))
        gemini_entry.insert(0, current_config.get("gemini_api_key", ""))
        gemini_entry.pack(padx=20)

        def on_save():
            save_config(gemini_entry.get(), settings_win)
            self.log("Gemini API Configuration saved.", "success")

        def on_reset():
            gemini_entry.delete(0, tk.END)
            save_config("", None)
            self.log("Gemini API Key has been reset.", "warn")

        btn_frame = tk.Frame(settings_win, bg=BG_DARK)
        btn_frame.pack(pady=25)

        save_btn = tk.Button(btn_frame, text="SAVE", font=("Courier", 10, "bold"), fg=BG_DARK, bg=SUCCESS, 
                             activebackground=ACCENT_DIM, bd=0, cursor="hand2", command=on_save, width=12, pady=5)
        save_btn.grid(row=0, column=0, padx=10)

        reset_btn = tk.Button(btn_frame, text="RESET KEY", font=("Courier", 10, "bold"), fg=TEXT_MAIN, bg=DANGER, 
                              activebackground=DANGER_DIM, bd=0, cursor="hand2", command=on_reset, width=12, pady=5)
        reset_btn.grid(row=0, column=1, padx=10)

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

    def start(self):
        path = filedialog.askopenfilename(
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.tif *.tiff *.webp"),
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
            
            threading.Thread(target=self.process, args=(path,), daemon=True).start()

    def _run_gemini_analysis(self, img_path, rust_verdict, rust_diff):
        config = load_config()
        api_key = config.get("gemini_api_key", "")
        
        if not api_key:
            self.log("Skipping AI Scan: API key not found.", "warn")
            return None, None

        self.log("Initiating Deep AI Contextual Scan...", "accent")
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            img = Image.open(img_path)
            
            exif_report = "No EXIF Metadata found (Common in screenshots, web downloads, or AI)."
            try:
                exif_data = img._getexif()
                if exif_data:
                    extracted = []
                    for tag_id, value in exif_data.items():
                        tag = ExifTags.TAGS.get(tag_id, tag_id)
                        if tag in ['Make', 'Model', 'Software', 'DateTimeOriginal']:
                            extracted.append(f"{tag}: {value}")
                    if extracted:
                        exif_report = " | ".join(extracted)
            except Exception:
                exif_report = "Error reading EXIF data."
            
            self.log(f"Metadata: {exif_report}", "info")

            # البرومبت الهندسي الهجين مع ميزة حق النقض (Veto Power)
            prompt = f"""
            You are an expert digital forensic analyst. We have scanned this image using a local physics engine.
            
            ENGINE DATA:
            1. Mathematical Pixel Variance Difference: {rust_diff:.2f} 
            (Note: High variance > 10.0 USUALLY means AI generation grids, BUT it can also be caused by severe JPEG compression, copy-pasting, or screenshots).
            2. Engine Preliminary Verdict: {rust_verdict}
            3. EXIF Metadata: {exif_report}
            
            YOUR TASK:
            Your job is to provide the FINAL verdict. You must synthesize the mathematical data with your visual analysis.
            - If the engine says FAKE and the image looks artificially generated (weird lighting, melting textures, logic errors), confirm it is FAKE.
            - VETO POWER: If the engine says FAKE due to high variance, BUT the image is clearly a normal, real-world photograph that just looks heavily compressed, screenshotted, or cropped, you are ALLOWED to override the engine and declare it REAL.
            - WARNING: DO NOT trust watermarks or logos.
            
            Format exactly like this on the first line:
            VERDICT: FAKE (or) VERDICT: REAL
            (Provide a 2-3 sentence explanation justifying your final decision based on both the math and visual evidence).
            """
            
            response = model.generate_content([prompt, img])
            text = response.text.strip()
            
            verdict = "INCONCLUSIVE"
            if "VERDICT: FAKE" in text.upper()[:15]:
                verdict = "FAKE"
            elif "VERDICT: REAL" in text.upper()[:15]:
                verdict = "REAL"
                
            return verdict, text
        except Exception as e:
            self.log(f"Gemini API Error: {str(e)}", "error")
            return None, None

    def process(self, img_path):
        try:
            self.log(f"Target: {os.path.basename(img_path)}", "accent")
            self.log("Phase 1: Local Rust Engine Analysis…")
            
            rust_verdict = "ERROR"
            diff = 0.0
            
            if not os.path.exists(RUST_BINARY):
                self.log("Rust binary not found! Skipping Phase 1.", "warn")
            else:
                proc = subprocess.run([RUST_BINARY, img_path], capture_output=True, text=True, timeout=10)
                stats = proc.stdout.strip().split(',')
                if len(stats) >= 3:
                    c00, c11 = float(stats[0]), float(stats[2])
                    self.root.after(0, lambda: self.c00_val.configure(text=f"{c00:.2f}", fg=SUCCESS if c00 >= 25 else DANGER))
                    self.root.after(0, lambda: self.c11_val.configure(text=f"{c11:.2f}", fg=SUCCESS if c11 >= 25 else DANGER))
                    self.log(f"Rust Output -> C00={c00:.2f}  C11={c11:.2f}")

                    diff = abs(c00 - c11)
                    if not (c00 > 25.0 and c11 > 25.0):
                        rust_verdict = "FAKE"
                        self.log(f"Status: FAKE (Smooth texture, Diff={diff:.2f})")
                    elif diff > 10.0:
                        rust_verdict = "FAKE"
                        self.log(f"Status: FAKE (Anisotropic grid detected, Diff={diff:.2f})")
                    else:
                        rust_verdict = "REAL"
                        self.log(f"Status: REAL (Natural noise, Diff={diff:.2f})")

            gemini_verdict, explanation = self._run_gemini_analysis(img_path, rust_verdict, diff)
            
            final_verdict = rust_verdict
            if gemini_verdict:
                self.log("--- AI FORENSIC REPORT ---", "warn")
                for line in explanation.split('\n'):
                    if line.strip():
                        self.log(line.strip(), "success" if gemini_verdict=="REAL" else "error")
                
                if gemini_verdict in ["REAL", "FAKE"]:
                    final_verdict = gemini_verdict

            self._finalize(final_verdict)
                
        except Exception as e:
            self.log(f"System Error: {str(e)}", "error")
            self._finalize("ERROR", DANGER)

    def _finalize(self, verdict, color=None):
        if color is None:
            color = SUCCESS if verdict == "REAL" else DANGER
        self.scanner.stop_scan(result=verdict if verdict in ("REAL","FAKE") else None)
        label_map = {
            "REAL":  "✓ AUTHENTIC IMAGE",
              "FAKE":  "✕ AI GENERATED",
            "ERROR": "⚠ ANALYSIS FAILED",
        }
        self.root.after(0, lambda: self._set_verdict(
               label_map.get(verdict, verdict), color))
        self.root.after(0, lambda: self._set_status(
            "COMPLETE" if verdict != "ERROR" else "ERROR", color))

if __name__ == "__main__":
    root = tk.Tk()
    app = DetectorApp(root)
    root.mainloop()