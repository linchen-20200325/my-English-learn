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
    {"m": "ex-", "zh": "向外／前任", "ex": ["exit", "export", "ex-wife"]},
    {"m": "en- em-", "zh": "使成為", "ex": ["enable", "ensure", "embrace"]},
    {"m": "co-", "zh": "共同", "ex": ["coworker", "cooperate", "coexist"]},
    {"m": "de-", "zh": "向下／除去", "ex": ["delete", "decline", "decode"]},
    {"m": "anti-", "zh": "反對", "ex": ["antibody", "antiwar", "antisocial"]},
    {"m": "auto-", "zh": "自動／自己", "ex": ["automatic", "autograph", "autobiography"]},
    {"m": "bi-", "zh": "二／雙", "ex": ["bicycle", "bilingual", "biweekly"]},
    {"m": "bio-", "zh": "生命／生物", "ex": ["biology", "biography", "biotech"]},
    {"m": "micro-", "zh": "微小", "ex": ["microwave", "microscope", "microchip"]},
    {"m": "mono-", "zh": "單一", "ex": ["monologue", "monopoly", "monorail"]},
    {"m": "fore-", "zh": "前面／先", "ex": ["forecast", "forehead", "foresee"]},
    {"m": "inter-", "zh": "之間", "ex": ["internet", "interact", "international"]},
    {"m": "multi-", "zh": "多", "ex": ["multimedia", "multitask", "multiple"]},
    {"m": "non-", "zh": "非", "ex": ["nonstop", "nonsense", "nonprofit"]},
    {"m": "post-", "zh": "之後", "ex": ["postpone", "postwar", "postscript"]},
    {"m": "sub-", "zh": "在下／次", "ex": ["submarine", "subway", "subtract"]},
    {"m": "super-", "zh": "超級", "ex": ["superman", "supermarket", "supervise"]},
    {"m": "trans-", "zh": "跨越", "ex": ["transport", "translate", "transfer"]},
    {"m": "tri-", "zh": "三", "ex": ["triangle", "tricycle", "trio"]},
    {"m": "uni-", "zh": "單一", "ex": ["unique", "uniform", "universe"]},
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
    {"m": "tract", "zh": "拉", "ex": ["attract", "contract", "extract"]},
    {"m": "ped pod", "zh": "腳", "ex": ["pedal", "pedestrian", "podium"]},
    {"m": "man manu", "zh": "手", "ex": ["manual", "manage", "manufacture"]},
    {"m": "dict", "zh": "說／指示", "ex": ["dictate", "predict", "dictionary"]},
    {"m": "mit miss", "zh": "送出", "ex": ["submit", "permit", "mission"]},
    {"m": "fac fact fect", "zh": "做／製造", "ex": ["factory", "effect", "perfect"]},
    {"m": "graph gram", "zh": "寫／圖", "ex": ["photograph", "diagram", "program"]},
    {"m": "log logy", "zh": "話／學科", "ex": ["dialogue", "biology", "psychology"]},
    {"m": "phon", "zh": "聲音", "ex": ["phone", "phonics", "symphony"]},
    {"m": "tele", "zh": "遠距", "ex": ["telephone", "television", "telescope"]},
    {"m": "cycl", "zh": "輪／循環", "ex": ["cycle", "bicycle", "recycle"]},
    {"m": "geo", "zh": "地球／土地", "ex": ["geography", "geology", "geometry"]},
    {"m": "audi", "zh": "聽", "ex": ["audio", "audience", "audible"]},
    {"m": "ven vent", "zh": "來", "ex": ["event", "invent", "prevent"]},
    {"m": "cap capt", "zh": "抓取／頭", "ex": ["capture", "captain", "capable"]},
    {"m": "mov mot", "zh": "移動", "ex": ["move", "motion", "motivate"]},
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
    {"m": "-ity -ty", "zh": "名詞／性質", "ex": ["ability", "reality", "safety"]},
    {"m": "-ist", "zh": "…主義者／專家", "ex": ["artist", "scientist", "tourist"]},
    {"m": "-ism", "zh": "主義／思想", "ex": ["tourism", "racism", "criticism"]},
    {"m": "-ish", "zh": "略帶…的／動詞化", "ex": ["childish", "selfish", "accomplish"]},
    {"m": "-ous", "zh": "充滿…的", "ex": ["famous", "dangerous", "curious"]},
    {"m": "-ive", "zh": "有…性質的", "ex": ["active", "creative", "expensive"]},
    {"m": "-ize -ise", "zh": "使…化", "ex": ["realize", "organize", "modernize"]},
    {"m": "-ate", "zh": "動詞／使成為", "ex": ["create", "celebrate", "educate"]},
    {"m": "-ic -ical", "zh": "形容詞／…的", "ex": ["magic", "logical", "tropical"]},
    {"m": "-en", "zh": "使變成", "ex": ["wooden", "darken", "strengthen"]},
    {"m": "-ship", "zh": "關係／身份", "ex": ["friendship", "leadership", "relationship"]},
    {"m": "-hood", "zh": "時期／身份", "ex": ["childhood", "neighborhood", "motherhood"]},
    {"m": "-ward", "zh": "向…方向", "ex": ["forward", "backward", "upward"]},
    {"m": "-wise", "zh": "在…方面／如…", "ex": ["clockwise", "otherwise", "likewise"]},
    {"m": "-ee", "zh": "被…的人", "ex": ["employee", "trainee", "interviewee"]},
    {"m": "-ant -ent", "zh": "做…的人／形容詞", "ex": ["assistant", "student", "important"]},
]


def _mm_escape(text: str) -> str:
    """Mermaid mindmap 節點字串內不能含雙引號;以單引號取代。"""
    return str(text).replace('"', "'")


def _norm_morph(m: str) -> str:
    """把 'in- im-' 之類多 token 標籤、含開頭 dash 的標籤,規一化成 mermaid 友善寫法:
    切空白 → 去前後 dash → 用 / 連起來。'-tion -sion' → 'tion/sion'。"""
    return "/".join(t.strip("-") for t in m.split() if t.strip("-"))


def build_mindmap(title: str, items: list) -> str:
    """改用 flowchart LR(樹狀左→右)取代 mermaid mindmap 渲染:同樣是樹狀視覺,
    但 mermaid flowchart 是最早最穩定的圖類型,不會因為標籤裡有 dash、中文點、
    多 token、reserved 詞(log/script...)而炸。每個節點用具名 id `nN` / `nN_M`。"""
    safe_title = _mm_escape(title)
    lines = [
        "flowchart LR",
        "    classDef cat fill:#dbeafe,stroke:#1d4ed8,stroke-width:1px;",
        "    classDef leaf fill:#fef3c7,stroke:#b45309,stroke-width:1px;",
        f'    root(("{safe_title}"))',
    ]
    for i, it in enumerate(items):
        label = _mm_escape(f"{_norm_morph(it['m'])} : {it['zh']}")
        lines.append(f'    n{i}["{label}"]:::cat')
        lines.append(f'    root --> n{i}')
        for j, ex in enumerate(it["ex"]):
            lines.append(f'    n{i}_{j}["{_mm_escape(ex)}"]:::leaf')
            lines.append(f'    n{i} --> n{i}_{j}')
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

    for d in (prefix, root, suffix):
        if d:
            d.pop("_len", None)
    # 即使無詞素匹配也回 dict(stem = 原字),確保每個單字都能畫出心智圖。
    return {"prefix": prefix, "root": root, "suffix": suffix, "stem": stem}


def build_word_mindmap(word: str, decomp: dict) -> str:
    """為單一單字建構迷你樹狀圖。改用 flowchart LR(橫向左→右),避免 mindmap 對
    少節點(只有字首沒字根/字尾時)自動轉成垂直佈局把高度撐爆。"""
    lines = [
        "flowchart LR",
        "    classDef cat fill:#dbeafe,stroke:#1d4ed8,stroke-width:1px;",
        "    classDef leaf fill:#fef3c7,stroke:#b45309,stroke-width:1px;",
        f'    root(("{_mm_escape(word)}"))',
    ]
    idx = 0
    if decomp.get("prefix"):
        zh = _mm_escape(decomp["prefix"]["zh"])
        form = _mm_escape(decomp["prefix"]["form"])
        lines.append(f'    n{idx}["字首 {form}"]:::cat')
        lines.append(f'    root --> n{idx}')
        lines.append(f'    n{idx}m["{zh}"]:::leaf')
        lines.append(f'    n{idx} --> n{idx}m')
        idx += 1
    if decomp.get("root"):
        zh = _mm_escape(decomp["root"]["zh"])
        form = _mm_escape(decomp["root"]["form"])
        lines.append(f'    n{idx}["字根 {form}"]:::cat')
        lines.append(f'    root --> n{idx}')
        lines.append(f'    n{idx}m["{zh}"]:::leaf')
        lines.append(f'    n{idx} --> n{idx}m')
        idx += 1
    elif decomp.get("stem"):
        stem = _mm_escape(decomp["stem"])
        lines.append(f'    n{idx}["字幹 {stem}"]:::cat')
        lines.append(f'    root --> n{idx}')
        idx += 1
    if decomp.get("suffix"):
        zh = _mm_escape(decomp["suffix"]["zh"])
        form = _mm_escape(decomp["suffix"]["form"])
        lines.append(f'    n{idx}["字尾 {form}"]:::cat')
        lines.append(f'    root --> n{idx}')
        lines.append(f'    n{idx}m["{zh}"]:::leaf')
        lines.append(f'    n{idx} --> n{idx}m')
        idx += 1
    return "\n".join(lines)


# SEED_WORDS 的台味諧音速記（key 必須對應 data.SEED_WORDS 的 word）
MNEMONICS = {
    "accomplish": {
        "kk": "[əˈkɑmplɪʃ]",
        "phonics": "uh-KOM-plish",
        "homophone": "阿康破立緒",
        "image": "阿康破除迷思、立起頭緒，終於達成大事。",
        "example_en": "She accomplished her goal of reading 50 books this year.",
        "example_zh": "她今年達成了讀 50 本書的目標。",
        "pos": "動詞",
        "other_forms": [
            {"word": "accomplishment", "pos": "名詞", "meaning_zh": "成就；完成", "example": "Reading 100 books was a real accomplishment."},
            {"word": "accomplished", "pos": "形容詞", "meaning_zh": "已完成的；熟練的", "example": "She's an accomplished pianist."}
        ],
    },
    "benefit": {
        "kk": "[ˈbɛnəfɪt]",
        "phonics": "BEH-nuh-fit",
        "homophone": "辦你 fit",
        "image": "辦活動讓你健身 fit，對你有好處。",
        "example_en": "Regular exercise has many health benefits.",
        "example_zh": "規律運動有許多健康上的好處。",
        "pos": "名詞 / 動詞",
        "other_forms": [
            {"word": "beneficial", "pos": "形容詞", "meaning_zh": "有益的", "example": "Exercise is beneficial to your health."},
            {"word": "beneficiary", "pos": "名詞", "meaning_zh": "受益者", "example": "Who is the beneficiary of this trust?"}
        ],
    },
    "consider": {
        "kk": "[kənˈsɪdɚ]",
        "phonics": "kun-SIH-der",
        "homophone": "肯洗熱",
        "image": "你『肯』不『肯』『洗熱』水？要『考慮』一下。",
        "example_en": "Please consider my suggestion carefully.",
        "example_zh": "請仔細考慮我的建議。",
        "pos": "動詞",
        "other_forms": [
            {"word": "consideration", "pos": "名詞", "meaning_zh": "考慮；體貼", "example": "Please take my advice into consideration."},
            {"word": "considerable", "pos": "形容詞", "meaning_zh": "相當大的", "example": "It took considerable effort to finish."},
            {"word": "considerate", "pos": "形容詞", "meaning_zh": "體貼的", "example": "He's always considerate of others' feelings."}
        ],
    },
    "determine": {
        "kk": "[dɪˈtɝmɪn]",
        "phonics": "dih-TER-min",
        "homophone": "弟特門",
        "image": "弟弟特別敲門，下定『決心』要進去。",
        "example_en": "The test will determine your English level.",
        "example_zh": "這個測驗會判定你的英文程度。",
        "pos": "動詞",
        "other_forms": [
            {"word": "determination", "pos": "名詞", "meaning_zh": "決心；決定", "example": "Her determination is truly inspiring."},
            {"word": "determined", "pos": "形容詞", "meaning_zh": "下定決心的", "example": "I'm determined to learn English this year."}
        ],
    },
    "efficient": {
        "kk": "[ɪˈfɪʃənt]",
        "phonics": "ih-FISH-unt",
        "homophone": "一肥神",
        "image": "一個肥神來幫忙，辦什麼都『有效率』。",
        "example_en": "This is a more efficient way to study vocabulary.",
        "example_zh": "這是更有效率的單字學習方法。",
        "pos": "形容詞",
        "other_forms": [
            {"word": "efficiency", "pos": "名詞", "meaning_zh": "效率", "example": "We need to improve our team's efficiency."},
            {"word": "efficiently", "pos": "副詞", "meaning_zh": "有效率地", "example": "She works quickly and efficiently."}
        ],
    },
    "fundamental": {
        "kk": "[ˌfʌndəˈmɛnt!]",
        "phonics": "fun-duh-MEN-tul",
        "homophone": "翻 do mental",
        "image": "翻過去『do mental』心算，才打下『基本』功。",
        "example_en": "Grammar is fundamental to learning a language.",
        "example_zh": "文法是學語言的根本。",
        "pos": "形容詞 / 名詞",
        "other_forms": [
            {"word": "fundamentally", "pos": "副詞", "meaning_zh": "根本上", "example": "The plan is fundamentally flawed."},
            {"word": "fundamentals", "pos": "名詞（複數）", "meaning_zh": "基本原理", "example": "Master the fundamentals first."}
        ],
    },
    "generate": {
        "kk": "[ˈdʒɛnəˌret]",
        "phonics": "JEN-uh-rayt",
        "homophone": "姊那 rate",
        "image": "姊姊那邊 rate 評分，『產生』新點子。",
        "example_en": "The app can generate a quiz from your word list.",
        "example_zh": "這個 app 可以從你的單字表自動產生測驗。",
        "pos": "動詞",
        "other_forms": [
            {"word": "generation", "pos": "名詞", "meaning_zh": "產生；世代", "example": "Our generation grew up with the internet."},
            {"word": "generator", "pos": "名詞", "meaning_zh": "發電機；產生者", "example": "The generator powers the entire building."}
        ],
    },
    "hesitate": {
        "kk": "[ˈhɛzəˌtet]",
        "phonics": "HEH-zuh-tayt",
        "homophone": "黑系貼",
        "image": "要不要貼黑系貼紙？你『猶豫』半天。",
        "example_en": "Don't hesitate to ask questions in class.",
        "example_zh": "上課別客氣，有問題就問。",
        "pos": "動詞",
        "other_forms": [
            {"word": "hesitation", "pos": "名詞", "meaning_zh": "猶豫", "example": "He answered without any hesitation."},
            {"word": "hesitant", "pos": "形容詞", "meaning_zh": "猶豫的", "example": "She seems hesitant about the offer."}
        ],
    },
    "improve": {
        "kk": "[ɪmˈpruv]",
        "phonics": "im-PROOV",
        "homophone": "贏 prove",
        "image": "想贏就要『證明』自己持續『進步』。",
        "example_en": "Reading every day will improve your English.",
        "example_zh": "每天閱讀會讓你的英文進步。",
        "pos": "動詞",
        "other_forms": [
            {"word": "improvement", "pos": "名詞", "meaning_zh": "改善；進步", "example": "There's still room for improvement."},
            {"word": "improved", "pos": "形容詞", "meaning_zh": "改良的", "example": "The improved version is much faster."}
        ],
    },
    "justify": {
        "kk": "[ˈdʒʌstəˌfaɪ]",
        "phonics": "JUS-tuh-fai",
        "homophone": "渣斯太肥",
        "image": "渣男理由太肥（腓），硬要『正當化』自己。",
        "example_en": "Can you justify your decision?",
        "example_zh": "你能為你的決定提出合理理由嗎？",
        "pos": "動詞",
        "other_forms": [
            {"word": "justification", "pos": "名詞", "meaning_zh": "正當理由", "example": "There's no justification for cheating."},
            {"word": "justified", "pos": "形容詞", "meaning_zh": "有正當理由的", "example": "You're justified in feeling angry."}
        ],
    },
    "knowledge": {
        "kk": "[ˈnɑlɪdʒ]",
        "phonics": "NAH-lij",
        "homophone": "腦力擠",
        "image": "腦力『擠』一擠，就變成『知識』。",
        "example_en": "Knowledge of vocabulary helps with reading.",
        "example_zh": "認識單字有助於閱讀。",
        "pos": "名詞",
        "other_forms": [
            {"word": "know", "pos": "動詞", "meaning_zh": "知道", "example": "I know exactly what you mean."},
            {"word": "knowledgeable", "pos": "形容詞", "meaning_zh": "博學的", "example": "She's very knowledgeable about wine."}
        ],
    },
    "luxury": {
        "kk": "[ˈlʌkʃəri]",
        "phonics": "LUK-shuh-ree",
        "homophone": "辣可學瑞",
        "image": "辣到可以去瑞士學廚藝，真『奢侈』。",
        "example_en": "A daily walk is a small luxury for me.",
        "example_zh": "每天散步是我的小確幸。",
        "pos": "名詞",
        "other_forms": [
            {"word": "luxurious", "pos": "形容詞", "meaning_zh": "奢華的", "example": "The hotel room was absolutely luxurious."},
            {"word": "luxuriously", "pos": "副詞", "meaning_zh": "奢華地", "example": "She lived luxuriously after the deal."}
        ],
    },
    "maintain": {
        "kk": "[menˈten]",
        "phonics": "mayn-TAYN",
        "homophone": "賣燈",
        "image": "燈泡『維持』長亮，才能一直『賣燈』。",
        "example_en": "It's important to maintain a study routine.",
        "example_zh": "維持讀書習慣很重要。",
        "pos": "動詞",
        "other_forms": [
            {"word": "maintenance", "pos": "名詞", "meaning_zh": "維護；保養", "example": "The car needs regular maintenance."}
        ],
    },
    "negotiate": {
        "kk": "[nɪˈɡoʃɪˌet]",
        "phonics": "ni-GOH-shee-ayt",
        "homophone": "你哥洗鞋",
        "image": "你哥幫你洗鞋，跟你『協商』條件。",
        "example_en": "They negotiated a better price.",
        "example_zh": "他們談到了比較好的價格。",
        "pos": "動詞",
        "other_forms": [
            {"word": "negotiation", "pos": "名詞", "meaning_zh": "協商；談判", "example": "The negotiation lasted three hours."},
            {"word": "negotiable", "pos": "形容詞", "meaning_zh": "可協商的", "example": "The price is fully negotiable."},
            {"word": "negotiator", "pos": "名詞", "meaning_zh": "談判者", "example": "He's a skilled negotiator."}
        ],
    },
    "obstacle": {
        "kk": "[ˈɑbstək!]",
        "phonics": "OB-stuh-kul",
        "homophone": "歐被四道扣",
        "image": "歐文被四道路障扣住，變成『障礙』。",
        "example_en": "Fear of mistakes is a common obstacle for learners.",
        "example_zh": "怕犯錯是學習者常見的阻礙。",
        "pos": "名詞",
        "other_forms": [],
    },
    "participate": {
        "kk": "[pɑrˈtɪsəˌpet]",
        "phonics": "par-TIH-suh-payt",
        "homophone": "怕踢西胚",
        "image": "怕被踢進西胚社，只好硬著頭皮『參與』。",
        "example_en": "Students should participate in class discussions.",
        "example_zh": "學生應該參與課堂討論。",
        "pos": "動詞",
        "other_forms": [
            {"word": "participation", "pos": "名詞", "meaning_zh": "參與", "example": "Class participation is mandatory."},
            {"word": "participant", "pos": "名詞", "meaning_zh": "參與者", "example": "Each participant gets a free meal."}
        ],
    },
    "qualify": {
        "kk": "[ˈkwɑləˌfaɪ]",
        "phonics": "KWAH-luh-fai",
        "homophone": "誇了肥",
        "image": "誇張到肥，才算『合格』入選。",
        "example_en": "She qualified for the advanced course.",
        "example_zh": "她取得了進階課程的資格。",
        "pos": "動詞",
        "other_forms": [
            {"word": "qualification", "pos": "名詞", "meaning_zh": "資格；學歷", "example": "What qualifications do you have?"},
            {"word": "qualified", "pos": "形容詞", "meaning_zh": "合格的", "example": "She's qualified to teach yoga."}
        ],
    },
    "reliable": {
        "kk": "[rɪˈlaɪəb!]",
        "phonics": "ri-LIE-uh-bul",
        "homophone": "瑞賴阿伯",
        "image": "瑞士賴著阿伯不走，因為他超『可靠』。",
        "example_en": "He is a reliable study partner.",
        "example_zh": "他是個可靠的讀書夥伴。",
        "pos": "形容詞",
        "other_forms": [
            {"word": "rely", "pos": "動詞", "meaning_zh": "依賴", "example": "You can always rely on her."},
            {"word": "reliability", "pos": "名詞", "meaning_zh": "可靠性", "example": "Reliability is what our customers want."},
            {"word": "reliance", "pos": "名詞", "meaning_zh": "依賴；信任", "example": "Our reliance on phones keeps growing."}
        ],
    },
    "significant": {
        "kk": "[sɪɡˈnɪfəkənt]",
        "phonics": "sig-NIH-fuh-kunt",
        "homophone": "係哥泥肥肯",
        "image": "係哥踩泥肥到肯特，『顯著』地引人注目。",
        "example_en": "You've made significant progress this month.",
        "example_zh": "你這個月有顯著的進步。",
        "pos": "形容詞",
        "other_forms": [
            {"word": "significantly", "pos": "副詞", "meaning_zh": "顯著地", "example": "Sales increased significantly this quarter."},
            {"word": "significance", "pos": "名詞", "meaning_zh": "重要性", "example": "The discovery has huge significance."}
        ],
    },
    "transparent": {
        "kk": "[trænsˈpɛrənt]",
        "phonics": "trans-PAIR-unt",
        "homophone": "傳吃拍人",
        "image": "傳吃播拍人，『透明』看得一清二楚。",
        "example_en": "The teacher gave transparent feedback.",
        "example_zh": "老師給了透明清楚的回饋。",
        "pos": "形容詞",
        "other_forms": [
            {"word": "transparency", "pos": "名詞", "meaning_zh": "透明；透明度", "example": "Voters demand transparency from government."},
            {"word": "transparently", "pos": "副詞", "meaning_zh": "透明地", "example": "The CEO acted transparently."}
        ],
    },
    "analyze": {
        "kk": "[ˈæn!ˌaɪz]",
        "phonics": "AN-uh-lize",
        "homophone": "安娜賴茲",
        "image": "『安娜』『賴』在『茲』（這）裡把資料一條條拆開分析。",
        "example_en": "Let's analyze the data before deciding.",
        "example_zh": "下決定前先來分析數據。",
        "pos": "動詞",
        "other_forms": [{"word": "analysis", "pos": "名詞", "meaning_zh": "分析", "example": "The analysis took two hours."}, {"word": "analyst", "pos": "名詞", "meaning_zh": "分析師", "example": "She works as a data analyst."}],
    },
    "approach": {
        "kk": "[əˈprotʃ]",
        "phonics": "uh-PROHCH",
        "homophone": "餓破吃",
        "image": "肚子『餓』到快『破』，慢慢『吃』地『接近』食物。",
        "example_en": "We need a new approach to this problem.",
        "example_zh": "這問題我們需要新的方法。",
        "pos": "名詞 / 動詞",
        "other_forms": [{"word": "approachable", "pos": "形容詞", "meaning_zh": "平易近人的", "example": "The teacher is very approachable."}],
    },
    "assume": {
        "kk": "[əˈsum]",
        "phonics": "uh-SOOM",
        "homophone": "阿summ",
        "image": "『阿』伯隨口『summ』（嗯）一聲，就『假定』事情成了。",
        "example_en": "Don't assume he's wrong before you ask.",
        "example_zh": "別在問之前就認定他錯了。",
        "pos": "動詞",
        "other_forms": [{"word": "assumption", "pos": "名詞", "meaning_zh": "假設", "example": "That's a dangerous assumption."}],
    },
    "available": {
        "kk": "[əˈveləb!]",
        "phonics": "uh-VAY-luh-bul",
        "homophone": "阿肥了寶",
        "image": "『阿肥』『了』（拿到）『寶』物，現在隨時『可取用』。",
        "example_en": "Is this seat available?",
        "example_zh": "這個位子有人坐嗎？",
        "pos": "形容詞",
        "other_forms": [{"word": "availability", "pos": "名詞", "meaning_zh": "可用性", "example": "Please check the availability of the room."}],
    },
    "brief": {
        "kk": "[brif]",
        "phonics": "BREEF",
        "homophone": "不理夫",
        "image": "老婆『不理』『夫』，只給他一句『簡短』的話。",
        "example_en": "Let me give you a brief summary.",
        "example_zh": "讓我給你一個簡短的摘要。",
        "pos": "形容詞 / 名詞",
        "other_forms": [{"word": "briefly", "pos": "副詞", "meaning_zh": "簡短地", "example": "He spoke briefly about the plan."}],
    },
    "capable": {
        "kk": "[ˈkepəb!]",
        "phonics": "KAY-puh-bul",
        "homophone": "K葡寶",
        "image": "拿『K』他用的『葡』萄餵『寶』寶，證明他很『有能力』。",
        "example_en": "She is capable of handling the project alone.",
        "example_zh": "她有能力獨自處理這專案。",
        "pos": "形容詞",
        "other_forms": [{"word": "capability", "pos": "名詞", "meaning_zh": "能力", "example": "We're expanding our capabilities."}],
    },
    "challenge": {
        "kk": "[ˈtʃæləndʒ]",
        "phonics": "CHAL-unj",
        "homophone": "騜稜橋",
        "image": "騎到『騜』（嘎）地過『稜』線『橋』，是個大『挑戰』。",
        "example_en": "Learning a language is a fun challenge.",
        "example_zh": "學語言是個有趣的挑戰。",
        "pos": "名詞 / 動詞",
        "other_forms": [{"word": "challenging", "pos": "形容詞", "meaning_zh": "有挑戰性的", "example": "It was a challenging exam."}],
    },
    "conclude": {
        "kk": "[kənˈklud]",
        "phonics": "kun-KLOOD",
        "homophone": "肯哭路的",
        "image": "他『肯』在『哭』完這段『路的』盡頭『下結論』。",
        "example_en": "We concluded the meeting at noon.",
        "example_zh": "我們在中午結束了會議。",
        "pos": "動詞",
        "other_forms": [{"word": "conclusion", "pos": "名詞", "meaning_zh": "結論", "example": "What's your conclusion?"}],
    },
    "contribute": {
        "kk": "[kənˈtrɪbjut]",
        "phonics": "kun-TRIB-yoot",
        "homophone": "肯出比有",
        "image": "他『肯』『出』力『比』別人都『有』心地『貢獻』。",
        "example_en": "Everyone can contribute to the team.",
        "example_zh": "每個人都能為團隊做出貢獻。",
        "pos": "動詞",
        "other_forms": [{"word": "contribution", "pos": "名詞", "meaning_zh": "貢獻", "example": "Thank you for your contribution."}],
    },
    "crucial": {
        "kk": "[ˈkruʃəl]",
        "phonics": "KROO-shul",
        "homophone": "哭休",
        "image": "錯過這步就只能『哭』著『休』息，因為它太『關鍵』。",
        "example_en": "This is a crucial moment for us.",
        "example_zh": "這對我們是關鍵時刻。",
        "pos": "形容詞",
        "other_forms": [],
    },
    "demonstrate": {
        "kk": "[ˈdɛmənˌstret]",
        "phonics": "DEH-mun-strayt",
        "homophone": "電門史崔",
        "image": "在『電門』前『史崔』（甩開）雙手，『示範』怎麼操作。",
        "example_en": "Let me demonstrate how it works.",
        "example_zh": "讓我示範它如何運作。",
        "pos": "動詞",
        "other_forms": [{"word": "demonstration", "pos": "名詞", "meaning_zh": "示範", "example": "There was a cooking demonstration."}],
    },
    "distribute": {
        "kk": "[dɪˈstrɪbjut]",
        "phonics": "dih-STRIB-yoot",
        "homophone": "地是出比有",
        "image": "『地』上『是』他『出』來『比』誰『有』份地『分發』東西。",
        "example_en": "Please distribute these handouts.",
        "example_zh": "請把這些講義發下去。",
        "pos": "動詞",
        "other_forms": [{"word": "distribution", "pos": "名詞", "meaning_zh": "分配", "example": "The distribution was fair."}],
    },
    "emphasize": {
        "kk": "[ˈɛmfəˌsaɪz]",
        "phonics": "EM-fuh-size",
        "homophone": "嗯för 賽資",
        "image": "『嗯』地『för』（為）『賽資』格反覆『強調』重點。",
        "example_en": "I want to emphasize this point.",
        "example_zh": "我想強調這一點。",
        "pos": "動詞",
        "other_forms": [{"word": "emphasis", "pos": "名詞", "meaning_zh": "強調、重點", "example": "The emphasis is on quality."}],
    },
    "encounter": {
        "kk": "[ɪnˈkaʊntɚ]",
        "phonics": "in-KOWN-ter",
        "homophone": "硬尻特",
        "image": "走路太『硬』，『尻』（撞）到『特』別的人，意外『偶遇』。",
        "example_en": "I encountered an old friend on the train.",
        "example_zh": "我在火車上偶遇一位老朋友。",
        "pos": "動詞 / 名詞",
        "other_forms": [],
    },
    "establish": {
        "kk": "[əˈstæblɪʃ]",
        "phonics": "uh-STAB-lish",
        "homophone": "餓死他不理續",
        "image": "就算『餓死』『他』也『不理』，繼『續』『建立』自己的事業。",
        "example_en": "They established the company in 1990.",
        "example_zh": "他們在 1990 年創立了公司。",
        "pos": "動詞",
        "other_forms": [{"word": "establishment", "pos": "名詞", "meaning_zh": "建立；機構", "example": "The establishment of rules took time."}],
    },
    "evaluate": {
        "kk": "[ɪˈvæljuˌet]",
        "phonics": "ih-VAL-yoo-ayt",
        "homophone": "一肥六A",
        "image": "『一』個『肥』佬吃『六』份『A』餐，被『評估』為大胃王。",
        "example_en": "We need to evaluate the results.",
        "example_zh": "我們需要評估這些結果。",
        "pos": "動詞",
        "other_forms": [{"word": "evaluation", "pos": "名詞", "meaning_zh": "評估", "example": "The evaluation is due Friday."}],
    },
    "evident": {
        "kk": "[ˈɛvədənt]",
        "phonics": "EH-vuh-dunt",
        "homophone": "A否登",
        "image": "證據一『A』（按）就見分曉，是『否』有罪很『明顯』。",
        "example_en": "His talent was evident from a young age.",
        "example_zh": "他的才華從小就很明顯。",
        "pos": "形容詞",
        "other_forms": [{"word": "evidence", "pos": "名詞", "meaning_zh": "證據", "example": "There's no evidence for that."}],
    },
    "flexible": {
        "kk": "[ˈflɛksəb!]",
        "phonics": "FLEK-suh-bul",
        "homophone": "膚雷可些寶",
        "image": "『膚』質如『雷』射般『可』伸縮一『些』的『寶』貝，超有『彈性』。",
        "example_en": "My schedule is flexible this week.",
        "example_zh": "我這週的行程很有彈性。",
        "pos": "形容詞",
        "other_forms": [{"word": "flexibility", "pos": "名詞", "meaning_zh": "彈性", "example": "Yoga improves flexibility."}],
    },
    "genuine": {
        "kk": "[ˈdʒɛnjuɪn]",
        "phonics": "JEN-yoo-in",
        "homophone": "賤又硬",
        "image": "看起來『賤』『又』『硬』，其實是『真正』的好人。",
        "example_en": "She gave a genuine smile.",
        "example_zh": "她露出真誠的微笑。",
        "pos": "形容詞",
        "other_forms": [],
    },
    "gratitude": {
        "kk": "[ˈɡrætəˌtud]",
        "phonics": "GRAT-uh-tood",
        "homophone": "葛雷圖",
        "image": "『葛』格收到『雷』神送的『圖』，感動地表達『感激』。",
        "example_en": "I want to express my gratitude.",
        "example_zh": "我想表達我的感激。",
        "pos": "名詞",
        "other_forms": [{"word": "grateful", "pos": "形容詞", "meaning_zh": "感激的", "example": "I'm grateful for your help."}],
    },
    "immediate": {
        "kk": "[ɪˈmidɪɪt]",
        "phonics": "ih-MEE-dee-it",
        "homophone": "一密弟欸",
        "image": "『一』有『密』報，『弟』『欸』一聲就『立即』衝出去。",
        "example_en": "We need an immediate response.",
        "example_zh": "我們需要立即的回應。",
        "pos": "形容詞",
        "other_forms": [{"word": "immediately", "pos": "副詞", "meaning_zh": "立刻", "example": "Call me immediately if there's a problem."}],
    },
    "inevitable": {
        "kk": "[ɪnˈɛvətəb!]",
        "phonics": "in-EV-uh-tuh-bul",
        "homophone": "硬A否他寶",
        "image": "命運『硬』要『A』（拿）走，是『否』『他』『寶』貝都『躲不掉』。",
        "example_en": "Change is inevitable.",
        "example_zh": "改變是不可避免的。",
        "pos": "形容詞",
        "other_forms": [],
    },
    "innovate": {
        "kk": "[ˈɪnəˌvet]",
        "phonics": "IN-uh-vayt",
        "homophone": "硬no肥",
        "image": "別人說『硬』要說『no』，他偏『肥』膽『創新』。",
        "example_en": "Companies must innovate to survive.",
        "example_zh": "公司必須創新才能生存。",
        "pos": "動詞",
        "other_forms": [{"word": "innovation", "pos": "名詞", "meaning_zh": "創新", "example": "This is a great innovation."}],
    },
    "perceive": {
        "kk": "[pɚˈsiv]",
        "phonics": "per-SEEV",
        "homophone": "破洗夫",
        "image": "看到老公把碗『破』著『洗』，『夫』人立刻『察覺』不對勁。",
        "example_en": "How do you perceive this situation?",
        "example_zh": "你怎麼看待這個情況？",
        "pos": "動詞",
        "other_forms": [{"word": "perception", "pos": "名詞", "meaning_zh": "感知、看法", "example": "Perception is not always reality."}],
    },
    "persuade": {
        "kk": "[pɚˈswed]",
        "phonics": "per-SWAYD",
        "homophone": "破說的",
        "image": "嘴皮子『破』了還在『說』，『的』確把人『說服』了。",
        "example_en": "I persuaded him to join us.",
        "example_zh": "我說服了他加入我們。",
        "pos": "動詞",
        "other_forms": [{"word": "persuasion", "pos": "名詞", "meaning_zh": "說服", "example": "It took some persuasion."}],
    },
    "precise": {
        "kk": "[prɪˈsaɪs]",
        "phonics": "prih-SISE",
        "homophone": "不理塞撕",
        "image": "『不理』別人，把紙『塞』進機器『撕』得分毫不差，超『精確』。",
        "example_en": "Please be precise about the time.",
        "example_zh": "請把時間說精確一點。",
        "pos": "形容詞",
        "other_forms": [{"word": "precisely", "pos": "副詞", "meaning_zh": "精確地", "example": "That's precisely what I meant."}],
    },
    "priority": {
        "kk": "[praɪˈɔrətɪ]",
        "phonics": "pry-OR-uh-tee",
        "homophone": "拍歐了踢",
        "image": "『拍』桌喊『歐』，把它放在最前『了』才『踢』走別的，這是『優先』。",
        "example_en": "Safety is our top priority.",
        "example_zh": "安全是我們的首要之務。",
        "pos": "名詞",
        "other_forms": [{"word": "prioritize", "pos": "動詞", "meaning_zh": "優先處理", "example": "Let's prioritize the urgent tasks."}],
    },
    "reluctant": {
        "kk": "[rɪˈlʌktənt]",
        "phonics": "rih-LUK-tunt",
        "homophone": "蕊辣坦",
        "image": "『蕊』（花蕊）被『辣』到還得『坦』白，一臉『不情願』。",
        "example_en": "He was reluctant to admit his mistake.",
        "example_zh": "他不情願承認自己的錯。",
        "pos": "形容詞",
        "other_forms": [{"word": "reluctance", "pos": "名詞", "meaning_zh": "不情願", "example": "She agreed with some reluctance."}],
    },
    "resource": {
        "kk": "[ˈrisɔrs]",
        "phonics": "REE-sors",
        "homophone": "蕊縮死",
        "image": "把花『蕊』『縮』到『死』也要省下這份『資源』。",
        "example_en": "Water is a precious resource.",
        "example_zh": "水是珍貴的資源。",
        "pos": "名詞",
        "other_forms": [{"word": "resourceful", "pos": "形容詞", "meaning_zh": "足智多謀的", "example": "She's very resourceful."}],
    },
    "strategy": {
        "kk": "[ˈstrætədʒɪ]",
        "phonics": "STRAT-uh-jee",
        "homophone": "史抓得急",
        "image": "『史』官『抓』筆『得』很『急』，火速寫下作戰『策略』。",
        "example_en": "We need a better marketing strategy.",
        "example_zh": "我們需要更好的行銷策略。",
        "pos": "名詞",
        "other_forms": [{"word": "strategic", "pos": "形容詞", "meaning_zh": "策略性的", "example": "It was a strategic decision."}],
    },
    "sufficient": {
        "kk": "[səˈfɪʃənt]",
        "phonics": "suh-FISH-unt",
        "homophone": "捨肥神",
        "image": "肯『捨』出『肥』『神』的份量，份量就『足夠』了。",
        "example_en": "We have sufficient time to finish.",
        "example_zh": "我們有足夠的時間完成。",
        "pos": "形容詞",
        "other_forms": [{"word": "sufficiently", "pos": "副詞", "meaning_zh": "充分地", "example": "The room was sufficiently warm."}],
    },
}
