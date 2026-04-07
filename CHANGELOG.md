# Changelog

繁體中文｜[简体中文](docs/CHANGELOG.zh-CN.md)｜[English](docs/CHANGELOG.en.md)

本檔案用來記錄 OCRTranslator 的重要變更。

## [Unreleased]

## [1.0.5] - 2026-04-07

### Added
- 新增 Windows 專用的截圖瞬時隱身與 compositor flush 輔助模組，並補上 frozen snapshot / concealment / compositor sync 的回歸測試與診斷日誌

### Changed
- 螢幕框選流程改為兩階段：先暫時隱藏應用自有視窗並凍結桌面快照，再顯示框選遮罩；完成框選後直接從 frozen snapshot 裁切，不再回頭對 live desktop 重抓
- 框選遮罩現在會以 frozen desktop background 作為底圖，截圖提示則延後到裁切完成後再顯示，降低截圖前自家 UI 干擾畫面的機率

### Fixed
- 修正 Win11 下主視窗、結果浮窗或 hover 觸發的新 UI 容易在截圖過渡期間混入畫面的問題
- 修正高 DPI / 多螢幕下框選區域與實際截圖不一致的問題，同時維持原始 PNG bytes 直送，不做額外圖片預處理

## [1.0.4] - 2026-04-06

### Added
- 新增預設啟用的「流式回應」設定，並在進階設定提供顯式開關；`OpenAI Compatible` / `Gemini Compatible` 的文字與圖片請求現在都支援流式增量更新
- 新增部分結果狀態標記與相關提示文案；串流中斷時會保留可見內容並標示 `串流中 / 已取消 / 請求失敗`

### Changed
- `Test API` 現在會跟隨目前的流式回應設定，第三方 Compatible 後端在流式不相容時會顯示狀態提示並嘗試自動回退為非流式
- 浮窗幾何策略調整為更穩定的兩段式行為：單次串流請求期間鎖定寬度、未 Pin 浮窗會沿用使用者執行期間手動調整過的寬度，且可跨重啟保留
- 部分結果 UI 更新改為 16ms latest-only frame coalescing，並縮減可見增量更新時不必要的 refresh / topmost / geometry / text work

### Fixed
- 修正 SSE 串流在 UTF-8 / CJK 內容下可能出現亂碼的問題
- 修正取消 / 失敗 / pinned restore 等中斷情境下的部分結果浮窗狀態，避免覆寫既有結果並讓複製與標題文案保持一致
- 修正未儲存 `overlay_width` 表單改動時，已保存的 `overlay_unpinned_width` 可能被提前寫盤清除的邊界問題

## [1.0.3] - 2026-04-06

### Added
- 新增 `--capture` 啟動兜底：若因設定校驗或執行期狀態無法直接開始截圖，會自動回到主視窗並顯示明確狀態提示
- 新增雙設定檔路徑說明與相關測試，補充便攜設定檔與使用者層級 fallback 設定檔的解析規則

### Changed
- 啟動鏈路進一步優化：`--capture` 啟動不再先顯示主視窗、最小化到系統匣前會先補齊 tray 初始化，且主視窗隱藏後會繼續輕量 prewarm、暫停較重的 UI 實例預熱
- 設定檔解析現在優先沿用專案根目錄 / exe 同層的便攜 `config.json`；若該位置沒有設定檔且目前目錄不可寫，則自動回退到使用者設定目錄

### Fixed
- 將 Qt 主執行緒未處理事件異常的關閉路徑統一到完整清理鏈路，補上 watchdog、熱鍵 / 托盤 / overlay / 單實例 IPC 清理，降低發生錯誤後只能強制結束的風險
- 修正更新檢查 worker 若直接拋例外時可能殘留 busy 狀態的問題，避免 UI 長時間停在 checking 狀態
- 清理舊的同步選取文字與未使用截圖死碼，降低維護噪音與啟動鏈路理解成本

## [1.0.2] - 2026-04-05

### Fixed
- 啟動後延遲執行的自動版本檢查現在只會讀取已儲存的 `check_updates_on_startup` 設定，不再受尚未儲存的 checkbox 即時狀態影響

### Changed
- `v1.0.2` 的發佈 tag annotation 改為以無 BOM 文案建立，避免 GitHub Release 正文繼承隱藏字元

## [1.0.1] - 2026-04-05

### Added
- 新增可選 GitHub Releases 更新檢查；進階設定支援啟動後背景檢查與手動立即檢查，發現新版本時可直接點開 Releases 連結
- 新增 API Keys 隱藏態的顯式引導；當欄位維持遮罩時，點擊編輯區會以按鈕與說明文提示先按「顯示 Key」，不會自動揭露敏感內容

### Changed
- 重新整理 API Keys 隱藏態的 Material 互動細節：隱藏表面維持穩定樣式，不再讓輸入框本體或外框跟著脈衝，提示只聚焦在按鈕與說明文
- 進階設定區塊的資訊順序調整為先顯示浮窗 / Pin 行為說明，再顯示版本檢查區塊，讓閱讀節奏更自然
- 更新檢查提示改為可點擊的 GitHub Releases 連結，同時保持啟動後無新版本 / 失敗時的低干擾策略

### Fixed
- 修正 API Keys 隱藏態 `eventFilter()` 在主視窗初始化早期可能先於屬性建立而觸發 `AttributeError` 的問題，避免啟動期連環 crash log
- 修正主執行緒 crash handling 在巢狀或短時間重複異常下可能連續寫出多份 crash log 的問題，加入重入與重複回報抑制
- 修正 API Keys 隱藏態在淺色 / 深色模式下的引導脈衝不同步、焦點殘留與高亮殘影問題

## [1.0.0] - 2026-04-05

### Added
- 新增 `startup_timing` 埋點與 `OCRTRANSLATOR_STARTUP_TIMING_VERBOSE=1` 詳細模式，方便分析冷啟動與首屏後預熱耗時
- 新增 IME-aware 多行輸入控件，修正手動輸入與設定頁多行編輯器在中文輸入法預編輯期間的 placeholder 重疊問題
- 新增應用內短時請求提示氣泡與可設定顯示秒數；進階設定現在可把氣泡時長設為 `0` 直接停用

### Changed
- 啟動鏈路改為更輕量的 bootstrap：延後 UI 建立、統一 lazy service 初始化、補上 idle prewarm，並保留單實例 IPC 與快速第二次啟動轉發的穩定性
- 全域快捷鍵衝突判定改為與低階 listener 共用相同的虛擬鍵語意，並新增未知主鍵 / 純修飾鍵防呆；快捷鍵錄製完成後會即時套用到執行期，設定頁也新增「捨棄變更」操作
- 前台請求提示改為優先使用應用內 toast，背景或最小化場景才回退系統匣通知，同時加入重複訊息節流
- 主視窗、側邊行動按鈕、直接輸入對話框與最新截圖 / social preview 一併更新，整體視覺與互動細節更一致
- Windows 打包持續採用較輕量的冷啟動配置，包含關閉 PyInstaller `UPX` 並同步維護版本化資產與 `SHA256SUMS.txt` 說明

### Fixed
- 已固定的翻譯浮窗在截圖完成後，現在會立即恢復舊內容與原位置，不再等到請求結果返回才重新顯示
- 修正啟動優化過程引入的回歸，包括 tray 屬性初始化、`QTimer` 遺漏匯入，以及主視窗首次顯示後不能立即最小化到系統匣的問題
- 修正請求提示氣泡在部分情況下卡在螢幕上的問題，並讓成功 / 失敗 / 取消路徑都能更一致地收回短時提示
- 修正手動輸入、選字與截圖翻譯流程中的多個邊界狀態，使取消、失敗與已 pin 浮窗還原行為更一致


## [0.9.9] - 2026-04-05

### Added
- 新增三語 `SUPPORT` 文件，整理一般問題、bug 回報、功能建議與安全問題的建議聯繫路徑，並反映目前 Discussions 已關閉的維護方式
- 新增 GitHub social preview 圖片資產 `docs/images/social-preview.png` 與生成腳本 `tools/generate_social_preview.py`
- FAQ 補上請求回覆速度說明，明確記錄 AI / LLM 模型、上游負載與限流會影響延遲，並補充 Google 官方 `gemini-3.1-flash-lite-preview` 常見的 5～10 秒、偶發 30～40 秒與 `429` / `503` 情況

### Changed
- README / docs README 的靜態 Release badge 更新為 `v0.9.9`，打包文檔中的示例 ZIP 檔名也同步更新
- Issue contact links 現在補上 Support 入口，README 與 docs index 也同步收錄 `SUPPORT.md`
- social preview 改為使用更簡潔的品牌 + 主視窗截圖版式，去除膠囊式功能標籤並統一左側資訊色系

### Fixed
- 修正 `release-build.yml` 在產生 fallback release notes 時的 YAML / PowerShell 結構問題，避免 workflow 因語法錯誤失效
- 修正私有倉庫下 README 的 Release / License badge 容易出現 `repo not found` 或 `no releases` 的問題，改為私有倉庫也可穩定顯示的靜態 badge
- 放寬 Dependabot 預設 label 依賴，避免因倉庫尚未建立 `dependencies`、`python`、`ci` 等 labels 而導致更新任務報錯

## [0.9.8] - 2026-04-05

### Added
- 新增專案治理與協作基礎文件：`CODE_OF_CONDUCT.md`、`.github/CODEOWNERS`、`.github/dependabot.yml`、`.editorconfig`、`.gitattributes`
- 新增三語 FAQ：`docs/FAQ.md`、`docs/FAQ.zh-CN.md`、`docs/FAQ.en.md`，補上平台支援、API Key、自架服務、離線 OCR、簽名狀態與安全回報等常見問題
- 新增動態預覽 GIF 資產 `docs/images/screenshots/ocrtranslator-preview.gif`，並接入 README 預覽區塊

### Changed
- README / SECURITY / CONTRIBUTING / docs index / packaging 文檔補上公開倉庫維護所需的信任資訊，包括私下安全聯絡 email、未簽名發布包狀態、簽名計畫與 FAQ / Code of Conduct 入口
- CI workflow 新增 `workflow_dispatch`、concurrency、timeout 與 pip cache；release workflow 也補上 concurrency、timeout、pip cache 與 annotated tag release note 轉發
- GitHub Release 自動發布現在會優先使用 annotated tag 內文作為 Release 正文，不再只依賴 GitHub Actions 自動生成 changelog

### Fixed
- 修正 `Save Settings` 在保存成功後仍可能因焦點回退與滾動區自動保證可見而跳到「目標語言」欄位的問題；保存後會恢復原捲動位置並清掉 Save 按鈕焦點
- 修正設定頁 API Keys、圖片提示詞與文字提示詞多行輸入框在深色模式下的雙層描邊感，改為更接近 Material 的 single-surface 焦點表面
- 修正淺色 / 深色模式下單行與多行輸入框文字選取高亮過淡的問題，現在統一採用更清楚的選取配色
- 補上 release workflow、theme token、style sheet、settings save scroll restore 與 validation scope 的回歸測試

## [0.9.7] - 2026-04-05

### Changed
- 設定表單中的 API Keys、圖片提示詞與文字提示詞多行輸入框改為共用單一焦點表面（single-surface）設計，減少深色模式下雙層描邊與厚重內框感
- 淺色 / 深色主題下的單行與多行輸入框，現在統一使用更清楚的文字選取高亮配色，提高選取狀態辨識度

### Fixed
- 修正只想先儲存 API Profile / Key 設定時，`Save Settings` 會因 `target_language` 空白而自動把捲動位置拉到目標語言欄位的問題；真正送出圖片 / 文字請求時仍會保留目標語言驗證
- 修正深色模式下 API Keys 與 Prompt 多行輸入區的焦點框層次不協調問題，讓 focus / invalid 狀態回到更接近 Material 的單層輪廓表達
- 修正淺色與深色模式下輸入框文字選取高亮過淡、難以判斷是否已選中文字的問題
- 補上設定儲存驗證、theme token 與 style sheet 的回歸測試

## [0.9.6] - 2026-04-05

### Added
- 新增 `LICENSE`（GPLv3），並補上 README / 貢獻指南中的授權說明，明確定義程式碼與後續貢獻的授權方式
- 新增 Pin 專用持久化幾何欄位，讓固定中的翻譯浮窗位置與尺寸可跨重啟保留

### Changed
- 預設結果浮窗字級從 `12` 調整為 `16`，`config.example.json` 與設定模型的預設值同步更新
- 打包 / 簽名基礎結構移至 `packaging/`，由 `packaging/windows/OCRTranslator.spec` 與 `packaging/signpath/` 集中管理
- GitHub Actions workflow 改為使用 Node 24 相容 action 版本，並以 SignPath gate step 避免 workflow 在 `if:` 直接引用 `secrets.*` 而失效
- 主視窗關於區塊現在會顯示 `License: GPLv3`，打包輸出的 ZIP 也會一併附上 `LICENSE`
- 執行期提示文案同步更新：未 Pin 浮窗每次都會從儲存的預設尺寸重新自動擴展，Pin 浮窗則自動記住目前幾何

### Fixed
- 修正英文 `Unsaved Changes` 對話框按鈕文案溢出、說明文截斷與中英文對齊不平衡問題，讓警告 icon、文案區與按鈕區更穩定
- 修正未 Pin 浮窗在自動擴展或手動 resize 後覆蓋 `overlay_width` / `overlay_height` 的問題；未 Pin 狀態現在每次新請求都會從儲存的預設尺寸重新起算
- 修正浮窗 runtime resize 會污染設定表單、觸發未保存提示的問題；未 Pin 的臨時幾何不再被當成需要保存的預設值
- 修正 Pin 浮窗在 runtime 幾何尚未載入時無法可靠沿用持久化尺寸的問題
- 補上 Pin 幾何持久化、未 Pin 尺寸回退、overlay dialog 版面與 release workflow 的回歸測試

## [0.9.5] - 2026-04-05

### Added
- 新增統一的應用圖示資源目錄 `app/assets/icons/`，收斂原始 icon、多尺寸 PNG 與 Windows `.ico`，讓執行期與打包流程共用同一套圖示資產
- 新增 `docs/images/screenshots/` 與 README 介面預覽區塊，補上主視窗與翻譯浮窗的淺色 / 深色效果圖展示
- 新增 GitHub Actions `release-build.yml`，支援手動觸發或推送 `v*` tag 自動打包，並只發布版本化 ZIP（GitHub 自帶 source code 壓縮檔）
- 新增 `.signpath/` 預留結構與 SignPath artifact configuration，為後續 GitHub Trusted Build / 自動簽名流程預先鋪路

### Changed
- 打包流程改為正式採用 `OCRTranslator.spec` + `build_exe.bat` 分工，將 PyInstaller datas / excludes / icon 設定收斂到 `.spec` 管理
- `build_exe.bat` 現在會自動清理 `.venv` 中殘留的 `~ip` 類 pip metadata、支援 `BUILD_NO_PAUSE` / `BUILD_SKIP_PIP_INSTALL`，並以更適合自動化的方式驅動打包
- 主視窗、應用層級 window icon、系統匣與打包輸出的 exe icon 現在統一使用外部圖示資源；凍結執行期也會透過 `resource_path()` 正確讀取 `_MEIPASS` 內資源
- 打包文檔補上 GitHub Actions / SignPath 接入說明，並同步更新版本化 ZIP 範例到 `v0.9.5`

### Fixed
- 修正 `build_exe.bat` 以 `for /f` 讀取 `APP_VERSION` 時的引號解析問題，避免腳本在讀版本號階段提前失敗
- 修正打包期 `Ignoring invalid distribution ~ip` 類 warning，降低虛擬環境殘留 metadata 對本地與 CI 打包流程的干擾
- 補上應用圖示資產與 Release workflow 配置的回歸測試

## [0.9.4] - 2026-04-05

### Added
- 新增退出 watchdog、非阻塞錯誤對話框 fallback 與 crash log 保險，讓關閉流程與執行期錯誤多一層最後防線
- 新增系統匣右鍵選單的淺色 / 深色主題樣式，避免菜單背景與文字對比錯置

### Changed
- 螢幕框選流程改為在背景執行截圖，但仍保留原始 PNG bytes 直送圖片請求，兼顧回應速度與主視窗流暢度
- Pin 狀態下的結果浮窗現在會在截圖、選字與手動輸入流程中保留原本的位置與尺寸；截圖期間僅暫時隱藏，完成後直接以既有幾何狀態恢復
- Pin 按鈕改為更接近 Material 風格的 pushpin icon 與更低存在感的 toggle state，主視窗表面陰影也同步收斂到更輕的層次

### Fixed
- 降低全域快捷鍵 listener、錄製 listener 與退出清理流程造成程式卡住、`X` / 托盤退出失效的風險
- 強化 `handle_error()` 的遞迴保護、錯誤提示回退與 crash log 記錄，降低錯誤處理本身再次崩潰的風險
- 修正淺色模式下系統匣右鍵選單背景過深、文字難以辨識的問題
- 修正極端情況下空的 `api_profiles` / `prompt_presets` 設定可能導致執行期索引錯誤的問題
- 補上背景截圖、Pin 幾何保留、系統匣主題、退出 watchdog 與設定自癒相關回歸測試

## [0.9.3] - 2026-04-04

### Added
- 新增翻譯浮窗自動擴展的頂部 / 底部安全邊距設定，並納入「介面與進階」區塊，可依個人桌面與 Taskbar 習慣微調
- 新增共用 `message_boxes.py`，統一訊息框的按鈕語義、危險操作確認、Escape 行為與可選 Escape Hatch（`prefer_native` / `preserve_initial_focus`）

### Changed
- 翻譯浮窗透明度改為只影響表面背景，不再讓翻譯文字跟著變淡；透明度 chip 可直接輸入，`+ / -` 步進改為 5，topbar hover 會暫時回到 100% 不透明
- 翻譯浮窗 Pin 按鈕改為更直覺的圖釘 icon，並保留 tooltip 與可存取名稱
- 自動擴展高度上限改為可更貼近 Taskbar，但仍永遠保留可調安全間距，不會自動直接貼住 Taskbar
- 刪除 Profile / Prompt Preset 的確認框改為明確動詞按鈕（取消 / 刪除…），降低 `Yes / No` 語義不清的風險
- 進階設定欄位順序調整：將浮窗邊距移到最下方，並補齊浮窗自動擴展安全邊距的命名

### Fixed
- 修正深色模式下編輯輸入框、數字欄位時，選中文字可能變成黑色而難以辨識的問題
- 修正翻譯浮窗與確認對話框初始焦點過亮、偶發白框，以及取消按鈕關閉後延遲清理焦點造成的錯誤 log
- 補上浮窗透明度、對話框 helper、可調安全邊距與深色選取前景的回歸測試

## [0.9.2] - 2026-04-04

### Added
- 新增頁首的三態主題快速切換（跟隨系統 / 淺色 / 深色），點擊後會立即套用並自動儲存
- 新增頁首工作摘要中的快捷鍵總覽，會同時顯示截圖、選字與輸入框三種快捷鍵

### Changed
- 將原本藏在進階設定中的主題下拉選單改為頁首分段切換，並重整頁首資訊架構
- 重新整理設定頁與側邊欄排版：微調品牌區、導覽區、開始使用區、使用提示與作者資訊的文字脊線、間距與層級
- 微調頁首標題、說明與摘要文字的節奏，將目前設定檔 / 方案 / 語言 / 模式 / 快捷鍵改為更容易掃讀的兩行 metadata
- 針對英文介面額外壓縮 sidebar 文案、調整欄寬策略並收斂 Author / Repo metadata，降低捲動與換行壓力
- 打包文檔中的版本化壓縮包範例同步更新到 `v0.9.2`

### Fixed
- 修正深色模式下頁首快捷鍵摘要對比不足、閱讀感偏弱的問題
- 修正頁首快捷鍵資訊與下方內容區之間留白過大，讓分隔線與內容區過渡更緊湊
- 修正英文側邊欄因文案與 metadata 過長導致的擁擠與易出現內部捲動的問題

## [0.9.1] - 2026-04-04

### Added
- 新增圖片請求鏈路耗時日誌，會記錄 `capture / request / total / png`，方便定位本地截圖、上傳或模型回應哪一段偏慢
- 新增 Windows 可執行檔版本資源產生腳本，打包後的 exe 現在會帶有 Product / File Version / Company 等中繼資料
- 新增版本化發佈壓縮包輸出，`build_exe.bat` 會自動建立 `OCRTranslator-v<version>-windows-x64.zip`
- 新增可選代碼簽名打包流程，支援 PFX 憑證、憑證存放區 Thumbprint / Subject Name 與簽名驗證

### Changed
- 螢幕框選現在會在完成截圖後直接把原始 PNG bytes 送往圖片請求鏈路，不再先做縮圖或額外圖像預處理
- 截圖預覽改為在圖片請求啟動後非阻塞更新，讓翻譯請求更早起跑
- 啟動流程改為下一拍主動喚醒主視窗；單實例轉發協議增加換行分隔與 ACK，降低啟動後只剩托盤或主視窗未被帶到前景的機率
- 翻譯浮窗顯示時新增 Windows 原生 topmost 兜底，提升結果浮窗被其他一般視窗蓋住的機率控制
- 打包文檔同步補齊版本資源、簽名參數、時間戳與建議發佈附件格式

### Fixed
- 修正全域快捷鍵對修飾鍵釋放事件的抑制不平衡問題，降低 `Shift / Ctrl / Win` 看起來被卡住的風險
- 新增快捷鍵狀態重同步保險：若釋放事件遺失，後續鍵盤事件會依實際物理按鍵狀態清理內部 pressed state
- 補上單實例 ACK、浮窗 topmost、圖片直送 PNG、快捷鍵卡鍵防護等回歸測試

## [0.9.0] - 2026-04-04

### Added
- 定義應用程式版本號 `v0.9.0`，並顯示於主視窗標題與側邊欄底部
- 新增主介面與托盤中的截圖 / 輸入框快捷入口
- 保留「選取文字」功能，但改回以全域快捷鍵作為主要入口
- 新增 `app/hotkey_utils.py`，統一快捷鍵切分、修飾鍵判斷與正規化規則
- 新增 `app/crash_handling.py`，把 crash hook 安裝邏輯抽成共用入口
- 新增 `requirements-dev.txt` 與多語系文檔版本
- 新增 `淺色 / 深色 / 跟隨系統` 三態主題設定與 `theme_mode` 設定欄位
- 新增 `SelectedTextCaptureSession`，以事件循環驅動非阻塞的選取文字擷取流程，並支援擷取階段取消

### Changed
- 優化設定介面：加入網格佈局 50:50 欄寬等比鎖定，解決多語系文字長度不一造成的排版跑版問題
- 優化側邊欄介面：放寬寬度限制並調整高度策略，解決英文介面下長單字與多行文字被裁切或擠壓的問題
- 優化側邊欄排版：微調元件間距、縮小次要資訊字體大小（11px），並加入底部留白，提供更精緻舒適的視覺與呼吸空間
- 引入零寬度空白字元（`&#8203;`）處理倉庫連結的自然換行，提升多語系排版的靈活性
- 設定表單校驗改為依操作場景拆分，避免 Fetch Models / Test API / 文字請求被無關欄位阻塞
- API Test 的 stale result 判斷現在會納入模型名稱
- 內建提示詞方案改為不可刪除，避免重啟後被自動補回造成語義不一致
- 選取文字流程改為非阻塞擷取：等待熱鍵釋放、剪貼簿 settle 與剪貼簿輪詢都改由 Qt 計時器分階段推進，不再同步卡住主視窗
- `取消目前操作` 現在可中止選取文字擷取階段，API 重試退避等待期間也會更快響應取消
- 設定頁資訊架構改為「連線與模型 → 翻譯方式與快捷鍵 → 介面與進階」，強化先完成連線再開始使用的主路徑
- UI 主題 token 重構為偏 Material Design 方法論的語義色彩系統，讓主按鈕、次按鈕、導航 selected、badge、warning / danger 狀態各自有明確角色
- 主視窗、結果浮窗與框選遮罩共用同一套主題角色，深色 / 淺色樣式與執行期切換邏輯一併收斂
- README 改為繁體中文預設版，並補上簡體中文與英文版本
- `docs/` 下的架構、開發與打包文檔補齊三語版本
- 非 QSS 的 UI 色彩常數開始收斂到 `app/ui/theme_tokens.py`
- 全面重構淺色與深色主題色彩，導入基於 Material Design 3 的「黑白與冷灰階 (Slate / Graphite)」高質感配色系統
- 移除設定介面多餘的邊框 (Box-in-box)，改以留白與背景色階 (Surface Tones) 來建立視覺層級
- 優化下拉選單圖示，將方形/減號替換為符合使用直覺的 SVG 箭頭
- 強化按鈕的視覺層級，動態依據未儲存狀態強調「儲存設定」主要按鈕 (Primary Action)
- 改善表單錯誤狀態 (Error States) 顯示，移除具攻擊性的紅色大框，改用內斂的文字與輸入框邊框提示
- 將深色模式的輸入框改為深邃內嵌式 (Recessed Inputs)，搭配柔光白主色提升長時間閱讀的舒適度
- 基於「親密性原則」優化設定頁面空間排版，拉大無關聯區塊間的間距 (32px)、縮小強關聯選項內的間距 (10px)，提升視覺層次感與呼吸空間
- 為翻譯結果懸浮視窗 (Translation Overlay) 的右下角加入半透明的「縮放把手 (Resize Grip)」SVG 圖示，增加拖曳縮放的視覺直覺性 (Affordance)
- 優化無障礙焦點狀態 (Focus States)，選單按鈕與輸入框在獲得焦點時會給予更明確的底色提亮與主題色外框，提升鍵盤操作的視覺回饋

### Fixed
- 修復選取文字或手動輸入流程會被圖片提示詞、快捷鍵等無關欄位阻塞的問題
- 清理未使用的 `app/constants.py` 與未被呼叫的 `ApiClient.translate_image()`
- 修正 `取消目前操作` 與 `刪除` 動作共用危險色的語義錯置，改以 warning / danger 分離處理
- 修正 `儲存設定`、`開啟輸入框`、disabled 與 validation 狀態在淺色主題下容易混淆的問題
- 修正選取文字翻譯會連發兩個 tray 氣泡的問題，現在只會在真正送出請求時顯示一次 processing 通知
- 修正 pinned 結果浮窗在換螢幕、拔除副螢幕或解析度變更後可能恢復到可視區域外的問題
- 修正 `load_config()` 會把設定遷移錯誤誤判成壞設定檔並重建 config 的問題
- 補上選取文字 async 流程、取消與浮窗位置夾回邏輯的回歸測試

## Earlier work

先前版本已完成這些基礎能力：

- Prompt Preset 系統與四組內建方案
- 選取文字與手動輸入入口
- Provider adapter 分層（OpenAI / Gemini compatible）
- `services / providers / platform / settings_service` 模組化拆分
- i18n locale 資源外置
- 背景請求取消、stale result 保護與執行期日誌
- PyInstaller 打包、CI、協作與安全文檔
