# Korean AI Workspace V1.0.0-rc1 正式驗收報告

日期：2026-11-18  
版本基線：`3c1d0a0`（正式驗收修正與 Windows 鎖定修正）  
驗收結論：**尚未達到 V1.0.0-rc1 發布條件**

本報告依照正式驗收規格執行，沒有把未實作或目前無法驗證的項目標示為通過。報告中的通過項目均使用獨立臨時測試資料；沒有使用或覆蓋使用者資料。

## 1. 測試環境

### 已執行環境

- Manus Sandbox Linux
- Python 3.12
- PySide6 6.8.1
- SQLAlchemy 2.0.36
- SQLite
- `QT_QPA_PLATFORM=offscreen`
- 測試命令：`QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q`
- 編譯命令：`.venv/bin/python -m compileall -q src tests`

### Windows CI 環境

正式驗收修正後的第一次 Run `44264083042` 暴露 Windows 測試在還原目標資料庫仍持有 SQLite 檔案鎖；該次在測試階段失敗，沒有進入 EXE 打包。修正測試先釋放資料庫 engine 後，Run `44264320814` 已在乾淨 `windows-latest` 通過 25 個測試、Windows 原生快捷鍵註冊、Portable EXE 建置、啟動 smoke test 與 Artifact 上傳。

## 2. 實際測試結果

| 驗收項目 | 結果 | 實際方式 |
|---|---|---|
| 完整 Python 測試 | 通過 | 25 passed |
| 編譯檢查 | 通過 | `compileall` |
| Git diff 空白檢查 | 通過 | `git diff --check` |
| 客戶、郵件、翻譯、詞庫資料重開 | 通過 | 臨時 SQLite 建立資料，dispose engine 後重新開啟並比對數量與內容 |
| SQLite 完整性 | 通過 | `PRAGMA integrity_check` 回傳 `ok`，`PRAGMA foreign_key_check` 無結果 |
| 客戶資料隔離 | 通過 | 兩個客戶、專屬詞庫、兩封郵件及翻譯歷史重新讀取驗證 |
| 附件重新載入 | 通過 | 附件保存、關閉資料庫、重新開啟後驗證實體檔案 |
| 相同內容不同檔名去重 | 通過 | `.txt` 與 `.bin` 內容相同，SHA-256 共用同一附件 |
| 多封郵件共用附件 | 通過 | 同一附件關聯兩封郵件並驗證關聯資料 |
| 備份 ZIP 內容 | 通過 | 驗證 `manifest.json`、SQLite、附件均存在 |
| 損壞 ZIP | 通過 | 非 ZIP 檔案被拒絕並回傳 `BackupError` |
| 不相容版本 ZIP | 通過 | manifest version 999 被拒絕 |
| 路徑穿越 ZIP | 通過 | `../outside.txt` 被拒絕 |
| 還原失敗資料保留 | 通過 | 模擬資料庫寫入後失敗，驗證原資料庫與附件回復 |
| API Key 不以明文保存 | 通過 | 設定檔只含加密密文，不含測試 API Key |
| 非 Windows 密鑰 fallback | 通過 | Fernet round-trip，密文不等於明文 |
| Windows DPAPI | 通過 | 最新 Run `44264320814` 在乾淨 Windows Runner 通過 25 個測試 |
| Windows Portable EXE | 通過 | 最新 Run `44264320814` 完成建置、啟動 smoke test 與 Artifact 上傳 |

## 3. Portable EXE 驗收狀態

| 項目 | 狀態 | 說明 |
|---|---|---|
| 無 Python 環境啟動 | 通過（CI 基線） | Windows CI 安裝的是建置用 Python，EXE 啟動不依賴專案虛擬環境；最新 Run `44264320814` 成功 |
| DLL／依賴收集 | 通過（CI 基線） | 最新 Run `44264320814` 完成 PyInstaller 與 smoke test |
| 介面載入 | 通過（CI smoke test） | 最新 Run `44264320814` EXE 啟動後存活 5 秒 |
| 正常關閉 | 尚未完整驗證 | 目前 smoke test 確認啟動後存活，再由 CI 強制停止；尚未做 GUI 正常關閉操作驗證 |
| 重新啟動 | 尚未驗證 | 尚未在 CI 中連續啟動／關閉兩次並驗證資料重開 |
| 不同 Windows 使用者 | 尚未驗證 | 需要不同 Windows 使用者 profile |
| 不同資料夾 | 尚未驗證 | 尚未用中文、空格、長路徑逐一執行 |
| USB／外接 SSD | 尚未驗證 | CI Runner 不代表實體 USB／外接 SSD |
| 高 DPI／不同解析度 | 尚未驗證 | Sandbox 無 Windows 顯示器驗證能力 |

## 4. 六大工作區功能狀態

### 翻譯中心

已驗證：基本韓文／繁中翻譯服務組裝、四種翻譯結果、歷史搜尋、浮動視窗核心元件、AI 錯誤不覆蓋原文。

尚未完成或未驗證：收藏功能、跨程式選取文字讀取、剪貼簿備援、剪貼簿原內容保護、多螢幕邊界處理。

### 郵件中心

已驗證：手動貼上郵件、郵件保存、翻譯／分析資料結構、三種韓文回信草稿、草稿保存、郵件搜尋、附件關聯與去重。

限制：目前不串 Gmail／Outlook，不自動寄信。

### 客戶中心

已驗證：新增、搜尋、修改、刪除、保存及客戶隔離。

尚未完成：客戶記憶功能。`data/customer_memory` 路徑存在，但目前沒有對應資料模型、repository 或 UI 功能，因此不能宣稱客戶記憶已完成。

### 詞庫中心

已驗證：新增、修改、刪除、搜尋、分類詞庫、客戶專屬詞庫、優先權及資料隔離。

### AI 引擎中心

已驗證：OpenAI／Gemini 相容 Provider 設定模型、模型切換、連線測試方法與 API 錯誤處理。

尚未完成：不同任務的模型分配設定。目前翻譯、郵件分析與回信草稿共用目前 Provider 設定。

### 系統管理中心

已驗證：Windows 全域快捷鍵第一版、加密 API Key 保存、手動備份與還原。

尚未完成：快捷鍵自訂、資料匯出、專用錯誤紀錄檢視、浮動視窗設定介面、軟體版本資訊頁。

## 5. API Key 安全檢查

目前實作使用 Windows DPAPI；非 Windows 僅作為開發環境使用本機 Fernet fallback。設定檔不寫入 API Key 明文，密文備份不等於明文 API Key。

已驗證：

- 設定檔不含 API Key 明文。
- API Key 不由本專案 logging 主動寫入。
- API Provider request 使用記憶體中的 API Key，不將 Key 放入 prompt。
- DPAPI 解密失敗時，設定載入會失敗並保留資料庫與其他功能，不會刪除客戶資料。
- 修改設定後會原子替換設定檔。

尚待驗證：

- 實際搬到另一個 Windows 使用者 profile 後，DPAPI 解密失敗畫面與重新輸入流程。
- Windows 事件檢視器／第三方網路攔截工具下的完整敏感資訊洩漏檢查。
- 真實使用者 API Key 不會進入外部 crash reporter；目前專案沒有外部 crash reporter。

## 6. 發現並修正的問題

### P1：還原失敗可能留下部分新資料（已修正）

原本 `restore_backup` 會先覆蓋資料庫，再刪除並重建附件資料夾；中途檔案操作失敗可能造成資料庫與附件不一致。

修正方式：

- 還原前建立獨立 rollback snapshot。
- 失敗時回復資料庫、附件與加密設定。
- 失敗時回傳「原本資料已保留」的錯誤。
- 新增正式測試模擬資料庫寫入後失敗並驗證回復。

### P2：附件資料庫交易失敗可能留下孤立實體檔案（已修正）

附件檔案複製後若 SQLite 關聯交易失敗，原本可能留下未被資料庫引用的實體檔案。

修正方式：交易失敗時刪除本次新複製的實體檔案，並新增資料安全測試覆蓋相關流程。

### P2：版本標示與文件過時（已修正）

主介面版本標籤原本仍為第五階段，README 也仍有過時的快捷鍵未實作文字；已更新為第六階段與目前功能狀態。

## 7. 已知限制與發布阻擋項

依正式驗收規格，下列功能尚未實作，不能建立「已完成所有六大工作區」的 V1.0.0-rc1 標籤：

1. 客戶記憶資料模型、保存、搜尋與 UI。
2. 資料匯出功能。
3. 專用錯誤紀錄檢視功能。
4. 快捷鍵自訂功能。
5. `Ctrl+Shift+T` 與 `Ctrl+Shift+C` 功能。
6. 跨程式選取文字讀取與剪貼簿備援。
7. 收藏功能。
8. 浮動視窗設定、多螢幕位置與螢幕邊界判斷。
9. 不同 Windows 使用者、USB／外接 SSD、中文／空格路徑、高 DPI 的實機驗收。

這些項目不是本次驗收中被忽略的測試，而是目前程式尚未提供或目前環境無法真實驗證的功能，因此標示為未完成／尚未驗證。

## 8. 結論

目前可確認：資料層、郵件與附件、加密設定、備份還原、Windows 全域快捷鍵以及既有 Portable EXE 流程已有實際測試基礎；最新本地驗收測試為 25 passed。

目前不可確認：所有正式規格要求的功能均已完成，也不可確認最新修正後的 Windows EXE 已重新驗收。因此目前狀態應為：

> **V1.0.0-rc1：Not Ready／尚未達發布條件**

完成最新提交後的 Windows Runner 重跑，以及補足上述發布阻擋功能或明確縮小 V1.0 規格，才可重新評估建立 `Korean AI Workspace V1.0.0-rc1`。
