"""Bilingual Windows desktop UI for local transcription. No external AI APIs."""
from __future__ import annotations

import os
from pathlib import Path
import queue
import shutil
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from whisper_local import (
    OperationCancelled, TranscriptionError, TranscriptionJob, YouTubeJob,
    transcribe, transcribe_youtube, validate_youtube_job,
)
from whisper_local.core import validate
from whisper_local.preferences import load_preferences, save_preferences

STRINGS = {
    "ja": {
        "title": "Local Speech Studio — オフライン文字起こし", "intro": "音声・動画 → 文字起こし（TXT）と字幕（SRT）。外部AI APIを使わず、PC内で処理します。",
        "input": "音声・動画ファイル", "model": "Whisperモデル (.bin)", "cli": "whisper-cli 実行ファイル", "ffmpeg": "ffmpeg 実行ファイル",
        "output": "保存先フォルダ", "browse": "参照", "language": "認識言語", "start": "文字起こし開始", "cancel": "キャンセル",
        "ready": "準備完了。必要な4つのファイル／フォルダを指定してください。", "converting": "音声を変換しています…", "transcribing": "文字起こし中…（数分以上かかる場合があります）",
        "saving": "保存しています…", "done": "完了しました。TXTとSRTを保存しました。", "cancelled": "キャンセルしました。",
        "error": "エラー", "success": "完了", "need_input": "音声・モデル・保存先を指定してください。", "note": "必要：whisper.cpp の whisper-cli、GGMLモデル、FFmpeg（それぞれ利用者が指定）。モデル同梱なし。",
        "closing": "処理停止中…", "auto": "自動判定", "jp": "日本語", "en": "英語",
        "source": "入力方法", "local": "PC内の音声・動画", "youtube": "YouTube URL（許可のある動画のみ）",
        "url": "YouTube動画URL", "ytdlp": "yt-dlp 実行ファイル", "downloading": "許可された動画から音声を取得しています…",
        "rights": "自分に保存・文字起こしの権限があり、YouTubeの利用規約にも適合することを確認しました。",
        "rights_needed": "YouTube動画を使用するための権限・利用条件を確認してください。",
        "youtube_notice": "YouTube取得は任意機能です。動画の権利と利用規約に従ってください。yt-dlpは利用者が用意し、\n認証・DRM回避は行いません。リンクからの取得に失敗する場合は正規に入手したファイルを選択してください。",
        "source_section": "1. 入力を選ぶ", "settings_section": "2. ローカル処理の設定", "result_section": "結果プレビュー",
        "setup_steps": "はじめに：入力 → 多言語モデル → whisper-cli → FFmpeg → 保存先の順に指定します。YouTube入力時だけyt-dlpが必要です。",
        "check": "設定を確認", "check_ok": "設定を確認しました。ネットワーク接続や文字起こしはまだ開始していません。",
        "help": "設定の説明", "help_title": "初回設定", "open_folder": "保存先を開く",
        "help_text": "1. whisper.cppのwhisper-cli.exeを用意します。\n2. 日本語には .en.bin ではない多言語GGMLモデルを選びます。\n3. ffmpeg.exeを用意します。\n4. YouTube入力を使う場合だけyt-dlp.exeを用意します。\n\nこのアプリはモデルやツールを自動取得しません。配布元・ライセンス・SHA-256を確認してください。\n設定確認後にツールの場所をPC内に記録します。動画URLや権限のチェック状態は記録しません。",
        "missing": "次の必須項目を指定してください：{items}", "preview_empty": "文字起こし完了後、ここにTXTの内容を表示します。",
    },
    "en": {
        "title": "Local Speech Studio — Offline Transcription", "intro": "Audio/video → transcript (TXT) and subtitles (SRT). Runs on your PC without external AI APIs.",
        "input": "Audio / video file", "model": "Whisper model (.bin)", "cli": "whisper-cli executable", "ffmpeg": "ffmpeg executable",
        "output": "Output folder", "browse": "Browse", "language": "Audio language", "start": "Start transcription", "cancel": "Cancel",
        "ready": "Ready. Select the required files and folder.", "converting": "Converting audio…", "transcribing": "Transcribing… (this may take several minutes)",
        "saving": "Saving…", "done": "Done. TXT and SRT have been saved.", "cancelled": "Cancelled.",
        "error": "Error", "success": "Complete", "need_input": "Select audio, model and output folder.", "note": "Required: whisper.cpp whisper-cli, GGML model and FFmpeg (user-provided). No model bundled.",
        "closing": "Stopping processing…", "auto": "Auto detect", "jp": "Japanese", "en": "English",
        "source": "Input source", "local": "Local audio / video", "youtube": "YouTube URL (authorized only)",
        "url": "YouTube video URL", "ytdlp": "yt-dlp executable", "downloading": "Obtaining audio from an authorized video…",
        "rights": "I have the necessary rights to download/transcribe this video and comply with YouTube's terms.",
        "rights_needed": "Confirm authorization and applicable YouTube terms first.",
        "youtube_notice": "YouTube import is optional. You must follow copyright and YouTube terms. Supply yt-dlp yourself;\nno authentication or DRM bypass. If importing fails, use a legitimately obtained local media file.",
        "source_section": "1. Choose input", "settings_section": "2. Local processing setup", "result_section": "Result preview",
        "setup_steps": "Start here: choose the input, multilingual model, whisper-cli, FFmpeg and output folder. yt-dlp is needed only for YouTube input.",
        "check": "Check setup", "check_ok": "Setup looks ready. No network access or transcription was started.",
        "help": "Setup help", "help_title": "First-time setup", "open_folder": "Open output folder",
        "help_text": "1. Obtain whisper-cli.exe from whisper.cpp.\n2. For Japanese, choose a multilingual GGML model, not an .en.bin model.\n3. Obtain ffmpeg.exe.\n4. yt-dlp.exe is needed only for YouTube input.\n\nThe app does not download tools or models. Verify each source, license and SHA-256.\nSuccessful setup checks remember local tool paths, not video URLs or permission consent.",
        "missing": "Provide these required items: {items}", "preview_empty": "The TXT result will appear here after transcription.",
    },
}


class TranscriberApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        prefs = load_preferences()
        self.locale = tk.StringVar(value=prefs.get("locale", "ja"))
        self.audio = tk.StringVar()
        self.source_mode = tk.StringVar(value="file")
        self.youtube_url = tk.StringVar()
        self.ytdlp = tk.StringVar(value=prefs.get("ytdlp") or shutil.which("yt-dlp") or "")
        self.rights_confirmed = tk.BooleanVar(value=False)
        self.model = tk.StringVar(value=prefs.get("model", ""))
        self.cli = tk.StringVar(value=prefs.get("cli") or shutil.which("whisper-cli") or "")
        self.ffmpeg = tk.StringVar(value=prefs.get("ffmpeg") or shutil.which("ffmpeg") or "")
        self.output = tk.StringVar(value=prefs.get("output") or (str(Path.home() / "Documents") if (Path.home() / "Documents").is_dir() else str(Path.home())))
        self.audio_language = tk.StringVar(value=prefs.get("audio_language", "auto"))
        self.status = tk.StringVar()
        self.events: queue.Queue[tuple] = queue.Queue()
        self.cancel = threading.Event()
        self.running = False
        self.close_requested = False
        self.last_output_directory: Path | None = None
        self.preview_has_result = False
        self.labels: dict[str, ttk.Label] = {}
        self.field_rows: dict[str, tuple[ttk.Label, ttk.Entry, ttk.Button]] = {}
        self.browse_buttons: list[ttk.Button] = []
        self.source_buttons: list[ttk.Radiobutton] = []
        self.entry_widgets: list[ttk.Entry] = []
        self._build()
        self._translate()
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self.root.after(120, self._poll)

    def _build(self) -> None:
        self.root.minsize(720, 520)
        self.root.geometry("920x650")
        shell = ttk.Frame(self.root)
        shell.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(shell, highlightthickness=0)
        scrollbar = ttk.Scrollbar(shell, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        container = ttk.Frame(self.canvas, padding=18)
        window = self.canvas.create_window((0, 0), window=container, anchor="nw")
        container.bind("<Configure>", lambda _event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfigure(window, width=event.width))
        self.root.bind("<MouseWheel>", lambda event: self.canvas.yview_scroll(int(-event.delta / 120), "units"))
        top = ttk.Frame(container)
        top.pack(fill="x")
        self.intro_label = ttk.Label(top, wraplength=690)
        self.intro_label.pack(side="left", fill="x", expand=True)
        ttk.Combobox(top, values=["ja", "en"], textvariable=self.locale, width=5, state="readonly").pack(side="right", padx=5)
        self.locale.trace_add("write", lambda *_: self._translate())
        self.setup_label = ttk.Label(container, wraplength=840, foreground="#3b556f")
        self.setup_label.pack(fill="x", pady=(9, 8))
        self.source_section = ttk.LabelFrame(container, padding=10)
        self.source_section.pack(fill="x", pady=(0, 8))
        source_frame = ttk.Frame(self.source_section)
        source_frame.pack(fill="x", pady=(0, 6))
        self.source_label = ttk.Label(source_frame)
        self.source_label.pack(side="left", padx=(0, 12))
        self.source_local = ttk.Radiobutton(source_frame, variable=self.source_mode, value="file", command=self._refresh_source)
        self.source_local.pack(side="left", padx=(0, 20))
        self.source_youtube = ttk.Radiobutton(source_frame, variable=self.source_mode, value="youtube", command=self._refresh_source)
        self.source_youtube.pack(side="left")
        self.source_buttons = [self.source_local, self.source_youtube]
        grid = ttk.Frame(self.source_section)
        grid.pack(fill="x")
        grid.columnconfigure(1, weight=1)
        for row, (key, variable, kind) in enumerate([
            ("input", self.audio, "audio"),
            ("url", self.youtube_url, "url"),
            ("ytdlp", self.ytdlp, "cli"),
            ("model", self.model, "model"),
            ("cli", self.cli, "cli"), ("ffmpeg", self.ffmpeg, "ffmpeg"),
            ("output", self.output, "directory"),
        ]):
            label = ttk.Label(grid, width=24)
            label.grid(row=row, column=0, sticky="w", pady=7)
            self.labels[key] = label
            entry = ttk.Entry(grid, textvariable=variable)
            entry.grid(row=row, column=1, sticky="ew", padx=(4, 10), pady=7)
            self.entry_widgets.append(entry)
            if key == "input": self.local_entry = entry
            if key == "url": self.url_entry = entry
            if key == "ytdlp": self.ytdlp_entry = entry
            button = ttk.Button(grid, command=lambda v=variable, k=kind: self._browse(v, k))
            button.grid(row=row, column=2, sticky="ew", pady=7)
            self.browse_buttons.append(button)
            if key == "input": self.local_browse = button
            if key == "url":
                self.url_browse = button
                button.configure(state="disabled")  # URLs must be entered, not browsed
            if key == "ytdlp": self.ytdlp_browse = button
            self.field_rows[key] = (label, entry, button)
        self.youtube_options = ttk.Frame(self.source_section)
        self.rights_box = ttk.Checkbutton(self.youtube_options, variable=self.rights_confirmed)
        self.rights_box.pack(anchor="w", pady=(4, 0))
        self.youtube_notice = ttk.Label(self.youtube_options, wraplength=825, foreground="#555555")
        self.youtube_notice.pack(anchor="w", pady=(2, 0))

        self.settings_section = ttk.LabelFrame(container, padding=10)
        self.settings_section.pack(fill="x", pady=(0, 8))
        row = ttk.Frame(self.settings_section)
        row.pack(fill="x", pady=(2, 4))
        self.language_label = ttk.Label(row)
        self.language_label.pack(side="left", padx=(0, 15))
        self.language_box = ttk.Combobox(row, textvariable=self.audio_language, values=["auto", "ja", "en"], state="readonly", width=12)
        self.language_box.pack(side="left")
        self.start_button = ttk.Button(row, command=self._start)
        self.start_button.pack(side="right")
        self.cancel_button = ttk.Button(row, command=self._cancel, state="disabled")
        self.cancel_button.pack(side="right", padx=8)
        self.check_button = ttk.Button(row, command=self._check_setup)
        self.check_button.pack(side="right", padx=8)
        self.help_button = ttk.Button(row, command=self._show_help)
        self.help_button.pack(side="right")
        self.bar = ttk.Progressbar(self.settings_section, mode="indeterminate")
        self.bar.pack(fill="x", pady=(8, 5))
        ttk.Label(self.settings_section, textvariable=self.status, wraplength=790).pack(anchor="w")
        self.note_label = ttk.Label(self.settings_section, wraplength=790, foreground="#555555")
        self.note_label.pack(anchor="w", pady=(8, 0))

        self.result_section = ttk.LabelFrame(container, padding=10)
        self.result_section.pack(fill="both", expand=True)
        self.preview = tk.Text(self.result_section, height=6, wrap="word", relief="flat", background="#f5f7f9")
        self.preview.pack(fill="both", expand=True)
        self.preview.configure(state="disabled")
        self.open_button = ttk.Button(self.result_section, command=self._open_output, state="disabled")
        self.open_button.pack(anchor="e", pady=(6, 0))
        self._refresh_source()

    def _translate(self):
        d = STRINGS[self.locale.get()]
        self.root.title(d["title"])
        self.intro_label.configure(text=d["intro"])
        self.setup_label.configure(text=d["setup_steps"])
        self.source_section.configure(text=d["source_section"])
        self.settings_section.configure(text=d["settings_section"])
        self.result_section.configure(text=d["result_section"])
        self.source_label.configure(text=d["source"])
        self.source_local.configure(text=d["local"])
        self.source_youtube.configure(text=d["youtube"])
        self.rights_box.configure(text=d["rights"])
        self.youtube_notice.configure(text=d["youtube_notice"])
        for k, label in self.labels.items():
            label.configure(text=d[k])
        for b in self.browse_buttons:
            b.configure(text=d["browse"])
        self.language_label.configure(text=d["language"])
        self.start_button.configure(text=d["start"])
        self.cancel_button.configure(text=d["cancel"])
        self.check_button.configure(text=d["check"])
        self.help_button.configure(text=d["help"])
        self.open_button.configure(text=d["open_folder"])
        self.note_label.configure(text=d["note"])
        if not self.preview_has_result:
            self._set_preview(d["preview_empty"])
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

    def _refresh_source(self):
        youtube = self.source_mode.get() == "youtube"
        for key, show in (("input", not youtube), ("url", youtube), ("ytdlp", youtube)):
            for widget in self.field_rows[key]:
                if show:
                    widget.grid()
                else:
                    widget.grid_remove()
        # A URL is typed or pasted; there is intentionally no file picker for it.
        self.url_browse.grid_remove()
        if youtube:
            self.youtube_options.pack(fill="x", after=self.field_rows["ytdlp"][0].master)
        else:
            self.youtube_options.pack_forget()
        self.local_entry.configure(state="disabled" if youtube or self.running else "normal")
        self.local_browse.configure(state="disabled" if youtube or self.running else "normal")
        self.url_entry.configure(state="normal" if youtube and not self.running else "disabled")
        self.ytdlp_entry.configure(state="normal" if youtube and not self.running else "disabled")
        self.ytdlp_browse.configure(state="normal" if youtube and not self.running else "disabled")
        self.rights_box.configure(state="normal" if youtube and not self.running else "disabled")

    def _make_job(self) -> TranscriptionJob | YouTubeJob:
        d = STRINGS[self.locale.get()]
        youtube = self.source_mode.get() == "youtube"
        values = {
            "input": self.audio.get().strip(), "url": self.youtube_url.get().strip(),
            "ytdlp": self.ytdlp.get().strip(), "model": self.model.get().strip(),
            "cli": self.cli.get().strip(), "ffmpeg": self.ffmpeg.get().strip(),
            "output": self.output.get().strip(),
        }
        required = ["url", "ytdlp", "model", "cli", "ffmpeg", "output"] if youtube else ["input", "model", "cli", "ffmpeg", "output"]
        missing = [d[key] for key in required if not values[key]]
        if missing:
            raise TranscriptionError(d["missing"].format(items=", ".join(missing)))
        if youtube and not self.rights_confirmed.get():
            raise TranscriptionError(d["rights_needed"])
        common = dict(model=Path(values["model"]), whisper_cli=values["cli"], ffmpeg=values["ffmpeg"],
                      output_directory=Path(values["output"]), language=self.audio_language.get())
        if youtube:
            return YouTubeJob(url=values["url"], yt_dlp=values["ytdlp"], permission_confirmed=True, **common)
        return TranscriptionJob(audio=Path(values["input"]), **common)

    def _check_setup(self):
        d = STRINGS[self.locale.get()]
        try:
            job = self._make_job()
            validate_youtube_job(job) if isinstance(job, YouTubeJob) else validate(job)
        except (TranscriptionError, OSError, ValueError) as exc:
            messagebox.showerror(d["error"], str(exc))
            return
        self._remember_settings()
        self.status.set(d["check_ok"])
        messagebox.showinfo(d["success"], d["check_ok"])

    def _remember_settings(self):
        # Save only local tool paths and language; never remember media URLs or rights consent.
        save_preferences({
            "locale": self.locale.get(), "audio_language": self.audio_language.get(),
            "model": self.model.get(), "cli": self.cli.get(),
            "ffmpeg": self.ffmpeg.get(), "ytdlp": self.ytdlp.get(),
            "output": self.output.get(),
        })

    def _show_help(self):
        d = STRINGS[self.locale.get()]
        messagebox.showinfo(d["help_title"], d["help_text"])

    def _start(self):
        if self.running:
            return
        d = STRINGS[self.locale.get()]
        try:
            job = self._make_job()
        except TranscriptionError as exc:
            messagebox.showerror(d["error"], str(exc))
            return
        self.cancel = threading.Event()
        self._set_running(True)
        threading.Thread(target=self._worker, args=(job, self.cancel), daemon=True).start()

    def _worker(self, job: TranscriptionJob | YouTubeJob, cancel: threading.Event):
        try:
            worker = transcribe_youtube if isinstance(job, YouTubeJob) else transcribe
            result = worker(job, cancel=cancel, on_stage=lambda stage: self.events.put(("stage", stage)))
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
        for widget in self.source_buttons:
            widget.configure(state="disabled" if running else "normal")
        self._refresh_source()
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
                        self._remember_settings()
                        self.last_output_directory = Path(value[0]).parent
                        self.open_button.configure(state="normal")
                        self.preview_has_result = True
                        try:
                            self._set_preview(Path(value[0]).read_text(encoding="utf-8", errors="replace"))
                        except OSError:
                            self._set_preview(str(value[0]))
                        messagebox.showinfo(d["success"], f"{d['done']}\n\n{value[0]}\n{value[1]}")
                    elif event == "cancelled":
                        self.status.set(d["cancelled"])
                    else:
                        self.status.set(d["error"])
                        messagebox.showerror(d["error"], str(value))
        except queue.Empty:
            pass
        self.root.after(120, self._poll)

    def _set_preview(self, text: str):
        self.preview.configure(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", text)
        self.preview.configure(state="disabled")

    def _open_output(self):
        if not self.last_output_directory:
            return
        try:
            os.startfile(self.last_output_directory)
        except OSError as exc:
            messagebox.showerror(STRINGS[self.locale.get()]["error"], str(exc))

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
