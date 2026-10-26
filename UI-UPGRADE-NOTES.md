# StegoShield Premium UI upgrade

This package preserves the original core steganography algorithms. It replaces only the dashboard, adds a local sidebar vault, and updates its theme.

## Apply on Windows

1. Open the existing `StegoShield` project folder in VS Code. Keep the working `.venv` unchanged.
2. Back up your current `app.py` if you have edited it.
3. Extract this ZIP **into the existing `StegoShield` project folder**, using overwrite/replace when prompted. The relative paths should match `app.py`, `stegoshield/history.py`, `.streamlit/config.toml`, `.gitignore`, and `tests/test_history.py`.
4. From that folder run `python -m streamlit run app.py`.

No additional pip packages are required beyond the original requirements.

## Local vault

The dashboard saves up to eight recently generated encoded output files in the ignored `.stegoshield_data/` folder. It lets you download or select a file for extraction even after Streamlit restarts. Select **Manage vault → Delete all saved files** to erase these local cached outputs.

The vault stores files unencrypted; only use your own classroom samples and no sensitive messages.

## Demo features

- Dark security-themed sidebar and cleaner workbench
- Four format selectors and hide/reveal modes
- Drag-and-drop carrier uploads
- Preloaded example carriers (Image, Audio and Video)
- Before/after image and audio previews
- Progress/capacity display for image and audio
- Result panel that persists when Streamlit reruns
- Recent-file history with download and decode shortcuts

Video remains a silent, lossless FFV1/MKV output and may not preview in browsers. The original encoder and decoder are unchanged.
