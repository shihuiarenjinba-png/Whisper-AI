> **2026-10-25 最新確認・引継ぎ追記（優先）**  
> 以下の「2026-10-24原文」は当時の未検証状況を示す履歴です。最新状態として使わないでください。現行の完了・HOLD判定はこの追記と `docs/WINDOWS_QA_2026-10-25.md` を優先してください。
>
> **販売/Store認定提出は依然HOLD。GitHub Actionsが成功したのは未署名QA用EXEまでです。**

## A. 2026-10-25 GitHub直接再確認済み

- Repo: `shihuiarenjinba-png/Whisper-AI`（Public）、GitHub接続: `shihuiarenjinba-png`
- **引継ぎ元HEAD（この追記前）**: `3c4e9f797eb19a3d5742f46169aeb2abc7833936`。直前の実装: `1b5d6cd5f0386884040a4bdb9f91fb48878af6d5`。
- **作業対象**: `codex/whisper-youtube-media-20261024`。デフォルトブランチは `codex/offline-whisper-mvp-20261024` であり、作業対象と異なる。ブランチ名とHEADは作業開始時に再確認。
- **Windows Actions**: https://github.com/shihuiarenjinba-png/Whisper-AI/actions/runs/40138293356 （source SHA `3c4e9f7…` / `test-and-build` SUCCESS）。Actions実ログで **19 tests OK**、Python構文チェック、Windows/Python 3.12のPyInstaller未署名EXE作成、artifactアップロードを確認。
- **直近artifact**: `LocalSpeechStudio_QA_UNSIGNED_Windows_x64` / artifact ID `12577332520` / ZIP digest `SHA-256 D468A55D3884984F8923F2EE73CD1DE1C8C6BA6500810BE6D3B6A430939B31B9`（GitHub API/Actions実ログ一致）。GitHub記録で `expired=false`、有効期限 `2026-10-31T22:23:20Z`。期限切れなら同じHEADもしくは更新後のHEADでActionsを再実行し、その新artifactのSHAを検証。
- **Actions EXE SHA-256**: `625494037EF9AEF6A9890CC9CB8F2674E265528AFFB434C5CBB2033BD5D76BF4` は前担当者の最終報告記録値。**本追記作成時にはZIP中EXEを独立に再ハッシュしていない**ため、配布判断時は実物から再計算すること。
- `docs/screenshots/` に4枚のWindows GUI画像がGitHub上で存在することを確認: `windows-ja-1280x720-fit.png`、`windows-en-1024x768-fit.png`、`windows-en-youtube-scrollable.png`、`windows-en-youtube-scrolled.png`。実機目視完了との報告はQA記録にあるが、本追記でスクリーンショットの視認を再実施したものではない。
- README、`THIRD_PARTY_NOTICES.md`、`.github/workflows/windows-qa.yml`、`app.py`、`whisper_local/core.py`、`whisper_local/media_url.py` とテストをGitHubから確認。日本語/英語UI、ローカル音声・動画、任意の権利確認済みYouTube URL、16kHz変換、TXT/SRT、キャンセル、モデル事前検証、ユーザー提供の外部ランタイムというMVP仕様に整合。

### Windows実モデルQA（以前の担当者の測定記録を引継ぎ）

`docs/WINDOWS_QA_2026-10-25.md` によると、Windows 11 Pro / Intel Core Ultra 7 265K / RAM約31.5GiB、whisper.cpp 1.9.4と多言語`ggml-base.bin`によって**模擬ではない**MP4→FFmpeg→whisper-cli→TXT/SRTが日英とも成功。アプリ全体の処理時間: 日本語1.276秒、英語1.314秒。Whisper CLI 3回の平均: 日本語1.170秒、英語1.067秒。平均マシンCPU: 日本語15.7–16.6%、英語15.0–15.7%。観測最大ワーキングセット: 日本語301.8MiB、英語303.4MiB。60秒英語音声3.956秒、キャンセル時残留ファイルなし。これは自作合成音声を使った限定結果であり、**一般音声の認識精度、WER/CER、低性能PC性能の証明ではない**。正答率を推定で付けない。

### 依然HOLDの事項

- 実際にYouTubeから動画を正規取得する**陽性ネットワーク試験**: 許諾およびYouTube利用条件を確認できる自作URLがないため未実施。現状はURL/権限判定とダウンロード模擬試験、正規自作MP4のローカル入力のみ。
- Store Package/Identity、Publisher、PFN、Store Version: **未確認**。MSIX候補は**未生成**。これらの値を推測・他製品から流用しない。
- コード署名、WACK、MSIX実機インストール/アンインストール、Partner Center登録・認定・公開、Stripe販売公開: **未実施**。
- 商用配布対象（Python/Tcl-Tk/PyInstaller/whisper.cpp/FFmpeg/yt-dlp/モデル）の正確なバージョン・権利・ライセンス条文・SBOM・同梱条件は最終未確定。現行EXEがWhisperモデルやFFmpeg/whisper-cliを自動同梱するわけではない。
- 実環境録音/雑音/長時間、低性能PC、GPU構成、アクセシビリティ、初回導入とエラー回復の追加評価は未完了。

## B. 次のコード担当が実行する順番（済んだ試験のやり直しを目的にしない）

1. 指定GitHubアカウントで対象ブランチの**その時点のリモートHEAD**、README、現行QA文書、ワークフロー、成果物の期限とSHAを再確認。別の作業ディレクトリの未コミット変更には触れない。`main`/`release`およびデフォルトMVPブランチへの直接変更は禁止。
2. **まず商用導線のボトルネックを解消**: 初回に必要な `whisper-cli.exe`、GGMLモデル、`ffmpeg.exe` の導入/選択を初心者でも迷わない方式に改善。無断ダウンロードや無許諾バイナリの同梱は避け、同梱・ダウンロード案をそれぞれライセンス/供給元/チェックサムを確認して採否決定。外部AI API/従量課金を追加しない。
3. **機能の回帰と商用耐久QA**: 日英実音声・雑音・長尺・低スペック・日本語ファイルパス・権限エラー・ディスク容量不足・キャンセル/再起動/再試行・既存出力を保護。YouTubeは権利/規約を満たす自作動画が用意できる場合だけ実取得試験を行い、無ければHOLDのままローカルMP4で進める。ネットワーク取得のサイズ/時間制限が未知メタデータや途中エラーでも十分かを見直す。
4. **表示と商品品質**: 日本語/英語の全ダイアログとエラー、1024×768と1280×720、DPI倍率変更、縦スクロール、キーボード/アクセシビリティ、TXT/SRT出力を確認。既存スクリーンショットは素材として再利用し、変更後だけ撮り直す。
5. **配布設計とOSS監査**: 正確な版数とライセンス本文/NOTICE/SBOM/出所/各SHAを台帳化。開発用`QA_UNSIGNED`表記を維持し、同梱しない依存がある場合は販売説明とインストール案内に明記。ローカル音声ファイルやログの外部送信はしない。
6. 作業ブランチ内で修正→ユニットテスト→Windows Actions→EXE起動確認→artifact本体と`SHA256SUMS.txt`の再照合→SHA/スクリーンショットを報告。可能な工程は調査だけで終えない。
7. MSIXは**対象アプリの実在Store Identity/Publisher/PFN/Versionを一次資料で確認できた場合のみ**候補生成。未知ならHOLDにし、Microsoft Store/Stripe公開へ進まない。

## C. 最終報告の必須項目

最新HEAD SHA、変更ファイル/コミット、テスト実数、Windows Actions Run URLと各ステップ、署名区分、artifact名/ID/期限、EXEとZIPの実測SHA-256、実モデルの言語別実測・文字起こし結果、画面画像、ライセンス配布判定、MSIX/Storeゲート、未完了項目、次の具体アクション。

---

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
