# StegoShield — four algorithms (presentation level)

| Type | Method | What changes? | How recovery works | Output |
|---|---|---|---|---|
| Image | RGB LSB substitution | Lowest bit of successive red/green/blue channel values | Read those low bits in the same order | PNG |
| Audio | PCM sample LSB substitution | Lowest bit of selected uncompressed audio samples | Read sample LSBs from WAV | WAV |
| Video | First-frame RGB LSB | Lowest bit of pixel-channel values in first decoded video frame | Decode first frame and read pixel LSBs | Lossless FFV1/MKV |
| Text | ASCII whitespace encoding | Append a line whose spaces and tabs represent binary digits | Translate the whitespace line back into bits | UTF-8 TXT |

## Common workflow
1. Convert UTF-8 secret text into a sequence of bytes/bits.
2. Add a small header (marker and message length) so the decoder can locate the payload.
3. Apply the selected media embedding rule.
4. Save in a format that preserves the hidden information.
5. Decode in reverse to reconstruct the original message.

## How video and audio fit together
- The **Audio** module hides bits **inside WAV sound samples**.
- The **Video** module hides bits **inside video frame pixels**; it keeps the original soundtrack when one exists.
- Keeping the video soundtrack is different from hiding text inside audio. These are two separate operations.

## Practical limits worth mentioning
- PNG and WAV are used because lossy recompression may destroy the modified least-significant bits.
- MKV/FFV1 is lossless for video pixel values; some browsers cannot play FFV1, so VLC is useful.
- Text whitespace may be removed by reformatting or editors.
- These are demonstration methods, not a guarantee that an observer cannot detect hidden information.
