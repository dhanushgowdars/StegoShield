StegoShield - audio player compatibility update

This update modifies ONLY app.py. Your stegoshield/core.py, stegoshield/video.py,
file vault, samples, and tests remain unchanged.

What changed:
- The audio listening player uses an MP3 preview for more consistent Chrome playback.
- The downloaded stego file remains the original WAV (it contains the hidden message).
- The audio player also appears after extracting an audio message.
- The bundled sample is a 1-second beep, not a spoken reading of the hidden text.
- If FFmpeg preview conversion is unavailable, the player falls back to WAV.

Installation from the StegoShield directory that contains app.py:
1. Stop Streamlit (Ctrl+C).
2. Back up: Copy-Item .\app.py .\app_before_audio_fix.py
3. Extract StegoShield-Audio-Playback-Fix.zip into this same directory, overwriting app.py.
4. Start: python -m streamlit run app.py
5. Select Audio -> Hide a message -> generate a WAV and play the preview.
6. Download the WAV and select Audio -> Reveal to recover the message.

IMPORTANT: Do NOT convert the actual downloaded stego WAV to MP3 before extraction.
Only the in-browser listening preview is MP3. Lossy MP3 may destroy hidden bits.

Tests: original 22 algorithm/history tests passed; FFmpeg decoded the generated
MP3 listening preview successfully. Browser playback must still be verified
in your own Chrome session.
