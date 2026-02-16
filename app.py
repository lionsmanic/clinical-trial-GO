import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床導航與 AI 決策系統 (FIGO 2023 分子分型版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=Roboto:wght@400;700;900&display=swap');
    
    /* === 全域 UI 緊緻化：壓縮所有留白 === */
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', 'Roboto', sans-serif;
        background-color: #F0F4F7;
        color: #1A1A1A;
        font-size: 19px !important;
        line-height: 1.25;
    }

    .main-title {
        font-size: 38px !important; font-weight: 900; color: #004D40;
        padding: 5px 0 5px 0; border-bottom: 3px solid #4DB6AC;
        margin-bottom: 10px;
    }

    /* === 大階段方塊：極致壓縮設計 === */
    .big-stage-card {
        border-radius: 12px; padding: 0px; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        border: 2px solid transparent;
        background: white; margin-bottom: 5px; overflow: hidden;
        min-height: 750px; /* 增加高度以容納多樣分型 */
    }
    .big-stage-header {
        font-size: 19px !important; font-weight: 900; color: white;
        padding: 6px; text-align: center;
    }

    /* === 子區塊 (Standard of Care & Molecular Subtypes) === */
    .sub-block {
        margin: 4px 6px; padding: 6px;
        border-radius: 8px; background: #F8F9FA;
        border-left: 4px solid #607D8B;
    }
    .sub-block-title {
        font-size: 14px; font-weight: 900; color: #455A64;
        margin-bottom: 2px; border-bottom: 1px solid #CFD8DC; padding-bottom: 1px;
    }
    .sub-block-content {
        font-size: 15px; color: #263238; font-weight: 500; line-height: 1.2;
        margin-bottom: 3px;
    }

    /* 強調標籤 */
    .tag-pole { color: #2E7D32; font-weight: 800; } /* 最佳預後 */
    .tag-mmrd { color: #1565C0; font-weight: 800; } /* 免疫敏感 */
    .tag-p53 { color: #C62828; font-weight: 800; }  /* 最差預後 */
    .tag-nsmp { color: #6A1B9A; font-weight: 800; } /* 異質最大 */

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
        background: white; border-radius: 18px; padding: 30px;
        margin-top: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        border: 1px solid #CFD8DC;
    }
    .hr-big-val { font-family: 'Roboto', sans-serif; font-size: 48px !important; font-weight: 900; color: #D84315; line-height: 1; }
    .pharma-badge { background: #004D40; color: white; padding: 4px 15px; border-radius: 50px; font-size: 13px; font-weight: 700; display: inline-block; margin-bottom: 8px; }

    /* Popover 按鈕：極大化壓縮 */
    .stPopover button { 
        font-weight: 700 !important; font-size: 13px !important; 
        border-radius: 5px !important; background-color: #E0F2F1 !important;
        border: 1px solid #B2DFDB !important;
        margin-top: 1px !important; padding: 0px 5px !important;
        width: 100% !important; text-align: left !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 指引大綱：分子分型與 MOC 路徑 ---
guidelines_nested = {
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "POLEmut (超突變型)", "content": "<span class='tag-pole'>最佳預後。</span> I-II期可考慮「治療降階」(De-escalation)甚至觀察。"},
            {"title": "MMRd / MSI-H", "content": "<span class='tag-mmrd'>免疫敏感。</span> 晚期一線首選：Chemo + PD-1 (GY018/RUBY) → PD-1 維持。"},
            {"title": "p53abn (Copy-number high)", "content": "<span class='tag-p53'>最差預後。</span> 早期亦需治療升級 (EBRT+Chemo)；Serous需驗HER2。"},
            {"title": "NSMP (Copy-number low)", "content": "<span class='tag-nsmp'>異質最大。</span> 治療依病理分層；ER-negative 被視為高風險子群。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "IO Maintenance", "content": "延續一線免疫藥物。MMRd 獲益顯著；pMMR 亦為目前 SoC 趨勢。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "MMRd / MSI-H", "content": "PD-1 抑制劑單藥治療 (高反應率)。"},
            {"title": "pMMR / MSS", "content": "Pembrolizumab + Lenvatinib (SoC)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Tx", "content": "維持有效治療直到 PD。"}]}
    ],
    "Ovarian": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "HGSC / Endometrioid", "content": "Surgery + Carbo/Pacli x6 ± Bev"},
            {"title": "Mucinous (MOC) 鑑別", "content": "CK7+/SATB2- (原發)。<br>1. <span class='subtype-label'>Expansile:</span> 預後佳，早期可保守。<br>2. <span class='subtype-label'>Infiltrative:</span> 高風險，Adjuvant門檻低。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "BRCA mutated", "content": "1. Olaparib 單藥維持<br>2. 曾用Bev且HRD+: Olaparib + Bev"},
            {"title": "HRD positive (wt)", "content": "1. 有用Bev: Olaparib + Bev<br>2. 沒用Bev: Niraparib"},
            {"title": "HRD negative / Unknown", "content": "用過Bev則續用；未用則觀察或視風險選Niraparib"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "PSOC / PROC", "content": "依 PFI 分流。標靶看生物標記 (FRα/HER2)。"},
            {"title": "MOC 晚期/復發", "content": "化療抗性高。優先考量 Trial 或 <span class='subtype-label'>GI-like regimens</span> / Anti-HER2。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Platinum Sensitive", "content": "含鉑救援後 PARPi 維持。"}]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [{"title": "Surgery / CCRT / 1L", "content": "Surgery (早期), CCRT (LA), Pembro+Chemo±Bev (轉移)"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "IO Maintenance", "content": "1L 轉移性後延續 Pembro 維持"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "2L / 3L Therapy", "content": "Tisotumab vedotin (Tivdak) 或 Cemiplimab"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Tx", "content": "維持當前治療直到進展"}]}
    ]
}

# --- 2. 深度臨床試驗資料庫 (8 核心 完整補完) ---
if 'trials_db' not in st.session_state:
    st.session_state.trials_db = [
        # Ovarian
        {"cancer": "Ovarian", "name": "FRAmework-01 (LY4170156)", "pharma": "Eli Lilly", "drug": "LY4170156 + Bevacizumab", "pos": "R-TX", "sub_pos": ["PSOC / PROC", "MOC 晚期/復發"],
         "rationale": "標靶 Folate Receptor alpha (FRα) ADC。聯手 Bevacizumab 利用抗血管生成與藥物遞送之協同效應 (Synergy)，專攻 PARPi 失敗後或 MOC 等化療抗性族群。",
         "dosing": {"Exp": "LY4170156 3mg/kg + Bev 15mg/kg Q3W", "Control": "TPC / Platinum doublet + Bev"},
         "outcomes": {"ORR": "Ph 1/2: ~35-40%", "mPFS": "主要終點 (Primary)", "HR": "Phase 3 進行中", "CI": "NCT06536348", "AE": "Proteinuria, ILD"},
         "inclusion": ["High-grade Serous / Carcinosarcoma / MOC", "FRα Expression Positive", "Part A (PROC), Part B (PSOC)"],
         "exclusion": ["曾用過 Topo I ADC (如 Enhertu)", "ILD病史", "UPCR ≥ 2.0"], "ref": "ClinicalTrials.gov 2026"},
        
        {"cancer": "Ovarian", "name": "REJOICE-Ovarian01", "pharma": "Daiichi Sankyo", "drug": "R-DXd (Raludotatug Deruxtecan)", "pos": "R-TX", "sub_pos": ["PSOC / PROC", "MOC 晚期/復發"],
         "rationale": "標靶 Cadherin-6 (CDH6) ADC。搭載 DXd 載荷並具備強大 Bystander Effect，能克服 PROC 腫瘤的高度異質性，提供後線精準救援。",
         "dosing": {"Exp": "R-DXd 5.6mg/kg IV Q3W", "Control": "TPC (Paclitaxel/PLD/Topotecan)"},
         "outcomes": {"ORR": "46.0%", "mPFS": "7.1m", "HR": "Phase 3", "CI": "NCT06161025", "AE": "ILD Risk, Nausea"},
         "inclusion": ["HG Serous 或 Endometrioid", "Platinum-resistant (PROC)", "需曾接受過 Bevacizumab"],
         "exclusion": ["Low-grade 腫瘤", "Grade ≥2 Neuropathy", "LVEF < 50%"], "ref": "JCO 2024"},
        
        {"cancer": "Ovarian", "name": "TroFuse-021 (MK-2870)", "pharma": "MSD", "drug": "Sac-TMT (MK-2870)", "pos": "P-MT", "sub_pos": ["HRD negative / pHRD"],
         "rationale": "標靶 Trop-2 ADC。結合 Bevacizumab 微環境調節與 ADC 誘導的 ICD 效應，旨在優化 pHRD 族群在一線化療後的維持策略。",
         "dosing": {"Arm 1": "Sac-TMT Mono", "Arm 2": "Sac-TMT + Beva", "Arm 3": "Observation/Beva"},
         "outcomes": {"ORR": "Est 40%", "mPFS": "招募中", "HR": "Phase 3", "CI": "NCT06241729", "AE": "Diarrhea, Anemia"},
         "inclusion": ["FIGO Stage III/IV", "HRD negative (pHRD)", "完成一線化療後達 CR/PR"],
         "exclusion": ["BRCA 突變或 HRD 陽性", "嚴重 IBD 史"], "ref": "ENGOT-ov85"},
        
        {"cancer": "Ovarian", "name": "DS8201-772 (Enhertu)", "pharma": "AstraZeneca", "drug": "T-DXd", "pos": "R-MT", "sub_pos": ["Platinum Sensitive", "MOC 晚期/復發"],
         "rationale": "標靶 HER2 ADC。救援化療穩定後之維持策略。超高 DAR (8) 優勢能有效對抗 HER2 表現者之微小殘留病灶。",
         "dosing": {"Standard": "T-DXd 5.4mg/kg Q3W", "Combo": "T-DXd + Beva"},
         "outcomes": {"ORR": "46.3% (IHC 3+)", "mPFS": "10.4m", "HR": "0.42", "CI": "95% CI: 0.30-0.58", "AE": "ILD Risk (6.2%)"},
         "inclusion": ["HER2 IHC 1+/2+/3+", "PSOC 救援化療達 Non-PD"],
         "exclusion": ["ILD 病史", "先前用過 HER2 ADC"], "ref": "JCO 2024"},

        {"cancer": "Ovarian", "name": "DOVE (APGOT-OV07)", "pharma": "GSK", "drug": "Dostarlimab + Beva", "pos": "R-TX", "sub_pos": ["PSOC / PROC"],
         "rationale": "針對 OCCC (透明細胞癌)。PD-1 + VEGF 雙重阻斷以改善免疫抑制環境，引發長期持續應答。",
         "dosing": {"Combo": "Dostarlimab + Bev Q3W", "Control": "Chemo"},
         "outcomes": {"ORR": "40.2%", "mPFS": "8.2m", "HR": "0.58", "CI": "NCT06023862", "AE": "Hypertension"},
         "inclusion": ["OCCC > 50%", "鉑類抗藥性 (PFI < 12m)"],
         "exclusion": ["先前用過免疫檢查點抑制劑"], "ref": "JCO 2025"},

        # Endometrial
        {"cancer": "Endometrial", "name": "MK2870-033", "pharma": "MSD", "drug": "Sac-TMT + Pembro", "pos": "P-MT", "sub_pos": ["IO Maintenance", "MMRd / MSI-H"],
         "rationale": "標靶 Trop-2 ADC 協同 PD-1。透過 ADC 誘導之免疫原性調節強化 Pembrolizumab 在 pMMR 或 MMRd 族群的應答深度。",
         "dosing": {"Maintenance": "Pembro 400mg + Sac-TMT 5mg/kg Q6W"},
         "outcomes": {"ORR": "Est 35%", "mPFS": "Phase 3 Ongoing", "HR": "TBD", "CI": "NCT06132958", "AE": "Anemia, Stomatitis"},
         "inclusion": ["pMMR 子宮內膜癌 (中心檢測)", "FIGO III/IV 一線化療後達 CR/PR"],
         "exclusion": ["子宮肉瘤 (Sarcoma)", "先前用過晚期 IO 治療"], "ref": "ESMO 2025"},
        
        {"cancer": "Endometrial", "name": "GU-US-682-6769", "pharma": "Gilead", "drug": "SG (Trodelvy)", "pos": "R-TX", "sub_pos": ["pMMR / MSS", "p53abn (Copy-number high)"],
         "rationale": "標靶 Trop-2 ADC。利用 SN-38 強效載荷引發 DNA 損傷，專攻鉑類與免疫治療失敗後之救援，具強大 Bystander Effect。",
         "dosing": {"Exp": "SG 10mg/kg (D1, D8 Q21D)", "Control": "TPC"},
         "outcomes": {"ORR": "28.5%", "mPFS": "5.6m", "HR": "0.64", "CI": "NCT03964727", "AE": "嗜中性球減少"},
         "inclusion": ["復發性 EC (非肉瘤)", "鉑類與 PD-1 失敗後進展"],
         "exclusion": ["先前用過 Trop-2 ADC"], "ref": "JCO 2024"},

        # Cervical
        {"cancer": "Cervical", "name": "innovaTV 301", "pharma": "Seagen", "drug": "Tivdak", "pos": "R-TX", "sub_pos": ["2L / 3L Therapy"],
         "rationale": "標靶 Tissue Factor (TF) ADC。旨在克服後線子宮頸癌之化療耐藥性，改善生存預後。",
         "dosing": {"Exp": "Tivdak 2.0mg/kg Q3W", "Control": "Chemo"},
         "outcomes": {"ORR": "17.8%", "mPFS": "4.2m", "HR": "0.70 (OS)", "CI": "NEJM 2024", "AE": "眼表毒性"},
         "inclusion": ["復發/轉移子宮頸癌", "先前 1–2 線治療後進展"],
         "exclusion": ["嚴重眼疾/角膜炎"], "ref": "NEJM 2024"}
    ]

# --- 3. 側邊欄：AI 分子媒合助里 ---
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = st.session_state.trials_db[0]['name']

with st.sidebar:
    st.markdown("<h3 style='color: #6A1B9A;'>🤖 AI 分子亞型媒合助理</h3>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 患者數據深度分析", expanded=True):
        p_notes = st.text_area("輸入病歷 (含分子標記)", height=250, placeholder="例：62y/o EC, MMRd, FIGO III...")
        if st.button("🚀 開始深度比對"):
            if api_key and p_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    prompt = f"分析病歷：{p_notes}。參考這 8 個試驗：{st.session_state.trials_db}。請依據 FIGO 2023 內膜癌亞型或 MOC 分流邏輯，建議適合試驗與理由。"
                    st.write(model.generate_content(prompt).text)
                except Exception as e: st.error(f"AI 異常: {e}")

# --- 4. 主頁面：緊縮大綱導覽 ---
st.markdown("<div class='main-title'>婦癌臨床試驗導航系統 (FIGO 2023 分子版)</div>", unsafe_allow_html=True)
cancer_type = st.radio("第一步：選擇癌症類型", ["Endometrial", "Ovarian", "Cervical"], horizontal=True)



st.subheader("第二步：點擊標記查看亮點 (對應 SoC 與分子亞型)")
cols = st.columns(4)
stages_data = guidelines_nested[cancer_type]

for i, stage in enumerate(stages_data):
    with cols[i]:
        st.markdown(f"""<div class='big-stage-card card-{stage['css']}'><div class='big-stage-header header-{stage['css']}'>{stage['header']}</div>""", unsafe_allow_html=True)
        for sub in stage['subs']:
            st.markdown(f"""<div class='sub-block'><div class='sub-block-title'>📘 {sub['title']}</div><div class='sub-block-content'>{sub['content']}</div>""", unsafe_allow_html=True)
            relevant_trials = [t for t in st.session_state.trials_db if t["cancer"] == cancer_type and t["pos"] == stage["id"] and any(s in sub["title"] for s in t["sub_pos"])]
            if relevant_trials:
                for t in relevant_trials:
                    ukey = f"btn_{t['name']}_{stage['id']}_{sub['title'].replace(' ', '')}"
                    with st.popover(f"📍 {t['pharma']} | {t['name']} | {t['drug']}", use_container_width=True):
                        st.markdown(f"#### ✨ {t['name']} 重點解析")
                        st.info(f"**Rationale:** {t['rationale'][:150]}...")
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
