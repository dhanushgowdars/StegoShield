"""StegoShield — local-first image, audio, video and text steganography lab.

Launch: python -m streamlit run app.py
For education only: hidden messages are not encrypted or authenticated.
"""
from __future__ import annotations

import html
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

import streamlit as st
import imageio_ffmpeg

from stegoshield.core import (
    StegoError, audio_capacity, image_capacity,
    encode_image, decode_image, encode_audio, decode_audio,
    encode_text, decode_text,
)
from stegoshield.history import (
    HistoryError, list_history, load_history, save_history, clear_history,
)
from stegoshield.video import video_capacity, encode_video, decode_video

BASE = Path(__file__).resolve().parent
SYMBOLS = {"Image": "🖼️", "Audio": "🎧", "Video": "🎞️", "Text": "📝"}
METHODS = {
    "Image": ("PNG / JPG / BMP", "PNG", "RGB LSB", "Image pixels carry message bits in their least significant channels."),
    "Audio": ("PCM WAV", "WAV", "PCM LSB", "Small changes to uncompressed PCM samples carry the message."),
    "Video": ("Common video formats", "MKV", "Frame LSB", "HD and high-FPS clips are automatically adapted for a short demo."),
    "Text": ("Cover paragraph", "UTF-8 TXT", "ASCII whitespace", "A final line of spaces and tabs carries data without altering the readable paragraph."),
}
EXTENSIONS = {"Image": ["png", "jpg", "jpeg", "bmp"], "Audio": ["wav"],
              "Video": ["mp4", "avi", "mov", "mkv", "webm", "m4v", "mpeg", "mpg", "wmv", "3gp", "ts"], "Text": ["txt"]}
OUTPUT_EXT = {"Image": "png", "Audio": "wav", "Video": "mkv", "Text": "txt"}
MIME = {"Image": "image/png", "Audio": "audio/wav", "Video": "video/x-matroska", "Text": "text/plain"}
SAMPLES = {"Image": "sample_image.png", "Audio": "sample_audio.wav", "Video": "sample_video.mp4"}

st.set_page_config(page_title="StegoShield | Media Security Studio", page_icon="🛡️",
                   layout="wide", initial_sidebar_state="expanded")

CSS = """
<style>
:root{--forest:#123831;--jade:#0b7d71;--mint:#d7f2e6;--ink:#172a2c;--muted:#657978;--paper:#f7f8f4;--line:#e4e9e2;--peach:#f5b783;}
html,body,.stApp,[data-testid="stMarkdownContainer"]{font-family:'Segoe UI',Arial,sans-serif;}
.stApp{background:#f7f8f4;color:var(--ink);}
.main .block-container{padding:1.65rem 2.65rem 3rem!important;max-width:1380px;}
#MainMenu,footer,[data-testid="stToolbar"]{visibility:hidden;}
/* Sidebar */
[data-testid="stSidebar"]{background:#14332e!important;border-right:1px solid #2d5044;}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] li{color:#e2f0ea;}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"]{color:#a0bbb2;}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:.48rem;}
.side-brand{padding:14px 0 16px;border-bottom:1px solid #375349;margin-bottom:12px;display:flex;align-items:center;gap:11px;}
.brand-icon{background:#d0f7e6;color:#126457;border-radius:14px;padding:10px 13px;font-size:22px;}
.brand-name{font-size:22px;color:white;font-weight:800;letter-spacing:-.5px;}
.brand-sub{color:#9ccec0;font-size:10px;letter-spacing:1.4px;font-weight:800;margin-top:2px;}
.side-label{font-size:10px;letter-spacing:1.8px;font-weight:900;color:#a2c6b8;margin:15px 0 8px;}
.side-stat{color:#e3f4ea;font-size:12px;line-height:2.1;}
.side-dot{color:#57ddb4;margin-right:7px;}
.vault-item{padding:11px 12px 9px;border:1px solid #3b5a4e;background:#1b4038;border-radius:12px;margin:10px 0 5px;}
.vault-name{font-size:12px;color:#f4fff8;font-weight:700;white-space:nowrap;text-overflow:ellipsis;overflow:hidden;}
.vault-meta{color:#b0cfc2;font-size:11px;margin-top:4px;}
.side-empty{padding:15px;text-align:center;border:1px dashed #55736a;border-radius:12px;color:#abc9bd;font-size:12px;line-height:1.7;}
[data-testid="stSidebar"] .stButton button, [data-testid="stSidebar"] .stDownloadButton button {border-radius:9px!important;min-height:35px!important;font-size:12px!important;font-weight:750!important;color:#eafff5!important;background:#27574a!important;border:1px solid #467768!important;}
[data-testid="stSidebar"] .stButton button:hover,[data-testid="stSidebar"] .stDownloadButton button:hover{background:#337764!important;color:#fff!important;}
.side-note{border-top:1px solid #38554b;color:#abc3b9;padding-top:14px;margin-top:18px;font-size:11px;line-height:1.7;}
/* New compact landing area */
.toolbar-line{display:flex;justify-content:space-between;align-items:center;gap:15px;flex-wrap:wrap;margin:0 0 17px;}
.toolbar-name{font-size:12px;letter-spacing:1.2px;font-weight:850;color:#667d77;}
.local-tag{border:1px solid #c2e8d4;background:#e9f8ed;border-radius:999px;padding:7px 12px;color:#207a59;font-size:11px;font-weight:850;}
.local-tag:before{content:'●';color:#1ea97b;margin-right:8px;}
.welcome{position:relative;overflow:hidden;display:flex;align-items:center;justify-content:space-between;gap:25px;padding:24px 28px;margin-bottom:21px;background:linear-gradient(110deg,#f0f8ed 0%,#eaf5ef 55%,#faefe3 100%);border:1px solid #d8e9df;border-radius:22px;box-shadow:0 12px 22px #113a2911;}
.welcome:after{content:'';height:210px;width:210px;border-radius:50%;border:36px solid #e7cbb84f;position:absolute;right:-92px;top:-89px;pointer-events:none;}
.welcome-copy{z-index:1;max-width:660px;}
.welcome-overline{font-size:11px;letter-spacing:1.9px;color:#168271;font-weight:900;margin-bottom:9px;}
.welcome h1{font-size:clamp(27px,3vw,38px);font-weight:800;letter-spacing:-1.4px;line-height:1.12;color:#153b34;margin:0 0 9px;}
.welcome p{color:#526d64;font-size:13px;line-height:1.7;max-width:550px;margin:0;}
.welcome-steps{display:flex;gap:9px;flex-wrap:wrap;margin-top:16px;}
.step-chip{background:#fff9;border:1px solid #c4dfd3;color:#2c6c5b;border-radius:999px;padding:6px 11px;font-size:11px;font-weight:800;}
.format-mosaic{flex-shrink:0;display:grid;grid-template-columns:repeat(2,84px);gap:8px;z-index:1;transform:rotate(-5deg);margin:0 10px 0 0;}
.mosaic-tile{display:flex;flex-direction:column;align-items:center;gap:5px;background:#fff;border:1px solid #d6e8de;border-radius:16px;padding:11px 9px;color:#275950;box-shadow:0 5px 12px #25463811;}
.mosaic-tile span{font-size:22px;}.mosaic-tile strong{font-size:10px;letter-spacing:.4px;}
/* Main sections */
.section-kicker{color:#558578;font-size:10px;font-weight:900;letter-spacing:1.8px;text-transform:uppercase;margin:18px 0 5px;}
.section-title{font-size:21px;color:#173b35;font-weight:800;letter-spacing:-.5px;margin-bottom:8px;}
[data-testid="stVerticalBlockBorderWrapper"]{background:#fff!important;border-radius:18px!important;border:1px solid #e2e9e1!important;box-shadow:0 6px 22px #1635270a;}
[data-testid="stRadio"] div[role="radiogroup"]{display:flex;gap:9px;flex-wrap:wrap;}
[data-testid="stRadio"] div[role="radiogroup"]>label{flex:1;min-width:130px;border:1px solid #e2e8e3;background:#fff;border-radius:12px;padding:11px 12px!important;cursor:pointer;}
[data-testid="stRadio"] div[role="radiogroup"]>label:has(input:checked){border-color:#148878;background:#edf9f3;box-shadow:0 0 0 2px #0b7d710a;}
[data-testid="stRadio"] div[role="radiogroup"]>label p{color:#24453f;font-size:13px;font-weight:800;}
[data-testid="stFileUploader"]{border:1.5px dashed #91c8b4;border-radius:14px;background:#f4fbf8;padding:6px;}
[data-testid="stFileUploaderDropzone"]{background:#f4fbf8!important;border:0!important;min-height:90px;}
.stTextArea textarea{background:#fcfefd;border:1px solid #dce9e1;border-radius:12px!important;}
.stButton button[kind="primary"],.stDownloadButton button[kind="primary"]{background:#0a7f71!important;color:#fff!important;border:1px solid #0a7f71!important;border-radius:12px!important;font-size:14px;font-weight:800;min-height:48px;box-shadow:0 6px 14px #0a7f7120;}
.stButton button[kind="primary"]:hover,.stDownloadButton button[kind="primary"]:hover{background:#076658!important;}
.stButton button,.stDownloadButton button{border-radius:10px;font-weight:700;}
[data-testid="stAlert"]{border-radius:12px;}
.info-card{background:#fff;border:1px solid #e3ebe4;border-radius:15px;padding:17px 18px;margin-bottom:14px;}
.info-card h3{font-size:14px;color:#173e35;font-weight:850;margin:0 0 12px;}
.info-step{display:flex;gap:11px;align-items:flex-start;margin:13px 0;}
.info-num{flex-shrink:0;background:#e2f5e9;border-radius:8px;color:#07816d;font-weight:900;font-size:11px;padding:5px 8px;}
.info-text{font-size:12px;line-height:1.6;color:#566f68;}
.tech-note{background:#fdf5e9;border:1px solid #f3dfc5;border-radius:13px;padding:15px;color:#805b35;font-size:12px;line-height:1.65;}
.meta-pill{display:inline-flex;gap:8px;background:#f2f8f4;color:#37685a;padding:7px 12px;border-radius:10px;font-size:12px;font-weight:800;margin:5px 5px 8px 0;border:1px solid #dfebe3;}
/* Prominent inline success result – intentionally next to the action button */
.result-success{background:linear-gradient(100deg,#e6f9ec,#f4fbef);border:1px solid #b6e7c7;border-left:5px solid #19a271;border-radius:14px;padding:17px 18px;margin:14px 0 12px;}
.result-title{font-weight:900;font-size:18px;color:#12644c;margin-bottom:5px;}
.result-desc{font-size:12px;line-height:1.7;color:#386e58;}
.result-grid{display:flex;gap:10px;flex-wrap:wrap;margin:10px 0;}
.result-chip{background:#f3f8f4;color:#315d52;border:1px solid #e0ece4;border-radius:10px;padding:9px 12px;font-size:12px;font-weight:750;}
.verify-box{border-radius:12px;border:1px dashed #b9d7c4;background:#f9fcf8;padding:14px;margin-top:12px;}
.verify-box strong{color:#235b48;font-size:13px;}
.footnote{border-top:1px solid #e2e8df;color:#7d9388;font-size:11px;display:flex;justify-content:space-between;gap:15px;padding-top:16px;margin-top:24px;}
@media(max-width:950px){.main .block-container{padding:1.2rem 1rem 3rem!important;}.format-mosaic{display:none;}.welcome{padding:23px 18px;}.welcome h1{font-size:29px;}}
</style>
"""


def readable_size(n: int) -> str:
    return f"{n/1024/1024:.1f} MB" if n >= 1024 * 1024 else f"{n/1024:.1f} KB"


def reset_result() -> None:
    st.session_state["last_result"] = None


def format_changed() -> None:
    reset_result()
    st.session_state["vault_selection"] = None
    st.session_state["sample_selection"] = None


def mode_changed() -> None:
    reset_result()
    st.session_state["vault_selection"] = None


def file_changed() -> None:
    reset_result()
    st.session_state["vault_selection"] = None


def use_demo(fmt: str) -> None:
    st.session_state["sample_selection"] = fmt
    st.session_state["vault_selection"] = None
    reset_result()


def select_saved(item_id: str, fmt: str) -> None:
    # Called before script rerun, so changing radio widget keys is supported.
    st.session_state["selected_format"] = fmt
    st.session_state["selected_mode"] = "Extract"
    st.session_state["vault_selection"] = item_id
    st.session_state["upload_epoch"] = st.session_state.get("upload_epoch", 0) + 1
    reset_result()


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown('''<div class="side-brand"><span class="brand-icon">⬡</span>
          <div><div class="brand-name">StegoShield</div><div class="brand-sub">LOCAL MEDIA SECURITY LAB</div></div></div>''',
                    unsafe_allow_html=True)
        st.markdown('<div class="side-label">WORKSPACE STATUS</div>', unsafe_allow_html=True)
        st.markdown('<div class="side-stat"><span class="side-dot">●</span> Processing stays on this computer<br>'
                    '<span class="side-dot">●</span> Four carrier types available<br>'
                    '<span class="side-dot">●</span> Easy message hiding and recovery</div>', unsafe_allow_html=True)
        st.markdown('<div class="side-label">RECENT GENERATED FILES</div>', unsafe_allow_html=True)
        try:
            items = list_history()
        except HistoryError as exc:
            st.error(str(exc))
            items = []
        st.caption(f"{len(items)} stored locally · up to 8 outputs")
        if not items:
            st.markdown('<div class="side-empty">▤<br>Your encoded files will appear here after you generate them.</div>',
                        unsafe_allow_html=True)
        for item in items:
            st.markdown(f'''<div class="vault-item"><div class="vault-name">{SYMBOLS.get(item["format"], "📄")}
              {html.escape(item["name"])}</div><div class="vault-meta">{html.escape(item["created"])} · {readable_size(item["size"])}</div></div>''',
                        unsafe_allow_html=True)
            try:
                _, raw = load_history(item["id"])
            except HistoryError:
                continue
            left, right = st.columns(2, gap="small")
            with left:
                st.download_button("↓ Download", data=raw, file_name=item["name"], mime=item["mime"],
                                   key=f"vault_dl_{item['id']}", use_container_width=True)
            with right:
                st.button("↗ Decode", key=f"vault_decode_{item['id']}",
                          on_click=select_saved, args=(item["id"], item["format"]), use_container_width=True)
        if items:
            with st.popover("Manage stored files", use_container_width=True):
                st.caption("These files stay on your computer.")
                if st.button("Delete all saved outputs", use_container_width=True):
                    try:
                        clear_history()
                        st.session_state["vault_selection"] = None
                        st.rerun()
                    except HistoryError as exc:
                        st.error(str(exc))
        st.markdown('<div class="side-note">SAVED ON YOUR COMPUTER<br>Use your own practice files for demonstrations.</div>',
                    unsafe_allow_html=True)



@st.cache_data(show_spinner=False, max_entries=12)
def browser_audio_preview(wav_bytes: bytes) -> bytes | None:
    """Create a browser-friendly listening preview; preserve stego WAV unchanged."""
    try:
        completed = subprocess.run(
            [
                imageio_ffmpeg.get_ffmpeg_exe(),
                "-hide_banner", "-loglevel", "error", "-nostdin",
                "-f", "wav", "-i", "pipe:0", "-vn", "-acodec", "libmp3lame",
                "-b:a", "128k", "-f", "mp3", "pipe:1",
            ],
            input=wav_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
            check=True,
        )
        return completed.stdout if completed.stdout else None
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def audio_player(wav_bytes: bytes, title: str) -> None:
    """Prefer a compatible MP3 preview, with native WAV fallback."""
    st.caption(title)
    preview = browser_audio_preview(wav_bytes)
    if preview:
        st.audio(preview, format="audio/mpeg")
    else:
        st.audio(wav_bytes, format="audio/wav")
    st.caption("Listening preview only. Use the downloadable WAV to extract your message.")

def process_standard(fmt: str, mode: str, raw: bytes | None, message: str, cover: str) -> dict:
    if mode == "Hide":
        if fmt != "Text" and raw is None:
            raise StegoError("Choose a carrier file or load a sample first.")
        if fmt == "Image":
            output = encode_image(raw, message)
        elif fmt == "Audio":
            output = encode_audio(raw, message)
        elif fmt == "Text":
            output = encode_text(cover, message).encode("utf-8")
        else:
            raise AssertionError("Video is processed separately")
        return {"format": fmt, "mode": mode, "bytes": output, "source": raw}
    if raw is None:
        raise StegoError("Upload an encoded file or select a recent output from the sidebar.")
    if fmt == "Image":
        text = decode_image(raw)
    elif fmt == "Audio":
        text = decode_audio(raw)
    elif fmt == "Text":
        text = decode_text(raw.decode("utf-8-sig"))
    else:
        raise AssertionError("Video is processed separately")
    return {"format": fmt, "mode": mode, "message": text, "source": raw if fmt == "Audio" else None}


def process_video(raw: bytes | None, suffix: str, mode: str, message: str) -> dict:
    if raw is None:
        raise StegoError("Choose a video first.")
    with tempfile.TemporaryDirectory() as temp:
        src = Path(temp) / ("input" + suffix)
        src.write_bytes(raw)
        if mode == "Hide":
            dest = Path(temp) / "stego_video.mkv"
            encode_video(str(src), str(dest), message)
            return {"format": "Video", "mode": mode, "bytes": dest.read_bytes(), "source": raw}
        recovered = decode_video(str(src))
        return {"format": "Video", "mode": mode, "message": recovered}


def render_result(result: dict) -> None:
    fmt, mode = result["format"], result["mode"]
    if mode == "Hide":
        output = result["bytes"]
        st.markdown('''<div class="result-success"><div class="result-title">✓ Message embedded successfully!</div>
          <div class="result-desc">Your file is ready. Preview and download it below.</div></div>''',
                    unsafe_allow_html=True)
        st.markdown(f'<div class="result-grid"><span class="result-chip">✓ Encoding complete</span><span class="result-chip">File: {html.escape(result["filename"])}</span><span class="result-chip">{readable_size(len(output))}</span></div>',
                    unsafe_allow_html=True)
        if fmt == "Image":
            a, b = st.columns(2, gap="medium")
            with a:
                st.caption("ORIGINAL IMAGE")
                if result.get("source"):
                    st.image(result["source"], use_container_width=True)
            with b:
                st.caption("ENCODED IMAGE · PNG")
                st.image(output, use_container_width=True)
        elif fmt == "Audio":
            a, b = st.columns(2)
            with a:
                if result.get("source"):
                    audio_player(result["source"], "ORIGINAL AUDIO")
            with b:
                audio_player(output, "ENCODED AUDIO")
            st.caption("The sample file is a one-second tone, not a voice reading the hidden text.")
        elif fmt == "Video":
            st.info("Video ready! Your hidden message is saved in the MKV file.")
        else:
            st.caption("Your visible paragraph stays unchanged. The secret is hidden using spaces and tabs.")
            st.code(result.get("cover", ""), language=None)
        st.download_button("⬇  DOWNLOAD ENCODED FILE", data=output, file_name=result["filename"],
                           mime=MIME[fmt], type="primary", use_container_width=True, key="result_download")
        st.markdown('''<div class="verify-box"><strong>Next: verify your result</strong><br>
          <span style="color:#567769;font-size:12px;line-height:1.8">Select “Reveal message” above, upload the generated file or use “Decode” in the sidebar, and confirm the original message is recovered.</span></div>''',
                    unsafe_allow_html=True)
    else:
        st.markdown('''<div class="result-success"><div class="result-title">✓ Message extracted successfully!</div>
          <div class="result-desc">Here is your hidden message.</div></div>''',
                    unsafe_allow_html=True)
        st.markdown("**Hidden message**")
        st.code(result["message"], language=None)
        if fmt == "Audio" and result.get("source"):
            audio_player(result["source"], "LISTEN TO THE AUDIO FILE")


for key, value in {"selected_format": "Image", "selected_mode": "Hide", "vault_selection": None,
                   "sample_selection": None, "last_result": None, "upload_epoch": 0}.items():
    if key not in st.session_state:
        st.session_state[key] = value

st.markdown(CSS, unsafe_allow_html=True)
st.markdown('''<div class="toolbar-line"><span class="toolbar-name">STEGOSHIELD / STEGANOGRAPHY STUDIO</span>
  <span class="local-tag">PRIVATE · LOCAL SESSION</span></div>''', unsafe_allow_html=True)
st.markdown('''<div class="welcome"><div class="welcome-copy"><div class="welcome-overline">THE MEDIA HIDING LAB</div>
  <h1>Hide in plain sight.</h1><p>A simple workspace to conceal a message in everyday media, recover it, and verify that nothing was lost.</p>
  <div class="welcome-steps"><span class="step-chip">01 Choose a carrier</span><span class="step-chip">02 Embed or reveal</span>
  <span class="step-chip">03 Verify & download</span></div></div>
  <div class="format-mosaic"><div class="mosaic-tile"><span>🖼️</span><strong>IMAGE</strong></div>
  <div class="mosaic-tile"><span>🎧</span><strong>AUDIO</strong></div>
  <div class="mosaic-tile"><span>🎞️</span><strong>VIDEO</strong></div>
  <div class="mosaic-tile"><span>📝</span><strong>TEXT</strong></div></div></div>''', unsafe_allow_html=True)

st.markdown('<div class="section-kicker">01 / Carrier format</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">What do you want to hide a message in?</div>', unsafe_allow_html=True)
fmt = st.radio("Carrier format", ["Image", "Audio", "Video", "Text"],
               format_func=lambda k: f"{SYMBOLS[k]}  {k}", horizontal=True, label_visibility="collapsed",
               key="selected_format", on_change=format_changed)
st.markdown('<div class="section-kicker">02 / Your workspace</div>', unsafe_allow_html=True)
work, details = st.columns([1.85, 0.85], gap="large")

with work:
    with st.container(border=True):
        st.markdown('<div class="section-title">Create or reveal a secret</div>', unsafe_allow_html=True)
        mode = st.radio("Action", ["Hide", "Extract"], key="selected_mode", horizontal=True,
                        format_func=lambda value: "🔒  Hide a message" if value == "Hide" else "🔎  Reveal a message",
                        on_change=mode_changed)
        st.markdown('<div class="section-kicker">Carrier input</div>', unsafe_allow_html=True)
        uploaded = None
        raw = None
        visible_cover = ""
        chosen_saved = None
        if fmt == "Text" and mode == "Hide":
            visible_cover = st.text_area("Visible cover paragraph", height=100,
                                         value="The project review is scheduled for tomorrow. All files are prepared and ready for inspection.",
                                         on_change=reset_result)
        else:
            uploaded = st.file_uploader(f"Drop your {fmt.lower()} here, or browse", type=EXTENSIONS[fmt],
                                        key=f"uploader_{fmt}_{mode}_{st.session_state['upload_epoch']}", on_change=file_changed)
            if mode == "Hide":
                st.button("✦ Use bundled demo sample", on_click=use_demo, args=(fmt,),
                          use_container_width=False, key=f"sample_{fmt}")
                if uploaded is None and st.session_state["sample_selection"] == fmt:
                    sample = BASE / "samples" / SAMPLES[fmt]
                    if sample.is_file():
                        raw = sample.read_bytes()
                        st.caption(f"✓ Using {sample.name} · {readable_size(len(raw))}")
                    else:
                        st.warning("Bundled sample missing; upload your own file instead.")
            elif st.session_state["vault_selection"]:
                try:
                    chosen_saved, saved_bytes = load_history(st.session_state["vault_selection"])
                    if chosen_saved["format"] == fmt:
                        st.info(f"Selected from recent files: {chosen_saved['name']}")
                        if uploaded is None:
                            raw = saved_bytes
                        if st.button("Remove recent-file selection", key="remove_saved"):
                            st.session_state["vault_selection"] = None
                            st.rerun()
                except HistoryError as exc:
                    st.warning(str(exc))
                    st.session_state["vault_selection"] = None
        if uploaded is not None and not (mode == "Extract" and chosen_saved):
            raw = uploaded.getvalue()

        if fmt == "Video" and mode == "Hide":
            st.caption("HD and high-FPS videos accepted. Large clips are resized and only the first 20 seconds are used.")

        message = ""
        if mode == "Hide":
            message = st.text_area("Secret message", height=98,
                                   value="Hello Sir! This is my CNS steganography project demo.",
                                   placeholder="Type the message you want to conceal...", on_change=reset_result)
            if raw and fmt in {"Image", "Audio"}:
                try:
                    capacity = image_capacity(raw) if fmt == "Image" else audio_capacity(raw)
                    if len(message.encode("utf-8")) > capacity:
                        st.warning("This file is too small. Use a larger file or a shorter message.")
                except (StegoError, OSError):
                    st.caption("Upload a supported file to calculate capacity.")
        else:
            st.caption("Select a generated stego file above, or click Decode next to a recent file in the sidebar.")
        trigger = st.button("🔐  HIDE MESSAGE & CREATE FILE" if mode == "Hide" else "🔎  EXTRACT HIDDEN MESSAGE",
                            type="primary", use_container_width=True)

        if trigger:
            try:
                with st.spinner("Hiding your message..." if mode == "Hide" else "Recovering your secret message..."):
                    if fmt == "Video":
                        extension = (".mkv" if chosen_saved and uploaded is None and mode == "Extract" else
                                     Path(uploaded.name).suffix.lower() if uploaded is not None else ".mp4")
                        result = process_video(raw, extension, mode, message)
                    else:
                        result = process_standard(fmt, mode, raw, message, visible_cover)
                    if mode == "Hide":
                        result["filename"] = f"stego_{fmt.lower()}_{datetime.now():%Y%m%d_%H%M%S}.{OUTPUT_EXT[fmt]}"
                        if fmt == "Text":
                            result["cover"] = visible_cover
                        try:
                            save_history(result["bytes"], display_name=result["filename"],
                                         fmt=fmt, mime=MIME[fmt])
                        except HistoryError as exc:
                            result["history_warning"] = str(exc)
                    st.session_state["last_result"] = result
                    st.toast("File ready to download!" if mode == "Hide" else "Message recovered!", icon="✅")
            except (StegoError, UnicodeError, OSError, ValueError, RuntimeError) as exc:
                st.session_state["last_result"] = None
                st.error(str(exc))
        last = st.session_state.get("last_result")
        if last and last["format"] == fmt and last["mode"] == mode:
            render_result(last)
            if last.get("history_warning"):
                st.warning("File created successfully, but it could not be added to the recent-files vault: " + last["history_warning"])

with details:
    st.markdown('<div class="section-kicker">Current method</div>', unsafe_allow_html=True)
    st.markdown(f'''<div class="info-card"><h3>{SYMBOLS[fmt]} {fmt} steganography</h3>
      <div class="meta-pill">Input: {html.escape(METHODS[fmt][0])}</div>
      <div class="meta-pill">Output: {html.escape(METHODS[fmt][1])}</div>
      <p style="color:#587267;font-size:12px;line-height:1.8;margin:8px 0 0"><b>{html.escape(METHODS[fmt][2])}.</b> {html.escape(METHODS[fmt][3])}</p></div>''',
                unsafe_allow_html=True)
    st.markdown('''<div class="info-card"><h3>How to complete a test</h3>
      <div class="info-step"><span class="info-num">01</span><span class="info-text">Choose a carrier and enter a short secret message.</span></div>
      <div class="info-step"><span class="info-num">02</span><span class="info-text">Generate the file and use its download button in the success panel.</span></div>
      <div class="info-step"><span class="info-num">03</span><span class="info-text">Switch to Reveal and confirm the exact message is recovered.</span></div>
      </div>''', unsafe_allow_html=True)
    note = ("Most common video files work. Large or high-FPS clips are automatically adjusted to 960×540, 30 FPS, and the first 20 seconds. Original sound is kept when present." if fmt == "Video" else
            "Editing, reformatting or trimming the hidden whitespace line can destroy the embedded message." if fmt == "Text" else
            "Uncompressed WAV preserves the LSB changes. Conversion to MP3 may destroy embedded bits." if fmt == "Audio" else
            "PNG preserves pixel bits. Re-saving the output as JPEG may destroy the hidden data.")
    st.markdown(f'<div class="tech-note"><b>✦ Format tip</b><br>{html.escape(note)}</div>', unsafe_allow_html=True)

# The sidebar is deliberately rendered AFTER processing: newly generated files
# appear immediately, without st.rerun() jumping the viewport back to the top.
render_sidebar()

with st.expander("How the four methods work"):
    st.markdown("""- **Image:** Hides bits by making tiny changes to image pixels (LSB).
- **Audio:** Hides bits in sound samples (LSB).
- **Video:** Hides bits in the first frame of a video (LSB).
- **Text:** Hides bits using spaces and tabs.

Use practice files. Editing or converting an encoded file may remove the hidden message.""")
st.markdown('<div class="footnote"><span>© StegoShield · Computer Network Security</span><span>LOCALLY PROCESSED · FOUR FORMATS · CLASSROOM DEMO</span></div>',
            unsafe_allow_html=True)
