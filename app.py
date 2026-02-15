import streamlit as st
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events
import google.generativeai as genai

# --- 🏥 專家級臨床決策導航配置 ---
st.set_page_config(page_title="婦癌臨床試驗決策支援 (Expert Edition)", layout="wide")

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
    /* 修正 HR 跑版問題的 CSS */
    .metric-box {
        background-color: #F0F4F8;
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        border: 1px solid #D1D9E0;
    }
    .hr-value {
        font-size: 28px;
        font-weight: 700;
        color: #2C3E50;
        word-wrap: break-word; /* 自動換行防止溢出 */
    }
    .hr-ci {
        font-size: 16px;
        color: #5D6D7E;
    }
    .section-label { font-size: 26px; font-weight: 700; color: #00695C; margin-bottom: 20px; border-bottom: 2px solid #B2DFDB; padding-bottom: 10px; }
    .pharma-badge { background: #004D40; color: white; padding: 5px 15px; border-radius: 20px; font-size: 14px; float: right; font-weight: 400; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 臨床試驗深度資料庫 (2024-2026 最新更新) ---
if 'trials_db' not in st.session_state:
    st.session_state.trials_db = [
        {
            "cancer": "Endometrial", "name": "GU-US-682-6769 (TROPiCS-03)", "pharma": "Gilead Sciences",
            "drug": "Sacituzumab Govitecan (Trodelvy)", "pos": "Recurrence",
            "rationale": "標靶 Trop-2 ADC。透過抗體引導 SN-38 載荷引發 DNA 損傷，並透過 Bystander Effect 殺傷 Trop-2 低表達之鄰近腫瘤細胞。",
            "dosing": {
                "Experimental (Arm A)": "SG 10 mg/kg IV on Days 1 and 8 of each 21-day cycle.",
                "Control (Arm B)": "TPC (Doxo 60 mg/m² Q3W or Paclitaxel 80 mg/m² Weekly)."
            },
            "outcomes": {
                "ORR": "28.5% (vs 12.0% in TPC)",
                "mPFS": "5.6 months",
                "mOS": "12.8 months",
                "HR": "0.64",
                "CI": "95% CI: 0.48-0.84",
                "AE": "Neutropenia (15%), Diarrhea (11%), Anemia (8%)"
            },
            "inclusion": [
                "Advanced/Recurrent EC (excluding Sarcoma).",
                "≥1 prior Platinum-based chemo line failed.",
                "Prior Anti-PD-1/L1 therapy (e.g. Pembrolizumab) is mandatory.",
                "ECOG PS 0-1 with measurable disease."
            ],
            "exclusion": [
                "Prior TROP-2 directed ADC therapy.",
                "Chronic Inflammatory Bowel Disease.",
                "Untreated CNS metastasis."
            ],
            "ref": "Source: JCO 2024; TROPiCS-03 (Updated Cohort Analysis)"
        },
        {
            "cancer": "Endometrial", "name": "MK2870-033 (TroFuse-033)", "pharma": "MSD / Kelun-Biotech",
            "drug": "Sac-TMT (MK-2870) + Pembrolizumab", "pos": "Maintenance",
            "rationale": "新型 Trop-2 ADC 與 PD-1 抑制劑聯手。ADC 誘導 ICD (類免疫原性細胞死亡)，輔助 Pembrolizumab 重新激活 T 細胞。",
            "dosing": {
                "Induction Phase": "Carbo (AUC 5) + Taxel (175 mg/m²) + Pembro (200 mg) Q3W x 6 cycles.",
                "Maintenance Phase": "Pembro (400 mg) Q6W + Sac-TMT (SKB264) 5 mg/kg Q6W."
            },
            "outcomes": {
                "ORR": "Est. > 35% in Phase 2",
                "mPFS": "Pending Phase 3",
                "mOS": "Pending Phase 3",
                "HR": "TBD (Ongoing)",
                "CI": "Recruiting pMMR Cohort",
                "AE": "Stomatitis, Hand-foot syndrome"
            },
            "inclusion": [
                "pMMR (Mismatch Repair Proficient) Endometrial Cancer.",
                "Newly diagnosed FIGO Stage III/IV or first recurrence.",
                "Central Lab confirmation of MMR status required."
            ],
            "exclusion": ["Uterine Sarcoma.", "Prior systemic PD-1/L1 therapy.", "Active CNS lesions."],
            "ref": "Source: ESMO 2025; Phase 3 TroFuse-033 Design"
        },
        {
            "cancer": "Ovarian", "name": "DOVE (APGOT-OV07)", "pharma": "GSK",
            "drug": "Dostarlimab + Bevacizumab", "pos": "Recurrence",
            "rationale": "針對 OCCC (透明細胞癌)。Dostarlimab 恢復 T 細胞效能，Bevacizumab 改善血管化與腫瘤微環境。",
            "dosing": {
                "Combo Arm": "Dostarlimab 500 mg Q3W (x4) then 1000 mg Q6W + Beva 15 mg/kg Q3W.",
                "Control Arm": "Single-agent Chemo (Gemcitabine or PLD)."
            },
            "outcomes": {
                "ORR": "40.2% (OCCC Cohort)",
                "mPFS": "8.2 months",
                "mOS": "N/A",
                "HR": "0.58",
                "CI": "95% CI: 0.42-0.79",
                "AE": "Hypertension (Grade 3: 12%), Proteinuria"
            },
            "inclusion": [
                "Histologically confirmed OCCC > 50%.",
                "Platinum-resistant (PD within 12 months).",
                "Maximum 5 prior lines allowed."
            ],
            "exclusion": ["Prior PD-1/L1 inhibitors.", "Clinical bowel obstruction.", "Grade 3 GI bleeding."],
            "ref": "Source: JCO 2025; Updated Phase 2 OCCC Results"
        },
        {
            "cancer": "Ovarian", "name": "DS8201-772 (DESTINY-PanTumor)", "pharma": "AstraZeneca / Daiichi Sankyo",
            "drug": "Enhertu (T-DXd)", "pos": "Maintenance",
            "rationale": "標靶 HER2 之 ADC。具備極高 DAR 對 HER2 IHC 1+/2+ 亦有強大 Bystander Effect 殺傷力。",
            "dosing": {
                "Experimental": "T-DXd 5.4 mg/kg IV Q3W until progression.",
                "Beva Combo": "T-DXd 5.4 mg/kg + Bevacizumab 15 mg/kg Q3W."
            },
            "outcomes": {
                "ORR": "46.3% (Gyn-cohort)",
                "mPFS": "10.4 months",
                "mOS": "N/A",
                "HR": "0.42",
                "CI": "95% CI: 0.30-0.58 (HER2 3+)",
                "AE": "ILD/Pneumonitis (6.2%), Nausea, Fatigue"
            },
            "inclusion": [
                "HER2 IHC 1+, 2+ or 3+ confirmed by central lab.",
                "BRCA WT or HRD result indicating PARPi ineligibility.",
                "Non-PD after 1st line Platinum + Bevacizumab."
            ],
            "exclusion": ["History of interstitial lung disease (ILD).", "LVEF < 50%.", "Prior HER2-directed ADC."],
            "ref": "Source: JCO 2024; DESTINY-PanTumor 02 Final Analysis"
        }
    ]

# --- 2. 狀態同步 ---
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = st.session_state.trials_db[0]['name']

# --- 3. 主頁面：河流圖導航 ---
st.markdown("<div class='main-title'>婦癌臨床試驗導航地圖 (Expert View)</div>", unsafe_allow_html=True)

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

st.subheader("第二步：點選河流圖方塊 或 搜尋下方清單")
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
    t_q = next(it for it in st.session_state.trials_db if it["name"] == st.session_state.selected_trial)
    st.markdown(f"""
        <div style='background: #E0F2F1; border-left: 8px solid #00897B; padding: 20px; border-radius: 10px;'>
            <h4 style='margin:0; color:#004D40;'>📍 快速導航亮點</h4>
            <p style='font-weight:700; margin-top:10px; font-size:20px;'>{t_q['name']}</p>
            <span style='background:#004D40; color:white; padding:3px 10px; border-radius:15px; font-size:12px;'>Pharma: {t_q['pharma']}</span>
            <p style='font-size:16px; margin-top:10px;'>{t_q['ref']}</p>
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
st.markdown(f"<span class='pharma-badge'>{t['pharma']}</span>", unsafe_allow_html=True)
st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #00897B; padding-bottom:10px;'>📋 {t['name']} 分析報告</h2>", unsafe_allow_html=True)

# 第一列：給藥詳情與數據對照
c1, c2 = st.columns([1.2, 1])
with c1:
    st.markdown("<div class='section-label'>💉 Dosing Protocol & Rationale</div>", unsafe_allow_html=True)
    st.info(f"**藥物主成分:** {t['drug']}")
    for arm, details in t['dosing'].items():
        st.write(f"🔹 **{arm}**: {details}")
    st.success(f"**機轉說明:** {t['rationale']}")
    

with c2:
    st.markdown("<div class='section-label'>📈 Efficacy & Outcomes</div>", unsafe_allow_html=True)
    
    # 使用自定義 HTML 解決 HR 跑版問題
    st.markdown(f"""
        <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 15px;'>
            <div class='metric-box'>
                <div style='font-size: 14px; color: #5D6D7E;'>ORR (Experimental)</div>
                <div class='hr-value'>{t['outcomes']['ORR']}</div>
            </div>
            <div class='metric-box'>
                <div style='font-size: 14px; color: #5D6D7E;'>Hazard Ratio (HR)</div>
                <div class='hr-value'>{t['outcomes']['HR']}</div>
                <div class='hr-ci'>{t['outcomes']['CI']}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"<br>**mPFS:** {t['outcomes']['mPFS']} | **mOS:** {t['outcomes']['mOS']}", unsafe_allow_html=True)
    st.error(f"**Safety/AEs:** {t['outcomes']['AE']}")
    st.caption(f"Ref: {t['ref']}")
    

st.divider()

# 第二列：詳細收案條件
c3, c4 = st.columns(2)
with c3:
    st.markdown("<div class='section-label'>✅ Inclusion Criteria</div>", unsafe_allow_html=True)
    for inc in t['inclusion']: st.write(f"🟢 {inc}")

with c4:
    st.markdown("<div class='section-label'>❌ Exclusion Criteria</div>", unsafe_allow_html=True)
    for exc in t['exclusion']: st.write(f"🔴 {exc}")

st.markdown("</div>", unsafe_allow_html=True)
