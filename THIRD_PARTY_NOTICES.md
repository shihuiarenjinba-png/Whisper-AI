# Third-party dependencies and commercial-release checklist

This repository currently contains the original Python wrapper/UI source. It does not commit or distribute `whisper.cpp`, FFmpeg, `yt-dlp`, GGML model weights, or Microsoft Store identity values. Users supply those runtime files separately.

Runtime tools supplied separately by the user:

- **whisper.cpp** — upstream project: https://github.com/ggml-org/whisper.cpp ; verify the exact version and license (upstream code is MIT) before bundling.
- **FFmpeg** — https://ffmpeg.org/legal.html ; licensing depends on the features and distribution build (LGPL/GPL and possibly additional obligations). Do not assume that every FFmpeg binary is suitable for closed-source commercial redistribution.
- **Whisper model weights** — verify the provenance, license, model checksum, and redistribution terms of the exact GGML model file. No model is downloaded or shipped by this project.
- **yt-dlp** — https://github.com/yt-dlp/yt-dlp ; verify the exact release, Unlicense text, bundled component notices, checksum, intended use, and applicable YouTube terms before bundling or recommending it. The app uses it only for an explicit, rights-confirmed URL import.
- **PyInstaller** — used only to package this wrapper during CI; review its bootloader/runtime license before distribution.
- **Python and Tcl/Tk** — a frozen executable can contain runtime components with their own notices; review the collected build before distribution.

Before commercial release, prepare: pinned source revisions, license texts and notices, software bill of materials, source/offer obligations as needed, approved binaries/models, privacy statements, Windows compatibility tests, code signing, and delivery/licensing flow.

Do not publish the QA_UNSIGNED artifact as a signed or Microsoft Store-certified build.
