# 專案戰情室 (Project State)

## 📌 當前狀態
- **專案**: 英文學習儀表板 (English Learning Dashboard)
- **環境**: Streamlit Cloud + GitHub
- **進度**: 代碼淨化與收尾完成。11 大分頁(總覽／單字學習／測驗／字根速記／口說範本／互動閱讀／單字庫／情境生成／複習／進度／計畫)通過 AppTest 驗證,Streamlit Cloud + GitHub auto-push 流程就緒。
- **分支**: `main`（預設分支）+ 開發分支 `claude/brave-lovelace-Q786A`

## 🛠️ 檔案結構與核心組件
- `CLAUDE.md`: 核心開發與治理協議 (v2.0)
- `STATE.md`: 專案熱資料與進度追蹤（本檔）
- `streamlit_app.py`: Streamlit 主程式入口（九分頁：總覽／單字學習／測驗／字根速記／單字庫／情境生成／複習／進度／計畫）
- `data.py`: 種子單字、每日一句、每週計畫範本
- `morphology.py`: 字根字首字尾構詞元件 + SEED 單字台味諧音速記（離線資料）
- `vocab_bank.json`: 大型單字庫（由 `scripts/generate_vocab.py` 透過 Claude API 批次填入，含諧音／例句／用法）
- `scripts/generate_vocab.py`: 批次生成腳本（讀 `vocab_wordlist.txt` → 呼叫 Claude → 寫 `vocab_bank.json`，可重跑略過已完成）
- `scripts/vocab_wordlist.txt`: 詞表（預設 ~250 字高頻詞,可換成 COCA/TOEIC/Oxford 4000）
- `requirements.txt`: 依賴清單（streamlit、pandas、anthropic）
- `.streamlit/config.toml`: 主題與瀏覽器設定
- `README.md`: 專案說明 + 一鍵部署徽章
- `dashboard_data.json`: 執行期學習資料（已 gitignore）

## 🐞 待辦與已知 Bug
- [x] 建立 `main` 並把 README 部署徽章與 Cloud 設定的 branch 改為 `main`
- [ ] 確認主程式檔名規範：維持 `streamlit_app.py` 或改名為 `app.py`（影響部署進入點）
- [ ] 評估是否建立 `Requirements.md` 作為需求真理來源
- [ ] 效能優化：對 `data.py` 種子載入導入 `st.cache_data`
- [ ] 情境生成需設定 `ANTHROPIC_API_KEY`（本機環境變數／Cloud Secrets）；未設定時該分頁顯示引導，其餘照常
- [ ] Mermaid 心智圖以 `st.iframe` 渲染，尚未經瀏覽器實機驗證（headless 僅驗腳本無例外）
- [x] 句卡接成間隔重複（SRS）複習：`data["review_cards"]` + SM-2 三鈕（忘記／普通／簡單），側欄顯示待複習數
- [ ] SRS 後續：可加每日複習上限、卡片來源標註、學習熱力圖統計
- [ ] 已知限制：Streamlit Cloud 檔案系統為暫存，`dashboard_data.json` 重新部署後會重置（需長期保存須接外部儲存）
