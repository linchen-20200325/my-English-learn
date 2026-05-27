"""英文學習儀表板 — Streamlit 版

執行：streamlit run streamlit_app.py
資料以本機 JSON 檔 (dashboard_data.json) 持久化。
"""

import json
import os
import random
import sys
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data import SEED_WORDS, DAILY_PHRASES, DEFAULT_WEEKLY_PLAN

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard_data.json")
WEEKDAY_ZH = ["一", "二", "三", "四", "五", "六", "日"]  # Monday=0


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

    st.markdown("### 🃏 單字卡")
    if not words:
        st.info("目前沒有單字，請到下方新增。")
    else:
        st.session_state.fc_index %= len(words)
        idx = st.session_state.fc_index
        w = words[idx]
        st.caption(f"{idx + 1} / {len(words)}")
        if st.session_state.fc_flipped:
            st.markdown(
                f"""<div class="flash-card back"><div class="meaning">{w['meaning']}</div>
                <div class="example">{w.get('example', '')}</div></div>""",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""<div class="flash-card"><div class="word">{w['word']}</div></div>""",
                unsafe_allow_html=True,
            )

        b1, b2, b3, b4 = st.columns(4)
        if b1.button("← 上一個", use_container_width=True):
            st.session_state.fc_index = (idx - 1) % len(words)
            st.session_state.fc_flipped = False
            st.rerun()
        if b2.button("🔄 翻面", use_container_width=True):
            st.session_state.fc_flipped = not st.session_state.fc_flipped
            st.rerun()
        learn_label = "↩︎ 取消學會" if w["learned"] else "✅ 標記學會"
        if b3.button(learn_label, use_container_width=True):
            toggle_learned(w["id"])
            st.rerun()
        if b4.button("下一個 →", use_container_width=True):
            st.session_state.fc_index = (idx + 1) % len(words)
            st.session_state.fc_flipped = False
            st.rerun()

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
    st.markdown("### ✏️ 單字測驗")

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


# ----------------------------- 主程式 -----------------------------
def main() -> None:
    st.set_page_config(page_title="英文學習儀表板", page_icon="📚", layout="wide")
    inject_css()

    if "data" not in st.session_state:
        st.session_state.data = load_data()
    st.session_state.setdefault("fc_index", 0)
    st.session_state.setdefault("fc_flipped", False)

    with st.sidebar:
        st.markdown("# 📚 English\nDashboard")
        view = st.radio(
            "導覽",
            ["🏠 總覽", "🗂️ 單字學習", "✏️ 單字測驗", "📈 學習進度", "✅ 學習計畫"],
            label_visibility="collapsed",
        )
        st.divider()
        st.metric("🔥 連續學習天數", compute_streak())

    st.title(view)
    st.caption(date.today().strftime("%Y 年 %m 月 %d 日"))

    if view.endswith("總覽"):
        view_overview()
    elif view.endswith("單字學習"):
        view_vocab()
    elif view.endswith("單字測驗"):
        view_quiz()
    elif view.endswith("學習進度"):
        view_progress()
    elif view.endswith("學習計畫"):
        view_plan()


if __name__ == "__main__":
    main()
