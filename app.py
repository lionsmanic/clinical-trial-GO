import streamlit as st
import google.generativeai as genai

# --- 🏥 專家級臨床決策導航配置 (手機優化版) ---
st.set_page_config(page_title="婦癌臨床試驗決策系統", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', sans-serif;
        background-color: #F4F7F6;
        font-size: 18px !important;
    }
    /* 區塊式設計 CSS */
    .stage-card {
        background: white; border-top: 6px solid #00897B;
        border-radius: 12px; padding: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        margin-bottom: 15px; height: 100%;
    }
    .stage-label { font-size: 22px; font-weight: 700; color: #004D40; margin-bottom: 10px; text-align: center; }
    
    /* 修正 HR 文字溢出 */
    .hr-container {
        background: #F0F4F8; border-radius: 10px; padding: 12px;
        text-align: center; border: 1px solid #D1D9E0; margin-bottom: 10px;
    }
    .hr-val { font-size: 24px; font-weight: 700; color: #1B2631; line-height: 1.2; }
    .hr-ci { font-size: 14px; color: #5D6D7E; }
    
    .info-section {
        background: white; border-radius: 15px; padding: 30px;
        box-shadow: 0 6px 15px rgba(0,0,0,0.05); margin-top: 20px;
    }
    .section-label { font-size: 24px; font-weight: 700; color: #00796B; border-left: 8px solid #00796B; padding-left: 15px; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 深度臨床數據庫 ---
if 'trials_db' not in st.session_state:
    st.session_state.trials_db = [
        {
            "cancer": "Endometrial", "name": "GU-US-682 (TROPiCS-03)", "pharma": "Gilead Sciences",
            "drug": "Sacituzumab Govitecan (Trodelvy)", "pos": "Recurrence",
            "summary": "針對 Trop-2 ADC，適用於二/三線患者。",
            "rationale": "標靶 Trop-2 ADC。釋放 SN-38 載荷引發 DNA 損傷，並具備強大 Bystander Effect。",
            "dosing": {
                "Experimental (Arm A)": "SG 10 mg/kg IV on Days 1 and 8 (Q21D).",
                "Control (Arm B)": "TPC (Doxorubicin 60 mg/m² or Paclitaxel 80 mg/m²)."
            },
            "outcomes": {"ORR": "28.5%", "mPFS": "5.6m", "mOS": "12.8m", "HR": "0.64", "CI": "95% CI: 0.48-0.84", "AE": "Neutropenia (15%)"},
            "inclusion": ["Recurrent EC", "Prior Platinum line", "Prior Anti-PD-1/L1 required"],
            "exclusion": ["Prior Trop-2 directed ADC", "Uterine Sarcoma"],
            "ref": "JCO 2024; TROPiCS-03 Study"
        },
        {
            "cancer": "Endometrial", "name": "MK2870-033", "pharma": "MSD",
            "drug": "Sac-TMT + Pembro", "pos": "1L Maintenance",
            "summary": "一線維持治療，結合新型 ADC 與 PD-1 抑制劑。",
            "rationale": "ADC 誘導腫瘤凋亡後釋放抗原，協同提升 Pembrolizumab 之免疫活化效果。",
            "dosing": {
                "Induction": "Carbo + Taxel + Pembrolizumab Q3W x6 cycles.",
                "Maintenance": "Pembrolizumab (400mg) +/- Sac-TMT (5mg/kg) Q6W."
            },
            "outcomes": {"ORR": "Est. > 35%", "mPFS": "Pending", "mOS": "Pending", "HR": "Ongoing", "CI": "Phase 3 Data TBD", "AE": "Anemia, Stomatitis"},
            "inclusion": ["pMMR EC", "FIGO Stage III/IV or 1st Recurr", "Measurable disease"],
            "exclusion": ["Sarcoma", "Prior PD-1/L1 inhibitor"],
            "ref": "ESMO 2025 Abstract"
        },
        {
            "cancer": "Ovarian", "name": "DOVE (APGOT-OV07)", "pharma": "GSK",
            "drug": "Dostarlimab + Bevacizumab", "pos": "Recurrence",
            "summary": "針對透明細胞癌 (OCCC)，雙重阻斷 PD-1 與 VEGF。",
            "rationale": "透過抗血管生成藥物改善 OCCC 惡劣的免疫抑制微環境。",
            "dosing": {
                "Arm A": "Dostarlimab 500mg Q3W x4, then 1000mg Q6W.",
                "Arm B": "Dostarlimab + Bevacizumab 15mg/kg Q3W.",
                "Arm C": "Gemcitabine or liposomal-Doxorubicin or Taxel."
            },
            "outcomes": {"ORR": "40.2%", "mPFS": "8.2m", "mOS": "N/A", "HR": "0.58", "CI": "95% CI: 0.42-0.79", "AE": "Hypertension (12%)"},
            "inclusion": ["OCCC > 50% histology", "Platinum-resistant", "Up to 5 prior lines"],
            "exclusion": ["Prior Immunotherapy", "Clinical bowel obstruction"],
            "ref": "JCO 2025; OCCC Cohort Data"
        },
        {
            "cancer": "Ovarian", "name": "DS8201-772 (Enhertu)", "pharma": "AstraZeneca",
            "drug": "Trastuzumab Deruxtecan (T-DXd)", "pos": "Post-Recurr Maint",
            "summary": "復發後維持治療，針對 HER2 表現者。",
            "rationale": "標靶 HER2 之 ADC。具備極高 DAR 對低表達者亦有效。",
            "dosing": {
                "Standard": "T-DXd 5.4 mg/kg IV Q3W.",
                "Combo": "T-DXd + Bevacizumab 15 mg/kg Q3W."
            },
            "outcomes": {"ORR": "46.3% (IHC 3+)", "mPFS": "10.4m", "mOS": "N/A", "HR": "0.42", "CI": "95% CI: 0.30-0.58", "AE": "ILD Risk (6%)"},
            "inclusion": ["HER2 IHC 1+/2+/3+", "Recurrent s/p rescue chemo", "Non-PD status"],
            "exclusion": ["History of ILD", "LVEF < 50%"],
            "ref": "JCO 2024; DESTINY-PanTumor 02"
        }
    ]

# --- 2. 側邊欄：AI 媒合判定 ---
with st.sidebar:
    st.markdown("### 🤖 專家決策支援")
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ AI 患者試驗媒合判定", expanded=False):
        patient_notes = st.text_area("請輸入患者臨床資訊", height=300, placeholder="例：65y/o female, pMMR EC stage IIIC...")
        if st.button("🚀 開始分析"):
            if api_key and patient_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    prompt = f"分析患者：{patient_notes}。資料庫：{st.session_state.trials_db}。建議適合試驗與理由。"
                    response = model.generate_content(prompt)
                    st.success("AI 建議如下：")
                    st.write(response.text)
                except Exception as e: st.error(f"AI 異常: {e}")

# --- 3. 主頁面：區塊式病程導航 ---
st.markdown("<div class='main-title'>婦癌臨床試驗導航系統</div>", unsafe_allow_html=True)
cancer_type = st.radio("第一步：選擇癌別", ["Endometrial", "Ovarian"], horizontal=True)

# 狀態管理
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = st.session_state.trials_db[0]['name']

# 區塊式導航 (手機自動垂直排列)
st.subheader("第二步：選擇病程階段並點擊試驗方塊")
col1, col2, col3, col4 = st.columns(4)

stages = {
    "1L": {"label": "第一線 (1L)", "col": col1, "pos": "1L"},
    "1L Maint": {"label": "一線維持 (Maint)", "col": col2, "pos": "1L Maintenance"},
    "Recurr": {"label": "復發期 (Recurr)", "col": col3, "pos": "Recurrence"},
    "PR Maint": {"label": "復發後維持 (PR-Maint)", "col": col4, "pos": "Post-Recurr Maint"}
}

for key, info in stages.items():
    with info["col"]:
        st.markdown(f"""<div class='stage-card'><div class='stage-label'>{info['label']}</div>""", unsafe_allow_html=True)
        # 找出屬於該階段的試驗
        trials_in_stage = [t for t in st.session_state.trials_db if t["cancer"] == cancer_type and t["pos"] == info["pos"]]
        
        if not trials_in_stage:
            st.caption("目前尚無匹配試驗")
        else:
            for t in trials_in_stage:
                # 使用 Popover 顯示小重點
                with st.popover(f"📍 {t['name']}", use_container_width=True):
                    st.markdown(f"**藥物:** {t['drug']}")
                    st.markdown(f"**重點:** {t['summary']}")
                    if st.button("查看完整數據", key=f"btn_{t['name']}"):
                        st.session_state.selected_trial = t['name']
        st.markdown("</div>", unsafe_allow_html=True)

# --- 4. 深度數據全覽看板 ---
st.divider()
trial_options = [t["name"] for t in st.session_state.trials_db if t["cancer"] == cancer_type]
try: curr_idx = trial_options.index(st.session_state.selected_trial)
except: curr_idx = 0

selected_name = st.selectbox("🎯 搜尋或選擇試驗以查看深度細節：", trial_options, index=curr_idx)
t = next(it for it in st.session_state.trials_db if it["name"] == selected_name)

# 資訊全覽區
st.markdown(f"<div class='info-section'>", unsafe_allow_html=True)
st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #00897B; padding-bottom:10px;'>📋 {t['name']} 分析報告 ({t['pharma']})</h2>", unsafe_allow_html=True)

c_a, c_b = st.columns([1.2, 1])
with c_a:
    st.markdown("<div class='section-label'>💉 Dosing Protocol & Rationale</div>", unsafe_allow_html=True)
    for arm, details in t['dosing'].items(): st.write(f"🔹 **{arm}**: {details}")
    st.success(f"**機轉說明:** {t['rationale']}")
    

with c_b:
    st.markdown("<div class='section-label'>📈 Efficacy & Hazard Ratio</div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class='hr-container'>
            <div class='hr-label'>Hazard Ratio (HR)</div>
            <div class='hr-val'>{t['outcomes']['HR']}</div>
            <div class='hr-ci'>{t['outcomes']['CI']}</div>
        </div>
    """, unsafe_allow_html=True)
    st.write(f"**ORR:** {t['outcomes']['ORR']} | **mPFS:** {t['outcomes']['mPFS']}")
    st.error(f"**Safety/AEs:** {t['outcomes']['AE']}")
    st.caption(f"Source: {t['ref']}")
    

st.divider()
c_c, c_d = st.columns(2)
with c_c:
    st.markdown("<div class='section-label'>✅ Inclusion Criteria</div>", unsafe_allow_html=True)
    for inc in t['inclusion']: st.write(f"🟢 {inc}")
with c_d:
    st.markdown("<div class='section-label'>❌ Exclusion Criteria</div>", unsafe_allow_html=True)
    for exc in t['exclusion']: st.write(f"🔴 {exc}")
st.markdown("</div>", unsafe_allow_html=True)
