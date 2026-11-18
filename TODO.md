# 第一階段 TODO

- [x] 建立 Python 模組化專案與依賴清單。
- [x] 建立 PySide6 繁體中文主介面與六個工作區導覽。
- [x] 建立 SQLite + SQLAlchemy 資料庫與翻譯歷史保存。
- [x] 建立 OpenAI、Gemini 相容 Endpoint 及其他 OpenAI 相容 API 的 Provider 介面。
- [x] 完成基本韓文→台灣繁體中文、台灣繁體中文→自然韓文及自動辨識方向。
- [x] AI API 錯誤時保留原文且顯示錯誤。
- [x] 建立 pytest 測試。
- [x] 建立 Windows GitHub Actions Runner 測試及 PyInstaller Portable EXE 設定。
- [x] 在 GitHub Actions 的乾淨 Windows Runner 完成實際 workflow 驗證；測試、Portable EXE 建置、smoke test 及 Artifact 上傳均成功。
- [x] 進入第二階段前修正 Windows Runner 發現的問題；本次 workflow 未發現阻斷性問題。

## 第二階段

- [x] 翻譯完成後顯示並保存最佳、正式、自然、親切四種結果，可在主畫面切換比較。
- [x] 翻譯歷史可在本機 SQLite 搜尋原文及四種翻譯結果，雙擊可載入。
- [x] 浮動翻譯視窗可重用、顯示原文與四種結果、複製目前版本、釘選，預設 8 秒自動關閉，滑鼠移入時暫停倒數。
- [x] 第二階段單元測試與主介面測試通過；共 7 個測試通過。
- [ ] 乾淨 Windows Runner 完成第二階段測試、打包與 smoke test。
