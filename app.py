"""Bilingual Windows desktop UI for local transcription. No external AI APIs."""
from __future__ import annotations

from pathlib import Path
import queue
import shutil
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from whisper_local import OperationCancelled, TranscriptionError, TranscriptionJob, transcribe

STRINGS = {
    "ja": {
        "title": "Local Speech Studio — オフライン文字起こし", "intro": "音声・動画 → 文字起こし（TXT）と字幕（SRT）。外部AI APIを使わず、PC内で処理します。",
        "input": "音声・動画ファイル", "model": "Whisperモデル (.bin)", "cli": "whisper-cli 実行ファイル", "ffmpeg": "ffmpeg 実行ファイル",
        "output": "保存先フォルダ", "browse": "参照", "language": "認識言語", "start": "文字起こし開始", "cancel": "キャンセル",
        "ready": "準備完了。必要な4つのファイル／フォルダを指定してください。", "converting": "音声を変換しています…", "transcribing": "文字起こし中…（数分以上かかる場合があります）",
        "saving": "保存しています…", "done": "完了しました。TXTとSRTを保存しました。", "cancelled": "キャンセルしました。",
        "error": "エラー", "success": "完了", "need_input": "音声・モデル・保存先を指定してください。", "note": "必要：whisper.cpp の whisper-cli、GGMLモデル、FFmpeg（それぞれ利用者が指定）。モデル同梱なし。",
        "closing": "処理停止中…", "auto": "自動判定", "jp": "日本語", "en": "英語",
    },
    "en": {
        "title": "Local Speech Studio — Offline Transcription", "intro": "Audio/video → transcript (TXT) and subtitles (SRT). Runs on your PC without external AI APIs.",
        "input": "Audio / video file", "model": "Whisper model (.bin)", "cli": "whisper-cli executable", "ffmpeg": "ffmpeg executable",
        "output": "Output folder", "browse": "Browse", "language": "Audio language", "start": "Start transcription", "cancel": "Cancel",
        "ready": "Ready. Select the required files and folder.", "converting": "Converting audio…", "transcribing": "Transcribing… (this may take several minutes)",
        "saving": "Saving…", "done": "Done. TXT and SRT have been saved.", "cancelled": "Cancelled.",
        "error": "Error", "success": "Complete", "need_input": "Select audio, model and output folder.", "note": "Required: whisper.cpp whisper-cli, GGML model and FFmpeg (user-provided). No model bundled.",
        "closing": "Stopping processing…", "auto": "Auto detect", "jp": "Japanese", "en": "English",
    },
}


class TranscriberApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        # Legibility-first desktop sizing; native Windows control styling, no external UI framework.
        from tkinter import font as tkfont
        tkfont.nametofont("TkDefaultFont").configure(family="Segoe UI", size=11)
        style = ttk.Style(root)
        style.configure(".", font=("Segoe UI", 11))
        style.configure("TButton", padding=(12, 7))
        style.configure("TNotebook.Tab", padding=(16, 8))
        self.locale = tk.StringVar(value="ja")
        self.audio = tk.StringVar()
        self.model = tk.StringVar()
        self.cli = tk.StringVar(value=shutil.which("whisper-cli") or "")
        self.ffmpeg = tk.StringVar(value=shutil.which("ffmpeg") or "")
        self.output = tk.StringVar(value=str(Path.home() / "Documents") if (Path.home() / "Documents").is_dir() else str(Path.home()))
        self.audio_language = tk.StringVar(value="auto")
        self.status = tk.StringVar()
        self.events: queue.Queue[tuple] = queue.Queue()
        self.cancel = threading.Event()
        self.running = False
        self.close_requested = False
        self.labels: dict[str, ttk.Label] = {}
        self.browse_buttons: list[ttk.Button] = []
        self.entry_widgets: list[ttk.Entry] = []
        self._build()
        self._translate()
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self.root.after(120, self._poll)

    def _build(self) -> None:
        self.root.minsize(700, 470)
        self.root.geometry("850x535")
        container = ttk.Frame(self.root, padding=18)
        container.pack(fill="both", expand=True)
        top = ttk.Frame(container)
        top.pack(fill="x")
        self.intro_label = ttk.Label(top, wraplength=690)
        self.intro_label.pack(side="left", fill="x", expand=True)
        ttk.Combobox(top, values=["ja", "en"], textvariable=self.locale, width=5, state="readonly").pack(side="right", padx=5)
        self.locale.trace_add("write", lambda *_: self._translate())
        ttk.Separator(container).pack(fill="x", pady=10)
        grid = ttk.Frame(container)
        grid.pack(fill="x")
        grid.columnconfigure(1, weight=1)
        for row, (key, variable, kind) in enumerate([
            ("input", self.audio, "audio"), ("model", self.model, "model"),
            ("cli", self.cli, "cli"), ("ffmpeg", self.ffmpeg, "ffmpeg"),
            ("output", self.output, "directory"),
        ]):
            label = ttk.Label(grid, width=24)
            label.grid(row=row, column=0, sticky="w", pady=7)
            self.labels[key] = label
            entry = ttk.Entry(grid, textvariable=variable)
            entry.grid(row=row, column=1, sticky="ew", padx=(4, 10), pady=7)
            self.entry_widgets.append(entry)
            button = ttk.Button(grid, command=lambda v=variable, k=kind: self._browse(v, k))
            button.grid(row=row, column=2, sticky="ew", pady=7)
            self.browse_buttons.append(button)
        row = ttk.Frame(container)
        row.pack(fill="x", pady=(12, 6))
        self.language_label = ttk.Label(row)
        self.language_label.pack(side="left", padx=(0, 15))
        self.language_box = ttk.Combobox(row, textvariable=self.audio_language, values=["auto", "ja", "en"], state="readonly", width=12)
        self.language_box.pack(side="left")
        self.start_button = ttk.Button(row, command=self._start)
        self.start_button.pack(side="right")
        self.cancel_button = ttk.Button(row, command=self._cancel, state="disabled")
        self.cancel_button.pack(side="right", padx=8)
        self.bar = ttk.Progressbar(container, mode="indeterminate")
        self.bar.pack(fill="x", pady=(16, 5))
        ttk.Label(container, textvariable=self.status, wraplength=790).pack(anchor="w")
        self.note_label = ttk.Label(container, wraplength=790, foreground="#555555")
        self.note_label.pack(anchor="w", pady=(10, 0))

    def _translate(self):
        d = STRINGS[self.locale.get()]
        self.root.title(d["title"])
        self.intro_label.configure(text=d["intro"])
        for k, label in self.labels.items():
            label.configure(text=d[k])
        for b in self.browse_buttons:
            b.configure(text=d["browse"])
        self.language_label.configure(text=d["language"])
        self.start_button.configure(text=d["start"])
        self.cancel_button.configure(text=d["cancel"])
        self.note_label.configure(text=d["note"])
        if not self.running:
            self.status.set(d["ready"])

    def _browse(self, variable: tk.StringVar, kind: str):
        if kind == "directory":
            result = filedialog.askdirectory()
        elif kind == "audio":
            result = filedialog.askopenfilename(filetypes=[("Audio / Video", "*.wav *.mp3 *.m4a *.flac *.ogg *.mp4 *.mkv *.webm *.aac *.wma"), ("All files", "*.*")])
        elif kind == "model":
            result = filedialog.askopenfilename(filetypes=[("GGML model", "*.bin"), ("All files", "*.*")])
        else:
            result = filedialog.askopenfilename(filetypes=[("Programs", "*.exe"), ("All files", "*.*")])
        if result:
            variable.set(result)

    def _start(self):
        if self.running:
            return
        d = STRINGS[self.locale.get()]
        if not self.audio.get().strip() or not self.model.get().strip() or not self.output.get().strip():
            messagebox.showerror(d["error"], d["need_input"])
            return
        job = TranscriptionJob(
            audio=Path(self.audio.get()), model=Path(self.model.get()),
            whisper_cli=self.cli.get(), ffmpeg=self.ffmpeg.get(),
            output_directory=Path(self.output.get()), language=self.audio_language.get(),
        )
        self.cancel = threading.Event()
        self._set_running(True)
        threading.Thread(target=self._worker, args=(job, self.cancel), daemon=True).start()

    def _worker(self, job: TranscriptionJob, cancel: threading.Event):
        try:
            result = transcribe(job, cancel=cancel, on_stage=lambda stage: self.events.put(("stage", stage)))
            self.events.put(("success", result))
        except OperationCancelled:
            self.events.put(("cancelled", None))
        except (TranscriptionError, OSError, ValueError) as exc:
            self.events.put(("error", str(exc)))
        except Exception as exc:
            self.events.put(("error", f"Unexpected error: {type(exc).__name__}: {exc}"))

    def _set_running(self, running: bool):
        self.running = running
        self.start_button.configure(state="disabled" if running else "normal")
        self.cancel_button.configure(state="normal" if running else "disabled")
        self.language_box.configure(state="disabled" if running else "readonly")
        for widget in self.entry_widgets:
            widget.configure(state="disabled" if running else "normal")
        for widget in self.browse_buttons:
            widget.configure(state="disabled" if running else "normal")
        if running:
            self.bar.start(12)
        else:
            self.bar.stop()

    def _cancel(self):
        if self.running:
            self.cancel.set()
            self.status.set(STRINGS[self.locale.get()]["closing"])
            self.cancel_button.configure(state="disabled")

    def _poll(self):
        try:
            while True:
                event, value = self.events.get_nowait()
                d = STRINGS[self.locale.get()]
                if event == "stage":
                    self.status.set(d[value])
                elif event in {"success", "cancelled", "error"}:
                    self._set_running(False)
                    if self.close_requested:
                        self.root.destroy()
                        return
                    if event == "success":
                        self.status.set(d["done"])
                        messagebox.showinfo(d["success"], f"{d['done']}\n\n{value[0]}\n{value[1]}")
                    elif event == "cancelled":
                        self.status.set(d["cancelled"])
                    else:
                        self.status.set(d["error"])
                        messagebox.showerror(d["error"], str(value))
        except queue.Empty:
            pass
        self.root.after(120, self._poll)

    def _close(self):
        if self.running:
            self.close_requested = True
            self._cancel()
        else:
            self.root.destroy()


def main():
    root = tk.Tk()
    TranscriberApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
