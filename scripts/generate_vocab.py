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
- "pos": 詞性的中文標籤,例如 "動詞"、"名詞"、"形容詞"、"副詞"、"介系詞"、"連接詞"、"助動詞"。
  多詞性用 " / " 連起來,例如 "動詞 / 名詞"
- "other_forms": 同源衍生字陣列(可空),每筆 {"word", "pos", "meaning_zh", "example"}。
  example = 一句 ≤ 10 字、自然口語的母語英文例句,展示該衍生字的真實用法。
  最多 4 筆,選最常用的(派生形容詞、名詞化、副詞等)。基本詞可空陣列 []。

# 品質規範
- 諧音要鮮明、好記,避免敷衍。
- 例句要像真實對話,不要 textbook English。
- 用法要點出常見搭配或語境差異。

# 輸出範例（單字 "consider"）
[{"word":"consider","meaning_zh":"考慮、視為","kk":"[kənˈsɪdɚ]","phonics":"kun-SIH-der","homophone":"肯洗熱","image":"你『肯』不『肯』『洗熱』水？讓你考慮一下。","example_en":"Have you considered taking the train?","example_zh":"你考慮過改搭火車嗎?","usage_zh":"提建議用 'Have you considered ...?' 比直接 'You should' 更委婉,日常對話常見。","pos":"動詞","other_forms":[{"word":"consideration","pos":"名詞","meaning_zh":"考慮；體貼","example":"Please take my advice into consideration."},{"word":"considerable","pos":"形容詞","meaning_zh":"相當大的","example":"It took considerable effort to finish."},{"word":"considerate","pos":"形容詞","meaning_zh":"體貼的","example":"He's always considerate of others' feelings."}]}]
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
    """從模型回應抽出 JSON array,容忍偶發的程式碼圍欄或前後雜訊。

    若整段 JSON 被 max_output_tokens 截斷而無法直接解析(常見錯誤
    'Unterminated string'),則退而逐一搶救陣列中「已完整」的物件,
    避免整批作廢。"""
    raw = (text or "").strip()
    body = raw
    # 去掉 ```json ... ``` 圍欄(若有)
    m = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", raw, re.DOTALL)
    if m:
        body = m.group(1)
    else:
        # 取第一個 [ 到最後一個 ] 之間(注意:KK 音標含 [],不能單純 rfind)
        s, e = raw.find("["), raw.rfind("]")
        if s != -1 and e != -1 and e > s:
            body = raw[s:e + 1]
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        # 被截斷或 [] 裁切失準:直接從原文逐一搶救完整物件,避免整批作廢
        return _salvage_objects(raw)


def _salvage_objects(text: str) -> list:
    """從(可能被截斷的)JSON 字串中,用 raw_decode 逐一解析頂層物件,
    回傳所有能成功解析的完整物件;截斷處後面的殘片自動丟棄。"""
    decoder = json.JSONDecoder()
    out = []
    i = text.find("{")
    n = len(text)
    while i != -1 and i < n:
        try:
            obj, end = decoder.raw_decode(text, i)
        except json.JSONDecodeError:
            break  # 剩下的是被截斷的殘片,停止
        if isinstance(obj, dict):
            out.append(obj)
        # 跳到下一個 '{'
        i = text.find("{", end)
    return out


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
