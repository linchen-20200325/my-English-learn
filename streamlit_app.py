"""英文學習儀表板 — Streamlit 版

執行：streamlit run streamlit_app.py
資料以本機 JSON 檔 (dashboard_data.json) 持久化。
"""

import html as _html
import json
import os
import random
import re
import sys
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data import SEED_WORDS, DAILY_PHRASES, DEFAULT_WEEKLY_PLAN
from dialogues import CONVERSATIONS, STORIES
from readings import READINGS
from comprehension import get_questions
from morphology import (PREFIXES, ROOTS, SUFFIXES, MNEMONICS, build_mindmap,
                        decompose_word, build_word_mindmap)

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard_data.json")
VOCAB_BANK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vocab_bank.json")
MORPH_EXAMPLES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "morph_examples_bank.json")
# AI 生成的閱讀永久庫（推回 GitHub 後會越長越多，重整不消失）
READINGS_BANK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "readings_bank.json")
# AI 生成的文法永久庫（依程度累積，越長越多）
GRAMMAR_BANK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "grammar_bank.json")
# AI 生成的情境課程永久庫（對話/句卡，累積長大）
LESSONS_BANK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lessons_bank.json")
# AI 生成的情境對話永久庫（加進口說範本、累積長大）
DIALOGUES_BANK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dialogues_bank.json")
# AI 生成的短篇故事永久庫（加進口說範本的短篇故事分頁、累積長大）
STORIES_BANK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stories_bank.json")
WEEKDAY_ZH = ["一", "二", "三", "四", "五", "六", "日"]  # Monday=0

# GEN_MODEL_TIERS 在下方 dispatcher 區段定義（依供應商映射到實際模型 ID）。

GEN_SYSTEM_PROMPT = """# 角色
你是科學化語言學習專家、記憶法大師兼資料工程師。

# 理論依據
1. 雙碼理論：透過心智圖視覺化建立大腦基模。
2. 間隔重複（SRS）：透過 JSON 抽認卡固化長期記憶。
3. 詞塊教學法：學習母語人士的固定搭配「詞塊（chunks）」。
4. 齊夫定律：嚴格只用日常最高頻的核心詞彙。
5. 精細複述與關鍵字記憶法：透過荒謬搞笑的中文諧音或視覺圖像，將外語聲音與母語意義強行連結。

# 任務
根據使用者訊息提供的【目標職業或情境】，產出符合上述理論的實用英文對話教材。
語言風格必須是母語人士的日常真實對話（casual & native）。

# 輸出限制（嚴格）
只輸出以下兩個程式碼區塊，前後與中間不得有任何開場白、結語或解釋文字。

## 區塊一：Mermaid flowchart 樹狀圖（中英雙語、嚴格語法）
用 ```mermaid 區塊製作一個 **`flowchart LR`** 樹狀圖（不要用 mindmap，mindmap 對特殊
字元容易解析失敗）。嚴格遵守以下語法,任何違規都會讓畫面顯示「Syntax error in text」:

**規則**:
- 第一行固定:`flowchart LR`
- 每個節點用 `nodeId["顯示文字"]` 寫法,nodeId 只能是 ASCII 英數字(n0、n1、n0_0、n1_2 ...)
- 節點文字務必用雙引號包起來
- **節點文字內絕對不可出現 `(` `)` `[` `]` `{` `}` 半形括號**(會被 mermaid 當形狀語法)。
  要表達括號請用全形 `（）` 或 `「」`
- 用 `-->` 連線
- 雙語用「英文 | 中文」分隔,例如 `n0_0["Hi there! | 你好!"]`

**結構**:
- root 節點:`root(("情境名稱中文"))`(雙重圓括號是 cloud 形狀,這裡是唯一允許的括號)
- 主分支 3-5 個,代表對話階段(開場、核心、結語等),英文 ≤ 3 字 + 中文標籤
- 每分支底下 2-4 個子節點,英文短句 ≤ 7 字 + 中文翻譯,用 `|` 分隔

**完整範例(請仿照產出,結構與標點都照抄)**:
```
flowchart LR
    root(("咖啡廳點餐"))
    n0["Opening 開場"]
    n1["Order 點餐"]
    n2["Complaint 反映問題"]
    n3["Closing 收尾"]
    root --> n0
    root --> n1
    root --> n2
    root --> n3
    n0_0["Hi there! | 嗨!"]
    n0 --> n0_0
    n0_1["What can I get you? | 想點什麼?"]
    n0 --> n0_1
    n1_0["A tall latte, please | 一杯中杯拿鐵"]
    n1 --> n1_0
    n2_0["This isn't what I ordered | 這不是我點的"]
    n2 --> n2_0
    n3_0["Sorry about that | 不好意思"]
    n3 --> n3_0
```

## 區塊二：SRS 抽認卡與速記法
用 ```json 區塊輸出 3 到 5 張最具代表性的金句，須取自心智圖中出現的句子。
嚴格符合此結構（請確保 JSON 完全合法、可被 Python 讀取）：
{
  "flashcards": [
    {"id": 1, "sentence": "...", "chinese": "...", "chunk": "...", "target_word": "...", "kk": "[...]", "phonics": "...", "mnemonic": "...", "context": "..."}
  ]
}
- "id"：唯一流水號（整數）
- "sentence"：完整實用英文句子
- "chinese"：繁體中文自然翻譯
- "chunk"：該句中最核心的母語人士常用詞塊
- "target_word"：從 chunk 中挑出一個最關鍵或最難記的單字
- "kk"：target_word 的 KK 音標（格式：[...]）
- "phonics"：target_word 的直覺式自然發音拆解（例如 schedule -> SKEH-jool）
- "mnemonic"：針對 target_word 的速記法，須是符合台灣人語感的搞笑諧音、網路迷因或極具視覺衝擊力的圖像記憶，越荒謬越好，一句話搞定
- "context"：一句繁體中文，說明在什麼具體情況下使用這句話
"""


# ----------------------------- 資料存取 -----------------------------
def today_str() -> str:
    return date.today().isoformat()


def default_state() -> dict:
    return {
        "words": [dict(w, id=i + 1, learned=False) for i, w in enumerate(SEED_WORDS)],
        "daily": {},
        "todos": [],
        "weekly_plan": [dict(p, id=i + 1, done=False) for i, p in enumerate(DEFAULT_WEEKLY_PLAN)],
        "goal": 10,
        "best_streak": 0,
        "phrase_index": datetime.now().timetuple().tm_yday % len(DAILY_PHRASES),
        "lessons": [],
        "review_cards": [],
    }


def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return default_state()


def save_data() -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.data, f, ensure_ascii=False, indent=2)


def today_entry() -> dict:
    daily = st.session_state.data["daily"]
    t = today_str()
    if t not in daily:
        daily[t] = {"minutes": 0, "words_learned": 0, "quiz_scores": []}
    return daily[t]


def has_activity(date_key: str) -> bool:
    e = st.session_state.data["daily"].get(date_key)
    return bool(e) and (e["minutes"] > 0 or e["words_learned"] > 0 or len(e["quiz_scores"]) > 0)


def compute_streak() -> int:
    streak = 0
    d = date.today()
    if not has_activity(today_str()):
        d -= timedelta(days=1)
    while has_activity(d.isoformat()):
        streak += 1
        d -= timedelta(days=1)
    if streak > st.session_state.data.get("best_streak", 0):
        st.session_state.data["best_streak"] = streak
        save_data()
    return streak


def last_7_days_df() -> pd.DataFrame:
    rows = []
    for i in range(6, -1, -1):
        d = date.today() - timedelta(days=i)
        e = st.session_state.data["daily"].get(d.isoformat())
        rows.append({"日期": f"{d.month}/{d.day}（{WEEKDAY_ZH[d.weekday()]}）",
                     "分鐘": e["minutes"] if e else 0})
    return pd.DataFrame(rows).set_index("日期")


def _render_activity_heatmap(weeks: int = 12) -> None:
    """GitHub 風格學習熱力圖(近 N 週 × 7 天)。
    每格代表一天,顏色深淺對應「分鐘 + 學會單字數 + 測驗次數」綜合活動量。"""
    daily = st.session_state.data.get("daily", {})
    today = date.today()
    # 以本週(週日結尾)當最右行
    end = today + timedelta(days=(6 - today.weekday()))
    start = end - timedelta(days=weeks * 7 - 1)

    def _intensity(d):
        e = daily.get(d.isoformat())
        if not e:
            return 0
        score = (e.get("minutes", 0)
                 + e.get("words_learned", 0) * 3
                 + len(e.get("quiz_scores", [])) * 5)
        return score

    # 收集所有強度找最大值,定 5 級
    scores = []
    cur = start
    while cur <= end:
        scores.append(_intensity(cur))
        cur += timedelta(days=1)
    mx = max(scores) if scores else 0

    def _color(score):
        if score == 0:
            return "#ebedf0"
        if mx == 0:
            return "#ebedf0"
        ratio = score / mx
        if ratio < 0.25:
            return "#9be9a8"
        if ratio < 0.5:
            return "#40c463"
        if ratio < 0.75:
            return "#30a14e"
        return "#216e39"

    # 渲染:7 行(週一→週日) × N 行(週)
    cells = []
    weekday_labels = ["一", "二", "三", "四", "五", "六", "日"]
    cells.append('<div style="display:flex; gap:3px; padding:8px 4px;">')
    cells.append('<div style="display:flex; flex-direction:column; gap:3px; '
                 'font-size:10px; color:#64748b; margin-right:4px; justify-content:space-around;">')
    for wl in weekday_labels:
        cells.append(f'<div style="height:14px;">{wl}</div>')
    cells.append('</div>')

    for wi in range(weeks):
        cells.append('<div style="display:flex; flex-direction:column; gap:3px;">')
        for di in range(7):
            day = start + timedelta(days=wi * 7 + di)
            if day > today:
                cells.append('<div style="width:14px; height:14px;"></div>')
                continue
            score = _intensity(day)
            color = _color(score)
            tip = f"{day.isoformat()}: {score} 點" if score else f"{day.isoformat()}: 無紀錄"
            cells.append(
                f'<div title="{tip}" style="width:14px; height:14px; '
                f'background:{color}; border-radius:3px;"></div>'
            )
        cells.append('</div>')
    cells.append('</div>')

    # 圖例
    legend = (
        '<div style="display:flex; align-items:center; gap:6px; font-size:11px; '
        'color:#64748b; margin-top:6px; padding-left:24px;">'
        '<span>少</span>'
        '<div style="width:12px; height:12px; background:#ebedf0; border-radius:2px;"></div>'
        '<div style="width:12px; height:12px; background:#9be9a8; border-radius:2px;"></div>'
        '<div style="width:12px; height:12px; background:#40c463; border-radius:2px;"></div>'
        '<div style="width:12px; height:12px; background:#30a14e; border-radius:2px;"></div>'
        '<div style="width:12px; height:12px; background:#216e39; border-radius:2px;"></div>'
        '<span>多</span></div>'
    )
    total_days = sum(1 for s in scores if s > 0)
    st.markdown("".join(cells) + legend, unsafe_allow_html=True)
    st.caption(f"近 {weeks} 週 = {weeks * 7} 天　·　**有紀錄 {total_days} 天**　·　"
               f"強度 = 分鐘 + 學會字×3 + 測驗次×5")


# ----------------------------- Gemini LLM dispatcher -----------------------------
# 免費 tier 每日請求數(GenerateRequestsPerDayPerProjectPerModel-FreeTier):
# - gemini-2.5-pro        ≈ 5  RPD  最強但極少
# - gemini-2.5-flash      ≈ 20 RPD  平衡
# - gemini-2.5-flash-lite ≈ 200 RPD 輕量、額度最多 ← 推薦
# - gemini-2.0-flash      ≈ 200 RPD 舊版但額度多、穩定
_MODEL_MAP = {
    "Flash-Lite（推薦，免費 ~200/天）": "gemini-2.5-flash-lite",
    "2.0 Flash（舊版但額度多，~200/天）": "gemini-2.0-flash",
    "Flash（平衡，免費 ~20/天）": "gemini-2.5-flash",
    "Pro（最強，免費僅 ~5/天）": "gemini-2.5-pro",
}
GEN_MODEL_TIERS = list(_MODEL_MAP.keys())


def _read_secret(name: str) -> str | None:
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.environ.get(name)


def _secret_names() -> list:
    """列出 st.secrets 中所有 key 名稱(不含值,用於偵錯顯示)。"""
    try:
        return list(st.secrets.keys())
    except Exception:
        return []


def _clean_keys(v) -> list:
    """從任何輸入(string/list/dict/含分隔符串接)抽出所有 AIza 開頭、長度 ≥ 30 的合法
    Gemini key 樣式。處理:控制字元、BOM、引號、換行/逗號/分號/Tab 分隔、'KEY=VAL' 形式。
    回傳去重且保序的 key 列表。"""
    import unicodedata as _ud
    if v is None:
        return []
    if isinstance(v, (list, tuple)):
        out = []
        for item in v:
            for k in _clean_keys(item):
                if k not in out:
                    out.append(k)
        return out
    if isinstance(v, dict):
        out = []
        for item in v.values():
            for k in _clean_keys(item):
                if k not in out:
                    out.append(k)
        return out
    # 字串:剝雜質。先把行尾/tab 換成空白(免得後面被當控制字元剝掉,失去 key 分隔)
    s = str(v).replace("\n", " ").replace("\r", " ").replace("\t", " ")
    s = "".join(c for c in s if _ud.category(c)[0] not in ("C", "M") or c == " ")
    s = s.strip()
    while len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'", "`"):
        s = s[1:-1].strip()
    # 切多 key:逗號/分號/換行/tab/等號/空白
    chunks = re.split(r"[,;\n\r\t=\s]+", s)
    out = []
    for c in chunks:
        c = c.strip().strip('"').strip("'").strip("`")
        if c.startswith("AIza") and len(c) >= 30 and c not in out:
            out.append(c)
    # 若整段沒切出任何 AIza key 但本身就是純 key,直接收
    if not out and s.startswith("AIza") and len(s) >= 30:
        out.append(s)
    return out


def _clean_key(v):
    """單一 key 取得(回傳第一個合法 key)。向後相容,sidebar 顯示用。"""
    keys = _clean_keys(v)
    return keys[0] if keys else None


def get_all_api_keys() -> list:
    """讀所有 Gemini key。標準名稱優先,再掃所有含 GEMINI/GOOGLE 名稱的 secret/env。
    支援單一 key、list、逗號串接、編號變體(GEMINI_API_KEY_1 / _2 ...)。
    回傳去重且保序的 key 列表,可在 _llm_generate 內輪流嘗試。"""
    keys = []
    seen = set()

    def _push(v):
        for k in _clean_keys(v):
            if k not in seen:
                seen.add(k)
                keys.append(k)

    for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GEMINI_KEY",
                 "GOOGLE_GENAI_API_KEY", "GEMINI_API_KEYS"):
        _push(_read_secret(name))
    for name in _secret_names():
        upper = name.upper()
        if ("GEMINI" in upper or "GOOGLE" in upper) and "API" in upper:
            _push(_read_secret(name))
    for name, val in os.environ.items():
        upper = name.upper()
        if val and ("GEMINI" in upper or "GOOGLE" in upper) and "API" in upper:
            _push(val)
    return keys


def get_api_key() -> str | None:
    """回傳第一把可用 key(優先未在 session 標記為耗盡的)。"""
    all_keys = get_all_api_keys()
    if not all_keys:
        return None
    try:
        exhausted = st.session_state.get("_exhausted_keys", set())
    except Exception:
        exhausted = set()
    fresh = [k for k in all_keys if k not in exhausted]
    return fresh[0] if fresh else all_keys[0]


def get_github_token() -> str | None:
    """讀 GitHub PAT,用於自動把 vocab_bank.json commit 回 repo。
    防呆:剝外層引號/空白/控制字元(複製貼上常見問題)。"""
    raw = (_read_secret("GITHUB_TOKEN")
           or _read_secret("GH_TOKEN")
           or _read_secret("GITHUB_PAT"))
    if not raw:
        return None
    import unicodedata as _ud
    s = str(raw).replace("\n", " ").replace("\r", " ").replace("\t", " ")
    s = "".join(c for c in s if _ud.category(c)[0] not in ("C", "M") or c == " ")
    s = s.strip()
    while len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'", "`"):
        s = s[1:-1].strip()
    return s or None


# 短暫伺服器忙(秒級重試有用)
_TRANSIENT_HINTS = ("503", "UNAVAILABLE", "overloaded", "high demand",
                    "DEADLINE_EXCEEDED")
# 配額耗盡(每日 free tier 上限,秒級重試無用,要等到隔天或換模型)
_QUOTA_HINTS = ("RESOURCE_EXHAUSTED", "429", "exceeded your current quota",
                "Resource has been exhausted")


def _friendly_gen_error(msg: str) -> str:
    """把生成錯誤翻成可行動的中文提示（區分配額／伺服器忙／金鑰／其他）。"""
    if any(h in msg for h in _QUOTA_HINTS):
        return ("⏰ **Gemini 今日免費額度用完了**（Google 每日上限，非程式問題）。解法："
                "①改用額度更多的模型（Flash-Lite／2.0 Flash）②等明天台灣 16:00 重置 "
                "③到 https://aistudio.google.com/apikey 開新 project 多生一把 key 貼進 Secrets。")
    if any(h in msg for h in _TRANSIENT_HINTS):
        return "⏳ Google 伺服器當下忙碌（503）。等 30 秒～2 分鐘再按一次，或改用負載較輕的模型。"
    if "API key not valid" in msg or "API_KEY_INVALID" in msg:
        return ("❌ Gemini 金鑰被拒。到 https://aistudio.google.com/apikey 重新「Create API key "
                "in new project」貼回 Cloud Secrets 的 `GEMINI_API_KEYS`。")
    if "尚未設定" in msg or "GEMINI_API_KEY" in msg:
        return "🔑 尚未偵測到 Gemini 金鑰。請至 Cloud Secrets 設定 `GEMINI_API_KEYS`。"
    return f"生成失敗：{msg[:500]}"


def _llm_generate(system_prompt: str, user_msg: str, tier: str,
                  max_tokens: int = 2000, retries: int = 3) -> str:
    """單次生成。支援多 key 輪轉:撞 429 RESOURCE_EXHAUSTED 自動換下一把 key,
    並把該 key 標記為今日已耗盡(放 st.session_state._exhausted_keys)。
    503 等暫時性錯誤仍走秒級退避重試。"""
    import time

    all_keys = get_all_api_keys()
    if not all_keys:
        raise RuntimeError("尚未設定 GEMINI_API_KEY")
    try:
        exhausted = st.session_state.setdefault("_exhausted_keys", set())
    except Exception:
        exhausted = set()
    # 優先用未耗盡的,全耗盡時再從頭跑一輪(也許 Google 已 reset)
    fresh_keys = [k for k in all_keys if k not in exhausted] or list(all_keys)

    model_id = _MODEL_MAP.get(tier) or next(iter(_MODEL_MAP.values()))

    from google import genai
    from google.genai import types

    last_err = None
    for key_idx, key in enumerate(fresh_keys):
        for attempt in range(retries):
            try:
                client = genai.Client(api_key=key)
                resp = client.models.generate_content(
                    model=model_id,
                    contents=user_msg,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.7,
                        max_output_tokens=max_tokens,
                    ),
                )
                return resp.text or ""
            except Exception as e:  # noqa: BLE001
                last_err = e
                em = str(e)
                # 配額耗盡:標記這把 key、立刻跳下一把,不浪費時間退避
                if any(h in em for h in _QUOTA_HINTS):
                    exhausted.add(key)
                    break  # 跳出 attempt 迴圈,換下一把 key
                # 短暫伺服器忙:秒級退避重試
                if attempt < retries - 1 and any(h in em for h in _TRANSIENT_HINTS):
                    time.sleep(2 ** attempt)
                    continue
                # 其他錯誤(API key invalid 等):立刻丟出
                raise
    if last_err:
        raise last_err
    return ""


def generate_material(scenario: str, tier: str) -> str:
    return _llm_generate(GEN_SYSTEM_PROMPT, f"Scenario: {scenario}", tier, max_tokens=2000)


_MORPH_GEN_PROMPT = """你是英文構詞學專家。給定某個{cat}「{m}」(意思:{zh}),
請列出 N 個含此{cat}、程度 B1-C1 常見實用的英文單字。

# 嚴格規範
- 必須真的含「{m}」的詞素(切空白用任一變體即可)
- 不可使用清單內已有的字:{existing}
- 全小寫(除非專有名詞)
- 只輸出 JSON array,例如 ["word1","word2","word3"],前後無任何文字、無 markdown

# 數量
回 {n} 個。
"""


def _gen_morph_examples(cat_zh: str, m: str, zh: str,
                        existing: list, n: int) -> list:
    """請 Gemini 對某個字首/字根/字尾補 n 個不重複的新例字。回 list of words。"""
    prompt = _MORPH_GEN_PROMPT.format(cat=cat_zh, m=m, zh=zh,
                                       existing=existing, n=n)
    text = _llm_generate(prompt, f"{cat_zh}「{m}」補 {n} 個例字",
                         next(iter(_MODEL_MAP.keys())), max_tokens=400)
    mm = re.search(r"\[[\s\S]*?\]", text)
    if not mm:
        return []
    try:
        words = json.loads(mm.group(0))
    except json.JSONDecodeError:
        return []
    exist_lower = {w.lower() for w in existing}
    out = []
    for w in words:
        ww = str(w).strip().lower()
        if (ww and ww not in exist_lower and ww not in {x.lower() for x in out}
                and re.match(r"^[a-z][a-z\-']*$", ww)):
            out.append(ww)
    return out[:n]


_NEW_MORPH_PROMPT = """你是英文構詞學專家。請補 {n} 個全新的英文「{cat}」(目前清單沒有的),
程度 B1-C1 常見實用、學習者該認識。

不可使用以下已有的 morpheme(無論大小寫):
{existing_m}

輸出嚴格 JSON array,每筆物件含三欄:
- "m": 該字首/字根/字尾的形式。字首結尾要 dash(例 "auto-"、"semi-");字尾開頭要 dash
  (例 "-able"、"-tion");多變體用空白隔開(例 "in- im-")。字根不加 dash。
- "zh": 繁中意思(精簡,1-2 詞,可用「／」分隔多義)
- "ex": 3 個常見英文例字(全小寫,陣列)

# 範例
- 字首:{{"m":"semi-","zh":"半／部分","ex":["semifinal","semicircle","semicolon"]}}
- 字根:{{"m":"voc voke","zh":"叫喚／聲音","ex":["vocal","provoke","advocate"]}}
- 字尾:{{"m":"-fy","zh":"使…成為","ex":["simplify","clarify","modify"]}}

只輸出 JSON array,前後無任何文字、無 markdown。
"""


def _gen_new_morphemes(cat_zh: str, existing_m: list, n: int) -> list:
    """請 Gemini 補 n 個全新的字首/字根/字尾條目(不重複 existing_m)。回 list of {m,zh,ex}。"""
    prompt = _NEW_MORPH_PROMPT.format(cat=cat_zh, n=n, existing_m=existing_m)
    text = _llm_generate(prompt, f"補 {n} 個新{cat_zh}",
                         next(iter(_MODEL_MAP.keys())), max_tokens=800)
    mm = re.search(r"\[[\s\S]*\]", text)
    if not mm:
        return []
    try:
        items = json.loads(mm.group(0))
    except json.JSONDecodeError:
        return []
    exist_lower = {str(m).strip().lower() for m in existing_m}
    out = []
    for it in items:
        if not isinstance(it, dict):
            continue
        m = str(it.get("m", "")).strip().lower()
        zh = str(it.get("zh", "")).strip()
        ex = it.get("ex", [])
        if not m or not zh or not isinstance(ex, list):
            continue
        if m in exist_lower or m in {x["m"] for x in out}:
            continue
        # ex 清洗
        clean_ex = []
        for w in ex:
            ww = str(w).strip().lower()
            if ww and re.match(r"^[a-z][a-z\-']*$", ww) and ww not in clean_ex:
                clean_ex.append(ww)
        if clean_ex:
            out.append({"m": m, "zh": zh, "ex": clean_ex[:6]})
    return out[:n]


def _sanitize_mermaid(text: str) -> str:
    """清潔 Gemini 產出的 mermaid 文字,避免常見解析失敗:
    - 移除節點標籤 `["..."]` 內部的半形括號(常被當形狀語法),改全形
    - 若第一行是 'mindmap',改成 'flowchart LR'(mindmap 對特殊字元易爆)
    - 保留 root((...)) 不動(這是合法的 cloud 形狀)
    """
    if not text:
        return text
    lines = text.splitlines()
    # 開頭規一化
    if lines and lines[0].strip().lower().startswith("mindmap"):
        lines[0] = "flowchart LR"

    # 清理 ["..."] 內的半形括號
    def _clean_label(m):
        inner = m.group(1)
        # 不動 root((..)) 形狀:這個函式只命中方括號雙引號內容
        inner = (inner.replace("(", "（").replace(")", "）")
                       .replace("[", "「").replace("]", "」")
                       .replace("{", "「").replace("}", "」"))
        return f'["{inner}"]'

    cleaned = []
    for ln in lines:
        ln = re.sub(r'\["([^"]*)"\]', _clean_label, ln)
        cleaned.append(ln)
    return "\n".join(cleaned)


def parse_blocks(text: str) -> tuple[str | None, list | None]:
    """從回應中抽出 mermaid 圖與 flashcards JSON。mermaid 經 _sanitize_mermaid 清潔。"""
    mermaid = None
    cards = None
    m = re.search(r"```mermaid\s*(.*?)```", text, re.DOTALL)
    if m:
        mermaid = _sanitize_mermaid(m.group(1).strip())
    j = re.search(r"```json\s*(.*?)```", text, re.DOTALL)
    if j:
        try:
            cards = json.loads(j.group(1).strip()).get("flashcards")
        except (json.JSONDecodeError, AttributeError):
            cards = None
    return mermaid, cards


_MERMAID_HTML = """
<div class="mermaid">__CODE__</div>
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
  mermaid.initialize({ startOnLoad: true, securityLevel: 'loose' });
</script>
"""


def render_mermaid(code: str, height: int = 420) -> None:
    html = _MERMAID_HTML.replace("__CODE__", code)
    if hasattr(st, "iframe"):  # Streamlit ≥ 1.57；components.html 於 2026-06-01 移除
        st.iframe(html, height=height)
    else:
        components.html(html, height=height, scrolling=True)


def render_flashcards(cards: list) -> None:
    for c in cards:
        with st.container(border=True):
            st.markdown(f"**{c.get('sentence', '')}**")
            if c.get("chinese"):
                st.markdown(f"🇹🇼 {c['chinese']}")
            if c.get("chunk"):
                st.markdown(f"🧩 詞塊：`{c['chunk']}`")
            if c.get("target_word"):
                bits = [f"🎯 **{c['target_word']}**"]
                if c.get("kk"):
                    bits.append(f"KK `{c['kk']}`")
                if c.get("phonics"):
                    bits.append(f"自然發音 `{c['phonics']}`")
                st.markdown("　".join(bits))
            if c.get("mnemonic"):
                st.markdown(f"🤯 速記：{c['mnemonic']}")
            if c.get("context"):
                st.caption(f"💡 {c['context']}")


def _embed_html(html: str, height: int) -> None:
    """渲染 HTML(含 JS)。優先 st.iframe(Streamlit ≥ 1.57),退回 components.html。"""
    if hasattr(st, "iframe"):
        st.iframe(html, height=height)
    else:
        components.html(html, height=height, scrolling=False)


def _esc_js(s) -> str:
    """逃脫字串以放入 JS string literal(單引號內)。"""
    return (str(s or "")
            .replace("\\", "\\\\").replace("'", "\\'")
            .replace("\n", " ").replace("\r", " "))


_TTS_BTN_TEMPLATE = """<button onclick="
  const u = new SpeechSynthesisUtterance('__TEXT__');
  u.lang='en-US'; u.rate=__RATE__;
  speechSynthesis.cancel(); speechSynthesis.speak(u);
" style="__STYLE__">__LABEL__</button>"""


def _tts_button_html(text: str, rate: float, style: str, label: str) -> str:
    return (_TTS_BTN_TEMPLATE
            .replace("__TEXT__", _esc_js(text))
            .replace("__RATE__", str(rate))
            .replace("__STYLE__", style)
            .replace("__LABEL__", label))


def render_flashcard(word: dict, mn: dict | None, flipped: bool) -> None:
    """整張單字卡用單一 components.html 渲染(讓 Web Speech API 在 iframe 內可執行 TTS)。
    正面:英文 + 諧音 + KK + 自然發音 + 🔊 唸；背面:中文意思 + 圖像 + 例句(含🔊) + 用法。"""
    w_en = _html.escape(word["word"])
    mn = mn or {}

    if not flipped:
        meaning_zh = _html.escape(mn.get("meaning_zh") or word.get("meaning", ""))
        pos = _html.escape(mn.get("pos", ""))
        homophone = _html.escape(mn.get("homophone", ""))
        kk = _html.escape(mn.get("kk", ""))
        phonics = _html.escape(mn.get("phonics", ""))
        tts_word = _tts_button_html(
            word["word"], 0.9,
            "margin-top:14px; padding:10px 22px; font-size:16px; border:none; "
            "border-radius:999px; cursor:pointer; background:rgba(255,255,255,.28); "
            "color:#fff; font-weight:600;",
            "🔊 唸這個字",
        )
        meaning_block = (
            f'<div style="font-size:26px; margin-top:10px; font-weight:600;">'
            f'{meaning_zh}</div>' if meaning_zh else ""
        )
        pos_block = (
            f'<div style="margin-top:8px;"><span style="display:inline-block; '
            f'background:rgba(255,255,255,.25); padding:4px 14px; border-radius:999px; '
            f'font-size:14px; font-weight:600;">📝 {pos}</span></div>' if pos else ""
        )
        # 其他型態列表
        other_forms = mn.get("other_forms") or []
        forms_html = ""
        if other_forms:
            items = "".join(
                f'<div style="margin:4px 0;"><span style="font-weight:600; color:#fef3c7;">'
                f'{_html.escape(f.get("word",""))}</span> '
                f'<span style="opacity:.85; font-size:13px;">({_html.escape(f.get("pos",""))})</span>'
                f' — {_html.escape(f.get("meaning_zh",""))}</div>'
                for f in other_forms[:4]
            )
            forms_html = (
                f'<div style="margin-top:14px; padding:10px 14px; '
                f'background:rgba(255,255,255,.12); border-radius:10px; '
                f'text-align:left; font-size:14px;">'
                f'<div style="opacity:.85; margin-bottom:4px;">💎 其他型態</div>'
                f'{items}</div>'
            )
        kk_block = (
            f'<span>KK <code style="background:rgba(255,255,255,.18); '
            f'padding:2px 8px; border-radius:6px;">{kk}</code></span>' if kk else ""
        )
        ph_block = (
            f'<span>自然發音 <code style="background:rgba(255,255,255,.18); '
            f'padding:2px 8px; border-radius:6px;">{phonics}</code></span>' if phonics else ""
        )
        pronunciation_block = (
            f'<div style="margin-top:14px; display:flex; justify-content:center; '
            f'gap:18px; flex-wrap:wrap; font-size:14px; opacity:.92;">'
            f'{kk_block}{ph_block}</div>' if (kk or phonics) else ""
        )
        # 📣 諧音 + 🖼️ 聯想：醒目顯示（記憶法是學習重點，不該縮小灰化）
        image = _html.escape(mn.get("image", ""))
        if homophone or image:
            hp = (f'<div style="font-size:20px; font-weight:800; '
                  f'color:#fde047;">📣 諧音 {homophone}</div>') if homophone else ""
            img = (f'<div style="margin-top:6px; font-size:14px; line-height:1.6; '
                   f'color:#f8fafc;">🖼️ {image}</div>') if image else ""
            homophone_block = (
                f'<div style="margin-top:16px; padding:12px 16px; '
                f'background:rgba(0,0,0,.18); border-radius:12px;">{hp}{img}</div>'
            )
        else:
            homophone_block = ""
        html = f"""
        <div style="background:linear-gradient(135deg,#6366f1,#8b5cf6); color:#fff;
                    border-radius:16px; padding:26px 24px; text-align:center;
                    font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;">
            <div style="font-size:42px; font-weight:800; letter-spacing:0.5px;">{w_en}</div>
            {meaning_block}
            {pos_block}
            {forms_html}
            {tts_word}
            {pronunciation_block}
            {homophone_block}
        </div>
        """
        # 動態高度估計
        h = 260
        if meaning_zh: h += 40
        if pos: h += 30
        if forms_html: h += 30 + 28 * min(len(other_forms), 4)
        if pronunciation_block: h += 40
        if homophone: h += 56
        if image: h += 30 + 22 * (len(image) // 22)
        _embed_html(html, h)
        return

    meaning = _html.escape(word.get("meaning", ""))
    example = mn.get("example_en") or word.get("example", "")
    example_esc = _html.escape(example)
    example_zh = _html.escape(mn.get("example_zh", ""))
    usage = _html.escape(mn.get("usage_zh", ""))
    image = _html.escape(mn.get("image", ""))
    tts_example = _tts_button_html(
        example, 0.95,
        "margin-left:8px; padding:6px 12px; font-size:14px; border:none; "
        "border-radius:999px; cursor:pointer; background:#4f46e5; color:#fff;",
        "🔊",
    ) if example else ""

    image_block = (f'<div style="margin-top:14px; padding:10px 14px; background:#fff; '
                   f'border-radius:10px;">🖼️ {image}</div>') if image else ""
    example_zh_block = (f'<div style="margin-top:6px; padding:8px 14px; background:#eef2ff; '
                        f'border-radius:8px; color:#3730a3; font-size:14px;">'
                        f'🇹🇼 {example_zh}</div>') if example_zh else ""
    example_block = (f'<div style="margin-top:10px; padding:10px 14px; background:#fff; '
                     f'border-radius:10px; display:flex; align-items:center; '
                     f'flex-wrap:wrap;">💬 <i style="flex:1; min-width:200px;">'
                     f'{example_esc}</i>{tts_example}</div>'
                     f'{example_zh_block}') if example else ""
    usage_block = (f'<div style="margin-top:10px; padding:10px 14px; background:#fff; '
                   f'border-radius:10px; font-size:14px; color:#475569;">💡 '
                   f'{usage}</div>') if usage else ""

    # 其他型態的「用法例句」(含 🔊)
    other_forms = mn.get("other_forms") or []
    forms_with_ex = [f for f in other_forms if f.get("example")]
    forms_block = ""
    if forms_with_ex:
        form_rows = []
        for f in forms_with_ex:
            fw = _html.escape(f.get("word", ""))
            fp = _html.escape(f.get("pos", ""))
            fm = _html.escape(f.get("meaning_zh", ""))
            fe = f.get("example", "")
            fe_esc = _html.escape(fe)
            fe_tts = _tts_button_html(
                fe, 0.95,
                "margin-left:6px; padding:4px 10px; font-size:13px; border:none; "
                "border-radius:999px; cursor:pointer; background:#b45309; color:#fff;",
                "🔊",
            )
            form_rows.append(
                f'<div style="margin:8px 0; padding:8px 12px; background:#fff; '
                f'border-radius:8px; border-left:3px solid #b45309;">'
                f'<div style="font-size:14px; color:#92400e;">'
                f'<b>{fw}</b> <span style="opacity:.7;">({fp})</span> — {fm}'
                f'</div>'
                f'<div style="margin-top:4px; display:flex; align-items:center; '
                f'flex-wrap:wrap; gap:4px;">'
                f'<i style="flex:1; min-width:180px; color:#1f2937; font-size:14px;">'
                f'💬 {fe_esc}</i>{fe_tts}</div>'
                f'</div>'
            )
        forms_block = (
            f'<div style="margin-top:12px; padding:10px 12px; background:#fffbeb; '
            f'border-radius:10px;">'
            f'<div style="font-size:14px; color:#78350f; font-weight:600; margin-bottom:4px;">'
            f'💎 其他型態用法</div>'
            + "".join(form_rows) + "</div>"
        )

    html = f"""
    <div style="background:#f8fafc; color:#312e81; border:2px solid #4f46e5;
                border-radius:16px; padding:22px;
                font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;">
        <div style="font-size:32px; font-weight:800; text-align:center;">{meaning}</div>
        {image_block}
        {example_block}
        {usage_block}
        {forms_block}
    </div>
    """
    # 動態高度估計
    h = (130 + (50 if image else 0)
         + (60 if example else 0)
         + (40 if example_zh else 0)
         + (50 if usage else 0)
         + (40 + 92 * len(forms_with_ex) if forms_with_ex else 0))
    _embed_html(html, h)


# ----------------------------- 複習 (SRS) -----------------------------
def add_cards_to_review(cards: list) -> int:
    """把句卡複製進複習清單並掛上 SM-2 排程欄位；以句子去重。回傳新增數。"""
    deck = st.session_state.data.setdefault("review_cards", [])
    existing = {c.get("sentence") for c in deck}
    next_id = max((c["id"] for c in deck), default=0) + 1
    added = 0
    for c in cards:
        if not c.get("sentence") or c["sentence"] in existing:
            continue
        rc = dict(c)
        rc.update(id=next_id, interval=0, ease=2.5, reps=0, due=today_str())
        deck.append(rc)
        existing.add(rc["sentence"])
        next_id += 1
        added += 1
    return added


def vocab_to_card(word: str, entry: dict) -> dict:
    """把單字庫的一筆單字轉成可進 SRS 的句卡（正面=單字，背面=意思/KK/諧音/例句）。"""
    ex_en = entry.get("example_en", "")
    ex_zh = entry.get("example_zh", "")
    context = f"{ex_en} — {ex_zh}".strip(" —") if (ex_en or ex_zh) else ""
    return {
        "sentence": word,                       # 複習正面顯示單字本身
        "chinese": entry.get("meaning_zh", ""),
        "target_word": word,
        "kk": entry.get("kk", ""),
        "phonics": entry.get("phonics", ""),
        "mnemonic": entry.get("image") or entry.get("homophone", ""),
        "context": context,
        "card_type": "vocab",
    }


def schedule_card(card: dict, grade: str) -> None:
    """SM-2 簡化版：grade 為 again / good / easy，就地更新排程。"""
    ease = card.get("ease", 2.5)
    reps = card.get("reps", 0)
    interval = card.get("interval", 0)
    if grade == "again":
        reps, interval = 0, 1
        ease = max(1.3, ease - 0.2)
    else:
        if reps == 0:
            interval = 1 if grade == "good" else 2
        elif reps == 1:
            interval = 3 if grade == "good" else 5
        else:
            interval = max(1, round(interval * (ease if grade == "good" else ease * 1.3)))
        reps += 1
        if grade == "easy":
            ease += 0.15
    card.update(
        ease=round(ease, 2),
        reps=reps,
        interval=interval,
        due=(date.today() + timedelta(days=interval)).isoformat(),
        last=today_str(),
        last_reviewed=today_str(),
    )


def due_count() -> int:
    today = today_str()
    return sum(1 for c in st.session_state.data.get("review_cards", [])
               if c.get("due", today) <= today)


def card_mastery(card: dict) -> str:
    """依間隔/複習次數判斷記憶強度：new / learning / young / mature。"""
    if card.get("reps", 0) == 0:
        return "new"
    interval = card.get("interval", 0)
    if interval >= 21:
        return "mature"
    if interval >= 7:
        return "young"
    return "learning"


def mastery_distribution() -> dict:
    """統計複習牌組各記憶強度的卡片數。"""
    dist = {"new": 0, "learning": 0, "young": 0, "mature": 0}
    for c in st.session_state.data.get("review_cards", []):
        dist[card_mastery(c)] = dist.get(card_mastery(c), 0) + 1
    return dist


def review_forecast(days: int = 7) -> dict:
    """回傳未來 days 天每天到期的卡片數（逾期算今天），供複習負擔預測。"""
    today = date.today()
    counts = {(today + timedelta(days=i)).strftime("%m/%d"): 0 for i in range(days)}
    keys = list(counts.keys())
    for c in st.session_state.data.get("review_cards", []):
        try:
            due = date.fromisoformat(c.get("due", today_str()))
        except ValueError:
            continue
        delta = (due - today).days
        if delta < 0:
            counts[keys[0]] += 1
        elif delta < days:
            counts[keys[delta]] += 1
    return counts


# ----------------------------- 樣式 -----------------------------
def inject_css() -> None:
    st.markdown(
        """
        <style>
        .block-container { padding-top: 2rem; max-width: 1100px; }
        .phrase-box {
            background: linear-gradient(135deg, #4f46e5, #7c3aed);
            color: #fff; padding: 22px 26px; border-radius: 16px; margin-bottom: 8px;
        }
        .phrase-box .en { font-size: 22px; font-weight: 700; line-height: 1.4;
            border-left: 4px solid rgba(255,255,255,.6); padding-left: 14px; }
        .phrase-box .zh { font-size: 16px; opacity: .92; margin-top: 10px; }
        .phrase-box .tag { display: inline-block; margin-top: 14px; background: rgba(255,255,255,.2);
            padding: 4px 12px; border-radius: 999px; font-size: 12px; }
        .flash-card {
            background: linear-gradient(135deg, #6366f1, #8b5cf6); color: #fff;
            border-radius: 16px; padding: 48px 24px; text-align: center; margin-bottom: 12px;
        }
        .flash-card.back { background: #f8fafc; color: #312e81; border: 2px solid #4f46e5; }
        .flash-card .word { font-size: 38px; font-weight: 800; }
        .flash-card .meaning { font-size: 28px; font-weight: 700; }
        .flash-card .example { font-size: 15px; opacity: .85; margin-top: 12px; font-style: italic; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ----------------------------- 各視圖 -----------------------------
def view_overview() -> None:
    data = st.session_state.data
    learned = sum(1 for w in data["words"] if w["learned"])
    streak = compute_streak()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📖 單字總數", len(data["words"]))
    c2.metric("✅ 已學會", learned)
    c3.metric("⏱️ 今日學習(分)", today_entry()["minutes"])
    c4.metric("🔥 連續天數", streak)

    st.divider()
    left, right = st.columns([3, 2])

    with left:
        st.markdown("#### 📌 每日一句")
        p = DAILY_PHRASES[data["phrase_index"] % len(DAILY_PHRASES)]
        en_js = _esc_js(p["en"])
        tts_html = (
            f'<button onclick="'
            f'const u=new SpeechSynthesisUtterance(\'{en_js}\');'
            f'u.lang=\'en-US\'; u.rate=0.92;'
            f'speechSynthesis.cancel(); speechSynthesis.speak(u);'
            f'" style="padding:8px 18px; font-size:14px; border:none; '
            f'border-radius:999px; cursor:pointer; background:rgba(255,255,255,.28); '
            f'color:#fff; font-weight:600; margin-top:12px;">🔊 唸這句</button>'
        )
        phrase_html = (
            f'<div class="phrase-box">'
            f'<div class="en">“{_html.escape(p["en"])}”</div>'
            f'<div class="zh">{_html.escape(p["zh"])}</div>'
            f'<span class="tag"># {_html.escape(p["tag"])}</span>'
            f'{tts_html}</div>'
        )
        _embed_html(phrase_html, 200)
        if st.button("換一句 🔄"):
            data["phrase_index"] = (data["phrase_index"] + 1) % len(DAILY_PHRASES)
            save_data()
            st.rerun()

        st.markdown("#### 📊 本週學習時間")
        st.bar_chart(last_7_days_df(), height=220, color="#6366f1")

    with right:
        st.markdown("#### 🎯 今日目標")
        goal = data["goal"]
        done = today_entry()["words_learned"]
        pct = min(1.0, done / goal) if goal else 0.0
        st.progress(pct, text=f"{done} / {goal} 個單字（{int(pct*100)}%）")
        new_goal = st.number_input("每日單字目標", min_value=1, max_value=100, value=goal, step=1)
        if new_goal != goal:
            data["goal"] = int(new_goal)
            save_data()
            st.rerun()

        st.markdown("#### 📝 待辦提醒")
        pending = [t for t in data["todos"] if not t["done"]]
        if pending:
            for t in pending[:5]:
                st.write(f"• {t['text']}")
        else:
            st.caption("沒有待辦任務 🎉")

    st.divider()
    st.markdown("#### 🔥 學習熱力圖（近 12 週）")
    _render_activity_heatmap()


def view_vocab() -> None:
    with st.expander("💡 這是什麼？怎麼用？", expanded=False):
        st.markdown(
            "**單字學習**＝主學習區。**單字卡**翻面+間隔複習，是記單字最有效的方法之一。\n\n"
            "**怎麼用**：\n"
            "1. 卡片正面看英文 + 諧音 + KK + 自然發音，按「🔊 唸這個字」聽發音\n"
            "2. 心裡先想中文意思，再按「🔄 翻面」對答案；背面有圖像聯想、口語例句（含翻譯+🔊）、用法、字根拆解\n"
            "3. 記得了按「✅ 標記學會」；忘了按「↩︎ 取消學會」回到複習池\n"
            "4. deck 自動合併 20 個 SEED + 「📖 單字庫」生成的字（目前合計顯示在下方計數）\n\n"
            "**清單區**＝你自己加的單字（可手動新增/刪除）；單字庫的字管理請到 📖 單字庫。"
        )
    data = st.session_state.data
    words = data["words"]

    # Deck = 使用者自管單字 ∪ vocab_bank.json 的字(以 bank 補上,使用者管理區仍在下方)
    file_bank = load_vocab_bank()
    live_bank = st.session_state.get("live_bank", {})
    synced = st.session_state.get("synced_bank", {})
    full_bank = {**file_bank, **synced, **live_bank}
    user_keys = {w["word"].lower() for w in words}
    deck = list(words) + [
        {"id": f"bank:{k}", "word": k,
         "meaning": e.get("meaning_zh", ""),
         "example": e.get("example_en", ""),
         "learned": False}
        for k, e in full_bank.items() if k.lower() not in user_keys
    ]

    st.markdown("### 🃏 單字卡")
    if not deck:
        st.info("目前沒有單字，請到下方新增，或到「📖 單字庫」生成。")
    else:
        # 把 fc_index 從 session_state 改放到 data 內(寫到 dashboard_data.json 持久化,
        # 重開瀏覽器/重新整理會接續上次的位置,不會每次從頭開始)
        data.setdefault("fc_index", 0)
        data["fc_index"] %= len(deck)
        idx = data["fc_index"]
        st.session_state.fc_index = idx  # 同步 session 給其他地方用
        w = deck[idx]
        is_bank_only = isinstance(w["id"], str) and w["id"].startswith("bank:")
        # 學會數計算(只算使用者區的字)
        learned_n = sum(1 for ww in words if ww.get("learned"))
        st.caption(
            f"📍 {idx + 1} / {len(deck)}"
            + (f"　·　共 {len(full_bank)} 字來自單字庫" if full_bank else "")
            + f"　·　已學會 {learned_n} / {len(words)}"
        )
        mn = MNEMONICS.get(w["word"]) or full_bank.get(w["word"])
        render_flashcard(w, mn, st.session_state.fc_flipped)
        # 每個單字都畫字首/字根/字尾心智圖(無詞素時退化為純字幹)
        decomp = decompose_word(w["word"])
        if decomp:
            st.caption("🧩 字首／字根／字尾拆解")
            branches = sum(1 for k in ("prefix", "root", "suffix") if decomp.get(k))
            h = 200 if branches <= 1 else (260 if branches == 2 else 320)
            render_mermaid(build_word_mindmap(w["word"], decomp), height=h)

        b1, b2, b3, b4, b5 = st.columns(5)
        if b1.button("← 上一個", use_container_width=True):
            data["fc_index"] = (idx - 1) % len(deck)
            st.session_state.fc_flipped = False
            save_data()
            st.rerun()
        if b2.button("🔄 翻面", use_container_width=True):
            st.session_state.fc_flipped = not st.session_state.fc_flipped
            st.rerun()
        learn_label = ("（單字庫專用）" if is_bank_only
                       else ("↩︎ 取消學會" if w["learned"] else "✅ 標記學會"))
        if b3.button(learn_label, use_container_width=True, disabled=is_bank_only):
            toggle_learned(w["id"])
            st.rerun()
        if b4.button("🎲 隨機", use_container_width=True,
                     help="隨機跳到任一張，避免每次從頭看相同的字"):
            import random
            data["fc_index"] = random.randrange(len(deck))
            st.session_state.fc_flipped = False
            save_data()
            st.rerun()
        if b5.button("下一個 →", use_container_width=True):
            data["fc_index"] = (idx + 1) % len(deck)
            st.session_state.fc_flipped = False
            save_data()
            st.rerun()

    st.divider()
    with st.expander("🤯 SEED 單字諧音速記（20 字一覽）"):
        st.caption("把英文聲音強行接到中文意思的搞笑諧音 + 圖像聯想。翻面卡背也看得到。")
        for word, mn in MNEMONICS.items():
            with st.container(border=True):
                c1, c2 = st.columns([2, 5])
                c1.markdown(f"### {word}")
                c1.caption(f"KK `{mn['kk']}`")
                c1.caption(f"自然發音 `{mn['phonics']}`")
                c2.markdown(f"🔊 諧音 **{mn['homophone']}**")
                c2.markdown(f"🖼️ {mn['image']}")

    st.divider()
    st.markdown("### 📚 單字清單")
    with st.expander("➕ 新增單字"):
        with st.form("add_word", clear_on_submit=True):
            nw = st.text_input("英文單字")
            nm = st.text_input("中文意思")
            ne = st.text_input("例句（選填）")
            if st.form_submit_button("儲存", type="primary"):
                if nw.strip() and nm.strip():
                    new_id = max((w["id"] for w in words), default=0) + 1
                    words.append({"id": new_id, "word": nw.strip(),
                                  "meaning": nm.strip(), "example": ne.strip(), "learned": False})
                    save_data()
                    st.success(f"已新增「{nw.strip()}」")
                    st.rerun()
                else:
                    st.warning("單字與意思為必填。")

    if not words:
        st.caption("尚未有任何單字。")
        return

    for w in words:
        col = st.columns([3, 4, 2, 1.4, 1])
        col[0].markdown(f"**{w['word']}**")
        col[1].write(w["meaning"])
        col[2].markdown("✅ 已學會" if w["learned"] else "🕘 學習中")
        if col[3].button("切換", key=f"tg_{w['id']}", use_container_width=True):
            toggle_learned(w["id"])
            st.rerun()
        if col[4].button("🗑️", key=f"del_{w['id']}", use_container_width=True):
            data["words"] = [x for x in words if x["id"] != w["id"]]
            save_data()
            st.rerun()


def toggle_learned(word_id: int) -> None:
    for w in st.session_state.data["words"]:
        if w["id"] == word_id:
            w["learned"] = not w["learned"]
            if w["learned"]:
                today_entry()["words_learned"] += 1
            else:
                today_entry()["words_learned"] = max(0, today_entry()["words_learned"] - 1)
            save_data()
            return


def view_quiz() -> None:
    data = st.session_state.data
    words = data["words"]

    if len(words) < 4:
        st.info("至少需要 4 個單字才能開始測驗。")
        return

    quiz = st.session_state.get("quiz")
    if quiz is None:
        st.write("從你的單字庫隨機出題，選出正確的中文意思。")
        if st.button("開始測驗", type="primary"):
            start_quiz()
            st.rerun()
        return

    if quiz["finished"]:
        total = len(quiz["questions"])
        score = round(quiz["correct"] / total * 100)
        st.success("測驗完成！🎉")
        st.metric("得分", f"{quiz['correct']} / {total}（{score} 分）")
        if st.button("再測一次", type="primary"):
            start_quiz()
            st.rerun()
        return

    q = quiz["questions"][quiz["idx"]]
    st.caption(f"第 {quiz['idx'] + 1} / {len(quiz['questions'])} 題")
    st.subheader(q["word"])

    if not quiz["answered"]:
        for i, opt in enumerate(q["options"]):
            if st.button(opt, key=f"q{quiz['idx']}_o{i}", use_container_width=True):
                quiz["answered"] = True
                quiz["selected"] = opt
                if opt == q["answer"]:
                    quiz["correct"] += 1
                st.rerun()
    else:
        for opt in q["options"]:
            if opt == q["answer"]:
                st.success(f"✅ {opt}")
            elif opt == quiz["selected"]:
                st.error(f"❌ {opt}")
            else:
                st.write(f"　{opt}")

        is_last = quiz["idx"] == len(quiz["questions"]) - 1
        if st.button("看結果 →" if is_last else "下一題 →", type="primary"):
            if is_last:
                total = len(quiz["questions"])
                today_entry()["quiz_scores"].append(round(quiz["correct"] / total * 100))
                save_data()
                quiz["finished"] = True
            else:
                quiz["idx"] += 1
                quiz["answered"] = False
                quiz["selected"] = None
            st.rerun()


def start_quiz() -> None:
    words = st.session_state.data["words"]
    pool = random.sample(words, len(words))[: min(10, len(words))]
    questions = []
    for q in pool:
        others = [w for w in words if w["id"] != q["id"]]
        distractors = random.sample(others, min(3, len(others)))
        options = [o["meaning"] for o in distractors] + [q["meaning"]]
        random.shuffle(options)
        questions.append({"word": q["word"], "answer": q["meaning"], "options": options})
    st.session_state.quiz = {"questions": questions, "idx": 0, "correct": 0,
                             "answered": False, "selected": None, "finished": False}


def view_progress() -> None:
    data = st.session_state.data
    days = [k for k in data["daily"] if has_activity(k)]
    total_minutes = sum(e["minutes"] for e in data["daily"].values())
    all_scores = [s for e in data["daily"].values() for s in e["quiz_scores"]]
    avg_score = round(sum(all_scores) / len(all_scores)) if all_scores else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📅 累計學習天數", len(days))
    c2.metric("⏱️ 累計學習(分)", total_minutes)
    c3.metric("🏆 最佳連續天數", data.get("best_streak", 0))
    c4.metric("🎯 平均測驗分數", f"{avg_score}%")

    st.divider()
    st.markdown("#### 📈 近 7 天學習時間")
    st.bar_chart(last_7_days_df(), height=260, color="#6366f1")

    st.divider()
    st.markdown("#### 🔥 學習熱力圖（近 12 週）")
    _render_activity_heatmap()

    with st.expander("⏱️ 記錄今日學習時間"):
        mins = st.number_input("學習時間（分鐘）", min_value=1, max_value=600, value=15, step=5)
        if st.button("儲存時間", type="primary"):
            today_entry()["minutes"] += int(mins)
            save_data()
            st.success(f"已記錄 {int(mins)} 分鐘")
            st.rerun()

    st.markdown("#### 🧩 單字掌握度")
    learned = sum(1 for w in data["words"] if w["learned"])
    pct = learned / len(data["words"]) if data["words"] else 0
    st.progress(pct, text=f"{learned} / {len(data['words'])} 已掌握（{int(pct*100)}%）")

    # ---------------- 🧠 記憶科學監督（SRS 分析）----------------
    st.divider()
    st.markdown("#### 🧠 記憶科學監督（間隔重複 SRS）")
    cards = data.get("review_cards", [])
    if not cards:
        st.info("複習牌組是空的。到「📚 互動閱讀」或「🤖 情境生成」把句卡加入複習，"
                "系統就會用間隔重複幫你科學排程、追蹤記憶強度。")
        return

    dist = mastery_distribution()
    total = len(cards)
    mature_pct = (dist["young"] + dist["mature"]) / total if total else 0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🃏 複習卡總數", total)
    c2.metric("📅 今日待複習", due_count())
    c3.metric("🌳 已熟（young+mature）", dist["young"] + dist["mature"])
    c4.metric("💪 熟練比例", f"{int(mature_pct * 100)}%")

    st.markdown("##### 🎯 記憶強度分布")
    labels = {"new": "🆕 新卡", "learning": "📖 學習中（<7天）",
              "young": "🌱 漸熟（7–20天）", "mature": "🌳 已掌握（≥21天）"}
    mc = st.columns(4)
    for col, k in zip(mc, ["new", "learning", "young", "mature"]):
        col.metric(labels[k], dist.get(k, 0))

    st.markdown("##### 📈 未來 7 天複習負擔預測")
    st.caption("提早知道哪天卡片會堆積，方便調配每天學習時間。")
    st.bar_chart(review_forecast(7), height=240, color="#10b981")


def view_plan() -> None:
    data = st.session_state.data
    st.markdown("### ✅ 學習待辦清單")
    with st.form("add_todo", clear_on_submit=True):
        col = st.columns([5, 1])
        text = col[0].text_input("新增任務", label_visibility="collapsed",
                                 placeholder="例如：背 20 個 TOEIC 單字")
        if col[1].form_submit_button("新增", type="primary", use_container_width=True):
            if text.strip():
                new_id = max((t["id"] for t in data["todos"]), default=0) + 1
                data["todos"].append({"id": new_id, "text": text.strip(), "done": False})
                save_data()
                st.rerun()

    if not data["todos"]:
        st.caption("還沒有待辦任務。")
    for t in data["todos"]:
        col = st.columns([0.6, 8, 1])
        checked = col[0].checkbox("完成", value=t["done"], key=f"todo_{t['id']}",
                                  label_visibility="collapsed")
        if checked != t["done"]:
            t["done"] = checked
            save_data()
            st.rerun()
        col[1].markdown(f"~~{t['text']}~~" if t["done"] else t["text"])
        if col[2].button("🗑️", key=f"todo_del_{t['id']}", use_container_width=True):
            data["todos"] = [x for x in data["todos"] if x["id"] != t["id"]]
            save_data()
            st.rerun()

    st.divider()
    st.markdown("### 🗓️ 每週學習計畫")
    cols = st.columns(7)
    for i, p in enumerate(data["weekly_plan"]):
        with cols[i]:
            st.markdown(f"**{p['day']}**")
            st.caption(p["task"])
            label = "✓ 完成" if p["done"] else "標記"
            if st.button(label, key=f"plan_{p['id']}", use_container_width=True):
                p["done"] = not p["done"]
                save_data()
                st.rerun()


def view_generate() -> None:
    data = st.session_state.data
    with st.expander("💡 這是什麼？怎麼用？", expanded=False):
        st.markdown(
            "**情境生成**＝把你想練的「真實場景」一鍵變成可學的內容。\n\n"
            "**怎麼用**：\n"
            "1. 輸入一個生活情境，例如：\n"
            "   - 在咖啡廳跟店員點餐，並反映飲料做錯了\n"
            "   - 面試自我介紹 + 回答「你的缺點」\n"
            "   - 跟外國朋友抱怨工作壓力\n"
            "   - 訂飯店 / 退換貨 / 機場海關問答\n"
            "2. 按「生成 ✨」，Gemini 會產出：\n"
            "   - 一張**對話心智圖**（流程：開口→反映→請求→確認）\n"
            "   - **5–8 張句卡**：英文 + 中文翻譯 + 詞塊 + KK + 自然發音 + 台味諧音\n"
            "3. 喜歡的句卡按「加入複習」→ 之後在「🔁 複習」分頁 SRS 排程練習\n\n"
            "**模型差別**：Flash 快又便宜（推薦），Pro 慢但句子更精緻。"
        )

    if not get_api_key():
        st.warning("尚未設定 Gemini API 金鑰，無法生成。")
        st.markdown(
            "- **Streamlit Cloud**：到 **Settings → Secrets** 加入：\n"
            "  ```\n  GEMINI_API_KEY = \"你的_key\"\n  ```\n"
            "- **本機**：`export GEMINI_API_KEY=你的_key`\n"
            "- 取得方式：https://aistudio.google.com/apikey"
        )
    else:
        st.caption("供應商：**Google Gemini**")
        rand_clicked = st.button("🎲 隨機生成情境", type="primary",
                                 use_container_width=True, key="gen_rand")
        with st.form("gen_form", clear_on_submit=False):
            scenario = st.text_input(
                "目標情境（自己指定）",
                placeholder="例如：在咖啡廳跟店員點餐，並反映飲料做錯了",
            )
            model_label = st.selectbox("生成模型", GEN_MODEL_TIERS)
            submitted = st.form_submit_button("生成 ✨", type="primary")

        target, tier = None, next(iter(GEN_MODEL_TIERS))
        if rand_clicked:
            target = random.choice(_DIALOGUE_TOPICS)
        elif submitted:
            if scenario.strip():
                target, tier = scenario.strip(), model_label
            else:
                st.warning("請先輸入情境，或直接按上方「🎲 隨機生成情境」。")
        if target:
            with st.spinner(f"AI 生成「{target}」中…"):
                try:
                    raw = generate_material(target, tier)
                    mermaid, cards = parse_blocks(raw)
                    st.session_state.gen_result = {
                        "scenario": target,
                        "mermaid": mermaid,
                        "flashcards": cards or [],
                        "raw": raw,
                    }
                except Exception as e:  # noqa: BLE001
                    st.session_state.gen_result = None
                    st.error(_friendly_gen_error(f"{type(e).__name__}: {e}"))

    result = st.session_state.get("gen_result")
    if result:
        st.divider()
        st.markdown(f"#### 📍 情境：{result['scenario']}")
        if result["mermaid"]:
            render_mermaid(result["mermaid"])
            st.caption("↑ 若上方畫面顯示「Syntax error in text」💣，代表 Gemini 違反 flowchart 語法；"
                       "可展開下方原始碼回報給開發者，或重新按「生成 ✨」(Gemini 偶有發揮)。")
            with st.expander("🔍 檢視 Mermaid 原始碼 / Gemini 完整回應"):
                st.markdown("**Mermaid 清潔後**:")
                st.code(result["mermaid"], language="text")
                st.markdown("**Gemini 完整原始輸出**:")
                st.code(result.get("raw", ""), language="text")
        else:
            st.info("未能解析出心智圖。")
            with st.expander("檢視 Gemini 原始回應"):
                st.code(result.get("raw", ""), language="text")

        if result["flashcards"]:
            st.markdown("#### 🃏 句卡")
            render_flashcards(result["flashcards"])
        else:
            st.info("未能解析出句卡，可展開下方原始回應檢查。")
            with st.expander("原始回應"):
                st.code(result["raw"], language="text")

        c1, c2, c3 = st.columns(3)
        if c1.button("💾 儲存這課", type="primary", use_container_width=True):
            new_id = max((l["id"] for l in data["lessons"]), default=0) + 1
            lesson = {
                "id": new_id,
                "scenario": result["scenario"],
                "mermaid": result["mermaid"],
                "flashcards": result["flashcards"],
                "created": today_str(),
            }
            data["lessons"].append(lesson)
            save_data()
            try:
                _persist_lesson(lesson)  # 推進永久庫，跨裝置/重整都在、持續長大
            except Exception:  # noqa: BLE001
                pass
            st.session_state.gen_result = None
            st.success("已儲存（並存進永久課程庫）。")
            st.rerun()
        if c2.button("➕ 加入複習", use_container_width=True,
                     disabled=not result["flashcards"]):
            n = add_cards_to_review(result["flashcards"])
            save_data()
            st.success(f"已加入 {n} 張到複習清單。" if n else "這些句卡已在複習清單中。")
        if c3.button("🗑️ 清除結果", use_container_width=True):
            st.session_state.gen_result = None
            st.rerun()

    # 顯示：本機課程 + 永久庫課程（去重，永久庫累積長大）
    seen_keys = {(l.get("scenario"), l.get("created")) for l in data["lessons"]}
    all_lessons = list(data["lessons"]) + [
        l for l in load_lessons_bank()
        if (l.get("scenario"), l.get("created")) not in seen_keys]
    if all_lessons:
        st.divider()
        st.markdown(f"### 📂 已儲存的情境課程（共 {len(all_lessons)} 課，永久累積）")
        for li, lesson in enumerate(reversed(all_lessons)):
            with st.expander(f"📍 {lesson['scenario']}（{lesson.get('created', '')}）"):
                if lesson.get("mermaid"):
                    render_mermaid(lesson["mermaid"])
                if lesson.get("flashcards"):
                    render_flashcards(lesson["flashcards"])
                if st.button("➕ 加入複習", key=f"lesson_rev_{li}",
                             use_container_width=True,
                             disabled=not lesson.get("flashcards")):
                    n = add_cards_to_review(lesson["flashcards"])
                    save_data()
                    st.success(f"已加入 {n} 張。" if n else "已在複習清單中。")


def view_review() -> None:
    data = st.session_state.data
    deck = data.setdefault("review_cards", [])
    # 每日複習上限(避免一次過量導致疲乏);可在下方 expander 調整,持久化到 data
    data.setdefault("review_daily_cap", 20)

    if not deck:
        st.info("複習清單是空的。可從「📖 單字庫」把單字、或「📚 互動閱讀」「🤖 情境生成」"
                "把句卡加入複習，系統會用間隔重複（SRS）幫你科學排程。")
        return

    today = today_str()
    due = [c for c in deck if c.get("due", today) <= today]

    # 計算今日已複習張數(用 last_reviewed == today 判斷)
    reviewed_today = sum(1 for c in deck if c.get("last_reviewed") == today)
    cap = int(data.get("review_daily_cap", 20))
    remaining = max(0, cap - reviewed_today)

    st.caption(
        f"清單共 {len(deck)} 張　·　今日到期 {len(due)} 張　·　"
        f"今日已複習 {reviewed_today}/{cap} 張(剩 {remaining})"
    )

    with st.expander("⚙️ 每日複習上限"):
        new_cap = st.slider("每日上限(超過會顯示「今日達標」)",
                            min_value=5, max_value=200,
                            value=cap, step=5, key="review_cap_slider")
        if new_cap != cap:
            data["review_daily_cap"] = int(new_cap)
            save_data()
            st.rerun()

    if not due:
        nxt = min((c.get("due", today) for c in deck), default=today)
        st.success(f"今天沒有要複習的卡 🎉 下次到期:{nxt}")
        with st.expander("清空複習清單"):
            if st.button("確認清空", type="primary"):
                data["review_cards"] = []
                save_data()
                st.rerun()
        return

    if remaining <= 0:
        st.success(f"🎯 今日已達 {cap} 張上限,別累壞了!"
                   f"還有 {len(due)} 張到期卡,明天繼續。")
        return

    card = due[0]
    st.progress((len(deck) - len(due)) / len(deck), text=f"剩 {len(due)} 張待複習")
    st.markdown(f"## {card.get('sentence', '')}")

    if st.session_state.get("review_reveal_id") != card["id"]:
        if st.button("🔄 翻面看答案", type="primary", use_container_width=True):
            st.session_state.review_reveal_id = card["id"]
            st.rerun()
        return

    render_flashcards([card])
    g1, g2, g3 = st.columns(3)
    graded = None
    if g1.button("😵 忘記", use_container_width=True):
        graded = "again"
    if g2.button("🙂 普通", use_container_width=True):
        graded = "good"
    if g3.button("😎 簡單", use_container_width=True):
        graded = "easy"
    if graded:
        schedule_card(card, graded)
        save_data()
        st.session_state.pop("review_reveal_id", None)
        st.rerun()


def view_morphology() -> None:
    with st.expander("💡 這是什麼？怎麼用？", expanded=False):
        st.markdown(
            "**字根速記**＝看到沒學過的字也能猜意思。英文 70% 單字可拆成「字首 + 字根 + 字尾」，"
            "記住元件就能組合理解新字。\n\n"
            "**例子**：\n"
            "- `inspect` ＝ `in-`（進入）+ `spect`（看）→ 進去看 → **檢查**\n"
            "- `transport` ＝ `trans-`（跨越）+ `port`（搬運）→ 跨越搬運 → **運輸**\n"
            "- `unhappy` ＝ `un-`（不）+ `happy`（快樂）→ **不快樂**\n\n"
            "**怎麼用**：點下方 3 個分頁分別看 25 個字首 / 24 個字根 / 24 個字尾。"
            "想專注少數可用「挑選想看」filter，例如只挑 `anti-` 與 `pre-`，就只渲染這兩棵分支。"
            "翻面卡背也會自動拆解當下單字。"
        )
    st.caption("離線字根字首字尾樹狀圖 + SEED 單字台味諧音速記，完全不需 API。")

    # AI 額外例字 + 新 morpheme:從檔案 + session 合併,生成後寫檔(永久保存)
    file_morph = load_morph_examples()
    sess = st.session_state.setdefault("live_morph_ex",
                                        {"pre": {}, "root": {}, "suf": {},
                                         "new_pre": [], "new_root": [], "new_suf": []})
    # 確保 6 個 key 都存在(向後相容舊 session)
    for k in ("new_pre", "new_root", "new_suf"):
        sess.setdefault(k, [])
    live = {}
    for k in ("pre", "root", "suf"):
        merged_k = {}
        for src in (file_morph.get(k, {}), sess.get(k, {})):
            for m_key, words in src.items():
                bucket = merged_k.setdefault(m_key, [])
                for w in words:
                    if w not in bucket:
                        bucket.append(w)
        live[k] = merged_k
    # 新 morpheme:合併檔案 + session,以 m 為 key 去重(檔案優先)
    for k in ("new_pre", "new_root", "new_suf"):
        seen_m = set()
        merged_list = []
        for it in list(file_morph.get(k, [])) + list(sess.get(k, [])):
            if isinstance(it, dict) and it.get("m") and it["m"] not in seen_m:
                seen_m.add(it["m"])
                merged_list.append(it)
        live[k] = merged_list

    tab1, tab2, tab3 = st.tabs(["字首 Prefix", "字中 Root", "字尾 Suffix"])
    for tab, title, items_base, key, cat_zh in (
        (tab1, "字首 Prefix", PREFIXES, "pre", "字首"),
        (tab2, "字中 Root", ROOTS, "root", "字根"),
        (tab3, "字尾 Suffix", SUFFIXES, "suf", "字尾"),
    ):
        with tab:
            # 包含 AI 新增的 morphemes
            new_items = live[f"new_{key}"]
            items = list(items_base) + new_items
            options = [f"{it['m']} · {it['zh']}" for it in items]
            picked = st.multiselect(
                f"挑選想看的（不選 = 全部 {len(items)} 個,含 AI 新增 {len(new_items)}）",
                options,
                key=f"morph_pick_{key}",
                placeholder="例如：anti-, pre-, dis-",
            )
            shown_base = ([it for it in items
                          if f"{it['m']} · {it['zh']}" in set(picked)]
                          if picked else items)
            # 把 session 累積的 AI 額外例字併進顯示用 list (不動原 PREFIXES/ROOTS/SUFFIXES)
            shown = []
            for it in shown_base:
                extra = live[key].get(it["m"], [])
                merged_ex = list(it["ex"]) + [e for e in extra if e not in it["ex"]]
                shown.append({**it, "ex": merged_ex})
            render_mermaid(build_mindmap(title, shown),
                           height=520 if len(shown) >= 5 else 360)

            # 🎲 AI 隨機加例字(挑了 1-3 個目標才有意義,避免一次塞太多)
            if picked and 1 <= len(picked) <= 3 and get_api_key():
                with st.expander(f"🎲 用 AI 給已選 {len(picked)} 個{cat_zh}各補例字"):
                    n_per = st.number_input(
                        "每個額外補幾個字", min_value=1, max_value=8, value=3,
                        step=1, key=f"morph_n_{key}",
                    )
                    if st.button(f"🚀 開始生成（不重複現有）",
                                 key=f"morph_gen_{key}", type="primary"):
                        try:
                            total_added = 0
                            with st.spinner("Gemini 生成中..."):
                                for it in shown_base:
                                    existing = (list(it["ex"]) +
                                                live[key].get(it["m"], []))
                                    fresh = _gen_morph_examples(
                                        cat_zh, it["m"], it["zh"],
                                        existing, int(n_per))
                                    if fresh:
                                        sess[key].setdefault(it["m"], []).extend(fresh)
                                        live[key].setdefault(it["m"], []).extend(fresh)
                                        total_added += len(fresh)
                            # 寫本機檔(下次重新整理仍在)
                            saved = save_morph_examples(live)
                            msg = f"✅ 新例字 +{total_added} 已加入心智圖"
                            msg += "(已寫入 morph_examples_bank.json)" if saved else "(本機寫檔失敗,僅在 session)"
                            st.success(msg)
                            # 有 GITHUB_TOKEN 自動推回 repo,永久保存
                            if get_github_token():
                                _push_file_to_github(
                                    MORPH_EXAMPLES_FILE, "morph_examples_bank.json",
                                    f"morph_examples: +{total_added} via 字根速記 AI",
                                )
                            st.rerun()
                        except Exception as e:  # noqa: BLE001
                            st.error(f"生成失敗:{type(e).__name__}: {str(e)[:200]}")
            elif picked and len(picked) > 3:
                st.caption("挑 1-3 個目標再用 AI 加例字（一次太多會稀釋學習）")
            elif picked and not get_api_key():
                st.caption("設好 Gemini key 後,選 1-3 個目標就可用 AI 補例字。")

            # 🆕 用 AI 補全新 morpheme(本分類目前沒有的)
            if get_api_key():
                with st.expander(f"🆕 用 AI 補全新{cat_zh}條目(不重複既有)"):
                    n_new = st.number_input(
                        f"一次補幾個新{cat_zh}", min_value=1, max_value=10, value=3,
                        step=1, key=f"morph_newn_{key}",
                    )
                    if st.button(f"🆕 生成新{cat_zh}",
                                 key=f"morph_newgen_{key}", type="primary"):
                        try:
                            existing_m = [it["m"] for it in items_base] + [
                                it["m"] for it in new_items]
                            with st.spinner(f"Gemini 補新{cat_zh}…"):
                                fresh = _gen_new_morphemes(
                                    cat_zh, existing_m, int(n_new))
                            if not fresh:
                                st.warning("Gemini 沒回任何新條目,可能本分類已涵蓋大部分常見項。")
                            else:
                                sess[f"new_{key}"].extend(fresh)
                                # 寫回檔案
                                live_for_save = {**live,
                                                 f"new_{key}": list(live[f"new_{key}"]) + fresh}
                                save_morph_examples(live_for_save)
                                # 有 token 自動推回
                                if get_github_token():
                                    _push_file_to_github(
                                        MORPH_EXAMPLES_FILE,
                                        "morph_examples_bank.json",
                                        f"morph_examples: +{len(fresh)} 新{cat_zh}",
                                    )
                                st.success(f"✅ 新增 {len(fresh)} 個新{cat_zh}: "
                                           + ", ".join(f["m"] for f in fresh))
                                st.rerun()
                        except Exception as e:  # noqa: BLE001
                            st.error(f"生成失敗:{type(e).__name__}: {str(e)[:200]}")

            with st.expander("檢視清單（點任一例字唸給你聽）"):
                # 把例字渲染成 chip,可點唸(Web Speech API)
                rows = []
                for it in items:
                    is_new = it in new_items
                    tag = "🆕 " if is_new else ""
                    chips = []
                    for ex in it["ex"]:
                        en_js = _esc_js(ex)
                        chips.append(
                            f'<button onclick="'
                            f'const u=new SpeechSynthesisUtterance(\'{en_js}\');'
                            f'u.lang=\'en-US\'; u.rate=0.95;'
                            f'speechSynthesis.cancel(); speechSynthesis.speak(u);'
                            f'" style="margin:2px; padding:3px 10px; font-size:13px; '
                            f'border:1px solid #b45309; border-radius:999px; '
                            f'background:#fef3c7; color:#7c2d12; cursor:pointer;">'
                            f'🔊 {_html.escape(ex)}</button>'
                        )
                    rows.append(
                        f'<div style="margin:8px 0; padding:6px 10px; background:#f8fafc; '
                        f'border-radius:6px;">'
                        f'<span style="font-weight:600; color:#4f46e5;">'
                        f'{tag}{_html.escape(it["m"])}</span>'
                        f'<span style="color:#64748b; font-size:13px;">'
                        f'　({_html.escape(it["zh"])})</span><br>'
                        f'{"".join(chips)}</div>'
                    )
                _embed_html(
                    '<div style="font-family:-apple-system,sans-serif;">'
                    + "".join(rows) + "</div>",
                    height=80 + 60 * len(items),
                )

    # 🔀 一鍵把累積的 AI 例字 + 新 morpheme 回流進 morphology.py 預設清單
    file_morph = load_morph_examples()
    pending_ex = sum(len(v) for k in ("pre", "root", "suf")
                     for v in file_morph.get(k, {}).values())
    pending_new = sum(len(file_morph.get(k, []))
                      for k in ("new_pre", "new_root", "new_suf"))
    pending_count = pending_ex + pending_new
    if pending_count > 0:
        st.divider()
        st.markdown(f"#### 🔀 把累積的 **{pending_count}** 個 AI 例字回流進 morphology.py 預設清單")
        st.caption("把 morph_examples_bank.json 內所有字合進 PREFIXES/ROOTS/SUFFIXES 的 `ex` 預設,"
                   "完成後 bank 清空。有 GITHUB_TOKEN 會自動推 morphology.py + 清空後的 bank 到 repo,永久內建。")
        col_dry, col_go = st.columns([1, 1])
        if col_dry.button("👀 預覽(不寫檔)", use_container_width=True,
                          key="morph_merge_dry"):
            res = _merge_morph_examples(dry_run=True)
            st.code("\n".join(res["report"]), language="text")
        if col_go.button("🚀 執行合併(寫檔 + 自動推回)",
                         type="primary", use_container_width=True,
                         key="morph_merge_go"):
            try:
                res = _merge_morph_examples(dry_run=False, clear_bank=True)
                st.success(f"✅ 合併完成,共加 {res['total']} 字到 morphology.py。"
                           "請強制重新整理瀏覽器,新例字就會出現在預設清單。")
                # 自動推 morphology.py + 清空後的 morph_examples_bank.json
                if get_github_token():
                    _push_file_to_github(
                        os.path.join(os.path.dirname(os.path.abspath(__file__)), "morphology.py"),
                        "morphology.py",
                        f"morphology: 回流 +{res['total']} AI 例字到預設清單",
                    )
                    _push_file_to_github(
                        MORPH_EXAMPLES_FILE, "morph_examples_bank.json",
                        "morph_examples_bank: 回流後清空",
                    )
                if res["unmatched"]:
                    st.warning(f"以下 morpheme 在 morphology.py 內找不到對應,未合(已留在 bank):"
                               f"\n```\n{res['unmatched']}\n```")
                st.rerun()
            except Exception as e:  # noqa: BLE001
                st.error(f"合併失敗:{type(e).__name__}: {str(e)[:300]}")


def _merge_morph_examples(dry_run: bool = False, clear_bank: bool = False) -> dict:
    """從 morph_examples_bank.json 回流字到 morphology.py。
    dry_run=True 不寫檔,只回報告。回 {total, report, unmatched}。"""
    import subprocess
    morph_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "morphology.py")
    bank_path = MORPH_EXAMPLES_FILE
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "scripts", "merge_morph_examples.py")
    cmd = [sys.executable, script]
    if dry_run:
        cmd.append("--dry-run")
    if clear_bank:
        cmd.append("--clear-bank")
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    out = proc.stdout + proc.stderr
    # 從輸出抽 "合計新增:N 字" 與 "未匹配 m:[...]"
    m_total = re.search(r"合計新增:\s*(\d+)", out)
    total = int(m_total.group(1)) if m_total else 0
    unmatched = re.findall(r"未匹配 m: \[([^\]]+)\]", out)
    # 清掉 morphology cache(本 process 內後續 import 才看得到新版)
    if not dry_run:
        load_morph_examples.clear() if hasattr(load_morph_examples, "clear") else None
    return {"total": total, "report": out.splitlines(), "unmatched": ", ".join(unmatched)}


@st.cache_data
def _load_vocab_bank_cached(_mtime: float) -> dict:
    """讀取 + 自動清理:把 key 正規化為小寫,大小寫撞 key 只保留第一筆,
    丟掉缺 meaning_zh 的不完整 entry(Gemini 生成失敗的殘留)。"""
    try:
        with open(VOCAB_BANK_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    cleaned = {}
    for k, v in (raw or {}).items():
        lk = (k or "").strip().lower()
        if not lk:
            continue
        if lk in cleaned:  # 大小寫去重,先到的保留
            continue
        if not isinstance(v, dict) or not v.get("meaning_zh"):
            continue
        v["word"] = lk  # 同步 word 欄位為正規化的 key
        cleaned[lk] = v
    return cleaned


def load_vocab_bank() -> dict:
    """讀取 vocab_bank.json;以檔案 mtime 當 cache key,檔案變動會自動失效。"""
    try:
        mtime = os.path.getmtime(VOCAB_BANK_FILE)
    except OSError:
        mtime = 0.0
    return _load_vocab_bank_cached(mtime)


# ---------------------------------------------------------------------------
# 字根速記 AI 補的例字永久庫(寫本機 + 可選自動推 GitHub)
# 結構:{"pre": {"un-": ["unread", ...]}, "root": {"spect": [...]}, "suf": {"-ly": [...]}}
# ---------------------------------------------------------------------------
@st.cache_data
def _load_morph_examples_cached(_mtime: float) -> dict:
    """讀 morph_examples_bank.json。結構含 6 key:
       前 3 (pre/root/suf) = 給已知 morpheme 加 ex;
       後 3 (new_pre/new_root/new_suf) = 全新 morpheme 條目陣列。"""
    default = {"pre": {}, "root": {}, "suf": {},
               "new_pre": [], "new_root": [], "new_suf": []}
    try:
        with open(MORPH_EXAMPLES_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        if not isinstance(d, dict):
            return default
        out = {**default}
        for k in ("pre", "root", "suf"):
            if isinstance(d.get(k), dict):
                out[k] = dict(d[k])
        for k in ("new_pre", "new_root", "new_suf"):
            if isinstance(d.get(k), list):
                out[k] = [x for x in d[k]
                          if isinstance(x, dict) and x.get("m") and x.get("zh")]
        return out
    except (OSError, json.JSONDecodeError):
        return default


def load_morph_examples() -> dict:
    try:
        mtime = os.path.getmtime(MORPH_EXAMPLES_FILE)
    except OSError:
        mtime = 0.0
    return _load_morph_examples_cached(mtime)


def save_morph_examples(d: dict) -> bool:
    try:
        with open(MORPH_EXAMPLES_FILE, "w", encoding="utf-8") as f:
            json.dump({"pre": d.get("pre", {}),
                       "root": d.get("root", {}),
                       "suf": d.get("suf", {}),
                       "new_pre": d.get("new_pre", []),
                       "new_root": d.get("new_root", []),
                       "new_suf": d.get("new_suf", [])},
                      f, ensure_ascii=False, indent=2)
            f.write("\n")
        load_morph_examples.clear() if hasattr(load_morph_examples, "clear") else None
        return True
    except OSError:
        return False


# ---------------------------------------------------------------------------
# 閱讀永久庫（AI 生成 → 寫本機 + 推回 GitHub，資料庫越長越大）
# ---------------------------------------------------------------------------
@st.cache_data
def _load_readings_bank_cached(_mtime: float) -> list:
    try:
        with open(READINGS_BANK_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def load_readings_bank() -> list:
    """讀取 readings_bank.json（AI 生成且已永久保存的閱讀清單）。"""
    try:
        mtime = os.path.getmtime(READINGS_BANK_FILE)
    except OSError:
        mtime = 0.0
    return _load_readings_bank_cached(mtime)


@st.cache_data
def _load_grammar_bank_cached(_mtime: float) -> list:
    try:
        with open(GRAMMAR_BANK_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def load_grammar_bank() -> list:
    """讀取 grammar_bank.json（AI 生成的文法清單，含 level 欄位）。"""
    try:
        mtime = os.path.getmtime(GRAMMAR_BANK_FILE)
    except OSError:
        mtime = 0.0
    return _load_grammar_bank_cached(mtime)


@st.cache_data
def _load_lessons_bank_cached(_mtime: float) -> list:
    try:
        with open(LESSONS_BANK_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def load_lessons_bank() -> list:
    """讀取 lessons_bank.json（AI 生成的情境課程，永久累積）。"""
    try:
        mtime = os.path.getmtime(LESSONS_BANK_FILE)
    except OSError:
        mtime = 0.0
    return _load_lessons_bank_cached(mtime)


@st.cache_data
def _load_dialogues_bank_cached(_mtime: float) -> list:
    try:
        with open(DIALOGUES_BANK_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def load_dialogues_bank() -> list:
    """讀取 dialogues_bank.json（AI 生成的情境對話，加進口說範本、永久累積）。"""
    try:
        mtime = os.path.getmtime(DIALOGUES_BANK_FILE)
    except OSError:
        mtime = 0.0
    return _load_dialogues_bank_cached(mtime)


def _persist_dialogue_en(conv: dict) -> None:
    """把生成的情境對話加入：session 疊加層（立即可見）+ 永久庫推 GitHub。"""
    st.session_state.setdefault("_sess_dialogues", []).insert(0, conv)  # 立即可見、最新在前
    bank = list(load_dialogues_bank())
    bank.append(conv)
    payload = json.dumps(bank, ensure_ascii=False, indent=2) + "\n"
    try:
        with open(DIALOGUES_BANK_FILE, "w", encoding="utf-8") as f:
            f.write(payload)
    except OSError:
        pass
    if hasattr(_load_dialogues_bank_cached, "clear"):
        _load_dialogues_bank_cached.clear()
    _github_put_file("dialogues_bank.json", payload,
                     f"dialogues_bank: AI 生成「{conv.get('title','')}」（共 {len(bank)} 段）")


@st.cache_data(show_spinner=False)
def _load_stories_bank_cached(_mtime: float) -> list:
    try:
        with open(STORIES_BANK_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def load_stories_bank() -> list:
    """讀取 stories_bank.json（AI 生成的短篇故事，加進口說範本、永久累積）。"""
    try:
        mtime = os.path.getmtime(STORIES_BANK_FILE)
    except OSError:
        mtime = 0.0
    return _load_stories_bank_cached(mtime)


def _persist_story_en(story: dict) -> None:
    """把生成的短篇故事加入：session 疊加層（立即可見）+ 永久庫推 GitHub。"""
    st.session_state.setdefault("_sess_stories", []).insert(0, story)
    bank = list(load_stories_bank())
    bank.append(story)
    payload = json.dumps(bank, ensure_ascii=False, indent=2) + "\n"
    try:
        with open(STORIES_BANK_FILE, "w", encoding="utf-8") as f:
            f.write(payload)
    except OSError:
        pass
    if hasattr(_load_stories_bank_cached, "clear"):
        _load_stories_bank_cached.clear()
    _github_put_file("stories_bank.json", payload,
                     f"stories_bank: AI 生成「{story.get('title','')}」（共 {len(bank)} 篇）")


def _persist_lesson(lesson: dict) -> bool:
    """把情境課程加入永久庫：寫本機 + 推回 GitHub（只增不減）。"""
    bank = list(load_lessons_bank())
    key = (lesson.get("scenario"), lesson.get("created"))
    if key in {(l.get("scenario"), l.get("created")) for l in bank}:
        return True
    bank.append(lesson)
    payload = json.dumps(bank, ensure_ascii=False, indent=2) + "\n"
    try:
        with open(LESSONS_BANK_FILE, "w", encoding="utf-8") as f:
            f.write(payload)
    except OSError:
        pass
    if hasattr(_load_lessons_bank_cached, "clear"):
        _load_lessons_bank_cached.clear()
    ok, _info = _github_put_file(
        "lessons_bank.json", payload,
        f"lessons_bank: 新增情境課程「{lesson.get('scenario','')}」（共 {len(bank)} 課）")
    return ok


def _github_put_file(path: str, payload_json: str, commit_msg: str) -> tuple:
    """通用 GitHub Contents API 寫檔：檔案不存在則建立、存在則更新。回傳 (ok, info)。"""
    import base64
    import urllib.error
    import urllib.request

    token = get_github_token()
    if not token:
        return False, "未設定 GITHUB_TOKEN"
    repo = _read_secret("GITHUB_REPO") or "linchen-20200325/my-English-learn"
    branch = _read_secret("GITHUB_BRANCH") or "main"
    api = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"Bearer {token}",
               "Accept": "application/vnd.github+json",
               "User-Agent": "english-learn-cloud",
               "X-GitHub-Api-Version": "2022-11-28"}
    # 取現有 sha + 遠端內容（不存在則建立新檔，無需 sha）
    sha = None
    try:
        req = urllib.request.Request(f"{api}?ref={branch}", headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            current = json.loads(r.read())
        sha = current.get("sha")
        # 與遠端現有內容聯集，避免覆蓋造成倒退流失（list 依 id/title 去重、dict 直接合併）
        try:
            remote = json.loads(base64.b64decode(current.get("content", "")).decode("utf-8"))
            new = json.loads(payload_json)
            if isinstance(remote, list) and isinstance(new, list):
                seen, union = set(), []
                for item in remote + new:  # 遠端在前為底，本機新增疊上
                    key = item.get("id") or item.get("title") if isinstance(item, dict) else item
                    if key in seen:
                        continue
                    seen.add(key)
                    union.append(item)
                payload_json = json.dumps(union, ensure_ascii=False, indent=2) + "\n"
            elif isinstance(remote, dict) and isinstance(new, dict):
                payload_json = json.dumps({**remote, **new}, ensure_ascii=False, indent=2) + "\n"
        except Exception:  # noqa: BLE001
            pass
    except Exception:  # noqa: BLE001 - 404 = 檔案不存在，首次建立
        sha = None
    body = {"message": commit_msg,
            "content": base64.b64encode(payload_json.encode("utf-8")).decode("ascii"),
            "branch": branch}
    if sha:
        body["sha"] = sha
    try:
        req2 = urllib.request.Request(api, data=json.dumps(body).encode("utf-8"),
                                      method="PUT",
                                      headers={**headers, "Content-Type": "application/json"})
        with urllib.request.urlopen(req2, timeout=20) as r:
            json.loads(r.read())
        return True, "ok"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.read().decode('utf-8','replace')[:200]}"
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"


def _persist_reading(reading: dict) -> tuple:
    """把一篇生成的閱讀加入永久庫：寫回本機 + 推回 GitHub。回傳 (ok, info)。

    讓資料庫越長越大：每生成一篇就 append、去重（以 id）、寫檔、push。
    無 GitHub Token 時仍寫本機（雲端重整會掉，但有 token 就永久）。
    """
    bank = list(load_readings_bank())
    ids = {r.get("id") for r in bank}
    rid = reading.get("id") or reading.get("title", "")
    reading["id"] = rid
    if rid in ids:  # 同 id 已存在就換成唯一 id，避免覆蓋
        reading["id"] = f"{rid}-{len(bank)}"
    bank.append(reading)
    payload = json.dumps(bank, ensure_ascii=False, indent=2) + "\n"
    # 先寫本機（即時生效），再推回 GitHub（永久保存）
    try:
        with open(READINGS_BANK_FILE, "w", encoding="utf-8") as f:
            f.write(payload)
    except OSError:
        pass
    if hasattr(_load_readings_bank_cached, "clear"):
        _load_readings_bank_cached.clear()
    ok, info = _github_put_file(
        "readings_bank.json", payload,
        f"readings_bank: AI 生成新增「{reading.get('title','')}」（共 {len(bank)} 篇）")
    return ok, info


def _run_inapp_generation(n: int, tier: str, auto_push: bool = False) -> None:
    """雲端內用 Gemini 生成 N 字資料,寫進 st.session_state.live_bank。
    嚴格三重去重(同 key 大小寫 / 已在檔案 / 已在 session)。
    auto_push=True 且有 GITHUB_TOKEN 時自動推回 repo,失敗時 banner 顯示。"""
    from scripts.generate_vocab import (SYSTEM_PROMPT, extract_json_array,
                                        load_wordlist)
    file_bank = load_vocab_bank()
    live = st.session_state.setdefault("live_bank", {})
    # 三重去重池(小寫)
    have_lower = {k.lower() for k in file_bank} | {k.lower() for k in live}
    wordlist = load_wordlist()
    todo = [w for w in wordlist if w.lower() not in have_lower][:n]
    todo_set = {w.lower() for w in todo}
    invent_mode = not todo
    if invent_mode:
        # 詞表用罄 → 改請 AI「自己想」尚未收錄的實用新字,達成「無上限」持續生成
        avoid = ", ".join(list(have_lower)[-120:])  # 給最近的字當避免清單
        user_msg = (
            f"請自行挑選 {n} 個「實用、常見、值得學」且**不在以下清單**的英文單字"
            f"（可含片語動詞、慣用搭配；避免重複、避免冷僻專有名詞），"
            f"並依系統格式輸出。已收錄(請避免):{avoid}")
    else:
        user_msg = "請為以下單字生成資料: " + ", ".join(todo)
    # 每字完整 8 欄約需 ~320 token,預留充裕上限避免 JSON 被截斷(上限 32k)
    max_tok = min(32000, 1200 + 360 * (len(todo) or n))
    with st.spinner(f"用 Gemini ({tier}) {'自動發想' if invent_mode else '生成'} "
                    f"{len(todo) or n} 字…"):
        text = _llm_generate(SYSTEM_PROMPT, user_msg, tier, max_tokens=max_tok)
        entries = extract_json_array(text)
    added, skipped = 0, 0
    new_words = []
    for e in entries:
        ww = (e.get("word") or "").strip().lower()
        if not ww:
            continue
        # 去重:詞表模式須是點名的字;發想模式接受任何未收錄的新字;且 entry 完整
        if ((invent_mode or ww in todo_set) and ww not in have_lower
                and e.get("meaning_zh") and e.get("kk")):
            live[ww] = e
            have_lower.add(ww)
            new_words.append(ww)
            added += 1
        else:
            skipped += 1
    msg = f"✅ 已生成 {added} 字：{', '.join(new_words[:10])}{' …' if len(new_words) > 10 else ''}"
    if skipped:
        msg += f"\n\n去重/欄位不全略過 {skipped} 字"
    st.success(msg)
    # 持久橫幅：rerun 後仍能看到本次成果（避免使用者以為沒反應）
    st.session_state["_just_generated"] = True
    st.session_state["_gen_result_banner"] = {
        "added": added,
        "preview": (", ".join(new_words[:8]) + (" …" if len(new_words) > 8 else "")),
        "total": len(file_bank) + len(live),
        "note": (f"這批字經去重後沒有新增（略過 {skipped} 字）。"
                 "再按一次會換下一批詞。" if added == 0 else ""),
    }
    # 自動推回:把結果記在 session,讓使用者看到「上次推回成功/失敗」
    if auto_push:
        st.info("⏳ 自動推回 GitHub repo 中…")
        ok = _push_bank_to_github(silent=False)
        st.session_state["_last_push"] = {
            "ok": ok,
            "added": added,
            "ts": __import__("datetime").datetime.now().strftime("%H:%M:%S"),
        }
        if not ok:
            st.error("⚠️ **重要**:這批 {added} 字推回失敗,只留在 session,**重整就消失**!\n"
                     "請手動按下方「⬇️ 下載合併後 vocab_bank.json」存檔。"
                     .format(added=added))
    return added


def _push_file_to_github(local_path: str, repo_path: str,
                         message: str, silent: bool = False) -> bool:
    """通用:把本機檔推回 repo(GitHub Contents API GET sha → PUT base64)。
    需 GITHUB_TOKEN。失敗時 silent=False 顯示 st.toast 提示。"""
    import base64
    import urllib.error
    import urllib.request

    token = get_github_token()
    if not token:
        return False
    try:
        with open(local_path, "rb") as f:
            content_bytes = f.read()
    except OSError:
        return False
    repo = _read_secret("GITHUB_REPO") or "linchen-20200325/my-English-learn"
    branch = _read_secret("GITHUB_BRANCH") or "main"
    api = f"https://api.github.com/repos/{repo}/contents/{repo_path}"
    headers = {"Authorization": f"Bearer {token}",
               "Accept": "application/vnd.github+json",
               "User-Agent": "english-learn-cloud",
               "X-GitHub-Api-Version": "2022-11-28"}
    sha = None
    try:
        req = urllib.request.Request(f"{api}?ref={branch}", headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            current = json.loads(r.read())
        sha = current.get("sha")
    except urllib.error.HTTPError as e:
        if e.code != 404:  # 404 = 檔案不存在(首次 commit),可繼續 PUT
            if not silent:
                st.toast(f"推 {repo_path} 失敗(GET sha {e.code})", icon="⚠️")
            return False
    except Exception:  # noqa: BLE001
        if not silent:
            st.toast(f"推 {repo_path} 失敗(GET)", icon="⚠️")
        return False
    try:
        body_obj = {"message": message,
                    "content": base64.b64encode(content_bytes).decode("ascii"),
                    "branch": branch}
        if sha:
            body_obj["sha"] = sha
        body = json.dumps(body_obj).encode("utf-8")
        req2 = urllib.request.Request(api, data=body, method="PUT",
                                       headers={**headers,
                                                "Content-Type": "application/json"})
        with urllib.request.urlopen(req2, timeout=20) as r:
            result = json.loads(r.read())
        if not silent:
            st.toast(f"✅ 推回 `{repo_path}` (commit {result.get('commit',{}).get('sha','')[:7]})",
                     icon="📤")
        return True
    except urllib.error.HTTPError as e:
        if not silent:
            body_text = e.read().decode("utf-8", "replace")[:120]
            st.toast(f"推 {repo_path} 失敗 {e.code}: {body_text}", icon="⚠️")
        return False
    except Exception as e:  # noqa: BLE001
        if not silent:
            st.toast(f"推 {repo_path} 失敗: {type(e).__name__}", icon="⚠️")
        return False


def _push_bank_to_github(silent: bool = False) -> bool:
    """把目前合併後的 vocab_bank(file + live)透過 GitHub Contents API 推回 repo。
    需要 GITHUB_TOKEN secret(repo 寫權限)。回傳是否成功。"""
    import base64
    import urllib.error
    import urllib.request

    token = get_github_token()
    if not token:
        if not silent:
            st.error("未設定 GITHUB_TOKEN secret，無法自動推回。"
                     "請至 Cloud Secrets 加入 `GITHUB_TOKEN = \"github_pat_...\"`。")
        return False

    repo = _read_secret("GITHUB_REPO") or "linchen-20200325/my-English-learn"
    branch = _read_secret("GITHUB_BRANCH") or "main"
    path = "vocab_bank.json"

    file_bank = load_vocab_bank()
    live = st.session_state.get("live_bank", {})
    synced = st.session_state.get("synced_bank", {})
    merged = {**file_bank, **synced, **live}
    payload_json = json.dumps(merged, ensure_ascii=False, indent=2) + "\n"

    api = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"Bearer {token}",
               "Accept": "application/vnd.github+json",
               "User-Agent": "english-learn-cloud",
               "X-GitHub-Api-Version": "2022-11-28"}

    def _save_err(stage, code, body_text):
        """把錯誤詳情存進 session,顯示時讓使用者看清楚到底哪裡卡住。"""
        st.session_state["_push_error"] = {
            "stage": stage, "code": code, "body": body_text[:2000],
            "repo": repo, "branch": branch, "path": path,
            "token_prefix": (token[:12] + "…" + token[-4:]) if token else "",
            "payload_size": len(payload_json),
            "live_count": len(live),
        }

    try:
        # 1) GET current sha + 遠端現有內容
        req = urllib.request.Request(f"{api}?ref={branch}", headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            current = json.loads(r.read())
        sha = current["sha"]
        # 關鍵：與「遠端現有字庫」做聯集再推，避免用較舊的本機檔覆蓋、造成字數倒退流失。
        try:
            remote_raw = base64.b64decode(current.get("content", "")).decode("utf-8")
            remote_bank = json.loads(remote_raw)
            if isinstance(remote_bank, dict):
                merged = {**remote_bank, **merged}  # 遠端為底，本機/session 新增疊上 → 只增不減
                payload_json = json.dumps(merged, ensure_ascii=False, indent=2) + "\n"
        except Exception:  # noqa: BLE001 - 遠端解析失敗就用原本的 merged
            pass
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", "replace")
        _save_err("GET sha", e.code, body_text)
        if not silent:
            st.error(
                f"❌ 推回第一步失敗:抓取現存檔案 sha (HTTP {e.code})\n\n"
                f"**Repo**: `{repo}@{branch}`\n"
                f"**API**: `{api}`\n\n"
                f"**Google 回應**: {body_text[:400]}\n\n"
                f"**最可能原因**:\n"
                f"- 404 → repo 名稱錯/branch 名稱錯,或 token 對該 repo 沒讀取權限\n"
                f"- 401/403 → token 無效、過期、或沒給 `Contents: Read+Write` 權限\n"
                f"**請到** https://github.com/settings/personal-access-tokens **重新生 PAT**,"
                f"Repository access 選 `Only this repo`(my-English-learn),"
                f"Permissions → Contents: Read and write。"
            )
        return False
    except Exception as e:  # noqa: BLE001
        _save_err("GET sha", 0, f"{type(e).__name__}: {e}")
        if not silent:
            st.error(f"❌ 推回失敗(GET sha 階段):{type(e).__name__}: {e}")
        return False

    try:
        # 2) PUT new content
        body = json.dumps({
            "message": f"vocab_bank: cloud append (+{len(live)} 字, 共 {len(merged)} 字)",
            "content": base64.b64encode(payload_json.encode("utf-8")).decode("ascii"),
            "sha": sha,
            "branch": branch,
        }).encode("utf-8")
        req2 = urllib.request.Request(api, data=body, method="PUT",
                                       headers={**headers,
                                                "Content-Type": "application/json"})
        with urllib.request.urlopen(req2, timeout=20) as r:
            result = json.loads(r.read())
        commit_sha = result.get("commit", {}).get("sha", "")[:7]
        if not silent:
            st.success(f"✅ 已推回 GitHub commit `{commit_sha}` 到 `{repo}@{branch}`("
                       f"+{len(live)} 字)。Cloud 自動重新部署後永久保存。")
        st.session_state.pop("_push_error", None)  # 成功就清掉錯誤紀錄
        # 嘗試寫本機（Streamlit Cloud 的 /mount/src 多為唯讀，會靜默失敗，故不依賴它）。
        try:
            with open(VOCAB_BANK_FILE, "w", encoding="utf-8") as f:
                f.write(payload_json)
        except OSError:
            pass
        load_vocab_bank.clear() if hasattr(load_vocab_bank, "clear") else None
        # 關鍵：把已推回的字移進「session 已同步層」（不清掉），畫面才會立刻顯示新總數
        # 而非讀到部署當下的舊本機檔（唯讀寫不進去）。重新部署後本機檔才會追上。
        st.session_state.setdefault("synced_bank", {}).update(live)
        st.session_state["live_bank"] = {}
        return True
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", "replace")
        _save_err("PUT", e.code, body_text)
        if not silent:
            st.error(
                f"❌ 推回第二步失敗:寫入 commit (HTTP {e.code})\n\n"
                f"**Google 回應**: {body_text[:400]}\n\n"
                f"**常見原因**:403 = 沒寫權限(token Permissions 沒給 Contents: Write);"
                f"422 = sha 對不上(他人剛剛改過,重試一次)。"
            )
        return False
    except Exception as e:  # noqa: BLE001
        _save_err("PUT", 0, f"{type(e).__name__}: {e}")
        if not silent:
            st.error(f"❌ 推回失敗(PUT 階段):{type(e).__name__}: {e}")
        return False


def _build_dialogue_html(lines: list) -> str:
    """把對話列表渲染成單一 HTML 區塊(含每行 🔊 TTS 按鈕)。"""
    rows = []
    for line in lines:
        en = _html.escape(line["en"])
        zh = _html.escape(line["zh"])
        spk = _html.escape(line["speaker"])
        en_js = _esc_js(line["en"])
        rows.append(f"""
        <div style="margin:6px 0; padding:10px 14px; background:#f8fafc; border-radius:8px;
                    border-left:4px solid #6366f1; display:flex; gap:10px;
                    align-items:flex-start;">
            <div style="flex:1;">
                <div><span style="font-weight:700; color:#4f46e5;">{spk}：</span>{en}</div>
                <div style="color:#475569; font-size:13px; margin-top:4px;">🇹🇼 {zh}</div>
            </div>
            <button onclick="
              const u=new SpeechSynthesisUtterance('{en_js}');
              u.lang='en-US'; u.rate=0.92;
              speechSynthesis.cancel(); speechSynthesis.speak(u);
            " style="padding:6px 12px; font-size:14px; border:none; border-radius:999px;
                     cursor:pointer; background:#4f46e5; color:#fff; flex-shrink:0;
                     align-self:center;">🔊</button>
        </div>""")
    play_all_js = "; ".join(
        f"q.push(new SpeechSynthesisUtterance('{_esc_js(L['en'])}'))" for L in lines
    )
    header = f"""
    <div style="margin-bottom:10px; text-align:right;">
        <button onclick="
          const q=[]; {play_all_js};
          q.forEach(u => {{ u.lang='en-US'; u.rate=0.9; speechSynthesis.speak(u); }});
        " style="padding:8px 16px; font-size:14px; border:none; border-radius:999px;
                 cursor:pointer; background:#10b981; color:#fff;">▶️ 唸整段對話</button>
        <button onclick="speechSynthesis.cancel();" style="padding:8px 14px; font-size:14px;
                border:1px solid #ddd; border-radius:999px; cursor:pointer;
                background:#fff; color:#475569; margin-left:6px;">⏹ 停止</button>
    </div>"""
    return ('<div style="font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;">'
            + header + "".join(rows) + "</div>")


def _build_story_html(paragraphs: list) -> str:
    rows = []
    full_text = " ".join(p["en"] for p in paragraphs)
    full_js = _esc_js(full_text)
    for p in paragraphs:
        en = _html.escape(p["en"])
        zh = _html.escape(p["zh"])
        en_js = _esc_js(p["en"])
        rows.append(f"""
        <div style="margin:8px 0; padding:12px 16px; background:#f8fafc;
                    border-radius:10px; border-left:4px solid #10b981;">
            <div style="display:flex; gap:10px; align-items:flex-start;">
                <div style="flex:1; line-height:1.7;">{en}</div>
                <button onclick="
                  const u=new SpeechSynthesisUtterance('{en_js}');
                  u.lang='en-US'; u.rate=0.92;
                  speechSynthesis.cancel(); speechSynthesis.speak(u);
                " style="padding:6px 12px; font-size:14px; border:none; border-radius:999px;
                         cursor:pointer; background:#10b981; color:#fff; flex-shrink:0;
                         align-self:center;">🔊</button>
            </div>
            <div style="color:#475569; font-size:14px; margin-top:6px; line-height:1.6;">
                🇹🇼 {zh}
            </div>
        </div>""")
    header = f"""
    <div style="margin-bottom:10px; text-align:right;">
        <button onclick="
          const u=new SpeechSynthesisUtterance('{full_js}');
          u.lang='en-US'; u.rate=0.9;
          speechSynthesis.cancel(); speechSynthesis.speak(u);
        " style="padding:8px 16px; font-size:14px; border:none; border-radius:999px;
                 cursor:pointer; background:#10b981; color:#fff;">▶️ 唸整篇故事</button>
        <button onclick="speechSynthesis.cancel();" style="padding:8px 14px; font-size:14px;
                border:1px solid #ddd; border-radius:999px; cursor:pointer;
                background:#fff; color:#475569; margin-left:6px;">⏹ 停止</button>
    </div>"""
    return ('<div style="font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;">'
            + header + "".join(rows) + "</div>")


def _render_grammar(items: list) -> None:
    """渲染文法重點區塊（對 AI 生成缺欄位防呆）。"""
    if not items:
        return
    st.markdown("##### 📚 文法重點")
    for g in items:
        if not isinstance(g, dict):
            continue
        with st.container(border=True):
            st.markdown(f"**🎯 {g.get('point', '')}**")
            if g.get("explain"):
                st.caption(g["explain"])
            for ex in g.get("examples", []):
                st.markdown(f"　- `{ex}`")


GRAMMAR_GEN_PROMPT = """你是英文文法教材編輯。使用者給「程度」與「已存在的文法（不可重複）」，
請產出該程度**新的、不重複**的核心文法/句型重點。

# 嚴格輸出 JSON（只輸出 JSON array，前後不得有任何文字、不得包 markdown code fence）
[
  {
    "point": "文法/句型名稱（英文＋中文，如 Present Perfect 現在完成式）",
    "explain": "繁中解說：意義、何時用、結構",
    "examples": ["English example 1", "English example 2", "English example 3"]
  }
]

# 規範
- 嚴禁與「已存在文法」清單重複。
- 每個文法 3 個英文例句。
- 難度貼合程度：A2 基礎、B1 中級、B2 中高級、C1 高級。
"""


def _extract_json_array(text: str):
    """從模型回應穩健抽出 JSON array（容忍 code fence 與前後雜訊）。"""
    text = (text or "").strip()
    m = re.search(r"```(?:json)?\s*(\[[\s\S]*?\])\s*```", text)
    if m:
        text = m.group(1)
    else:
        s, e = text.find("["), text.rfind("]")
        if s != -1 and e != -1 and e > s:
            text = text[s:e + 1]
    return json.loads(text)


def _gen_grammar_batch(level: str, existing: list, n: int) -> list:
    """為指定程度生成 n 個不重複的新文法點。回傳 list（每筆含 level）。"""
    ex = "、".join(existing) if existing else "（無）"
    text = _llm_generate(GRAMMAR_GEN_PROMPT,
                         f"程度：{level}\n數量：{n}\n已存在文法（不可重複）：{ex}",
                         next(iter(_MODEL_MAP.keys())), max_tokens=6000)
    items = _extract_json_array(text)
    out, have = [], set(existing)
    for it in items:
        if not isinstance(it, dict):
            continue
        point = (it.get("point") or "").strip()
        if not point or point in have or not it.get("explain"):
            continue
        it["level"] = level
        it.setdefault("examples", [])
        out.append(it)
        have.add(point)
    return out


def _persist_grammar(items: list, level: str) -> tuple:
    """把 AI 生成的文法加入永久庫：寫本機 + 推回 GitHub。回傳 (added, ok)。"""
    bank = list(load_grammar_bank())
    have = {(g.get("level"), g.get("point")) for g in bank}
    added = 0
    for it in items:
        it.setdefault("level", level)
        if (it.get("level"), it.get("point")) in have:
            continue
        bank.append(it)
        have.add((it.get("level"), it.get("point")))
        added += 1
    payload = json.dumps(bank, ensure_ascii=False, indent=2) + "\n"
    try:
        with open(GRAMMAR_BANK_FILE, "w", encoding="utf-8") as f:
            f.write(payload)
    except OSError:
        pass
    if hasattr(_load_grammar_bank_cached, "clear"):
        _load_grammar_bank_cached.clear()
    ok, _info = _github_put_file(
        "grammar_bank.json", payload,
        f"grammar_bank: AI 生成 {level} 文法 +{added}（共 {len(bank)} 條）")
    return added, ok


def _grammar_for_level(level: str) -> list:
    """合併「部署檔 + 本 session 生成」的文法（去重），確保生成後立刻看得到。

    Streamlit Cloud 的 /mount/src 唯讀，寫本機會失敗，故顯示一律疊上 session 生成的內容。
    """
    sess = st.session_state.get("_sess_grammar", [])
    out, seen = [], set()
    for g in list(load_grammar_bank()) + list(sess):
        if g.get("level") != level:
            continue
        if g.get("point") in seen:
            continue
        seen.add(g.get("point"))
        out.append(g)
    return out


def view_library() -> None:
    """📚 我的資料庫：所有 AI 生成並累積的內容（單字/文法/閱讀/情境）集中瀏覽。"""
    st.caption("所有 AI 生成、累積的內容都在這裡瀏覽——這些都會推到 GitHub 永久保存、持續長大。")

    vocab = {**load_vocab_bank(),
             **st.session_state.get("synced_bank", {}),
             **st.session_state.get("live_bank", {})}
    # 文法（合併部署檔 + session 生成，去重）
    gseen, grammar = set(), []
    for g in list(load_grammar_bank()) + list(st.session_state.get("_sess_grammar", [])):
        k = (g.get("level"), g.get("point"))
        if k in gseen:
            continue
        gseen.add(k)
        grammar.append(g)
    # 閱讀（含字幕，合併永久庫 + 本 session）
    rseen, reading = set(), []
    for r in list(st.session_state.get("live_readings", [])) + list(load_readings_bank()):
        k = r.get("id") or r.get("title")
        if k in rseen:
            continue
        rseen.add(k)
        reading.append(r)
    # 情境課程（本機 + 永久庫，去重）
    data = st.session_state.data
    lseen, lessons = set(), []
    for l in list(data.get("lessons", [])) + list(load_lessons_bank()):
        k = (l.get("scenario"), l.get("created"))
        if k in lseen:
            continue
        lseen.add(k)
        lessons.append(l)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📗 單字", len(vocab))
    m2.metric("📐 文法", len(grammar))
    m3.metric("📚 閱讀／字幕", len(reading))
    m4.metric("🗣️ 情境課程", len(lessons))

    t_v, t_g, t_r, t_l = st.tabs(["📗 單字", "📐 文法", "📚 閱讀／字幕", "🗣️ 情境課程"])
    with t_v:
        if not vocab:
            st.info("還沒有單字。到「📖 單字庫」按生成。")
        else:
            q = st.text_input("搜尋（英文／中文／諧音）", key="lib_vq").strip().lower()
            words = sorted(vocab)
            if q:
                words = [w for w in words if q in w.lower()
                         or q in (vocab[w].get("meaning_zh") or "").lower()
                         or q in (vocab[w].get("homophone") or "").lower()]
            st.caption(f"共 {len(vocab)} 字　·　符合 {len(words)} 字（最多顯示 80）")
            for w in words[:80]:
                e = vocab[w]
                st.markdown(f"**{w}**　{e.get('kk','')}　— {e.get('meaning_zh','')}"
                            + (f"　🔊 {e['homophone']}" if e.get("homophone") else ""))
    with t_g:
        if not grammar:
            st.info("還沒有文法。到「📐 文法生成」用 AI 生成。")
        for g in grammar:
            with st.expander(f"[{g.get('level','')}] {g.get('point','')}"):
                st.caption(g.get("explain", ""))
                for ex in g.get("examples", []):
                    st.markdown(f"- {ex}")
    with t_r:
        if not reading:
            st.info("還沒有閱讀。到「📚 互動閱讀」或「🎬 影視字幕」生成。")
        for r in reading:
            with st.expander(f"{r.get('title','')}　{r.get('title_zh','')}"):
                for s in r.get("sentences", []):
                    st.markdown(f"- {s.get('en','')}（{s.get('zh','')}）")
    with t_l:
        if not lessons:
            st.info("還沒有情境課程。到「💬 情境會話 → AI 情境生成」按「儲存這課」。")
        for l in lessons:
            with st.expander(f"📍 {l.get('scenario','')}（{l.get('created','')}）"):
                for c in l.get("flashcards", []):
                    st.markdown(f"- **{c.get('sentence','')}**（{c.get('chinese','')}）")


def view_grammar() -> None:
    """📐 文法生成：AI 依程度生成不重複文法，存進資料庫持續長大。"""
    level = st.session_state.get("en_level", "B1")
    st.caption(f"AI 依**目前程度 {level}**（左側 sidebar 可改）生成核心文法/句型，"
               "每次不重複，永久存進資料庫越累積越多。")
    bank = _grammar_for_level(level)

    if st.session_state.pop("_gram_saved", None) is not None:
        st.success(f"已生成並存進文法資料庫！{level} 現有 {len(bank)} 條。")

    api_key = get_api_key()
    if not api_key:
        st.warning("需要 Gemini 金鑰才能生成（下方已生成的文法仍可閱讀）。請至 sidebar 確認金鑰。")
    else:
        c1, c2 = st.columns([2, 3])
        n = c1.number_input("一次生成幾條", 1, 10, 3, key="gramn")
        if c2.button("🤖 生成新文法", type="primary", use_container_width=True):
            try:
                with st.spinner("AI 生成中…"):
                    items = _gen_grammar_batch(level, [g["point"] for g in bank], int(n))
                if items:
                    # 先放進 session 疊加層 → 立刻看得到（不依賴唯讀本機檔）
                    st.session_state.setdefault("_sess_grammar", []).extend(items)
                    try:
                        _persist_grammar(items, level)  # 推回 GitHub 永久保存
                    except Exception:  # noqa: BLE001
                        pass
                    st.session_state["_gram_saved"] = len(items)
                    st.rerun()
                else:
                    st.warning("這次沒有產生新的（可能與既有重複），請再試一次。")
            except Exception as e:  # noqa: BLE001
                st.error(_friendly_gen_error(f"{type(e).__name__}: {e}"))

    if bank:
        st.markdown(f"#### 📐 {level} 文法（已累積 {len(bank)} 條）")
        _render_grammar(list(reversed(bank)))
    else:
        st.info("此程度尚無文法。按上方「🤖 生成新文法」開始建立你的文法資料庫。")


def view_scenario() -> None:
    """情境會話（整合）：把原「口說範本」與「情境生成」合併為單一入口。

    兩者皆圍繞「同一情境的會話練習」：口說範本是離線範本打底，情境生成是
    Gemini 依任意主題即時產生對話心智圖＋句卡。合併後介面更乾淨、語意不重疊。
    """
    st.caption("同一情境的兩種練法：先用離線範本打底跟讀，再用 AI 依你想練的主題即時生成。")
    tab_template, tab_ai = st.tabs(["🗣️ 口說範本（離線）", "🤖 AI 情境生成"])
    with tab_template:
        view_speak_story()
    with tab_ai:
        view_generate()


def view_speak_story() -> None:
    with st.expander("💡 這是什麼？怎麼用？", expanded=False):
        st.markdown(
            "**口說範本**＝離線預載的「情境對話 + 短篇故事」雙語對照範本，每段附文法重點。\n\n"
            "**怎麼用**：\n"
            "1. 展開任一情境（咖啡廳／同事閒聊／退換貨／抱怨工作／週末約）或故事（晨間日常／旅行回憶）\n"
            "2. 每句／每段右側「🔊」唸該句；頂部「▶️ 唸整段／整篇」一鍵連讀\n"
            "3. **跟著唸**（shadowing 跟讀法）：聽一遍 → 暫停 → 模仿語調再唸一次。是進步口說最有效的練習\n"
            "4. 下方「📚 文法重點」逐句解說 + 同類型例句，可結合到日常表達\n"
            "5. 喜歡的對話可「加入複習」，SRS 排程之後回頭練\n\n"
            "**程度**：A2 = 基礎對話、B1 = 中級流暢、B2 = 進階表達。從低到高循序漸進。"
        )
    # 累積對話（session 疊加層 + 永久庫，去重）＋ 內建範本
    gen_dialogues, dseen = [], set()
    for d in list(st.session_state.get("_sess_dialogues", [])) + list(load_dialogues_bank()):
        k = d.get("id") or d.get("title")
        if k in dseen:
            continue
        dseen.add(k)
        gen_dialogues.append(d)
    all_convs = gen_dialogues + list(CONVERSATIONS)

    tab1, tab2 = st.tabs([f"🗣️ 情境對話（{len(all_convs)} 個）",
                          f"📖 短篇故事（{len(STORIES)} 篇）"])

    with tab1:
        # 🎲 隨機生成情境對話 → 加進範本、永久累積
        api_key = get_api_key()
        lvl = st.session_state.get("en_level", "B1")
        if st.session_state.pop("_dlg_toast", None):
            st.success("已生成新情境對話，已加進範本最上面（並永久存入資料庫）。")
        rc1, rc2 = st.columns([3, 2])
        if rc1.button(f"🎲 隨機生成情境對話（{lvl}）", type="primary",
                      use_container_width=True, disabled=not api_key):
            used = {d.get("title") for d in gen_dialogues}
            pool = [t for t in _DIALOGUE_TOPICS if t not in used] or _DIALOGUE_TOPICS
            try:
                with st.spinner("Gemini 生成情境對話中…"):
                    conv = _gen_dialogue_en(random.choice(pool), lvl)
                _persist_dialogue_en(conv)
                st.session_state["_dlg_toast"] = True
                st.rerun()
            except Exception as e:  # noqa: BLE001
                st.error(_friendly_gen_error(f"{type(e).__name__}: {e}"))
        rc2.caption(f"🌱 已累積 **{len(gen_dialogues)}** 段 AI 對話")

        for ci, conv in enumerate(all_convs):
            if not isinstance(conv.get("lines"), list) or not conv["lines"]:
                continue
            tag = "🌱 " if ci < len(gen_dialogues) else ""
            with st.expander(
                f"{tag}**{conv.get('title','')}**　·　程度 {conv.get('level','')}　·　{conv.get('scene','')}",
            ):
                _embed_html(_build_dialogue_html(conv["lines"]),
                            height=120 + 78 * len(conv["lines"]))
                st.divider()
                _render_grammar(conv.get("grammar", []))
                if st.button(f"➕ 加入 {len(conv['lines'])} 句到「🔁 複習」",
                             key=f"add_conv_{ci}", use_container_width=True):
                    cards = [
                        {"sentence": L.get("en", ""), "chinese": L.get("zh", ""),
                         "chunk": L.get("en", "")[:40], "context": f"情境：{conv.get('title','')}"}
                        for L in conv["lines"] if L.get("en")
                    ]
                    n = add_cards_to_review(cards)
                    st.success(f"已加入 {n} 句到複習清單。")

    with tab2:
        # 累積故事（session 疊加層 + 永久庫，去重）＋ 內建範本
        gen_stories, sseen = [], set()
        for s in list(st.session_state.get("_sess_stories", [])) + list(load_stories_bank()):
            k = s.get("id") or s.get("title")
            if k in sseen:
                continue
            sseen.add(k)
            gen_stories.append(s)
        all_stories = gen_stories + list(STORIES)

        # 🎲 隨機生成短篇故事 → 加進範本、永久累積
        api_key = get_api_key()
        lvl = st.session_state.get("en_level", "B1")
        if st.session_state.pop("_story_toast", None):
            st.success("已生成新短篇故事，已加進範本最上面（並永久存入資料庫）。")
        sc1, sc2 = st.columns([3, 2])
        if sc1.button(f"🎲 隨機生成短篇故事（{lvl}）", type="primary",
                      use_container_width=True, disabled=not api_key, key="story_rand_gen"):
            used = {s.get("title") for s in gen_stories}
            pool = [t for t in _STORY_TOPICS if t not in used] or _STORY_TOPICS
            try:
                with st.spinner("Gemini 生成短篇故事中…"):
                    story = _gen_story_en(random.choice(pool), lvl)
                _persist_story_en(story)
                st.session_state["_story_toast"] = True
                st.rerun()
            except Exception as e:  # noqa: BLE001
                st.error(_friendly_gen_error(f"{type(e).__name__}: {e}"))
        sc2.caption(f"🌱 已累積 **{len(gen_stories)}** 篇 AI 故事")

        for si, story in enumerate(all_stories):
            if not isinstance(story.get("paragraphs"), list) or not story["paragraphs"]:
                continue
            tag = "🌱 " if si < len(gen_stories) else ""
            with st.expander(f"{tag}**{story.get('title','')}**　·　程度 "
                             f"{story.get('level','')}　·　{story.get('scene','')}"):
                _embed_html(_build_story_html(story["paragraphs"]),
                            height=120 + 130 * len(story["paragraphs"]))
                st.divider()
                _render_grammar(story.get("grammar", []))
                if st.button(f"➕ 加入 {len(story['paragraphs'])} 段到「🔁 複習」",
                             key=f"add_story_{si}", use_container_width=True):
                    cards = [
                        {"sentence": p.get("en", ""), "chinese": p.get("zh", ""),
                         "chunk": p.get("en", "")[:40], "context": f"故事：{story.get('title','')}"}
                        for p in story["paragraphs"] if p.get("en")
                    ]
                    n = add_cards_to_review(cards)
                    st.success(f"已加入 {n} 段到複習清單。")


def _annotate_sentence_html(en: str, vocab: dict) -> str:
    """把英文句子每個字包成 <span class="word" data-zh="...">word</span>。
    可點看翻譯與聽發音。標點與空白保留原樣。"""
    vocab_lower = {k.lower(): v for k, v in (vocab or {}).items()}

    def _wrap(match):
        word = match.group(0)
        zh = vocab_lower.get(word.lower(), "")
        if zh:
            return (f'<span class="word" data-zh="{_html.escape(zh)}">'
                    f'{_html.escape(word)}</span>')
        return f'<span class="word">{_html.escape(word)}</span>'

    parts = re.findall(r"[A-Za-zÀ-ɏ一-鿿']+|[^A-Za-zÀ-ɏ一-鿿'\s]+|\s+", en)
    out = []
    for p in parts:
        if re.match(r"[A-Za-z']+$", p):
            out.append(_wrap(re.match(r".*", p)))
        else:
            out.append(_html.escape(p))
    return "".join(out)


def _build_reading_html(passage: dict) -> str:
    """把整篇閱讀渲染成單一 HTML(含 JS):點字看翻譯、點句子高亮+全句翻譯+朗讀。"""
    sentence_blocks = []
    for i, s in enumerate(passage["sentences"]):
        en = s.get("en", "")
        body = _annotate_sentence_html(en, s.get("vocab", {}))
        zh_full = _html.escape(s.get("zh", ""))
        en_js = _esc_js(en)
        sentence_blocks.append(
            f'<span class="sentence" data-id="{i}" data-zh="{zh_full}" '
            f'data-en="{_html.escape(en)}" data-enjs="{en_js}">{body}</span> '
        )
    full_text_js = _esc_js(" ".join(s.get("en", "") for s in passage["sentences"]))

    css = """
    .reading {
        font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;
        font-size: 18px; line-height: 2.0; padding: 18px 22px;
        background: #fafaf9; border-radius: 12px; border:1px solid #e7e5e4;
    }
    .word {
        cursor: pointer; padding: 1px 2px; border-radius: 4px;
        transition: background 0.1s;
    }
    .word[data-zh]:hover { background: #fde68a; }
    .word.tts-active { background: #fbbf24; }
    .sentence { transition: background 0.15s; padding: 2px 0; }
    .sentence:hover { background: #f5f5f4; }
    .sentence.active { background: #dbeafe; }
    #tooltip {
        position: fixed; background: #0f172a; color: #fff;
        padding: 6px 10px; border-radius: 6px; font-size: 14px;
        pointer-events: none; z-index: 9999; display: none; max-width: 280px;
        box-shadow: 0 4px 12px rgba(0,0,0,.18);
    }
    #panel {
        margin-top: 14px; padding: 14px 18px; background: #fff;
        border: 2px solid #4f46e5; border-radius: 12px; color: #312e81;
        min-height: 50px; font-size: 15px;
    }
    #panel .pen { color: #4338ca; font-weight: 600; }
    #panel .pzh { color: #1e293b; margin-top: 6px; }
    .controls { margin-bottom: 10px; }
    .btn {
        padding: 8px 16px; font-size: 14px; border: none; border-radius: 999px;
        cursor: pointer; margin-right: 6px;
    }
    .btn-play { background:#10b981; color:#fff; }
    .btn-stop { background:#fff; color:#475569; border:1px solid #ddd; }
    .hint { color: #64748b; font-size: 13px; margin-top: 8px; }
    """
    body = "".join(sentence_blocks)
    html = f"""
    <style>{css}</style>
    <div class="controls">
        <button class="btn btn-play" onclick="
          const u=new SpeechSynthesisUtterance('{full_text_js}');
          u.lang='en-US'; u.rate=0.9;
          speechSynthesis.cancel(); speechSynthesis.speak(u);">▶️ 唸整篇</button>
        <button class="btn btn-stop" onclick="speechSynthesis.cancel();">⏹ 停止</button>
    </div>
    <div class="reading">{body}</div>
    <div class="hint">💡 滑鼠移到單字可看翻譯，點單字會唸該字；點句子會高亮並在下方顯示全句翻譯與朗讀。</div>
    <div id="panel">點選任一句子，這裡會顯示中文翻譯。</div>
    <div id="tooltip"></div>
    <script>
    const tooltip = document.getElementById('tooltip');
    const panel = document.getElementById('panel');
    document.querySelectorAll('.word').forEach(el => {{
        el.addEventListener('mouseenter', () => {{
            const zh = el.dataset.zh;
            if (!zh) return;
            tooltip.textContent = zh;
            tooltip.style.display = 'block';
            const r = el.getBoundingClientRect();
            tooltip.style.left = r.left + 'px';
            tooltip.style.top = (r.top - 36) + 'px';
        }});
        el.addEventListener('mouseleave', () => tooltip.style.display = 'none');
        el.addEventListener('click', e => {{
            e.stopPropagation();
            document.querySelectorAll('.word.tts-active').forEach(w => w.classList.remove('tts-active'));
            el.classList.add('tts-active');
            const u = new SpeechSynthesisUtterance(el.textContent);
            u.lang = 'en-US'; u.rate = 0.95;
            speechSynthesis.cancel(); speechSynthesis.speak(u);
            setTimeout(() => el.classList.remove('tts-active'), 800);
        }});
    }});
    document.querySelectorAll('.sentence').forEach(el => {{
        el.addEventListener('click', () => {{
            document.querySelectorAll('.sentence').forEach(s => s.classList.remove('active'));
            el.classList.add('active');
            const en = el.dataset.en || '';
            const zh = el.dataset.zh || '';
            panel.innerHTML = '<div class="pen">' + en + '</div><div class="pzh">🇹🇼 ' + zh + '</div>';
            const u = new SpeechSynthesisUtterance(el.dataset.enjs);
            u.lang='en-US'; u.rate=0.92;
            speechSynthesis.cancel(); speechSynthesis.speak(u);
        }});
    }});
    </script>
    """
    return html


READING_GEN_PROMPT = """你是英文閱讀教材編輯。使用者給「主題 + 程度」,你產出一篇可互動的閱讀練習。

# 嚴格輸出 JSON(只輸出 JSON,前後不得有任何文字、不得包 markdown code fence)
{
  "id": "topic-keyword-id",
  "title": "英文標題",
  "title_zh": "繁中標題",
  "level": "A2 / B1 / B2 / C1 擇一",
  "summary": "繁中一句話描述文章特色與適用文法",
  "sentences": [
    {
      "en": "自然口語/書面英文,≤ 25 字/句",
      "zh": "繁中翻譯",
      "vocab": {"word": "中文翻譯", "word2": "..."},
      "phrases": [{"en": "multi-word phrase", "zh": "中文 + 語境提示"}]
    }
  ],
  "grammar": [
    {"point": "文法重點", "explain": "繁中解說", "examples": ["例 1", "例 2", "例 3"]}
  ]
}

# 數量規範
- sentences: 6-8 句
- 每句 vocab 5-8 個字(挑學習者最可能不懂的,key 用小寫純字母,不含標點)
- 每句 phrases 2-4 個多字片語
- grammar: 3-5 條重點

# 程度差異
- A2: 簡單現在式、基礎詞、生活情境
- B1: 過去式 + 完成式、職場 / 旅行 / 情感
- B2: 抽象概念、條件式、被動、複合句
- C1: 文學 / 評論、進階句型、學術詞
"""


SUBTITLE_GEN_PROMPT = """你是英文影視教學編輯。使用者會貼上一段英文影集／電影台詞（可能含字幕序號與時間軸，請忽略那些）。
請把台詞整理成可互動的學習課程，逐句英翻中並標註教學重點（特別是教科書學不到的口語、俚語、慣用語）。

# 嚴格輸出 JSON（只輸出 JSON，前後不得有任何文字、不得包 markdown code fence）
{
  "id": "短英文 id",
  "title": "依內容取的英文標題",
  "title_zh": "繁中標題",
  "level": "A2 / B1 / B2 / C1 擇一（依台詞難度）",
  "summary": "繁中一句話：這段在演什麼、適合學什麼",
  "sentences": [
    {"en": "原台詞（口語照舊，可略修為完整句）", "zh": "自然繁中翻譯",
     "vocab": {"word": "中文翻譯"}, "phrases": [{"en": "片語/俚語", "zh": "中文 + 語境提示"}]}
  ],
  "grammar": [{"point": "口語/文法重點", "explain": "繁中解說", "examples": ["例 1", "例 2"]}]
}

# 規範
- 盡量保留原台詞順序與內容，逐句翻譯（過短的句子可合併）。
- vocab / phrases 著重「影視口語、俚語、縮寫、慣用語」。
- sentences 最多 12 句（台詞太長就取最精華的前段）。
- grammar 3-5 條，點出口語特徵（縮寫如 gonna/wanna、省略主詞、語氣詞等）。
"""


def _clean_subtitle_text(raw: str) -> str:
    """清理字幕：移除 SRT 序號、時間軸（含 --> 的行）、HTML 標籤與空行。"""
    out = []
    for ln in raw.splitlines():
        s = ln.strip()
        if not s or s.isdigit() or "-->" in s:
            continue
        s = re.sub(r"<[^>]+>", "", s)
        if s:
            out.append(s)
    return "\n".join(out)


def _gen_subtitle_lesson(raw_text: str, level: str, tier: str) -> dict:
    """把貼上的英文台詞／字幕轉成一篇互動學習課程（結構同 readings 條目）。"""
    cleaned = _clean_subtitle_text(raw_text)[:4000]  # 限長度避免超出 token
    text = _llm_generate(SUBTITLE_GEN_PROMPT,
                         f"程度參考：{level}\n台詞：\n{cleaned}", tier, max_tokens=6000)
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise RuntimeError(f"Gemini 回應內無 JSON：{text[:200]}")
    return json.loads(m.group(0))


DIALOGUE_GEN_PROMPT = """你是英文會話教材編輯。使用者給「情境主題 + 程度」，產出一段自然的英文情境對話。

# 嚴格輸出 JSON（只輸出 JSON，前後不得有任何文字、不得包 markdown code fence）
{
  "id": "短英文 id",
  "title": "繁中情境標題（如：在咖啡廳點餐）",
  "level": "A2 / B1 / B2 / C1 擇一",
  "scene": "繁中一句話描述對話場景",
  "lines": [
    {"speaker": "A 或 角色名", "en": "自然口語英文，≤ 18 字/句", "zh": "繁中翻譯"}
  ],
  "grammar": [
    {"point": "口語/文法重點", "explain": "繁中解說", "examples": ["English example 1", "English example 2"]}
  ]
}

# 規範
- lines: 6-10 句（兩人來回對話），口語自然、貼合程度。
- grammar: 2-4 條，點出對話中的實用句型/口語。
"""


def _gen_dialogue_en(topic: str, level: str) -> dict:
    """呼叫 Gemini 產出一段情境對話（結構同 CONVERSATIONS 條目）。"""
    text = _llm_generate(DIALOGUE_GEN_PROMPT, f"情境主題：{topic}\n程度：{level}",
                         next(iter(_MODEL_MAP.keys())), max_tokens=4000)
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise RuntimeError(f"Gemini 回應內無 JSON：{text[:200]}")
    return json.loads(m.group(0))


STORY_GEN_PROMPT = """你是英文短文教材編輯。使用者給「主題 + 程度」，產出一篇自然的英文短篇故事（第一人稱、生活感）。

# 嚴格輸出 JSON（只輸出 JSON，前後不得有任何文字、不得包 markdown code fence）
{
  "id": "短英文 id",
  "title": "English title（4-8 字）",
  "level": "A2 / B1 / B2 / C1 擇一",
  "scene": "繁中一句話描述主題與練到的文法",
  "paragraphs": [
    {"en": "自然英文段落，2-4 句", "zh": "繁中翻譯"}
  ],
  "grammar": [
    {"point": "文法/句型重點", "explain": "繁中解說", "examples": ["English example 1", "English example 2"]}
  ]
}

# 規範
- paragraphs: 3-5 段，依程度遞增句子複雜度（A2 簡單現在式 → C1 進階句型）。
- grammar: 2-4 條，點出文中實用句型。
- 故事要連貫、有畫面、像真實生活。
"""


def _gen_story_en(topic: str, level: str) -> dict:
    """呼叫 Gemini 產出一篇短篇故事（結構同 STORIES 條目）。"""
    text = _llm_generate(STORY_GEN_PROMPT, f"主題：{topic}\n程度：{level}",
                         next(iter(_MODEL_MAP.keys())), max_tokens=4000)
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise RuntimeError(f"Gemini 回應內無 JSON：{text[:200]}")
    return json.loads(m.group(0))


def _gen_reading(topic: str, level: str, tier: str) -> dict:
    """呼叫 Gemini 產出一篇可互動閱讀(結構同 readings.py 條目)。"""
    text = _llm_generate(READING_GEN_PROMPT,
                         f"主題:{topic}\n程度:{level}",
                         tier, max_tokens=6000)
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise RuntimeError(f"Gemini 回應內無 JSON: {text[:200]}")
    return json.loads(m.group(0))


def _render_reading_quiz(passage: dict, uid: str) -> None:
    """閱讀理解測驗：讀完文章後作答並即時批改（主動回憶）。

    uid 為呼叫端傳入的唯一前綴（用迴圈索引），避免不同文章（含 AI 生成、
    可能 id 重複或缺漏）造成 widget key 衝突。
    """
    questions = get_questions(passage.get("id", ""))
    if not questions:
        return
    st.divider()
    st.markdown("##### 🧩 閱讀理解測驗（先別看翻譯，挑戰讀懂了沒）")
    with st.form(key=f"reading_quiz_{uid}"):
        answers = []
        for i, q in enumerate(questions):
            pick = st.radio(f"Q{i + 1}. {q['q']}", q["options"],
                            key=f"rq_{uid}_{i}", index=None)
            answers.append(pick)
        submitted = st.form_submit_button("送出作答")
    if submitted:
        correct = 0
        for i, q in enumerate(questions):
            if answers[i] == q["answer"]:
                correct += 1
                st.success(f"Q{i + 1} ✅ 正解：{q['answer']}")
            else:
                st.error(f"Q{i + 1} ❌ 正確答案：{q['answer']}")
            if q.get("explain"):
                st.caption(f"💡 {q['explain']}")
        score = round(correct / len(questions) * 100)
        st.info(f"得分：{correct} / {len(questions)}（{score}%）")
        # 把閱讀理解分數記進今日統計，供「學習進度」追蹤
        today_entry()["quiz_scores"].append(score)
        save_data()


# 隨機生成用的多元主題池（涵蓋日常／職場／旅行／科技／情感／社會等，讓每次都不同）
_DIALOGUE_TOPICS = [
    "在咖啡廳點餐", "跟同事閒聊週末", "退換貨遇到問題", "跟朋友抱怨工作",
    "看房子跟房東談條件", "面試自我介紹", "看醫生描述症狀", "跟朋友約週末出遊",
    "在餐廳訂位", "問路與指路", "機場辦理登機", "飯店入住與客訴",
    "點外送電話溝通", "跟鄰居打招呼閒聊", "健身房諮詢方案", "銀行開戶詢問",
    "二手物品議價", "跟老師請假", "電話客服處理帳單", "超市結帳對話",
    "計程車上閒聊", "向同事求助", "拒絕推銷", "安慰難過的朋友",
    "第一次約會聊天", "跟室友協調家務", "報名課程詢問", "歸還借的東西",
]

_READING_TOPICS = [
    "搬到新城市的第一週", "第一次養寵物的趣事", "和老朋友久別重逢", "學一項新技能的過程",
    "一次難忘的旅行", "在咖啡廳觀察到的人們", "週末的市場採買", "面試當天的緊張",
    "戒掉一個壞習慣", "一場突如其來的大雨", "深夜的便利商店", "搬家整理舊物的回憶",
    "嘗試一道新料理", "迷路後的意外發現", "和家人的一頓晚餐", "通勤路上的小確幸",
    "一封遲來的信", "換工作的決定", "假日的山林健行", "第一次做志工",
    "手機壞掉的一天", "鄰居之間的小故事", "學外語的挫折與突破", "一個關於夢想的對話",
    "退休後的生活", "城市與鄉村的對比", "科技如何改變購物", "一次失敗帶來的成長",
    "陌生人的善意", "重新拾起的興趣",
]

_STORY_TOPICS = [
    "我的早晨習慣", "一趟難忘的旅行", "我為什麼開始學英文", "我最喜歡的週末",
    "一次搬家的回憶", "養寵物的日子", "和好友的重逢", "學會一道新料理",
    "雨天的小故事", "我的第一份工作", "一個改變我的決定", "深夜的散步",
    "假期計畫", "一封寫給未來的信", "我最珍惜的物品", "克服恐懼的那天",
    "通勤路上的觀察", "和家人的晚餐", "一次志工經驗", "重新整理房間",
    "陌生人的幫助", "迷路的意外收穫", "戒掉壞習慣", "追逐夢想的開始",
]


def _generate_reading_into_session(topic: str, level: str) -> None:
    """用 Gemini 生成一篇閱讀 → 存進永久庫(寫本機+推回GitHub) → 顯示在最上面。

    有 GitHub Token 時，生成的閱讀會永久累積到 readings_bank.json，資料庫越長越大、
    重整也不消失；沒 token 則僅留在本 session。
    """
    with st.spinner(f"Gemini 生成「{topic}」({level})…"):
        new_reading = _gen_reading(topic, level, next(iter(_MODEL_MAP.keys())))
    title = new_reading.get("title", "(無標題)")
    # 不論存檔/推回成敗，一律先把生成結果放進 session，確保使用者一定看得到。
    live = st.session_state.setdefault("live_readings", [])
    live.insert(0, new_reading)
    try:
        ok, info = _persist_reading(new_reading)  # 寫本機 + 推回 GitHub
    except Exception as e:  # noqa: BLE001 - 存檔出錯絕不影響「已生成」
        ok, info = False, f"{type(e).__name__}: {e}"
    if ok:
        st.session_state["_reading_toast"] = f"{title}（已永久存入資料庫）"
    else:
        st.session_state["_reading_toast"] = f"{title}（已生成，但永久保存失敗：{info}）"


def view_subtitles() -> None:
    """🎬 影視字幕學習：貼上英文台詞/字幕 → AI 逐句英翻中 + 教口語/俚語/文法。"""
    with st.expander("💡 這是什麼？怎麼用？", expanded=False):
        st.markdown(
            "**影視字幕學習**＝把真實影集／電影的英文台詞變成互動課程。\n\n"
            "1. 貼上一段英文台詞，或直接貼 `.srt` 字幕內容（時間軸會自動忽略）\n"
            "2. 按「🎬 生成字幕課程」→ AI **逐句英翻中** + 標出**口語／俚語／慣用語**與文法\n"
            "3. 可整段**加入複習（SRS）**，也會**存進閱讀庫永久累積**\n\n"
            "💡 影視台詞最道地，是教科書學不到的真實英文。"
        )

    api_key = get_api_key()
    if st.session_state.pop("_sub_saved", None):
        st.success("已生成並存進閱讀庫（可在「📚 互動閱讀」重看，資料庫持續長大）。")

    if not api_key:
        st.warning("需要 Gemini API 金鑰才能生成。請至 sidebar 確認金鑰狀態。")
    else:
        raw = st.text_area("貼上英文台詞 / 字幕（.srt 也可）", height=200,
                           placeholder="例：\nI'm gonna make him an offer he can't refuse.\nYou talking to me?\n\n（可直接貼字幕檔內容，序號與時間軸會自動忽略）",
                           key="sub_raw")
        level = st.session_state.get("en_level", "B1")
        col1, col2 = st.columns([2, 3])
        col1.caption(f"程度參考：**{level}**（左側可改）")
        if col2.button("🎬 生成字幕課程", type="primary", use_container_width=True,
                       disabled=not (raw and raw.strip())):
            try:
                with st.spinner("AI 逐句翻譯 + 教學中…"):
                    lesson = _gen_subtitle_lesson(raw, level, next(iter(_MODEL_MAP.keys())))
                ok, _info = _persist_reading(lesson)
                st.session_state["_sub_result"] = lesson
                st.session_state["_sub_saved"] = ok
                st.rerun()
            except Exception as e:  # noqa: BLE001
                st.error(_friendly_gen_error(f"{type(e).__name__}: {e}"))

    lesson = st.session_state.get("_sub_result")
    if lesson and lesson.get("sentences"):
        st.divider()
        st.markdown(f"#### 🎬 {lesson.get('title', '')}　{lesson.get('title_zh', '')}")
        if lesson.get("summary"):
            st.caption(lesson["summary"])
        _embed_html(_build_reading_html(lesson),
                    height=140 + 80 * len(lesson["sentences"]) + 200)
        if lesson.get("grammar"):
            _render_grammar(lesson["grammar"])
        if st.button(f"➕ 加入 {len(lesson['sentences'])} 句到「🔁 複習」",
                     use_container_width=True, key="sub_add_review"):
            cards = [{"sentence": s["en"], "chinese": s.get("zh", ""),
                      "chunk": s["en"][:40], "context": f"字幕：{lesson.get('title', '')}"}
                     for s in lesson["sentences"] if s.get("en")]
            n = add_cards_to_review(cards)
            save_data()
            st.success(f"已加入 {n} 句到複習清單。")


def view_reading() -> None:
    with st.expander("💡 這是什麼？怎麼用？", expanded=False):
        st.markdown(
            "**互動閱讀本**＝可點字看翻譯、點句子聽朗讀、看中文對照的互動式閱讀練習。\n\n"
            "**操作**：\n"
            "1. 點開任一篇 → 看英文閱讀正文\n"
            "2. **滑鼠移到單字**：上方跳小視窗顯示中文翻譯\n"
            "3. **點單字**：高亮 + 唸該字（瀏覽器 TTS）\n"
            "4. **點整句**：句子高亮 + 唸該句 + 下方面板顯示「英文 + 🇹🇼 中文翻譯」\n"
            "5. **▶️ 唸整篇**：從頭到尾連讀\n"
            "6. 下方有「💡 多字片語」列出該句的固定搭配，與「📚 文法重點」\n\n"
            "**推薦學法**：\n"
            "1. 先點「唸整篇」聽一遍（不看翻譯）\n"
            "2. 一句一句點，先猜中文 → 再看面板對照\n"
            "3. 滑鼠掃過陌生單字看翻譯\n"
            "4. 看文法重點 → 試造一句"
        )
    # 🤖 AI 即時生成新閱讀
    api_key = get_api_key()
    _toast = st.session_state.pop("_reading_toast", None)
    if _toast:
        st.success(f"已生成新閱讀「{_toast}」，見下方最上面那篇。")

    # 一鍵隨機生成：每按一次自動換主題＋程度，源源不絕的新例子（免自己想主題）
    rc1, rc2 = st.columns([3, 2])
    if rc1.button("🎲 隨機生成一篇新閱讀", disabled=not api_key,
                  use_container_width=True, type="primary",
                  help="自動挑一個主題與程度，生成一篇全新的閱讀。每按一次都不一樣。"):
        used = {r.get("title") for r in st.session_state.get("live_readings", [])}
        pool = [t for t in _READING_TOPICS if t not in used] or _READING_TOPICS
        topic = random.choice(pool)
        level = st.session_state.get("en_level", "B1")
        try:
            _generate_reading_into_session(topic, level)
            st.rerun()
        except Exception as e:  # noqa: BLE001
            st.error(_friendly_gen_error(f"{type(e).__name__}: {e}"))
    live_now = st.session_state.get("live_readings", [])
    rc2.caption(f"🌱 本 session 已生成 **{len(live_now)}** 篇"
                + ("（新的排在最上面）" if live_now else ""))

    with st.expander("✍️ 想指定主題自己生成？", expanded=False):
        if not api_key:
            st.warning("尚未設定 Gemini API 金鑰。請至 sidebar 確認金鑰狀態。")
        col1, col3 = st.columns([5, 2])
        topic = col1.text_input(
            "主題",
            placeholder="例如：搬到新城市的第一週 / 創業失敗的教訓 / 養貓日常",
            key="rd_topic",
        )
        level = st.session_state.get("en_level", "B1")
        if col3.button(f"🚀 生成（{level}）", disabled=not api_key, use_container_width=True):
            try:
                _generate_reading_into_session(topic.strip() or "Daily life", level)
                st.rerun()
            except Exception as e:  # noqa: BLE001
                st.error(_friendly_gen_error(f"{type(e).__name__}: {e}"))
        st.caption("💡 有設定 GITHUB_TOKEN 時，生成的閱讀會永久存進資料庫並越累積越多；"
                   "沒設定則僅留在本次瀏覽。")

    # 渲染順序：先「AI 生成的閱讀」（永久庫 + 本 session，最新在上、去重），再「離線範例範本」
    persisted = list(reversed(load_readings_bank()))   # 檔案後面 append 的較新 → 反轉讓新的在上
    live_readings = st.session_state.get("live_readings", [])
    generated, seen = [], set()
    for p in list(live_readings) + persisted:
        pid = p.get("id") or p.get("title")
        if pid in seen:
            continue
        seen.add(pid)
        generated.append(p)
    if generated:
        st.markdown(f"### 🌱 AI 生成的閱讀（已累積 **{len(generated)}** 篇，會持續長大）")
    all_passages = generated + list(READINGS)
    for idx, passage in enumerate(all_passages):
        if idx == len(generated):
            st.markdown("### 📚 範例閱讀（離線範本，固定不變）")
        # 防呆：AI 生成結果若缺關鍵欄位就跳過，不讓整頁崩潰
        if not (passage.get("title") and isinstance(passage.get("sentences"), list)
                and passage["sentences"]):
            continue
        with st.expander(
            f"**{passage['title']}**　·　{passage.get('title_zh','')}　·　"
            f"程度 {passage.get('level','?')}　·　{passage.get('summary','')}"
        ):
            _embed_html(_build_reading_html(passage),
                        height=140 + 80 * len(passage["sentences"]) + 200)

            st.markdown("##### 💡 多字片語（每句的固定搭配）")
            for i, s in enumerate(passage["sentences"], 1):
                phrases = s.get("phrases") or []
                if not phrases:
                    continue
                with st.container(border=True):
                    st.caption(f"句 {i}：{s.get('en', '')}")
                    for p in phrases:
                        if isinstance(p, dict):
                            st.markdown(f"　- `{p.get('en', '')}` — {p.get('zh', '')}")
                        else:
                            st.markdown(f"　- {p}")

            st.divider()
            _render_grammar(passage.get("grammar", []))

            _render_reading_quiz(passage, uid=str(idx))

            if st.button(
                f"➕ 加入 {len(passage['sentences'])} 句到「🔁 複習」",
                key=f"add_reading_{idx}",
                use_container_width=True,
            ):
                cards = [
                    {"sentence": s.get("en", ""), "chinese": s.get("zh", ""),
                     "chunk": s.get("en", "")[:40], "context": f"閱讀：{passage.get('title','')}"}
                    for s in passage["sentences"] if s.get("en")
                ]
                n = add_cards_to_review(cards)
                st.success(f"已加入 {n} 句到複習清單。")


def _collect_listening_pool() -> list:
    """從現有素材抽英中對照句:vocab_bank example + SEED MNEMONICS + 口說範本 +
    故事段落 + 互動閱讀句子。每筆 {en, zh, source}。"""
    pool = []
    # SEED MNEMONICS
    for w, m in MNEMONICS.items():
        if m.get("example_en") and m.get("example_zh"):
            pool.append({"en": m["example_en"], "zh": m["example_zh"],
                         "source": f"SEED · {w}"})
    # vocab_bank
    for w, e in load_vocab_bank().items():
        if e.get("example_en") and e.get("example_zh"):
            pool.append({"en": e["example_en"], "zh": e["example_zh"],
                         "source": f"單字庫 · {w}"})
    # 口說範本 - 對話
    for conv in CONVERSATIONS:
        for line in conv.get("lines", []):
            if line.get("en") and line.get("zh"):
                pool.append({"en": line["en"], "zh": line["zh"],
                             "source": f"對話 · {conv.get('title','')}"})
    # 口說範本 - 故事
    for story in STORIES:
        for p in story.get("paragraphs", []):
            if p.get("en") and p.get("zh"):
                pool.append({"en": p["en"], "zh": p["zh"],
                             "source": f"故事 · {story.get('title','')}"})
    # 互動閱讀
    for passage in READINGS:
        for s in passage.get("sentences", []):
            if s.get("en") and s.get("zh"):
                pool.append({"en": s["en"], "zh": s["zh"],
                             "source": f"閱讀 · {passage.get('title','')}"})
    return pool


def view_listening() -> None:
    with st.expander("💡 這是什麼？怎麼用？", expanded=False):
        st.markdown(
            "**聽力訓練**＝從你現有的學習素材(SEED / 單字庫 / 對話 / 故事 / 互動閱讀)"
            "隨機抽句做聽寫練習。\n\n"
            "**兩種模式**:\n"
            "1. **🇹🇼 看中文聽英文**:先看中文 → 按 ▶️ 聽英文 → 心裡跟讀 → 翻面對答案\n"
            "2. **🇬🇧 純聽寫**:只聽不看 → 嘗試在腦中還原 → 翻面看英文+中文\n\n"
            "**最有效學法**:**Shadowing 跟讀**——聽一遍 → 暫停模仿 → 比對你跟原音的差異。"
        )
    pool = _collect_listening_pool()
    if not pool:
        st.info("素材池是空的(SEED MNEMONICS 應有 20 句,看看是否載入正常)。")
        return

    # session 狀態:打亂後的順序 + 當前索引
    pool_sig = (len(pool), pool[0]["en"][:20])
    if st.session_state.get("_listen_sig") != pool_sig:
        import random
        shuffled = list(pool)
        random.shuffle(shuffled)
        st.session_state["_listen_pool"] = shuffled
        st.session_state["_listen_sig"] = pool_sig
        st.session_state["_listen_idx"] = 0
        st.session_state["_listen_reveal"] = False

    shuffled = st.session_state["_listen_pool"]
    idx = st.session_state["_listen_idx"] % len(shuffled)
    item = shuffled[idx]
    reveal = st.session_state.get("_listen_reveal", False)

    st.caption(f"📚 共 {len(shuffled)} 句　·　第 {idx + 1} 句　·　來源:{item['source']}")
    mode = st.radio("模式", ["🇹🇼 看中文聽英文", "🇬🇧 純聽寫(英文翻中)"],
                    horizontal=True, key="_listen_mode")

    en_js = _esc_js(item["en"])
    play_btn = (
        f'<button onclick="'
        f'const u=new SpeechSynthesisUtterance(\'{en_js}\');'
        f'u.lang=\'en-US\'; u.rate=__RATE__;'
        f'speechSynthesis.cancel(); speechSynthesis.speak(u);'
        f'" style="padding:14px 28px; font-size:18px; border:none; '
        f'border-radius:999px; cursor:pointer; background:__BG__; color:#fff; '
        f'font-weight:700; margin:6px 6px;">__LABEL__</button>'
    )
    slow_btn = play_btn.replace("__RATE__", "0.7").replace("__BG__", "#0ea5e9").replace("__LABEL__", "🐌 慢速")
    norm_btn = play_btn.replace("__RATE__", "0.92").replace("__BG__", "#10b981").replace("__LABEL__", "▶️ 正常速度")
    fast_btn = play_btn.replace("__RATE__", "1.1").replace("__BG__", "#f59e0b").replace("__LABEL__", "🐇 快")

    if mode.startswith("🇹🇼"):
        card_inner = (
            f'<div style="font-size:24px; font-weight:700; color:#312e81; '
            f'text-align:center; margin-bottom:14px;">'
            f'🇹🇼 {_html.escape(item["zh"])}</div>'
        )
    else:
        card_inner = (
            '<div style="font-size:18px; color:#64748b; text-align:center; margin-bottom:14px;">'
            '🎧 聽下方音檔,試著在腦中還原英文;按「翻面」對答案</div>'
        )
    html = (
        f'<div style="padding:20px; background:#f8fafc; border:2px solid #4f46e5; '
        f'border-radius:16px; font-family:-apple-system,sans-serif; text-align:center;">'
        + card_inner +
        f'<div>{slow_btn}{norm_btn}{fast_btn}</div></div>'
    )
    _embed_html(html, 220)

    c1, c2, c3 = st.columns(3)
    if c1.button("← 上一句", use_container_width=True, key="_listen_prev"):
        st.session_state["_listen_idx"] = (idx - 1) % len(shuffled)
        st.session_state["_listen_reveal"] = False
        st.rerun()
    if c2.button(("🙈 隱藏答案" if reveal else "🔄 翻面看答案"),
                 use_container_width=True, type="primary", key="_listen_flip"):
        st.session_state["_listen_reveal"] = not reveal
        st.rerun()
    if c3.button("下一句 →", use_container_width=True, key="_listen_next"):
        st.session_state["_listen_idx"] = (idx + 1) % len(shuffled)
        st.session_state["_listen_reveal"] = False
        st.rerun()

    if reveal:
        with st.container(border=True):
            st.markdown(f"**🇬🇧 英文**:{item['en']}")
            st.caption(f"🇹🇼 中文:{item['zh']}")
            if st.button("➕ 加入複習(SRS 排程)", key="_listen_addrev"):
                added = add_cards_to_review([{
                    "sentence": item["en"], "chinese": item["zh"],
                    "chunk": item["en"][:40], "context": f"聽力 · {item['source']}",
                }])
                st.success(f"已加入 {added} 句到複習清單。")


def view_vocab_bank() -> None:
    with st.expander("💡 這是什麼？怎麼用？", expanded=False):
        st.markdown(
            "**單字庫**＝可成長到 4000+ 字的單字資料庫。每筆都有 8 欄完整資訊：\n"
            "中文意思、KK 音標、自然發音、台味諧音、圖像聯想、口語例句、中文翻譯、用法說明。\n\n"
            "**怎麼用**：\n"
            "1. 展開「🤖 用 AI 在雲端即時生成」面板，按「🚀 開始生成」"
            "（一次 5–50 字，從 `scripts/vocab_wordlist.txt` 取尚未做過的字）\n"
            "2. 想永久保存：勾選「✅ 生成完自動推回 GitHub」（需在 Cloud Secrets 設 `GITHUB_TOKEN`）"
            "或手動按「⬇️ 下載」覆蓋 repo 的 `vocab_bank.json`\n"
            "3. 這裡生成的字會**自動出現在「🗂️ 單字學習」flashcard**（deck 數字增加）\n"
            "4. 下方搜尋框可查英文/中文/諧音；分頁瀏覽\n\n"
            "**換 4000 字詞表**：替換 `scripts/vocab_wordlist.txt` 為正版 COCA / TOEIC / Oxford 4000，再按生成。"
        )
    file_bank = load_vocab_bank()
    live_bank = st.session_state.setdefault("live_bank", {})
    synced = st.session_state.get("synced_bank", {})
    bank = {**file_bank, **synced, **live_bank}
    api_key = get_api_key()

    # 生成後面板維持展開（剛生成完 _just_generated 為真），讓使用者看到結果橫幅
    _open = (not bank) or st.session_state.get("_just_generated", False)
    with st.expander("🤖 用 AI 在雲端即時生成（無需本機）", expanded=_open):
        # 持久橫幅：上一輪生成結果（rerun 不會洗掉）
        gr = st.session_state.pop("_gen_result_banner", None)
        if gr:
            if gr["added"]:
                st.success(f"✅ 上次生成新增 **{gr['added']}** 字："
                           f"{gr['preview']}　·　庫存現為 **{gr['total']}** 字")
            else:
                st.warning(gr.get("note") or "上次沒有新增字（可能詞表這批已生過或被去重）。")
        st.session_state["_just_generated"] = False
        if not api_key:
            st.warning(
                "尚未設定 Gemini API 金鑰。請至 Streamlit Cloud → **Manage app → "
                "Settings → Secrets** 加入下列其中一種寫法後重新部署：\n\n"
                "```toml\n"
                "# 單一 key:\n"
                "GEMINI_API_KEY = \"AIzaSy...\"\n\n"
                "# 多 key 輪轉(撞 429 自動換下一把):\n"
                "GEMINI_API_KEYS = [\"AIzaSy...1\", \"AIzaSy...2\", \"AIzaSy...3\"]\n"
                "```\n"
                "取得方式：https://aistudio.google.com/apikey"
            )
        else:
            n_total = len(get_all_api_keys())
            n_avail = sum(1 for k in get_all_api_keys()
                          if k not in st.session_state.get("_exhausted_keys", set()))
            st.caption(f"供應商:**Google Gemini**　·　偵測到 **{n_total} 把 key**"
                       f"({n_avail} 把可用)。撞 429 時自動換下一把。")
        col1, col2, col3 = st.columns([2, 2, 2])
        n = col1.number_input("一次生成幾個字", min_value=5, max_value=50, value=20, step=5)
        tier = col2.selectbox("模型", GEN_MODEL_TIERS, index=0)
        gh = get_github_token()
        # 自動推回:有 token 就一律自動推,不再用 checkbox(避免使用者忘記勾)
        auto_push = bool(gh)
        if gh:
            st.caption("🔄 **自動推回**已啟用:生成完會立刻 commit 到 repo,Cloud 重新部署後永久保存。")
        else:
            st.warning(
                "⚠️ 未設 `GITHUB_TOKEN`,生成的字只會留在當前 session,**重新整理就消失**。"
                "若想永久保存,請至 Cloud Secrets 加 `GITHUB_TOKEN = \"github_pat_...\"`,"
                "或每次生成後手動按下方「⬇️ 下載」覆蓋 repo 的 vocab_bank.json 再 push。"
            )
        if col3.button("🚀 生成這批", disabled=not api_key,
                       use_container_width=True, type="primary"):
            try:
                _run_inapp_generation(int(n), tier, auto_push=auto_push)
                st.rerun()
            except Exception as e:  # noqa: BLE001
                msg = str(e)
                if any(h in msg for h in _QUOTA_HINTS):
                    # 解析 retryDelay 與 model name 給具體建議
                    rd = re.search(r"retryDelay['\"]?\s*:\s*['\"]?(\d+)s", msg)
                    mm = re.search(r"model:\s*([\w\-.]+)", msg)
                    qval = re.search(r"quotaValue['\"]?\s*:\s*['\"]?(\d+)", msg)
                    parts = ["⏰ **Gemini 免費額度用完了** — 這是 Google 的每日上限,跟 key 沒問題。"]
                    if mm and qval:
                        parts.append(f"\n當下模型 `{mm.group(1)}` 免費 tier 每日上限 = **{qval.group(1)} 次**。")
                    elif mm:
                        parts.append(f"\n當下模型:`{mm.group(1)}`。")
                    parts.append(
                        "\n\n**📊 各 Gemini 模型免費每日額度(per project per model)**:\n"
                        "| 模型 | RPD | 用途 |\n"
                        "|---|---|---|\n"
                        "| `gemini-2.5-pro` | ~5 | 最強但極少 |\n"
                        "| `gemini-2.5-flash` | ~20 | 平衡 |\n"
                        "| **`gemini-2.5-flash-lite`** | **~200** | 輕量、額度最多 |\n"
                        "| `gemini-2.0-flash` | ~200 | 舊版穩定 |\n\n"
                        "**🛠 解法(任選)**:\n"
                        "1. **上方下拉改選「Flash-Lite」或「2.0 Flash」** ← 額度多 10 倍,**現在馬上能用**\n"
                        "2. 等明天台灣時間 16:00(UTC 0:00)免費額度重置\n"
                        "3. 到 https://aistudio.google.com/apikey 開**新 Google project** 再生一把 key\n"
                        "   (每個 project 有獨立配額,等於額度翻倍)\n"
                        "4. 升級 AI Studio 付費版(約 USD $1-5 可跑完 4000 字)"
                    )
                    if rd:
                        parts.append(f"\n\n(Google 建議等 {rd.group(1)} 秒,但其實是日配額,等到明天才會完全重置)")
                    st.warning("".join(parts))
                elif any(h in msg for h in _TRANSIENT_HINTS):
                    st.warning(
                        "⏳ Google 伺服器當下忙碌(503 UNAVAILABLE)。"
                        "這是 Gemini 服務端問題,跟你的 key 與我的程式都無關。\n\n"
                        "**做法**:\n"
                        "1. 等 30 秒～2 分鐘再按一次(高峰時段常見)\n"
                        "2. 改用 Flash-Lite 或 2.0 Flash(負載比 Pro 輕)\n"
                        "3. 把每批字數調小(從 50 改成 20)"
                    )
                elif "API key not valid" in msg or "API_KEY_INVALID" in msg:
                    st.error(
                        "❌ Google 拒絕了你的 API key（不是 app 抓不到，是 key 本身被拒）。\n\n"
                        "**常見原因（請逐項檢查）**：\n"
                        "1. **key 寫錯 / 多了空白或引號** — 重新到 "
                        "https://aistudio.google.com/apikey 複製一遍\n"
                        "2. **不是 Generative Language API 的 key** — Google Cloud 有多種 key，"
                        "AI Studio 取出來的才能用\n"
                        "3. **專案沒啟用 Generative Language API** — "
                        "https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com\n"
                        "4. **配額用完或計費未設定** — AI Studio 免費額度足夠日常用，但要先在 "
                        "Google Cloud Console 確認專案綁定\n\n"
                        "最簡單的解法：到 https://aistudio.google.com/apikey 按「Create API key in new project」"
                        "完全新開一把貼回 Streamlit Cloud Secrets 試試。"
                    )
                else:
                    st.error(f"生成失敗：{e}")

        # ── 連續生成到目標字數（按一次自動跑多批，撞額度或達標才停）──
        st.divider()
        running = st.session_state.get("_autogen_active", False)
        ac1, ac2 = st.columns([2, 2])
        target = ac1.number_input("🎯 連續生成到（總庫存字數，無上限）",
                                  min_value=len(bank) + 1, max_value=1_000_000,
                                  value=len(bank) + 1000, step=500,
                                  disabled=running or not api_key)
        if not running:
            if ac2.button("🔁 連續生成到目標", disabled=not api_key,
                          use_container_width=True, type="primary"):
                st.session_state["_autogen_active"] = True
                st.session_state["_autogen_target"] = int(target)
                st.session_state["_autogen_batch"] = int(n)
                st.session_state["_autogen_tier"] = tier
                st.session_state["_autogen_stall"] = 0
                st.rerun()
        else:
            if ac2.button("⏹ 停止連續生成", use_container_width=True):
                for k in ("_autogen_active", "_autogen_target", "_autogen_batch",
                          "_autogen_tier", "_autogen_stall"):
                    st.session_state.pop(k, None)
                if auto_push:
                    _push_bank_to_github(silent=True)
                st.rerun()

        st.caption(
            f"詞表 {len(__import__('scripts.generate_vocab', fromlist=['load_wordlist']).load_wordlist())} 字"
            f"　·　已完成 **{len(bank)}** 字"
            f"　·　📁 部署檔 {len(file_bank)} / ☁️ 已推 GitHub {len(synced)} / 🌱 待推 {len(live_bank)}"
        )

        # 連續生成驅動：每次 render 跑一批,未達標就自動 rerun 接著跑
        if st.session_state.get("_autogen_active"):
            tgt = st.session_state.get("_autogen_target", 0)
            batch = st.session_state.get("_autogen_batch", 20)
            atier = st.session_state.get("_autogen_tier", tier)
            st.info(f"🔁 連續生成中… 目前 **{len(bank)}** / 目標 **{tgt}** 字。"
                    "可按「⏹ 停止連續生成」中斷;撞額度會自動停。")
            if len(bank) >= tgt:
                st.success(f"🎉 已達標!庫存 {len(bank)} 字。")
                st.session_state["_autogen_active"] = False
                if auto_push:
                    _push_bank_to_github(silent=True)
                st.rerun()
            else:
                try:
                    # 連續模式下單批不每次推 GitHub(太慢/太多 commit),達標或停止時才推
                    added = _run_inapp_generation(int(batch), atier, auto_push=False)
                except Exception as e:  # noqa: BLE001
                    st.session_state["_autogen_active"] = False
                    if auto_push:
                        _push_bank_to_github(silent=True)
                    st.warning(f"連續生成已停止：{_friendly_gen_error(str(e))}")
                    added = None
                if added is not None:
                    stall = st.session_state.get("_autogen_stall", 0)
                    stall = 0 if added else stall + 1
                    st.session_state["_autogen_stall"] = stall
                    # 連續 2 批沒新增(詞表用罄或全部 key 撞額度)→ 停
                    if stall >= 2:
                        st.session_state["_autogen_active"] = False
                        if auto_push:
                            _push_bank_to_github(silent=True)
                        st.warning("連續生成已停止：連續多批沒有新增字"
                                   "(詞表已生完或今日額度用罄)。已推回目前進度。")
                    import time as _t
                    _t.sleep(0.5)
                    st.rerun()
        if synced:
            st.caption("💡 ☁️ 已推 GitHub 的字本次就看得到；Cloud 下次重新部署後會併入部署檔。")
        last_push = st.session_state.get("_last_push")
        if last_push:
            if last_push["ok"]:
                st.success(f"📤 最後一次推回:{last_push['ts']} 成功 (+{last_push['added']} 字)")
            else:
                st.error(f"📤 最後一次推回:{last_push['ts']} **失敗** — 請手動下載 JSON 保存!")
        # 推回失敗時,把 GitHub API 真實錯誤詳情顯示出來
        err = st.session_state.get("_push_error")
        if err:
            with st.expander("🩺 上次推回失敗的詳細原因(點開看 GitHub 真實回應)",
                             expanded=True):
                st.markdown(
                    f"- **階段**: `{err['stage']}`\n"
                    f"- **HTTP code**: `{err['code']}`\n"
                    f"- **Repo**: `{err['repo']}@{err['branch']}` / `{err['path']}`\n"
                    f"- **Token 開頭…末**: `{err.get('token_prefix','?')}`\n"
                    f"- **Payload 大小**: {err.get('payload_size', 0)} bytes "
                    f"({err.get('live_count', 0)} 個新字)"
                )
                st.markdown("**GitHub 完整回應**(複製整段給開發者看):")
                st.code(err["body"], language="json")
                st.markdown(
                    "**對症修法**(以實際 HTTP code + GitHub 回應的 `message` 為準):\n"
                    "- `401 Bad credentials` → token 過期或寫錯,重生 PAT\n"
                    "- `403 Resource not accessible by personal access token` (常見!) → "
                    "**Fine-grained PAT 陷阱**:你看到 Contents: Read+Write 但實際沒生效。"
                    "**最快解法:改用 Classic PAT**(https://github.com/settings/tokens → "
                    "Generate new token (classic) → 勾 `repo` scope),貼到 Cloud Secrets 的 `GITHUB_TOKEN`。\n"
                    "- `404 Not Found` → repo 名稱大小寫錯,或 token 對該 repo 沒讀取權限\n"
                    "- `409 Conflict` 或 `422 Unprocessable` → sha 衝突,**按下方「🔄 強制重新推回」**\n"
                    "- `405 Method Not Allowed` → branch protection 禁直接 push,需經 PR\n\n"
                    "**Branch protection 檢查**:到 https://github.com/linchen-20200325/my-English-learn/settings/branches "
                    "看 main 是否有 protection rules。"
                )
        # 警告:有未保存的字 → 緊急下載提醒(無論有沒有 token)
        if live_bank:
            st.error(
                f"🚨 **session 有 {len(live_bank)} 個新生成的字尚未真正進 repo!**\n\n"
                "重整瀏覽器或 Cloud 重啟就會消失。立刻按下方「⬇️ 下載合併後 vocab_bank.json」"
                "**先存到本機**,再:\n"
                "1. 把下載的檔覆蓋 repo 內 `vocab_bank.json`\n"
                "2. `git push` → Cloud 重新部署\n\n"
                "或修好 GitHub Token 權限後按「🚀 立即推回」自動推回。"
            )

    if bank:
        col_dl, col_push = st.columns([3, 2])
        merged_json = json.dumps(bank, ensure_ascii=False, indent=2) + "\n"
        col_dl.download_button(
            "⬇️ 下載合併後 vocab_bank.json",
            data=merged_json,
            file_name="vocab_bank.json",
            mime="application/json",
            use_container_width=True,
        )
        if col_push.button(
            "🚀 立即推回 GitHub repo",
            disabled=not get_github_token() or not live_bank,
            use_container_width=True,
            help="把目前 session 內已生成的字 commit 回 repo,永久保存。需設定 GITHUB_TOKEN。"
                 if get_github_token() else
                 "未設 GITHUB_TOKEN secret 或 session 沒有新生成的字。",
        ):
            _push_bank_to_github()
            st.rerun()

        # 強制重試:撞 sha 衝突或暫時性錯誤時,清掉錯誤紀錄後再 push
        if live_bank and get_github_token() and st.session_state.get("_push_error"):
            if st.button("🔄 強制重新推回（重抓 sha 後再試）",
                         use_container_width=True,
                         type="secondary"):
                st.session_state.pop("_push_error", None)
                load_vocab_bank.clear() if hasattr(load_vocab_bank, "clear") else None
                _push_bank_to_github()
                st.rerun()

    if not bank:
        st.info(
            "單字庫是空的。展開上方面板用 AI 即時生成，"
            "或在本機跑 `python scripts/generate_vocab.py` 後 push 回 repo。"
        )
        return

    words = sorted(bank.keys())

    # 📊 統計與去重檢查
    keys_lower = [k.lower() for k in words]
    unique_lower = set(keys_lower)
    dups = [k for k in words if keys_lower.count(k.lower()) > 1]
    incomplete = [k for k in words if not bank[k].get("meaning_zh")]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📚 庫存", len(bank))
    c2.metric("🔤 唯一鍵", len(unique_lower))
    c3.metric("⚠️ 重複", len(dups), delta_color="inverse")
    c4.metric("❓ 缺欄位", len(incomplete), delta_color="inverse")
    if dups:
        st.warning(f"發現大小寫重複: {dups[:10]}")
    if incomplete:
        st.caption(f"⚠️ {len(incomplete)} 字缺 meaning_zh，可能是 Gemini 生成失敗的殘留")

    query = st.text_input(
        "搜尋（英文／中文／諧音）",
        placeholder="輸入單字、諧音、或中文意思片段",
    ).strip().lower()
    if query:
        def _match(w: str) -> bool:
            e = bank[w]
            return (query in w.lower()
                    or query in (e.get("meaning_zh") or "").lower()
                    or query in (e.get("homophone") or "").lower())
        filtered = [w for w in words if _match(w)]
    else:
        filtered = words

    per_page = 10
    total_pages = max(1, (len(filtered) + per_page - 1) // per_page)
    page = st.number_input("頁", min_value=1, max_value=total_pages, value=1, step=1) - 1
    st.caption(f"庫存 {len(bank)} 字　|　符合 {len(filtered)} 字　|　頁 {page + 1}/{total_pages}")

    # 批次把搜尋結果的單字一次納入 SRS 複習（科學記憶排程）
    if filtered and st.button(
        f"🧠 把符合的 {len(filtered)} 字全部加入「🔁 複習」（SRS 排程）",
        use_container_width=True,
    ):
        cards = [vocab_to_card(w, bank[w]) for w in filtered]
        n = add_cards_to_review(cards)
        save_data()
        st.success(f"已加入 {n} 字到複習清單（其餘已在清單中）。到「🔁 複習」開始今日複習。"
                   if n else "這些字已全部在複習清單中。")

    for word in filtered[page * per_page:(page + 1) * per_page]:
        e = bank[word]
        with st.container(border=True):
            c1, c2 = st.columns([2, 5])
            c1.markdown(f"### {word}")
            if c1.button("➕ 加入複習", key=f"bank_rev_{word}", use_container_width=True):
                n = add_cards_to_review([vocab_to_card(word, e)])
                save_data()
                c1.success("已加入！" if n else "已在清單中")
            if e.get("meaning_zh"):
                c1.markdown(f"**{e['meaning_zh']}**")
            if e.get("kk"):
                c1.caption(f"KK `{e['kk']}`")
            if e.get("phonics"):
                c1.caption(f"自然發音 `{e['phonics']}`")
            if e.get("homophone"):
                c2.markdown(f"🔊 諧音 **{e['homophone']}**")
            if e.get("image"):
                c2.markdown(f"🖼️ {e['image']}")
            if e.get("example_en"):
                c2.markdown(f"💬 *{e['example_en']}*")
            if e.get("example_zh"):
                c2.markdown(f"🇹🇼 {e['example_zh']}")
            if e.get("usage_zh"):
                c2.caption(f"💡 {e['usage_zh']}")


# ----------------------------- 主程式 -----------------------------
def main() -> None:
    st.set_page_config(page_title="英文學習儀表板", page_icon="📚", layout="wide")
    inject_css()

    if "data" not in st.session_state:
        st.session_state.data = load_data()
    st.session_state.data.setdefault("lessons", [])  # 相容舊資料
    st.session_state.data.setdefault("review_cards", [])
    st.session_state.setdefault("fc_index", 0)
    st.session_state.setdefault("fc_flipped", False)

    with st.sidebar:
        st.markdown("# 📚 English\nDashboard")
        view = st.radio(
            "導覽",
            ["🏠 總覽", "🗂️ 單字學習", "✏️ 單字測驗", "🔤 字根速記",
             "💬 情境會話", "📚 互動閱讀", "👂 聽力訓練",
             "🎬 影視字幕", "📐 文法生成",
             "📖 單字庫", "📚 我的資料庫", "🔁 複習", "✅ 學習計畫"],
            label_visibility="collapsed",
        )
        st.divider()
        # 🎯 程度：驅動所有 AI 生成（閱讀／字幕／文法／情境）使用此程度
        st.selectbox("🎯 學習程度（AI 生成依此）",
                     ["A2", "B1", "B2", "C1"], index=1, key="en_level",
                     help="A2 基礎 / B1 中級 / B2 中高級 / C1 高級。各頁 AI 生成都會用這個程度。")
        st.divider()
        m1, m2 = st.columns(2)
        m1.metric("🔥 連續天數", compute_streak())
        m2.metric("🔁 待複習", due_count())
        st.divider()
        # API key 偵測 + 輪轉狀態
        all_keys = get_all_api_keys()
        exhausted = st.session_state.setdefault("_exhausted_keys", set())
        n_total = len(all_keys)
        n_avail = sum(1 for k in all_keys if k not in exhausted)
        if n_total:
            st.caption(f"🔑 Gemini key：**{n_avail} / {n_total} 把可用**"
                       + (f"（{n_total - n_avail} 把今日已耗盡）" if n_total > n_avail else ""))
        else:
            st.caption("⚪ 尚未偵測到 Gemini key")

        # 一鍵測試所有 key
        if st.button("🔍 測試所有金鑰", use_container_width=True, disabled=not n_total):
            from google import genai
            from google.genai import types
            results = []
            with st.spinner(f"逐一測試 {n_total} 把 key..."):
                for i, key in enumerate(all_keys, 1):
                    try:
                        client = genai.Client(api_key=key)
                        client.models.generate_content(
                            model="gemini-2.5-flash-lite",
                            contents="hi",
                            config=types.GenerateContentConfig(max_output_tokens=10),
                        )
                        results.append((i, "✅", key[:8] + "…", ""))
                    except Exception as e:  # noqa: BLE001
                        em = str(e)
                        if any(h in em for h in _QUOTA_HINTS):
                            tag, note = "⏰", "今日配額用完"
                            exhausted.add(key)
                        elif "API key not valid" in em or "API_KEY_INVALID" in em:
                            tag, note = "❌", "key 被拒"
                        else:
                            tag, note = "⚠️", f"{type(e).__name__}: {em[:40]}"
                        results.append((i, tag, key[:8] + "…", note))
            st.session_state["_key_test"] = results

        last = st.session_state.get("_key_test")
        if last:
            for i, tag, prefix, note in last:
                st.caption(f"{tag} #{i} `{prefix}` {note}")

        if exhausted and st.button("🔄 重置耗盡標記", use_container_width=True,
                                    help="清掉「今日已耗盡」標記,讓所有 key 再次嘗試。"
                                         "Google 配額重置時(每日 UTC 0:00)用得到。"):
            st.session_state["_exhausted_keys"] = set()
            st.session_state.pop("_key_test", None)
            st.rerun()

        # GitHub Token + 診斷
        ghk = get_github_token()
        if ghk:
            st.caption(f"🟢 GitHub Token `{ghk[:12]}…`")
            st.caption(f"長度 {len(ghk)} 字　·　末 4 字 `…{ghk[-4:]}`")
            if st.button("🔍 測試 GitHub 連線", use_container_width=True,
                         help="逐步測試:讀 token、抓 repo、抓 vocab_bank.json,"
                              "確認真的能寫回。"):
                import urllib.request, urllib.error
                repo = _read_secret("GITHUB_REPO") or "linchen-20200325/my-English-learn"
                branch = _read_secret("GITHUB_BRANCH") or "main"
                results = []
                headers = {"Authorization": f"Bearer {ghk}",
                           "Accept": "application/vnd.github+json",
                           "User-Agent": "english-learn-cloud",
                           "X-GitHub-Api-Version": "2022-11-28"}
                # 0) 顯示送出的 token 樣貌(前 12 字 + 後 4 字 + 是否含奇怪字元)
                import re as _re
                has_weird = bool(_re.search(r'[^A-Za-z0-9_]', ghk))
                results.append((
                    "🔑",
                    f"送出 token = `{ghk[:12]}…{ghk[-4:]}` (長度 {len(ghk)},"
                    f"{'⚠️ 含非英數字元(可能有引號或空白殘留)' if has_weird else '純英數'})"
                ))
                # 1) /user 看 token 是否有效
                try:
                    req = urllib.request.Request("https://api.github.com/user", headers=headers)
                    with urllib.request.urlopen(req, timeout=10) as r:
                        user = json.loads(r.read())
                    results.append(("✅", f"Token 有效,登入者 = **{user.get('login')}**"))
                except urllib.error.HTTPError as e:
                    body = e.read().decode('utf-8', 'replace')[:200]
                    results.append(("❌", f"Token 無效 (HTTP {e.code}):{body}\n\n"
                                          "**對症**:401 = token 寫錯/過期/含雜質;"
                                          "重新到 https://github.com/settings/personal-access-tokens "
                                          "複製貼上。"))
                except Exception as e:
                    results.append(("❌", f"連線錯誤:{type(e).__name__}: {e}"))
                # 2) /repos/<repo> 看 repo 與權限
                try:
                    req = urllib.request.Request(f"https://api.github.com/repos/{repo}", headers=headers)
                    with urllib.request.urlopen(req, timeout=10) as r:
                        repo_info = json.loads(r.read())
                    perms = repo_info.get("permissions", {})
                    full = repo_info.get("full_name", repo)
                    if perms.get("push"):
                        results.append(("ℹ️", f"Repo `{full}` 帳號層級 push={perms.get('push')} "
                                              "(**fine-grained PAT 不一定真的能寫,以下方真實 PUT 為準**)"))
                    else:
                        results.append(("⚠️", f"Repo `{full}` 帳號層級沒寫權限 ({perms})"))
                except urllib.error.HTTPError as e:
                    body = e.read().decode('utf-8', 'replace')[:200]
                    results.append(("❌", f"Repo `{repo}` 找不到 (HTTP {e.code}):{body}\n\n"
                                          "**對症**:404 = token Repository access 沒包含此 repo,"
                                          "或 repo 名稱大小寫錯。"))
                # 3) 抓 vocab_bank.json 看 path 是否對
                current_sha = None
                current_content = None
                try:
                    api = f"https://api.github.com/repos/{repo}/contents/vocab_bank.json?ref={branch}"
                    req = urllib.request.Request(api, headers=headers)
                    with urllib.request.urlopen(req, timeout=10) as r:
                        d = json.loads(r.read())
                    current_sha = d.get('sha', '')
                    current_content = d.get('content', '')
                    results.append(("✅", f"vocab_bank.json @ `{branch}` sha=`{current_sha[:7]}` size={d.get('size','?')}B"))
                except urllib.error.HTTPError as e:
                    body = e.read().decode('utf-8', 'replace')[:200]
                    results.append(("❌", f"抓不到 vocab_bank.json @ {branch} (HTTP {e.code}):{body}"))
                except Exception as e:
                    results.append(("❌", f"{type(e).__name__}: {e}"))
                # 4) 真實 PUT 測試:用既有 sha+content 做 no-op 寫入,確認 PAT 真的能寫
                if current_sha and current_content:
                    try:
                        put_api = f"https://api.github.com/repos/{repo}/contents/vocab_bank.json"
                        put_body = json.dumps({
                            "message": "diagnostic: no-op write test (verifying PAT write permission)",
                            "content": current_content.replace("\n", ""),  # GitHub 不接受換行
                            "sha": current_sha,
                            "branch": branch,
                        }).encode("utf-8")
                        req = urllib.request.Request(
                            put_api, data=put_body, method="PUT",
                            headers={**headers, "Content-Type": "application/json"})
                        with urllib.request.urlopen(req, timeout=15) as r:
                            put_result = json.loads(r.read())
                        commit_sha = put_result.get("commit", {}).get("sha", "")[:7]
                        results.append(("✅", f"**真實 PUT 寫入測試 OK** commit `{commit_sha}` — "
                                              "PAT 真的可以寫,推回應該會成功。"))
                    except urllib.error.HTTPError as e:
                        body = e.read().decode('utf-8', 'replace')[:400]
                        results.append((
                            "❌",
                            f"**真實 PUT 寫入測試失敗 (HTTP {e.code})**:{body}\n\n"
                            "**這代表你的 fine-grained PAT 沒真正獲得 Contents: Write 權限**\n"
                            "(即使上方 step 2 顯示 push=true 也不算,因為那是帳號層級不是 PAT 層級)。\n\n"
                            "**最快解法:改用 Classic PAT(更簡單,不會踩這種坑)**:\n"
                            "1. 到 https://github.com/settings/tokens(注意不是 fine-grained)\n"
                            "2. 點 `Generate new token (classic)`\n"
                            "3. Note 填任意,Expiration 選 No expiration 或 90 天\n"
                            "4. **Scopes 只勾 `repo`** (整個區塊),這會自動包含 contents write\n"
                            "5. 按 Generate token,複製 `ghp_xxxxx`\n"
                            "6. 回 Streamlit Cloud Secrets,把 `GITHUB_TOKEN` 換成這把新 ghp_,save\n"
                            "7. 重新測試"
                        ))
                    except Exception as e:
                        results.append(("❌", f"PUT 測試錯誤:{type(e).__name__}: {e}"))
                st.session_state["_gh_test"] = results
            for tag, msg in st.session_state.get("_gh_test", []):
                st.markdown(f"{tag} {msg}")
            # 📤 雲端備份學習進度(解 Streamlit Cloud 暫存檔系統重啟丟資料的問題)
            if st.button("📤 雲端備份學習進度",
                         use_container_width=True,
                         help="把 dashboard_data.json(學會字、SRS 排程、待辦、目標、"
                              "連續天數等)commit 回 repo,Cloud 重新部署後自動恢復。"):
                if os.path.exists(DATA_FILE):
                    ok = _push_file_to_github(
                        DATA_FILE, "dashboard_data.json",
                        "dashboard_data: 雲端備份學習進度",
                    )
                    if ok:
                        st.session_state["_last_data_backup"] = \
                            datetime.now().strftime("%m/%d %H:%M")
                else:
                    st.caption("尚無 dashboard_data.json 可備份")
            last_bk = st.session_state.get("_last_data_backup")
            if last_bk:
                st.caption(f"💾 上次備份:{last_bk}")
        else:
            st.caption("⚪ GitHub Token 未設（無法自動推回 / 雲端備份）")

    st.title(view)
    st.caption(date.today().strftime("%Y 年 %m 月 %d 日"))

    if view.endswith("總覽"):
        view_overview()
    elif view.endswith("單字學習"):
        view_vocab()
    elif view.endswith("單字測驗"):
        view_quiz()
    elif view.endswith("字根速記"):
        view_morphology()
    elif view.endswith("情境會話"):
        view_scenario()
    elif view.endswith("互動閱讀"):
        view_reading()
    elif view.endswith("聽力訓練"):
        view_listening()
    elif view.endswith("影視字幕"):
        view_subtitles()
    elif view.endswith("文法生成"):
        view_grammar()
    elif view.endswith("單字庫"):
        view_vocab_bank()
    elif view.endswith("複習"):
        view_review()
    elif view.endswith("我的資料庫"):
        view_library()
    elif view.endswith("學習計畫"):
        view_plan()


if __name__ == "__main__":
    main()
