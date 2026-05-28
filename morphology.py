"""字根字首字尾構詞元件 + SEED_WORDS 台味諧音速記（離線資料，不需 API）。

PREFIXES / ROOTS / SUFFIXES 用於建構 Mermaid 心智圖；
MNEMONICS 用於翻面單字卡背面與字根速記分頁的諧音表。
"""

PREFIXES = [
    {"m": "un-", "zh": "不／相反", "ex": ["unhappy", "unfair", "unlock"]},
    {"m": "re-", "zh": "再次／回", "ex": ["redo", "replay", "return"]},
    {"m": "pre-", "zh": "事前", "ex": ["preview", "prepare", "predict"]},
    {"m": "dis-", "zh": "相反／分離", "ex": ["dislike", "disagree", "disappear"]},
    {"m": "mis-", "zh": "錯誤", "ex": ["mistake", "misread", "misuse"]},
    {"m": "over-", "zh": "過度", "ex": ["overdo", "overcook", "overpay"]},
    {"m": "under-", "zh": "在下／不足", "ex": ["underline", "undergo", "understand"]},
    {"m": "in- im-", "zh": "不／向內", "ex": ["incorrect", "impossible", "include"]},
]

ROOTS = [
    {"m": "spect", "zh": "看", "ex": ["inspect", "respect", "suspect"]},
    {"m": "port", "zh": "搬運", "ex": ["import", "export", "transport"]},
    {"m": "ject", "zh": "投擲", "ex": ["inject", "reject", "project"]},
    {"m": "duc duct", "zh": "引導", "ex": ["introduce", "conduct", "produce"]},
    {"m": "scrib script", "zh": "書寫", "ex": ["describe", "prescribe", "manuscript"]},
    {"m": "vis vid", "zh": "看見", "ex": ["vision", "visible", "evidence"]},
    {"m": "struct", "zh": "建造", "ex": ["construct", "instruct", "structure"]},
    {"m": "form", "zh": "形狀", "ex": ["inform", "transform", "uniform"]},
]

SUFFIXES = [
    {"m": "-tion -sion", "zh": "名詞／動作", "ex": ["action", "decision", "education"]},
    {"m": "-able -ible", "zh": "可…的", "ex": ["readable", "edible", "possible"]},
    {"m": "-er -or", "zh": "做…的人", "ex": ["teacher", "actor", "writer"]},
    {"m": "-less", "zh": "沒有…的", "ex": ["hopeless", "useless", "careless"]},
    {"m": "-ful", "zh": "充滿…的", "ex": ["helpful", "useful", "careful"]},
    {"m": "-ment", "zh": "名詞／結果", "ex": ["development", "agreement", "treatment"]},
    {"m": "-ly", "zh": "副詞", "ex": ["quickly", "slowly", "happily"]},
    {"m": "-ness", "zh": "名詞／性質", "ex": ["happiness", "kindness", "darkness"]},
]


def _mm_escape(text: str) -> str:
    """Mermaid mindmap 節點字串內不能含雙引號;以單引號取代。"""
    return str(text).replace('"', "'")


def build_mindmap(title: str, items: list) -> str:
    """把字根／字首／字尾資料轉成 Mermaid mindmap 字串(縮排式語法)。
    所有節點都用 ["..."] 包起來,確保空格、中文點(·)、reserved keyword
    都被當作純文字、而不是 mermaid 的 shape/keyword 語法。"""
    lines = ["mindmap", f'  root(("{_mm_escape(title)}"))']
    for it in items:
        label = _mm_escape(f"{it['m']} · {it['zh']}")
        lines.append(f'    ["{label}"]')
        for ex in it["ex"]:
            lines.append(f'      ["{_mm_escape(ex)}"]')
    return "\n".join(lines)


def _affix_variants(m: str, side: str) -> list:
    """把 'in- im-' 拆成 ['in','im'];'-tion -sion' 拆成 ['tion','sion'];'duc duct' 拆成 ['duc','duct']。"""
    out = []
    for v in m.split():
        v = v.strip()
        if side == "prefix":
            v = v.rstrip("-")
        elif side == "suffix":
            v = v.lstrip("-")
        if v:
            out.append(v)
    return out


def decompose_word(word: str) -> dict | None:
    """用 PREFIXES/ROOTS/SUFFIXES 嘗試把單字拆成字首、字根、字尾。
    至少匹配到一個元件才回 dict;全沒中回 None。
    Heuristic 簡單匹配,純供記憶聯想參考(可能有誤匹配)。
    """
    w = word.lower().strip()
    if len(w) < 4:
        return None

    prefix = None
    for p in PREFIXES:
        for v in _affix_variants(p["m"], "prefix"):
            if len(v) >= 2 and w.startswith(v) and len(w) > len(v) + 2:
                if not prefix or len(v) > prefix["_len"]:
                    prefix = {"form": v + "-", "zh": p["zh"], "_len": len(v)}
    rest = w[prefix["_len"]:] if prefix else w

    suffix = None
    for s in SUFFIXES:
        for v in _affix_variants(s["m"], "suffix"):
            if len(v) >= 2 and rest.endswith(v) and len(rest) > len(v) + 1:
                if not suffix or len(v) > suffix["_len"]:
                    suffix = {"form": "-" + v, "zh": s["zh"], "_len": len(v)}
    stem = rest[:-suffix["_len"]] if suffix else rest

    root = None
    for r in ROOTS:
        for v in _affix_variants(r["m"], "root"):
            if len(v) >= 3 and v in stem:
                if not root or len(v) > root["_len"]:
                    root = {"form": v, "zh": r["zh"], "_len": len(v)}

    if not (prefix or root or suffix):
        return None
    for d in (prefix, root, suffix):
        if d:
            d.pop("_len", None)
    return {"prefix": prefix, "root": root, "suffix": suffix, "stem": stem}


def build_word_mindmap(word: str, decomp: dict) -> str:
    """為單一單字建構迷你 Mermaid mindmap(字首/字根/字尾分支)。"""
    lines = ["mindmap", f'  root(("{_mm_escape(word)}"))']
    if decomp.get("prefix"):
        lines.append(f'    ["字首 {_mm_escape(decomp["prefix"]["form"])}"]')
        lines.append(f'      ["{_mm_escape(decomp["prefix"]["zh"])}"]')
    if decomp.get("root"):
        lines.append(f'    ["字根 {_mm_escape(decomp["root"]["form"])}"]')
        lines.append(f'      ["{_mm_escape(decomp["root"]["zh"])}"]')
    elif decomp.get("stem"):
        lines.append(f'    ["字幹 {_mm_escape(decomp["stem"])}"]')
    if decomp.get("suffix"):
        lines.append(f'    ["字尾 {_mm_escape(decomp["suffix"]["form"])}"]')
        lines.append(f'      ["{_mm_escape(decomp["suffix"]["zh"])}"]')
    return "\n".join(lines)


# SEED_WORDS 的台味諧音速記（key 必須對應 data.SEED_WORDS 的 word）
MNEMONICS = {
    "accomplish": {
        "kk": "[əˈkɑmplɪʃ]",
        "phonics": "uh-KOM-plish",
        "homophone": "阿康破立緒",
        "image": "阿康破除迷思、立起頭緒，終於達成大事。",
    },
    "benefit": {
        "kk": "[ˈbɛnəfɪt]",
        "phonics": "BEH-nuh-fit",
        "homophone": "辦你 fit",
        "image": "辦活動讓你健身 fit，對你有好處。",
    },
    "consider": {
        "kk": "[kənˈsɪdɚ]",
        "phonics": "kun-SIH-der",
        "homophone": "肯洗熱",
        "image": "你『肯』不『肯』『洗熱』水？要『考慮』一下。",
    },
    "determine": {
        "kk": "[dɪˈtɝmɪn]",
        "phonics": "dih-TER-min",
        "homophone": "弟特門",
        "image": "弟弟特別敲門，下定『決心』要進去。",
    },
    "efficient": {
        "kk": "[ɪˈfɪʃənt]",
        "phonics": "ih-FISH-unt",
        "homophone": "一肥神",
        "image": "一個肥神來幫忙，辦什麼都『有效率』。",
    },
    "fundamental": {
        "kk": "[ˌfʌndəˈmɛnt!]",
        "phonics": "fun-duh-MEN-tul",
        "homophone": "翻 do mental",
        "image": "翻過去『do mental』心算，才打下『基本』功。",
    },
    "generate": {
        "kk": "[ˈdʒɛnəˌret]",
        "phonics": "JEN-uh-rayt",
        "homophone": "姊那 rate",
        "image": "姊姊那邊 rate 評分，『產生』新點子。",
    },
    "hesitate": {
        "kk": "[ˈhɛzəˌtet]",
        "phonics": "HEH-zuh-tayt",
        "homophone": "黑系貼",
        "image": "要不要貼黑系貼紙？你『猶豫』半天。",
    },
    "improve": {
        "kk": "[ɪmˈpruv]",
        "phonics": "im-PROOV",
        "homophone": "贏 prove",
        "image": "想贏就要『證明』自己持續『進步』。",
    },
    "justify": {
        "kk": "[ˈdʒʌstəˌfaɪ]",
        "phonics": "JUS-tuh-fai",
        "homophone": "渣斯太肥",
        "image": "渣男理由太肥（腓），硬要『正當化』自己。",
    },
    "knowledge": {
        "kk": "[ˈnɑlɪdʒ]",
        "phonics": "NAH-lij",
        "homophone": "腦力擠",
        "image": "腦力『擠』一擠，就變成『知識』。",
    },
    "luxury": {
        "kk": "[ˈlʌkʃəri]",
        "phonics": "LUK-shuh-ree",
        "homophone": "辣可學瑞",
        "image": "辣到可以去瑞士學廚藝，真『奢侈』。",
    },
    "maintain": {
        "kk": "[menˈten]",
        "phonics": "mayn-TAYN",
        "homophone": "賣燈",
        "image": "燈泡『維持』長亮，才能一直『賣燈』。",
    },
    "negotiate": {
        "kk": "[nɪˈɡoʃɪˌet]",
        "phonics": "ni-GOH-shee-ayt",
        "homophone": "你哥洗鞋",
        "image": "你哥幫你洗鞋，跟你『協商』條件。",
    },
    "obstacle": {
        "kk": "[ˈɑbstək!]",
        "phonics": "OB-stuh-kul",
        "homophone": "歐被四道扣",
        "image": "歐文被四道路障扣住，變成『障礙』。",
    },
    "participate": {
        "kk": "[pɑrˈtɪsəˌpet]",
        "phonics": "par-TIH-suh-payt",
        "homophone": "怕踢西胚",
        "image": "怕被踢進西胚社，只好硬著頭皮『參與』。",
    },
    "qualify": {
        "kk": "[ˈkwɑləˌfaɪ]",
        "phonics": "KWAH-luh-fai",
        "homophone": "誇了肥",
        "image": "誇張到肥，才算『合格』入選。",
    },
    "reliable": {
        "kk": "[rɪˈlaɪəb!]",
        "phonics": "ri-LIE-uh-bul",
        "homophone": "瑞賴阿伯",
        "image": "瑞士賴著阿伯不走，因為他超『可靠』。",
    },
    "significant": {
        "kk": "[sɪɡˈnɪfəkənt]",
        "phonics": "sig-NIH-fuh-kunt",
        "homophone": "係哥泥肥肯",
        "image": "係哥踩泥肥到肯特，『顯著』地引人注目。",
    },
    "transparent": {
        "kk": "[trænsˈpɛrənt]",
        "phonics": "trans-PAIR-unt",
        "homophone": "傳吃拍人",
        "image": "傳吃播拍人，『透明』看得一清二楚。",
    },
}
