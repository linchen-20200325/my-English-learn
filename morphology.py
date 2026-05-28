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


def build_mindmap(title: str, items: list) -> str:
    """把字根／字首／字尾資料轉成 Mermaid mindmap 字串。
    為每個節點明確產生唯一 id(n0、n0_1...),避免 mermaid 11.15 對「以 dash 開頭」
    的純 ["..."] 節點解析失敗。"""
    lines = ["mindmap", f'  root(("{_mm_escape(title)}"))']
    for i, it in enumerate(items):
        label = _mm_escape(f"{it['m']} · {it['zh']}")
        lines.append(f'    n{i}["{label}"]')
        for j, ex in enumerate(it["ex"]):
            lines.append(f'      n{i}_{j}["{_mm_escape(ex)}"]')
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
        "example_en": "She accomplished her goal of reading 50 books this year.",
        "example_zh": "她今年達成了讀 50 本書的目標。",
    },
    "benefit": {
        "kk": "[ˈbɛnəfɪt]",
        "phonics": "BEH-nuh-fit",
        "homophone": "辦你 fit",
        "image": "辦活動讓你健身 fit，對你有好處。",
        "example_en": "Regular exercise has many health benefits.",
        "example_zh": "規律運動有許多健康上的好處。",
    },
    "consider": {
        "kk": "[kənˈsɪdɚ]",
        "phonics": "kun-SIH-der",
        "homophone": "肯洗熱",
        "image": "你『肯』不『肯』『洗熱』水？要『考慮』一下。",
        "example_en": "Please consider my suggestion carefully.",
        "example_zh": "請仔細考慮我的建議。",
    },
    "determine": {
        "kk": "[dɪˈtɝmɪn]",
        "phonics": "dih-TER-min",
        "homophone": "弟特門",
        "image": "弟弟特別敲門，下定『決心』要進去。",
        "example_en": "The test will determine your English level.",
        "example_zh": "這個測驗會判定你的英文程度。",
    },
    "efficient": {
        "kk": "[ɪˈfɪʃənt]",
        "phonics": "ih-FISH-unt",
        "homophone": "一肥神",
        "image": "一個肥神來幫忙，辦什麼都『有效率』。",
        "example_en": "This is a more efficient way to study vocabulary.",
        "example_zh": "這是更有效率的單字學習方法。",
    },
    "fundamental": {
        "kk": "[ˌfʌndəˈmɛnt!]",
        "phonics": "fun-duh-MEN-tul",
        "homophone": "翻 do mental",
        "image": "翻過去『do mental』心算，才打下『基本』功。",
        "example_en": "Grammar is fundamental to learning a language.",
        "example_zh": "文法是學語言的根本。",
    },
    "generate": {
        "kk": "[ˈdʒɛnəˌret]",
        "phonics": "JEN-uh-rayt",
        "homophone": "姊那 rate",
        "image": "姊姊那邊 rate 評分，『產生』新點子。",
        "example_en": "The app can generate a quiz from your word list.",
        "example_zh": "這個 app 可以從你的單字表自動產生測驗。",
    },
    "hesitate": {
        "kk": "[ˈhɛzəˌtet]",
        "phonics": "HEH-zuh-tayt",
        "homophone": "黑系貼",
        "image": "要不要貼黑系貼紙？你『猶豫』半天。",
        "example_en": "Don't hesitate to ask questions in class.",
        "example_zh": "上課別客氣，有問題就問。",
    },
    "improve": {
        "kk": "[ɪmˈpruv]",
        "phonics": "im-PROOV",
        "homophone": "贏 prove",
        "image": "想贏就要『證明』自己持續『進步』。",
        "example_en": "Reading every day will improve your English.",
        "example_zh": "每天閱讀會讓你的英文進步。",
    },
    "justify": {
        "kk": "[ˈdʒʌstəˌfaɪ]",
        "phonics": "JUS-tuh-fai",
        "homophone": "渣斯太肥",
        "image": "渣男理由太肥（腓），硬要『正當化』自己。",
        "example_en": "Can you justify your decision?",
        "example_zh": "你能為你的決定提出合理理由嗎？",
    },
    "knowledge": {
        "kk": "[ˈnɑlɪdʒ]",
        "phonics": "NAH-lij",
        "homophone": "腦力擠",
        "image": "腦力『擠』一擠，就變成『知識』。",
        "example_en": "Knowledge of vocabulary helps with reading.",
        "example_zh": "認識單字有助於閱讀。",
    },
    "luxury": {
        "kk": "[ˈlʌkʃəri]",
        "phonics": "LUK-shuh-ree",
        "homophone": "辣可學瑞",
        "image": "辣到可以去瑞士學廚藝，真『奢侈』。",
        "example_en": "A daily walk is a small luxury for me.",
        "example_zh": "每天散步是我的小確幸。",
    },
    "maintain": {
        "kk": "[menˈten]",
        "phonics": "mayn-TAYN",
        "homophone": "賣燈",
        "image": "燈泡『維持』長亮，才能一直『賣燈』。",
        "example_en": "It's important to maintain a study routine.",
        "example_zh": "維持讀書習慣很重要。",
    },
    "negotiate": {
        "kk": "[nɪˈɡoʃɪˌet]",
        "phonics": "ni-GOH-shee-ayt",
        "homophone": "你哥洗鞋",
        "image": "你哥幫你洗鞋，跟你『協商』條件。",
        "example_en": "They negotiated a better price.",
        "example_zh": "他們談到了比較好的價格。",
    },
    "obstacle": {
        "kk": "[ˈɑbstək!]",
        "phonics": "OB-stuh-kul",
        "homophone": "歐被四道扣",
        "image": "歐文被四道路障扣住，變成『障礙』。",
        "example_en": "Fear of mistakes is a common obstacle for learners.",
        "example_zh": "怕犯錯是學習者常見的阻礙。",
    },
    "participate": {
        "kk": "[pɑrˈtɪsəˌpet]",
        "phonics": "par-TIH-suh-payt",
        "homophone": "怕踢西胚",
        "image": "怕被踢進西胚社，只好硬著頭皮『參與』。",
        "example_en": "Students should participate in class discussions.",
        "example_zh": "學生應該參與課堂討論。",
    },
    "qualify": {
        "kk": "[ˈkwɑləˌfaɪ]",
        "phonics": "KWAH-luh-fai",
        "homophone": "誇了肥",
        "image": "誇張到肥，才算『合格』入選。",
        "example_en": "She qualified for the advanced course.",
        "example_zh": "她取得了進階課程的資格。",
    },
    "reliable": {
        "kk": "[rɪˈlaɪəb!]",
        "phonics": "ri-LIE-uh-bul",
        "homophone": "瑞賴阿伯",
        "image": "瑞士賴著阿伯不走，因為他超『可靠』。",
        "example_en": "He is a reliable study partner.",
        "example_zh": "他是個可靠的讀書夥伴。",
    },
    "significant": {
        "kk": "[sɪɡˈnɪfəkənt]",
        "phonics": "sig-NIH-fuh-kunt",
        "homophone": "係哥泥肥肯",
        "image": "係哥踩泥肥到肯特，『顯著』地引人注目。",
        "example_en": "You've made significant progress this month.",
        "example_zh": "你這個月有顯著的進步。",
    },
    "transparent": {
        "kk": "[trænsˈpɛrənt]",
        "phonics": "trans-PAIR-unt",
        "homophone": "傳吃拍人",
        "image": "傳吃播拍人，『透明』看得一清二楚。",
        "example_en": "The teacher gave transparent feedback.",
        "example_zh": "老師給了透明清楚的回饋。",
    },
}
