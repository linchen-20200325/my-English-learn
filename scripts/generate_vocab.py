#!/usr/bin/env python3
"""批次生成單字庫：呼叫 Gemini API 為 vocab_wordlist.txt 內每個字補上諧音／造句／用法,
結果寫進 vocab_bank.json,Streamlit「📖 單字庫」分頁即時讀取。

使用方式：
    pip install google-genai
    export GEMINI_API_KEY=...                            # 取得 https://aistudio.google.com/apikey
    python scripts/generate_vocab.py --limit 30          # 先試 30 字
    python scripts/generate_vocab.py                     # 跑完整份詞表
    python scripts/generate_vocab.py --model pro         # 改用 Gemini 2.5 Pro 高品質
    python scripts/generate_vocab.py --batch-size 25     # 自訂批次

可重跑：已在 vocab_bank.json 內的字會自動略過。
每批寫檔一次,中斷不會遺失既有進度。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORDLIST = ROOT / "scripts" / "vocab_wordlist.txt"
BANK = ROOT / "vocab_bank.json"

MODELS = {
    "flash": "gemini-2.5-flash",
    "pro": "gemini-2.5-pro",
}

SYSTEM_PROMPT = """你是台味英文單字記憶教練,擅長把英文聲音強行接到中文意思,並寫出母語人士日常口語例句。

# 輸出格式（嚴格）
只輸出一個 JSON array,前後不得有任何文字、不得包 markdown 程式碼區塊。
array 內每個物件對應一個輸入單字,順序與輸入相同,且必須含以下欄位:
- "word": 輸入單字原樣(全小寫除非專有名詞)
- "meaning_zh": 繁體中文意思(精簡,1–2 詞組)
- "kk": KK 音標,以方括號包住,例如 "[əˈkɑmplɪʃ]"
- "phonics": 直覺自然發音拆解,例如 "uh-KOM-plish"
- "homophone": 台味諧音(繁中,4–8 字,生動好記,可以荒謬搞笑)
- "image": 一句繁中(≤30 字),把諧音聲音對應到單字意思的具體畫面
- "example_en": 一句口語自然的母語人士例句(≤15 字),拒絕生硬教科書英文
- "example_zh": example_en 的繁中口語翻譯(自然,不死板)
- "usage_zh": 一句繁中,說明此字在對話中的「使用時機與搭配」(常見 collocation、語感、正式或口語)

# 品質規範
- 諧音要鮮明、好記,避免敷衍。
- 例句要像真實對話,不要 textbook English。
- 用法要點出常見搭配或語境差異。

# 輸出範例（單字 "consider"）
[{"word":"consider","meaning_zh":"考慮、視為","kk":"[kənˈsɪdɚ]","phonics":"kun-SIH-der","homophone":"肯洗熱","image":"你『肯』不『肯』『洗熱』水？讓你考慮一下。","example_en":"Have you considered taking the train?","example_zh":"你考慮過改搭火車嗎?","usage_zh":"提建議用 'Have you considered ...?' 比直接 'You should' 更委婉,日常對話常見。"}]
"""


def load_bank() -> dict:
    if BANK.exists():
        try:
            return json.loads(BANK.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"⚠️  {BANK} 內容損毀,以空庫重來。", file=sys.stderr)
    return {}


def save_bank(bank: dict) -> None:
    BANK.write_text(json.dumps(bank, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_wordlist() -> list[str]:
    if not WORDLIST.exists():
        sys.exit(f"找不到詞表：{WORDLIST}")
    words = []
    for line in WORDLIST.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            words.append(s.lower())
    # 去重保留順序
    seen = set()
    out = []
    for w in words:
        if w not in seen:
            seen.add(w)
            out.append(w)
    return out


def chunked(seq: list, n: int):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def extract_json_array(text: str):
    """從模型回應抽出 JSON array,容忍偶發的程式碼圍欄或前後雜訊。"""
    text = text.strip()
    # 去掉 ```json ... ``` 圍欄(若有)
    m = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)
    else:
        # 取第一個 [ 到最後一個 ] 之間
        s, e = text.find("["), text.rfind("]")
        if s != -1 and e != -1 and e > s:
            text = text[s:e + 1]
    return json.loads(text)


def generate_batch(client, model: str, words: list[str]):
    """呼叫 Gemini 一次生成一批單字的 JSON 資料。"""
    from google.genai import types
    resp = client.models.generate_content(
        model=model,
        contents="請為以下單字生成資料: " + ", ".join(words),
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.7,
            max_output_tokens=8000,
        ),
    )
    return extract_json_array(resp.text or "")


def main() -> None:
    parser = argparse.ArgumentParser(description="批次生成 vocab_bank.json (Gemini)")
    parser.add_argument("--limit", type=int, default=None,
                        help="只跑前 N 個待補單字(用於試跑)")
    parser.add_argument("--model", choices=list(MODELS), default="flash",
                        help="模型: flash(預設,便宜) | pro(高品質)")
    parser.add_argument("--batch-size", type=int, default=20,
                        help="每批字數,預設 20")
    parser.add_argument("--retries", type=int, default=3,
                        help="單批失敗最多重試次數")
    args = parser.parse_args()

    try:
        from google import genai
    except ImportError:
        sys.exit("請先安裝套件: pip install google-genai")

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        sys.exit("請先設定環境變數: export GEMINI_API_KEY=... "
                 "(取得 https://aistudio.google.com/apikey)")

    client = genai.Client(api_key=api_key)
    bank = load_bank()
    words = load_wordlist()
    todo = [w for w in words if w not in bank]
    if args.limit:
        todo = todo[:args.limit]

    print(f"詞表 {len(words)} 字 | 已完成 {len(bank)} 字 | 待補 {len(todo)} 字 "
          f"| 模型 {MODELS[args.model]} | 批次 {args.batch_size}")
    if not todo:
        print("沒有待補單字。")
        return

    done = 0
    for batch in chunked(todo, args.batch_size):
        entries = None
        for attempt in range(args.retries):
            try:
                entries = generate_batch(client, MODELS[args.model], batch)
                break
            except (json.JSONDecodeError, Exception) as e:  # Gemini 例外類型較雜,廣泛攔截
                wait = 2 ** attempt
                print(f"  retry {attempt + 1}/{args.retries} after {wait}s ({type(e).__name__}: {e!s:.80})")
                time.sleep(wait)
        if entries is None:
            print(f"  ⚠️  跳過此批: {batch}")
            continue

        added = 0
        for e in entries:
            w = (e.get("word") or "").strip().lower()
            if w:
                bank[w] = e
                added += 1
        save_bank(bank)
        done += len(batch)
        print(f"[{done}/{len(todo)}] +{added} 字寫入  |  目前庫存 {len(bank)} 字")

    print(f"完成。{BANK} 共 {len(bank)} 字。")


if __name__ == "__main__":
    main()
