"""StegoShield video: accept ordinary clips and prepare a bounded lossless demo.

Common videos can be any input resolution or frame rate. To avoid huge outputs,
HD/high-FPS/long input is adapted to at most 960x540, 30 fps, first 20 seconds.
The LSB packet is embedded *after* input normalization, in the first RGB frame.
FFV1/MKV output is lossless; the original audio is retained when present.
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import subprocess
import tempfile

import imageio_ffmpeg

from .core import StegoError, _decode_lsb, _embed_lsb, make_packet, HEADER_SIZE, CHECKSUM_SIZE

MAX_WIDTH = 960
MAX_HEIGHT = 540
MAX_FPS = 30.0
MAX_SECONDS = 20.0
MAX_FRAMES = 630
MAX_DECODE_PIXELS = 16_000_000


def _read(path: str):
    """Open video with FFmpeg; unlike the original demo, do not reject HD / 60fps."""
    reader = None
    try:
        reader = imageio_ffmpeg.read_frames(path, pix_fmt="rgb24")
        metadata = next(reader)
        width, height = metadata["size"]
        if width <= 0 or height <= 0 or width * height > MAX_DECODE_PIXELS:
            raise StegoError("This video is too large to decode safely. Use an ordinary HD clip.")
        return reader, metadata
    except (OSError, RuntimeError, StopIteration, KeyError, TypeError, ValueError) as exc:
        if reader is not None:
            reader.close()
        if isinstance(exc, StegoError):
            raise
        raise StegoError("Couldn't read the video. Try MP4, MOV, AVI, MKV or WebM.") from exc


def _target_dimensions(width: int, height: int) -> tuple[int, int]:
    scale = min(1.0, MAX_WIDTH / width, MAX_HEIGHT / height)
    return max(2, int(width * scale) // 2 * 2), max(2, int(height * scale) // 2 * 2)


def _normalization_needed(metadata: dict) -> bool:
    width, height = metadata["size"]
    fps = float(metadata.get("fps") or 0)
    duration = float(metadata.get("duration") or 0)
    return (width > MAX_WIDTH or height > MAX_HEIGHT or fps <= 0 or fps > MAX_FPS
            or duration <= 0 or duration > MAX_SECONDS)


@contextmanager
def _prepared_input(input_path: str):
    """Prepare overly large/high-FPS videos before applying LSB substitution.

    This separate FFmpeg pass lets imageio_ffmpeg correctly parse the resized
    dimensions and frame rate; frame filtering within read_frames is unsafe
    because its metadata can still describe the original input dimensions.
    """
    reader, metadata = _read(input_path)
    reader.close()
    if not _normalization_needed(metadata):
        yield input_path
        return
    fps = float(metadata.get("fps") or 24)
    fps = min(max(fps, 1), MAX_FPS)
    with tempfile.TemporaryDirectory(prefix="stegoshield_video_") as temp:
        output_path = str(Path(temp) / "prepared.mp4")
        # min(iw,960)/min(ih,540) prevents unnecessary upscaling.
        filter_chain = (
            "scale=w='min(iw,960)':h='min(ih,540)':"
            "force_original_aspect_ratio=decrease:force_divisible_by=2,"
            f"fps={fps:.4f}"
        )
        command = [
            imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel", "error",
            "-nostdin", "-y", "-i", input_path,
            "-map", "0:v:0", "-t", str(int(MAX_SECONDS)),
            "-vf", filter_chain, "-an", "-sn", "-dn",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", output_path,
        ]
        try:
            completed = subprocess.run(command, capture_output=True, timeout=180, check=False)
        except subprocess.TimeoutExpired as exc:
            raise StegoError("Video preparation took too long. Use a shorter clip.") from exc
        except OSError as exc:
            raise StegoError("Unable to prepare this video on your computer.") from exc
        if completed.returncode != 0 or not Path(output_path).is_file():
            details = completed.stderr.decode("utf-8", errors="replace")[-280:].strip()
            raise StegoError("Unable to prepare this video. " + (details or "Try another file."))
        yield output_path


def video_capacity(input_path: str) -> int:
    """Estimate payload capacity after any automatic reduction in dimensions."""
    reader, metadata = _read(input_path)
    try:
        width, height = _target_dimensions(*metadata["size"])
        return max(0, width * height * 3 // 8 - HEADER_SIZE - CHECKSUM_SIZE)
    finally:
        reader.close()


def encode_video(input_path: str, output_path: str, message: str) -> None:
    """Embed text in first video frame; remux source audio into final MKV.

    The video stream is copied, not re-encoded, during the final mux step. This
    matters: lossy video re-encoding could damage the hidden LSB payload.
    """
    if Path(input_path).resolve() == Path(output_path).resolve():
        raise StegoError("Input and output paths must be different.")
    packet = make_packet(message)
    with tempfile.TemporaryDirectory(prefix="stegoshield_mux_") as work:
        silent_path = str(Path(work) / "encoded_video.mkv")
        success = False
        with _prepared_input(input_path) as prepared:
            reader, metadata = _read(prepared)
            writer = None
            try:
                width, height = metadata["size"]
                if len(packet) * 8 > width * height * 3:
                    raise StegoError("This video is too small for the message. Use a shorter message.")
                fps = float(metadata.get("fps") or 24)
                writer = imageio_ffmpeg.write_frames(
                    silent_path, (width, height), fps=fps,
                    codec="ffv1", pix_fmt_in="rgb24", pix_fmt_out="bgr0",
                    quality=None, macro_block_size=1, ffmpeg_log_level="error",
                    output_params=["-f", "matroska"],
                )
                next(writer)
                count = 0
                for frame in reader:
                    if count >= MAX_FRAMES:
                        break
                    if count == 0:
                        frame = _embed_lsb(frame, packet)
                    writer.send(frame)
                    count += 1
                if count == 0:
                    raise StegoError("The video has no readable frames.")
                success = True
            except (OSError, RuntimeError, ValueError) as exc:
                if isinstance(exc, StegoError):
                    raise
                raise StegoError(f"Video conversion failed: {str(exc)[:180]}") from exc
            finally:
                reader.close()
                if writer is not None:
                    writer.close()
                if not success:
                    Path(output_path).unlink(missing_ok=True)

        # Audio, when present, comes from the *original* input video.
        # Audio is a separate stream; it never carries our hidden message.
        # FFV1 pixels must be stream-copied to preserve the secret bits.
        cmd = [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
            "-i", silent_path,
            "-i", input_path,
            "-map", "0:v:0", "-map", "1:a:0?",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
            "-t", str(int(MAX_SECONDS)),
            "-f", "matroska", output_path,
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, timeout=180, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            Path(output_path).unlink(missing_ok=True)
            raise StegoError("Could not finish the video. Try a shorter clip.") from exc
        if proc.returncode != 0 or not Path(output_path).is_file():
            Path(output_path).unlink(missing_ok=True)
            details = proc.stderr.decode("utf-8", errors="replace")[-280:].strip()
            raise StegoError("Could not preserve the video's soundtrack. " +
                             (details or "Try another video."))


def decode_video(input_path: str) -> str:
    reader, _ = _read(input_path)
    try:
        try:
            frame = next(reader)
        except StopIteration as exc:
            raise StegoError("The video does not contain any readable frames.") from exc
        return _decode_lsb(frame)
    finally:
        reader.close()
