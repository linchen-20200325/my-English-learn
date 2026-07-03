# -*- coding: utf-8 -*-
"""
自動化遺產分配、特留分計算與保險避稅補償規劃系統
================================================
基於台灣《民法》繼承編、《遺產及贈與稅法》、《保險法》之確定性演算法。
部署目標：Streamlit Community Cloud。

四大階段：
  1. 淨資產與遺產總額計算
  2. 2026（115 年度）最新遺產稅率精算
  3. 民法應繼分、特留分與重組家庭痛點診斷
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


def calc_estate_tax(net_estate, has_spouse, num_children):
    """
    第二階段：2026 遺產稅精算。

    課稅遺產淨額 = 淨遺產總額 - 免稅額 - 各項扣除額（最低為 0）
      各項扣除額 = (配偶 553 萬 if 有配偶) + 子女 56 萬 × 人數
    再套用 2026 累進級距計算應納遺產稅。
    """
    num_children = max(0, int(num_children))  # 邊界：人數不可為負

    spouse_deduction = SPOUSE_DEDUCTION if has_spouse else 0
    children_deduction = CHILD_DEDUCTION * num_children
    total_deduction = BASIC_EXEMPTION + spouse_deduction + children_deduction

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
        "total_deduction": total_deduction,
        "taxable": taxable,
        "rate": rate,
        "progressive_diff": diff,
        "tax": tax,
    }


def calc_reserved_portion(net_estate, has_spouse, num_children, num_excluded):
    """
    第三階段：民法應繼分 / 特留分與重組家庭診斷。

    - 總法定繼承人數(第一順位) = 子女總數 + (1 if 有配偶)
    - 應繼分比例 = 1 / 總繼承人數
    - 特留分比例 = 應繼分 × 1/2（民法 §1223 直系血親卑親屬為應繼分二分之一）
    - 特定人可強制主張之「特留分總額」= 淨遺產總額 × 特留分比例 × 不想給的子女人數
    """
    num_children = max(0, int(num_children))
    # 邊界：不想給的人數不可超過實際子女數，也不可為負
    num_excluded = max(0, min(int(num_excluded), num_children))

    total_heirs = num_children + (1 if has_spouse else 0)

    # 邊界：無任何繼承人時，避免除以零
    if total_heirs == 0:
        return {
            "total_heirs": 0,
            "inherit_ratio": 0.0,
            "reserved_ratio": 0.0,
            "reserved_total": 0,
            "num_excluded": 0,
            "has_heir": False,
        }

    inherit_ratio = 1.0 / total_heirs
    reserved_ratio = inherit_ratio * 0.5
    reserved_total = net_estate * reserved_ratio * num_excluded

    return {
        "total_heirs": total_heirs,
        "inherit_ratio": inherit_ratio,
        "reserved_ratio": reserved_ratio,
        "reserved_total": reserved_total,
        "num_excluded": num_excluded,
        "has_heir": True,
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
        num_children = st.number_input(
            "親生子女總數（含前段婚姻與現任子女）",
            min_value=0, max_value=30, value=2, step=1,
        )
        num_excluded = st.number_input(
            "「不想給遺產」的特定子女人數",
            min_value=0, max_value=int(num_children), value=0, step=1,
            help="這些人依民法 §1223 仍可強制主張『特留分』，需以保險補償繞道規劃。",
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
    tax_info = calc_estate_tax(net, has_spouse, num_children)
    reserved = calc_reserved_portion(net, has_spouse, num_children, num_excluded)
    insurance = calc_insurance_plan(tax_info["tax"], reserved["reserved_total"])

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
                   f"＋子女 {tax_info['children_deduction']/WAN:.0f} 萬")
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
| （＝）**課稅遺產淨額** | **{fmt_ntd(tax_info['taxable'])}** |
| 適用稅率 | {tax_info['rate']*100:.0f}% |
| 累進差額 | {fmt_ntd(tax_info['progressive_diff'])} |
| （＝）**應納遺產稅** | **{fmt_ntd(tax_info['tax'])}** |

> 稅額公式：課稅淨額 × 稅率 − 累進差額
"""
        )

    st.subheader("⚖️ 民法應繼分／特留分診斷")
    if not reserved["has_heir"]:
        st.warning(
            "目前無配偶且無子女（第一順位繼承人為 0）。遺產將依序由父母、"
            "兄弟姊妹、祖父母繼承；若全無繼承人則歸屬國庫。本工具僅計算第一順位。"
        )
    else:
        r1, r2, r3 = st.columns(3)
        r1.metric("法定繼承人數（第一順位）", f"{reserved['total_heirs']} 人")
        r2.metric("每人應繼分比例", f"{reserved['inherit_ratio']*100:.2f}%")
        r3.metric("每人特留分比例", f"{reserved['reserved_ratio']*100:.2f}%")

        st.metric(
            "🚨 特定人可強制分走的『特留分總額』",
            fmt_ntd(reserved["reserved_total"]),
            help="= 淨遺產總額 × 特留分比例 × 不想給的子女人數；"
                 "即使立遺囑排除，這些人仍可依民法主張此金額。",
        )
        if reserved["num_excluded"] > 0 and reserved["reserved_total"] > 0:
            st.warning(
                f"你指定 {reserved['num_excluded']} 位子女不予分配，"
                f"但依民法 §1223，他們仍可合計強制主張 "
                f"**{fmt_ntd(reserved['reserved_total'])}** 的特留分。"
                "→ 請見下方【策略Ｂ】以保險金繞道補償想給的人。"
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
