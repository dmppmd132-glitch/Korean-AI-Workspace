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
