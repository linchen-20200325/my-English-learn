// 英文學習儀表板 - 主程式
// 所有資料存於 localStorage，無需後端。

const STORE_KEY = "englishDashboard.v1";

/* ---------------- 狀態管理 ---------------- */
const todayStr = () => new Date().toISOString().slice(0, 10);

function loadState() {
  const raw = localStorage.getItem(STORE_KEY);
  if (raw) {
    try { return JSON.parse(raw); } catch (e) { /* 損毀則重建 */ }
  }
  // 初始種子資料
  return {
    words: SEED_WORDS.map((w, i) => ({ id: i + 1, ...w, learned: false })),
    daily: {},                       // { "2026-05-27": { minutes, wordsLearned, quizScores: [] } }
    todos: [],
    weeklyPlan: DEFAULT_WEEKLY_PLAN.map((p, i) => ({ id: i + 1, ...p })),
    goal: 10,
    bestStreak: 0,
    phraseIndex: dayOfYear() % DAILY_PHRASES.length
  };
}

let state = loadState();

function save() {
  localStorage.setItem(STORE_KEY, JSON.stringify(state));
}

function todayEntry() {
  const t = todayStr();
  if (!state.daily[t]) state.daily[t] = { minutes: 0, wordsLearned: 0, quizScores: [] };
  return state.daily[t];
}

function dayOfYear() {
  const now = new Date();
  const start = new Date(now.getFullYear(), 0, 0);
  return Math.floor((now - start) / 86400000);
}

/* ---------------- Streak 計算 ---------------- */
function computeStreak() {
  let streak = 0;
  const d = new Date();
  // 今天若無活動，從昨天往前算（避免今天尚未學習就中斷顯示）
  if (!hasActivity(todayStr())) d.setDate(d.getDate() - 1);
  while (true) {
    const key = d.toISOString().slice(0, 10);
    if (hasActivity(key)) { streak++; d.setDate(d.getDate() - 1); }
    else break;
  }
  if (streak > (state.bestStreak || 0)) { state.bestStreak = streak; save(); }
  return streak;
}

function hasActivity(dateKey) {
  const e = state.daily[dateKey];
  return e && (e.minutes > 0 || e.wordsLearned > 0 || e.quizScores.length > 0);
}

/* ---------------- 工具函式 ---------------- */
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

function toast(msg) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.remove("show"), 2200);
}

function shuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

/* ---------------- 導覽切換 ---------------- */
const VIEW_META = {
  overview: { title: "總覽", sub: "歡迎回來，繼續今天的學習吧！" },
  vocab: { title: "單字學習", sub: "用單字卡記憶，並管理你的單字庫" },
  quiz: { title: "單字測驗", sub: "測測看你記住多少單字" },
  progress: { title: "學習進度", sub: "追蹤你的學習成果與趨勢" },
  plan: { title: "學習計畫", sub: "規劃任務，養成每日學習習慣" }
};

function switchView(view) {
  $$(".nav-item").forEach(b => b.classList.toggle("active", b.dataset.view === view));
  $$(".view").forEach(v => v.classList.toggle("active", v.id === `view-${view}`));
  $("#viewTitle").textContent = VIEW_META[view].title;
  $("#viewSubtitle").textContent = VIEW_META[view].sub;
  if (view === "progress") renderProgress();
  if (view === "overview") renderOverview();
}

$$(".nav-item").forEach(btn => {
  btn.addEventListener("click", () => switchView(btn.dataset.view));
});

/* ---------------- 總覽 ---------------- */
function renderOverview() {
  const learned = state.words.filter(w => w.learned).length;
  const streak = computeStreak();
  $("#statTotalWords").textContent = state.words.length;
  $("#statLearnedWords").textContent = learned;
  $("#statTodayMinutes").textContent = todayEntry().minutes;
  $("#statStreak").textContent = streak;
  $("#sidebarStreak").textContent = streak;

  renderDailyGoal();
  renderPhrase();
  renderChart("#overviewChart", 7);
  renderOverviewTodos();
}

function renderDailyGoal() {
  const target = state.goal;
  const done = todayEntry().wordsLearned;
  const pct = Math.min(100, Math.round((done / target) * 100)) || 0;
  $("#goalDone").textContent = done;
  $("#goalTarget").textContent = target;
  $("#goalPercent").textContent = pct + "%";
  $("#goalInput").value = target;
  $("#goalRing").style.background =
    `conic-gradient(var(--primary) ${pct * 3.6}deg, var(--border) 0deg)`;
}

function renderPhrase() {
  const p = DAILY_PHRASES[state.phraseIndex % DAILY_PHRASES.length];
  $("#phraseEn").textContent = `"${p.en}"`;
  $("#phraseZh").textContent = p.zh;
  $("#phraseTag").textContent = "# " + p.tag;
}

$("#newPhraseBtn").addEventListener("click", () => {
  state.phraseIndex = (state.phraseIndex + 1) % DAILY_PHRASES.length;
  save();
  renderPhrase();
});

function renderOverviewTodos() {
  const ul = $("#overviewTodos");
  const pending = state.todos.filter(t => !t.done).slice(0, 4);
  if (pending.length === 0) {
    ul.innerHTML = `<li class="muted">沒有待辦任務 🎉</li>`;
    return;
  }
  ul.innerHTML = pending.map(t => `<li>• ${escapeHtml(t.text)}</li>`).join("");
}

/* ---------------- 長條圖（近 N 天學習分鐘）---------------- */
function renderChart(selector, days) {
  const el = $(selector);
  const cols = [];
  let max = 1;
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    const key = d.toISOString().slice(0, 10);
    const mins = state.daily[key] ? state.daily[key].minutes : 0;
    max = Math.max(max, mins);
    cols.push({ label: ["日", "一", "二", "三", "四", "五", "六"][d.getDay()], mins });
  }
  el.innerHTML = cols.map(c => {
    const h = Math.round((c.mins / max) * 100);
    return `<div class="bar-col">
      <span class="bar-val">${c.mins || ""}</span>
      <div class="bar" style="height:${c.mins ? Math.max(h, 6) : 0}%"></div>
      <span class="bar-label">${c.label}</span>
    </div>`;
  }).join("");
}

/* ---------------- 單字卡 ---------------- */
let fcIndex = 0;
function renderFlashcard() {
  const words = state.words;
  const card = $("#flashcard");
  card.classList.remove("flipped");
  if (words.length === 0) {
    $("#fcWord").textContent = "點擊新增單字開始";
    $("#fcMeaning").textContent = "";
    $("#fcExample").textContent = "";
    $("#flashcardCounter").textContent = "0 / 0";
    return;
  }
  fcIndex = (fcIndex + words.length) % words.length;
  const w = words[fcIndex];
  $("#fcWord").textContent = w.word;
  $("#fcMeaning").textContent = w.meaning;
  $("#fcExample").textContent = w.example || "";
  $("#flashcardCounter").textContent = `${fcIndex + 1} / ${words.length}`;
  $("#fcLearned").textContent = w.learned ? "✅ 已學會（取消）" : "✅ 標記學會";
}

$("#flashcard").addEventListener("click", () => $("#flashcard").classList.toggle("flipped"));
$("#fcPrev").addEventListener("click", (e) => { e.stopPropagation(); fcIndex--; renderFlashcard(); });
$("#fcNext").addEventListener("click", (e) => { e.stopPropagation(); fcIndex++; renderFlashcard(); });
$("#fcLearned").addEventListener("click", (e) => {
  e.stopPropagation();
  const w = state.words[fcIndex];
  if (!w) return;
  toggleLearned(w.id);
  renderFlashcard();
});

/* ---------------- 單字清單 ---------------- */
function renderWordTable() {
  const tbody = $("#wordTableBody");
  tbody.innerHTML = state.words.map(w => `
    <tr>
      <td><strong>${escapeHtml(w.word)}</strong></td>
      <td>${escapeHtml(w.meaning)}</td>
      <td><span class="badge ${w.learned ? "learned" : "learning"}">${w.learned ? "已學會" : "學習中"}</span></td>
      <td style="text-align:right">
        <button class="row-btn" data-toggle="${w.id}">${w.learned ? "↩︎" : "✓"}</button>
        <button class="row-btn del" data-del="${w.id}">🗑️</button>
      </td>
    </tr>`).join("");
  $("#wordEmptyHint").classList.toggle("hidden", state.words.length > 0);

  tbody.querySelectorAll("[data-toggle]").forEach(b =>
    b.addEventListener("click", () => { toggleLearned(Number(b.dataset.toggle)); }));
  tbody.querySelectorAll("[data-del]").forEach(b =>
    b.addEventListener("click", () => { deleteWord(Number(b.dataset.del)); }));
}

function toggleLearned(id) {
  const w = state.words.find(x => x.id === id);
  if (!w) return;
  w.learned = !w.learned;
  if (w.learned) { todayEntry().wordsLearned++; toast(`已標記「${w.word}」學會 🎉`); }
  else { todayEntry().wordsLearned = Math.max(0, todayEntry().wordsLearned - 1); }
  save();
  renderWordTable();
  renderOverview();
}

function deleteWord(id) {
  state.words = state.words.filter(x => x.id !== id);
  save();
  renderWordTable();
  renderFlashcard();
  renderOverview();
  toast("已刪除單字");
}

$("#addWordBtn").addEventListener("click", () => $("#wordForm").classList.toggle("hidden"));
$("#cancelWordBtn").addEventListener("click", () => {
  $("#wordForm").classList.add("hidden");
  $("#wordForm").reset();
});
$("#wordForm").addEventListener("submit", (e) => {
  e.preventDefault();
  const word = $("#wordInput").value.trim();
  const meaning = $("#meaningInput").value.trim();
  const example = $("#exampleInput").value.trim();
  if (!word || !meaning) return;
  const id = state.words.reduce((m, w) => Math.max(m, w.id), 0) + 1;
  state.words.push({ id, word, meaning, example, learned: false });
  save();
  e.target.reset();
  $("#wordForm").classList.add("hidden");
  renderWordTable();
  renderFlashcard();
  renderOverview();
  toast("已新增單字 ✨");
});

/* ---------------- 測驗 ---------------- */
let quiz = { questions: [], idx: 0, correct: 0 };

function startQuiz() {
  if (state.words.length < 4) {
    $("#quizEmptyHint").classList.remove("hidden");
    return;
  }
  const pool = shuffle(state.words);
  const count = Math.min(10, pool.length);
  quiz = { questions: pool.slice(0, count), idx: 0, correct: 0 };
  $("#quizStart").classList.add("hidden");
  $("#quizResult").classList.add("hidden");
  $("#quizBody").classList.remove("hidden");
  renderQuestion();
}

function renderQuestion() {
  const q = quiz.questions[quiz.idx];
  $("#quizProgress").textContent = `第 ${quiz.idx + 1} / ${quiz.questions.length} 題`;
  $("#quizQuestion").textContent = q.word;
  // 產生選項：正確答案 + 3 個干擾
  const distractors = shuffle(state.words.filter(w => w.id !== q.id)).slice(0, 3);
  const options = shuffle([q, ...distractors]);
  const box = $("#quizOptions");
  box.innerHTML = options.map(o =>
    `<button class="quiz-option" data-id="${o.id}">${escapeHtml(o.meaning)}</button>`).join("");
  box.querySelectorAll(".quiz-option").forEach(btn =>
    btn.addEventListener("click", () => answerQuestion(btn, q.id)));
  $("#nextQuestionBtn").classList.add("hidden");
}

function answerQuestion(btn, correctId) {
  const chosen = Number(btn.dataset.id);
  const buttons = $$(".quiz-option");
  buttons.forEach(b => {
    b.disabled = true;
    if (Number(b.dataset.id) === correctId) b.classList.add("correct");
  });
  if (chosen === correctId) { quiz.correct++; }
  else { btn.classList.add("wrong"); }
  $("#nextQuestionBtn").classList.remove("hidden");
}

$("#startQuizBtn").addEventListener("click", startQuiz);
$("#retryQuizBtn").addEventListener("click", startQuiz);
$("#nextQuestionBtn").addEventListener("click", () => {
  quiz.idx++;
  if (quiz.idx < quiz.questions.length) renderQuestion();
  else finishQuiz();
});

function finishQuiz() {
  const total = quiz.questions.length;
  const score = Math.round((quiz.correct / total) * 100);
  todayEntry().quizScores.push(score);
  save();
  $("#quizBody").classList.add("hidden");
  $("#quizResult").classList.remove("hidden");
  $("#quizScoreText").textContent = `答對 ${quiz.correct} / ${total} 題（${score} 分）`;
  $("#quizProgress").textContent = "";
  toast(score >= 80 ? "表現優異！🏆" : "繼續加油 💪");
  renderOverview();
}

/* ---------------- 學習進度 ---------------- */
function renderProgress() {
  const days = Object.keys(state.daily).filter(hasActivity);
  const totalMinutes = Object.values(state.daily).reduce((s, e) => s + (e.minutes || 0), 0);
  const allScores = Object.values(state.daily).flatMap(e => e.quizScores || []);
  const avgScore = allScores.length
    ? Math.round(allScores.reduce((a, b) => a + b, 0) / allScores.length) : 0;

  $("#progTotalDays").textContent = days.length;
  $("#progTotalMinutes").textContent = totalMinutes;
  $("#progBestStreak").textContent = state.bestStreak || computeStreak();
  $("#progAvgScore").textContent = avgScore + "%";

  renderChart("#progressChart", 7);

  const learned = state.words.filter(w => w.learned).length;
  const pct = state.words.length ? Math.round((learned / state.words.length) * 100) : 0;
  $("#masteryFill").style.width = pct + "%";
  $("#masteryText").textContent = pct + "%";
}

/* ---------------- 學習時間記錄 ---------------- */
$("#logTimeBtn").addEventListener("click", () => $("#timeModal").classList.remove("hidden"));
$("#closeTimeBtn").addEventListener("click", () => $("#timeModal").classList.add("hidden"));
$("#saveTimeBtn").addEventListener("click", () => {
  const mins = parseInt($("#timeInput").value, 10);
  if (mins > 0) {
    todayEntry().minutes += mins;
    save();
    toast(`已記錄 ${mins} 分鐘學習時間 ⏱️`);
  }
  $("#timeModal").classList.add("hidden");
  renderProgress();
  renderOverview();
});

/* ---------------- 目標設定 ---------------- */
$("#goalInput").addEventListener("change", (e) => {
  const v = parseInt(e.target.value, 10);
  if (v > 0) { state.goal = v; save(); renderDailyGoal(); }
});

/* ---------------- 待辦清單 ---------------- */
function renderTodos() {
  const ul = $("#todoList");
  ul.innerHTML = state.todos.map(t => `
    <li class="todo-item ${t.done ? "done" : ""}">
      <input type="checkbox" class="todo-check" data-id="${t.id}" ${t.done ? "checked" : ""}>
      <span class="todo-text">${escapeHtml(t.text)}</span>
      <button class="todo-del" data-id="${t.id}">×</button>
    </li>`).join("");
  $("#todoEmptyHint").classList.toggle("hidden", state.todos.length > 0);

  ul.querySelectorAll(".todo-check").forEach(c =>
    c.addEventListener("change", () => {
      const t = state.todos.find(x => x.id === Number(c.dataset.id));
      t.done = c.checked;
      save();
      renderTodos();
      renderOverviewTodos();
    }));
  ul.querySelectorAll(".todo-del").forEach(b =>
    b.addEventListener("click", () => {
      state.todos = state.todos.filter(x => x.id !== Number(b.dataset.id));
      save();
      renderTodos();
      renderOverviewTodos();
    }));
}

$("#todoForm").addEventListener("submit", (e) => {
  e.preventDefault();
  const text = $("#todoInput").value.trim();
  if (!text) return;
  const id = state.todos.reduce((m, t) => Math.max(m, t.id), 0) + 1;
  state.todos.push({ id, text, done: false });
  save();
  e.target.reset();
  renderTodos();
  renderOverviewTodos();
});

/* ---------------- 每週計畫 ---------------- */
function renderPlan() {
  const grid = $("#planGrid");
  grid.innerHTML = state.weeklyPlan.map(p => `
    <div class="plan-day ${p.done ? "done" : ""}">
      <span class="plan-day-name">${p.day}</span>
      <span class="plan-day-task">${escapeHtml(p.task)}</span>
      <button class="plan-toggle" data-id="${p.id}">${p.done ? "✓ 完成" : "標記完成"}</button>
    </div>`).join("");
  grid.querySelectorAll(".plan-toggle").forEach(b =>
    b.addEventListener("click", () => {
      const p = state.weeklyPlan.find(x => x.id === Number(b.dataset.id));
      p.done = !p.done;
      save();
      renderPlan();
    }));
}

/* ---------------- 安全處理 ---------------- */
function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, c =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

/* ---------------- 初始化 ---------------- */
function init() {
  const d = new Date();
  $("#todayDate").textContent = d.toLocaleDateString("zh-TW", {
    year: "numeric", month: "long", day: "numeric", weekday: "long"
  });
  renderOverview();
  renderFlashcard();
  renderWordTable();
  renderTodos();
  renderPlan();
}

init();
