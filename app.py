import streamlit as st
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events
import google.generativeai as genai

# --- 🏥 專業臨床導航視覺配置 ---
st.set_page_config(page_title="婦癌臨床試驗決策支援系統", layout="wide")

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
        text-align: center; padding: 30px; background: #FFFFFF;
        border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 20px;
    }
    .info-section {
        background: #FFFFFF; border-radius: 15px; padding: 30px;
        border: 1px solid #E0F2F1; box-shadow: 0 6px 18px rgba(0,0,0,0.06); margin-bottom: 25px;
    }
    .section-label { font-size: 26px; font-weight: 700; color: #00695C; margin-bottom: 20px; border-bottom: 2px solid #B2DFDB; padding-bottom: 10px; }
    .metric-card { background: #F0F4F8; padding: 15px; border-radius: 10px; text-align: center; }
    .pharma-tag { background: #004D40; color: white; padding: 4px 12px; border-radius: 20px; font-size: 14px; float: right; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 深度臨床數據庫 ---
if 'trials_db' not in st.session_state:
    st.session_state.trials_db = [
        {
            "cancer": "Endometrial", "name": "GU-US-682-6769 (SG vs. TPC)", "pharma": "Gilead Sciences",
            "drug": "Sacituzumab Govitecan (Trodelvy)", "pos": "Recurrence",
            "protocol_details": {
                "Arm A (Experimental)": "SG 10 mg/kg IV on Days 1 and 8 of each 21-day cycle.",
                "Arm B (Control)": "Physician's choice: Doxorubicin 60 mg/m² or Paclitaxel 80 mg/m² weekly."
            },
            "outcomes": {"ORR": "28.5%", "mPFS": "5.6m", "mOS": "12.8m", "HR": "0.64 (95% CI: 0.48-0.84)", "AE": "Grade ≥3 Neutropenia (15%), Diarrhea (11%)"},
            "inclusion": [
                "Advanced/Recurrent Endometrial Cancer (any histology except sarcoma).",
                "At least 1 prior Platinum-based chemotherapy line.",
                "Prior Anti-PD-1/L1 therapy required (e.g. Pembrolizumab).",
                "ECOG Performance Status 0-1.",
                "Measurable disease by RECIST 1.1."
            ],
            "exclusion": [
                "Prior TROP-2 directed ADC therapy.",
                "Uterine Sarcoma.",
                "Active/Untreated CNS metastasis.",
                "Chronic Inflammatory Bowel Disease."
            ],
            "ref": "JCO 2024; TROPiCS-03 Study"
        },
        {
            "cancer": "Endometrial", "name": "MK2870-033 (TroFuse-033)", "pharma": "Merck (MSD) / Kelun-Biotech",
            "drug": "Sac-TMT + Pembrolizumab", "pos": "Maintenance",
            "protocol_details": {
                "Induction": "Carbo (AUC 5) + Taxel (175 mg/m²) + Pembro (200 mg) Q3W for 6 cycles.",
                "Maintenance": "Pembro (400 mg) Q6W +/- Sac-TMT (SKB264) 5 mg/kg Q6W."
            },
            "outcomes": {"ORR": "Estimated > 35%", "mPFS": "TBD", "mOS": "TBD", "HR": "Pending Phase 3 Data", "AE": "Stomatitis, Anemia"},
            "inclusion": [
                "Mismatch Repair Proficient (pMMR) EC.",
                "Newly diagnosed FIGO Stage III/IV or first recurrence.",
                "No prior systemic therapy for advanced disease.",
                "Must provide tumor tissue for central lab (UK) verification."
            ],
            "exclusion": ["Uterine Sarcoma.", "Prior PD-1/L1 inhibitors.", "Active autoimmune disease."],
            "ref": "ESMO 2025 Abstract"
        },
        {
            "cancer": "Ovarian", "name": "DOVE (APGOT-OV07)", "pharma": "GSK",
            "drug": "Dostarlimab + Bevacizumab", "pos": "Recurrence",
            "protocol_details": {
                "Arm A": "Dostarlimab 500 mg Q3W x4, then 1000 mg Q6W.",
                "Arm B": "Dostarlimab + Bevacizumab 15 mg/kg Q3W.",
                "Arm C": "Standard Non-platinum chemotherapy (Gem/Doxo/Taxel)."
            },
            "outcomes": {"ORR": "40.2%", "mPFS": "8.2m", "mOS": "N/A", "HR": "0.58 vs. Chemo (Phase 2)", "AE": "Hypertension, Fatigue"},
            "inclusion": [
                "Clear Cell Carcinoma (OCCC) > 50% histology.",
                "Platinum-resistant (PD < 12 months from last platinum).",
                "Prior Bevacizumab is allowed but not mandatory.",
                "Up to 5 prior lines of therapy."
            ],
            "exclusion": ["Prior Immunotherapy (Anti-PD-1/L1).", "Clinical bowel obstruction.", "Grade 3-4 GI bleed."],
            "ref": "NCT06023862; ESMO-IO"
        },
        {
            "cancer": "Ovarian", "name": "DS8201-772 (DESTINY-PanTumor)", "pharma": "AstraZeneca / Daiichi Sankyo",
            "drug": "Trastuzumab Deruxtecan (Enhertu)", "pos": "Maintenance",
            "protocol_details": {
                "Maintenance Arm": "T-DXd 5.4 mg/kg IV Q3W until progression.",
                "Combination Arm": "T-DXd 5.4 mg/kg + Bevacizumab 15 mg/kg Q3W."
            },
            "outcomes": {"ORR": "46.3% (HER2 IHC 3+)", "mPFS": "10.4m", "mOS": "N/A", "HR": "0.42 (HER2 3+ cohort)", "AE": "ILD/Pneumonitis (6%), Nausea"},
            "inclusion": [
                "HER2-expressing (IHC 3+, 2+, or 1+) Gynecologic tumors.",
                "BRCA Wild-type or HRD result indicates PARP-inhibitor ineligibility.",
                "No disease progression after 6-8 cycles of Platinum + Beva."
            ],
            "exclusion": ["History of Interstitial Lung Disease (ILD).", "LVEF < 50%.", "Prior HER2-targeted ADC."],
            "ref": "JCO 2023; DESTINY-PanTumor 02"
        }
    ]

# --- 2. 狀態管理 ---
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = st.session_state.trials_db[0]['name']

# --- 3. 主頁面：河流圖導航 ---
st.markdown("<div class='main-title'>婦癌臨床試驗導航系統 (Expert Edition)</div>", unsafe_allow_html=True)

cancer_type = st.radio("第一步：選擇癌別", ["Endometrial", "Ovarian"], horizontal=True)

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

# 河流圖與互動區
st.subheader("第二步：點選河流圖 Trial 方塊 或 使用選單")
col_chart, col_quick = st.columns([2.5, 1])

with col_chart:
    fig, current_labels = draw_locked_river(cancer_type)
    clicked_data = plotly_events(fig, click_event=True, key=f"sankey_{cancer_type}")
    if clicked_data:
        clicked_idx = clicked_data[0]['pointNumber']
        label_text = current_labels[clicked_idx].split("\n")[0]
        if label_text in [t["name"] for t in st.session_state.trials_db]:
            st.session_state.selected_trial = label_text

with col_quick:
    t_quick = next(it for it in st.session_state.trials_db if it["name"] == st.session_state.selected_trial)
    st.markdown(f"""
        <div style='background: #E0F2F1; border-left: 8px solid #00897B; padding: 20px; border-radius: 10px;'>
            <h4 style='margin:0; color:#004D40;'>📍 當前選擇</h4>
            <p style='font-weight:700; margin-top:10px; font-size:20px;'>{t_quick['name']}</p>
            <p style='font-size:16px;'>{t_quick['summary']}</p>
            <span style='background:#004D40; color:white; padding:3px 8px; border-radius:5px; font-size:12px;'>{t_quick['pharma']}</span>
        </div>
    """, unsafe_allow_html=True)

# --- 4. 深度數據全覽看板 ---
st.divider()
st.subheader("🔍 第三步：深度臨床數據、Protocol 與收案全覽")

trial_options = [t["name"] for t in st.session_state.trials_db if t["cancer"] == cancer_type]
try:
    current_idx = trial_options.index(st.session_state.selected_trial)
except ValueError:
    current_idx = 0

selected_name = st.selectbox("🎯 快速搜尋試驗：", trial_options, index=current_idx)
t = next(it for it in st.session_state.trials_db if it["name"] == selected_name)

# --- 資訊全覽區 ---
st.markdown(f"<div class='info-section'>", unsafe_allow_html=True)
st.markdown(f"<span class='pharma-tag'>{t['pharma']}</span>", unsafe_allow_html=True)
st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #00897B; padding-bottom:10px;'>📋 {t['name']} 專家級分析報告</h2>", unsafe_allow_html=True)

# 第一列：Protocol 與 Efficacy Data
c1, c2 = st.columns([1.2, 1])

with c1:
    st.markdown("<div class='section-label'>💉 Dosing Protocol & Mechanism</div>", unsafe_allow_html=True)
    st.info(f"**藥物主成分:** {t['drug']}")
    for arm, detail in t['protocol_details'].items():
        st.write(f"🔹 **{arm}**: {detail}")
    st.success(f"**Rationale:** {t['rationale']}")

with c2:
    st.markdown("<div class='section-label'>📈 Efficacy & Hazard Ratio</div>", unsafe_allow_html=True)
    m1, m2 = st.columns(2)
    m1.metric("ORR (Primary/Post)", t['outcomes']['ORR'])
    m2.metric("Hazard Ratio (HR)", t['outcomes']['HR'], delta_color="inverse")
    
    st.write(f"**Median PFS:** {t['outcomes']['mPFS']} | **Median OS:** {t['outcomes']['mOS']}")
    st.error(f"**Safety (AEs):** {t['outcomes']['AE']}")
    st.caption(f"Ref: {t['ref']}")

st.divider()

# 第二列：精細 Inclusion/Exclusion
c3, c4 = st.columns(2)

with c3:
    st.markdown("<div class='section-label'>✅ Inclusion Criteria (Detailed)</div>", unsafe_allow_html=True)
    for inc in t['inclusion']:
        st.write(f"🟢 {inc}")

with c4:
    st.markdown("<div class='section-label'>❌ Exclusion Criteria (Detailed)</div>", unsafe_allow_html=True)
    for exc in t['exclusion']:
        st.write(f"🔴 {exc}")

st.markdown("</div>", unsafe_allow_html=True)
