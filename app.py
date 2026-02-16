import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床導航與 AI 決策系統 (2026 專家實證數據全補完版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=Roboto:wght@400;700;900&display=swap');
    
    /* === 全域 UI 緊緻化設定 === */
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', 'Roboto', sans-serif;
        background-color: #F0F4F7;
        color: #1A1A1A;
        font-size: 20px !important;
        line-height: 1.3;
    }

    .main-title {
        font-size: 40px !important; font-weight: 900; color: #004D40;
        padding: 10px 0 5px 0; border-bottom: 4px solid #4DB6AC;
        margin-bottom: 15px;
    }

    /* === 大階段方塊：移除冗餘留白 === */
    .big-stage-card {
        border-radius: 14px; padding: 0px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.06);
        border: 2px solid transparent;
        background: white; margin-bottom: 8px; overflow: hidden;
    }
    .big-stage-header {
        font-size: 20px !important; font-weight: 900; color: white;
        padding: 8px; text-align: center;
    }

    /* === 子區塊 (Standard of Care) === */
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

    /* 階段配色 */
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
        margin-top: 25px; box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        border: 1px solid #CFD8DC;
    }
    .hr-big-val {
        font-family: 'Roboto', sans-serif; font-size: 50px !important; 
        font-weight: 900; color: #D84315; line-height: 1;
    }
    .pharma-badge { 
        background: #004D40; color: white; padding: 5px 16px; 
        border-radius: 50px; font-size: 13px; font-weight: 700;
        display: inline-block; margin-bottom: 10px;
    }

    /* 試驗按鈕緊縮 */
    .stPopover button { 
        font-weight: 700 !important; font-size: 14px !important; 
        border-radius: 6px !important; background-color: #E0F2F1 !important;
        border: 1px solid #B2DFDB !important;
        margin-top: 2px !important; padding: 1px 6px !important;
        width: 100% !important; text-align: left !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 指引大綱架構 (精準對應臨床共識) ---
guidelines_nested = {
    "Ovarian": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "Surgery + Chemo", "content": "PDS 或 NACT/IDS + Carboplatin/Paclitaxel x6 ± Bevacizumab"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "BRCA mutated", "content": "1. Olaparib 單藥維持 (1L後CR/PR)<br>2. 曾用Bev且HRD+: Olaparib + Bev 聯合維持"},
            {"title": "HRD positive (BRCA wt)", "content": "1. 曾用Bev: Olaparib + Bev 聯合維持<br>2. 未用Bev: Niraparib 單藥維持"},
            {"title": "HRD negative / Unknown", "content": "曾用Bev者續用Bev直到進展；未用者多為觀察，或視風險評估選用 Niraparib"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "PSOC (Platinum Sensitive)", "content": "含鉑複方化療 (Platinum doublet) ± Bevacizumab"},
            {"title": "PROC (Platinum Resistant)", "content": "單藥化療 (Weekly Taxel/PLD/Gem) ± Bev 或 Elahere (FRα+)"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [
            {"title": "Platinum Sensitive Maint", "content": "對含鉑救援反應後，視前線用藥史選用 PARPi 維持治療"}]}
    ],
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [{"title": "Advanced / Metastatic", "content": "標準方案：Carbo/Pacli + IO (Pembro/Dostarlimab)"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "IO Maintenance", "content": "延續一線使用之免疫藥物持續維持至疾病進展 (PD)"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "pMMR / MSS", "content": "Pembrolizumab + Lenvatinib"}, {"title": "dMMR / MSI-H", "content": "PD-1 抑制劑單藥 (如 Pembro)"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Tx", "content": "維持當前有效治療直到進展"}]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [{"title": "CCRT / Metastatic", "content": "CCRT 或 Pembro + Chemo ± Bevacizumab"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Metastatic Maint", "content": "轉移性一線後延續 Pembro 維持治療"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "2L / 3L Therapy", "content": "Tivdak (Tisotumab vedotin) 或 Cemiplimab / TPC"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Tx", "content": "維持當前有效治療直到進展"}]}
    ]
}

# --- 2. 深度臨床試驗資料庫 (8 核心 深度數據增強) ---
if 'trials_db' not in st.session_state:
    st.session_state.trials_db = [
        # Ovarian
        {"cancer": "Ovarian", "name": "FRAmework-01 (LY4170156)", "pharma": "Eli Lilly (禮來)", "drug": "LY4170156 + Bevacizumab", "pos": "R-TX", "sub_pos": ["PSOC", "PROC"],
         "rationale": "標靶 Folate Receptor alpha (FRα) ADC。搭載類微管蛋白載荷 (Payload)，利用 ADC 精準傳遞與 Bevacizumab 抗血管生成的協同作用，旨在克服 PARPi 耐藥後患者之需求，特別針對 FRα 陽性族群。",
         "dosing": {"Experimental": "LY4170156 3 mg/kg + Bev 15 mg/kg Q3W", "Control A (PROC)": "TPC or Mirvetuximab (MIRV)", "Control B (PSOC)": "Platinum doublet + Bev"},
         "outcomes": {"ORR": "Ph 1/2: ~35-40%", "mPFS": "主要終點 (Primary)", "HR": "Phase 3 進行中", "CI": "NCT06536348", "AE": "Proteinuria, Hypertension"},
         "inclusion": ["High-grade Serous / Carcinosarcoma", "FRα Expression Positive (Central Lab)", "Part A: PROC (復發≤6m)", "Part B: PSOC (復發>6m) 且須曾用過 PARPi", "ECOG 0-1"],
         "exclusion": ["曾用過 Topo I ADC (如 DS-8201)", "ILD/肺臟炎病史", "顯著蛋白尿 (UPCR ≥2.0)"], "ref": "ClinicalTrials.gov 2026"},
        
        {"cancer": "Ovarian", "name": "REJOICE-Ovarian01", "pharma": "Daiichi Sankyo (DS)", "drug": "R-DXd (Raludotatug Deruxtecan)", "pos": "R-TX", "sub_pos": ["PROC"],
         "rationale": "標靶 Cadherin-6 (CDH6) ADC，搭載 DXd 載荷。具備極高 DAR 與強力 Bystander Effect，可克服 PROC 腫瘤的高度異質性，提供後線救援。",
         "dosing": {"Experimental": "R-DXd 5.6 mg/kg IV Q3W", "Control": "TPC (Paclitaxel/PLD/Topotecan)"},
         "outcomes": {"ORR": "46.0% (Update)", "mPFS": "7.1m", "HR": "Phase 3", "CI": "NCT06161025", "AE": "ILD Risk, Nausea"},
         "inclusion": ["HG Serous 或 Endometrioid 卵巢癌", "Platinum-resistant (PROC)", "曾接受 1-4 線治療", "需曾接受過 Bevacizumab"],
         "exclusion": ["Low-grade 腫瘤", "ILD 病史", "LVEF < 50%", "Grade ≥2 周邊神經病變"], "ref": "JCO 2024"},
        
        {"cancer": "Ovarian", "name": "TroFuse-021 (MK-2870)", "pharma": "MSD (Merck)", "drug": "Sac-TMT (MK-2870)", "pos": "P-MT", "sub_pos": ["HRD negative / Unknown"],
         "rationale": "標靶 Trop-2 ADC。結合 Bevacizumab 的微環境調節，旨在優化 pHRD 族群在一線化療後達到緩解時的維持策略，填補 PARPi 獲益不足的缺口。",
         "dosing": {"Arm 1": "Sac-TMT Mono", "Arm 2": "Sac-TMT + Beva 15mg/kg", "Arm 3": "Observation/Beva"},
         "outcomes": {"ORR": "Est 40%", "mPFS": "招募中", "HR": "Phase 3", "CI": "NCT06241729", "AE": "Diarrhea, Anemia"},
         "inclusion": ["FIGO Stage III/IV 卵巢癌", "HRD negative (pHRD) / BRCA WT", "完成一線含鉑化療後達 CR/PR", "具備 Trop-2 表達樣品"],
         "exclusion": ["BRCA 突變或 HRD 陽性", "嚴重腸胃病史/IBD", "先前用過 Trop-2 ADC"], "ref": "ENGOT-ov85"},
        
        {"cancer": "Ovarian", "name": "DOVE (APGOT-OV07)", "pharma": "GSK", "drug": "Dostarlimab + Beva", "pos": "R-TX", "sub_pos": ["PROC"],
         "rationale": "針對透明細胞癌 (OCCC) 的免疫抑制環境。利用 PD-1 阻斷與 VEGF 抑制之雙重打擊，恢復 T 細胞浸潤並誘發應答。",
         "dosing": {"Experimental": "Dostarlimab + Bev 15mg/kg Q3W", "Control": "Chemo (Gem/PLD/Taxel)"},
         "outcomes": {"ORR": "40.2% (OCCC)", "mPFS": "8.2m", "HR": "0.58", "CI": "NCT06023862", "AE": "Hypertension"},
         "inclusion": ["組織學 OCCC > 50%", "鉑類抗藥性 (PFI < 12m)", "先前線數 ≤ 5 線", "可測量病灶"],
         "exclusion": ["先前接受過任何免疫檢查點抑制劑", "臨床顯著腸阻塞病史"], "ref": "JCO 2025"},
        
        {"cancer": "Ovarian", "name": "DS8201-772 (Enhertu)", "pharma": "AstraZeneca", "drug": "Trastuzumab Deruxtecan", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"],
         "rationale": "標靶 HER2 ADC。救援化療穩定後之精準維持策略。透過 ADC 的強效載荷延長疾病緩解，特別針對 HER2 表現者。",
         "dosing": {"Standard": "T-DXd 5.4 mg/kg Q3W", "Combination": "T-DXd + Beva 15 mg/kg Q3W"},
         "outcomes": {"ORR": "46.3% (IHC 3+)", "mPFS": "10.4m", "HR": "0.42", "CI": "95% CI: 0.30-0.58", "AE": "ILD Risk (6%)"},
         "inclusion": ["HER2 IHC 1+/2+/3+", "PSOC 復發後救援化療達穩定 (Non-PD)", "LVEF ≥ 50%"],
         "exclusion": ["曾患有需類固醇治療之 ILD/肺臟炎", "先前接受過 HER2 ADC"], "ref": "JCO 2024"},

        # Endometrial
        {"cancer": "Endometrial", "name": "MK2870-033", "pharma": "MSD", "drug": "Sac-TMT + Pembro", "pos": "P-MT", "sub_pos": ["IO Maintenance"],
         "rationale": "標靶 Trop-2 ADC 協同 PD-1 抑制劑。利用 ADC 誘導之免疫原性調節強化 Pembrolizumab 在 pMMR 族群的長期應答。",
         "dosing": {"Maintenance": "Pembrolizumab 400mg + Sac-TMT 5mg/kg Q6W"},
         "outcomes": {"ORR": "Est 35%", "mPFS": "Phase 3 Ongoing", "HR": "TBD", "CI": "NCT06132958", "AE": "Anemia, Stomatitis"},
         "inclusion": ["pMMR 子宮內膜癌 (中心實驗室確認)", "FIGO III/IV 一線含鉑化療後達 CR/PR", "ECOG 0-1"],
         "exclusion": ["子宮肉瘤 (Sarcoma)", "先前接受過針對晚期病灶之 IO 治療"], "ref": "ESMO 2025"},
        
        {"cancer": "Endometrial", "name": "GU-US-682-6769", "pharma": "Gilead", "drug": "SG (Trodelvy)", "pos": "R-TX", "sub_pos": ["pMMR / MSS"],
         "rationale": "標靶 Trop-2 ADC。釋放 SN-38 載荷引發 DNA 損傷，專攻鉑類與免疫治療進展後之救援，具備強大旁觀者效應。",
         "dosing": {"Exp": "SG 10 mg/kg IV (D1, D8 Q21D)", "Control": "TPC (Doxo/Taxel)"},
         "outcomes": {"ORR": "28.5%", "mPFS": "5.6m", "HR": "0.64", "CI": "NCT03964727", "AE": "Neutropenia, Diarrhea"},
         "inclusion": ["復發性/進展性內膜癌 (非肉瘤)", "鉑類與 PD-1/L1 失敗後進展", "充分器官功能"],
         "exclusion": ["先前曾用過 Trop-2 ADC", "活動性 CNS 轉移", "IBD 病史"], "ref": "JCO 2024"},

        # Cervical
        {"cancer": "Cervical", "name": "innovaTV 301", "pharma": "Seagen/Genmab", "drug": "Tivdak", "pos": "R-TX", "sub_pos": ["2L / 3L Therapy"],
         "rationale": "標靶 Tissue Factor (TF) ADC。搭載 MMAE 載荷，旨在克服後線子宮頸癌化療耐藥性，改善生存預後。",
         "dosing": {"Exp": "Tisotumab vedotin 2.0 mg/kg Q3W", "Control": "Chemotherapy (TPC)"},
         "outcomes": {"ORR": "17.8%", "mPFS": "4.2m", "HR": "0.70 (OS)", "CI": "95% CI: 0.54-0.89", "AE": "眼表毒性, 神經病變"},
         "inclusion": ["復發性/轉移性子宮頸癌", "先前接受過 1–2 線治療後進展", "可測量病灶"],
         "exclusion": ["嚴重眼疾/角膜炎", "先前用過 TF 標靶藥物", "活動性出血傾向"], "ref": "NEJM 2024"}
    ]

# --- 3. 側邊欄：AI 媒合判定 ---
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = st.session_state.trials_db[0]['name']

with st.sidebar:
    st.markdown("<h3 style='color: #6A1B9A;'>🤖 AI 專家決策助理</h3>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 患者條件深度媒合分析", expanded=True):
        patient_notes = st.text_area("輸入病歷摘要", height=300, placeholder="Paste clinical notes here...")
        if st.button("🚀 開始臨床分析"):
            if api_key and patient_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    prompt = f"分析病歷：{patient_notes}。請與這 8 個試驗數據進行交叉比對：{st.session_state.trials_db}。請依據指引大綱判定階段，建議適合試驗並詳細說明醫學理由。"
                    st.write(model.generate_content(prompt).text)
                except Exception as e: st.error(f"AI 異常: {e}")

# --- 4. 主頁面：病程大綱導覽 ---
st.markdown("<div class='main-title'>婦癌臨床試驗導航系統 (SoC 精準整合版)</div>", unsafe_allow_html=True)
cancer_type = st.radio("第一步：選擇癌症類型", ["Ovarian", "Endometrial", "Cervical"], horizontal=True)



st.subheader("第二步：點擊下方標記查看亮點 (對應指引 SoC 子區塊)")
cols = st.columns(4)
stages_data = guidelines_nested[cancer_type]

for i, stage in enumerate(stages_data):
    with cols[i]:
        st.markdown(f"""<div class='big-stage-card card-{stage['css']}'><div class='big-stage-header header-{stage['css']}'>{stage['header']}</div>""", unsafe_allow_html=True)
        for sub in stage['subs']:
            st.markdown(f"""<div class='sub-block'><div class='sub-block-title'>📘 {sub['title']}</div><div class='sub-block-content'>{sub['content']}</div>""", unsafe_allow_html=True)
            
            # 匹配邏輯：搜尋該階段與子標題關聯的試驗
            relevant_trials = [t for t in st.session_state.trials_db if t["cancer"] == cancer_type and t["pos"] == stage["id"] and any(s in sub["title"] for s in t["sub_pos"])]
            
            if relevant_trials:
                for t in relevant_trials:
                    ukey = f"btn_{t['name']}_{stage['id']}_{sub['title']}"
                    with st.popover(f"📍 {t['pharma']} | {t['name']} | {t['drug']}", use_container_width=True):
                        st.markdown(f"#### ✨ {t['name']} 重點解析")
                        st.info(f"**Rationale:** {t['rationale'][:150]}...")
                        if st.button("📊 開啟深度分析報告", key=ukey):
                            st.session_state.selected_trial = t['name']
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. 深度分析報告看板 ---
st.divider()
t_options = [t["name"] for t in st.session_state.trials_db if t["cancer"] == cancer_type]
try: curr_idx = t_options.index(st.session_state.selected_trial)
except: curr_idx = 0

if t_options:
    selected_name = st.selectbox("🎯 切換詳細試驗報告：", t_options, index=curr_idx)
    t = next(it for it in st.session_state.trials_db if it["name"] == selected_name)

    st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
    st.markdown(f"<span class='pharma-badge'>Pharma: {t['pharma']}</span>", unsafe_allow_html=True)
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
        st.error(f"**Safety / AE:** {t['outcomes']['AE']}")
        

    st.divider()
    r2_c1, r2_c2 = st.columns(2)
    with r2_c1:
        st.markdown("<div class='info-box-blue' style='background:#E8F5E9; border-left:8px solid #2E7D32; padding:15px; border-radius:10px;'><b>✅ Inclusion Criteria (納入標準)</b></div>", unsafe_allow_html=True)
        for inc in t['inclusion']: st.write(f"• **{inc}**")
    with r2_c2:
        st.markdown("<div class='info-box-blue' style='background:#FFEBEE; border-left:8px solid #C62828; padding:15px; border-radius:10px;'><b>❌ Exclusion Criteria (排除標準)</b></div>", unsafe_allow_html=True)
        for exc in t['exclusion']: st.write(f"• **{exc}**")
    st.markdown("</div>", unsafe_allow_html=True)
