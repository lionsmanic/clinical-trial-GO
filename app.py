import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床試驗導航系統 (三大癌症大綱重構版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=Roboto:wght@400;700;900&display=swap');
    
    /* === 全域視覺樣式 === */
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', 'Roboto', sans-serif;
        background-color: #F4F7F9; /* 晨霧灰藍背景 */
        color: #1A1A1A;
        font-size: 21px !important;
        line-height: 1.6;
    }

    /* 主標題 */
    .main-title {
        font-size: 46px !important; font-weight: 900; color: #004D40;
        padding: 25px 0 15px 0; border-bottom: 5px solid #4DB6AC;
        margin-bottom: 30px;
    }

    /* === 臨床大綱區塊卡片 === */
    .stage-card-base {
        border-radius: 18px; padding: 18px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.06);
        border: 2.5px solid transparent;
        min-height: 200px; background: white;
        transition: all 0.2s ease;
    }
    
    .stage-header {
        font-size: 24px !important; font-weight: 900; color: white;
        margin: -18px -18px 15px -18px; padding: 12px;
        border-radius: 16px 16px 0 0; text-align: center;
    }

    /* 四大療程區塊配色 */
    /* Primary Tx (1L) */
    .card-primary-tx { border-color: #43A047; }
    .header-primary-tx { background: linear-gradient(135deg, #66BB6A, #43A047); }
    /* Primary Maintenance */
    .card-primary-maint { border-color: #0288D1; }
    .header-primary-maint { background: linear-gradient(135deg, #29B6F6, #0288D1); }
    /* Recurrence Tx */
    .card-recurr-tx { border-color: #F57C00; }
    .header-recurr-tx { background: linear-gradient(135deg, #FFB74D, #F57C00); }
    /* Recurrence Maintenance */
    .card-recurr-maint { border-color: #7B1FA2; }
    .header-recurr-maint { background: linear-gradient(135deg, #BA68C8, #7B1FA2); }

    /* === 深度分析數據呈現 === */
    .detail-section {
        background: white; border-radius: 20px; padding: 40px;
        margin-top: 40px; box-shadow: 0 15px 50px rgba(0,0,0,0.1);
        border: 1px solid #CFD8DC;
    }

    .info-box-blue { background: #E3F2FD; border-radius: 15px; padding: 25px; border-left: 10px solid #1976D2; }
    .info-box-gold { background: #FFF8E1; border-radius: 15px; padding: 25px; border-left: 10px solid #FBC02D; }
    
    .hr-display {
        background: white; border-radius: 15px; padding: 25px;
        text-align: center; border: 3px solid #FFE082;
    }
    .hr-big-val {
        font-family: 'Roboto', sans-serif; font-size: 52px !important; 
        font-weight: 900; color: #D84315; line-height: 1;
    }
    .hr-ci-label { font-size: 20px !important; color: #5D4037; margin-top: 10px; font-weight: 700; }

    .pharma-tag { 
        background: #004D40; color: white; padding: 8px 20px; 
        border-radius: 50px; font-size: 15px; font-weight: 700;
        display: inline-block; margin-bottom: 15px;
    }

    /* 按鈕字體加粗 */
    .stPopover button { font-weight: 700 !important; font-size: 19px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 深度臨床資料庫 (依新大綱重新分類) ---
if 'trials_db' not in st.session_state:
    st.session_state.trials_db = [
        # --- Ovarian Cancer ---
        {
            "cancer": "Ovarian", "name": "FRAmework-01 (LY4170156)", "pharma": "Eli Lilly",
            "drug": "LY4170156 + Bevacizumab", "pos": "Recurrence Tx",
            "summary": "針對 FRα 陽性。Part A (PROC) 與 Part B (PSOC)。",
            "rationale": "標靶 FRα ADC 聯手 Bevacizumab。專攻 PARPi 失敗後之需求。",
            "dosing": {"Experimental": "LY4170156 3 mg/kg + Bev 15 mg/kg Q3W", "Control": "TPC or Platinum doublet"},
            "outcomes": {"ORR": "35-40%", "mPFS": "TBD", "mOS": "TBD", "HR": "Recruiting", "CI": "NCT06536348", "AE": "Proteinuria, ILD"},
            "inclusion": ["High-grade Serous / Carcinosarcoma", "FRα Positive", "Part A (PROC), Part B (PSOC)"],
            "exclusion": ["曾用過 Topo I ADC (如 DS-8201)", "ILD 病史"],
            "ref": "Source: NCT06536348"
        },
        {
            "cancer": "Ovarian", "name": "REJOICE-Ovarian01", "pharma": "Daiichi Sankyo",
            "drug": "R-DXd (Raludotatug Deruxtecan)", "pos": "Recurrence Tx",
            "summary": "針對 CDH6 標靶 ADC，專攻鉑類抗藥性 (PROC) 患者。",
            "rationale": "標靶 CDH6 ADC。具備強力 Bystander Effect，適合 PROC 後線治療。",
            "dosing": {"Experimental": "R-DXd 5.6 mg/kg IV Q3W.", "Control": "TPC (Paclitaxel/PLD/Topotecan)"},
            "outcomes": {"ORR": "46.0%", "mPFS": "7.1m", "mOS": "N/A", "HR": "Phase 3", "CI": "NCT06161025", "AE": "ILD Risk, Nausea"},
            "inclusion": ["PROC 卵巢癌", "曾接受 1-4 線治療", "需曾用過 Bevacizumab"],
            "exclusion": ["Low-grade 腫瘤", "ILD 病史"],
            "ref": "JCO 2024"
        },
        {
            "cancer": "Ovarian", "name": "TroFuse-021", "pharma": "MSD",
            "drug": "Sac-TMT (MK-2870)", "pos": "Primary Maintenance",
            "summary": "一線維持治療。針對 pHRD 患者，結合 Trop-2 ADC 與 Beva。",
            "rationale": "針對 Trop-2 高表達之 pHRD 患者，旨在優化一線化療後的維持方案。",
            "dosing": {"Arm 1": "Sac-TMT Mono", "Arm 2": "Sac-TMT + Beva", "Arm 3": "Observation/Beva"},
            "outcomes": {"ORR": "Est. 40%", "mPFS": "TBD", "mOS": "TBD", "HR": "Ongoing", "CI": "NCT06241729", "AE": "Diarrhea, Stomatitis"},
            "inclusion": ["新診斷 FIGO III/IV", "HRD Negative (pHRD)", "1L Chemo CR/PR"],
            "exclusion": ["HRD Positive", "嚴重腸胃道疾病史"],
            "ref": "ENGOT-ov85"
        },
        {
            "cancer": "Ovarian", "name": "DS8201-772 (Enhertu)", "pharma": "AstraZeneca",
            "drug": "T-DXd", "pos": "Recurrence Maintenance",
            "summary": "針對 HER2 Low 之 PSOC 維持治療。",
            "rationale": "HER2 標靶 ADC。救援化療後穩定 (Non-PD) 族群之維持首選。",
            "dosing": {"Mono": "T-DXd 5.4 mg/kg Q3W", "Combo": "T-DXd + Beva 15 mg/kg Q3W"},
            "outcomes": {"ORR": "46.3%", "mPFS": "10.4m", "mOS": "N/A", "HR": "0.42", "CI": "95% CI: 0.30-0.58", "AE": "ILD Risk"},
            "inclusion": ["HER2 IHC 1+/2+/3+", "Recurrent s/p rescue chemo"],
            "exclusion": ["ILD 病史", "LVEF < 50%"],
            "ref": "JCO 2024"
        },
        # --- Endometrial Cancer ---
        {
            "cancer": "Endometrial", "name": "MK2870-033", "pharma": "MSD",
            "drug": "Sac-TMT + Pembro", "pos": "Primary Maintenance",
            "summary": "一線化療合併免疫後之維持治療 (pMMR)。",
            "rationale": "Chemo-IO 時代之維持首選，結合 Trop-2 ADC 強化應答。",
            "dosing": {"Maintenance": "Pembro (400mg) + Sac-TMT (5mg/kg) Q6W"},
            "outcomes": {"ORR": "Est. > 35%", "mPFS": "Phase 3", "mOS": "TBD", "HR": "Ongoing", "CI": "NCT06132958", "AE": "Stomatitis"},
            "inclusion": ["pMMR EC", "FIGO III/IV", "1L CR/PR"],
            "exclusion": ["Sarcoma", "Prior PD-1"],
            "ref": "ESMO 2025"
        },
        {
            "cancer": "Endometrial", "name": "GU-US-682-6769", "pharma": "Gilead",
            "drug": "SG (Trodelvy)", "pos": "Recurrence Tx",
            "summary": "二/三線 EC 復發治療。針對 Trop-2 ADC。",
            "rationale": "針對 Platinum + PD-1 失敗後患者之重要救援方案。",
            "dosing": {"Experimental": "SG 10 mg/kg IV (D1, D8)", "Control": "TPC (Doxo/Taxel)"},
            "outcomes": {"ORR": "28.5%", "mPFS": "5.6m", "mOS": "12.8m", "HR": "0.64", "CI": "95% CI: 0.48-0.84", "AE": "Neutropenia"},
            "inclusion": ["Recurrent EC", "≥1 prior Platinum line", "Prior Anti-PD-1/L1 required"],
            "exclusion": ["Prior Trop-2 ADC", "Active CNS 轉移"],
            "ref": "JCO 2024"
        },
        # --- Cervical Cancer ---
        {
            "cancer": "Cervical", "name": "innovaTV 301", "pharma": "Seagen / Genmab",
            "drug": "Tisotumab Vedotin (Tivdak)", "pos": "Recurrence Tx",
            "summary": "針對二/三線復發性子宮頸癌之 ADC 藥物。FDA 已核准。",
            "rationale": "標靶 Tissue Factor (TF) ADC。用於前線化療與免疫治療失敗後之轉移性病灶。",
            "dosing": {"Experimental": "Tisotumab vedotin 2.0 mg/kg IV Q3W.", "Control": "Chemotherapy (TPC)"},
            "outcomes": {"ORR": "17.8%", "mPFS": "4.2m", "mOS": "11.5m", "HR": "0.70 (OS)", "CI": "95% CI: 0.54-0.89", "AE": "Ocular toxicity, Neuropathy"},
            "inclusion": ["Recurrent/Metastatic Cervical Cancer", "Prior 1-2 systemic lines", "Prior bevacizumab and Anti-PD-1/L1 (if applicable)"],
            "exclusion": ["Active CNS metastasis", "Severe ocular surface disease"],
            "ref": "NEJM 2024; innovaTV 301"
        }
    ]

# --- 2. 狀態同步 ---
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = st.session_state.trials_db[0]['name']

# --- 3. 側邊欄：AI 決策助理 ---
with st.sidebar:
    st.markdown("<h2 style='color: #6A1B9A;'>🤖 AI 專家助理</h2>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 臨床條件比對 (大綱導航)", expanded=False):
        patient_notes = st.text_area("輸入病歷摘要", height=250, placeholder="例：62y/o Ovarian cancer, PROC, FRα+, ECOG 1...")
        if st.button("🚀 開始深度分析"):
            if api_key and patient_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    prompt = f"分析病歷：{patient_notes}。請參考這 7 個臨床試驗：{st.session_state.trials_db}，根據使用者提供的大綱分類，判斷該患者應屬於哪個療程區塊，並建議適合的試驗。"
                    response = model.generate_content(prompt)
                    st.write(response.text)
                except Exception as e: st.error(f"AI 異常: {e}")

# --- 4. 主頁面：療程區塊導航 ---
st.markdown("<div class='main-title'>婦癌臨床試驗導航地圖 (2026 專家版)</div>", unsafe_allow_html=True)

# 顯示治療大綱示意圖


cancer_type = st.radio("第一步：選擇癌症類型", ["Ovarian", "Endometrial", "Cervical"], horizontal=True)

st.subheader("第二步：選擇療程區塊查看對應試驗")
c1, c2, c3, c4 = st.columns(4)

stages = {
    "P-TX": {"label": "初治 (Primary Tx)", "col": c1, "pos": "Primary Treatment", "css": "primary-tx"},
    "P-MT": {"label": "一線維持 (1L Maint)", "col": c2, "pos": "Primary Maintenance", "css": "primary-maint"},
    "R-TX": {"label": "復發治療 (Recurr Tx)", "col": c3, "pos": "Recurrence Tx", "css": "recurr-tx"},
    "R-MT": {"label": "復發後維持 (PR-Maint)", "col": c4, "pos": "Recurrence Maintenance", "css": "recurr-maint"}
}

for key, info in stages.items():
    with info["col"]:
        st.markdown(f"""<div class='stage-card-base card-{info['css']}'><div class='stage-header header-{info['css']}'>{info['label']}</div>""", unsafe_allow_html=True)
        relevant_trials = [t for t in st.session_state.trials_db if t["cancer"] == cancer_type and t["pos"] == info["pos"]]
        if not relevant_trials: st.caption("無匹配試驗")
        else:
            for t in relevant_trials:
                label = f"📍 {t['pharma']} | {t['name']}"
                with st.popover(label, use_container_width=True):
                    st.markdown(f"### ✨ {t['name']} 亮點")
                    st.info(t['summary'])
                    if st.button("📊 開啟分析報告", key=f"go_{t['name']}"):
                        st.session_state.selected_trial = t['name']
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. 深度分析報告看板 ---
st.divider()
t_options = [t["name"] for t in st.session_state.trials_db if t["cancer"] == cancer_type]
try: curr_idx = t_options.index(st.session_state.selected_trial)
except: curr_idx = 0

if t_options:
    selected_name = st.selectbox("🎯 快速搜尋詳細試驗報告：", t_options, index=curr_idx)
    t = next(it for it in st.session_state.trials_db if it["name"] == selected_name)

    st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
    st.markdown(f"<span class='pharma-tag'>Pharma: {t['pharma']}</span>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #E0E0E0; padding-bottom:15px; font-weight:900;'>📋 {t['name']} 深度分析報告</h2>", unsafe_allow_html=True)

    r1_c1, r1_c2 = st.columns([1.3, 1])
    with r1_c1:
        st.markdown("<div class='info-box-blue'><b>💉 Dosing Protocol & Rationale</b></div>", unsafe_allow_html=True)
        st.write(f"**核心藥物:** {t['drug']}")
        for arm, details in t['dosing'].items(): st.write(f"🔹 **{arm}**: {details}")
        st.markdown("---")
        st.success(f"**機轉 Rationale:** {t['rationale']}")
        

    with r1_c2:
        st.markdown("<div class='info-box-gold'><b>📈 Efficacy & Outcomes</b></div>", unsafe_allow_html=True)
        st.markdown(f"""
            <div class='hr-display'>
                <div style='font-size: 16px; color: #795548; font-weight:700; margin-bottom:8px;'>Hazard Ratio (HR) / NCT</div>
                <div class='hr-big-val'>{t['outcomes']['HR']}</div>
                <div class='hr-ci'>{t['outcomes']['CI']}</div>
            </div>
        """, unsafe_allow_html=True)
        st.write(f"**ORR:** {t['outcomes']['ORR']} | **mPFS:** {t['outcomes']['mPFS']}")
        st.error(f"**Safety / AE:** {t['outcomes']['AE']}")
        

    st.divider()
    r2_c1, r2_c2 = st.columns(2)
    with r2_c1:
        st.markdown("<div class='info-box-blue' style='background:#E8F5E9; border-left:8px solid #2E7D32;'><b>✅ Inclusion Criteria</b></div>", unsafe_allow_html=True)
        for inc in t['inclusion']: st.write(f"• **{inc}**")
    with r2_c2:
        st.markdown("<div class='info-box-blue' style='background:#FFEBEE; border-left:8px solid #C62828;'><b>❌ Exclusion Criteria</b></div>", unsafe_allow_html=True)
        for exc in t['exclusion']: st.write(f"• **{exc}**")
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("請先選擇癌別。")
