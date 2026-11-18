# 開發紀錄

## 2026-11-18｜第一階段啟動

### 需求確認

已完整閱讀原始開發提示詞。第一階段優先交付主介面、SQLite/SQLAlchemy 資料層、AI Provider 管理與基本雙向翻譯。最終目標是以乾淨 Windows Runner 測試的 Portable EXE。

### 實作內容

- 建立 `src/korean_ai_workspace` 模組化 Python 專案。
- 建立可調整大小的 PySide6 主視窗、左側工作區導覽及翻譯中心。
- 建立 SQLite 資料庫與 `translation_history` 資料表。
- 建立 OpenAI Chat Completions 相容 Provider；Gemini 可透過使用者指定的相容 Endpoint 使用。
- 建立 AI JSON 翻譯結果解析，保護價格、數量、日期、型號、交期及商業承諾的提示規則。
- AI 失敗時不覆蓋原文，成功時保存原文與最佳翻譯。
- 建立 pytest 單元測試與 Windows GitHub Actions workflow。

### 環境限制

目前 Manus 開發環境是 Linux，不能宣稱已在 Windows 執行 EXE。Windows 測試及 EXE 產物由 GitHub Actions `windows-latest` 負責。

### 待驗證

- Linux 依賴安裝後的單元測試。
- GitHub Actions Windows Runner 的 GUI 依賴、測試與 PyInstaller 產物。
- 實際 AI API 連線需要使用者在本機輸入自己的 API Key。

### 2026-11-18 實測結果

- `pytest -q`：4 passed。
- `compileall`：通過。
- Qt offscreen 啟動檢查：通過，主視窗標題正確，六個工作區均建立成功。
- Linux PyInstaller spec 檢查：onedir 設定建置通過；Linux 產物不視為 Windows EXE，Windows EXE 仍必須由乾淨 Windows Runner 驗證。
- GitHub Actions Windows Runner：成功。乾淨 `windows-latest` 環境完成依賴安裝、4 個測試、Portable EXE 建置、EXE smoke test 及 Artifact 上傳。

## 2026-11-18｜第二階段

### 實作內容

- 主畫面以四個分頁顯示最佳、正式、自然及親切翻譯結果，四種結果全部保存於既有 SQLite 歷史資料表。
- 新增本機翻譯歷史搜尋，可搜尋原文與四種譯文；雙擊結果可載入主畫面及浮動視窗。
- 新增可重用浮動翻譯視窗。新翻譯會更新同一個視窗，支援四種版本切換、目前版本複製、釘選、滑鼠移入暫停倒數及預設 8 秒自動關閉。
- 搜尋使用 SQLAlchemy 對本機 SQLite 執行，不會把搜尋關鍵字傳給 AI。

### 第二階段實測結果

- `pytest -q`：7 passed。
- `compileall`：通過。
- 歷史搜尋資料 smoke test：原文與自然版本均可搜尋，四種結果均可讀回。
- Qt offscreen UI smoke test：主視窗、四個結果分頁與浮動翻譯視窗建立成功。
- GitHub Actions Windows Runner：成功。乾淨 `windows-latest` 環境完成 7 個測試、Portable EXE 建置、EXE smoke test 及 Artifact 上傳；實際 AI API 連線仍需要使用者自行輸入 API Key。

## 2026-11-18｜第三階段

### 實作內容

- 新增 `customers` 客戶資料表，保存公司名稱、韓文公司名稱、聯絡人、Email、公司資料、職稱、產業、溝通語氣與重要備註。
- 新增客戶中心，可新增、搜尋、修改及刪除客戶；刪除客戶時不刪除詞條，而是解除詞條的客戶關聯。
- 新增 `glossary_terms` 詞庫資料表，支援全域詞庫、分類詞庫與客戶專屬詞庫，以及指定繁中、指定韓文、禁止翻譯、強制套用、分類、備註與使用範例。
- 新增詞庫中心，可依範圍與分類搜尋、保存、修改及刪除詞條。
- 翻譯時只載入未指定客戶的全域／分類詞條與目前客戶的專屬詞條；同一韓文詞語由客戶專屬詞條優先覆蓋，其他客戶詞條不會進入提示。
- 翻譯歷史新增客戶關聯；既有 SQLite 資料庫使用加法式 migration 補上欄位，不刪除既有資料。

### 第三階段實測結果

- `pytest -q`：10 passed。
- `compileall`：通過。
- 客戶與詞庫資料保存、搜尋及刪除客戶後保留詞條：通過。
- A/B 客戶相同詞條隔離與詞庫優先權：通過。
- 客戶中心、詞庫中心與主介面 Qt offscreen smoke test：通過。
- GitHub Actions Windows Runner：成功。乾淨 `windows-latest` 環境完成 10 個測試、Portable EXE 建置、EXE smoke test 及 Artifact 上傳。

## 2026-11-18｜第四階段

### 實作內容

- 新增商務郵件資料表與郵件中心，支援選取客戶、手動貼上韓文郵件、保存主旨與原文。
- 新增 AI 郵件完整翻譯、摘要、語氣、對方需求及重要事項分析；價格、數量、日期、型號、交期與商業承諾要求保留，無法確定時標示[需確認]。
- 新增中文回覆意思輸入與正式、自然、親切三種韓文回信草稿。所有 AI 回信都保存為草稿，不宣稱已寄出。
- 新增郵件狀態：待處理、已翻譯、分析完成、回信撰寫中、草稿完成、已完成。
- 新增附件資料表與本機複製保存，單檔上限 100 MB，以 SHA-256 去重；相同內容可共用既有實體檔案。
- 附件支援開啟、解除郵件關聯與刪除實體檔案，解除關聯與刪除實體檔案分開處理；附件不解析、不上傳給 AI。
- SQLite 已啟用外鍵約束，刪除郵件會清理關聯列，但不會刪除仍被其他郵件共用的附件實體。

### 第四階段實測結果

- `pytest -q`：14 passed。
- `compileall`：通過。
- 郵件分析與三種回信草稿 JSON 解析及保存：通過。
- 郵件狀態與客戶關聯保存：通過。
- 附件 SHA-256 去重、郵件關聯及刪除保護：通過。
- 郵件中心 Qt 匯入與主介面 smoke test：通過。
- GitHub Actions Windows Runner：成功。Run `44235588030` 在乾淨 `windows-latest` 環境完成 14 個測試、Portable EXE 建置、EXE smoke test 及 Artifact 上傳。

## 2026-11-18｜第五階段

### 實作內容

- 新增系統管理中心，提供保存／載入 AI 設定、手動建立備份與從 ZIP 備份還原。
- 新增 `SecretStore`：Windows 使用原生 DPAPI；Linux／macOS 開發測試使用本機 Fernet fallback。API Key 不以明文寫入設定檔。
- 新增 `SettingsStore`，以原子替換方式保存服務商、模型、Endpoint 與加密 API Key。
- 備份包含 SQLite 資料庫、附件與加密設定；還原前拒絕絕對路徑、`..` 路徑及符號連結，降低 ZIP 路徑穿越風險。
- Windows workflow 增加完整測試與 Portable EXE 啟動 smoke test。

### 第五階段本地實測結果

- `pytest -q`：19 passed。
- `compileall` 與 `git diff --check`：通過。
- API Key 加密／解密、設定檔無明文、資料庫／附件／設定備份還原：通過。
- ZIP 路徑穿越防護：通過。
- 系統管理中心 Qt offscreen smoke test：通過。
- GitHub Actions Windows Runner：成功。Run `44238055149` 在乾淨 `windows-latest` 環境通過 Windows DPAPI、19 個測試、Portable EXE 建置、啟動 smoke test 及 Artifact 上傳。

## 2026-11-18｜第六階段

### 實作內容

- 新增 Windows 原生 `RegisterHotKey` 全域快捷鍵服務，預設組合鍵為 `Ctrl+Shift+Space`。
- 快捷鍵觸發時顯示並聚焦主視窗；主視窗已在前景時再次觸發會隱藏視窗。
- 系統管理中心顯示快捷鍵狀態與使用方式；快捷鍵被占用時會在狀態列顯示錯誤。
- Linux／macOS 開發環境不呼叫 Windows API，安全停用此功能。

### 第六階段本地實測結果

- `pytest -q`：22 passed。
- `compileall` 與 `git diff --check`：通過。
- 快捷鍵格式解析、錯誤輸入拒絕及非 Windows 停用：通過。
- GitHub Actions Windows Runner：成功。Run `44257724670` 在乾淨 `windows-latest` 環境通過 Windows 原生快捷鍵註冊、22 個測試、Portable EXE 建置、啟動 smoke test 及 Artifact 上傳。

## 2026-11-18｜V1.0.0-rc1 正式驗收準備

- 依正式驗收規格建立 `RELEASE_ACCEPTANCE.md`，逐項區分通過、尚未驗證與尚未實作，不建立未經驗證的 RC1 標籤。
- 新增獨立正式驗收測試：資料重開、SQLite integrity／foreign key、跨客戶隔離、附件與郵件關聯、備份內容、損壞／不相容 ZIP、路徑穿越及還原失敗回復。
- 修正備份還原失敗時可能造成資料庫與附件不一致的問題，加入 rollback snapshot 與回復流程。
- 修正附件資料庫交易失敗後可能留下孤立實體檔案的問題。
- 修正主介面第五階段版本標籤及 README 過時快捷鍵說明。

### 正式驗收實測結果

- 本地完整測試：25 passed。
- `compileall` 與 `git diff --check`：通過。
- 最新修正後 Windows Runner：尚待本次提交後重新執行。
- V1.0.0-rc1：尚未達發布條件。客戶記憶、資料匯出、錯誤紀錄、快捷鍵自訂、跨程式選取文字與部分系統管理功能仍未實作或未能在目前環境驗證。
- Windows 重跑紀錄：Run `44264083042` 首次暴露還原目標 SQLite engine 未釋放造成的 Windows `PermissionError`；修正測試先 `dispose()` 後，Run `44264320814` 成功通過 25 個測試、Portable EXE、啟動 smoke test 與 Artifact 上傳。
