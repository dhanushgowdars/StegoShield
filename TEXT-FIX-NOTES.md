# StegoShield Text Fix (October 2026)

The original text encoder stored payload bits in zero-width Unicode markers.
Windows Notepad can render some of these as a visible box, which undermines
the text steganography demonstration.

## New encoder
- Leaves the original cover text exactly as provided.
- Appends a newline, then an encoded ASCII-only sequence of spaces and tabs,
  then a newline.
- Maps a payload bit of `0` to a space and `1` to a tab.
- Uses the same STG1 packet with payload length and CRC32 as the other modes.
- Exports UTF-8 TXT. New generated files have no Unicode zero-width markers.
- The decoder can still open older StegoShield files that used Unicode markers.

## Limitations
This is *whitespace steganography*, not undetectable security. The whitespace
line may be revealed by selecting text or enabling whitespace markers. Text
editors or online platforms may strip trailing whitespace, changing or
removing the payload. Use only the original downloaded TXT for extraction.
Do not put real passwords or confidential data in this project.

## Installation
Back up `stegoshield/core.py` and `app.py`, then extract the upgrade ZIP
into the existing project root (the directory with `app.py`), overwriting
these files:

- `stegoshield/core.py`
- `app.py`
- `tests/test_core.py`
- `README.md`
- `TEXT-FIX-NOTES.md`

No packages to install and no need to change other steganography modules.
Generate new TXT files; older files will not visually change themselves.

Run: `python -m pytest -q`; this package passed 22 tests.
