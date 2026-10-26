# StegoShield — video sound preservation update

## What changed
- Video steganography still uses **LSB substitution in the RGB values of the first decoded frame**.
- The stego video is still encoded using **lossless FFV1 in MKV** to preserve embedded bits.
- The app now adds the **original video's audio** to the output if it has an audio track.
- The final FFmpeg step uses `-c:v copy` to avoid recompressing the stego video, and AAC audio for compatibility.
- Inputs with no soundtrack remain silent; no audio is invented.
- Large or high-frame-rate inputs continue to use a maximum of 960 × 540 pixels, 30 frames per second, and the first 20 seconds.
- Image, audio and text algorithms are unchanged.

## Install on Windows
Stop Streamlit with Ctrl+C, then from the StegoShield folder containing app.py:

```powershell
Copy-Item .\app.py .\app_before_sound_fix.py
Copy-Item .\stegoshield\video.py .\stegoshield\video_before_sound_fix.py
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\StegoShield-Video-Sound-Update.zip" -DestinationPath (Get-Location).Path -Force
python -m streamlit run app.py
```

## Test
1. Choose Video → Hide a message and upload a video that actually has sound.
2. Generate and download the output MKV.
3. Play the MKV in VLC (or a player supporting FFV1/MKV). Confirm it has the original sound.
4. Upload that MKV under Reveal a message and confirm the original text is extracted.
5. Run `python -m pytest -q` to run the automated tests.

If the source video has no audio track, its output will remain silent.

## Simple viva explanation
The system decodes the video into frames and stores the secret message bits in the least-significant bits of RGB pixels in the first frame. It then writes a lossless video so the hidden bits are not destroyed by compression. If the original video has sound, the application adds that soundtrack as a separate audio track; **the secret message is not hidden in the soundtrack**. During extraction, the first frame is decoded and the hidden message bits are reconstructed.
