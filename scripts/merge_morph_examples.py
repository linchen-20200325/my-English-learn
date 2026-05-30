#!/usr/bin/env python3
"""把 morph_examples_bank.json 累積的 AI 例字合併回 morphology.py 的
PREFIXES / ROOTS / SUFFIXES 的 ex 預設清單(永久內建)。

用法:
    python scripts/merge_morph_examples.py              # 合併,不清空 bank
    python scripts/merge_morph_examples.py --clear-bank # 合併後清空 bank
    python scripts/merge_morph_examples.py --dry-run    # 只報告會加哪些字,不寫檔

可重跑且冪等:已在 ex 內的字不會重複。bank 內找不到對應 m 的字會被忽略並列出。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MORPH_PY = ROOT / "morphology.py"
BANK = ROOT / "morph_examples_bank.json"

CATEGORY_MAP = {"pre": "PREFIXES", "root": "ROOTS", "suf": "SUFFIXES"}


def find_list_block(src: str, var_name: str):
    """找 `VAR = [` 對應的 top-level ]。逐字掃描並跳過字串內括號,避免誤判。"""
    m = re.search(rf"^{var_name} = \[", src, re.MULTILINE)
    if not m:
        return None, None
    start = m.start()
    i = m.end() - 1
    depth = 0
    n = len(src)
    while i < n:
        c = src[i]
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return start, i + 1
        elif c == '"':
            j = i + 1
            while j < n and src[j] != '"':
                if src[j] == "\\":
                    j += 2
                else:
                    j += 1
            i = j
        i += 1
    return None, None


def render_block(var_name: str, items: list) -> str:
    lines = [f"{var_name} = ["]
    for it in items:
        m_esc = it["m"].replace('"', '\\"')
        zh_esc = it["zh"].replace('"', '\\"')
        ex_str = ", ".join(f'"{e}"' for e in it["ex"])
        lines.append(f'    {{"m": "{m_esc}", "zh": "{zh_esc}", "ex": [{ex_str}]}},')
    lines.append("]")
    return "\n".join(lines)


def merge_into(items: list, additions: dict) -> tuple[list, int, list]:
    """回傳 (新 items, 實際新增字數, 未匹配的 m 列表)。"""
    items_new = deepcopy(items)
    keys_in_items = {it["m"] for it in items_new}
    added = 0
    unmatched = []
    for m, words in additions.items():
        if m not in keys_in_items:
            unmatched.append(m)
            continue
        for it in items_new:
            if it["m"] != m:
                continue
            for w in words:
                w = (w or "").strip().lower()
                if w and w not in it["ex"]:
                    it["ex"].append(w)
                    added += 1
            break
    return items_new, added, unmatched


def append_new(items: list, new_entries: list) -> tuple[list, int]:
    """把全新 morpheme 條目 append 進 items。以 m 去重,跳過已存在的。"""
    items_new = deepcopy(items)
    existing_m = {it["m"] for it in items_new}
    added = 0
    for ent in new_entries:
        if not isinstance(ent, dict):
            continue
        m = ent.get("m", "").strip()
        zh = ent.get("zh", "").strip()
        ex = ent.get("ex", [])
        if not m or not zh or not isinstance(ex, list):
            continue
        if m in existing_m:
            continue
        existing_m.add(m)
        items_new.append({"m": m, "zh": zh, "ex": list(ex)})
        added += 1
    return items_new, added


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clear-bank", action="store_true",
                        help="合併後清空 morph_examples_bank.json")
    parser.add_argument("--dry-run", action="store_true",
                        help="只列出會加哪些字,不寫檔")
    args = parser.parse_args()

    if not BANK.exists():
        sys.exit(f"找不到 {BANK}")
    bank = json.loads(BANK.read_text(encoding="utf-8"))
    if not isinstance(bank, dict):
        sys.exit(f"{BANK} 結構不對(應為 dict)")

    # 載入 morphology 來取得當前 PREFIXES/ROOTS/SUFFIXES
    sys.path.insert(0, str(ROOT))
    from morphology import PREFIXES, ROOTS, SUFFIXES

    src = MORPH_PY.read_text(encoding="utf-8")

    totals = {"pre": 0, "root": 0, "suf": 0}
    new_morph_added = {"pre": 0, "root": 0, "suf": 0}
    unmatched_all = {"pre": [], "root": [], "suf": []}
    new_blocks = {}

    for cat_key, items_now in (("pre", PREFIXES), ("root", ROOTS),
                                ("suf", SUFFIXES)):
        # 1) 先把 ex 例字合進已有 morpheme
        merged_items, added, unmatched = merge_into(items_now, bank.get(cat_key, {}))
        # 2) 再 append 全新 morpheme 條目
        merged_items, new_added = append_new(
            merged_items, bank.get(f"new_{cat_key}", []))
        totals[cat_key] = added
        new_morph_added[cat_key] = new_added
        unmatched_all[cat_key] = unmatched
        new_blocks[cat_key] = render_block(CATEGORY_MAP[cat_key], merged_items)

    print("=== 合併報告 ===")
    for k in ("pre", "root", "suf"):
        print(f"  {CATEGORY_MAP[k]:8} +{totals[k]} 例字, +{new_morph_added[k]} 新 morpheme"
              + (f" (未匹配 m: {unmatched_all[k]})" if unmatched_all[k] else ""))
    total = sum(totals.values()) + sum(new_morph_added.values())
    print(f"  合計新增:{total} 項 (例字 {sum(totals.values())} + 新 morpheme {sum(new_morph_added.values())})")

    if args.dry_run:
        print("\n[dry-run] 不寫檔。")
        return

    if total == 0:
        print("\n沒有新字要合,morphology.py 不動。")
        if args.clear_bank:
            BANK.write_text(json.dumps({"pre": {}, "root": {}, "suf": {},
                                        "new_pre": [], "new_root": [], "new_suf": []},
                                       ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
            print(f"已清空 {BANK.name}")
        return

    # 用 bracket-counting 找原 block 範圍,替換成新 block
    for cat_key, var in CATEGORY_MAP.items():
        s, e = find_list_block(src, var)
        if s is None:
            sys.exit(f"找不到 {var} 區塊")
        src = src[:s] + new_blocks[cat_key] + src[e:]

    MORPH_PY.write_text(src, encoding="utf-8")
    print(f"\n✅ 已寫回 {MORPH_PY.name}")

    if args.clear_bank:
        BANK.write_text(json.dumps({"pre": {}, "root": {}, "suf": {},
                                    "new_pre": [], "new_root": [], "new_suf": []},
                                   ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
        print(f"已清空 {BANK.name}")


if __name__ == "__main__":
    main()
