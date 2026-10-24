# Local Speech Studio — Windows QA record

Date: 2026-10-24 to 2026-10-25 (Asia/Tokyo)  
Status: development / unsigned QA; commercial release and Store submission remain HOLD

## Source state

- Repository: `shihuiarenjinba-png/Whisper-AI`
- Working branch: `codex/whisper-youtube-media-20261024`
- Starting remote HEAD: `7eb9ce95cb24fecd90f01340e8e06a5e8ea33d6a`
- No changes were made to `main`, `release`, or the unrelated parent workspace repository.

## Windows test machine

- OS: Windows 11 Pro 64-bit, build `10.0.26200`
- CPU: Intel Core Ultra 7 265K, 20 cores / 20 logical processors
- RAM: 33,786,073,088 bytes (approximately 31.5 GiB)
- Source-test Python: 3.14.4; GitHub Actions remains configured for Python 3.12

This machine is not a low-spec reference device. The measurements below must not be generalized to other CPUs.

## QA-only dependencies

These files were acquired only for local QA and are excluded by `.gitignore`; they are not bundled in the product or committed to the repository.

| Component | QA version/source | SHA-256 |
| --- | --- | --- |
| whisper.cpp Windows x64 | tag `b5130`, `whisper.cpp 1.9.4`, commit `927cfce34f31707e17f2bff35c349632fb9e2c3a` | ZIP `F9EC6C52A2E949B62AB51FA21D0D497958F9E41C3010C157C4E42932D5316F3C` |
| Multilingual model | `ggerganov/whisper.cpp` `ggml-base.bin`, 147,951,465 bytes | `60ED5BC3DD14EEA856493D334349B405782DDCAF0028D4B5DF4088345FBA2EFE` |
| FFmpeg | winget `BtbN.FFmpeg.LGPL.9.0` 9.0.1-20260831; runtime `n9.0.1-11-ge47273f4d9` | winget verified installer hash; binary is not redistributed here |
| yt-dlp | release `2026.10.21`, `yt-dlp.exe`, 17,880,111 bytes | `33121D192D706E62F684A06F80918E3F3A8BA52AC3A65213B6951C39C7D9F555` (matched upstream `SHA2-256SUMS`) |
| PyInstaller | 6.22.3 in an isolated local venv | build tool only |

The directly downloaded FFmpeg archive matched its upstream checksum but was blocked by the machine's application-control policy. The test therefore used the same project's LGPL 9.0 package installed through winget. This is a QA environment fact, not approval to redistribute that binary.

## Test material and rights

The Japanese and English sentences were written for this QA run and synthesized locally with installed Microsoft Haruka (Japanese) and Microsoft Zira (English) Windows voices. The resulting WAV and MP4 files were not downloaded from a third party and were not uploaded. Test files and outputs remain under ignored `.qa-evidence/`.

- Japanese prompt: `こんにちは。これはローカル音声認識のテストです。東京で会議を始めます。番号は二千二十六です。`
- English prompt: `Hello. This is a local speech recognition test. The meeting begins in Tokyo. The project number is two zero two six.`
- Japanese MP4: 1024x768, SHA-256 `6A6948C2589D52A56794C56F6834440C4224B94ABFBF8F393593F99B9BCDF9ED`
- English MP4: 1280x720, SHA-256 `F30EBDB42435FC3C12AA94E39FF6163886BF51093F0F02E0B67B5BB3751E1583`

## Real-model results

Both cases used the application's real local path: MP4 -> FFmpeg PCM WAV -> real `whisper-cli.exe` -> TXT and SRT -> atomic publish.

### Japanese

- Application-pipeline elapsed time: 1.276 seconds
- Output TXT:

```text
こんにちは これはローカル音声認識のテストです
東京で会議を始めます 番号は2026です
```

- SRT segments: 2; timing covered 00:00:00.000 through 00:00:11.240.
- Observation: all intended lexical content was present. Punctuation was normalized/omitted and `二千二十六` became `2026`. No calibrated accuracy percentage is claimed.

### English

- Application-pipeline elapsed time: 1.314 seconds
- Output TXT:

```text
Hello. This is a local speech recognition test. The meeting begins in Tokyo. The project number is 2026.
```

- SRT segments: 1; timing covered 00:00:00.000 through 00:00:10.000.
- Observation: intended wording was present; spoken digits were normalized to `2026`. No calibrated accuracy percentage is claimed.

## CPU, memory, and repeat timing

Direct `whisper-cli` measurements used the same 16 kHz converted material. Each invocation was a new process. `avg machine` is CPU time divided by wall time and 20 logical processors; it is not an instantaneous peak.

| Language | Runs | Wall time (s) | CPU time (s) | Avg machine CPU | Peak working set |
| --- | ---: | ---: | ---: | ---: | ---: |
| Japanese | 3 | 1.150–1.180 (mean 1.170) | 3.610–3.920 | 15.7–16.6% | 301.8 MiB max |
| English | 3 | 1.040–1.110 (mean 1.067) | 3.250–3.310 | 15.0–15.7% | 303.4 MiB max |

A separately generated 60-second English WAV completed through the full application pipeline in 3.956 seconds. A second 60-second run was cancelled after 0.35 seconds; it raised `OperationCancelled`, terminated, and left no output or temporary file in the cancellation output directory.

## Automated tests and layout checks

- `python -m unittest discover -s tests -v` with `TEMP`/`TMP` pointed at ignored workspace-local `.qa-temp/` because the managed sandbox blocks its default OS Temp: 19/19 PASS.
- `python -m compileall -q app.py whisper_local`: PASS.
- `git diff --check`: PASS.
- Programmatic Tk layout at 100% scaling:
  - 1024x768 window: content height 673 px; no vertical clipping expected.
  - 1280x720 window: content height 673 px; no vertical clipping expected.
  - 720x520 window: content height 673 px; vertical scrolling is available.
- Windows visual QA completed after UI-control approval:
  - `docs/screenshots/windows-ja-1280x720-fit.png` — Japanese local-file UI; complete controls and result preview visible within a 922x682 app window, which fits the 1280x720 target envelope.
  - `docs/screenshots/windows-en-1024x768-fit.png` — English local-file UI; complete controls and corrected English preview placeholder visible within a 922x682 app window, which fits the 1024x768 target envelope.
  - `docs/screenshots/windows-en-youtube-scrollable.png` and `windows-en-youtube-scrolled.png` — YouTube fields, rights notice, actions, preview, and working vertical scroll at the same constrained height.
- The Japanese-to-English switch initially exposed a Japanese preview placeholder in English UI. It was fixed and the English screenshot was retaken.

## Local unsigned EXE

- Local PyInstaller build completed with Python 3.14.4 / PyInstaller 6.22.3.
- File: `LocalSpeechStudio_QA_UNSIGNED.exe`
- Size: 12,616,421 bytes
- SHA-256: `97B366DD35758C294511FF87E627066D3B0BAD3A4A28228CF96AB643C3D5159B`
- Authenticode: `NotSigned`
- A clean restart exposed a responding `Local Speech Studio — オフライン文字起こし` window and closed without a remaining parent/child process. PyInstaller one-file creates a launcher parent plus an application child; QA accounted for both.
- This local build is QA-only. A final hash is recorded after the final source rebuild; the GitHub Actions artifact is the authoritative Windows/Python 3.12 build when available.

## YouTube input

- Offline URL allowlist, malformed/unsafe URL rejection, rights gate, missing-downloader failure, cancellation, size/empty-output handling, and simulated download-to-local-transcription flow are covered by passing unit tests.
- `yt-dlp 2026.10.21` launched successfully with the upstream checksum verified.
- No positive YouTube download was performed because no owner-controlled URL with separately confirmed download permission and applicable YouTube terms was supplied. The positive network path remains HOLD; a legitimately obtained local MP4 was used instead.

## Store / commercial HOLD items

- Repository search found no verified Package/Identity, Publisher, PFN, or Store version. No MSIX candidate was generated.
- Code signing, signed installer/MSIX, WACK, real MSIX install/uninstall, Partner Center submission, Store publication, and Stripe publication were not performed.
- Dependency redistribution approval, complete third-party license bundle, and SBOM remain required.
- Low-spec device coverage, GPU variants, accessibility review, and long-duration/noisy real-world recordings remain open.
