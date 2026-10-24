# Local Speech Studio — offline transcription (Windows MVP)

> **Status: development / QA only. Not a ready-for-sale release.**
> The GitHub repository is `Whisper-AI`, but this tool is not an official OpenAI/Whisper product.

A small bilingual Windows desktop UI for making **TXT transcripts** and **SRT subtitles** from local audio/video files. It runs `whisper.cpp` on **your own PC**, without OpenAI APIs, external cloud accounts, subscriptions, or per-minute recognition charges. No audio, files, prompts, or usage data are transmitted by this app.

## What works in this MVP

- Japanese / English application UI; speech language: auto-detect / Japanese / English.
- Audio and video picker (WAV, MP3, M4A, FLAC, OGG, MP4, MKV, WebM, AAC, WMA).
- FFmpeg converts selected media to 16 kHz, mono, signed 16-bit PCM WAV.
- An existing, user-supplied `whisper-cli` executable and compatible multilingual GGML `.bin` model transcribe the audio.
- Local TXT and SRT output; no output overwrite; cancellation; clear recoverable errors.
- No Ollama or external AI API required. Optional Ollama summaries are a *separate future feature*, not claimed to work in this version.

### Prerequisites (not bundled)

1. **Windows 10/11 and Python 3.12** for source use. Tkinter is included with normal official Python for Windows.
2. A compatible `whisper-cli.exe` built from [whisper.cpp](https://github.com/ggml-org/whisper.cpp) for your hardware. If it is on `PATH`, the app can detect it automatically; otherwise browse to the `.exe`.
3. A compatible GGML **multilingual** model such as `ggml-base.bin` or `ggml-small.bin`, obtained separately from a trusted source. **Do not use** an English-only `.en.bin` model for Japanese. The model is selected by the user.
4. `ffmpeg.exe` from a trustworthy distributable build. If present on `PATH`, it is detected automatically; otherwise browse to it. Review FFmpeg licensing before commercial redistribution.

## Run

```powershell
py -3.12 app.py
```

1. Select a local audio or video file.
2. Select a multilingual GGML Whisper model (`.bin`).
3. Select `whisper-cli.exe` and `ffmpeg.exe`, then an existing output directory.
4. Choose `Auto`, `ja`, or `en` for speech recognition.
5. Click **Start transcription / 文字起こし開始**. TXT and SRT are saved in the selected directory with a unique basename.

The app works offline **after prerequisites have been installed**. It does **not** automatically download runtimes or models or call an AI API. Transcription may take a long time on slower PCs. The progress indicator shows the current stage, not a fabricated percentage.

## Tests

```powershell
py -3.12 -m unittest discover -s tests -v
```

These tests use **fake runtimes** to verify command construction, cancellation, missing files, cleanup and no-overwrite behavior. They do not claim to measure real Japanese accuracy, GPU performance, or actual whisper inference.

## Windows QA artifact

The workflow `.github/workflows/windows-qa.yml` runs unit tests on Windows and packages `LocalSpeechStudio_QA_UNSIGNED.exe` with PyInstaller. It is an **unsigned QA-only EXE**, **not an MSIX**, not tested against a real model, and not a certified Microsoft Store release. A real signed MSIX requires additional validation of app identity/Publisher, signing, installation/uninstallation, licensing, screenshots, and WACK/Store checks.

## Security and privacy

- Child processes are launched as argument arrays without a shell, never by interpolating audio filenames into shell commands.
- Files stay on the local PC. No network code, telemetry, model downloader, or automatic service discovery is included.
- Temporary converted audio and temporary transcripts are removed after completion, cancellation, or failure.
- Existing TXT/SRT files are not overwritten. Select a destination folder you trust and have write permission to.
- Windows app does not request administrative privileges.

## Planned commercial-quality work (not implemented)

- Guided, offline-friendly runtime/model setup and signed installer/MSIX.
- Actual Japanese + English recognition quality benchmarks and low-spec Windows performance tests.
- GUI subtitle editing, video preview, batch queue, accessibility checks at 1024x768.
- Runtime checksums, SBOM, license audit for each bundled binary/model, signed MSIX QA.
- Optional user-provided Ollama integration for transcript summaries with clear uncertainty labels.

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for upstream attribution and redistribution obligations.
