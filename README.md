# 📚 英文學習儀表板

以 Python + [Streamlit](https://streamlit.io) 製作的英文學習儀表板，資料以本機 JSON 檔持久化。

功能：
- **總覽** — 學習統計、每日一句、今日目標、本週學習圖、待辦提醒
- **單字學習** — 翻面單字卡 + 單字庫（新增／刪除／標記學會）
- **單字測驗** — 從單字庫隨機四選一、即時對錯回饋與計分
- **學習進度** — 累計天數／時間、最佳連續天數、平均測驗分數、單字掌握度
- **學習計畫** — 待辦清單 + 每週七天計畫

## 🚀 一鍵部署到 Streamlit Community Cloud

[![Deploy to Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy?repository=linchen-20200325/my-English-learn&branch=claude/brave-lovelace-Q786A&mainModule=streamlit_app.py)

點上方按鈕，使用 GitHub 帳號登入 [share.streamlit.io](https://share.streamlit.io) 後即可部署。部署設定已預填：

| 欄位 | 值 |
|------|----|
| Repository | `linchen-20200325/my-English-learn` |
| Branch | `claude/brave-lovelace-Q786A` |
| Main file path | `streamlit_app.py` |

> 合併到 `main` 後，建議把上方徽章連結與部署設定的 Branch 改為 `main`。

部署所需檔案皆已就緒：`requirements.txt`（相依套件）、`.streamlit/config.toml`（主題）、`streamlit_app.py`（進入點）。

## 💻 本機執行

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

瀏覽器開啟 `http://localhost:8501` 即可使用。

## 🗂️ 專案結構

```
streamlit_app.py        # 主程式（五個分頁與互動邏輯）
data.py                 # 種子單字、每日一句、每週計畫範本
requirements.txt        # 相依套件
.streamlit/config.toml  # 主題設定
dashboard_data.json     # 執行期自動產生的學習資料（已 gitignore）
```

## 📝 注意事項

- 學習資料存於 `dashboard_data.json`。在 Streamlit Community Cloud 上檔案系統為暫存性質，**重新部署或休眠後資料可能重置**；若需長期保存，建議改接資料庫或 Google Sheets 等外部儲存。
