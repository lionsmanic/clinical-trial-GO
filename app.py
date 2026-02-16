import streamlit as st
import google.generativeai as genai

# --- 🏥 專家級醫學儀表板視覺配置 (高清晰度版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=Roboto:wght@700;900&display=swap');
    
    /* === 全域字體級距上調 === */
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', 'Roboto', sans-serif;
        background-color: #F0F4F8;
        color: #1A1A1A; /* 提高對比度 */
        font-size: 21px !important; /* 全局基準放大 */
        line-height: 1.6;
    }

    /* 主標題：大幅強化 */
    .main-title {
        font-size: 48px !important; font-weight: 900; color: #004D40;
        padding: 25px 0 15px 0; border-bottom: 4px solid #4DB6AC;
        margin-bottom: 25px;
    }

    /* === 病程區塊卡片：比例與字體調整 === */
    .stage-card-base {
        border-radius: 16px; padding: 15px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.08);
        border: 2px solid transparent;
        min-height: 160px; background: white;
        transition: all 0.2s ease;
    }
    
    .stage-header {
        font-size: 26px !important; font-weight: 900; color: white;
        margin: -15px -15px 15px -15px; padding: 12px;
        border-radius: 14px 14px 0 0; text-align: center;
        letter-spacing: 1px;
    }

    /* 各階段配色 */
    .card-1l { border-color: #66BB6A; }
    .header-1l { background: linear-gradient(135deg, #43A047, #2E7D32); }
    .card-1lm { border-color: #29B6F6; }
    .header-1lm { background: linear-gradient(135deg, #0288D1, #01579B); }
    .card-rc { border-color: #FFA726; }
    .header-rc { background: linear-gradient(135deg, #FB8C00, #EF6C00); }
    .card-prm { border-color: #AB47BC; }
    .header-prm { background: linear-gradient(135deg, #8E24AA, #6A1B9A); }

    /* === 深度報告區塊：字體與間距優化 === */
    .detail-section-container {
        background: white; border-radius: 20px; padding: 40px;
        margin-top: 35px; box-shadow: 0 12px 40px rgba(0,0,0,0.1);
        border: 1px solid #CFD8DC;
    }

    .info-box-blue {
        background: #E3F2FD; border-radius: 15px; padding: 25px;
        border-left: 8px solid #1976D2; color: #0D47A1; font-size: 22px;
    }
    .info-box-gold {
        background: #FFF8E1; border-radius: 15px; padding: 25px;
        border-left: 8px solid #FBC02D; color: #5F4B09; font-size: 22px;
    }
    
    /* Hazard Ratio 核心數值：極大化呈現 */
    .hr-display-box {
        background: white; border-radius: 15px; padding: 20px;
        text-align: center; border: 3px solid #FFE082;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
    .hr-label-text { font-size: 18px; color: #795548; font-weight: 700; margin-bottom: 8px; }
    .hr-big-val {
        font-family: 'Roboto', sans-serif; font-size: 48px !important; 
        font-weight: 900; color: #D84315; line-height: 1;
    }
    .hr-ci-small { font-size: 20px !important; color: #5D4037; margin-top: 10px; font-weight: 700; }

    /* 收案條件字體加重 */
    .inc-box { background: #E8F5E9; padding: 20px; border-radius: 12px; border-left: 6px solid #2E7D32; font-size: 21px; }
    .exc-box { background: #FFEBEE; padding: 20px; border-radius: 12px; border-left: 6px solid #C62828; font-size: 21px; }

    /* Pharma Badge */
    .pharma-badge { 
        background: #004D40; color: white; 
        padding: 6px 18px; border-radius: 50px; font-size: 14px; font-weight: 700;
        display: inline-block; margin-bottom: 12px;
    }
    
    /* 加強 Popover 按鈕的字體 */
    .stPopover button {
        font-weight: 700 !important;
        font-size: 18px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 深度臨床資料庫 ---
if 'trials_db' not in st.session_state:
    st.session_state.trials_db = [
        {
            "cancer": "Endometrial", "name": "GU-US-682-6769 (TROPiCS-03)", "pharma": "Gilead",
            "drug": "SG (Trodelvy)", "pos": "Recurrence",
            "summary": "針對 Trop-2 ADC。顯著改善二/三線 EC 患者存活期。具備強力 Bystander Effect。",
            "rationale": "標靶 Trop-2 ADC。釋放 SN-38 載荷引發 DNA 損傷。適合先前 Platinum + PD-1 失敗之進展性患者。",
            "dosing": {
                "Experimental (Arm A)": "SG 10 mg/kg IV (Days 1, 8 of Q21D).",
                "Control (Arm B)": "TPC (Doxorubicin 60 mg/m² Q3W or Paclitaxel 80 mg/m² Weekly)."
            },
            "outcomes": {"ORR": "28.5%", "mPFS": "5.6m", "mOS": "12.8m", "HR": "0.64", "CI": "95% CI: 0.48-0.84", "AE": "Neutropenia, Diarrhea"},
            "inclusion": ["Recurrent EC (excluding Sarcoma)", "≥1 prior Platinum line failed", "Prior Anti-PD-1/L1 therapy mandatory"],
            "exclusion": ["Prior TROP-2 ADC therapy", "Active/Untreated CNS metastasis"],
            "ref": "JCO 2024; TROPiCS-03 Study"
        },
        {
            "cancer": "Endometrial", "name": "MK2870-033 (TroFuse-033)", "pharma": "MSD",
            "drug": "Sac-TMT + Pembro", "pos": "1L Maintenance",
            "summary": "新型 ADC 聯手 PD-1 抑制劑。旨在挑戰一線維持治療現有標準。",
            "rationale": "ADC 誘導腫瘤凋亡後釋放新抗原，增強 Pembrolizumab 的 T 細胞再活化。用於延緩一線化療後復發。",
            "dosing": {
                "Induction": "Carbo (AUC 5) + Taxel (175 mg/m²) + Pembro (200 mg) Q3W x6.",
                "Maintenance": "Pembrolizumab (400 mg) Q6W + Sac-TMT (5 mg/kg) Q6W."
            },
            "outcomes": {"ORR": "Est. > 35%", "mPFS": "Pending Phase 3", "mOS": "Pending", "HR": "TBD", "CI": "Ongoing pMMR Cohort", "AE": "Anemia, Stomatitis"},
            "inclusion": ["pMMR Endometrial Cancer", "FIGO III/IV or first recurrence", "Central Lab MMR confirmation required"],
            "exclusion": ["Uterine Sarcoma", "Prior systemic PD-1 therapy"],
            "ref": "ESMO 2025; ClinicalTrial.gov Update"
        },
        {
            "cancer": "Ovarian", "name": "DOVE (APGOT-OV07)", "pharma": "GSK",
            "drug": "Dostarlimab + Beva", "pos": "Recurrence",
            "summary": "針對 OCCC (透明細胞癌)。利用 PD-1 與 VEGF 雙重阻斷改善腫瘤微環境。",
            "rationale": "抗血管生成藥物改善 OCCC 惡劣之免疫抑制環境，使免疫檢查點抑制劑發揮更佳效能。",
            "dosing": {
                "Arm B (Combo)": "Dostarlimab + Bevacizumab 15mg/kg Q3W.",
                "Arm C (Control)": "Standard Chemo (Gemcitabine / PLD / Taxel)."
            },
            "outcomes": {"ORR": "40.2% (OCCC)", "mPFS": "8.2m", "mOS": "N/A", "HR": "0.58", "CI": "95% CI: 0.42-0.79", "AE": "Hypertension, Fatigue"},
            "inclusion": ["Clear Cell Carcinoma > 50% histology", "Platinum-resistant (PD < 12m)", "Prior Bevacizumab allowed"],
            "exclusion": ["Prior Immunotherapy (PD-1/L1)", "Bowel obstruction history"],
            "ref": "JCO 2025; APGOT-OV07 Data"
        },
        {
            "cancer": "Ovarian", "name": "DS8201-772", "pharma": "AstraZeneca",
            "drug": "Enhertu (T-DXd)", "pos": "Post-Recurr Maint",
            "summary": "復發後救援化療達穩定後之維持治療。針對 HER2 Low 族群表現極佳。",
            "rationale": "標靶 HER2 之 ADC。高 DAR 具備強大旁觀者效應，對於 IHC 1+/2+ 之腫瘤細胞亦有顯著殺傷力。",
            "dosing": {
                "Experimental": "T-DXd 5.4 mg/kg IV Q3W.",
                "Combination": "T-DXd + Bevacizumab 15 mg/kg Q3W."
            },
            "outcomes": {"ORR": "46.3% (IHC 3+)", "mPFS": "10.4m", "mOS": "N/A", "HR": "0.42", "CI": "95% CI: 0.30-0.58", "AE": "ILD Risk (6.2%)"},
            "inclusion": ["HER2 IHC 1+/2+/3+", "Recurrent s/p rescue chemo", "LVEF ≥ 50%"],
            "exclusion": ["History of Interstitial Lung Disease (ILD)", "Prior HER2-directed ADC"],
            "ref": "JCO 2024; DESTINY-PanTumor 02 Final"
        }
    ]

# --- 2. 狀態同步 ---
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = st.session_state.trials_db[0]['name']

# --- 3. 側邊欄：AI 決策助理 ---
with st.sidebar:
    st.markdown("<h2 style='color: #6A1B9A;'>🤖 AI 專家助理</h2>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 患者條件媒合分析", expanded=False):
        patient_notes = st.text_area("輸入病歷摘要", height=300)
        if st.button("🚀 開始深度分析"):
            if api_key and patient_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    prompt = f"分析病歷：{patient_notes}。資料庫：{st.session_state.trials_db}。建議適合試驗與理由。"
                    response = model.generate_content(prompt)
                    st.write(response.text)
                except Exception as e: st.error(f"AI 異常: {e}")

# --- 4. 主頁面：區塊導航 ---
st.markdown("<div class='main-title'>婦癌臨床試驗導航地圖</div>", unsafe_allow_html=True)

# 顯示病程路徑參考圖


cancer_type = st.radio("第一步：選擇癌症類型", ["Endometrial", "Ovarian"], horizontal=True)

st.subheader("第二步：點擊下方標記查看亮點摘要")
c1, c2, c3, c4 = st.columns(4)

stages = {
    "1L": {"label": "第一線 (1L)", "col": c1, "pos": "1L", "css": "1l"},
    "1LM": {"label": "一線維持 (Maint)", "col": c2, "pos": "1L Maintenance", "css": "1lm"},
    "RC": {"label": "復發期 (Recurr)", "col": c3, "pos": "Recurrence", "css": "rc"},
    "PRM": {"label": "復發後維持 (PRM)", "col": c4, "pos": "Post-Recurr Maint", "css": "prm"}
}

for key, info in stages.items():
    with info["col"]:
        st.markdown(f"""<div class='stage-card-base card-{info['css']}'><div class='stage-header header-{info['css']}'>{info['label']}</div>""", unsafe_allow_html=True)
        relevant_trials = [t for t in st.session_state.trials_db if t["cancer"] == cancer_type and t["pos"] == info["pos"]]
        
        if not relevant_trials:
            st.caption("無匹配試驗")
        else:
            for t in relevant_trials:
                label = f"📍 {t['pharma']} | {t['name']} | {t['drug']}"
                with st.popover(label, use_container_width=True):
                    st.markdown(f"### ✨ {t['name']} 核心重點")
                    st.info(t['summary'])
                    if st.button("📊 開啟深度分析報告", key=f"go_{t['name']}"):
                        st.session_state.selected_trial = t['name']
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. 深度分析報告看板 ---
st.divider()
t_options = [t["name"] for t in st.session_state.trials_db if t["cancer"] == cancer_type]
try: curr_idx = t_options.index(st.session_state.selected_trial)
except: curr_idx = 0

selected_name = st.selectbox("🎯 快速搜尋或切換詳細試驗報告：", t_options, index=curr_idx)
t = next(it for it in st.session_state.trials_db if it["name"] == selected_name)

# 深度報告容器
st.markdown(f"<div class='detail-section-container'>", unsafe_allow_html=True)
st.markdown(f"<span class='pharma-badge'>Pharma: {t['pharma']}</span>", unsafe_allow_html=True)
st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #E0E0E0; padding-bottom:15px; font-weight:900;'>📋 {t['name']} 深度分析報告</h2>", unsafe_allow_html=True)

# 藥物機轉視覺


r1_c1, r1_c2 = st.columns([1.3, 1])
with r1_c1:
    st.markdown("<div class='info-box-blue'><b>💉 Dosing Protocol & Rationale</b></div>", unsafe_allow_html=True)
    st.write(f"**核心藥物:** {t['drug']}")
    for arm, details in t['dosing'].items():
        st.write(f"🔹 **{arm}**: {details}")
    st.markdown("---")
    st.write(f"**機轉 Rationale:** {t['rationale']}")

with r1_c2:
    st.markdown("<div class='info-box-gold'><b>📈 Efficacy & Outcomes (Hazard Ratio)</b></div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class='hr-display-box'>
            <div class='hr-label-text'>Hazard Ratio (HR)</div>
            <div class='hr-big-val'>{t['outcomes']['HR']}</div>
            <div class='hr-ci-small'>{t['outcomes']['CI']}</div>
        </div>
    """, unsafe_allow_html=True)
    
    # KM 曲線參考
    
    
    st.write(f"**ORR:** {t['outcomes']['ORR']} | **mPFS:** {t['outcomes']['mPFS']}")
    st.error(f"**Safety / AE:** {t['outcomes']['AE']}")
    st.caption(f"Ref: {t['ref']}")

st.divider()
r2_c1, r2_c2 = st.columns(2)
with r2_c1:
    st.markdown("<div class='inc-box'><b>✅ Inclusion Criteria</b></div>", unsafe_allow_html=True)
    for inc in t['inclusion']: st.write(f"• **{inc}**")
with r2_c2:
    st.markdown("<div class='exc-box'><b>❌ Exclusion Criteria</b></div>", unsafe_allow_html=True)
    for exc in t['exclusion']: st.write(f"• **{exc}**")
st.markdown("</div>", unsafe_allow_html=True)
