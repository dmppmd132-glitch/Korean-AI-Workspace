# Korean AI Workspace

韓文 AI 翻譯與商務工作站。這是一個以 Python/PySide6 建立的 Windows Portable 桌面應用程式，資料預設保存在 EXE 同層的 `data/` 目錄。

## 第一階段已完成

- PySide6 可調整大小的繁體中文主介面與六個工作區導覽
- SQLite + SQLAlchemy 本機資料庫
- 翻譯原文、語言方向、最佳翻譯及 Provider/Model 紀錄
- OpenAI、Gemini（相容 Endpoint）及其他 OpenAI Chat Completions 相容 API
- AI API 連線測試、逾時與錯誤提示
- 基本韓文→繁中、繁中→韓文及自動辨識翻譯
- GitHub Actions Windows Runner 測試與 PyInstaller Portable EXE 打包流程

## 第二階段已完成

- 最佳、正式、自然、親切四種翻譯結果分頁比較
- 翻譯歷史本機搜尋，可搜尋原文及四種譯文
- 歷史項目雙擊載入原文與四種結果
- 可重用浮動翻譯視窗，支援版本切換、複製、釘選、滑鼠移入暫停倒數及 8 秒自動關閉

## 開發環境

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
$env:PYTHONPATH = "src"
python -m korean_ai_workspace.app
```

Linux/macOS 開發環境可使用 `python3`、`source .venv/bin/activate` 及 `export PYTHONPATH=src`。第一階段的 GUI 與 EXE 必須在 Windows Runner 驗證。

## AI 設定

在翻譯中心輸入服務商、API Key、模型與 Endpoint。第一階段 API Key 僅存在目前執行程序記憶體，尚未保存到磁碟；Windows DPAPI 安全保存會在第五階段加入。

## 測試

```bash
PYTHONPATH=src pytest -q
```

## Windows Portable EXE

GitHub Actions workflow `.github/workflows/windows-build.yml` 會在乾淨的 `windows-latest` Runner 安裝依賴、執行測試、使用 `packaging/KoreanAI.spec` 打包，並上傳 `Korean-AI-Workspace-Windows-Portable` Artifact。此專案不把真實 API Key 或本機資料提交到 Git。

## 範圍聲明

郵件中心、客戶中心、詞庫中心、附件、全域快捷鍵、DPAPI 及備份還原將按後續階段開發；目前介面會明確標示尚未實作的功能，不會以假按鈕宣稱完成。
