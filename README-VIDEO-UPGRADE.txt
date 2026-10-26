STEGOSHIELD VIDEO COMPATIBILITY UPDATE
======================================

Why the old video failed:
The original classroom prototype rejected any video above 640x480 or 30 fps,
and clips longer than 15 seconds. This was an artificial demo limit, not
an inherent limitation of steganography.

What's new:
- Accepts common containers (MP4, MOV, AVI, MKV, WebM, M4V, MPEG, MPG,
  WMV, 3GP, TS), where supported by the bundled FFmpeg decoder.
- Accepts ordinary HD and high-frame-rate input video.
- Automatically adjusts larger videos to max 960x540 and 30 fps.
- For long input, the FIRST 20 SECONDS are used. The clip is shortened on purpose.
- Output stays a lossless, SILENT MKV (FFV1). Input audio is NOT preserved.
- LSB hiding/extraction and the other three steganography modules stay unchanged.
- Very large, damaged or unusual codec videos can still fail; available RAM,
  disk space, processing speed, and the Streamlit upload-size setting still matter.
- Lossless MKV can be much larger than the MP4 source. Do not convert the
  stego MKV to lossy MP4 before extraction.

INSTALL
-------
1. Open terminal inside folder containing app.py. Stop Streamlit with Ctrl+C.
2. Backup:
   Copy-Item .\app.py .\app_backup_before_video_update.py
   Copy-Item .\stegoshield\video.py .\stegoshield\video_backup.py
3. Unzip StegoShield-Video-Compatibility-Upgrade.zip into this folder, replacing
   app.py, stegoshield/video.py and tests/test_video.py.
4. Restart:
   python -m streamlit run app.py
5. Test:
   python -m pytest -q
6. Video -> Hide -> upload your MP4 -> Encode -> download MKV ->
   Video -> Reveal -> upload MKV -> Extract.

Notes:
- No additional Python dependency is needed.
- It is not possible to promise universal support for EVERY codec/format.
- Generated audio is intentionally omitted from video as before.
