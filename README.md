# 🛡️ Deepfake Detector (AI-Shield)

**Deepfake Detector** is a high-performance, **100% offline** hybrid forensic tool designed to detect AI-generated images. It combines the raw computational speed of **Rust** with a modern, animated **Python** GUI. 

By analyzing the physical properties of image noise using covariance matrices and spatial gradients, this tool deterministicly separates authentic camera sensor noise from artificial neural network artifacts—without needing an internet connection or cloud APIs.

## ✨ Key Features
* **100% Offline Forensics:** Zero data leaves your machine. Maximum privacy and instant sub-second execution.
* **Hybrid Architecture:** Uses a Rust-compiled binary for lightning-fast image texture analysis and a Python backend for logic and UI.
* **Animated Cyber-UI:** Features a custom-built Tkinter Canvas radar scanner with real-time visual feedback.
* **Isotropic vs. Anisotropic Heuristics:** Employs advanced spatial gradient analysis to differentiate natural chaotic noise from artificial geometric grid artifacts.



## 📂 Project Structure

```text
AI_IMAGE_DETECTOR/
├── src/                # Rust source code (main.rs)
├── target/             # Compiled Rust binaries (auto-generated)
├── venv/               # Python virtual environment
├── main_app.py         # Python GUI and Core Logic
├── Cargo.toml          # Rust dependencies and config
├── Cargo.lock          # Rust version lockfile
└── README.md           # Project documentation

```

## 🚀 Installation & Setup

### Prerequisites

* [Rust & Cargo](https://www.rust-lang.org/tools/install) installed.
* [Python 3.10+](https://www.python.org/downloads/) installed.

### 1. Build the Rust Engine

The Python script relies on a compiled Rust binary. Build it first by running this in the root directory:

```bash
cargo build --release

```

### 2. Set Up the Python Environment

Create a virtual environment and install the required UI library (Pillow):

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

pip install Pillow

```

### 3. Run the Scanner

With the virtual environment activated, launch the UI:

```bash
python main_app.py

```

## 🧠 The Science: Isotropic vs. Anisotropic Noise

Detecting modern AI images requires analyzing the underlying physical light simulation. The Rust engine extracts the texture covariance matrix, specifically the $C_{00}$ (X-axis variance) and $C_{11}$ (Y-axis variance).

### 1. The Smoothness Check (Thresholding)

AI generators often produce "perfect" pixels lacking natural entropy.

* If $C_{00}$ or $C_{11}$ is **< 25.0**: Flagged immediately as **FAKE**.

### 2. The Noise Symmetry Check (Differential Variance)

If the variance is high (> 25.0), the engine calculates the difference: `abs(C00 - C11)`.

* **Authentic Photographs (Isotropic Noise):** Real camera sensors capture physical light chaotically but uniformly in all directions. The difference will be exceptionally low (e.g., `< 10.0`).
* **AI-Generated Images (Anisotropic Artifacts):** Advanced AI models use upsampling grids and deconvolution layers. These leave behind geometric, directional footprints, resulting in highly asymmetrical variance (e.g., `> 10.0`).

### Case Study (Real Test Data)

* **Real Image (National Geographic):** $C_{00} = 192.81$, $C_{11} = 195.00$
* *Difference:* **2.19** (Highly Isotropic ➡️ **REAL**)


* **AI Deepfake:** $C_{00} = 215.28$, $C_{11} = 186.08$
* *Difference:* **29.20** (Highly Anisotropic ➡️ **FAKE**)



## 📄 License

This project is open-source and available under the **MIT License**.
