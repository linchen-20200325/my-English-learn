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

## 🛠️ 檔案結構與核心組件
- `CLAUDE.md`: 核心開發與治理協議 (v2.0)
- `STATE.md`: 專案熱資料與進度追蹤（本檔）
- `streamlit_app.py`: Streamlit 主程式入口（九分頁：總覽／單字學習／測驗／字根速記／單字庫／情境生成／複習／進度／計畫）
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
