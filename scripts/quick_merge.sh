#!/usr/bin/env bash
# quick_merge.sh — 跳 PR 直推預設分支(main / master 兼容)
#
# 用途:套用 CLAUDE.md §4「跳 PR 直推例外」條款
#   1) STATE.md / CLAUDE.md / 註解 / typo
#   2) 版本字串 bump(不含程式邏輯)
#   3) 不影響功能行為的純文件改動
#
# 用法: ./scripts/quick_merge.sh "commit message"
#
# 流程:檢查環境 → 切預設分支 + pull → squash merge 當前分支 →
#       commit + push → 刪本地+遠端分支

set -euo pipefail

if [[ $# -ne 1 ]] || [[ -z "${1// }" ]]; then
  echo "用法: $0 \"commit message\"" >&2
  exit 1
fi

msg="$1"

# 解析預設分支(優先取 origin/HEAD;退而求其次 main → master)
default_branch=""
if git symbolic-ref -q refs/remotes/origin/HEAD >/dev/null 2>&1; then
  default_branch="$(git symbolic-ref --short refs/remotes/origin/HEAD | sed 's@^origin/@@')"
elif git show-ref --verify --quiet refs/remotes/origin/main; then
  default_branch="main"
elif git show-ref --verify --quiet refs/remotes/origin/master; then
  default_branch="master"
else
  echo "❌ 找不到預設分支(origin/HEAD、main、master 皆不存在)" >&2
  exit 1
fi

current_branch="$(git symbolic-ref --short HEAD 2>/dev/null || echo "")"
if [[ -z "$current_branch" ]]; then
  echo "❌ 目前處於 detached HEAD,中止" >&2
  exit 1
fi

if [[ "$current_branch" == "$default_branch" ]]; then
  echo "❌ 已在預設分支 $default_branch,本腳本只用於從 feature 分支 squash 回主幹" >&2
  exit 1
fi

# 必須在乾淨的 working tree(避免把未提交內容帶進 squash)
if [[ -n "$(git status --porcelain)" ]]; then
  echo "❌ Working tree 不乾淨,請先 commit 或 stash 後再執行" >&2
  git status --short >&2
  exit 1
fi

feature_branch="$current_branch"

echo "▶ 預設分支: $default_branch"
echo "▶ 來源分支: $feature_branch"
echo "▶ Commit msg: $msg"

echo "▶ 切到 $default_branch 並 pull..."
git checkout "$default_branch"
git pull --ff-only origin "$default_branch"

echo "▶ Squash merge $feature_branch..."
git merge --squash "$feature_branch"

# squash 後若沒有實際變更就直接收工(避免空 commit)
if git diff --cached --quiet; then
  echo "ℹ️  Squash 後無變更,跳過 commit / push;清掉本地分支即可"
  git branch -D "$feature_branch" || true
  git push origin --delete "$feature_branch" 2>/dev/null || true
  exit 0
fi

git commit -m "$msg"

echo "▶ Push 到 origin/$default_branch..."
git push -u origin "$default_branch"

echo "▶ 刪除本地分支 $feature_branch..."
git branch -D "$feature_branch" || true

echo "▶ 刪除遠端分支 origin/$feature_branch..."
git push origin --delete "$feature_branch" 2>/dev/null || \
  echo "ℹ️  遠端分支 $feature_branch 不存在或已刪除"

echo "✅ Done: $feature_branch → $default_branch (squash) 推送完成"
