# Rust 重構調查與暫緩決策

**狀態：已記錄，暫不執行。** 使用者於 2026-11-06 決定先優化現有 Python／Qt 程式。此文件保留未來選型依據；尚未選定框架，也不啟動 Rust 原型、遷移或新增 Rust 執行期。待使用者明確要求重啟評估／重構時，再依當時版本重新查核與實測。

查核日期：2026-11-06。此文件是架構與官方文件調查；尚未建立等功能 Rust 版本，也沒有 Rust 版的記憶體實測。下列記憶體判斷是依渲染引擎、依賴和程序生命週期做的工程評估，不能當成 MB 排名。

Rust GUI 沒有固定的方案總數。以下列出 25 個具名框架／整合路線，分成六類；部分可以互相組合。`windows` 與 `windows-sys` 是 Windows API 綁定，`winit` 是視窗／事件層，`wgpu` 是繪圖層，均不能直接視為一套包含文字輸入與表單的完整 UI 框架。同一框架的 CPU／GPU 後端也應分開測量。

## 1. Windows 系統 UI

| 路線 | 對本專案的意義 | 評估 |
|---|---|---|
| 1. Rust + Win32（windows / windows-sys） | 使用系統視窗、控制項、RichEdit，搭配 GDI／DirectWrite／Direct2D；全域快捷鍵、系統匣、剪貼簿和置頂浮窗也可走 Windows API。 | 追求低常駐用量時值得做基準原型。現在的自訂外觀與 Markdown 排版需要額外實作；不是將 API 邏輯翻譯成 Rust 就完成。官方：[Windows API bindings](https://microsoft.github.io/windows-docs-rs/doc/windows/Win32/)。 |
| 2. native-windows-gui（NWG） | 在 Win32 控制項上增加較方便的 Rust 封裝，包含系統匣與控制項。 | 簡單設定表單很合適。官方稱其為輕量包裝；查核時主倉庫最近推送為 2024-05-16，採用前須確認所需功能與維護能力。來源：[專案說明](https://github.com/gabdube/native-windows-gui/blob/master/readme.md)、[倉庫資料](https://api.github.com/repos/gabdube/native-windows-gui)。 |
| 3. Rust 核心 + WinUI 3 宿主／橋接 | Fluent 外觀、XAML 與 Windows 整合。 | 是混合方案。官方主要支援 C#／C++ 的開發流程，Rust 整合與部署成本須另估；不能與直接用 Win32 控制項視為同樣的資源成本。[官方說明](https://learn.microsoft.com/en-us/windows/apps/winui/winui3/)。 |

## 2. 跨平台既有工具箱的 Rust 綁定

| 路線 | 渲染／依賴 | 對本專案的評估 |
|---|---|---|
| 4. fltk-rs | FLTK；可靜態連結。 | 低記憶體工具值得優先測試。完整表單、文字顯示等工具箱功能可減少自行造元件的工作；目前外觀、透明浮窗、中文輸入和 Markdown 選字仍要驗證。[官方 README](https://github.com/fltk-rs/fltk-rs)。 |
| 5. gtk4-rs / Relm4 | GTK4、GLib、Pango 等；Relm4 是 GTK4 上的應用框架。 | Linux 也是主要目標時較有吸引力。Windows 可用，但依賴部署與本機體驗要一起評估，並非以 Windows 便攜低用量為唯一目標的首選。[GTK4](https://github.com/gtk-rs/gtk4-rs)、[Relm4](https://github.com/Relm4/Relm4)。 |
| 6. Rust + Qt（CXX-Qt 等） | 保留 Qt，移除或縮小 Python 層。 | 可保留 Qt 能力，Qt 字型回退與圖片資源成本仍需處理。CXX-Qt 主要處理 QObject／C++／QML 整合，不提供完整 QWidget Rust 綁定，不能逐行替換目前 PySide6 程式。[官方說明](https://github.com/KDAB/cxx-qt)。 |

## 3. 自行繪製 UI 的 Rust 框架

| 路線 | 官方文件中的渲染方向 | 對本專案的評估 |
|---|---|---|
| 7. Slint | Winit 下有簡單 software、Skia software、FemtoVG、Skia GPU、Vello 等。 | 自訂外觀與宣告式 UI 的候選。應實測 Skia software 和 GPU 後端；不能以「Slint」一個名稱推斷用量。簡單 software renderer 的官方文件仍列文字支援限於 western scripts，且部分陰影／裁切效果未實作，中日文工具不可直接假設它滿足需求。[後端表](https://docs.slint.dev/latest/docs/slint/guide/backends-and-renderers/backend_winit/)、[渲染限制](https://docs.slint.dev/latest/docs/slint/guide/backends-and-renderers/backends_and_renderers/)。 |
| 8. Iced | wgpu GPU 後端，以及 tiny-skia 軟體後端。 | **兼顧完整 Rust UI 和低用量，值得先測 tiny-skia。** 表單與非同步工作適合現有功能。中日文輸入、跨螢幕 DPI、透明浮窗、長文選字與 Markdown 是原型驗收項目。官方仍稱為 experimental，需選定版本後驗證。[官方 README](https://github.com/iced-rs/iced)、[後端文件](https://docs.iced.rs/iced_core/backend/enum.Backend.html)。 |
| 9. egui / eframe | Immediate mode UI；eframe 可搭配 Glow 或 WGPU。 | 快速做工具與原型很合適。中文需配置字型，字型資料和 atlas 都要計入用量。Immediate mode 不代表必須一直以 60 FPS 運轉；官方說明在沒有互動／動畫時不持續重繪。[官方 README 的 CPU 與字型說明](https://github.com/emilk/egui)。 |
| 10. GPUI | 混合 immediate／retained，GPU 加速。 | 適合複雜自訂 UI，但不應因為 Zed 使用它就假設小工具用量最低。需要量測 GPU 裝置、字型和繪圖快取的固定成本。[官方網站](https://gpui.rs/)。 |
| 11. Floem | 多種 GPU 後端，也有 tiny-skia CPU fallback。 | 宣告式／細粒度反應式路線。官方明示仍在成熟中、會有破壞性變更；不要只把它歸成 GPU-only。[官方 README](https://github.com/lapce/floem)。 |
| 12. Xilem / Masonry | Winit、文字堆疊、Vello；2026 年官方進度亦提到 Vello CPU。 | 可列技術原型候選；官方仍明確標示 experimental。不要依舊文章認定永遠只有 GPU 後端。[README](https://github.com/linebender/xilem)、[2026 Q1 進度](https://linebender.org/blog/tmil-25/)。 |
| 13. Makepad | 自有跨平台 UI runtime、DSL、GPU 2D／3D。 | 自訂視覺與複雜互動的另一條路。對以文字為主的小工具，需先確認其固定資源成本是否划算。[官方 README](https://github.com/makepad/makepad)。 |
| 14. Freya | 跨平台、原生編譯、宣告式 Rust UI。 | 可列候選；評估時應依目前版本查核元件／文字／視窗能力，避免套用舊版本的架構印象。[官方 README](https://github.com/marc2332/freya)。 |
| 15. Ribir | 宣告式 Rust UI、預設 WGPU。 | 官方仍註記文字／IME 和元件處於較粗糙的階段、API 未穩定；這個依賴中文輸入與選字的工具不宜優先直接整套遷移。[官方 README](https://github.com/RibirX/Ribir)。 |
| 16. Vizia | 宣告式、Skia、自有元件。 | 又一條無 WebView 的路線；效益須由同樣文字內容、視窗數與功能的原型驗證。[官方 README](https://github.com/vizia/vizia)。 |
| 17. KAS | 自有元件／文字系統，具鍵盤與部分 IME／輔助功能支援。 | 可研究，但先驗證中文編輯與候選字位置；存在框架不代表現有功能可無成本移植。[官方 README](https://github.com/kas-gui/kas)。 |
| 18. Cushy | Winit + WGPU + cosmic-text。 | 官方標為 alpha／experimental，適合探索，不列本次重構的優先候選。[官方 README](https://github.com/khonsulabs/cushy)。 |

## 4. 系統 WebView

| 路線 | 架構 | 對本專案的評估 |
|---|---|---|
| 19. Tauri | Rust 核心 + 系統 WebView；Windows 為 WebView2。 | 完整 UI、Markdown、文字選取和樣式較方便，低記憶體需看完整程序群。小安裝包不能代表小執行用量。[官方程序模型](https://tauri.app/concept/process-model/)。 |
| 20. Dioxus Desktop | 應用邏輯以 Rust 編譯，桌面 UI 使用系統 WebView／Wry。 | 使用 Rust 寫 UI 邏輯，仍不等於沒有瀏覽器引擎。與 Dioxus Native 是不同路線。[官方 Desktop 指南](https://dioxuslabs.com/learn/0.7/guides/platforms/desktop/)。 |
| 21. Wry + 自行組裝 | 較低層的 WebView 包裝，自行處理視窗／IPC 等。 | 可以減少高層應用框架，但 WebView2 成本仍在，也要自行補齊更多應用能力。[官方 README](https://github.com/tauri-apps/wry)。 |

## 5. HTML／CSS 風格的自有渲染器

| 路線 | 架構 | 對本專案的評估 |
|---|---|---|
| 22. Dioxus Native / Blitz | 自有 HTML/CSS DOM／渲染堆疊，與系統 WebView 不同。 | 可能兼顧 CSS 與無 WebView 的架構，值得追蹤。查核時 Blitz README 為 beta，仍明示缺少功能與 bug；不能假設它和完整瀏覽器等價。[Blitz 官方狀態與架構](https://github.com/DioxusLabs/blitz)。 |
| 23. Azul | WebRender、CSS／HTML 風格 DOM。 | 查核時官方 README 明示尚不可用，不列目前正式重構候選，避免被舊介紹誤導。[官方狀態](https://github.com/fschutt/azul)。 |

## 6. 混合與程序分工

| 路線 | 架構 | 對本專案的評估 |
|---|---|---|
| 24. Flutter + Rust（flutter_rust_bridge） | Dart／Flutter UI + Rust 邏輯。 | 元件和自訂外觀是一個方向，整體仍包含 Flutter runtime，需量測；不是全 Rust UI，也不能先認定記憶體更低。[官方橋接專案](https://github.com/fzyzcjy/flutter_rust_bridge)。 |
| 25. Rust 常駐核心 + 按需 UI 程序 | 常駐程序處理系統匣、熱鍵、請求；設定 UI 另開程序，用完退出。UI 可用既有 PySide6、Tauri 或上表其他框架。 | 對「平常常駐、偶爾開設定」尤其值得評估。GUI 程序退出能回收該程序資源，但 IPC、設定同步、浮窗和取消操作需重新設計。這是可搭配多種框架的架構選項，非另一個獨立 GUI 套件。 |

## 對本專案的建議

1. 先處理已在 Windows 原始碼測試中重現的字型指定／回退問題。它能解釋額外約 300 MiB 的用量，不能直接把這部分歸為 Python 的固定成本。
2. 若仍想完整遷移 Rust，優先做 **Iced + tiny-skia、Slint + Skia software、fltk-rs、Win32** 四個候選的精簡原型。這個順序考量現有功能與開發便利，不是記憶體實測排名。純粹以低常駐資源為第一目標時，Win32 是有價值的基準。
3. 原型須包括繁中／日文長文、IME 候選字、文字選取複製、透明置頂浮窗、雙螢幕 DPI、系統匣與快捷鍵；只有英文 Hello World 不足以做決策。Markdown 的表格／程式碼區塊與串流更新也須納入。
4. 比較 fresh process 的啟動峰值、可見／隱藏的 Private Bytes 與工作集、十次截圖後是否穩定、關閉 UI 後的常駐基線、重開時間、閒置 CPU 與 GPU 記憶體。WebView 路線要統計整個程序群；共享工作集不可單純重複相加。
5. 如果最在意的是背景常駐用量，也應把「Rust 常駐核心 + 獨立設定 UI」納入比較，不必把所有 UI 長時間保留在同一程序。

上表直接連結官方文件與專案倉庫。查核日期只記錄本次調查時間；重新啟動此計畫前，需確認維護狀態、穩定版本、文字功能和渲染後端。
