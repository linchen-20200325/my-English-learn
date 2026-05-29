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
        # 諧音縮小放最下方
        homophone_block = (
            f'<div style="margin-top:14px; padding-top:10px; '
            f'border-top:1px solid rgba(255,255,255,.25); font-size:13px; opacity:.78;">'
            f'📣 諧音 {homophone}</div>' if homophone else ""
        )
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
        if homophone: h += 40
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
        st.markdown(
            f"""<div class="phrase-box">
            <div class="en">“{p['en']}”</div>
            <div class="zh">{p['zh']}</div>
            <span class="tag"># {p['tag']}</span></div>""",
            unsafe_allow_html=True,
        )
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
    full_bank = {**file_bank, **live_bank}
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
        with st.form("gen_form", clear_on_submit=False):
            scenario = st.text_input(
                "目標情境",
                placeholder="例如：在咖啡廳跟店員點餐，並反映飲料做錯了",
            )
            model_label = st.selectbox("生成模型", GEN_MODEL_TIERS)
            submitted = st.form_submit_button("生成 ✨", type="primary")

        if submitted:
            if not scenario.strip():
                st.warning("請先輸入情境。")
            else:
                with st.spinner("生成中…"):
                    try:
                        raw = generate_material(scenario.strip(), model_label)
                        mermaid, cards = parse_blocks(raw)
                        st.session_state.gen_result = {
                            "scenario": scenario.strip(),
                            "mermaid": mermaid,
                            "flashcards": cards or [],
                            "raw": raw,
                        }
                    except Exception as e:  # noqa: BLE001 — 對使用者顯示友善訊息
                        st.session_state.gen_result = None
                        st.error(f"生成失敗：{e}")

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
            data["lessons"].append({
                "id": new_id,
                "scenario": result["scenario"],
                "mermaid": result["mermaid"],
                "flashcards": result["flashcards"],
                "created": today_str(),
            })
            save_data()
            st.session_state.gen_result = None
            st.success("已儲存到下方的課程清單。")
            st.rerun()
        if c2.button("➕ 加入複習", use_container_width=True,
                     disabled=not result["flashcards"]):
            n = add_cards_to_review(result["flashcards"])
            save_data()
            st.success(f"已加入 {n} 張到複習清單。" if n else "這些句卡已在複習清單中。")
        if c3.button("🗑️ 清除結果", use_container_width=True):
            st.session_state.gen_result = None
            st.rerun()

    if data["lessons"]:
        st.divider()
        st.markdown("### 📂 已儲存的情境課程")
        for lesson in reversed(data["lessons"]):
            with st.expander(f"📍 {lesson['scenario']}（{lesson.get('created', '')}）"):
                if lesson.get("mermaid"):
                    render_mermaid(lesson["mermaid"])
                if lesson.get("flashcards"):
                    render_flashcards(lesson["flashcards"])
                lc1, lc2 = st.columns(2)
                if lc1.button("➕ 加入複習", key=f"lesson_rev_{lesson['id']}",
                              use_container_width=True,
                              disabled=not lesson.get("flashcards")):
                    n = add_cards_to_review(lesson["flashcards"])
                    save_data()
                    st.success(f"已加入 {n} 張。" if n else "已在複習清單中。")
                if lc2.button("🗑️ 刪除這課", key=f"lesson_del_{lesson['id']}",
                              use_container_width=True):
                    data["lessons"] = [l for l in data["lessons"] if l["id"] != lesson["id"]]
                    save_data()
                    st.rerun()


def view_review() -> None:
    data = st.session_state.data
    deck = data.setdefault("review_cards", [])

    if not deck:
        st.info("複習清單是空的。可從「📖 單字庫」把單字、或「📚 互動閱讀」「🤖 情境生成」"
                "把句卡加入複習，系統會用間隔重複（SRS）幫你科學排程。")
        return

    today = today_str()
    due = [c for c in deck if c.get("due", today) <= today]
    st.caption(f"清單共 {len(deck)} 張，今天到期 {len(due)} 張。")

    if not due:
        nxt = min((c.get("due", today) for c in deck), default=today)
        st.success(f"今天沒有要複習的卡 🎉 下次到期：{nxt}")
        with st.expander("清空複習清單"):
            if st.button("確認清空", type="primary"):
                data["review_cards"] = []
                save_data()
                st.rerun()
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

    tab1, tab2, tab3 = st.tabs(["字首 Prefix", "字中 Root", "字尾 Suffix"])
    for tab, title, items, key in (
        (tab1, "字首 Prefix", PREFIXES, "pre"),
        (tab2, "字中 Root", ROOTS, "root"),
        (tab3, "字尾 Suffix", SUFFIXES, "suf"),
    ):
        with tab:
            options = [f"{it['m']} · {it['zh']}" for it in items]
            picked = st.multiselect(
                f"挑選想看的（不選 = 全部 {len(items)} 個）",
                options,
                key=f"morph_pick_{key}",
                placeholder="例如：anti-, pre-, dis-",
            )
            shown = ([it for it in items
                     if f"{it['m']} · {it['zh']}" in set(picked)]
                     if picked else items)
            render_mermaid(build_mindmap(title, shown),
                           height=520 if len(shown) >= 5 else 360)
            with st.expander("檢視清單"):
                for it in items:
                    st.markdown(f"- **{it['m']}**（{it['zh']}）：{', '.join(it['ex'])}")



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
    if not todo:
        st.success("詞表已全數完成,沒有待補單字。如需更多請編輯 `scripts/vocab_wordlist.txt`。")
        return
    with st.spinner(f"用 Gemini ({tier}) 生成 {len(todo)} 字…"):
        text = _llm_generate(SYSTEM_PROMPT,
                             "請為以下單字生成資料: " + ", ".join(todo),
                             tier, max_tokens=8000)
        entries = extract_json_array(text)
    added, skipped = 0, 0
    new_words = []
    for e in entries:
        ww = (e.get("word") or "").strip().lower()
        if not ww:
            continue
        # 嚴格去重:必須是我們點名的字、未在檔案/session、且 entry 完整
        if (ww in todo_set and ww not in have_lower
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
    merged = {**file_bank, **live}
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
        # 1) GET current sha
        req = urllib.request.Request(f"{api}?ref={branch}", headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            current = json.loads(r.read())
        sha = current["sha"]
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
        # 同步寫回「本機」vocab_bank.json：否則本機檔仍是部署當下的舊版，
        # 清掉 live_bank 後畫面會誤顯示舊字數（使用者回報的「資料庫不會更新」）。
        # 寫本機後 load_vocab_bank 立刻讀到合併結果，數字即時更新；遠端也已是同一份。
        try:
            with open(VOCAB_BANK_FILE, "w", encoding="utf-8") as f:
                f.write(payload_json)
        except OSError:
            pass
        st.session_state["live_bank"] = {}
        load_vocab_bank.clear() if hasattr(load_vocab_bank, "clear") else None
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
    """渲染文法重點區塊。"""
    st.markdown("##### 📚 文法重點")
    for g in items:
        with st.container(border=True):
            st.markdown(f"**🎯 {g['point']}**")
            st.caption(g["explain"])
            for ex in g["examples"]:
                st.markdown(f"　- `{ex}`")


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
    tab1, tab2 = st.tabs([f"🗣️ 情境對話（{len(CONVERSATIONS)} 個）",
                          f"📖 短篇故事（{len(STORIES)} 篇）"])

    with tab1:
        for conv in CONVERSATIONS:
            with st.expander(
                f"**{conv['title']}**　·　程度 {conv['level']}　·　{conv['scene']}",
            ):
                _embed_html(_build_dialogue_html(conv["lines"]),
                            height=120 + 78 * len(conv["lines"]))
                st.divider()
                _render_grammar(conv["grammar"])
                if st.button(f"➕ 加入 {len(conv['lines'])} 句到「🔁 複習」",
                             key=f"add_conv_{conv['id']}", use_container_width=True):
                    cards = [
                        {"sentence": L["en"], "chinese": L["zh"],
                         "chunk": L["en"][:40], "context": f"情境：{conv['title']}"}
                        for L in conv["lines"]
                    ]
                    n = add_cards_to_review(cards)
                    st.success(f"已加入 {n} 句到複習清單。")

    with tab2:
        for story in STORIES:
            with st.expander(f"**{story['title']}**　·　程度 {story['level']}　·　{story['scene']}"):
                _embed_html(_build_story_html(story["paragraphs"]),
                            height=120 + 130 * len(story["paragraphs"]))
                st.divider()
                _render_grammar(story["grammar"])
                if st.button(f"➕ 加入 {len(story['paragraphs'])} 段到「🔁 複習」",
                             key=f"add_story_{story['id']}", use_container_width=True):
                    cards = [
                        {"sentence": p["en"], "chinese": p["zh"],
                         "chunk": p["en"][:40], "context": f"故事：{story['title']}"}
                        for p in story["paragraphs"]
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
        body = _annotate_sentence_html(s["en"], s.get("vocab", {}))
        zh_full = _html.escape(s["zh"])
        en_js = _esc_js(s["en"])
        sentence_blocks.append(
            f'<span class="sentence" data-id="{i}" data-zh="{zh_full}" '
            f'data-en="{_html.escape(s["en"])}" data-enjs="{en_js}">{body}</span> '
        )
    full_text_js = _esc_js(" ".join(s["en"] for s in passage["sentences"]))

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


def _gen_reading(topic: str, level: str, tier: str) -> dict:
    """呼叫 Gemini 產出一篇可互動閱讀(結構同 readings.py 條目)。"""
    text = _llm_generate(READING_GEN_PROMPT,
                         f"主題:{topic}\n程度:{level}",
                         tier, max_tokens=6000)
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise RuntimeError(f"Gemini 回應內無 JSON: {text[:200]}")
    return json.loads(m.group(0))


def _render_reading_quiz(passage: dict) -> None:
    """閱讀理解測驗：讀完文章後作答並即時批改（主動回憶）。"""
    questions = get_questions(passage.get("id", ""))
    if not questions:
        return
    st.divider()
    st.markdown("##### 🧩 閱讀理解測驗（先別看翻譯，挑戰讀懂了沒）")
    with st.form(key=f"reading_quiz_{passage['id']}"):
        answers = []
        for i, q in enumerate(questions):
            pick = st.radio(f"Q{i + 1}. {q['q']}", q["options"],
                            key=f"rq_{passage['id']}_{i}", index=None)
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
    with st.expander("🤖 AI 即時生成新閱讀（無上限，主題自選）", expanded=False):
        if not api_key:
            st.warning("尚未設定 Gemini API 金鑰。請至 sidebar 確認金鑰狀態。")
        col1, col2, col3 = st.columns([4, 2, 2])
        topic = col1.text_input(
            "主題",
            placeholder="例如：搬到新城市的第一週 / 創業失敗的教訓 / 養貓日常",
            key="rd_topic",
        )
        level = col2.selectbox("程度", ["A2", "B1", "B2", "C1"], index=1, key="rd_lvl")
        if col3.button("🚀 生成", disabled=not api_key, use_container_width=True,
                       type="primary"):
            try:
                with st.spinner(f"Gemini 生成「{topic or '日常生活'}」({level})…"):
                    new_reading = _gen_reading(
                        topic.strip() or "Daily life", level,
                        next(iter(_MODEL_MAP.keys()))  # Flash-Lite
                    )
                live = st.session_state.setdefault("live_readings", [])
                live.append(new_reading)
                st.success(f"已新增「{new_reading.get('title', '(無標題)')}」,展開下方閱讀。")
                st.rerun()
            except Exception as e:  # noqa: BLE001
                st.error(f"生成失敗：{type(e).__name__}: {str(e)[:300]}")
        live = st.session_state.get("live_readings", [])
        if live:
            st.caption(f"🌱 本 session 已生成 {len(live)} 篇（重新整理會消失,記得加入複習保留句子）")

    # 渲染 READINGS(靜態) + live_readings(本 session AI 生成)
    all_passages = list(READINGS) + st.session_state.get("live_readings", [])
    for passage in all_passages:
        with st.expander(
            f"**{passage['title']}**　·　{passage.get('title_zh','')}　·　"
            f"程度 {passage['level']}　·　{passage['summary']}"
        ):
            _embed_html(_build_reading_html(passage),
                        height=140 + 80 * len(passage["sentences"]) + 200)

            st.markdown("##### 💡 多字片語（每句的固定搭配）")
            for i, s in enumerate(passage["sentences"], 1):
                phrases = s.get("phrases") or []
                if not phrases:
                    continue
                with st.container(border=True):
                    st.caption(f"句 {i}：{s['en']}")
                    for p in phrases:
                        st.markdown(f"　- `{p['en']}` — {p['zh']}")

            st.divider()
            _render_grammar(passage["grammar"])

            _render_reading_quiz(passage)

            if st.button(
                f"➕ 加入 {len(passage['sentences'])} 句到「🔁 複習」",
                key=f"add_reading_{passage['id']}",
                use_container_width=True,
            ):
                cards = [
                    {"sentence": s["en"], "chinese": s["zh"],
                     "chunk": s["en"][:40], "context": f"閱讀：{passage['title']}"}
                    for s in passage["sentences"]
                ]
                n = add_cards_to_review(cards)
                st.success(f"已加入 {n} 句到複習清單。")


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
    bank = {**file_bank, **live_bank}
    api_key = get_api_key()

    with st.expander("🤖 用 AI 在雲端即時生成（無需本機）", expanded=not bank):
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
        if col3.button("🚀 開始生成", disabled=not api_key,
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
        st.caption(
            f"詞表 {len(__import__('scripts.generate_vocab', fromlist=['load_wordlist']).load_wordlist())} 字"
            f"　·　已完成 {len(bank)} 字"
            f"　·　📁 repo 已存 {len(file_bank)} 字 / 🌱 session 新增 {len(live_bank)} 字"
        )
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
             "🗣️ 口說範本", "📚 互動閱讀", "📖 單字庫", "🤖 情境生成",
             "🔁 複習", "📈 學習進度", "✅ 學習計畫"],
            label_visibility="collapsed",
        )
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
        else:
            st.caption("⚪ GitHub Token 未設（無法自動推回）")

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
    elif view.endswith("口說範本"):
        view_speak_story()
    elif view.endswith("互動閱讀"):
        view_reading()
    elif view.endswith("單字庫"):
        view_vocab_bank()
    elif view.endswith("情境生成"):
        view_generate()
    elif view.endswith("複習"):
        view_review()
    elif view.endswith("學習進度"):
        view_progress()
    elif view.endswith("學習計畫"):
        view_plan()


if __name__ == "__main__":
    main()
