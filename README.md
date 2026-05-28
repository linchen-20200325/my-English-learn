# 📚 英文學習儀表板

以 Python + [Streamlit](https://streamlit.io) 製作的英文學習儀表板，資料以本機 JSON 檔持久化。

功能：
- **總覽** — 學習統計、每日一句、今日目標、本週學習圖、待辦提醒
- **單字學習** — 翻面單字卡 + 單字庫（新增／刪除／標記學會）
- **單字測驗** — 從單字庫隨機四選一、即時對錯回饋與計分
- **字根速記（離線）** — 字首／字中／字尾三張 Mermaid 心智圖 + 20 個 SEED 單字台味諧音速記（含 KK 音標、自然發音、圖像聯想），同步顯示於單字學習翻面卡背面，**不需 API**
- **單字庫** — 大型單字資料庫（諧音、KK、自然發音、口語例句、用法說明），支援搜尋與分頁；資料由 `scripts/generate_vocab.py` 用 Claude API 批次生成寫入 `vocab_bank.json`
- **情境會話生成** — 輸入生活情境，串接 Claude API 產生對話心智圖（Mermaid）與速記句卡（詞塊、KK 音標、自然發音、搞笑諧音），可存成課程或加入複習
- **複習（SRS）** — 句卡以 SM-2 間隔重複排程，每天只複習到期卡，三鍵評分（忘記／普通／簡單）自動安排下次出現
- **學習進度** — 累計天數／時間、最佳連續天數、平均測驗分數、單字掌握度
- **學習計畫** — 待辦清單 + 每週七天計畫

> 「情境會話生成」需設定 Anthropic API 金鑰：本機設環境變數 `ANTHROPIC_API_KEY`，Streamlit Cloud 則於 **Settings → Secrets** 加入 `ANTHROPIC_API_KEY`。未設定時其餘分頁照常運作。

## 🚀 一鍵部署到 Streamlit Community Cloud

[![Deploy to Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy?repository=linchen-20200325/my-English-learn&branch=main&mainModule=streamlit_app.py)

點上方按鈕，使用 GitHub 帳號登入 [share.streamlit.io](https://share.streamlit.io) 後即可部署。部署設定已預填：

| 欄位 | 值 |
|------|----|
| Repository | `linchen-20200325/my-English-learn` |
| Branch | `main` |
| Main file path | `streamlit_app.py` |

部署所需檔案皆已就緒：`requirements.txt`（相依套件）、`.streamlit/config.toml`（主題）、`streamlit_app.py`（進入點）。

## 💻 本機執行

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

瀏覽器開啟 `http://localhost:8501` 即可使用。

## 🗂️ 專案結構

```
streamlit_app.py        # 主程式（九個分頁與互動邏輯）
data.py                 # 種子單字、每日一句、每週計畫範本
morphology.py           # 字根字首字尾 + SEED 單字諧音速記（離線資料）
vocab_bank.json         # 大型單字庫（由生成腳本填入）
scripts/
  generate_vocab.py     # 批次呼叫 Claude API 生成單字資料
  vocab_wordlist.txt    # 詞表（一行一字，預設 ~250 高頻詞）
requirements.txt        # 相依套件（streamlit、pandas、anthropic）
.streamlit/config.toml  # 主題設定
dashboard_data.json     # 執行期自動產生的學習資料（已 gitignore）
```

## 📝 注意事項

- 學習資料存於 `dashboard_data.json`。在 Streamlit Community Cloud 上檔案系統為暫存性質，**重新部署或休眠後資料可能重置**；若需長期保存，建議改接資料庫或 Google Sheets 等外部儲存。
