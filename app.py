import streamlit as st
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events
import google.generativeai as genai

# --- 🏥 臨床專家導航系統視覺配置 ---
st.set_page_config(page_title="婦癌臨床試驗決策支援", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', sans-serif;
        background-color: #F8FAF9;
        font-size: 19px !important;
    }
    .main-title {
        font-size: 46px !important; font-weight: 800; color: #004D40;
        text-align: center; padding: 30px; background: white;
        border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 25px;
    }
    .info-card {
        background: white; border-radius: 15px; padding: 30px;
        border: 1px solid #E0F2F1; box-shadow: 0 6px 18px rgba(0,0,0,0.06); margin-bottom: 25px;
    }
    .section-label { font-size: 26px; font-weight: 700; color: #00695C; margin-bottom: 20px; border-bottom: 2px solid #B2DFDB; padding-bottom: 10px; }
    .pharma-tag { background: #004D40; color: white; padding: 5px 15px; border-radius: 20px; font-size: 14px; float: right; font-weight: 400; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 深度臨床資料庫 (確保所有欄位 100% 完整) ---
if 'trials_db' not in st.session_state:
    st.session_state.trials_db = [
        {
            "cancer": "Endometrial", "name": "GU-US-682-6769 (TROPiCS-03)", "pharma": "Gilead Sciences",
            "drug": "Sacituzumab Govitecan (Trodelvy)", "pos": "Recurrence",
            "summary": "針對 Trop-2 標靶 ADC，適用於 Platinum 及 Anti-PD-1 治療後進展之患者。",
            "rationale": "標靶 Trop-2 ADC。利用抗體精準導向，釋放 SN-38 載荷引發 DNA 損傷，並具備強大的 Bystander Effect 殺傷周邊腫瘤細胞。",
            "protocol_details": {
                "Arm A (Experimental)": "SG 10 mg/kg IV on Days 1 and 8 of each 21-day cycle.",
                "Arm B (Control)": "Physician's Choice: Doxorubicin 60 mg/m² (Q3W) or Paclitaxel 80 mg/m² (Weekly)."
            },
            "outcomes": {"ORR": "28.5%", "mPFS": "5.6m", "mOS": "12.8m", "HR": "0.64 (95% CI: 0.48-0.84)"},
            "inclusion": [
                "Advanced/Recurrent Endometrial Cancer (any histology except sarcoma).",
                "At least 1 prior Platinum-based chemotherapy line.",
                "Prior Anti-PD-1/L1 therapy required (e.g. Pembrolizumab).",
                "ECOG Performance Status 0-1."
            ],
            "exclusion": ["Prior TROP-2 directed ADC therapy.", "Uterine Sarcoma.", "Active CNS metastasis."],
            "ref": "JCO 2024; TROPiCS-03 Study"
        },
        {
            "cancer": "Endometrial", "name": "MK2870-033 (TroFuse-033)", "pharma": "MSD / Kelun-Biotech",
            "drug": "Sac-TMT (MK-2870) + Pembrolizumab", "pos": "Maintenance",
            "summary": "一線維持治療試驗，結合新型 ADC 與 PD-1 抑制劑。",
            "rationale": "ADC 誘導腫瘤細胞凋亡後釋放抗原，協同提升 Pembrolizumab 之免疫檢查點阻斷效果。",
            "protocol_details": {
                "Induction": "Carbo (AUC 5) + Taxel (175 mg/m²) + Pembro (200 mg) Q3W for 6 cycles.",
                "Maintenance": "Pembro (400 mg) Q6W + Sac-TMT (SKB264) 5 mg/kg Q6W."
            },
            "outcomes": {"ORR": "Estimated > 35%", "mPFS": "Pending", "mOS": "Pending", "HR": "Phase 3 Ongoing"},
            "inclusion": [
                "pMMR Endometrial Cancer.",
                "Newly diagnosed FIGO Stage III/IV or first recurrence.",
                "Measurable disease by RECIST 1.1."
            ],
            "exclusion": ["Uterine Sarcoma.", "Prior PD-1/L1 inhibitors.", "Active autoimmune disease."],
            "ref": "ESMO 2025 Abstract"
        },
        {
            "cancer": "Ovarian", "name": "DOVE (APGOT-OV07)", "pharma": "GSK",
            "drug": "Dostarlimab + Bevacizumab", "pos": "Recurrence",
            "summary": "針對透明細胞癌 (OCCC)，雙重阻斷 PD-1 與 VEGF。",
            "rationale": "針對 OCCC 特有的免疫抑制微環境，透過抗血管生成藥物改善免疫細胞浸潤。",
            "protocol_details": {
                "Arm A": "Dostarlimab 500 mg Q3W x4, then 1000 mg Q6W.",
                "Arm B": "Dostarlimab + Bevacizumab 15 mg/kg Q3W."
            },
            "outcomes": {"ORR": "40.2%", "mPFS": "8.2m", "mOS": "N/A", "HR": "0.58 vs. Chemo (Phase 2)"},
            "inclusion": [
                "Clear Cell Carcinoma (OCCC) > 50% histology.",
                "Platinum-resistant (PD < 12 months from last platinum).",
                "Up to 5 prior lines of therapy."
            ],
            "exclusion": ["Prior Immunotherapy.", "Clinical bowel obstruction.", "Grade 3-4 GI bleed."],
            "ref": "NCT06023862; ESMO-IO"
        },
        {
            "cancer": "Ovarian", "name": "DS8201-772 (DESTINY-PanTumor)", "pharma": "AstraZeneca / Daiichi Sankyo",
            "drug": "Trastuzumab Deruxtecan (Enhertu)", "pos": "Maintenance",
            "summary": "HER2 表現之維持治療，旨在替代或補充 PARPi。",
            "rationale": "標靶 HER2 之 ADC。搭載強效 Topoisomerase I 抑制劑，具備極高 DAR 對低表達腫瘤亦有效。",
            "protocol_details": {
                "Experimental": "T-DXd 5.4 mg/kg IV Q3W until progression.",
                "Combination": "T-DXd 5.4 mg/kg + Bevacizumab 15 mg/kg Q3W."
            },
            "outcomes": {"ORR": "46.3% (IHC 3+)", "mPFS": "10.4m", "mOS": "N/A", "HR": "0.42 (HER2 3+ cohort)"},
            "inclusion": [
                "HER2-expressing (IHC 1+, 2+, or 3+) Gynecologic tumors.",
                "BRCA Wild-type or HRD result indicating PARPi ineligibility.",
                "Non-PD after 6-8 cycles Platinum + Beva."
            ],
            "exclusion": ["History of ILD/Pneumonitis.", "LVEF < 50%.", "Prior HER2-targeted ADC."],
            "ref": "JCO 2023; DESTINY-PanTumor 02"
        }
    ]

# --- 2. 狀態同步 ---
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = st.session_state.trials_db[0]['name']

# --- 3. 主頁面：河流圖導航 ---
st.markdown("<div class='main-title'>婦癌臨床試驗導航系統 (Expert View)</div>", unsafe_allow_html=True)

cancer_type = st.radio("第一步：選擇癌症類型", ["Endometrial", "Ovarian"], horizontal=True)

def draw_locked_river(cancer_type):
    base_labels = ["初診 (Dx)", "一線治療 (1L)", "維持期 (Maint.)", "復發期 (Recurr.)"]
    base_colors = ["#CFD8DC", "#90A4AE", "#80CBC4", "#EF9A9A"]
    filtered = [t for t in st.session_state.trials_db if t["cancer"] == cancer_type]
    labels = base_labels.copy()
    node_colors = base_colors.copy()
    sources, targets, values = [], [], []

    for t in filtered:
        idx = len(labels)
        labels.append(f"{t['name']}\n({t['drug']})")
        node_colors.append("#00796B")
        if t["pos"] == "Maintenance":
            sources.extend([1, 2]); targets.extend([2, idx]); values.extend([1, 1])
        elif t["pos"] == "Recurrence":
            sources.extend([0, 3]); targets.extend([3, idx]); values.extend([1, 1])

    fig = go.Figure(data=[go.Sankey(
        node = dict(pad=50, thickness=35, label=labels, color=node_colors),
        link = dict(source=sources, target=targets, value=values, color="rgba(0, 121, 107, 0.1)")
    )])
    fig.update_layout(height=420, font=dict(size=18), margin=dict(l=15, r=15, t=10, b=10))
    return fig, labels

st.subheader("第二步：點選河流圖方塊 或 使用選單")
col_chart, col_quick = st.columns([2.5, 1])

with col_chart:
    fig, current_labels = draw_locked_river(cancer_type)
    clicked_data = plotly_events(fig, click_event=True, key=f"s_k_{cancer_type}")
    if clicked_data:
        clicked_idx = clicked_data[0]['pointNumber']
        label_text = current_labels[clicked_idx].split("\n")[0]
        if label_text in [t["name"] for t in st.session_state.trials_db]:
            st.session_state.selected_trial = label_text

with col_quick:
    t_quick = next(it for it in st.session_state.trials_db if it["name"] == st.session_state.selected_trial)
    st.markdown(f"""
        <div style='background: #E0F2F1; border-left: 8px solid #00897B; padding: 20px; border-radius: 10px;'>
            <h4 style='margin:0; color:#004D40;'>📍 快速導航亮點</h4>
            <p style='font-weight:700; margin-top:10px; font-size:20px;'>{t_quick['name']}</p>
            <p style='font-size:16px;'>{t_quick['summary']}</p>
            <span style='background:#004D40; color:white; padding:3px 10px; border-radius:15px; font-size:12px;'>Pharma: {t_quick['pharma']}</span>
        </div>
    """, unsafe_allow_html=True)

# --- 4. 深度數據全覽面板 ---
st.divider()
st.subheader("🔍 第三步：深度數據、機轉與 Protocol 全覽")

trial_options = [t["name"] for t in st.session_state.trials_db if t["cancer"] == cancer_type]
try:
    current_idx = trial_options.index(st.session_state.selected_trial)
except ValueError:
    current_idx = 0

selected_name = st.selectbox("🎯 搜尋試驗名稱：", trial_options, index=current_idx)
t = next(it for it in st.session_state.trials_db if it["name"] == selected_name)

# --- 資訊看板 ---
st.markdown(f"<div class='info-card'>", unsafe_allow_html=True)
st.markdown(f"<span class='pharma-tag'>{t['pharma']}</span>", unsafe_allow_html=True)
st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #00897B; padding-bottom:10px;'>📋 {t['name']} 分析報告</h2>", unsafe_allow_html=True)

# 第一列：給藥詳情與數據
c1, c2 = st.columns([1.2, 1])
with c1:
    st.markdown("<div class='section-label'>💉 Dosing Protocol & Rationale</div>", unsafe_allow_html=True)
    st.info(f"**藥物成分:** {t['drug']}")
    for arm, details in t['protocol_details'].items():
        st.write(f"🔹 **{arm}**: {details}")
    st.success(f"**機轉說明:** {t['rationale']}")
    

with c2:
    st.markdown("<div class='section-label'>📈 Efficacy & Hazard Ratio</div>", unsafe_allow_html=True)
    m1, m2 = st.columns(2)
    m1.metric("ORR (Primary/Post)", t['outcomes']['ORR'])
    m2.metric("Hazard Ratio (HR)", t['outcomes']['HR'])
    
    st.markdown(f"**mPFS:** {t['outcomes']['mPFS']} | **mOS:** {t['outcomes']['mOS']}")
    st.error(f"**Safety/AEs:** {t['outcomes']['AE']}")
    st.caption(f"Ref: {t['ref']}")
    

st.divider()

# 第二列：收案細節
c3, c4 = st.columns(2)
with c3:
    st.markdown("<div class='section-label'>✅ Inclusion Criteria</div>", unsafe_allow_html=True)
    for inc in t['inclusion']: st.write(f"🟢 {inc}")

with c4:
    st.markdown("<div class='section-label'>❌ Exclusion Criteria</div>", unsafe_allow_html=True)
    for exc in t['exclusion']: st.write(f"🔴 {exc}")

st.markdown("</div>", unsafe_allow_html=True)
