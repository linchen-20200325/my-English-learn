# 專案戰情室 (Project State)

## 📌 當前狀態
- **專案**: 英文學習儀表板 (English Learning Dashboard)
- **環境**: Streamlit Cloud + GitHub
- **進度**: 六大分頁已完成並通過 AppTest 驗證（新增「情境會話生成」串接 Claude API，輸出 Mermaid 心智圖＋句卡並可存課）；Streamlit Cloud 部署設定就緒；協議 v2.0 已部署
- **分支**: `main`（預設分支）+ 開發分支 `claude/brave-lovelace-Q786A`

## 🛠️ 檔案結構與核心組件
- `CLAUDE.md`: 核心開發與治理協議 (v2.0)
- `STATE.md`: 專案熱資料與進度追蹤（本檔）
- `streamlit_app.py`: Streamlit 主程式入口（六分頁：總覽／單字學習／測驗／情境生成／進度／計畫）
- `data.py`: 種子單字、每日一句、每週計畫範本
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
- [ ] 未來可將句卡接成間隔重複（SRS）複習排程；目前僅存於 `data["lessons"]`
- [ ] 已知限制：Streamlit Cloud 檔案系統為暫存，`dashboard_data.json` 重新部署後會重置（需長期保存須接外部儲存）
