# 🛡️ Deepfake Detector (AI-Shield) - Hybrid Edition

**Deepfake Detector** is a high-performance, hybrid forensic tool designed to detect AI-generated images. It combines the raw, offline computational speed of **Rust** (for physical noise analysis) with the advanced multimodal cognitive capabilities of **Google's Gemini Pro API** (for semantic and contextual forensics).

By analyzing both the microscopic physical properties of image noise (covariance matrices) and the macroscopic semantic logic of the scene (lighting, anatomical consistency), this tool provides an enterprise-grade, two-phase pipeline to catch deepfakes.

## ✨ Key Features

* **Two-Phase Hybrid Architecture:**
  * **Phase 1 (Local/Offline):** A Rust-compiled binary performs lightning-fast texture and spatial gradient analysis.
  * **Phase 2 (Cloud/AI):** Integration with the Gemini Pro API for deep contextual scanning, examining biological/architectural consistency and lighting logic.
* **Animated Cyber-UI:** Features a custom-built Tkinter Canvas radar scanner with real-time visual feedback and an integrated system log.
* **BYOK (Bring Your Own Key) Privacy:** API keys are managed locally by the user via a secure GUI settings panel and saved in a local `config.json`.
* **Isotropic vs. Anisotropic Heuristics:** Employs advanced spatial gradient analysis to differentiate natural chaotic noise from artificial geometric grid artifacts.

*(Optional: Add a screenshot or GIF of your UI running here)*

## 📂 Project Structure

```text
AI_IMAGE_DETECTOR/
├── src/                # Rust source code (main.rs)
├── target/             # Compiled Rust binaries (auto-generated)
├── venv/               # Python virtual environment
├── main_app.py         # Python GUI and Core Logic
├── config.json         # Local API Key storage (auto-generated)
├── Cargo.toml          # Rust dependencies and config
├── Cargo.lock          # Rust version lockfile
└── README.md           # Project documentation

```

## 🚀 Installation & Setup

**Prerequisites**

* Rust & Cargo installed.
* Python 3.10+ installed.

**1. Build the Rust Engine**
The Python script relies on a compiled Rust binary. Build it first by running this in the root directory:

```bash
cargo build --release

```

**2. Set Up the Python Environment**
Create a virtual environment and install the required libraries for the UI and the Gemini AI engine:

```bash
python -m venv venv
# On Windows use: venv\Scripts\activate
source venv/bin/activate  

pip install Pillow google-generativeai

```

**3. Run the Scanner**
With the virtual environment activated, launch the UI:

```bash
python main_app.py

```

*Note: Upon first launch, click the **"⚙️ API"** button in the top right to securely enter your Gemini API Key.*

## 🧠 The Science: How It Works

Detecting modern AI images requires analyzing both the underlying physical light simulation and the logical composition of the image.

### Phase 1: Local Texture Analysis (Rust)

The Rust engine extracts the texture covariance matrix, specifically C00 (X-axis variance) and C11 (Y-axis variance).

1. **The Smoothness Check (Thresholding):** AI generators often produce "perfect" pixels lacking natural entropy. If variance is < 25.0, it is flagged.
2. **The Noise Symmetry Check:** * **Authentic Photographs (Isotropic Noise):** Real sensors capture light chaotically but uniformly. Difference is exceptionally low (`abs(C00 - C11) < 10.0`).
* **AI-Generated Images (Anisotropic Artifacts):** Advanced models use upsampling grids, leaving directional footprints resulting in highly asymmetrical variance.



### Phase 2: Semantic & Contextual Analysis (Gemini Pro)

If configured, the image is passed to a multimodal LLM (Gemini Pro) with a strict forensic prompt. The AI acts as a digital investigator, analyzing:

* **Lighting Logic:** Do the shadows match the implied light sources?
* **Anatomical/Architectural Consistency:** Are there AI hallucinations (e.g., extra fingers, melting background structures, nonsensical text)?
* **Verdict & Explanation:** The engine outputs a final `REAL` or `FAKE` verdict alongside a concise, readable forensic report directly in the System Log.

## 📄 License

This project is open-source and available under the MIT License.