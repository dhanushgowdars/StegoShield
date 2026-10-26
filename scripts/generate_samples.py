"""Generate small, original sample files suitable for a short classroom demo."""
from pathlib import Path
import io
import math
import struct
import wave
from PIL import Image
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[1] / "samples"
ROOT.mkdir(exist_ok=True)

# A gradient with detail avoids requiring a downloaded photograph.
width, height = 256, 180
picture = Image.new("RGB", (width, height))
pixels = picture.load()
for y in range(height):
    for x in range(width):
        pixels[x, y] = (int(35 + 180 * x / width), int(65 + 150 * y / height), int(70 + 85 * ((x + y) % 31) / 30))
picture.save(ROOT / "sample_image.png")

# One second of original PCM WAV audio, mono 16-bit / 16 kHz.
samples = 16000
with wave.open(str(ROOT / "sample_audio.wav"), "wb") as writer:
    writer.setnchannels(1)
    writer.setsampwidth(2)
    writer.setframerate(16000)
    writer.writeframes(b"".join(struct.pack("<h", int(6500 * math.sin(2 * math.pi * 440 * i / 16000))) for i in range(samples)))

(ROOT / "sample_text.txt").write_text(
    "The class assignment demonstrates information hiding in digital media.\n"
    "This document contains the public version of the demonstration notes.\n", encoding="utf-8"
)

# Three seconds, 10 frames per second, compact sample MP4.
video_path = ROOT / "sample_video.mp4"
writer = imageio_ffmpeg.write_frames(str(video_path), (160, 120), fps=10,
                                     codec="libx264", pix_fmt_in="rgb24", pix_fmt_out="yuv420p",
                                     macro_block_size=1, ffmpeg_log_level="error")
next(writer)
try:
    for t in range(30):
        frame = bytearray(160 * 120 * 3)
        for y in range(120):
            for x in range(160):
                p = 3 * (y * 160 + x)
                frame[p] = (x + t * 5) % 256
                frame[p + 1] = (y * 2 + t * 4) % 256
                frame[p + 2] = (x + y + t * 2) % 256
        writer.send(bytes(frame))
finally:
    writer.close()

print("Sample files created in:", ROOT)
for sample in sorted(ROOT.iterdir()):
    if sample.is_file():
        print(sample.name, sample.stat().st_size, "bytes")
