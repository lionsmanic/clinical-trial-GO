import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床導航系統 (指引 SoS + 試驗對照版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=Roboto:wght@400;700;900&display=swap');
    
    /* === 全域字體與背景 === */
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', 'Roboto', sans-serif;
        background-color: #F0F4F8;
        color: #1A1A1A;
        font-size: 21px !important;
        line-height: 1.6;
    }

    /* 主標題 */
    .main-title {
        font-size: 44px !important; font-weight: 900; color: #004D40;
        padding: 20px 0 10px 0; border-bottom: 4px solid #4DB6AC;
        margin-bottom: 25px;
    }

    /* === 大區塊：病程階段卡片 === */
    .big-stage-card {
        border-radius: 20px; padding: 15px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.07);
        border: 2.5px solid transparent;
        min-height: 350px; background: white;
        margin-bottom: 20px;
    }
    .big-stage-header {
        font-size: 25px !important; font-weight: 900; color: white;
        margin: -15px -15px 15px -15px; padding: 12px;
        border-radius: 18px 18px 0 0; text-align: center;
    }

    /* === 小區塊：指引建議 (SoC) === */
    .soc-block {
        background: #ECEFF1; border-radius: 10px; padding: 12px;
        margin-bottom: 15px; border-left: 6px solid #607D8B;
    }
    .soc-title { font-size: 16px; font-weight: 800; color: #455A64; margin-bottom: 5px; }
    .soc-content { font-size: 18px; color: #263238; font-weight: 500; }

    /* 配色方案 */
    .card-p-tx { border-color: #43A047; }
    .header-p-tx { background: linear-gradient(135deg, #66BB6A, #43A047); }
    .card-p-mt { border-color: #0288D1; }
    .header-p-mt { background: linear-gradient(135deg, #29B6F6, #0288D1); }
    .card-r-tx { border-color: #FB8C00; }
    .header-r-tx { background: linear-gradient(135deg, #FFB74D, #F57C00); }
    .card-r-mt { border-color: #8E24AA; }
    .header-r-mt { background: linear-gradient(135deg, #BA68C8, #7B1FA2); }

    /* === 深度數據看板 === */
    .detail-section {
        background: white; border-radius: 20px; padding: 40px;
        margin-top: 30px; box-shadow: 0 15px 50px rgba(0,0,0,0.1);
        border: 1px solid #CFD8DC;
    }
    .hr-big-val {
        font-family: 'Roboto', sans-serif; font-size: 50px !important; 
        font-weight: 900; color: #D84315; line-height: 1;
    }
    .pharma-badge { 
        background: #004D40; color: white; padding: 6px 18px; 
        border-radius: 50px; font-size: 14px; font-weight: 700;
        display: inline-block; margin-bottom: 12px;
    }
    .stPopover button { font-weight: 700 !important; font-size: 17px !important; border-radius: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 指引大綱數據庫 (Standard of Care) ---
guidelines = {
    "Ovarian": {
        "P-TX": "Surgery (PDS/IDS) + Carboplatin/Paclitaxel x6 ± Bevacizumab",
        "P-MT": "BRCAm: PARPi (Olaparib/Niraparib); HRD+: PARPi ± Bev; pHRD: Bevacizumab or observation",
        "R-TX": "Sensitive (PFI >6m): Platinum doublet ± Bev; Resistant (PFI <6m): Single Chemo ± Bev or Elahere (FRα+)",
        "R-MT": "PARPi Maintenance (if not used 1L and platinum-sensitive)"
    },
    "Endometrial": {
        "P-TX": "Surgery + Radiotherapy ± Chemo; Advanced: Chemo + IO (Pembro/Dostarlimab)",
        "P-MT": "Continue IO Maintenance (Pembro or Dostarlimab) for advanced/recurrent primary",
        "R-TX": "dMMR: Anti-PD-1; pMMR: Pembro + Lenvatinib; Serous HER2+: Chemo + Anti-HER2",
        "R-MT": "Continuous therapy until PD (Pembro + Lenva)"
    },
    "Cervical": {
        "P-TX": "Early: Surgery; Locally Advanced: CCRT (Cisplatin + Brachytherapy); Metastatic: Pembro + Chemo ± Bev",
        "P-MT": "Follow-up for early/LA; Pembro maintenance for metastatic 1L",
        "R-TX": "Tisotumab vedotin (Tivdak) for 2L/3L; Cemiplimab or Chemo (Topotecan/Gemcitabine)",
        "R-MT": "Continuous 1L IO therapy until PD"
    }
}

# --- 2. 臨床試驗數據庫 (7 核心試驗) ---
if 'trials_db' not in st.session_state:
    st.session_state.trials_db = [
        {"cancer": "Ovarian", "name": "FRAmework-01", "pharma": "Eli Lilly", "drug": "LY4170156 + Bev", "pos": "R-TX", "summary": "針對 FRα+ 之 PROC/PSOC 患者。LY4170156 3mg/kg + Bev 15mg/kg Q3W。", "rationale": "FRα 標靶 ADC 聯手 Bevacizumab。利用協同效應克服 PARPi 耐藥。", "dosing": {"Experimental": "LY4170156 3 mg/kg + Bev 15 mg/kg Q3W", "Control A (PROC)": "TPC or Mirvetuximab", "Control B (PSOC)": "Platinum doublet + Bev"}, "outcomes": {"ORR": "35-40%", "mPFS": "Endpoint", "HR": "Phase 3", "CI": "NCT06536348", "AE": "Proteinuria, ILD"}, "inclusion": ["High-grade Serous / Carcinosarcoma", "FRα 陽性", "Part A: PROC, Part B: PSOC"], "exclusion": ["曾用過 Topo I ADC", "ILD 病史"], "ref": "NCT06536348"},
        {"cancer": "Ovarian", "name": "REJOICE-Ovarian01", "pharma": "Daiichi Sankyo", "drug": "R-DXd", "pos": "R-TX", "summary": "針對 CDH6 標靶 ADC，專攻 PROC 患者。", "rationale": "標靶 CDH6 ADC。具備強力 Bystander Effect，適合 PROC 後線。", "dosing": {"Experimental": "R-DXd 5.6 mg/kg Q3W", "Control": "TPC (Taxel/PLD/Topotecan)"}, "outcomes": {"ORR": "46.0%", "mPFS": "7.1m", "HR": "Phase 3", "CI": "NCT06161025", "AE": "ILD Risk"}, "inclusion": ["PROC 卵巢癌", "曾接受 1-4 線", "需曾用過 Bev"], "exclusion": ["ILD 病史", "LVEF < 50%"], "ref": "JCO 2024"},
        {"cancer": "Ovarian", "name": "TroFuse-021", "pharma": "MSD", "drug": "Sac-TMT (MK-2870)", "pos": "P-MT", "summary": "針對 pHRD 患者之 1L 維持。結合 Trop-2 ADC 與 Beva。", "rationale": " Trop-2 ADC 誘導 ICD 協同 Beva 改善微環境，挑戰 SoC。", "dosing": {"Arm 1": "Sac-TMT Mono", "Arm 2": "Sac-TMT + Beva", "Arm 3": "Observation/Beva"}, "outcomes": {"ORR": "Est 40%", "mPFS": "Ongoing", "HR": "Phase 3", "CI": "NCT06241729", "AE": "Diarrhea"}, "inclusion": ["Stage III/IV", "pHRD / BRCA WT", "1L Chemo CR/PR"], "exclusion": ["HRD Positive", "嚴重腸胃病史"], "ref": "ENGOT-ov85"},
        {"cancer": "Ovarian", "name": "DOVE", "pharma": "GSK", "drug": "Dostarlimab + Beva", "pos": "R-TX", "summary": "針對 OCCC 透明細胞癌，雙重阻斷 PD-1 與 VEGF。", "rationale": "改善 OCCC 免疫抑制微環境，恢復 T 細胞效能。", "dosing": {"Combo": "Dostarlimab + Bev 15mg/kg Q3W", "Control": "Chemo (Gem/PLD/Taxel)"}, "outcomes": {"ORR": "40.2%", "mPFS": "8.2m", "HR": "0.58", "CI": "95% CI: 0.42-0.79", "AE": "Hypertension"}, "inclusion": ["OCCC > 50%", "Platinum-resistant"], "exclusion": ["Prior IO therapy"], "ref": "JCO 2025"},
        {"cancer": "Ovarian", "name": "DS8201-772", "pharma": "AstraZeneca", "drug": "Enhertu (T-DXd)", "pos": "R-MT", "summary": "針對 HER2 Low 之 PSOC 維持治療。", "rationale": "HER2 標靶 ADC。救援化療後 Non-PD 族群之維持首選。", "dosing": {"Mono": "T-DXd 5.4 mg/kg Q3W", "Combo": "T-DXd + Beva 15 mg/kg Q3W"}, "outcomes": {"ORR": "46.3%", "mPFS": "10.4m", "HR": "0.42", "CI": "95% CI: 0.30-0.58", "AE": "ILD Risk"}, "inclusion": ["HER2 IHC 1+/2+/3+", "Recurr s/p rescue chemo"], "exclusion": ["ILD 病史"], "ref": "JCO 2024"},
        {"cancer": "Endometrial", "name": "MK2870-033", "pharma": "MSD", "drug": "Sac-TMT + Pembro", "pos": "P-MT", "summary": "一線化療合併免疫後之維持 (pMMR)。", "rationale": "結合 Trop-2 ADC 強化 Chemo-IO 時代的應答持續性。", "dosing": {"Maintenance": "Pembro 400mg + Sac-TMT 5mg/kg Q6W"}, "outcomes": {"ORR": "Est 35%", "mPFS": "Ongoing", "HR": "TBD", "CI": "NCT06132958", "AE": "Stomatitis"}, "inclusion": ["pMMR EC", "FIGO III/IV", "1L CR/PR"], "exclusion": ["Sarcoma", "Prior IO for advanced"], "ref": "ESMO 2025"},
        {"cancer": "Endometrial", "name": "GU-US-682-6769", "pharma": "Gilead", "drug": "SG (Trodelvy)", "pos": "R-TX", "summary": "二/三線復發治療。針對 Trop-2 ADC。", "rationale": "針對 Platinum + PD-1 失敗後之重要救援方案。", "dosing": {"Exp": "SG 10 mg/kg IV (D1, D8)", "Control": "TPC (Doxo/Taxel)"}, "outcomes": {"ORR": "28.5%", "mPFS": "5.6m", "HR": "0.64", "CI": "95% CI: 0.48-0.84", "AE": "Neutropenia"}, "inclusion": ["Recurrent EC", "Prior Platinum + IO", "ECOG 0-1"], "exclusion": ["Prior Trop-2 ADC"], "ref": "JCO 2024"},
        {"cancer": "Cervical", "name": "innovaTV 301", "pharma": "Seagen", "drug": "Tivdak (Tisotumab)", "pos": "R-TX", "summary": "針對 2L/3L 復發性子宮頸癌。TF 標靶 ADC。", "rationale": "標靶 Tissue Factor。解決前線化療與 IO 失敗後的需求。", "dosing": {"Exp": "Tivdak 2.0 mg/kg Q3W", "Control": "Chemotherapy (TPC)"}, "outcomes": {"ORR": "17.8%", "mPFS": "4.2m", "HR": "0.70 (OS)", "CI": "95% CI: 0.54-0.89", "AE": "Ocular toxicity"}, "inclusion": ["Recurr/Metastatic Cervical", "Prior 1-2 lines"], "exclusion": ["Severe ocular disease"], "ref": "NEJM 2024"}
    ]

# --- 3. 狀態與側邊欄 ---
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = st.session_state.trials_db[0]['name']

with st.sidebar:
    st.markdown("<h2 style='color: #6A1B9A;'>🤖 AI 專家助理</h2>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 臨床條件比對 (大綱導航)", expanded=False):
        patient_notes = st.text_area("輸入病歷摘要")
        if st.button("🚀 開始深度分析"):
            if api_key and patient_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    prompt = f"分析病歷：{patient_notes}。參考試驗：{st.session_state.trials_db}。根據病程大綱建議療效與試驗選擇。"
                    st.write(model.generate_content(prompt).text)
                except Exception as e: st.error(f"AI 異常: {e}")

# --- 4. 主頁面：療程大綱導航 ---
st.markdown("<div class='main-title'>婦癌臨床試驗導航系統 (2026 SoC 對照版)</div>", unsafe_allow_html=True)

cancer_type = st.radio("第一步：選擇癌症類型", ["Ovarian", "Endometrial", "Cervical"], horizontal=True)

# 顯示病程路徑參考圖


st.subheader("第二步：根據病程階段檢索「標準治療 (SoC)」與「臨床試驗」")
c1, c2, c3, c4 = st.columns(4)

stages = [
    {"id": "P-TX", "label": "初治 (Primary Tx)", "col": c1, "css": "p-tx"},
    {"id": "P-MT", "label": "一線維持 (1L Maint)", "col": c2, "css": "p-mt"},
    {"id": "R-TX", "label": "復發治療 (Recurr Tx)", "col": c3, "css": "r-tx"},
    {"id": "R-MT", "label": "復發後維持 (PR-Maint)", "col": c4, "css": "r-mt"}
]

for stage in stages:
    with stage["col"]:
        st.markdown(f"""<div class='big-stage-card card-{stage['css']}'><div class='big-stage-header header-{stage['css']}'>{stage['label']}</div>""", unsafe_allow_html=True)
        
        # 1. 小區塊：指引建議 (SoC)
        st.markdown(f"""<div class='soc-block'><div class='soc-title'>📘 指引建議 (Standard of Care)</div><div class='soc-content'>{guidelines[cancer_type][stage['id']]}</div></div>""", unsafe_allow_html=True)
        
        # 2. 臨床試驗標記
        relevant_trials = [t for t in st.session_state.trials_db if t["cancer"] == cancer_type and t["pos"] == stage["id"]]
        if relevant_trials:
            st.markdown("<div style='font-size:14px; font-weight:800; color:#004D40; margin-bottom:5px;'>🧪 相關臨床試驗 (Trials)</div>", unsafe_allow_html=True)
            for t in relevant_trials:
                # 📍 藥廠 | 代碼 | 藥物配方
                btn_label = f"📍 {t['pharma']} | {t['name']} | {t['drug']}"
                with st.popover(btn_label, use_container_width=True):
                    st.markdown(f"### ✨ {t['name']} 核心重點")
                    st.info(t['summary'])
                    if st.button("📊 開啟深度報告", key=f"go_{t['name']}"):
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
    st.markdown(f"<span class='pharma-badge'>Pharma: {t['pharma']}</span>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #E0E0E0; padding-bottom:15px; font-weight:900;'>📋 {t['name']} 深度分析報告</h2>", unsafe_allow_html=True)

    # 藥物機轉視覺
    

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
                <div style='font-size: 16px; color: #795548; font-weight:700; margin-bottom:8px;'>Hazard Ratio (HR) / NCT ID</div>
                <div class='hr-big-val'>{t['outcomes']['HR']}</div>
                <div class='hr-ci'>{t['outcomes']['CI']}</div>
            </div>
        """, unsafe_allow_html=True)
        st.write(f"**ORR:** {t['outcomes']['ORR']} | **mPFS:** {t['outcomes']['mPFS']}")
        st.error(f"**Safety / AE:** {t['outcomes']['AE']}")
        

    st.divider()
    r2_c1, r2_c2 = st.columns(2)
    with r2_c1:
        st.markdown("<div class='info-box-blue' style='background:#E8F5E9; border-left:8px solid #2E7D32;'><b>✅ Inclusion Criteria (繁中/En)</b></div>", unsafe_allow_html=True)
        for inc in t['inclusion']: st.write(f"• **{inc}**")
    with r2_c2:
        st.markdown("<div class='info-box-blue' style='background:#FFEBEE; border-left:8px solid #C62828;'><b>❌ Exclusion Criteria (繁中/En)</b></div>", unsafe_allow_html=True)
        for exc in t['exclusion']: st.write(f"• **{exc}**")
    st.markdown("</div>", unsafe_allow_html=True)
