import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床導航系統 (2026 分子分型與 SoC 整合版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=Roboto:wght@400;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', 'Roboto', sans-serif;
        background-color: #F0F4F7;
        color: #1A1A1A;
        font-size: 20px !important;
        line-height: 1.3;
    }

    .main-title {
        font-size: 40px !important; font-weight: 900; color: #004D40;
        padding: 10px 0 5px 0; border-bottom: 3px solid #4DB6AC;
        margin-bottom: 15px;
    }

    /* === 大階段方塊 === */
    .big-stage-card {
        border-radius: 14px; padding: 0px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.06);
        border: 2px solid transparent;
        background: white; margin-bottom: 8px; overflow: hidden;
        min-height: 600px;
    }
    .big-stage-header {
        font-size: 20px !important; font-weight: 900; color: white;
        padding: 8px; text-align: center;
    }

    /* === 子區塊 (Molecular Subtypes & SoC) === */
    .sub-block {
        margin: 6px 8px; padding: 8px;
        border-radius: 8px; background: #F8F9FA;
        border-left: 5px solid #607D8B;
    }
    .sub-block-title {
        font-size: 15px; font-weight: 900; color: #455A64;
        margin-bottom: 3px; border-bottom: 1.2px solid #CFD8DC; padding-bottom: 2px;
    }
    .sub-block-content {
        font-size: 16px; color: #263238; font-weight: 500; line-height: 1.25;
        margin-bottom: 5px;
    }

    /* 亞型強調標籤 */
    .subtype-label { font-weight: 800; color: #00796B; }
    .risk-high { color: #C62828; font-weight: 800; }
    .risk-low { color: #2E7D32; font-weight: 800; }

    /* 階段配色 */
    .card-p-tx { border-color: #43A047; }
    .header-p-tx { background: linear-gradient(135deg, #66BB6A, #43A047); }
    .card-p-mt { border-color: #0288D1; }
    .header-p-mt { background: linear-gradient(135deg, #29B6F6, #0288D1); }
    .card-r-tx { border-color: #FB8C00; }
    .header-r-tx { background: linear-gradient(135deg, #FFB74D, #F57C00); }
    .card-r-mt { border-color: #8E24AA; }
    .header-r-mt { background: linear-gradient(135deg, #BA68C8, #7B1FA2); }

    .detail-section {
        background: white; border-radius: 20px; padding: 40px;
        margin-top: 25px; box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        border: 1px solid #CFD8DC;
    }
    .hr-big-val { font-family: 'Roboto', sans-serif; font-size: 50px !important; font-weight: 900; color: #D84315; }
    .pharma-badge { background: #004D40; color: white; padding: 5px 16px; border-radius: 50px; font-size: 13px; font-weight: 700; display: inline-block; margin-bottom: 10px; }

    .stPopover button { 
        font-weight: 700 !important; font-size: 14px !important; 
        border-radius: 6px !important; background-color: #E0F2F1 !important;
        border: 1px solid #B2DFDB !important;
        margin-top: 2px !important; padding: 1px 6px !important;
        width: 100% !important; text-align: left !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 指引與分子分型導航數據 (包含 FIGO 2023 與 MOC) ---
guidelines_nested = {
    "Ovarian": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "HGSC / Endometrioid", "content": "PDS 或 NACT/IDS + Carboplatin/Paclitaxel x6 ± Bev"},
            {"title": "Mucinous (MOC) 鑑別", "content": "CK7+/SATB2- (原發) vs SATB2+ (GI轉移)。<br><span class='subtype-label'>Expansile:</span> 預後佳，I期可相對保守。<br><span class='subtype-label'>Infiltrative:</span> 易微轉移，Adjuvant門檻低。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "BRCA mutated", "content": "1. Olaparib 單藥維持<br>2. 曾用Bev且HRD+: Olaparib + Bev"},
            {"title": "HRD positive (wt)", "content": "1. 曾用Bev: Olaparib + Bev<br>2. 未用Bev: Niraparib"},
            {"title": "HRD negative / pHRD", "content": "Bev續用或觀察；視風險選用Niraparib"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "PSOC (PFI > 6m)", "content": "含鉑複方化療 ± Bevacizumab"},
            {"title": "PROC (PFI < 6m)", "content": "單藥化療 ± Bev 或 Elahere (FRα+)"},
            {"title": "MOC 晚期/復發", "content": "化療抗性高。考慮 <span class='subtype-label'>GI-like regimens</span> 與 HER2 檢測。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Platinum Sensitive", "content": "含鉑救援後，視前線史選 PARPi 維持"}]}
    ],
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "POLEmut (超突變)", "content": "<span class='risk-low'>最佳預後</span>。早期(I-II)可考慮「治療降階」(De-escalation)。"},
            {"title": "MMRd / MSI-H", "content": "免疫敏感。一線趨勢：Chemo + PD-1 (GY018/RUBY)。"},
            {"title": "p53abn (Copy-number high)", "content": "<span class='risk-high'>最差預後</span>。早期亦需升級治療 (EBRT+Chemo)。"},
            {"title": "NSMP (Copy-number low)", "content": "異質性大。ER- (或 High-grade) 屬較高風險子群。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "IO Maintenance", "content": "MMRd/MSI-H 族群延續 IO 維持獲益最大；pMMR 亦見 PFS 改善。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "dMMR / MSI-H", "content": "PD-1 抑制劑單藥 (高反應率)。"},
            {"title": "pMMR / MSS", "content": "Pembrolizumab + Lenvatinib (SoC)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [
            {"title": "Continuous Therapy", "content": "持續 IO 或 Pembro+Lenva 直到疾病進展。"}]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [{"title": "LA / Metastatic", "content": "CCRT 或 Pembro + Chemo ± Bev (CPS≥1)"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Metastatic Maint", "content": "1L 後延續 Pembro 維持"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "2L / 3L Therapy", "content": "Tisotumab vedotin (Tivdak) 或 Cemiplimab"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Tx", "content": "維持當前有效治療"}]}
    ]
}

# --- 2. 深度臨床試驗資料庫 (8 核心 試驗與亞型對位) ---
if 'trials_db' not in st.session_state:
    st.session_state.trials_db = [
        # Ovarian
        {"cancer": "Ovarian", "name": "FRAmework-01 (LY4170156)", "pharma": "Eli Lilly", "drug": "LY4170156 + Bev", "pos": "R-TX", "sub_pos": ["PSOC", "PROC", "MOC 晚期/復發"], 
         "rationale": "標靶 FRα ADC。結合 Bevacizumab 抗血管生成協同作用，解決 PARPi 耐藥後或 MOC 族群之需求。",
         "dosing": {"Exp": "LY4170156 3 mg/kg + Bev 15 mg/kg Q3W", "Control": "TPC / Platinum doublet + Bev"},
         "outcomes": {"ORR": "35-40%", "mPFS": "Primary", "HR": "Phase 3", "CI": "NCT06536348", "AE": "Proteinuria"},
         "inclusion": ["High-grade Serous / Carcinosarcoma / MOC", "FRα Positive", "Part A: PROC, Part B: PSOC"],
         "exclusion": ["曾用過 Topo I ADC", "具有臨床顯著蛋白尿"], "ref": "ClinicalTrials.gov 2026"},
        
        {"cancer": "Ovarian", "name": "REJOICE-Ovarian01", "pharma": "Daiichi Sankyo", "drug": "R-DXd (5.6 mg/kg)", "pos": "R-TX", "sub_pos": ["PROC", "MOC 晚期/復發"], 
         "rationale": "標靶 CDH6 ADC，具強力 Bystander Effect，解決 PROC 腫瘤異質性，MOC 分子亞群亦具備潛力。",
         "dosing": {"Exp": "R-DXd 5.6 mg/kg Q3W", "Control": "TPC"},
         "outcomes": {"ORR": "46.0%", "mPFS": "7.1m", "HR": "Phase 3", "CI": "NCT06161025", "AE": "ILD Risk"},
         "inclusion": ["PROC 卵巢癌", "曾接受 1-4 線", "需曾接受過 Bevacizumab"],
         "exclusion": ["Low-grade 腫瘤", "ILD 病史"], "ref": "JCO 2024"},
        
        {"cancer": "Ovarian", "name": "TroFuse-021 (MK-2870)", "pharma": "MSD", "drug": "Sac-TMT (MK-2870)", "pos": "P-MT", "sub_pos": ["HRD negative / Unknown"], 
         "rationale": "標靶 Trop-2 ADC。結合 Beva 微環境調節，優化 pHRD 族群在一線化療後達到緩解時的維持策略。",
         "dosing": {"Arm 1": "Sac-TMT Mono", "Arm 2": "Sac-TMT + Beva", "Arm 3": "Observation"},
         "outcomes": {"ORR": "Est 40%", "mPFS": "Ongoing", "HR": "Phase 3", "CI": "NCT06241729", "AE": "Diarrhea"},
         "inclusion": ["Stage III/IV 卵巢癌", "pHRD / BRCA WT", "完成一線含鉑化療後達 CR/PR"],
         "exclusion": ["BRCA 突變或 HRD 陽性", "嚴重腸胃病史"], "ref": "ENGOT-ov85"},

        # Endometrial (與分子亞型對應)
        {"cancer": "Endometrial", "name": "MK2870-033", "pharma": "MSD", "drug": "Sac-TMT + Pembro", "pos": "P-MT", "sub_pos": ["IO Maintenance", "MMRd / MSI-H", "pMMR / MSS"], 
         "rationale": "標靶 Trop-2 ADC 協同 PD-1。強化 Chemo-IO 時代應答，特別針對 pMMR/NSMP 族群提升緩解持續性。",
         "dosing": {"Maintenance": "Pembro 400mg + Sac-TMT 5mg/kg Q6W"},
         "outcomes": {"ORR": "Est 35%", "mPFS": "Phase 3", "HR": "TBD", "CI": "NCT06132958", "AE": "貧血, 口腔炎"},
         "inclusion": ["pMMR 子宮內膜癌 (中心實驗室確認)", "FIGO III/IV 一線化療後達 CR/PR"],
         "exclusion": ["子宮肉瘤 (Sarcoma)", "先前用過晚期 IO 治療"], "ref": "ESMO 2025"},
        
        {"cancer": "Endometrial", "name": "GU-US-682-6769", "pharma": "Gilead", "drug": "SG (Trodelvy)", "pos": "R-TX", "sub_pos": ["pMMR / MSS", "p53abn (Copy-number high)"], 
         "rationale": "針對 Trop-2 ADC。釋放 SN-38 載荷引發 DNA 損傷，專攻鉑類與免疫治療進展後之救援。",
         "dosing": {"Exp": "SG 10 mg/kg IV (D1, D8)", "Control": "TPC"},
         "outcomes": {"ORR": "28.5%", "mPFS": "5.6m", "HR": "0.64", "CI": "NCT03964727", "AE": "嗜中性球減少"},
         "inclusion": ["復發性內膜癌 (非肉瘤)", "先前 Platinum + IO 失敗"],
         "exclusion": ["曾用過 Trop-2 ADC", "活動性 CNS 轉移"], "ref": "JCO 2024"},

        {"cancer": "Ovarian", "name": "DS8201-772 (Enhertu)", "pharma": "AstraZeneca", "drug": "T-DXd", "pos": "R-MT", "sub_pos": ["Platinum Sensitive", "MOC 晚期/復發"], 
         "rationale": "標靶 HER2 ADC。超高 DAR (8) 優勢克服 MOC 或 Serous HER2 表現者之異質性。",
         "dosing": {"Mono": "T-DXd 5.4 mg/kg Q3W", "Combo": "T-DXd + Beva"},
         "outcomes": {"ORR": "46.3%", "mPFS": "10.4m", "HR": "0.42", "CI": "95% CI: 0.30-0.58", "AE": "ILD Risk (6%)"},
         "inclusion": ["HER2 IHC 1+/2+/3+", "復發後救援化療達穩定 (Non-PD)"],
         "exclusion": ["ILD 病史", "LVEF < 50%"], "ref": "JCO 2024"},

        # Cervical
        {"cancer": "Cervical", "name": "innovaTV 301", "pharma": "Seagen", "drug": "Tivdak", "pos": "R-TX", "sub_pos": ["2L / 3L Therapy"], 
         "rationale": "標靶 Tissue Factor ADC，解決前線失敗需求。",
         "dosing": {"Exp": "Tivdak 2.0 mg/kg Q3W", "Control": "Chemo"},
         "outcomes": {"ORR": "17.8%", "mPFS": "4.2m", "HR": "0.70", "CI": "NEJM 2024", "AE": "眼表毒性"},
         "inclusion": ["復發性子宮頸癌", "先前 1-2 線進展"],
         "exclusion": ["嚴重眼疾"], "ref": "NEJM 2024"}
    ]

# --- 3. 狀態管理與 AI 媒合 ---
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = st.session_state.trials_db[0]['name']

with st.sidebar:
    st.markdown("<h3 style='color: #6A1B9A;'>🤖 AI 分子亞型媒合助理</h3>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 患者數據媒合分析", expanded=True):
        p_notes = st.text_area("輸入病歷 (含分子標記)", height=300, placeholder="例：62y/o EC, MMRd, FIGO III, s/p Chemo...")
        if st.button("🚀 開始深度分析"):
            if api_key and p_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    prompt = f"分析病歷：{p_notes}。參考這 8 個試驗：{st.session_state.trials_db}。請依據 FIGO 2023 內膜癌亞型或 Ovarian MOC 邏輯，建議適合試驗與理由。"
                    st.write(model.generate_content(prompt).text)
                except Exception as e: st.error(f"AI 異常: {e}")

# --- 4. 主頁面：病程導航 (分子亞型整合版) ---
st.markdown("<div class='main-title'>婦癌臨床試驗導航系統 (FIGO 2023 分子亞型版)</div>", unsafe_allow_html=True)
cancer_type = st.radio("選擇癌症類型", ["Endometrial", "Ovarian", "Cervical"], horizontal=True)

st.subheader("病程階段與分子亞型地圖 (點擊標記查看亮點)")
cols = st.columns(4)
stages_data = guidelines_nested[cancer_type]

for i, stage in enumerate(stages_data):
    with cols[i]:
        st.markdown(f"""<div class='big-stage-card card-{stage['css']}'><div class='big-stage-header header-{stage['css']}'>{stage['header']}</div>""", unsafe_allow_html=True)
        for sub in stage['subs']:
            st.markdown(f"""<div class='sub-block'><div class='sub-block-title'>📘 {sub['title']}</div><div class='sub-block-content'>{sub['content']}</div>""", unsafe_allow_html=True)
            
            # 尋找匹配試驗：檢查 sub_pos 列表是否與標題相關
            relevant_trials = [t for t in st.session_state.trials_db if t["cancer"] == cancer_type and t["pos"] == stage["id"] and any(s in sub["title"] for s in t["sub_pos"])]
            
            if relevant_trials:
                for t in relevant_trials:
                    ukey = f"btn_{t['name']}_{stage['id']}_{sub['title']}"
                    with st.popover(f"📍 {t['pharma']} | {t['name']} | {t['drug']}", use_container_width=True):
                        st.markdown(f"#### ✨ {t['name']} 分子解析")
                        st.info(t['rationale'][:160] + "...")
                        if st.button("📊 開啟深度分析報告", key=ukey):
                            st.session_state.selected_trial = t['name']
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. 深度分析看板 ---
st.divider()
t_options = [t["name"] for t in st.session_state.trials_db if t["cancer"] == cancer_type]
try: curr_idx = t_options.index(st.session_state.selected_trial)
except: curr_idx = 0

if t_options:
    selected_name = st.selectbox("🎯 切換詳細試驗報告：", t_options, index=curr_idx)
    t = next(it for it in st.session_state.trials_db if it["name"] == selected_name)

    st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
    st.markdown(f"<span class='pharma-badge'>{t['pharma']}</span>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #E0E0E0; padding-bottom:15px; font-weight:900;'>📋 {t['name']} 深度分析報告</h2>", unsafe_allow_html=True)

    r1_c1, r1_c2 = st.columns([1.3, 1])
    with r1_c1:
        st.markdown("<div class='info-box-blue' style='background:#E3F2FD; border-left:8px solid #1976D2; padding:15px; border-radius:10px;'><b>💉 Dosing Protocol & Rationale</b></div>", unsafe_allow_html=True)
        st.write(f"**核心藥物:** {t['drug']}")
        for arm, details in t['dosing'].items(): st.write(f"🔹 **{arm}**: {details}")
        st.markdown("---")
        st.success(f"**機轉實證 (Rationale):** {t['rationale']}")
        

    with r1_c2:
        st.markdown("<div class='info-box-gold' style='background:#FFF8E1; border-left:8px solid #FBC02D; padding:15px; border-radius:10px;'><b>📈 Efficacy & Outcomes</b></div>", unsafe_allow_html=True)
        st.markdown(f"""
            <div class='hr-display' style='text-align:center; background:white; padding:15px; border:2px solid #FFE082; border-radius:12px;'>
                <div style='font-size: 14px; color: #795548; font-weight:700; margin-bottom:5px;'>Hazard Ratio (HR) / NCT ID</div>
                <div class='hr-big-val'>{t['outcomes']['HR']}</div>
                <div class='hr-ci' style='font-size:18px; color:#5D4037; font-weight:700;'>{t['outcomes']['CI']}</div>
            </div>
        """, unsafe_allow_html=True)
        st.write(f"**ORR:** {t['outcomes']['ORR']} | **mPFS:** {t['outcomes']['mPFS']}")
        

    st.divider()
    r2_c1, r2_c2 = st.columns(2)
    with r2_c1:
        st.markdown("<div class='info-box-blue' style='background:#E8F5E9; border-left:8px solid #2E7D32; padding:15px; border-radius:10px;'><b>✅ Inclusion Criteria (繁中/En)</b></div>", unsafe_allow_html=True)
        for inc in t['inclusion']: st.write(f"• **{inc}**")
    with r2_c2:
        st.markdown("<div class='info-box-blue' style='background:#FFEBEE; border-left:8px solid #C62828; padding:15px; border-radius:10px;'><b>❌ Exclusion Criteria (繁中/En)</b></div>", unsafe_allow_html=True)
        for exc in t['exclusion']: st.write(f"• **{exc}**")
    st.markdown("</div>", unsafe_allow_html=True)
