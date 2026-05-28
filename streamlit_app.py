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

## 區塊一：Mermaid 心智圖
用 ```mermaid 區塊製作一個 mindmap，歸納該情境的核心對話流程：
- 根節點：情境名稱
- 主分支：對話階段（例如 開場、核心討論、結語）
- 子節點：實用短句，每個節點嚴格限制在 7 個英文單字以內

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
_MODEL_MAP = {
    "Flash（快速・推薦）": "gemini-2.5-flash",
    "Pro（高品質・慢）": "gemini-2.5-pro",
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


def get_api_key() -> str | None:
    """讀 Gemini key。先試標準名稱(GEMINI_API_KEY / GOOGLE_API_KEY),
    沒中就掃描所有 secrets/環境變數,只要名稱含 GEMINI 或 GOOGLE 就採用,
    讓使用者在 Cloud Secrets 取的名字較寬鬆也能抓到。"""
    for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GEMINI_KEY", "GOOGLE_GENAI_API_KEY"):
        v = _read_secret(name)
        if v:
            return v
    # 寬鬆比對
    for name in _secret_names():
        upper = name.upper()
        if ("GEMINI" in upper or "GOOGLE" in upper) and "API" in upper:
            v = _read_secret(name)
            if v:
                return v
    for name, val in os.environ.items():
        upper = name.upper()
        if val and ("GEMINI" in upper or "GOOGLE" in upper) and "API" in upper:
            return val
    return None


def get_github_token() -> str | None:
    """讀 GitHub PAT,用於自動把 vocab_bank.json commit 回 repo。"""
    return (_read_secret("GITHUB_TOKEN")
            or _read_secret("GH_TOKEN")
            or _read_secret("GITHUB_PAT"))


def _llm_generate(system_prompt: str, user_msg: str, tier: str, max_tokens: int = 2000) -> str:
    """單次生成。tier 對應 _MODEL_MAP 的標籤。"""
    key = get_api_key()
    if not key:
        raise RuntimeError("尚未設定 GEMINI_API_KEY")
    model_id = _MODEL_MAP.get(tier) or next(iter(_MODEL_MAP.values()))

    from google import genai
    from google.genai import types

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


def generate_material(scenario: str, tier: str) -> str:
    return _llm_generate(GEN_SYSTEM_PROMPT, f"Scenario: {scenario}", tier, max_tokens=2000)


def parse_blocks(text: str) -> tuple[str | None, list | None]:
    """從回應中抽出 mermaid 圖與 flashcards JSON。"""
    mermaid = None
    cards = None
    m = re.search(r"```mermaid\s*(.*?)```", text, re.DOTALL)
    if m:
        mermaid = m.group(1).strip()
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
        homophone = _html.escape(mn.get("homophone", ""))
        kk = _html.escape(mn.get("kk", ""))
        phonics = _html.escape(mn.get("phonics", ""))
        tts_word = _tts_button_html(
            word["word"], 0.9,
            "margin-top:18px; padding:10px 22px; font-size:16px; border:none; "
            "border-radius:999px; cursor:pointer; background:rgba(255,255,255,.28); "
            "color:#fff; font-weight:600;",
            "🔊 唸這個字",
        )
        homophone_block = (
            f'<div style="font-size:28px; margin-top:12px; opacity:.95; '
            f'letter-spacing:1px;">📣 {homophone}</div>' if homophone else ""
        )
        kk_block = (
            f'<span>KK <code style="background:rgba(255,255,255,.18); '
            f'padding:2px 8px; border-radius:6px;">{kk}</code></span>' if kk else ""
        )
        ph_block = (
            f'<span>自然發音 <code style="background:rgba(255,255,255,.18); '
            f'padding:2px 8px; border-radius:6px;">{phonics}</code></span>' if phonics else ""
        )
        html = f"""
        <div style="background:linear-gradient(135deg,#6366f1,#8b5cf6); color:#fff;
                    border-radius:16px; padding:30px 24px; text-align:center;
                    font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;">
            <div style="font-size:44px; font-weight:800; letter-spacing:0.5px;">{w_en}</div>
            {homophone_block}
            <div style="margin-top:16px; display:flex; justify-content:center;
                        gap:18px; flex-wrap:wrap; font-size:15px; opacity:.92;">
                {kk_block}
                {ph_block}
            </div>
            {tts_word}
        </div>
        """
        _embed_html(html, 300 if homophone else 230)
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
    html = f"""
    <div style="background:#f8fafc; color:#312e81; border:2px solid #4f46e5;
                border-radius:16px; padding:22px;
                font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;">
        <div style="font-size:32px; font-weight:800; text-align:center;">{meaning}</div>
        {image_block}
        {example_block}
        {usage_block}
    </div>
    """
    # 動態高度估計
    h = (130 + (50 if image else 0)
         + (60 if example else 0)
         + (40 if example_zh else 0)
         + (50 if usage else 0))
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
        st.session_state.fc_index %= len(deck)
        idx = st.session_state.fc_index
        w = deck[idx]
        is_bank_only = isinstance(w["id"], str) and w["id"].startswith("bank:")
        st.caption(
            f"{idx + 1} / {len(deck)}"
            + (f"　·　共 {len(full_bank)} 字來自單字庫" if full_bank else "")
        )
        mn = MNEMONICS.get(w["word"]) or full_bank.get(w["word"])
        render_flashcard(w, mn, st.session_state.fc_flipped)
        # 每個單字都畫字首/字根/字尾心智圖(無詞素時退化為純字幹)
        decomp = decompose_word(w["word"])
        if decomp:
            st.caption("🧩 字首／字根／字尾拆解")
            render_mermaid(build_word_mindmap(w["word"], decomp), height=260)

        b1, b2, b3, b4 = st.columns(4)
        if b1.button("← 上一個", use_container_width=True):
            st.session_state.fc_index = (idx - 1) % len(deck)
            st.session_state.fc_flipped = False
            st.rerun()
        if b2.button("🔄 翻面", use_container_width=True):
            st.session_state.fc_flipped = not st.session_state.fc_flipped
            st.rerun()
        learn_label = ("（單字庫，到清單區管理）" if is_bank_only
                       else ("↩︎ 取消學會" if w["learned"] else "✅ 標記學會"))
        if b3.button(learn_label, use_container_width=True, disabled=is_bank_only):
            toggle_learned(w["id"])
            st.rerun()
        if b4.button("下一個 →", use_container_width=True):
            st.session_state.fc_index = (idx + 1) % len(deck)
            st.session_state.fc_flipped = False
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
    st.caption("輸入一個生活情境，AI 會產生對話心智圖與可複習的句卡（採用詞塊與高頻口語）。")

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
            with st.expander("檢視 Mermaid 原始碼"):
                st.code(result["mermaid"], language="text")
        else:
            st.info("未能解析出心智圖。")

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
        st.info("複習清單是空的。到「🤖 情境生成」把句卡加入複習。")
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
    st.caption("離線字根字首字尾心智圖 + SEED 單字台味諧音速記，完全不需 API。")

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
    try:
        with open(VOCAB_BANK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def load_vocab_bank() -> dict:
    """讀取 vocab_bank.json;以檔案 mtime 當 cache key,檔案變動會自動失效。"""
    try:
        mtime = os.path.getmtime(VOCAB_BANK_FILE)
    except OSError:
        mtime = 0.0
    return _load_vocab_bank_cached(mtime)


def _run_inapp_generation(n: int, tier: str, auto_push: bool = False) -> None:
    """雲端內用 Gemini 生成 N 字資料,寫進 st.session_state.live_bank。
    嚴格去重:已在檔案或 session 內的字不會重新生成,Gemini 回多的字也會丟掉。"""
    from scripts.generate_vocab import (SYSTEM_PROMPT, extract_json_array,
                                        load_wordlist)
    file_bank = load_vocab_bank()
    live = st.session_state.setdefault("live_bank", {})
    have = {**file_bank, **live}
    wordlist = load_wordlist()
    todo = [w for w in wordlist if w not in have][:n]
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
    for e in entries:
        ww = (e.get("word") or "").strip().lower()
        if not ww:
            continue
        # 嚴格去重:必須是我們點名的字,且未在檔案/session 內
        if ww in todo_set and ww not in have and ww not in live:
            live[ww] = e
            added += 1
        else:
            skipped += 1
    msg = f"已生成 {added} 字（暫存於 session）"
    if skipped:
        msg += f"，去重略過 {skipped} 字"
    st.success(msg)
    if auto_push:
        _push_bank_to_github(silent=False)


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

    repo = _read_secret("GITHUB_REPO") or "linchen-20200325/my-english-learn"
    branch = _read_secret("GITHUB_BRANCH") or "main"
    path = "vocab_bank.json"

    file_bank = load_vocab_bank()
    live = st.session_state.get("live_bank", {})
    merged = {**file_bank, **live}
    payload_json = json.dumps(merged, ensure_ascii=False, indent=2) + "\n"

    api = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"Bearer {token}",
               "Accept": "application/vnd.github+json",
               "User-Agent": "english-learn-cloud"}
    try:
        req = urllib.request.Request(f"{api}?ref={branch}", headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            current = json.loads(r.read())
        sha = current["sha"]
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
            st.success(f"✅ 已推回 GitHub commit `{commit_sha}` 到 `{repo}@{branch}`。"
                       "Cloud 將自動重新部署後永久保存。")
        # 清掉 live(已落地)與檔案快取
        st.session_state["live_bank"] = {}
        load_vocab_bank.clear() if hasattr(load_vocab_bank, "clear") else None
        return True
    except urllib.error.HTTPError as e:
        if not silent:
            st.error(f"推回失敗（HTTP {e.code}）：{e.read().decode('utf-8', 'replace')[:300]}")
        return False
    except Exception as e:  # noqa: BLE001
        if not silent:
            st.error(f"推回失敗：{type(e).__name__}: {e}")
        return False


def view_vocab_bank() -> None:
    file_bank = load_vocab_bank()
    live_bank = st.session_state.setdefault("live_bank", {})
    bank = {**file_bank, **live_bank}
    api_key = get_api_key()

    with st.expander("🤖 用 AI 在雲端即時生成（無需本機）", expanded=not bank):
        if not api_key:
            st.warning(
                "尚未設定 Gemini API 金鑰。請至 Streamlit Cloud → **Manage app → "
                "Settings → Secrets** 加入下列一行後重新部署：\n\n"
                "```\nGEMINI_API_KEY = \"你的_key\"\n```\n"
                "取得方式：https://aistudio.google.com/apikey\n\n"
                "如已設定但這裡仍顯示未偵測，請看左側 sidebar「偵錯：列出 secrets 名稱」核對。"
            )
        else:
            st.caption(f"供應商：**Google Gemini**　·　已偵測 key `{api_key[:8]}…`")
        col1, col2, col3 = st.columns([2, 2, 2])
        n = col1.number_input("一次生成幾個字", min_value=5, max_value=50, value=20, step=5)
        tier = col2.selectbox("模型", GEN_MODEL_TIERS, index=0)
        auto_push = st.checkbox(
            "✅ 生成完自動推回 GitHub repo（永久保存，需 GITHUB_TOKEN）",
            value=bool(get_github_token()),
            disabled=not get_github_token(),
            help="勾選後每次生成完會用 GitHub Contents API 把 vocab_bank.json commit 回 repo。"
                 "需在 Cloud Secrets 設 GITHUB_TOKEN（PAT，含 repo 寫權限）。",
        )
        if col3.button("🚀 開始生成", disabled=not api_key,
                       use_container_width=True, type="primary"):
            try:
                _run_inapp_generation(int(n), tier, auto_push=auto_push)
                st.rerun()
            except Exception as e:  # noqa: BLE001
                st.error(f"生成失敗：{e}")
        st.caption(
            f"詞表 {len(__import__('scripts.generate_vocab', fromlist=['load_wordlist']).load_wordlist())} 字"
            f"　·　已完成 {len(bank)} 字"
            f"　·　檔案 {len(file_bank)} 字 / session 暫存 {len(live_bank)} 字"
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

    if not bank:
        st.info(
            "單字庫是空的。展開上方面板用 AI 即時生成，"
            "或在本機跑 `python scripts/generate_vocab.py` 後 push 回 repo。"
        )
        return

    words = sorted(bank.keys())
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

    for word in filtered[page * per_page:(page + 1) * per_page]:
        e = bank[word]
        with st.container(border=True):
            c1, c2 = st.columns([2, 5])
            c1.markdown(f"### {word}")
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
             "📖 單字庫", "🤖 情境生成", "🔁 複習", "📈 學習進度", "✅ 學習計畫"],
            label_visibility="collapsed",
        )
        st.divider()
        m1, m2 = st.columns(2)
        m1.metric("🔥 連續天數", compute_streak())
        m2.metric("🔁 待複習", due_count())
        st.divider()
        # API key 狀態(讓使用者一眼看到 Cloud Secrets 是否有抓到)
        gem = get_api_key()
        ghk = get_github_token()
        st.caption(f"Gemini API：{'🟢 已偵測 ' + gem[:6] + '…' if gem else '🔴 未設定'}")
        st.caption(f"GitHub Token：{'🟢 已偵測' if ghk else '⚪ 未設定（無法自動推回）'}")
        with st.expander("偵錯：列出 secrets 名稱"):
            names = _secret_names()
            if names:
                st.write(names)
            else:
                st.caption("st.secrets 為空（本機無 .streamlit/secrets.toml）")
            env_match = [n for n in os.environ
                         if any(k in n.upper() for k in ("GEMINI", "GOOGLE", "GITHUB", "ANTHROPIC"))]
            if env_match:
                st.write({"env vars": env_match})

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
