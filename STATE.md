# 專案戰情室 (Project State)

## 📌 當前狀態
- **專案**: 英文學習儀表板 (English Learning Dashboard)
- **環境**: Streamlit Cloud + GitHub
- **進度**: 代碼淨化與收尾完成。11 大分頁通過 AppTest 驗證,Streamlit Cloud + GitHub auto-push 流程就緒。新增 SRS 每日複習上限 + GitHub 風格學習熱力圖。
- **分支**: `main`(預設分支)+ 開發分支 `claude/brave-lovelace-Q786A`、`claude/affectionate-bardeen-wMVbS`

## 🆕 本次優化（科學學習 + 閱讀 + 字庫）
- **介面整理**：導覽 11→10 項。「🗣️ 口說範本」＋「🤖 情境生成」合併為單一「💬 情境會話」（`view_scenario`，分頁：口說範本/AI 情境生成）；「📈 學習進度」更名「📊 學習儀表板」（含 SRS 記憶監督），與日文版一致。
- **閱讀理解測驗**（`comprehension.py`）：7 篇互動閱讀皆加入選擇題,讀完即時批改+解析,分數計入今日統計（主動回憶 active recall）。
- **記憶科學監督**（`view_progress`／學習儀表板）：複習牌組的記憶強度分布（新卡/學習中/漸熟/已掌握）、熟練比例、今日待複習、**未來 7 天複習負擔預測圖**。
- **字庫與詞表擴充**：`vocab_bank.json` 50 → 106 字；`scripts/vocab_wordlist.txt` 擴充至 468 字供 AI 生成。
- **修正**：AI 生成單字推回成功後資料庫數字不更新（同步寫回本機 + 清快取）。
- **SRS 每日複習上限**:預設 20/可調 5-200;`last_reviewed` 計算今日已複習數,達標自動停止避免疲乏。
- **學習熱力圖**:GitHub 風格 12 週 × 7 天網格,強度公式 = 分鐘 + 學會字×3 + 測驗次×5,5 級漸層配色 + tooltip + 圖例。

## 📌 現行主線（已遷入獨立 repo `linchen-20200325/Tawian_law`）
- 遺產稅系統已從 `my-english-learn` 遷入獨立 repo **`Tawian_law`**（`main`），並部署於 Streamlit Cloud。
- **v1.1 更新（2026-07-03）**：民法繼承由「僅第一順位」擴充為**完整四順位＋配偶並存（§1144）**：
  - 無子女→配偶＋父母（配偶 ½）；再無父母→配偶＋兄弟姊妹（配偶 ½）；再無→配偶＋祖父母（配偶 ⅔）。
  - 特留分分數依 §1223：卑親屬/父母/配偶＝應繼分 ½；兄弟姊妹/祖父母＝應繼分 ⅓。
  - 遺產稅新增**父母（直系尊親屬）扣除額 138 萬/人**（上限 2 人）。
  - 重組家庭：新增「前段婚姻子女數」欄位＋專屬診斷，點明前婚子女與現任子女法律平等、須靠策略Ｂ保險補償。
  - 核心函式 `calc_reserved_portion` → 改寫為 `calc_inheritance`；驗證：11 項純函式測試＋7 情境 AppTest 全綠。

## 🆕 遺產稅規劃系統（分支 `claude/streamlit-estate-tax-planner-r5kzrc`）
- `app.py`: 獨立 Streamlit 工具「自動化遺產分配・特留分計算・保險避稅補償規劃系統」。
- 四階段確定性演算法（純函式與 UI 解耦，通過單元測試 + AppTest）：
  1) 淨遺產（喪葬費 138 萬，負值歸零＝限定繼承）
  2) 2026 遺產稅（免稅額 1,333 萬／配偶 553 萬／子女 56 萬；10/15/20% 累進，差額 281.05 萬・843.15 萬）
  3) 民法應繼分＝1/繼承人數、特留分＝應繼分×½（§1223）、特留分總額
  4) 保險策略Ａ 預留稅源＝遺產稅、策略Ｂ 特留分補償＝特留分總額（保險法 §112）
- 實質課稅警示：資產≥1 億或年齡≥75 → 建議分期繳＋分年贈與 244 萬。
- **資料架構（SSOT）**：無持久化。所有 2026 稅法/民法數字集中於 `app.py` 頂端「法定常數區塊」（`FUNERAL_DEDUCTION`、`BASIC_EXEMPTION`、`SPOUSE_DEDUCTION`、`CHILD_DEDUCTION`、`TAX_BRACKET_1/2`、`PROGRESSIVE_DIFF_15/20`、`ANNUAL_GIFT_EXEMPTION`、`HIGH_ASSET_ALERT`、`HIGH_AGE_ALERT`）→ 為稅法參數的**單一真實來源**，未來修法只改此區塊。輸入→純函式（`calc_net_estate`／`calc_estate_tax`／`calc_reserved_portion`／`calc_insurance_plan`）→UI 呈現，單向資料流，無 session state 依賴、無外部 I/O。

## 🧠 記憶點 (Memory Checkpoint) — 2026-07-03
- **里程碑**：遺產稅規劃系統 v1.0 完成並 **merge 進 `main`**（PR）。
- **驗證狀態**：9 項純函式單元測試 + Streamlit AppTest headless 全綠（14 個 st.metric、級距交界稅額連續、除零/負值/超額防禦）。
- **下一步接手點**：如需擴充，候選為 ①第二/三順位繼承人（父母、兄弟姊妹）②農地/公設地扣除額 ③配偶剩餘財產差額分配請求權。修改前務必先讀 `app.py` 法定常數區塊（SSOT）。

## 🛠️ 檔案結構與核心組件
- `CLAUDE.md`: 核心開發與治理協議 (v2.0)
- `STATE.md`: 專案熱資料與進度追蹤（本檔）
- `streamlit_app.py`: Streamlit 主程式入口（九分頁：總覽／單字學習／測驗／字根速記／單字庫／情境生成／複習／進度／計畫）
- `app.py`: 遺產稅・特留分・保險傳承規劃系統（獨立 Streamlit 工具，四階段確定性演算法，稅法常數 SSOT）
- `data.py`: 種子單字、每日一句、每週計畫範本
- `morphology.py`: 字根字首字尾構詞元件 + SEED 單字台味諧音速記（離線資料）
- `vocab_bank.json`: 大型單字庫（由 `scripts/generate_vocab.py` 透過 Gemini API 批次填入，含諧音／例句／用法／詞性／同源衍生字）
- `scripts/generate_vocab.py`: 批次生成腳本（讀 `vocab_wordlist.txt` → 呼叫 Claude → 寫 `vocab_bank.json`，可重跑略過已完成）
- `scripts/vocab_wordlist.txt`: 詞表（預設 ~250 字高頻詞,可換成 COCA/TOEIC/Oxford 4000）
- `requirements.txt`: 依賴清單（streamlit、pandas、anthropic）
- `.streamlit/config.toml`: 主題與瀏覽器設定
- `README.md`: 專案說明 + 一鍵部署徽章
- `dashboard_data.json`: 執行期學習資料（已 gitignore）

## 🐞 待辦與已知 Bug
- [x] 建立 `main` 並把 README 部署徽章與 Cloud 設定的 branch 改為 `main`
- [x] 確認主程式檔名規範:**維持 `streamlit_app.py`**(Streamlit Cloud 預設自動偵測、所有 docs/PR 已長期引用,改名零收益且打斷 CI/部署設定)。
- [x] 評估是否建立 `Requirements.md`:**不建立**(CLAUDE.md 已寫治理協議 + STATE.md 寫熱資料與進度,Requirements 會與兩者重疊且快速腐爛,維護成本 > 收益)。
- [x] 效能優化:`data.py` 種子已是 module-level 常量(Python import 已 O(1) 快取),加 `st.cache_data` 反引入 wrapper 開銷,審計確認**不適用**。
- [x] 情境生成 / 單字庫 / 字根速記 AI 補例字均支援 `GEMINI_API_KEY` 或 `GEMINI_API_KEYS` 多 key 輪轉;sidebar 有「測試所有金鑰」逐把驗證,未設時各分頁顯示具體設定指引(連結至 https://aistudio.google.com/apikey 與 Cloud Secrets toml 範例)。
- [x] Mermaid 心智圖渲染:headless AppTest 全綠 + PR #10/#12/#16 三波修正(從 mindmap → flowchart LR、樹狀替代、半形括號清潔、_sanitize_mermaid 救援)後實機 已穩定。如未來瀏覽器仍見 syntax error,展開「🔍 檢視 Mermaid 原始碼」截圖開新 issue。
- [x] 句卡接成間隔重複(SRS)複習:`data["review_cards"]` + SM-2 三鈕(忘記／普通／簡單),側欄顯示待複習數
- [x] SRS 每日複習上限:複習頁加 slider(預設 20 / max 200);superseed last_reviewed 計算今日已複習數;達標顯示「今日達標」訊息。
- [x] 學習熱力圖:📈 學習進度頁新增 GitHub 風格 12 週 × 7 天熱力圖,強度 = 分鐘 + 學會字×3 + 測驗次×5,5 級顏色 + tooltip + 圖例。
- [x] 雲端永久學習進度:sidebar 加「📤 雲端備份學習進度」按鈕,透過 `_push_file_to_github` 把 `dashboard_data.json` commit 回 repo;Cloud 重新部署後 `load_data()` 自動恢復(取代「需接外部儲存」原方案)。需 `GITHUB_TOKEN`。
