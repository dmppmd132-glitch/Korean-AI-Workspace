
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
