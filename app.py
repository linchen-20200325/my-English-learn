# -*- coding: utf-8 -*-
"""
自動化遺產分配、特留分計算與保險避稅補償規劃系統
================================================
基於台灣《民法》繼承編、《遺產及贈與稅法》、《保險法》之確定性演算法。
部署目標：Streamlit Community Cloud。

四大階段：
  1. 淨資產與遺產總額計算
  2. 2026（115 年度）最新遺產稅率精算
  3. 民法應繼分、特留分與重組家庭痛點診斷（含第一～四順位＋配偶並存）
  4. 自動化保險節稅與補償推薦

作者：財富傳承精算 × Python 全端
"""

import streamlit as st

# =============================================================================
# 一、2026（115 年度）法定常數（單位：新台幣元）
# 集中管理所有稅法/民法數字，未來調整只需改這一區塊，避免魔術數字散落。
# =============================================================================
FUNERAL_DEDUCTION = 1_380_000        # 喪葬費扣除額（2026 固定 138 萬）
BASIC_EXEMPTION = 13_330_000         # 一般免稅額（1,333 萬）
SPOUSE_DEDUCTION = 5_530_000         # 配偶扣除額（553 萬）
CHILD_DEDUCTION = 560_000            # 直系血親卑親屬（子女）扣除額（56 萬/人）
PARENT_DEDUCTION = 1_380_000         # 直系尊親屬（父母）扣除額（138 萬/人）
ANNUAL_GIFT_EXEMPTION = 2_440_000    # 每年贈與稅免稅額（244 萬）

# 2026 累進稅率級距（課稅遺產淨額）
TAX_BRACKET_1 = 56_210_000           # 5,621 萬（10% 上限）
TAX_BRACKET_2 = 112_420_000          # 1 億 1,242 萬（15% 上限）
PROGRESSIVE_DIFF_15 = 2_810_500      # 15% 級距累進差額
PROGRESSIVE_DIFF_20 = 8_431_500      # 20% 級距累進差額

# 實質課稅原則警示門檻（可依實務調整）
HIGH_ASSET_ALERT = 100_000_000       # 資產過大警示線（1 億）
HIGH_AGE_ALERT = 75                  # 高齡警示線（避免臨終前躉繳被實質課稅）

WAN = 10_000                         # 「萬」換算


# =============================================================================
# 二、核心確定性演算法（純函式，與 UI 解耦，便於單元測試與邊界防禦）
# =============================================================================
def calc_net_estate(cash, stocks, land_value, house_value,
                    mortgage, private_debt, medical_debt):
    """
    第一階段：計算淨遺產總額。

    淨遺產總額 = (現金 + 股票 + 土地公告現值 + 房屋評定價格)
                 - 總負債 - 喪葬費扣除額(138 萬)

    防禦：所有輸入以 max(0, x) 夾住負值；結果若 < 0 自動歸零
         （代表限定繼承，繼承人不需以自身財產償債，遺產不可為負）。
    """
    # 邊界防禦：任何欄位不接受負數輸入
    total_assets = (max(0, cash) + max(0, stocks)
                    + max(0, land_value) + max(0, house_value))
    total_debt = max(0, mortgage) + max(0, private_debt) + max(0, medical_debt)

    net = total_assets - total_debt - FUNERAL_DEDUCTION
    net = max(0, net)  # 限定繼承：不得出現負遺產

    return {
        "total_assets": total_assets,
        "total_debt": total_debt,
        "funeral_deduction": FUNERAL_DEDUCTION,
        "net_estate": net,
    }


def calc_estate_tax(net_estate, has_spouse, num_children, num_parents=0):
    """
    第二階段：2026 遺產稅精算。

    課稅遺產淨額 = 淨遺產總額 - 免稅額 - 各項扣除額（最低為 0）
      各項扣除額 = (配偶 553 萬 if 有配偶)
                 + 子女 56 萬 × 人數
                 + 父母 138 萬 × 人數（最多 2 人）
    註：遺產稅扣除額依《遺贈稅法》§17 以「遺有之親屬」計算，與實際由誰繼承無關，
        故父母只要在世即可扣除，即使由子女（第一順位）繼承亦然。
    再套用 2026 累進級距計算應納遺產稅。
    """
    num_children = max(0, int(num_children))            # 邊界：人數不可為負
    num_parents = max(0, min(int(num_parents), 2))      # 父母最多 2 人

    spouse_deduction = SPOUSE_DEDUCTION if has_spouse else 0
    children_deduction = CHILD_DEDUCTION * num_children
    parents_deduction = PARENT_DEDUCTION * num_parents
    total_deduction = (BASIC_EXEMPTION + spouse_deduction
                       + children_deduction + parents_deduction)

    taxable = max(0, net_estate - total_deduction)  # 課稅淨額最低為 0

    # 2026 累進級距：稅額 = 課稅淨額 × 稅率 - 累進差額
    if taxable <= TAX_BRACKET_1:
        rate, diff = 0.10, 0
    elif taxable <= TAX_BRACKET_2:
        rate, diff = 0.15, PROGRESSIVE_DIFF_15
    else:
        rate, diff = 0.20, PROGRESSIVE_DIFF_20

    tax = max(0, taxable * rate - diff)

    return {
        "basic_exemption": BASIC_EXEMPTION,
        "spouse_deduction": spouse_deduction,
        "children_deduction": children_deduction,
        "parents_deduction": parents_deduction,
        "total_deduction": total_deduction,
        "taxable": taxable,
        "rate": rate,
        "progressive_diff": diff,
        "tax": tax,
    }


def calc_inheritance(net_estate, has_spouse, num_children,
                     num_parents, num_siblings, num_grandparents,
                     num_excluded):
    """
    第三階段：依民法決定「實際繼承順位」、應繼分與特留分（含第二～四順位與配偶並存）。

    繼承順位（民法 §1138）：① 直系血親卑親屬（子女）② 父母 ③ 兄弟姊妹 ④ 祖父母。
    僅「最優先且有人」的血親順位參與繼承；配偶（§1144）恆與該順位並存：
      - 與 ①：配偶與卑親屬「按人數平均分」。
      - 與 ② 或 ③：配偶得 1/2，該順位均分另 1/2。
      - 與 ④：配偶得 2/3，祖父母均分 1/3。
      - 無任何血親順位：配偶單獨繼承（全部）。
      - 無配偶：由該順位均分全部。
    特留分（民法 §1223）：
      - 直系血親卑親屬、父母、配偶 → 應繼分之 1/2。
      - 兄弟姊妹、祖父母 → 應繼分之 1/3。

    「不想給遺產的特定人」僅適用於第一順位子女（重組家庭核心痛點）；
    其可強制主張之特留分總額 = 淨遺產 × 每位成員特留分比例 × 不想給人數。
    """
    # 邊界防禦：夾住負值與上限
    num_children = max(0, int(num_children))
    num_parents = max(0, min(int(num_parents), 2))
    num_siblings = max(0, int(num_siblings))
    num_grandparents = max(0, min(int(num_grandparents), 4))

    # 決定實際參與繼承的血親順位（只有最優先且有人者繼承）
    if num_children > 0:
        order_name, members, reserve_ratio = "第一順位・直系血親卑親屬（子女）", num_children, 0.5
    elif num_parents > 0:
        order_name, members, reserve_ratio = "第二順位・父母", num_parents, 0.5
    elif num_siblings > 0:
        order_name, members, reserve_ratio = "第三順位・兄弟姊妹", num_siblings, 1.0 / 3.0
    elif num_grandparents > 0:
        order_name, members, reserve_ratio = "第四順位・祖父母", num_grandparents, 1.0 / 3.0
    else:
        order_name, members, reserve_ratio = None, 0, 0.0

    is_first_order = order_name is not None and order_name.startswith("第一")

    # ── 應繼分（配偶 vs 成員）依民法 §1144 ──
    spouse_inherit = 0.0
    member_inherit = 0.0
    if members > 0 and has_spouse:
        if is_first_order:                                  # 與卑親屬：平均分
            spouse_inherit = member_inherit = 1.0 / (members + 1)
        elif order_name.startswith("第二") or order_name.startswith("第三"):
            spouse_inherit, member_inherit = 0.5, 0.5 / members
        else:                                               # 第四順位：配偶 2/3
            spouse_inherit, member_inherit = 2.0 / 3.0, (1.0 / 3.0) / members
    elif members > 0 and not has_spouse:                    # 無配偶：該順位均分
        member_inherit = 1.0 / members
    elif members == 0 and has_spouse:                       # 無血親：配偶單獨繼承
        spouse_inherit = 1.0
    # else：無配偶且無血親 → 無人繼承（歸國庫）

    # ── 特留分：配偶恆為應繼分 1/2；成員依 reserve_ratio ──
    spouse_reserve = spouse_inherit * 0.5
    member_reserve = member_inherit * reserve_ratio

    # 「不想給」僅適用第一順位子女
    excluded = max(0, min(int(num_excluded), num_children)) if is_first_order else 0
    reserved_total = net_estate * member_reserve * excluded

    total_heirs = members + (1 if has_spouse else 0)

    return {
        "order_name": order_name,
        "members": members,
        "total_heirs": total_heirs,
        "has_spouse": has_spouse,
        "spouse_inherit": spouse_inherit,
        "member_inherit": member_inherit,
        "spouse_reserve": spouse_reserve,
        "member_reserve": member_reserve,
        "reserve_ratio": reserve_ratio,
        "num_excluded": excluded,
        "reserved_total": reserved_total,
        "has_heir": total_heirs > 0,
        "is_first_order": is_first_order,
    }


def calc_insurance_plan(estate_tax, reserved_total):
    """
    第四階段：自動化保險節稅與補償推薦。

    策略Ａ 預留稅源保單：保額 = 遺產稅總額（受益人＝心儀繼承人，備妥繳稅現金）。
    策略Ｂ 特留分補償保單：保額 = 特留分總額（利用《保險法》§112 保險金不列入遺產，
             將財富補償給想給的人）。
    """
    return {
        "plan_a_tax_reserve": max(0, estate_tax),        # 策略Ａ 保額
        "plan_b_reserved_comp": max(0, reserved_total),  # 策略Ｂ 保額
        "total_coverage": max(0, estate_tax) + max(0, reserved_total),
    }


# =============================================================================
# 三、輔助顯示函式
# =============================================================================
def fmt_ntd(amount):
    """格式化為新台幣（含千分位），並附上「萬」的直覺換算。"""
    amount = round(amount)
    return f"NT$ {amount:,.0f} 元（約 {amount / WAN:,.1f} 萬）"


# =============================================================================
# 四、Streamlit UI
# =============================================================================
def main():
    st.set_page_config(
        page_title="遺產稅・特留分・保險傳承規劃系統",
        page_icon="🏛️",
        layout="wide",
    )

    st.title("🏛️ 自動化遺產分配・特留分計算・保險避稅補償規劃系統")
    st.caption(
        "依 2026（115 年度）台灣《遺產及贈與稅法》、《民法》繼承編、"
        "《保險法》§112 之確定性演算法。本工具僅供試算參考，實際申報請洽會計師／地政士。"
    )

    # ---------------------------------------------------------------------
    # 側邊欄：家庭結構與資產負債輸入
    # ---------------------------------------------------------------------
    with st.sidebar:
        st.header("👪 家庭結構")
        age = st.number_input(
            "被繼承人年齡（歲）", min_value=0, max_value=120, value=65, step=1,
            help="用於『實質課稅原則』風險評估，高齡臨終前躉繳保單易被國稅局補稅。",
        )
        has_spouse = st.checkbox("是否有現任配偶", value=True)

        st.markdown("**第一順位：子女（直系血親卑親屬）**")
        num_children = st.number_input(
            "親生子女總數（含前段婚姻與現任子女）",
            min_value=0, max_value=30, value=2, step=1,
        )
        num_prev_children = st.number_input(
            "↳ 其中『前段婚姻』所生子女數（重組家庭）",
            min_value=0, max_value=int(num_children), value=0, step=1,
            help="前婚子女在法律上與現任子女同為第一順位，應繼分／特留分完全相同，"
                 "不能僅因非現任配偶所生而剝奪。此欄僅供重組家庭情境說明。",
        )
        num_excluded = st.number_input(
            "「不想給遺產」的特定子女人數",
            min_value=0, max_value=int(num_children), value=0, step=1,
            help="這些人依民法 §1223 仍可強制主張『特留分』，需以保險補償繞道規劃。",
        )

        st.markdown("**後順位（無子女時才繼承）**")
        num_parents = st.number_input(
            "在世父母人數（第二順位，0–2）",
            min_value=0, max_value=2, value=0, step=1,
            help="無子女時，遺產由『配偶＋父母』共同繼承（配偶 1/2、父母均分 1/2）。",
        )
        num_siblings = st.number_input(
            "兄弟姊妹人數（第三順位）",
            min_value=0, max_value=20, value=0, step=1,
            help="無子女且無父母時，遺產由『配偶＋兄弟姊妹』共同繼承（配偶 1/2、手足均分 1/2）。",
        )
        num_grandparents = st.number_input(
            "在世祖父母人數（第四順位，0–4）",
            min_value=0, max_value=4, value=0, step=1,
            help="無子女、父母、兄弟姊妹時，遺產由『配偶＋祖父母』共同繼承（配偶 2/3、祖父母均分 1/3）。",
        )

        st.divider()
        st.header("💰 資產（正值）")
        cash = st.number_input("現金與銀行存款（元）", min_value=0.0,
                               value=10_000_000.0, step=100_000.0, format="%.0f")
        stocks = st.number_input("上市櫃股票（以市價計，元）", min_value=0.0,
                                 value=5_000_000.0, step=100_000.0, format="%.0f")
        land_value = st.number_input(
            "土地（請填『公告現值』，非市價，元）", min_value=0.0,
            value=30_000_000.0, step=100_000.0, format="%.0f",
            help="土地以『公告現值』計入遺產，通常遠低於市價。",
        )
        house_value = st.number_input(
            "房屋（請填『評定標準價格』，非市價，元）", min_value=0.0,
            value=8_000_000.0, step=100_000.0, format="%.0f",
            help="房屋以『房屋評定標準價格』計入遺產，非成交市價。",
        )

        st.divider()
        st.header("📉 負債（正值）")
        mortgage = st.number_input("房屋貸款餘額（元）", min_value=0.0,
                                   value=0.0, step=100_000.0, format="%.0f")
        private_debt = st.number_input("私人未償債務（元）", min_value=0.0,
                                       value=0.0, step=100_000.0, format="%.0f")
        medical_debt = st.number_input("生前未結醫藥費（元）", min_value=0.0,
                                       value=0.0, step=100_000.0, format="%.0f")

    # ---------------------------------------------------------------------
    # 後台計算（純函式，O(1)，無需 st.cache_data）
    # ---------------------------------------------------------------------
    estate = calc_net_estate(cash, stocks, land_value, house_value,
                             mortgage, private_debt, medical_debt)
    net = estate["net_estate"]
    tax_info = calc_estate_tax(net, has_spouse, num_children, num_parents)
    heirs = calc_inheritance(net, has_spouse, num_children,
                             num_parents, num_siblings, num_grandparents,
                             num_excluded)
    insurance = calc_insurance_plan(tax_info["tax"], heirs["reserved_total"])

    # =====================================================================
    # 區塊一：資產健康診斷
    # =====================================================================
    st.header("① 資產健康診斷")
    c1, c2, c3 = st.columns(3)
    c1.metric("資產總額", fmt_ntd(estate["total_assets"]))
    c2.metric("負債總額", fmt_ntd(estate["total_debt"]))
    c3.metric("喪葬費扣除額", fmt_ntd(estate["funeral_deduction"]))

    st.metric("💠 淨遺產總額", fmt_ntd(net),
              help="= 資產總額 − 負債總額 − 喪葬費 138 萬；小於 0 自動歸零（限定繼承）。")

    if estate["total_assets"] < estate["total_debt"]:
        st.error(
            "⚠️ 資產小於負債：建議繼承人考慮辦理『限定繼承』或『拋棄繼承』，"
            "以免以自身財產代償被繼承人債務。淨遺產已歸零。"
        )
    elif net == 0:
        st.warning("扣除負債與喪葬費後淨遺產為 0，無遺產稅負擔。")
    else:
        st.success("資產結構健康，續看稅務與特留分精算。")

    st.divider()

    # =====================================================================
    # 區塊二：2026 稅務與特留分精算
    # =====================================================================
    st.header("② 2026 稅務與特留分精算")

    st.subheader("💵 遺產稅試算")
    t1, t2, t3 = st.columns(3)
    t1.metric("各項扣除額合計", fmt_ntd(tax_info["total_deduction"]),
              help=f"免稅額 {BASIC_EXEMPTION/WAN:.0f} 萬 "
                   f"＋配偶 {tax_info['spouse_deduction']/WAN:.0f} 萬 "
                   f"＋子女 {tax_info['children_deduction']/WAN:.0f} 萬 "
                   f"＋父母 {tax_info['parents_deduction']/WAN:.0f} 萬")
    t2.metric("課稅遺產淨額", fmt_ntd(tax_info["taxable"]))
    t3.metric(f"預估遺產稅（適用 {tax_info['rate']*100:.0f}%）",
              fmt_ntd(tax_info["tax"]))

    with st.expander("🔍 遺產稅計算明細"):
        st.markdown(
            f"""
| 項目 | 金額 |
|---|---|
| 淨遺產總額 | {fmt_ntd(net)} |
| （−）一般免稅額 | {fmt_ntd(tax_info['basic_exemption'])} |
| （−）配偶扣除額 | {fmt_ntd(tax_info['spouse_deduction'])} |
| （−）子女扣除額 | {fmt_ntd(tax_info['children_deduction'])} |
| （−）父母扣除額 | {fmt_ntd(tax_info['parents_deduction'])} |
| （＝）**課稅遺產淨額** | **{fmt_ntd(tax_info['taxable'])}** |
| 適用稅率 | {tax_info['rate']*100:.0f}% |
| 累進差額 | {fmt_ntd(tax_info['progressive_diff'])} |
| （＝）**應納遺產稅** | **{fmt_ntd(tax_info['tax'])}** |

> 稅額公式：課稅淨額 × 稅率 − 累進差額
"""
        )

    st.subheader("⚖️ 民法應繼分／特留分診斷")
    if not heirs["has_heir"]:
        st.warning(
            "目前無配偶、無子女、無父母、無兄弟姊妹、無祖父母 —— 全無法定繼承人，"
            "遺產將歸屬國庫（民法 §1185）。"
        )
    else:
        # 顯示實際繼承順位（重點：無子女時會落到父母／兄弟姊妹／祖父母）
        if heirs["order_name"]:
            st.info(f"🧭 實際參與繼承：**配偶** ＋ **{heirs['order_name']}** "
                    f"（僅最優先且有人的血親順位繼承）"
                    if heirs["has_spouse"] else
                    f"🧭 實際參與繼承：**{heirs['order_name']}**（無配偶）")
        else:
            st.info("🧭 實際參與繼承：**配偶單獨繼承**（無任何血親順位在世）")

        cols = st.columns(3)
        cols[0].metric("法定繼承人數", f"{heirs['total_heirs']} 人")
        if heirs["has_spouse"]:
            cols[1].metric("配偶應繼分", f"{heirs['spouse_inherit']*100:.2f}%")
            cols[2].metric("配偶特留分", f"{heirs['spouse_reserve']*100:.2f}%")
        if heirs["members"] > 0:
            m1, m2 = st.columns(2)
            m1.metric(f"每位成員應繼分（{heirs['order_name'].split('・')[-1]}）",
                      f"{heirs['member_inherit']*100:.2f}%")
            m2.metric("每位成員特留分",
                      f"{heirs['member_reserve']*100:.2f}%",
                      help=f"特留分 = 應繼分 × {heirs['reserve_ratio']:.3g}"
                           "（卑親屬/父母/配偶 1/2；兄弟姊妹/祖父母 1/3）")

        # 重組家庭專屬診斷
        if num_prev_children > 0:
            st.info(
                f"👨‍👩‍👧 **重組家庭診斷**：你有 {num_children} 位子女，其中 "
                f"{num_prev_children} 位為前段婚姻所生。**前婚子女與現任子女法律上完全平等**"
                f"（同為第一順位），各自應繼分 {heirs['member_inherit']*100:.2f}%、"
                f"特留分 {heirs['member_reserve']*100:.2f}%，"
                "無法僅以遺囑剝奪。若想讓財富偏向現任家庭，須靠下方【策略Ｂ】保險補償。"
            )

        if heirs["num_excluded"] > 0 and heirs["reserved_total"] > 0:
            st.warning(
                f"🚨 你指定 {heirs['num_excluded']} 位子女不予分配，"
                f"但依民法 §1223，他們仍可合計強制主張 "
                f"**{fmt_ntd(heirs['reserved_total'])}** 的特留分。"
                "→ 請見下方【策略Ｂ】以保險金繞道補償想給的人。"
            )
        st.metric(
            "🚨 特定人可強制分走的『特留分總額』",
            fmt_ntd(heirs["reserved_total"]),
            help="= 淨遺產總額 × 每位成員特留分比例 × 不想給的子女人數；"
                 "即使立遺囑排除，這些人仍可依民法主張此金額。",
        )

    st.divider()

    # =====================================================================
    # 區塊三：自動化保險傳承方案
    # =====================================================================
    st.header("③ 自動化保險傳承方案")

    i1, i2 = st.columns(2)
    with i1:
        st.metric("【策略Ａ】預留稅源保單保額", fmt_ntd(insurance["plan_a_tax_reserve"]))
        st.markdown(
            "**目的**：身故保險金＝遺產稅總額，指定**心儀繼承人**為受益人。\n\n"
            "確保繼承人有**現金繳稅**，避免土地、房屋因繳不出稅金遭國稅局實物抵繳或法拍，"
            "保全不動產完整傳承。"
        )
    with i2:
        st.metric("【策略Ｂ】特留分補償保單保額", fmt_ntd(insurance["plan_b_reserved_comp"]))
        st.markdown(
            "**目的**：身故保險金＝特留分總額，指定**想給的受益人**。\n\n"
            "依《保險法》§112「保險金不作為被保險人遺產」，此金額不列入遺產分割、"
            "亦不受特留分主張追及，達成財富定向傳承。"
        )

    st.metric("🎯 建議規劃保險總保額（Ａ＋Ｂ）", fmt_ntd(insurance["total_coverage"]))

    st.divider()

    # =====================================================================
    # 實質課稅原則警示紅線
    # =====================================================================
    st.header("🚩 實質課稅原則警示紅線")
    alerts = []
    if estate["total_assets"] >= HIGH_ASSET_ALERT:
        alerts.append(
            f"**資產規模達 {estate['total_assets']/WAN:,.0f} 萬**（≥ 1 億），"
            "屬國稅局重點稽核對象。"
        )
    if age >= HIGH_AGE_ALERT:
        alerts.append(
            f"**被繼承人年齡 {age} 歲**（≥ {HIGH_AGE_ALERT} 歲），"
            "臨終前短期內躉繳大額保單，易被認定『帶病投保／規避稅負』而遭實質課稅。"
        )

    if alerts:
        st.error(
            "偵測到以下實質課稅風險，請務必採取防禦性規劃：\n\n"
            + "\n".join(f"- {a}" for a in alerts)
            + "\n\n**建議做法：**\n"
            "1. 保單改採**分期繳（非躉繳）**，拉長投保與身故間隔，降低『規避意圖』認定。\n"
            f"2. 結合**分年贈與**：善用每人每年 {ANNUAL_GIFT_EXEMPTION/WAN:.0f} 萬"
            "贈與稅免稅額，由**子女擔任要保人**逐年繳費，資產與稅源提早移轉。\n"
            "3. 保留完整**財務規劃軌跡與健康證明**，避免『重病期間投保、鉅額投保、"
            "短期投保、躉繳投保、舉債投保、高齡投保、密集投保、保費≒保額』等實質課稅八大態樣。"
        )
    else:
        st.success(
            "目前資產規模與年齡未觸及實質課稅高風險門檻。仍建議儘早以分年贈與"
            f"（每年 {ANNUAL_GIFT_EXEMPTION/WAN:.0f} 萬免稅）＋分期繳保單穩健佈局。"
        )

    st.caption(
        "免責聲明：本系統為確定性試算工具，數字依 2026 公告參數計算，"
        "不構成稅務或法律意見。實際個案請諮詢專業會計師、地政士或律師。"
    )


if __name__ == "__main__":
    main()
