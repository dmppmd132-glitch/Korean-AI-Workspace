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

## 第三階段已完成

- 客戶資料庫與客戶中心，保存公司、聯絡人、Email、產業、溝通語氣及備註
- 全域、分類及客戶專屬詞庫
- 詞庫指定繁中、指定韓文、禁止翻譯、強制套用、分類、備註與使用範例
- 客戶專屬詞庫優先於分類詞庫及全域詞庫，且不同客戶資料隔離
- 客戶與詞庫搜尋、修改、刪除及本機保存

## 第四階段已完成

- 手動貼上韓文商務郵件並選取客戶
- 完整郵件翻譯、摘要、語氣、需求與重要事項分析
- 中文回覆意思轉換為正式、自然、親切三種韓文回信草稿
- 郵件狀態與草稿管理，AI 內容不會假裝已寄出
- 附件本機複製保存、SHA-256 去重、單檔 100 MB 上限及郵件關聯管理
- 附件可開啟、解除關聯及刪除實體檔案；附件不會自動解析或上傳給 AI

## 第五階段已完成

- 系統管理中心支援手動建立 ZIP 備份與從備份還原
- 備份包含 SQLite 資料庫、附件及加密設定；還原前會檢查 ZIP 路徑安全性
- Windows 使用 DPAPI 加密 API Key；非 Windows 開發環境使用本機 Fernet fallback，密文不保存明文
- 啟動時可載入已保存的加密 AI 設定，亦可手動重新保存
- Windows GitHub Actions 會執行完整測試、Portable EXE 建置、啟動 smoke test 與 Artifact 上傳

## 第六階段已完成

- Windows 支援原生全域快捷鍵 `Ctrl+Shift+Space`
- 快捷鍵不論目前焦點在哪個程式，都可顯示／聚焦 Korean AI Workspace；再次按下可隱藏
- 快捷鍵被其他程式占用時會顯示明確錯誤，不會假裝已啟用
- Linux／macOS 開發環境會安全停用 Windows 全域快捷鍵，不影響其他功能

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

在翻譯中心輸入服務商、API Key、模型與 Endpoint。可到系統管理中心按「保存目前 AI 設定（加密）」。Windows 使用目前 Windows 使用者的 DPAPI 保護 API Key；備份中的 DPAPI 密文預期只能在可解密的原 Windows 使用者環境使用。

## 測試

```bash
PYTHONPATH=src pytest -q
```

## Windows Portable EXE

GitHub Actions workflow `.github/workflows/windows-build.yml` 會在乾淨的 `windows-latest` Runner 安裝依賴、執行測試、使用 `packaging/KoreanAI.spec` 打包、啟動 EXE smoke test，並上傳 `Korean-AI-Workspace-Windows-Portable` Artifact。此專案不把真實 API Key 或本機資料提交到 Git。

## 範圍聲明

目前尚未實作的功能會明確標示，不會以假按鈕宣稱完成；全域快捷鍵第一版已支援 Windows `Ctrl+Shift+Space`。

## V1.0.0-rc1 驗收狀態

正式驗收報告位於 [RELEASE_ACCEPTANCE.md](RELEASE_ACCEPTANCE.md)。目前最新本地驗收測試為 25 passed，但客戶記憶、資料匯出、錯誤紀錄、快捷鍵自訂、跨程式選取文字及部分 Windows 實機情境尚未完成或驗證，因此尚未建立 `V1.0.0-rc1` 標籤。
