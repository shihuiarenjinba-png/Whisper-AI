# Whisper-AI — コード担当引継ぎ・実行指示
作成: 2026-10-24 (Asia/Tokyo) / 状態: **開発・QA段階 / 販売・認定提出 HOLD**

## 0. 重要事項
この文書はソース確認とローカルQAに基づく。**本物のWhisperモデルを用いた音声認識、Windows実機、Windows Actions成功、MSIX、署名、WACK、Partner Center公開は未確認または未実施**。模擬認識と本物の音声認識を混同しないこと。
**外部AI APIなし、従量課金なし、ローカルでの音声認識**が製品方針。Ollamaは不要、将来任意の要約用として検討可能。モデル自体はユーザー提供を想定。

## 1. 対象とGit情報
- Owner: `shihuiarenjinba-png`
- Repo: https://github.com/shihuiarenjinba-png/Whisper-AI
- Visibility: Public（2026-10-24 GitHub確認）
- **今回の作業元・引継ぎ対象**: `codex/whisper-youtube-media-20261024`
- GitHubで確認した**デフォルトブランチ**: `codex/offline-whisper-mvp-20261024`（通常の main ではないので注意）
- 既存MVPブランチ: `codex/offline-whisper-mvp-20261024`
- 対応版リンク: https://github.com/shihuiarenjinba-png/Whisper-AI/tree/codex/whisper-youtube-media-20261024
- **main / release へ直接変更禁止**。引継ぎ対象ブランチを取得し、さらに必要ならそのHEADから別の `codex/` 作業ブランチを作ること。すでにこのブランチで進行中の変更がある場合は差分を調べてから作業すること。
- 実作業前に `git status`、`git branch -vv`、`git rev-parse HEAD`、リモートHEADを記録。コミットSHAやリポジトリの状態を推測しないこと。
- GitHubアカウントは `shihuiarenjinba-png` 接続を使うこと。

## 2. 既存コード・構成
- `app.py` — Tkinter日本語/英語UI。ローカル音声・動画とYouTube URLの入力切替、言語選択、キャンセル、状態表示
- `whisper_local/core.py` — FFmpegによる16 kHzモノラルWAV変換、ユーザー指定`whisper-cli`実行、TXT/SRT保存、既存ファイルの上書き防止、一時ファイル削除、キャンセル
- `whisper_local/media_url.py` — 明示的な権限確認後の任意YouTube入力。単一HTTPS動画URLのみ許可し、`yt-dlp`をユーザー指定して取得後にローカル音声処理へ
- `whisper_local/__init__.py` — パッケージ公開インターフェース
- `tests/test_core.py`、`tests/test_media_url.py` — コア・URL検証・権限ゲート・模擬取得・キャンセル等のテスト
- `scripts/video_smoke_qa.py` — テスト動画生成、実FFmpeg音声抽出、模擬Whisper認識出力によるTXT/SRT保存確認
- `.github/workflows/windows-qa.yml` — `codex/**` push/手動でWindowsテスト・PyInstaller未署名QA EXE作成・artifactアップロードを試行する設定
- `README.md`、`THIRD_PARTY_NOTICES.md`、`.gitignore`

現在のYouTube入力は許諾のある動画に限り、HTTPSのYouTube/youtu.beのwatch/shorts/live単一動画形式を検証する。リストや任意ホストを拒否し、20分/200MiB制限を設け、Cookie/DRM/認証回避は実装しない。YouTubeへの取得時のみネットワークを利用し、**音声認識そのものはローカル**。利用規約への適合を各動画・各利用形態で確認し、取得不可時は正規に入手したローカルファイルを案内する。権限確認チェックだけで第三者動画の取得を許可されたものとみなさないこと。

## 3. 必要環境と実行
- Windows 10/11 / 開発時 Python 3.12 (Tkinter)
- ユーザー指定の `whisper-cli.exe`（https://github.com/ggml-org/whisper.cpp）
- ユーザー指定の多言語GGML `.bin`モデル（日本語で`.en.bin`モデルを使用しない）
- `ffmpeg.exe`（https://ffmpeg.org/）
- YouTube任意機能のみ `yt-dlp` 実行体（利用規約・ライセンス確認が前提）
- 外部AI API、OpenAI APIキー、Ollamaは必須ではない。モデル/ランタイム/動画は現行コードでは基本的に同梱しない。

コマンド:
```powershell
git clone https://github.com/shihuiarenjinba-png/Whisper-AI.git
cd Whisper-AI
git fetch origin
git switch codex/whisper-youtube-media-20261024
py -3.12 -m unittest discover -s tests -v
py -3.12 -m compileall -q app.py whisper_local
py -3.12 app.py
# FFmpegのある環境では: py -3.12 scripts/video_smoke_qa.py
```
URL経由の処理は利用規約・権利を確認できる動画だけを対象とし、試験時に無断取得を行わない。

## 4. 今回までに確認したQA
- **16/16 unittest PASS**：2026-10-24ローカル（Linux/Python 3.13系）。URL正常・異常系、権限未確認拒否、模擬ダウンロード、キャンセル、衝突回避、模擬文字起こし等
- **動画スモークPASS**：実際のMP4からFFmpegでPCM WAVを抽出 → **模擬**認識 → TXT/SRT生成。ネットワーク不要
- `python -m compileall -q app.py whisper_local` PASS
- 音声・動画テスト素材は会話の `Whisper_AI_Offline_Test_Demo.mp4`、ソース同梱ZIP `WhisperAI_YouTube_Video_QA_Source.zip` を参照。ZIPのサンプルは作成済みの人工テスト動画で、YouTube実取得の証拠ではない。
- **未検証**：実際のGGMLモデルと本物のWhisper CLIでの日英認識、精度・処理時間、GPU対応、YouTube実取得、Windows Actions完走/成果物、Windows実機、MSIX/Store。
- 現行GitHub Actionsファイルは存在するが、Actionsの成功およびEXE artifactの存在は**未確認**。成功と表記禁止。

## 5. コード担当に依頼する順序（調査だけで終わらせない）
**P0-1 — ソース・台帳整合**:
- 引継ぎ対象ブランチの最新HEAD、変更内容、README、workflowを照合する。
- **GitHub上READMEに「ネットワークコードはない」等、YouTube機能導入前の説明が残存**。現在は任意のYouTube取得のみネットワークアクセスを行う。README/第三者ライセンス通知/プライバシー説明を現実の機能に合わせて修正（`yt-dlp`を含む）。
- ライセンス・ソース同梱範囲を監査し、未確認事項はHOLD表示。

**P0-2 — 実モデルによるWindows検証**:
- 権利・ライセンスを確認した短い日本語音声と英語音声（10–60秒など）を準備。自身で録音・合成した素材を優先。
- 実際の `whisper-cli.exe` と多言語モデルでTXT/SRTを生成し、文字列・時刻・実行時間・RAM/CPU使用を記録。再起動後/長い音声でも実行。
- 重要語、聞き取れない区間、固有名詞の誤認識を可視化。内部スコアを校正なしで「正答率○%」に変換しない。
- 正常・失敗・キャンセル・再試行・上書き防止、日本語パス、低スペック環境もテスト。

**P0-3 — YouTubeとローカル動画**:
- 権利とサービス利用条件を満たす自作テスト動画だけで、YouTube URL→取得→FFmpeg→実モデル→TXT/SRTをWindows上で検証。
- 取得権限が確認できない動画はダウンロードしない。制限や利用規約に反する経路は実装せず、ローカルファイル方式を代替とする。
- `yt-dlp`未配置、規約・権限未確認、非YouTube URL、不正URL、長時間動画、過大ファイル、動画削除、通信遮断、途中キャンセル、後片付けの確認。

**P1 — 販売向けUI/配布**:
- 一般利用者向けの設定案内（Whisper CLI、モデル、FFmpeg、YouTube任意時のyt-dlp）。不要な手順は削減。日本語/英語切替。
- 1024×768 / 1280×720で主要操作が画面外に出ないこと、タブ等必要最小限のUI改善、音声と字幕のプレビュー・修正・保存・明確なエラー説明。
- GitHub ActionsでWindows x64テストを実行し、`LocalSpeechStudio_QA_UNSIGNED.exe` artifactを入手、SHA-256、実機起動・停止・再起動、ログ・画面キャプチャを記録。
- Store向けMSIX候補は**実在確認したPublisher/Identity/PFN/Store Versionのみ**利用。推測禁止。不明ならHOLD。署名、インストールQA、WACK、1024×768/1280×720、Partner Centerへの登録は別ゲート。
- Windowsランタイム実測と依存配布権利が解消するまで**販売・公開・本番Payment Link作成はHOLD**。

## 6. OSS・法務上の確認
- `whisper.cpp` upstream: https://github.com/ggml-org/whisper.cpp （使用revisionとライセンス同梱が必要）
- `FFmpeg` buildの配布条件: https://ffmpeg.org/legal.html （構成ごとにLGPL/GPLなど確認）
- `yt-dlp` upstream: https://github.com/yt-dlp/yt-dlp （同梱する場合は対象バージョン・依存物・ライセンス確認）
- GGMLモデルの出所・再配布条件・SHA-256を確認。
- 本家Whisper/OpenAI公式製品だと誤認させない名称・UI・表記にする。
- YouTubeの動画・音声の著作権だけでなく、YouTubeのサービス利用条件も確認する。
- 生データ・文字起こし結果・プライベートなログの無断送信禁止。クラウドAI APIは導入しない。

## 7. 最終報告で必須の証跡
1. repository / branch / remote HEAD / 変更ファイル / 未コミット差分
2. テスト実行コマンドと実際の件数・成功失敗
3. 日英の実モデル検証ログ（サンプルの利用権限、実文字起こし結果、速度・メモリ）
4. 動画URLテスト（許諾・利用条件・取得成功/失敗理由）
5. GitHub Actions run URL、各step結果、artifact名・ダウンロード先・SHA-256
6. Windows実機QA（1024×768・1280×720スクリーンショット）
7. OSS版数・ライセンス・配布元・SBOM/NOTICES
8. EXE/MSIXの区別、署名/Store Identity/WACK/Partner Centerの未完了状態
9. 現在の不具合とHOLD理由、**次の具体的アクション**

販売・公開を承認したと勝手に判断しない。既存の実装・ブランチ・ユーザーデータを保護しながら、可能な範囲はコミット→Windows QA→成果物まで前進すること。
