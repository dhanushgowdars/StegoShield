from pathlib import Path
import pytest
import imageio_ffmpeg
from stegoshield.core import StegoError
from stegoshield.video import encode_video, decode_video, video_capacity


def test_video_roundtrip(tmp_path: Path):
    source = str(tmp_path / "source.mp4")
    output = str(tmp_path / "stego.mkv")
    writer = imageio_ffmpeg.write_frames(source, (64, 48), fps=8,
                                         codec="libx264", pix_fmt_out="yuv420p",
                                         ffmpeg_log_level="error", macro_block_size=1)
    next(writer)
    try:
        for frame_no in range(8):
            data = bytes([(frame_no * 5 + i) % 256 for i in range(64 * 48 * 3)])
            writer.send(data)
    finally:
        writer.close()
    assert video_capacity(source) > 0
    encode_video(source, output, "Secret video! 🎬")
    assert Path(output).exists()
    assert decode_video(output) == "Secret video! 🎬"
    with pytest.raises(StegoError, match="No StegoShield message"):
        decode_video(source)


def test_high_resolution_high_fps_is_adapted(tmp_path: Path):
    """An input larger than 640x480 and above 30fps should now work."""
    source = str(tmp_path / "hd_input.mp4")
    result = str(tmp_path / "adapted_stego.mkv")
    writer = imageio_ffmpeg.write_frames(source, (800, 600), fps=45,
                                         codec="libx264", pix_fmt_out="yuv420p",
                                         ffmpeg_log_level="error", macro_block_size=1)
    next(writer)
    try:
        for index in range(10):
            # Constant-color RGB image with a changing tint.
            writer.send(bytes([index * 15, 70, 130]) * (800 * 600))
    finally:
        writer.close()
    encode_video(source, result, "HD 45 fps works!")
    assert decode_video(result) == "HD 45 fps works!"
    reader = imageio_ffmpeg.read_frames(result, pix_fmt="rgb24")
    meta = next(reader)
    reader.close()
    assert meta["size"][0] <= 960 and meta["size"][1] <= 540
    assert float(meta["fps"]) <= 30.1


def test_long_video_is_shortened(tmp_path: Path):
    """Long inputs can be demonstrated without a hard reject."""
    source = str(tmp_path / "long_input.mp4")
    result = str(tmp_path / "long_stego.mkv")
    writer = imageio_ffmpeg.write_frames(source, (64, 48), fps=1,
                                         codec="libx264", pix_fmt_out="yuv420p",
                                         ffmpeg_log_level="error", macro_block_size=1)
    next(writer)
    try:
        for index in range(23):
            writer.send(bytes([index * 3, 110, 40]) * (64 * 48))
    finally:
        writer.close()
    encode_video(source, result, "Long video works")
    assert decode_video(result) == "Long video works"
    reader = imageio_ffmpeg.read_frames(result, pix_fmt="rgb24")
    meta = next(reader)
    reader.close()
    assert 0 < float(meta["duration"]) <= 21


def test_video_preserves_source_soundtrack(tmp_path: Path):
    """Source MP4 has a short tone; stego MKV must retain an audio track."""
    import subprocess
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    silent = str(tmp_path / "raw_video.mp4")
    source = str(tmp_path / "with_sound.mp4")
    output = str(tmp_path / "stego_with_sound.mkv")
    writer = imageio_ffmpeg.write_frames(silent, (64, 48), fps=8,
                                         codec="libx264", pix_fmt_out="yuv420p",
                                         ffmpeg_log_level="error", macro_block_size=1)
    next(writer)
    try:
        for i in range(16):
            writer.send(bytes([i*4, 75, 100]) * (64*48))
    finally:
        writer.close()
    made = subprocess.run([
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
        "-i", silent, "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-shortest", source
    ], capture_output=True)
    assert made.returncode == 0, made.stderr.decode(errors="replace")
    encode_video(source, output, "Message with soundtrack")
    assert decode_video(output) == "Message with soundtrack"
    verify = subprocess.run([ffmpeg, "-hide_banner", "-i", output, "-map", "0:a:0",
                             "-f", "null", "-"], capture_output=True)
    assert verify.returncode == 0, verify.stderr.decode(errors="replace")
    assert b"Audio: aac" in verify.stderr
