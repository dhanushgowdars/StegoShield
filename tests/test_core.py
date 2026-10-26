import io
import struct
import wave

import pytest
from PIL import Image
from stegoshield.core import (
    StegoError, encode_image, decode_image, encode_audio, decode_audio,
    encode_text, decode_text, image_capacity, audio_capacity,
)


def image_bytes():
    raw = io.BytesIO()
    Image.new("RGB", (40, 40), (51, 102, 204)).save(raw, format="PNG")
    return raw.getvalue()


def audio_bytes(sample_width):
    raw = io.BytesIO()
    with wave.open(raw, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(sample_width)
        w.setframerate(16000)
        w.writeframes(bytes(4000 * sample_width))
    return raw.getvalue()


@pytest.mark.parametrize("message", ["hello", "CNS ✓", "नमस्ते 🌏"])
def test_image_roundtrip(message):
    stego = encode_image(image_bytes(), message)
    assert decode_image(stego) == message
    assert image_capacity(image_bytes()) > 0


@pytest.mark.parametrize("sample_width", [1, 2, 3, 4])
def test_wav_roundtrip(sample_width):
    wav = audio_bytes(sample_width)
    assert decode_audio(encode_audio(wav, "Audio says hello!")) == "Audio says hello!"
    assert audio_capacity(wav) > 0


@pytest.mark.parametrize("message", ["ABC", "emoji 🔒", "Secure note ✓"])
def test_text_roundtrip(message):
    cover = "This looks like a normal paragraph of text."
    stego = encode_text(cover, message)
    assert decode_text(stego) == message
    assert stego.startswith(cover + "\n")
    # Everything after the cover is ordinary ASCII whitespace: no replacement
    # glyph / visible box characters in Notepad.
    payload_line = stego.rsplit("\n", 2)[1]
    assert set(payload_line) <= {" ", "\t"}
    assert "\u2060" not in stego and "\u2063" not in stego
    assert "\u200b" not in stego and "\u200c" not in stego


def test_no_packet_rejected():
    with pytest.raises(StegoError, match="No StegoShield message"):
        decode_image(image_bytes())
    with pytest.raises(StegoError, match="No hidden text"):
        decode_text("ordinary text")


def test_short_carrier_rejected():
    with pytest.raises(StegoError, match="Carrier too small"):
        encode_image(image_bytes(), "x" * 1000)


def test_empty_secret_rejected():
    with pytest.raises(StegoError):
        encode_text("hello", "")


def test_text_whitespace_crlf_roundtrip():
    stego = encode_text("A normal one-line note.", "secret 123 🌟")
    assert decode_text(stego.replace("\n", "\r\n")) == "secret 123 🌟"


def test_text_modified_whitespace_detected():
    stego = encode_text("A normal note.", "hidden data")
    prefix, bits, final = stego.rsplit("\n", 2)
    changed = ("\t" if bits[0] == " " else " ") + bits[1:]
    with pytest.raises(StegoError):
        decode_text(prefix + "\n" + changed + "\n" + final)


def test_legacy_unicode_stego_still_decodes():
    from stegoshield.core import make_packet
    packet = make_packet("legacy note")
    bits = "".join("\u200c" if (b >> bit) & 1 else "\u200b" for b in packet for bit in range(7, -1, -1))
    old_file = "Cover" + "\u2060" + bits + "\u2063" + " paragraph"
    assert decode_text(old_file) == "legacy note"
