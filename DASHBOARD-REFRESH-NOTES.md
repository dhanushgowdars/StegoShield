# StegoShield Dashboard Refresh

This is a **UI-only** update to the existing StegoShield CNS project. It does not change the four encoding or decoding algorithms. It retains `.stegoshield_data` on your computer.

## What changed

- New compact cream, evergreen and jade-themed landing area; previous oversized blue hero removed.
- Generated output appears **immediately below the Hide / Extract button** in the main workspace.
- Clear green completion panel, toast, original/encoded image previews, and an obvious download button.
- No `st.rerun()` after embedding: avoids unexpectedly jumping back to the top of the page.
- Sidebar file vault is rendered after processing so the freshly generated file appears there on the same request.
- History Decode uses an `on_click` callback and resets the uploader to prevent stale uploads from overriding a selected saved file.
- Preserved text whitespace encoding fix, video lossless MKV output, and CRC32 integrity verification.

## Apply this update to your Windows project

1. Stop the current Streamlit process with **Ctrl+C** in VS Code.
2. In your `StegoShield` folder (the folder containing `app.py`), back up `app.py`.
3. Extract the update ZIP into that same `StegoShield` folder, allowing it to replace only `app.py` and `.streamlit/config.toml`.
4. Run `python -m streamlit run app.py`, then hard-refresh browser with **Ctrl+Shift+R** if necessary.
5. Test Image Hide: upload PNG, encode, confirm a green success panel below the action button, see side-by-side preview and a large download button. Switch to Reveal and verify the recovered message.

### Install existing dependencies (only if necessary)

`python -m pip install -r requirements.txt`

### Verify algorithms

`python -m pytest -q`

**Privacy:** Encoded files in `.stegoshield_data` are stored unencrypted and should contain demo data only.
