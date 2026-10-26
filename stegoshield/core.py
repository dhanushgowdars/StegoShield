"""Classroom-focused LSB steganography for PNG, WAV, and UTF-8 text.

Not encryption or a secure channel. Binary payload format:
    magic (4 bytes) | message length (4 bytes, big endian) | UTF-8 message | CRC32 (4 bytes)
"""
from __future__ import annotations

import io
import struct
import wave
import zlib
from PIL import Image, UnidentifiedImageError

MAGIC = b"STG1"
HEADER_SIZE = 8
CHECKSUM_SIZE = 4
MAX_SECRET_BYTES = 100_000


class StegoError(ValueError):
    """Expected input, capacity, or decoding failure."""


def make_packet(message: str) -> bytes:
    if not message:
        raise StegoError("Enter a non-empty secret message.")
    message_bytes = message.encode("utf-8")
    if len(message_bytes) > MAX_SECRET_BYTES:
        raise StegoError(f"Message is too long (limit: {MAX_SECRET_BYTES:,} UTF-8 bytes).")
    return MAGIC + struct.pack(">I", len(message_bytes)) + message_bytes + struct.pack(">I", zlib.crc32(message_bytes))


def _read_bits(raw: bytes, start: int, count: int, stride: int = 1) -> bytes:
    """Read `count` complete bytes from least-significant bits."""
    if (start + count * 8) * stride > len(raw):
        raise StegoError("The carrier is too small or does not contain a full message.")
    result = bytearray(count)
    for byte_no in range(count):
        number = 0
        for bit_no in range(8):
            number = (number << 1) | (raw[(start + byte_no * 8 + bit_no) * stride] & 1)
        result[byte_no] = number
    return bytes(result)


def _decode_lsb(raw: bytes, stride: int = 1) -> str:
    if len(raw) // stride < (HEADER_SIZE + CHECKSUM_SIZE) * 8:
        raise StegoError("The carrier is too small to contain a StegoShield message.")
    header = _read_bits(raw, 0, HEADER_SIZE, stride)
    if not header.startswith(MAGIC):
        raise StegoError("No StegoShield message found. Use an unmodified encoded file.")
    n = struct.unpack(">I", header[4:])[0]
    if n > MAX_SECRET_BYTES:
        raise StegoError("The embedded message length is invalid.")
    if (HEADER_SIZE + n + CHECKSUM_SIZE) * 8 > len(raw) // stride:
        raise StegoError("The encoded file is incomplete or corrupted.")
    message = _read_bits(raw, HEADER_SIZE * 8, n, stride)
    crc = _read_bits(raw, (HEADER_SIZE + n) * 8, CHECKSUM_SIZE, stride)
    if zlib.crc32(message) != struct.unpack(">I", crc)[0]:
        raise StegoError("Checksum failed. Message bits were changed or damaged.")
    try:
        return message.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise StegoError("The embedded text is not valid UTF-8.") from exc


def _embed_lsb(raw: bytes, packet: bytes, stride: int = 1) -> bytes:
    available_bits = len(raw) // stride
    required_bits = len(packet) * 8
    if required_bits > available_bits:
        usable = max(0, available_bits // 8 - HEADER_SIZE - CHECKSUM_SIZE)
        raise StegoError(f"Carrier too small. Maximum message payload: {usable:,} bytes.")
    output = bytearray(raw)
    offset = 0
    for byte in packet:
        for pos in range(7, -1, -1):
            index = offset * stride
            output[index] = (output[index] & 254) | ((byte >> pos) & 1)
            offset += 1
    return bytes(output)


def image_capacity(image_bytes: bytes) -> int:
    with Image.open(io.BytesIO(image_bytes)) as picture:
        return max(0, picture.width * picture.height * 3 // 8 - HEADER_SIZE - CHECKSUM_SIZE)


def encode_image(image_bytes: bytes, message: str) -> bytes:
    try:
        with Image.open(io.BytesIO(image_bytes)) as picture:
            if picture.width * picture.height > 16_000_000:
                raise StegoError("Image is too large for this classroom demo (max 16 MP).")
            rgb = picture.convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise StegoError("Please upload a valid image file.") from exc
    result = Image.frombytes("RGB", rgb.size, _embed_lsb(rgb.tobytes(), make_packet(message)))
    output = io.BytesIO()
    result.save(output, format="PNG")
    return output.getvalue()


def decode_image(image_bytes: bytes) -> str:
    try:
        with Image.open(io.BytesIO(image_bytes)) as picture:
            if picture.width * picture.height > 16_000_000:
                raise StegoError("Image is too large for this classroom demo (max 16 MP).")
            return _decode_lsb(picture.convert("RGB").tobytes())
    except (UnidentifiedImageError, OSError) as exc:
        raise StegoError("Please upload a valid image file.") from exc


def _open_pcm_wav(wav_bytes: bytes) -> tuple[wave._wave_params, bytes]:
    try:
        with wave.open(io.BytesIO(wav_bytes), "rb") as reader:
            if reader.getcomptype() != "NONE":
                raise StegoError("Only uncompressed PCM WAV audio is supported.")
            params = reader.getparams()
            raw = reader.readframes(reader.getnframes())
    except (EOFError, wave.Error, OSError) as exc:
        raise StegoError("Please use a valid uncompressed PCM WAV file.") from exc
    if params.sampwidth not in (1, 2, 3, 4):
        raise StegoError("Unsupported WAV sample width.")
    return params, raw


def audio_capacity(wav_bytes: bytes) -> int:
    params, raw = _open_pcm_wav(wav_bytes)
    return max(0, len(raw) // params.sampwidth // 8 - HEADER_SIZE - CHECKSUM_SIZE)


def encode_audio(wav_bytes: bytes, message: str) -> bytes:
    params, raw = _open_pcm_wav(wav_bytes)
    modified = _embed_lsb(raw, make_packet(message), params.sampwidth)
    output = io.BytesIO()
    with wave.open(output, "wb") as writer:
        writer.setparams(params)
        writer.writeframes(modified)
    return output.getvalue()


def decode_audio(wav_bytes: bytes) -> str:
    params, raw = _open_pcm_wav(wav_bytes)
    return _decode_lsb(raw, params.sampwidth)


# Legacy format constants. Decode support is retained so older StegoShield TXT
# files remain readable. New files use ASCII-only whitespace to avoid the
# tofu/boxed glyph that some Windows text editors show for zero-width markers.
ZERO = "\u200b"
ONE = "\u200c"
START = "\u2060"
END = "\u2063"


def _message_from_packet(packet: bytes) -> str:
    """Validate STG1, expected byte count, and CRC32 for a text carrier."""
    if len(packet) < HEADER_SIZE + CHECKSUM_SIZE or packet[:4] != MAGIC:
        raise StegoError("No valid StegoShield text payload found.")
    n = struct.unpack(">I", packet[4:8])[0]
    if n > MAX_SECRET_BYTES or len(packet) != HEADER_SIZE + n + CHECKSUM_SIZE:
        raise StegoError("Hidden text has an invalid length or was modified.")
    message = packet[HEADER_SIZE:HEADER_SIZE + n]
    if zlib.crc32(message) != struct.unpack(">I", packet[-CHECKSUM_SIZE:])[0]:
        raise StegoError("Text checksum failed. The hidden data was altered.")
    try:
        return message.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise StegoError("The hidden message is not valid UTF-8.") from exc


def _bytes_from_text_bits(bits: str, zero: str, one: str) -> bytes:
    if not bits or len(bits) % 8 != 0 or any(bit not in (zero, one) for bit in bits):
        raise StegoError("Text embedding bits are incomplete or damaged.")
    return bytes(
        int("".join("1" if character == one else "0" for character in bits[i:i + 8]), 2)
        for i in range(0, len(bits), 8)
    )


def encode_text(cover: str, message: str) -> str:
    """Hide a packet with ordinary ASCII space/tab characters after cover text.

    The readable cover characters are unchanged. A whitespace-only final line
    carries one payload bit per ASCII space or tab. This method is NOT robust
    against text editors trimming trailing whitespace or reformatting the file.
    """
    if not cover.strip():
        raise StegoError("Enter some visible cover text.")
    packet = make_packet(message)
    whitespace_bits = "".join(
        "\t" if ((byte >> bit) & 1) else " "
        for byte in packet for bit in range(7, -1, -1)
    )
    # Final newline is deliberate: in Notepad the visible paragraph stays
    # untouched and there are no unsupported Unicode control-glyph markers.
    return cover + "\n" + whitespace_bits + "\n"


def decode_text(stego_text: str) -> str:
    """Read new ASCII whitespace TXT, or an older zero-width Unicode TXT."""
    # Preserve compatibility with StegoShield files generated before this fix.
    marker_start = stego_text.find(START)
    if marker_start >= 0:
        marker_end = stego_text.find(END, marker_start + 1)
        if marker_end < 0:
            raise StegoError("The older hidden Unicode text was damaged.")
        legacy_bits = stego_text[marker_start + 1:marker_end]
        return _message_from_packet(_bytes_from_text_bits(legacy_bits, ZERO, ONE))

    # Windows Notepad may rewrite LF newlines as CRLF when a user saves a file.
    normalized = stego_text.replace("\r\n", "\n")
    lines = normalized.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    if not lines:
        raise StegoError("No hidden text found. Upload an encoded TXT file.")
    bit_line = lines[-1]
    if not bit_line or any(c not in (" ", "\t") for c in bit_line):
        raise StegoError("No hidden text found. Upload an encoded TXT file.")
    return _message_from_packet(_bytes_from_text_bits(bit_line, " ", "\t"))
