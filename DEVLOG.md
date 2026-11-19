
## 2026-11-18｜第六階段延伸：客戶記憶第一輪

### 實作內容

- 新增 `customer_memories` 與 `customer_memory_revisions` SQLite 資料表，透過既有 `Base.metadata.create_all` 採加法式建立，不刪除既有資料表或資料。
- 每筆記憶固定歸屬單一客戶，保存分類、內容、來源郵件 ID、待確認／已確認／已拒絕狀態、建議日期、確認日期與更新日期。
- 新增記憶 repository：新增待確認建議、修改、確認、拒絕、刪除、搜尋及變更歷史。
- 新增 AI 記憶建議 service。AI 只回傳候選建議，不直接寫入資料庫；格式錯誤時不保存任何資料。
- 客戶中心新增記憶面板；使用者可檢視、搜尋、修改、確認、拒絕及刪除目前客戶的記憶。
- 只有狀態為「已確認」且屬於目前客戶的記憶會加入翻譯與郵件使用的客戶 context；其他客戶記憶不會混用。

### 實測結果

- 本地完整測試：29 passed。
- `compileall`：通過。
- `git diff --check`：通過。
- 客戶隔離、待確認不進有效 context、確認後進 context、變更歷史及 AI 格式錯誤不落庫：通過。
- Windows 實機與 Windows Runner：本次客戶記憶延伸提交後尚未重新驗證。


## 2026-11-18｜第六階段延伸：翻譯收藏功能

### 實作內容

新增 `translation_favorites` SQLite 資料表。收藏資料與 `translation_history` 分開管理，但保留可選的歷史 ID 關聯；原文、語言方向、單一翻譯版本、Provider、模型、客戶 ID 與收藏時間都以快照形式保存。資料表加入歷史 ID、語言、版本、客戶及日期索引，同一筆翻譯的同一版本重複收藏會回傳既有記錄，不會建立重複資料。

翻譯中心與浮動翻譯視窗都能針對最佳、正式、自然、親切四種版本獨立收藏。工具列的「翻譯收藏」會開啟管理對話框，提供原文／譯文搜尋、翻譯方向、版本、客戶篩選、日期倒序、完整內容、複製原文、複製譯文與取消收藏。取消收藏只刪除收藏快照，不會刪除翻譯歷史。

備份 manifest 明確標記 `translation_favorites`；收藏實體資料位於 SQLite，因此既有備份／還原流程會一併保存及還原收藏，不需另建不一致的附件式備份資料。

### 實測結果

本地完整測試為 **35 passed**，包含四版本獨立收藏、重複收藏去重、收藏重開、快照不受重新翻譯影響、搜尋與篩選、客戶隔離、空白資料拒絕、舊資料庫加法式 migration、備份還原及既有客戶記憶測試。`compileall` 與 `git diff --check` 均通過。第一次測試發現新增第七工作區破壞既有六工作區 UI 合約，已改為工具列對話框並重新驗證通過。

GitHub Actions Windows Runner Run `44267777323` 成功：在 `phase6-extension` 的乾淨 `windows-latest` 環境通過 35 項測試、SQLite migration／收藏資料保存與還原測試、Portable EXE 建置、5 秒啟動 smoke test 及 Artifact 上傳。Node.js 20 deprecation 僅為 GitHub Actions annotation，未影響 job 結果。


## 2026-11-18｜第六階段延伸：完整本機資料匯出第一輪

### 實作內容

新增 `DataExportService` 與系統管理中心「資料匯出（CSV／JSON）」對話框。使用者可複選客戶、詞庫、翻譯歷史、翻譯收藏、客戶記憶、記憶變更歷史、郵件、附件 metadata 及郵件附件關聯；單一資料類別可輸出 CSV，多類別 CSV 會封裝為 ZIP，JSON 則保留 `schema_version`、軟體版本、匯出時間、原始 ID、完整欄位與關聯資料。

CSV 使用 UTF-8 BOM 與 Python CSV writer，正確處理繁體中文、韓文、逗號、雙引號、換行及 NULL。匯出前會顯示各類別筆數與敏感資料警告，使用者確認後以 QThreadPool 背景工作執行並更新進度。匯出使用單一 SQLAlchemy read session 讀取，不修改原始資料；輸出檔案使用暫存檔後原子替換，失敗時清理未完成檔案。

匯出資料不包含設定檔，因此不會包含 API Key、Bearer Token、OAuth Token、密碼或加密憑證。附件本輪只匯出附件 ID、原始檔名、大小、SHA-256、mime type、保存路徑及郵件關聯，不複製實體附件檔案；UI 與 JSON 都明確標示此限制。

### 實測結果

本地完整測試：**41 passed**。已驗證各資料類別 CSV、CSV ZIP、JSON schema／完整欄位、UTF-8 BOM、繁中／韓文、逗號／引號／換行、客戶與郵件／附件關聯、API Key／Token／密碼排除、空資料庫、空選擇錯誤、原始資料不修改、進度回報、既有客戶記憶與翻譯收藏回歸，以及 Qt offscreen 匯出對話框。

GitHub Actions Windows Runner Run `44268710297` 成功：在 `phase6-extension` 的乾淨 `windows-latest` 環境通過完整測試、CSV／JSON 匯出相關測試、Portable EXE 建置、5 秒啟動 smoke test 與 Artifact 上傳。Windows 中文／空格路徑的實際人工互動選擇與附件實體檔案匯出仍不在本輪支援範圍，分別列為人工驗證與已知限制。


## 2026-11-18｜緊急 Bug 修復：韓文顯示為方框

### 問題診斷

翻譯中心輸入框實際使用 `QPlainTextEdit`，剪貼簿與 Python／Qt 字串均使用 Unicode；測試貼上 `안녕하세요. 감사합니다. 한국어 번역 테스트입니다.`、`대한민국 서울특별시`、`거래처 담당자님께` 及 `가격 및 납기일을 확인 부탁드립니다.` 後，文字內容未損壞，也沒有發現錯誤的 encode/decode 或字元替換。原本 QSS 卻把所有 QWidget 固定為 `Microsoft JhengHei`／`Noto Sans CJK TC`，未依作業系統實際可用字型選擇 Hangul glyph，並可能覆蓋 Qt 的字型 fallback，因此在缺少相容字型時顯示方框。

### 修復內容

新增 `ui/font_support.py`，透過 `QFontDatabase` 實際檢查字型及 Korean writing system，Windows 優先使用 Malgun Gothic，開發環境優先使用 Noto Sans CJK KR／TC，並保留可用 fallback families。`QApplication` 啟動及 `MainWindow` 建立時套用同一套全域 QFont；移除 QSS 的固定 `font-family`，讓翻譯中心、浮動視窗、郵件中心、收藏、歷史及其他頁面共用相同字型設定。

### 實測結果

本地完整測試：**44 passed**。新增測試驗證 Qt glyph 支援、韓文與中韓混合文字、剪貼簿 Unicode 貼上、翻譯中心輸入框字型與主視窗共用字型。Linux 環境實際找到 Noto Sans CJK KR／TC；Windows 字型選擇與 Portable EXE 將由 Windows Runner 驗證。資料匯出及其他既有功能回歸測試均通過。

### Windows Runner 追蹤與最終狀態

第一次 Windows Run `44271576548` 的 2 個失敗來自測試錯誤假設 `QFontDatabase` 必須回傳 CJK family；該 Runner 的 Qt offscreen 環境實際回傳空清單。調整測試後，第二次 Run `44272191770` 進一步確認同一環境的 `QFontMetrics.inFont()` 也無法提供韓文 glyph provider，而不是原文、剪貼簿或翻譯 Unicode 流程損壞。

因此測試改為：在正常具備韓文字型的環境嚴格驗證 glyph coverage；若 Qt offscreen 沒有任何可用 provider，明確以 skip 記錄環境限制，不偽造通過。最終 Windows Run `44273043124` 成功完成 42 passed、2 skipped、Portable EXE 建置、啟動 smoke test 與 Artifact 上傳。Linux 開發環境的 44 passed 已實際驗證 Noto Sans CJK KR／TC；Windows 實機（含實際 Malgun Gothic／fallback 的視覺 glyph 渲染）仍尚未驗證。

## 2026-11-18｜韓文字型深入診斷功能

### 實作內容

- 新增 `FontDiagnosticsDialog`，由系統管理中心開啟；測試區使用真正的 `QPlainTextEdit` 顯示三段韓文，讓使用者直接觀察 glyph，而不是只看布林值。
- 診斷會記錄 OS、Qt、PySide6、是否為 frozen EXE、QApplication QFont、QFontInfo 實際解析 family、Qt family 數量、Malgun Gothic 是否存在／支援韓文、Korean WritingSystem、候選 fallback 逐項檢查與目前字型 glyph coverage。
- 「複製診斷資訊」只複製 runtime 字型資訊；未讀取 API Key、郵件、客戶、翻譯或剪貼簿既有內容。
- PyInstaller spec 已支援選擇性封裝 `resources/fonts`；程式以 `QFontDatabase.addApplicationFont()` 載入實際存在的資產，並回報 `applicationFontFamilies()` 結果。尚未加入 Noto 字型檔，因目前尚未確認實際使用者環境需要及可接受的再散布授權。

### 實測結果

- 本地完整測試：**46 passed**。
- `compileall` 與 `git diff --check`：通過。
- 本機診斷確認 Qt 6.8.1／PySide6 6.8.1、Noto Sans CJK KR／TC 可用，QFontInfo 可解析到 Noto Sans CJK KR；該結果不能取代使用者 Windows 桌面實機驗收。

## 2026-11-19｜翻譯卡住與 Provider 設定修正

- `TranslationWorker` 現在會在成功、例外與 finally 路徑發出訊號；主視窗保存 worker 引用，並以 timeout 保護翻譯請求。
- 翻譯成功保存失敗、HTTP／網路錯誤及逾時都會清除「翻譯中」、重新啟用開始翻譯按鈕並顯示明確錯誤。
- 服務商、模型與 Endpoint 改為選單預設值加可編輯自訂欄位。Gemini 預設使用 Google OpenAI-compatible Endpoint；OpenAI 與自訂 OpenAI-compatible API 分開處理。
- 本地完整測試：**48 passed**。
- Windows Runner Run `44426958872`：完整測試、Portable EXE、啟動 smoke test 與 Artifact upload 均成功。

## 2026-11-19｜AI API read timeout 修正

使用 Gemini 翻譯時若模型在 60 秒內沒有完成回應，原本會回報 `the read operation timed out`；現在預設 API timeout 延長至 180 秒，並將 `TimeoutError`／`URLError` 中的 timeout 分類為明確的「AI API 回應逾時」。背景 worker 的 timeout 收尾仍會解除 UI 的「翻譯中」狀態。新增設定測試後，本地完整測試為 **49 passed**。
