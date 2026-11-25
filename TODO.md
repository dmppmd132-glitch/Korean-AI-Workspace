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
- [x] 乾淨 Windows Runner 完成第二階段測試、打包與 smoke test；7 個測試及 Portable EXE Artifact 均成功。

## 第三階段

- [x] 客戶資料庫可新增、搜尋、修改、刪除並保存公司、韓文公司名、聯絡人、Email、職稱、產業、溝通語氣、公司資料與備註。
- [x] 詞庫支援全域、分類及客戶專屬範圍，包含指定翻譯、禁止翻譯、強制套用、分類、備註與使用範例。
- [x] 翻譯只取得目前選取客戶可用的詞條，不得混入其他客戶資料；客戶專屬詞條優先於分類與全域詞庫。
- [x] 客戶與詞庫資料可實際保存並在重新開啟後讀回；刪除客戶時保留詞條並解除關聯。
- [x] 第三階段資料層、提示組裝與 Qt 主介面測試通過；共 10 個測試通過。
- [x] 乾淨 Windows Runner 完成第三階段測試、打包與 smoke test；10 個測試及 Portable EXE Artifact 均成功。

## 第四階段

- [x] 商務郵件可選取客戶、手動貼上原文並保存主旨、原文、客戶與建立時間。
- [x] AI 可產生完整郵件翻譯、摘要、語氣、對方需求與重要事項分析。
- [x] 使用者可輸入中文回覆意思，AI 可產生正式、自然、親切三種韓文回信草稿；草稿不宣稱已寄出。
- [x] 郵件狀態支援待處理、已翻譯、分析完成、回信撰寫中、草稿完成、已完成。
- [x] 附件支援單檔 100 MB、SHA-256 去重、本機複製保存、郵件關聯、開啟、解除關聯及分離刪除實體檔案。
- [x] 第四階段資料層、AI 服務與 Qt 主介面測試通過；共 14 個測試通過，包含郵件刪除時附件關聯的外鍵級聯驗證。
- [x] 乾淨 Windows Runner 完成第四階段測試、打包與 smoke test；Run `44235588030` 成功，14 個測試、Portable EXE 與 Artifact 均成功。

## 第五階段

- [x] 系統管理中心支援手動建立 ZIP 備份。
- [x] 備份包含 SQLite 資料庫、附件與加密設定，並可還原至 Portable 資料路徑。
- [x] ZIP 還原拒絕絕對路徑、路徑穿越與符號連結。
- [x] Windows API Key 使用 DPAPI 加密；設定檔不保存明文 API Key。
- [x] 非 Windows 開發測試使用本機 Fernet fallback，且不宣稱為 Windows DPAPI。
- [x] 19 個本地測試、編譯檢查及系統管理中心 Qt smoke test 通過。
- [x] 乾淨 Windows Runner 驗證 DPAPI、完整測試、Portable EXE 啟動與 Artifact 上傳；Run `44238055149` 成功，19 個測試、Portable EXE 與 Artifact 均成功。

## 第六階段

- [x] Windows 原生全域快捷鍵 `Ctrl+Shift+Space` 可註冊。
- [x] 快捷鍵可顯示／聚焦主視窗，再次觸發可隱藏主視窗。
- [x] 快捷鍵被占用或平台不支援時不假裝啟用，並提供狀態提示。
- [x] 快捷鍵解析、錯誤輸入、Linux fallback 測試通過；目前本地共 22 個測試通過。
- [x] 乾淨 Windows Runner 完成第六階段快捷鍵註冊、Portable EXE 與完整測試驗證；Run `44257724670` 成功，22 個測試、Portable EXE 與 Artifact 均成功。

## V1.0.0-rc1 正式驗收

- [x] 建立正式驗收報告，區分通過、尚未驗證與尚未實作項目。
- [x] 完成獨立資料重開、SQLite integrity／foreign key、附件關聯與跨客戶隔離測試。
- [x] 完成損壞／不相容 ZIP、路徑穿越與還原失敗回復測試。
- [x] 修正備份還原部分成功造成資料不一致的風險。
- [x] 修正附件交易失敗後可能留下孤立檔案的風險。
- [x] 最新驗收修改在乾淨 Windows Runner 重新通過完整測試與 Portable EXE；Run `44264320814` 成功，25 個測試、DPAPI、Portable EXE、啟動 smoke test 與 Artifact 均成功。
- [x] 客戶記憶第一輪：SQLite 保存、客戶隔離、待確認／確認／拒絕、來源郵件欄位、變更歷史及有效 context 隔離；AI 建議尚未直接寫入正式記憶。
- [x] 翻譯收藏：四版本獨立快照、搜尋／方向／版本／客戶篩選、複製、完整內容、取消收藏、歷史獨立保存、migration 與備份還原測試。
- [x] 翻譯收藏在乾淨 Windows Runner 驗證：Run `44267777323` 通過 35 個測試、Portable EXE、啟動 smoke test 與 Artifact 上傳。
- [x] 本機資料匯出第一輪：選擇類別輸出 UTF-8 BOM CSV／ZIP 或完整 JSON，保留 ID、日期、客戶／郵件／附件關聯與記憶歷史，排除 API Key 等秘密；附件目前只匯出 metadata 清單。
- [x] 資料匯出 Windows Runner 驗證：Run `44268710297` 成功完成完整測試、Portable EXE、啟動 smoke test 與 Artifact 上傳。
- [x] 緊急韓文顯示修復第一輪：移除固定中文字型 QSS，新增依 Qt writing system 實際解析 Hangul 字型與全域 fallback，並通過 44 個本地測試。
- [x] Windows Runner Run `44273043124` 完成完整 pytest、Portable EXE、啟動 smoke test 與 Artifact 上傳；pytest 為 42 passed、2 skipped。兩項 glyph 測試因 `QT_QPA_PLATFORM=offscreen` 沒有可供 Qt 渲染的韓文字型 provider 而明確 skip，未宣稱 Windows 實機 glyph 已驗證。
- [x] 新增系統管理中心「韓文字型診斷」：顯示 QApplication QFont、QFontInfo、Qt/PySide6、Malgun Gothic、Korean WritingSystem、fallback 檢查及 QPlainTextEdit 實際測試區；可複製不含敏感資料的診斷報告。
- [x] PyInstaller spec 支援將已明確放入 `resources/fonts` 的合法字型資產封裝；目前未加入未確認授權的 Noto 字型檔。
- [ ] 錯誤紀錄、快捷鍵自訂、跨程式選取文字與剪貼簿備援，以及 Windows 中文／空格路徑人工互動驗收。
- [ ] 不同 Windows 使用者、USB／外接 SSD、中文／空格路徑、高 DPI 與多螢幕實機驗收。
- [ ] 使用者 Windows 實機開啟字型診斷，回傳報告中的 QFontInfo resolved family、Malgun Gothic found/support、Korean glyph check 與測試區截圖；依結果決定是否加入已確認授權的 bundled font。
- [x] 翻譯 worker 增加成功／錯誤／逾時收尾，避免結果或網路例外造成 UI 永久停在「翻譯中」。
- [x] 服務商切換時以選單帶入模型與 Endpoint 預設值，模型與 Endpoint 仍可手動輸入自訂內容；新增 Provider／worker 回歸測試。
- [x] AI API 預設 response timeout 延長至 180 秒，區分 read timeout 與一般網路錯誤，並保證翻譯 UI 會解除「翻譯中」。
- [x] 翻譯中心新增快速翻譯模式，只要求 AI 回傳最佳翻譯；完整模式仍保留四種版本。
- [x] AI 設定固定使用 Gemini、`gemini-4-hydrogen` 與 Google OpenAI-compatible Endpoint。
- [x] 詞庫新增「公司名稱」分類，並建立全域固定詞條 `달마 → 達磨`。
- [x] 新增公司專用詞庫預設詞條：公司名稱、人名、Tmp／LOT／Alarm、系統操作、品質報告及後續流程術語。
- [x] 翻譯中心新增「品質異常報告固定格式」，保留發生原因、改善對策、技術原因、資料驗證與後續流程結構。
- [x] 依 46L LASER 與 46M VRS 案例補充 Shutdown、Gathering、備份、資料錯誤、管理通報及完整 Alarm 原文固定詞條。
- [x] 品質報告模式要求正式敬體、冒號條列標題，並保留「預計／已完成」原文狀態，不自行改寫。
- [x] 整合 Sorter／Genesem 設備排查語料：Emergency、Vacuum、DC24V、Regulator、Handler UI、Dummy／正常產品、TeamViewer 遠端支援。
- [x] 整合三星客戶品質抱怨語料：不良率、管理編號、檢驗條件最佳化、Overkill、出貨限制、密切管理與緊急追加確認。
- [ ] 所有發布阻擋項完成後，才建立 `Korean AI Workspace V1.0.0-rc1`。
