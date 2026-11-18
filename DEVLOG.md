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
