# 第一階段計畫

## 實作決策

採用 Python 3.12、PySide6、SQLAlchemy、SQLite 與 OpenAI Chat Completions 相容 HTTP API。UI 與服務層分離，翻譯呼叫放入 QThreadPool，避免網路請求阻塞主視窗。SQLite 檔案位於 EXE 同層 `data/database/workspace.db`。

## 交付邊界

本階段完成可執行主介面、資料庫初始化與歷史保存、AI Provider 驗證及基本雙向翻譯。尚未進入的功能會明確標示，不以靜態畫面冒充完成。

## 驗證方式

在 Linux 執行資料庫與服務層測試；提交後由乾淨 Windows GitHub Actions Runner 安裝依賴、重新執行測試及 PyInstaller 打包，再檢查 EXE 存在。
