# 🔐 StegoShield — Four-Format Steganography Lab

**A polished local-first Computer Network Security (CNS) classroom project** that hides and extracts short UTF-8 messages using **image, audio, video, and text steganography**, from a local Streamlit web interface.

> **Educational use only.** The messages are concealed, not encrypted, authenticated, or protected from steganalysis. Use only files you own or have permission to process.

## Features

| Type | Hiding method | Carrier | Encoded output | Extracts? |
| --- | --- | --- | --- | --- |
| 🖼 Image | RGB least-significant-bit substitution | PNG/JPG/BMP | **PNG** (lossless) | ✅ |
| 🎵 Audio | PCM sample LSB substitution | PCM WAV | **WAV** | ✅ |
| 🎬 Video | LSB in first decoded RGB frame | Small MP4/AVI/MOV/MKV/WebM | **MKV with FFV1** (lossless) | ✅ |
| 📝 Text | ASCII space/tab whitespace steganography | Text paragraph | **UTF-8 TXT** | ✅ |

The dashboard includes a drag-and-drop uploader, side-by-side original/stego previews for images and audio, bundled demo samples, a persistent local file vault (last eight outputs), one-click extraction from vault items, and format-specific guidance.

Each embedded secret uses a `STG1` marker, length, and CRC32 checksum for integrity checking. A checksum **does not** provide cryptographic security.

### Requirements

- Windows 10/11, or macOS/Linux
- Python **3.10–3.12** recommended
- VS Code (optional, but convenient)
- An internet connection for the initial package installation

## Run locally (Windows PowerShell in VS Code terminal)

```powershell
cd StegoShield
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

If PowerShell blocks venv activation, use the interpreter directly instead:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Your browser should open a local page, usually `http://localhost:8501`. **No API keys, database, Docker, or paid hosting required.**

## Classroom demo (all four types)

Four original test carriers are included in `samples/`. If missing, regenerate them using `python scripts/generate_samples.py`.

1. **Image:** select Image → Hide → upload `samples/sample_image.png` → enter `CNS project demo` → Hide → download the stego PNG. Switch to Extract, upload that new PNG, and show the recovered text.
2. **Audio:** select Audio → Hide → upload `samples/sample_audio.wav` → hide and download the WAV. Switch to Extract, upload the downloaded WAV, and reveal the text. Play both if desired.
3. **Video:** select Video → Hide → upload `samples/sample_video.mp4` → download the stego `.mkv`. Switch to Extract, upload **the exported MKV**, and reveal the text. Some browsers cannot preview FFV1/MKV; extraction works in the application.
4. **Text:** select Text → Hide → use the provided ordinary cover paragraph → hide and download the generated `.txt` file. Open it in Notepad and check the paragraph has **no boxed Unicode glyphs**, then switch to Extract, upload the unchanged TXT, and recover the secret text.

**Important:** The exported video is **silent** (audio tracks are not carried over). This avoids additional requirements for a classroom proof-of-concept. Editing/recompressing a stego file, especially video, can corrupt the hidden message.

### Recent file vault and privacy

After encoding, the generated file is copied to `.stegoshield_data/` so recent outputs remain accessible after restarting Streamlit. The sidebar displays up to eight recent files, with **Download** and **Decode** shortcuts. The *Manage vault* menu allows deletion of all saved files. The vault is intentionally ignored by Git. Files are stored **unencrypted** on your computer; use only classroom samples, not actual confidential messages. The vault is a local demo utility, not a secure storage system.

### Video constraints

The short-demo implementation accepts clips up to **15 seconds**, **640×480**, **30 frames/second**, and **450 frames**. The encoded output uses FFV1 video in a Matroska container so pixels can be recovered accurately. A typical MP4/H.264 conversion is **lossy** and can erase LSB data. The package `imageio-ffmpeg` provides the necessary FFmpeg binary on most Windows/macOS/Linux systems.

## Run tests

```powershell
python -m pytest -q
```

The tests check image, WAV (8/16/24/32-bit sample widths), Unicode text, real MP4→FFV1/MKV video embedding/extraction, missing-message rejection, and capacity failures.

## Repository layout

```text
StegoShield/
├── app.py                    # Premium dashboard UI
├── stegoshield/
│   ├── core.py               # Image, WAV, text, packet encoding
│   ├── history.py            # Local private file vault / recent outputs
│   └── video.py              # Video encoder/decoder via FFmpeg
├── scripts/generate_samples.py
├── tests/
├── samples/                  # Small original classroom carriers
├── requirements.txt
├── .stegoshield_data/        # Local recent files, created at runtime (ignored by git)
├── .streamlit/config.toml
├── .gitignore
├── LICENSE
└── README.md
```

## Suggested GitHub publication

```powershell
git init
git add .
git commit -m "feat: build four-format steganography demo"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/StegoShield.git
git push -u origin main
```

Create an **empty** repository named `StegoShield` on GitHub before running the final two commands. Replace `YOUR_USERNAME` with your GitHub username. Do not commit `.venv/`, user-sensitive test data, or API credentials.

## Concepts & limitations for viva

- **Steganography** hides that a secret communication exists; **cryptography** hides the content. This project does not encrypt.
- **Image** embedding changes selected RGB-channel LSBs and stores as PNG to preserve exact pixel data.
- **Audio** embedding changes the lowest bit of each PCM sample's least significant byte and preserves WAV sample characteristics.
- **Video** embedding changes bits in the first decoded frame and saves as a mathematically lossless FFV1 stream. It is not robust against re-encoding or cropping.
- **Text** encoding adds an ASCII spaces-and-tabs data line after the readable cover paragraph. Windows Notepad will not display unsupported Unicode boxes, but selecting/showing whitespace can reveal the hidden line. Editors that remove trailing spaces/tabs, reflow content or otherwise normalize text can destroy the message. This is an educational demonstration, not an undetectable or secure system.
- **Capacity:** approx. `floor(available bytes / 8) - 12` bytes for one bit per image-channel/audio sample; the 12 bytes include the packet header and CRC. Video uses only the first frame.
- **Security:** simple LSB techniques can be detected by steganalysis; CRC32 detects corruption but does not prevent tampering.

## Suggested next additions after a successful demo

A demo video, UI screenshots, brief architecture diagram, and a reference section matching the CNS assignment's seven research papers.
