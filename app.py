import streamlit as st
import google.generativeai as genai

# --- 🏥 專家級臨床決策導航配置 (區塊+彈窗優化版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', sans-serif;
        background-color: #F8FAF9;
        font-size: 18px !important;
    }
    /* 區塊式設計 CSS */
    .stage-card {
        background: white; border-top: 5px solid #00897B;
        border-radius: 12px; padding: 15px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        margin-bottom: 20px; min-height: 200px;
    }
    .stage-label { font-size: 21px; font-weight: 700; color: #004D40; margin-bottom: 12px; text-align: center; background: #E0F2F1; border-radius: 8px; padding: 5px; }
    
    /* 修正 HR 顯示 */
    .hr-container {
        background: #F0F4F8; border-radius: 10px; padding: 15px;
        text-align: center; border: 1px solid #D1D9E0; margin-top: 10px;
    }
    .hr-val { font-size: 26px; font-weight: 700; color: #1B2631; line-height: 1.1; }
    .hr-ci { font-size: 15px; color: #5D6D7E; margin-top: 4px; }
    
    .info-section {
        background: white; border-radius: 15px; padding: 30px;
        box-shadow: 0 6px 15px rgba(0,0,0,0.06); margin-top: 25px; border: 1px solid #B2DFDB;
    }
    .section-label { font-size: 24px; font-weight: 700; color: #00796B; border-left: 10px solid #00796B; padding-left: 15px; margin-bottom: 20px; }
    .pharma-badge { background: #004D40; color: white; padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 400; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 深度臨床資料庫 (2024-2026 最新版) ---
if 'trials_db' not in st.session_state:
    st.session_state.trials_db = [
        {
            "cancer": "Endometrial", "name": "GU-US-682-6769", "pharma": "Gilead Sciences",
            "drug": "SG (Trodelvy)", "pos": "Recurrence",
            "summary": "針對 Trop-2 ADC。顯著改善二/三線 EC 患者生存期。Bystander Effect 強。",
            "rationale": "標靶 Trop-2 ADC。釋放 SN-38 載荷引發 DNA 損傷，特別適合先前 Platinum + PD-1 失敗者。",
            "dosing": {
                "Experimental (Arm A)": "SG 10 mg/kg IV (D1, D8 Q21D).",
                "Control (Arm B)": "TPC (Doxo 60 mg/m² or Paclitaxel 80 mg/m²)."
            },
            "outcomes": {"ORR": "28.5%", "mPFS": "5.6m", "mOS": "12.8m", "HR": "0.64", "CI": "95% CI: 0.48-0.84", "AE": "Neutropenia, Diarrhea"},
            "inclusion": ["Recurrent EC (excluding Sarcoma)", "≥1 prior Platinum chemo line", "Prior Anti-PD-1/L1 required"],
            "exclusion": ["Prior Trop-2 directed ADC", "Active CNS metastasis"],
            "ref": "JCO 2024; TROPiCS-03 Study"
        },
        {
            "cancer": "Endometrial", "name": "MK2870-033", "pharma": "MSD / Kelun-Biotech",
            "drug": "Sac-TMT + Pembro", "pos": "1L Maintenance",
            "summary": "新型 Trop-2 ADC 聯手 PD-1 抑制劑，挑戰一線維持治療新標準。",
            "rationale": "ADC 誘導腫瘤凋亡後釋放新抗原，增強 Pembrolizumab 的 T 細胞活化與應答。",
            "dosing": {
                "Induction": "Carbo (AUC 5) + Taxel (175 mg/m²) + Pembro (200 mg) Q3W x6.",
                "Maintenance": "Pembrolizumab (400 mg) Q6W +/- Sac-TMT (5 mg/kg) Q6W."
            },
            "outcomes": {"ORR": "Est. > 35%", "mPFS": "Pending", "mOS": "Pending", "HR": "Ongoing", "CI": "Phase 3 In Progress", "AE": "Anemia, Stomatitis"},
            "inclusion": ["pMMR Endometrial Cancer", "FIGO Stage III/IV or first recurrence", "Central Lab MMR confirmation"],
            "exclusion": ["Uterine Sarcoma", "Prior systemic PD-1 therapy"],
            "ref": "ESMO 2025; TroFuse-033 Design"
        },
        {
            "cancer": "Ovarian", "name": "DOVE (APGOT-OV07)", "pharma": "GSK",
            "drug": "Dostarlimab + Beva", "pos": "Recurrence",
            "summary": "針對 OCCC (透明細胞癌)，利用 PD-1 與 VEGF 雙重阻斷改善微環境。",
            "rationale": "針對 OCCC 特有的免疫抑制環境，Bevacizumab 改善血管化以利免疫細胞浸潤。",
            "dosing": {
                "Arm A": "Dostarlimab 500mg Q3W x4 -> 1000mg Q6W.",
                "Arm B": "Dostarlimab + Bevacizumab 15mg/kg Q3W.",
                "Arm C": "Standard Chemo (Gem/PLD/Taxel)."
            },
            "outcomes": {"ORR": "40.2% (OCCC)", "mPFS": "8.2m", "mOS": "N/A", "HR": "0.58", "CI": "95% CI: 0.42-0.79", "AE": "Hypertension, Fatigue"},
            "inclusion": ["OCCC > 50% histology", "Platinum-resistant (PD < 12m)", "Prior Beva allowed"],
            "exclusion": ["Prior Immunotherapy", "Bowel obstruction history"],
            "ref": "JCO 2025; APGOT-OV07 Final"
        },
        {
            "cancer": "Ovarian", "name": "DS8201-772", "pharma": "AstraZeneca / DS",
            "drug": "Enhertu (T-DXd)", "pos": "Post-Recurr Maint",
            "summary": "復發救援化療後的維持治療。針對 HER2 Low 族群表現強大療效。",
            "rationale": "標靶 HER2 ADC。高 DAR 載荷具備強大 Bystander Effect，對 IHC 1+/2+ 腫瘤亦有效。",
            "dosing": {
                "Experimental": "T-DXd 5.4 mg/kg IV Q3W.",
                "Combination": "T-DXd + Bevacizumab 15 mg/kg Q3W."
            },
            "outcomes": {"ORR": "46.3% (IHC 3+)", "mPFS": "10.4m", "mOS": "N/A", "HR": "0.42", "CI": "95% CI: 0.30-0.58", "AE": "ILD Risk (6.2%)"},
            "inclusion": ["HER2 IHC 1+/2+/3+", "Recurrent disease s/p rescue chemo", "LVEF ≥ 50%"],
            "exclusion": ["History of ILD/Pneumonitis", "Prior HER2-directed ADC"],
            "ref": "JCO 2024; DESTINY-PanTumor 02"
        }
    ]

# --- 2. 側邊欄：AI 媒合判定 ---
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = st.session_state.trials_db[0]['name']

with st.sidebar:
    st.markdown("### 🤖 專家決策支援")
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ AI 患者試驗媒合判定", expanded=False):
        patient_notes = st.text_area("輸入病歷摘要", height=300, placeholder="例：62y/o pMMR EC, s/p Platinum, now PD...")
        if st.button("🚀 開始分析"):
            if api_key and patient_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    prompt = f"分析病歷：{patient_notes}。資料庫：{st.session_state.trials_db}。建議適合試驗與 HR 數據意義。"
                    response = model.generate_content(prompt)
                    st.success("AI 建議報告：")
                    st.write(response.text)
                except Exception as e: st.error(f"AI 異常: {e}")

# --- 3. 主頁面：病程階段區塊導航 ---
st.markdown("<div class='main-title'>婦癌臨床試驗導航系統 (Expert Edition)</div>", unsafe_allow_html=True)
cancer_type = st.radio("第一步：選擇癌症類型", ["Endometrial", "Ovarian"], horizontal=True)



st.subheader("第二步：點擊下方階段標記按鈕查看摘要")
c1, c2, c3, c4 = st.columns(4)

stages = {
    "1L": {"label": "第一線 (1L)", "col": c1, "pos": "1L"},
    "1LM": {"label": "一線維持 (Maint)", "col": c2, "pos": "1L Maintenance"},
    "RC": {"label": "復發期 (Recurr)", "col": c3, "pos": "Recurrence"},
    "PRM": {"label": "復發後維持 (PR-Maint)", "col": c4, "pos": "Post-Recurr Maint"}
}

for key, info in stages.items():
    with info["col"]:
        st.markdown(f"""<div class='stage-card'><div class='stage-label'>{info['label']}</div>""", unsafe_allow_html=True)
        relevant_trials = [t for t in st.session_state.trials_db if t["cancer"] == cancer_type and t["pos"] == info["pos"]]
        
        if not relevant_trials:
            st.caption("目前尚無匹配試驗")
        else:
            for t in relevant_trials:
                # 併列顯示試驗名稱與藥物
                with st.popover(f"📍 {t['name']} | {t['drug']}", use_container_width=True):
                    st.markdown(f"#### ✨ {t['name']} 亮點摘要")
                    st.markdown(f"**藥物配方:** {t['drug']}")
                    st.info(t['summary'])
                    st.markdown("---")
                    if st.button("📊 查看完整實證數據與 Protocol", key=f"go_{t['name']}"):
                        st.session_state.selected_trial = t['name']
        st.markdown("</div>", unsafe_allow_html=True)

# --- 4. 深度數據全覽看板 ---
st.divider()
t_options = [t["name"] for t in st.session_state.trials_db if t["cancer"] == cancer_type]
try: curr_idx = t_options.index(st.session_state.selected_trial)
except: curr_idx = 0

selected_name = st.selectbox("🎯 快速搜尋或切換試驗詳細報告：", t_options, index=curr_idx)
t = next(it for it in st.session_state.trials_db if it["name"] == selected_name)

# 深度報告看板
st.markdown(f"<div class='info-section'>", unsafe_allow_html=True)
st.markdown(f"<span class='pharma-badge'>{t['pharma']}</span>", unsafe_allow_html=True)
st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #00897B; padding-bottom:10px;'>📋 {t['name']} 深度分析報告</h2>", unsafe_allow_html=True)

r1_c1, r1_c2 = st.columns([1.2, 1])
with r1_c1:
    st.markdown("<div class='section-label'>💉 Dosing Protocol & Rationale</div>", unsafe_allow_html=True)
    for arm, details in t['dosing'].items():
        st.write(f"🔹 **{arm}**: {details}")
    st.success(f"**機轉說明 (Rationale):** {t['rationale']}")
    

with r1_c2:
    st.markdown("<div class='section-label'>📈 Efficacy & Outcomes</div>", unsafe_allow_html=True)
    # 解決 HR 溢出問題
    st.markdown(f"""
        <div class='hr-container'>
            <div style='font-size: 14px; color: #5D6D7E; margin-bottom:5px;'>Hazard Ratio (HR)</div>
            <div class='hr-val'>{t['outcomes']['HR']}</div>
            <div class='hr-ci'>{t['outcomes']['CI']}</div>
        </div>
    """, unsafe_allow_html=True)
    st.write(f"**ORR:** {t['outcomes']['ORR']} | **mPFS:** {t['outcomes']['mPFS']}")
    st.error(f"**Safety (Common AEs):** {t['outcomes']['AE']}")
    st.caption(f"Ref: {t['ref']}")
    

st.divider()
r2_c1, r2_c2 = st.columns(2)
with r2_c1:
    st.markdown("<div class='section-label'>✅ Inclusion Criteria (Detailed)</div>", unsafe_allow_html=True)
    for inc in t['inclusion']: st.write(f"🟢 {inc}")
with r2_c2:
    st.markdown("<div class='section-label'>❌ Exclusion Criteria (Detailed)</div>", unsafe_allow_html=True)
    for exc in t['exclusion']: st.write(f"🔴 {exc}")
st.markdown("</div>", unsafe_allow_html=True)
