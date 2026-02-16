import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床試驗專家導航系統 (2026 SIV 更新版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=Roboto:wght@400;700;900&display=swap');
    
    /* === 全域 UI 優化 === */
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', 'Roboto', sans-serif;
        background-color: #F0F4F8;
        color: #1A1A1A;
        font-size: 21px !important;
        line-height: 1.6;
    }

    /* 主標題：專業漸層 */
    .main-title {
        font-size: 48px !important; font-weight: 900; color: #004D40;
        padding: 25px 0 15px 0; border-bottom: 4px solid #4DB6AC;
        margin-bottom: 25px;
    }

    /* === 病程區塊卡片：緊湊比例與字體 === */
    .stage-card-base {
        border-radius: 16px; padding: 15px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.08);
        border: 2.5px solid transparent;
        min-height: 200px; background: white;
        transition: all 0.2s ease;
    }
    
    .stage-header {
        font-size: 24px !important; font-weight: 900; color: white;
        margin: -15px -15px 15px -15px; padding: 12px;
        border-radius: 14px 14px 0 0; text-align: center;
    }

    /* 配色編碼 */
    .card-1l { border-color: #43A047; }
    .header-1l { background: linear-gradient(135deg, #66BB6A, #43A047); }
    .card-1lm { border-color: #0288D1; }
    .header-1lm { background: linear-gradient(135deg, #29B6F6, #0288D1); }
    .card-rc { border-color: #FB8C00; }
    .header-rc { background: linear-gradient(135deg, #FFB74D, #F57C00); }
    .card-prm { border-color: #8E24AA; }
    .header-prm { background: linear-gradient(135deg, #BA68C8, #7B1FA2); }

    /* === 深度分析看板 === */
    .detail-section {
        background: white; border-radius: 20px; padding: 40px;
        margin-top: 35px; box-shadow: 0 12px 40px rgba(0,0,0,0.1);
        border: 1px solid #CFD8DC;
    }

    .info-box-blue {
        background: #E3F2FD; border-radius: 15px; padding: 25px;
        border-left: 8px solid #1976D2; color: #0D47A1; font-size: 21px;
    }
    .info-box-gold {
        background: #FFF8E1; border-radius: 15px; padding: 25px;
        border-left: 8px solid #FBC02D; color: #5F4B09; font-size: 21px;
    }
    
    /* Hazard Ratio 數值巨量化 */
    .hr-display {
        background: white; border-radius: 15px; padding: 20px;
        text-align: center; border: 3px solid #FFE082;
    }
    .hr-big-val {
        font-family: 'Roboto', sans-serif; font-size: 50px !important; 
        font-weight: 900; color: #D84315; line-height: 1;
    }
    .hr-ci { font-size: 20px !important; color: #5D4037; margin-top: 10px; font-weight: 700; }

    /* 收案條件 */
    .inc-box { background: #E8F5E9; padding: 20px; border-radius: 12px; border-left: 8px solid #2E7D32; }
    .exc-box { background: #FFEBEE; padding: 20px; border-radius: 12px; border-left: 8px solid #C62828; }

    .pharma-badge { 
        background: #004D40; color: white; padding: 6px 18px; 
        border-radius: 50px; font-size: 14px; font-weight: 700;
        display: inline-block; margin-bottom: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 深度臨床資料庫 (含明早 SIV 兩大試驗) ---
if 'trials_db' not in st.session_state:
    st.session_state.trials_db = [
        {
            "cancer": "Ovarian", "name": "REJOICE-Ovarian01", "pharma": "Daiichi Sankyo",
            "drug": "R-DXd (Raludotatug Deruxtecan)", "pos": "Recurrence",
            "summary": "針對 CDH6 標靶之 ADC，專攻鉑類抗藥性 (PROC) 患者。是目前 PROC 後線最有潛力的試驗。",
            "rationale": "標靶 CDH6 ADC。利用 Deruxtecan 強效載荷與高 DAR 優勢，透過 Bystander Effect 克服腫瘤異質性。",
            "dosing": {
                "Experimental Arm": "R-DXd 5.6 mg/kg IV Q3W.",
                "Control Arm (TPC)": "Paclitaxel, PLD, or Topotecan (研究者選擇化療)."
            },
            "outcomes": {"ORR": "46.0% (Phase 1 Update)", "mPFS": "7.1 months", "mOS": "N/A", "HR": "Phase 3 Pending", "CI": "NCT06161025", "AE": "Nausea, Fatigue, ILD Risk"},
            "inclusion": ["High-grade Serous/Endometrioid Ovarian Cancer", "Platinum-resistant (PROC)", "1-3 prior lines of therapy", "Prior Bevacizumab use is required"],
            "exclusion": ["Low-grade/Borderline tumors", "Prior ILD requiring steroids", "Grade ≥2 neuropathy"],
            "ref": "JCO 2024; ESMO 2025 update"
        },
        {
            "cancer": "Ovarian", "name": "TroFuse-021", "pharma": "MSD (Merck)",
            "drug": "Sac-TMT (MK-2870)", "pos": "1L Maintenance",
            "summary": "一線維持治療。針對 HRD 陰性 (pHRD) 患者，結合 Trop-2 ADC 與 Bevacizumab。",
            "rationale": "針對 Trop-2 高表達之 pHRD 患者。ADC 誘導 ICD 協同 Bevacizumab 改善微環境，旨在替代或優化現有維持方案。",
            "dosing": {
                "Arm 1": "Sac-TMT Monotherapy Q2W/Q3W.",
                "Arm 2": "Sac-TMT + Bevacizumab 15 mg/kg Q3W.",
                "Arm 3 (SoC)": "Observation or Bevacizumab alone."
            },
            "outcomes": {"ORR": "Est. 40% (pHRD cohort)", "mPFS": "Phase 3 Recruiting", "mOS": "TBD", "HR": "Ongoing", "CI": "NCT06241729", "AE": "Stomatitis, Diarrhea, Anemia"},
            "inclusion": ["Newly diagnosed FIGO Stage III/IV Ovarian Cancer", "HRD Negative (pHRD) / BRCA WT", "Post-1L Platinum Chemo (Achieved CR/PR)"],
            "exclusion": ["BRCA Mutation / HRD Positive", "Severe Gastrointestinal disease", "Active Autoimmune disease"],
            "ref": "ENGOT-ov85; ClinicalTrials.gov 2026"
        },
        {
            "cancer": "Endometrial", "name": "GU-US-682-6769", "pharma": "Gilead",
            "drug": "SG (Trodelvy)", "pos": "Recurrence",
            "summary": "針對 Trop-2 ADC。顯著改善二/三線 EC 患者生存期。具備強力 Bystander Effect。",
            "rationale": "標靶 Trop-2 ADC。釋放 SN-38 載荷引發 DNA 損傷。適合先前 Platinum + PD-1 失敗之進展性患者。",
            "dosing": {
                "Arm A": "SG 10 mg/kg IV (Days 1, 8 of Q21D).",
                "Arm B (TPC)": "Doxorubicin or Paclitaxel weekly."
            },
            "outcomes": {"ORR": "28.5%", "mPFS": "5.6m", "mOS": "12.8m", "HR": "0.64", "CI": "95% CI: 0.48-0.84", "AE": "Neutropenia"},
            "inclusion": ["Recurrent EC", "≥1 prior Platinum chemo line", "Prior Anti-PD-1/L1 mandatory"],
            "exclusion": ["Prior TROP-2 ADC therapy", "Active CNS metastasis"],
            "ref": "JCO 2024; TROPiCS-03 Study"
        }
    ]

# --- 2. 狀態同步 ---
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = st.session_state.trials_db[0]['name']

# --- 3. 側邊欄：AI 專家助理 ---
with st.sidebar:
    st.markdown("<h2 style='color: #6A1B9A;'>🤖 專家決策助理</h2>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 患者條件媒合分析 (SIV 輔助)", expanded=False):
        patient_notes = st.text_area("輸入病歷摘要", height=250, placeholder="例：62y/o OCCC, pHRD, s/p 1L Chemo CR...")
        if st.button("🚀 開始深度分析"):
            if api_key and patient_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    prompt = f"分析病歷：{patient_notes}。資料庫：{st.session_state.trials_db}。建議適合試驗與理由。"
                    response = model.generate_content(prompt)
                    st.write(response.text)
                except Exception as e: st.error(f"AI 異常: {e}")

# --- 4. 主頁面：病程導航 ---
st.markdown("<div class='main-title'>婦癌臨床試驗導航儀表板 (2026 SIV Edition)</div>", unsafe_allow_html=True)
cancer_type = st.radio("第一步：選擇癌症類型", ["Ovarian", "Endometrial"], horizontal=True)

st.subheader("第二步：點擊階段標記查看 SIV 試驗亮點")
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
                    st.write(f"**藥廠:** {t['pharma']}")
                    st.write(f"**主要配方:** {t['drug']}")
                    if st.button("📊 開啟深度分析報告", key=f"go_{t['name']}"):
                        st.session_state.selected_trial = t['name']
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. 深度分析報告看板 ---
st.divider()
t_options = [t["name"] for t in st.session_state.trials_db if t["cancer"] == cancer_type]
try: curr_idx = t_options.index(st.session_state.selected_trial)
except: curr_idx = 0

selected_name = st.selectbox("🎯 快速搜尋詳細試驗報告：", t_options, index=curr_idx)
t = next(it for it in st.session_state.trials_db if it["name"] == selected_name)

st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
st.markdown(f"<span class='pharma-badge'>Pharma: {t['pharma']}</span>", unsafe_allow_html=True)
st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #E0E0E0; padding-bottom:15px; font-weight:900;'>📋 {t['name']} 深度分析報告</h2>", unsafe_allow_html=True)

r1_c1, r1_c2 = st.columns([1.3, 1])
with r1_c1:
    st.markdown("<div class='info-box-blue'><b>💉 Dosing Protocol & Rationale</b></div>", unsafe_allow_html=True)
    st.write(f"**核心藥物:** {t['drug']}")
    for arm, details in t['dosing'].items():
        st.write(f"🔹 **{arm}**: {details}")
    st.markdown("---")
    st.success(f"**機轉 Rationale:** {t['rationale']}")

with r1_c2:
    st.markdown("<div class='info-box-gold'><b>📈 Efficacy & Outcomes</b></div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class='hr-display'>
            <div style='font-size: 16px; color: #795548; font-weight:700; margin-bottom:8px;'>Hazard Ratio (HR) / ID</div>
            <div class='hr-big-val'>{t['outcomes']['HR']}</div>
            <div class='hr-ci'>{t['outcomes']['CI']}</div>
        </div>
    """, unsafe_allow_html=True)
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
