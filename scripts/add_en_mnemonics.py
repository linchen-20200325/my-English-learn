"""一次性腳本：擴充英文離線單字的聯想諧音記憶法。
同步寫入 data.SEED_WORDS（讓單字卡帶出新字）與 morphology.MNEMONICS（卡背諧音／字根速記頁），純離線、不需 API。
冪等：已存在的字會跳過。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

# 30 個高頻實用字：諧音把英文聲音接到中文意思，image 一句畫面把聲音連到字義
NEW = [
    ("analyze", "分析、解析", "動詞", "[ˈæn!ˌaɪz]", "AN-uh-lize", "安娜賴茲",
     "『安娜』『賴』在『茲』（這）裡把資料一條條拆開分析。",
     "Let's analyze the data before deciding.", "下決定前先來分析數據。",
     [("analysis", "名詞", "分析", "The analysis took two hours."),
      ("analyst", "名詞", "分析師", "She works as a data analyst.")]),
    ("approach", "接近；方法", "名詞 / 動詞", "[əˈprotʃ]", "uh-PROHCH", "餓破吃",
     "肚子『餓』到快『破』，慢慢『吃』地『接近』食物。",
     "We need a new approach to this problem.", "這問題我們需要新的方法。",
     [("approachable", "形容詞", "平易近人的", "The teacher is very approachable.")]),
    ("assume", "假定、認為", "動詞", "[əˈsum]", "uh-SOOM", "阿summ",
     "『阿』伯隨口『summ』（嗯）一聲，就『假定』事情成了。",
     "Don't assume he's wrong before you ask.", "別在問之前就認定他錯了。",
     [("assumption", "名詞", "假設", "That's a dangerous assumption.")]),
    ("available", "可獲得的、有空的", "形容詞", "[əˈveləb!]", "uh-VAY-luh-bul", "阿肥了寶",
     "『阿肥』『了』（拿到）『寶』物，現在隨時『可取用』。",
     "Is this seat available?", "這個位子有人坐嗎？",
     [("availability", "名詞", "可用性", "Please check the availability of the room.")]),
    ("brief", "簡短的；摘要", "形容詞 / 名詞", "[brif]", "BREEF", "不理夫",
     "老婆『不理』『夫』，只給他一句『簡短』的話。",
     "Let me give you a brief summary.", "讓我給你一個簡短的摘要。",
     [("briefly", "副詞", "簡短地", "He spoke briefly about the plan.")]),
    ("capable", "有能力的", "形容詞", "[ˈkepəb!]", "KAY-puh-bul", "K葡寶",
     "拿『K』他用的『葡』萄餵『寶』寶，證明他很『有能力』。",
     "She is capable of handling the project alone.", "她有能力獨自處理這專案。",
     [("capability", "名詞", "能力", "We're expanding our capabilities.")]),
    ("challenge", "挑戰", "名詞 / 動詞", "[ˈtʃæləndʒ]", "CHAL-unj", "騜稜橋",
     "騎到『騜』（嘎）地過『稜』線『橋』，是個大『挑戰』。",
     "Learning a language is a fun challenge.", "學語言是個有趣的挑戰。",
     [("challenging", "形容詞", "有挑戰性的", "It was a challenging exam.")]),
    ("conclude", "下結論、結束", "動詞", "[kənˈklud]", "kun-KLOOD", "肯哭路的",
     "他『肯』在『哭』完這段『路的』盡頭『下結論』。",
     "We concluded the meeting at noon.", "我們在中午結束了會議。",
     [("conclusion", "名詞", "結論", "What's your conclusion?")]),
    ("contribute", "貢獻、捐助", "動詞", "[kənˈtrɪbjut]", "kun-TRIB-yoot", "肯出比有",
     "他『肯』『出』力『比』別人都『有』心地『貢獻』。",
     "Everyone can contribute to the team.", "每個人都能為團隊做出貢獻。",
     [("contribution", "名詞", "貢獻", "Thank you for your contribution.")]),
    ("crucial", "關鍵的、決定性的", "形容詞", "[ˈkruʃəl]", "KROO-shul", "哭休",
     "錯過這步就只能『哭』著『休』息，因為它太『關鍵』。",
     "This is a crucial moment for us.", "這對我們是關鍵時刻。",
     []),
    ("demonstrate", "示範、證明", "動詞", "[ˈdɛmənˌstret]", "DEH-mun-strayt", "電門史崔",
     "在『電門』前『史崔』（甩開）雙手，『示範』怎麼操作。",
     "Let me demonstrate how it works.", "讓我示範它如何運作。",
     [("demonstration", "名詞", "示範", "There was a cooking demonstration.")]),
    ("distribute", "分配、分發", "動詞", "[dɪˈstrɪbjut]", "dih-STRIB-yoot", "地是出比有",
     "『地』上『是』他『出』來『比』誰『有』份地『分發』東西。",
     "Please distribute these handouts.", "請把這些講義發下去。",
     [("distribution", "名詞", "分配", "The distribution was fair.")]),
    ("emphasize", "強調", "動詞", "[ˈɛmfəˌsaɪz]", "EM-fuh-size", "嗯för 賽資",
     "『嗯』地『för』（為）『賽資』格反覆『強調』重點。",
     "I want to emphasize this point.", "我想強調這一點。",
     [("emphasis", "名詞", "強調、重點", "The emphasis is on quality.")]),
    ("encounter", "遭遇、偶遇", "動詞 / 名詞", "[ɪnˈkaʊntɚ]", "in-KOWN-ter", "硬尻特",
     "走路太『硬』，『尻』（撞）到『特』別的人，意外『偶遇』。",
     "I encountered an old friend on the train.", "我在火車上偶遇一位老朋友。",
     []),
    ("establish", "建立、設立", "動詞", "[əˈstæblɪʃ]", "uh-STAB-lish", "餓死他不理續",
     "就算『餓死』『他』也『不理』，繼『續』『建立』自己的事業。",
     "They established the company in 1990.", "他們在 1990 年創立了公司。",
     [("establishment", "名詞", "建立；機構", "The establishment of rules took time.")]),
    ("evaluate", "評估、評價", "動詞", "[ɪˈvæljuˌet]", "ih-VAL-yoo-ayt", "一肥六A",
     "『一』個『肥』佬吃『六』份『A』餐，被『評估』為大胃王。",
     "We need to evaluate the results.", "我們需要評估這些結果。",
     [("evaluation", "名詞", "評估", "The evaluation is due Friday.")]),
    ("evident", "明顯的", "形容詞", "[ˈɛvədənt]", "EH-vuh-dunt", "A否登",
     "證據一『A』（按）就見分曉，是『否』有罪很『明顯』。",
     "His talent was evident from a young age.", "他的才華從小就很明顯。",
     [("evidence", "名詞", "證據", "There's no evidence for that.")]),
    ("flexible", "有彈性的、靈活的", "形容詞", "[ˈflɛksəb!]", "FLEK-suh-bul", "膚雷可些寶",
     "『膚』質如『雷』射般『可』伸縮一『些』的『寶』貝，超有『彈性』。",
     "My schedule is flexible this week.", "我這週的行程很有彈性。",
     [("flexibility", "名詞", "彈性", "Yoga improves flexibility.")]),
    ("genuine", "真正的、真誠的", "形容詞", "[ˈdʒɛnjuɪn]", "JEN-yoo-in", "賤又硬",
     "看起來『賤』『又』『硬』，其實是『真正』的好人。",
     "She gave a genuine smile.", "她露出真誠的微笑。",
     []),
    ("gratitude", "感激、感謝", "名詞", "[ˈɡrætəˌtud]", "GRAT-uh-tood", "葛雷圖",
     "『葛』格收到『雷』神送的『圖』，感動地表達『感激』。",
     "I want to express my gratitude.", "我想表達我的感激。",
     [("grateful", "形容詞", "感激的", "I'm grateful for your help.")]),
    ("immediate", "立即的", "形容詞", "[ɪˈmidɪɪt]", "ih-MEE-dee-it", "一密弟欸",
     "『一』有『密』報，『弟』『欸』一聲就『立即』衝出去。",
     "We need an immediate response.", "我們需要立即的回應。",
     [("immediately", "副詞", "立刻", "Call me immediately if there's a problem.")]),
    ("inevitable", "不可避免的", "形容詞", "[ɪnˈɛvətəb!]", "in-EV-uh-tuh-bul", "硬A否他寶",
     "命運『硬』要『A』（拿）走，是『否』『他』『寶』貝都『躲不掉』。",
     "Change is inevitable.", "改變是不可避免的。",
     []),
    ("innovate", "創新", "動詞", "[ˈɪnəˌvet]", "IN-uh-vayt", "硬no肥",
     "別人說『硬』要說『no』，他偏『肥』膽『創新』。",
     "Companies must innovate to survive.", "公司必須創新才能生存。",
     [("innovation", "名詞", "創新", "This is a great innovation.")]),
    ("perceive", "察覺、感知", "動詞", "[pɚˈsiv]", "per-SEEV", "破洗夫",
     "看到老公把碗『破』著『洗』，『夫』人立刻『察覺』不對勁。",
     "How do you perceive this situation?", "你怎麼看待這個情況？",
     [("perception", "名詞", "感知、看法", "Perception is not always reality.")]),
    ("persuade", "說服", "動詞", "[pɚˈswed]", "per-SWAYD", "破說的",
     "嘴皮子『破』了還在『說』，『的』確把人『說服』了。",
     "I persuaded him to join us.", "我說服了他加入我們。",
     [("persuasion", "名詞", "說服", "It took some persuasion.")]),
    ("precise", "精確的", "形容詞", "[prɪˈsaɪs]", "prih-SISE", "不理塞撕",
     "『不理』別人，把紙『塞』進機器『撕』得分毫不差，超『精確』。",
     "Please be precise about the time.", "請把時間說精確一點。",
     [("precisely", "副詞", "精確地", "That's precisely what I meant.")]),
    ("priority", "優先、優先事項", "名詞", "[praɪˈɔrətɪ]", "pry-OR-uh-tee", "拍歐了踢",
     "『拍』桌喊『歐』，把它放在最前『了』才『踢』走別的，這是『優先』。",
     "Safety is our top priority.", "安全是我們的首要之務。",
     [("prioritize", "動詞", "優先處理", "Let's prioritize the urgent tasks.")]),
    ("reluctant", "不情願的", "形容詞", "[rɪˈlʌktənt]", "rih-LUK-tunt", "蕊辣坦",
     "『蕊』（花蕊）被『辣』到還得『坦』白，一臉『不情願』。",
     "He was reluctant to admit his mistake.", "他不情願承認自己的錯。",
     [("reluctance", "名詞", "不情願", "She agreed with some reluctance.")]),
    ("resource", "資源", "名詞", "[ˈrisɔrs]", "REE-sors", "蕊縮死",
     "把花『蕊』『縮』到『死』也要省下這份『資源』。",
     "Water is a precious resource.", "水是珍貴的資源。",
     [("resourceful", "形容詞", "足智多謀的", "She's very resourceful.")]),
    ("strategy", "策略", "名詞", "[ˈstrætədʒɪ]", "STRAT-uh-jee", "史抓得急",
     "『史』官『抓』筆『得』很『急』，火速寫下作戰『策略』。",
     "We need a better marketing strategy.", "我們需要更好的行銷策略。",
     [("strategic", "形容詞", "策略性的", "It was a strategic decision.")]),
    ("sufficient", "足夠的", "形容詞", "[səˈfɪʃənt]", "suh-FISH-unt", "捨肥神",
     "肯『捨』出『肥』『神』的份量，份量就『足夠』了。",
     "We have sufficient time to finish.", "我們有足夠的時間完成。",
     [("sufficiently", "副詞", "充分地", "The room was sufficiently warm.")]),
]


def fmt_mnemonic(word, zh, pos, kk, phonics, homophone, image, ex_en, ex_zh, forms):
    lines = [f'    "{word}": {{']
    lines.append(f'        "kk": "{kk}",')
    lines.append(f'        "phonics": "{phonics}",')
    lines.append(f'        "homophone": "{homophone}",')
    lines.append(f'        "image": "{image}",')
    lines.append(f'        "example_en": "{ex_en}",')
    lines.append(f'        "example_zh": "{ex_zh}",')
    lines.append(f'        "pos": "{pos}",')
    if forms:
        fl = ", ".join(
            f'{{"word": "{w}", "pos": "{p}", "meaning_zh": "{m}", "example": "{e}"}}'
            for w, p, m, e in forms)
        lines.append(f'        "other_forms": [{fl}],')
    else:
        lines.append('        "other_forms": [],')
    lines.append("    },")
    return "\n".join(lines)


def main():
    from morphology import MNEMONICS
    from data import SEED_WORDS
    existing_mn = set(MNEMONICS)
    existing_seed = {w["word"] for w in SEED_WORDS}

    # --- 1. 注入 morphology.MNEMONICS（在最後一個 } 前插入）---
    mpath = os.path.join(ROOT, "morphology.py")
    msrc = open(mpath, encoding="utf-8").read()
    blocks, added_mn = [], []
    for row in NEW:
        word = row[0]
        if word in existing_mn:
            continue
        blocks.append(fmt_mnemonic(*row))
        added_mn.append(word)
    if blocks:
        # 找 MNEMONICS dict 的結尾：第一個出現在 'MNEMONICS = {' 之後、頂格的 '}'
        idx = msrc.index("MNEMONICS = {")
        close = msrc.index("\n}", idx)
        msrc = msrc[:close] + "\n" + "\n".join(blocks) + msrc[close:]
        open(mpath, "w", encoding="utf-8").write(msrc)

    # --- 2. 注入 data.SEED_WORDS ---
    dpath = os.path.join(ROOT, "data.py")
    dsrc = open(dpath, encoding="utf-8").read()
    seed_lines, added_seed = [], []
    for row in NEW:
        word, zh = row[0], row[1]
        ex_en = row[7]
        if word in existing_seed:
            continue
        seed_lines.append(
            f'    {{"word": "{word}", "meaning": "{zh}", "example": "{ex_en}"}},')
        added_seed.append(word)
    if seed_lines:
        marker = "SEED_WORDS = ["
        i = dsrc.index(marker)
        close = dsrc.index("\n]", i)
        dsrc = dsrc[:close] + "\n" + "\n".join(seed_lines) + dsrc[close:]
        open(dpath, "w", encoding="utf-8").write(dsrc)

    print(f"MNEMONICS 新增 {len(added_mn)}：{added_mn}")
    print(f"SEED_WORDS 新增 {len(added_seed)}：{added_seed}")


if __name__ == "__main__":
    main()
