import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床導航與 AI 決策系統 (視覺優化與實證數據全補完版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=Roboto:wght@400;700;900&display=swap');
    
    /* === 全域 UI 極致緊緻化 === */
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', 'Roboto', sans-serif;
        background-color: #F4F7F9;
        color: #1A1A1A;
        font-size: 19px !important;
        line-height: 1.1;
    }

    .main-title {
        font-size: 34px !important; font-weight: 900; color: #004D40;
        padding: 5px 0; border-bottom: 3px solid #4DB6AC; margin-bottom: 8px;
    }

    /* 大階段方塊：高度自適應，取消所有留白 */
    .big-stage-card {
        border-radius: 10px; padding: 0px; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border: 2px solid transparent;
        background: white; margin-bottom: 5px; overflow: hidden;
        height: auto !important; min-height: 0 !important;
    }
    .big-stage-header {
        font-size: 18px !important; font-weight: 900; color: white;
        padding: 5px; text-align: center;
    }

    /* 子區塊 (SoC)：縮減間距 */
    .sub-block {
        margin: 2px 4px; padding: 5px;
        border-radius: 6px; background: #F8F9FA;
        border-left: 5px solid #607D8B;
    }
    .sub-block-title {
        font-size: 14px; font-weight: 900; color: #455A64;
        margin-bottom: 1px; border-bottom: 1.5px solid #CFD8DC; padding-bottom: 1px;
    }
    .sub-block-content {
        font-size: 14px; color: #263238; font-weight: 500; line-height: 1.2;
        margin-bottom: 2px;
    }

    /* 階段顏色定義 */
    .card-p-tx { border-color: #2E7D32; }
    .header-p-tx { background: linear-gradient(135deg, #43A047, #2E7D32); }
    .card-p-mt { border-color: #1565C0; }
    .header-p-mt { background: linear-gradient(135deg, #1E88E5, #1565C0); }
    .card-r-tx { border-color: #EF6C00; }
    .header-r-tx { background: linear-gradient(135deg, #FB8C00, #EF6C00); }
    .card-r-mt { border-color: #6A1B9A; }
    .header-r-mt { background: linear-gradient(135deg, #8E24AA, #6A1B9A); }

    /* 亞型標籤配色 */
    .tag-pole { color: #2E7D32; font-weight: 800; }
    .tag-mmrd { color: #1565C0; font-weight: 800; }
    .tag-p53 { color: #C62828; font-weight: 800; }
    .tag-nsmp { color: #6A1B9A; font-weight: 800; }

    /* --- 試驗按鈕標記：藥廠配色與白字加粗 --- */
    .stPopover button { 
        font-weight: 900 !important; font-size: 12px !important; 
        border-radius: 5px !important; margin-top: 2px !important;
        padding: 1px 6px !important; width: 100% !important; 
        text-align: left !important; color: white !important; 
        border: none !important; box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
    }
    
    .stPopover button[aria-label*="Eli Lilly"] { background: #D81B60 !important; } 
    .stPopover button[aria-label*="Daiichi Sankyo"] { background: #43A047 !important; } 
    .stPopover button[aria-label*="MSD"] { background: #002D62 !important; } 
    .stPopover button[aria-label*="AstraZeneca"] { background: #512D6D !important; } 
    .stPopover button[aria-label*="GSK"] { background: #E94E1B !important; } 
    .stPopover button[aria-label*="Gilead"] { background: #00A9E0 !important; } 
    .stPopover button[aria-label*="Seagen"] { background: #000000 !important; } 

    .detail-section {
        background: white; border-radius: 18px; padding: 25px;
        margin-top: 15px; box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        border: 1px solid #CFD8DC;
    }
    .hr-big-val { font-family: 'Roboto', sans-serif; font-size: 50px !important; font-weight: 900; color: #D84315; }
    .pharma-badge { background: #004D40; color: white; padding: 4px 15px; border-radius: 50px; font-size: 13px; font-weight: 700; display: inline-block; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 指引大綱數據庫 (NSMP 深度補完) ---
guidelines_nested = {
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "POLEmut (超突變型)", "content": "<span class='tag-pole'>最佳預後。</span> FIGO 2023 建議早期可考慮降階 (De-escalation)，避免過度治療。"},
            {"title": "MMRd / MSI-H", "content": "<span class='tag-mmrd'>免疫敏感。</span> 晚期一線首選：Chemo + PD-1 (GY018/RUBY) → IO 維持。"},
            {"title": "p53abn (Copy-number high)", "content": "<span class='tag-p53'>最高復發風險。</span> 早期亦需積極輔助化放療；Serous 需評估 HER2。"},
            {"title": "NSMP (最大宗亞型)", "content": "<span class='tag-nsmp'>No Specific Molecular Profile (IHC MMR intact / p53 wt / POLE wt)。</span><br>1. <span class='tag-nsmp'>臨床異質性:</span> 預後介於良好至中等。關鍵風險因子包含 ER 狀態、Grade 3 及顯著 LVSI。<br>2. <span class='tag-nsmp'>決策路徑:</span> NSMP ER-negative 為高風險子群；ER-positive 且病程緩慢者，可考慮荷爾蒙治療 (Progestin/AI) 以減少全身毒性。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "IO Maintenance", "content": "針對 Chemo-IO 一線方案後，延續 Pembro 或 Dostarlimab 維持直到 PD。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "MMRd / MSI-H", "content": "PD-1 抑制劑單藥高反應。"}, {"title": "pMMR / NSMP", "content": "標準二線方案：Pembrolizumab + Lenvatinib (SoC)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Tx", "content": "維持當前有效治療(標靶/免疫)直至進展。"}]}
    ],
    "Ovarian": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "HGSC / Endometrioid", "content": "PDS/IDS 手術 + Carboplatin/Paclitaxel x6 ± Bevacizumab"},
            {"title": "Mucinous (MOC) 鑑別", "content": "1. <span class='subtype-label'>病理:</span> CK7+/SATB2- (原發) 排除 GI 轉移。<br>2. <span class='subtype-label'>型態:</span> Expansile (預後佳) vs Infiltrative (高復發風險)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "BRCA mutated", "content": "Olaparib 單藥或 Olaparib+Bev (若一線已含Bev)"},
            {"title": "HRD positive (wt)", "content": "1. 曾用 Bev: Olaparib + Bev<br>2. 未用 Bev: Niraparib"},
            {"title": "HRD negative / pHRD", "content": "Bev 續用或觀察；視高風險情況選 Niraparib"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "PSOC / PROC 分流", "content": "依 PFI 分流。標靶看生物標記：FRα (Elahere) 或 HER2。"},
            {"title": "MOC 晚期/復發", "content": "化療抗性強。考慮 GI-like、Trial 或 Anti-HER2 策略。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Platinum Sensitive", "content": "救援緩解後選 PARPi 維持治療。"}]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [{"title": "Primary Protocols", "content": "Surgery (早期), CCRT (LA), Pembro+Chemo±Bev (轉移)"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "IO Maint", "content": "1L 轉移性方案後延續 Pembro 維持至 PD"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "2L / 3L Therapy", "content": "Tivdak (Tisotumab vedotin) 或 Cemiplimab"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Tx", "content": "維持當前有效治療直到進展"}]}
    ]
}

# --- 2. 深度臨床試驗資料庫 (8 核心 極大化擴充) ---
if 'trials_db' not in st.session_state:
    st.session_state.trials_db = [
        {"cancer": "Ovarian", "name": "FRAmework-01 (LY4170156)", "pharma": "Eli Lilly", "drug": "LY4170156 + Bevacizumab", "pos": "R-TX", "sub_pos": ["PSOC", "PROC", "MOC 晚期/復發"], 
         "rationale": "標靶 Folate Receptor alpha (FRα) ADC。搭載類微管蛋白載荷。聯用 Bevacizumab 可產生血管重塑協同效應 (Synergy)，提升 ADC 的腫瘤穿透深度，專攻 PARPi 耐藥後或 MOC 族群。",
         "dosing": {
             "Experimental Arm (Part A/B)": "LY4170156 3 mg/kg IV + Bevacizumab 15 mg/kg IV Q3W。",
             "Control (PROC)": "TPC (Pacli/PLD/Gem/Top) 或 MIRV (Elahere)。",
             "Control (PSOC)": "Platinum doublet + Bevacizumab。"
         },
         "outcomes": {"ORR": "Ph 1/2: ~35-40%", "mPFS": "主要終點 (Primary)", "HR": "Phase 3 Recruiting", "CI": "NCT06536348", "AE": "Proteinuria, Hypertension"},
         "inclusion": [
             "18歲以上，病理證實之 HG Serous 或 Carcinosarcoma 之卵巢/輸卵管/原發腹膜癌。",
             "腫瘤檢體經中央實驗室確認為 FRα Expression Positive。",
             "Part A (PROC): 最後一劑鉑類後 90–180 天惡化；曾接受過 1–3 線治療。",
             "Part B (PSOC): 最後一劑鉑類後 >180 天惡化；必須曾用過 PARPi 或不適用者。",
             "充分骨髓、肝腎功能 (ANC ≥1500, Hb ≥9g/dL, CrCl ≥30mL/min)。"
         ],
         "exclusion": [
             "曾用過 Topoisomerase I 抑制劑載荷 ADC (如 DS-8201)。",
             "具有臨床顯著蛋白尿 (24h尿蛋白 ≥2g 或 UPCR ≥2.0)。",
             "曾有非感染性 ILD/肺臟炎病史需類固醇治療者。"
         ], "ref": "ClinicalTrials.gov 2026"},
        
        {"cancer": "Ovarian", "name": "REJOICE-Ovarian01", "pharma": "Daiichi Sankyo", "drug": "R-DXd (Raludotatug Deruxtecan)", "pos": "R-TX", "sub_pos": ["PROC", "MOC 晚期/復發"], 
         "rationale": "標靶 Cadherin-6 (CDH6) ADC。搭載強效 DXd (Topo I inhibitor) 載荷。具備極高 DAR 與強力 Bystander Effect，能克服高度異質性之 PROC 腫瘤。",
         "dosing": {"Exp": "R-DXd 5.6 mg/kg IV Q3W", "Control": "TPC (Paclitaxel/PLD/Topotecan)"},
         "outcomes": {"ORR": "46.0%", "mPFS": "7.1m", "HR": "Phase 3", "CI": "NCT06161025", "AE": "ILD Risk, Nausea"},
         "inclusion": ["HG Serous 或 Endometrioid PROC", "曾接受 1-4 線治療", "需曾用過 Bevacizumab"],
         "exclusion": ["Low-grade 腫瘤", "ILD 病史", "基線 Grade ≥2 周邊神經病變"], "ref": "JCO 2024"},
        
        {"cancer": "Ovarian", "name": "TroFuse-021 (MK-2870)", "pharma": "MSD", "drug": "Sac-TMT (MK-2870)", "pos": "P-MT", "sub_pos": ["HRD negative / Unknown"], 
         "rationale": "標靶 Trop-2 ADC。結合 Beva 微環境調節與 ADC 誘導的 ICD 效應，優化 pHRD 族群在一線化療後的維持策略。",
         "dosing": {"Arm 1": "Sac-TMT Mono Q2W/Q3W", "Arm 2": "Sac-TMT + Beva 15mg/kg", "Arm 3": "Observation/Beva"},
         "outcomes": {"ORR": "Est 40% (pHRD)", "mPFS": "Ongoing", "HR": "Phase 3", "CI": "NCT06241729", "AE": "口腔炎, 腹瀉"},
         "inclusion": ["新診斷 FIGO III/IV", "HRD negative (pHRD) / BRCA WT", "1L含鉑後達 CR/PR"],
         "exclusion": ["BRCA 突變或 HRD 陽性", "嚴重腸胃病史 (IBD)"], "ref": "ENGOT-ov85"},
        
        {"cancer": "Endometrial", "name": "MK2870-033", "pharma": "MSD", "drug": "Sac-TMT + Pembro", "pos": "P-MT", "sub_pos": ["IO Maintenance", "MMRd / MSI-H", "NSMP"], 
         "rationale": "標靶 Trop-2 ADC 協同 PD-1 抑制劑。強化 Pembrolizumab 在 pMMR 或 NSMP 族群的應答深度。",
         "dosing": {"Induction": "Carbo+Pacli+Pembro Q3W", "Maintenance": "Pembro 400mg + Sac-TMT 5mg/kg Q6W"},
         "outcomes": {"ORR": "Est 35%", "mPFS": "Phase 3", "HR": "TBD", "CI": "NCT06132958", "AE": "貧血, 口腔炎"},
         "inclusion": ["pMMR 子宮內膜癌", "FIGO III/IV 一線含鉑後達 CR/PR"],
         "exclusion": ["先前接受過任何晚期 IO 治療"], "ref": "ESMO 2025"},
        
        {"cancer": "Endometrial", "name": "GU-US-682-6769", "pharma": "Gilead", "drug": "SG (Trodelvy)", "pos": "R-TX", "sub_pos": ["pMMR / NSMP", "p53abn"], 
         "rationale": "標靶 Trop-2 ADC。利用 SN-38 強效載荷引發 DNA 損傷，專攻鉑類與免疫進展後之救援。",
         "dosing": {"Exp": "SG 10mg/kg (D1, D8 Q21D)", "Control": "TPC (Doxo/Taxel)"},
         "outcomes": {"ORR": "28.5%", "mPFS": "5.6m", "HR": "0.64", "CI": "NCT03964727", "AE": "嗜中性球減少"},
         "inclusion": ["復發性 EC (非肉瘤)", "鉑類與 PD-1 失敗後進展"],
         "exclusion": ["曾用過 Trop-2 ADC"], "ref": "JCO 2024"},

        {"cancer": "Ovarian", "name": "DS8201-772 (Enhertu)", "pharma": "AstraZeneca", "drug": "T-DXd", "pos": "R-MT", "sub_pos": ["Platinum Sensitive"], 
         "rationale": "標靶 HER2 ADC。救援化療穩定後之維持首選。超高 DAR (8) 優勢能有效對抗 HER2 表現者。",
         "dosing": {"Standard": "T-DXd 5.4mg/kg IV Q3W", "Combo": "T-DXd + Beva 15mg/kg"},
         "outcomes": {"ORR": "46.3% (IHC 3+)", "mPFS": "10.4m", "HR": "0.42", "CI": "NCT04482309", "AE": "ILD Risk (6.2%)"},
         "inclusion": ["HER2 IHC 1+/2+/3+", "PSOC 救援化療達 Non-PD", "LVEF ≥ 50%"],
         "exclusion": ["ILD 肺臟炎病史"], "ref": "JCO 2024"},

        {"cancer": "Ovarian", "name": "DOVE", "pharma": "GSK", "drug": "Dostarlimab + Beva", "pos": "R-TX", "sub_pos": ["PROC"], 
         "rationale": "針對 OCCC (透明細胞癌)。PD-1 + VEGF 雙重阻斷改善微環境。",
         "dosing": {"Combo": "Dostarlimab + Bev Q3W", "Control": "Chemo (Gem/PLD/Taxel)"},
         "outcomes": {"ORR": "40.2%", "mPFS": "8.2m", "HR": "0.58", "CI": "NCT06023862", "AE": "高血壓"},
         "inclusion": ["組織學 OCCC > 50%", "鉑類抗藥性 (PFI < 12m)"],
         "exclusion": ["先前用過免疫治療"], "ref": "JCO 2025"},

        {"cancer": "Cervical", "name": "innovaTV 301", "pharma": "Seagen", "drug": "Tivdak", "pos": "R-TX", "sub_pos": ["2L / 3L Therapy"], 
         "rationale": "標靶 Tissue Factor ADC。旨在克服後線子宮頸癌化療耐藥性。",
         "dosing": {"Exp": "Tivdak 2.0mg/kg Q3W", "Control": "Chemo (TPC)"},
         "outcomes": {"ORR": "17.8%", "mPFS": "4.2m", "HR": "0.70", "CI": "NEJM 2024", "AE": "眼表毒性"},
         "inclusion": ["復發/轉移子宮頸癌", "先前 1–2 線治療後進展"],
         "exclusion": ["嚴重眼疾"], "ref": "NEJM 2024"}
    ]

# --- 3. 側邊欄：AI 媒合 ---
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = st.session_state.trials_db[0]['name']

with st.sidebar:
    st.markdown("<h3 style='color: #6A1B9A;'>🤖 AI 臨床媒合助理</h3>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 患者數據深度分析", expanded=True):
        p_notes = st.text_area("輸入病歷 (含分子標記)", height=250, placeholder="例：62y/o EC, NSMP, ER-negative, FIGO III...")
        if st.button("🚀 開始深度分析"):
            if api_key and p_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    prompt = f"分析病歷：{p_notes}。參考這 8 個試驗：{st.session_state.trials_db}。請依據 FIGO 2023 內膜癌亞型或 MOC 分流邏輯建議試驗與理由。"
                    st.write(model.generate_content(prompt).text)
                except Exception as e: st.error(f"AI 異常: {e}")

# --- 4. 主頁面：緊湊導航 ---
st.markdown("<div class='main-title'>婦癌臨床試驗導航儀表板 (FIGO 2023 專業版)</div>", unsafe_allow_html=True)
cancer_type = st.radio("第一步：選擇癌症類型", ["Endometrial", "Ovarian", "Cervical"], horizontal=True)

st.subheader("第二步：點擊彩色標記查看亮點 (SoC 與試驗對應)")
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
                    label = f"{t['pharma']} | {t['name']} | {t['drug']}"
                    ukey = f"btn_{t['name']}_{stage['id']}_{sub['title'].replace(' ', '')}"
                    with st.popover(label, use_container_width=True):
                        st.markdown(f"#### ✨ {t['name']} 臨床解析")
                        st.info(f"**Rationale:** {t['rationale'][:160]}...")
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
    st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #E0E0E0; padding-bottom:10px; font-weight:900;'>📋 {t['name']} 深度分析報告</h2>", unsafe_allow_html=True)

    r1, r2 = st.columns([1.3, 1])
    with r1:
        st.markdown("<div class='info-box-blue' style='background:#E3F2FD; border-left:10px solid #1976D2; padding:15px; border-radius:10px;'><b>💉 Dosing Protocol & Rationale</b></div>", unsafe_allow_html=True)
        st.write(f"**核心藥物:** {t['drug']}")
        for arm, details in t['dosing'].items(): st.write(f"🔹 **{arm}**: {details}")
        st.markdown("---")
        st.success(f"**機轉實證 (Rationale):** {t['rationale']}")

    with r2:
        st.markdown("<div class='info-box-gold' style='background:#FFF8E1; border-left:10px solid #FBC02D; padding:15px; border-radius:10px;'><b>📈 Efficacy & Outcomes</b></div>", unsafe_allow_html=True)
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
    r3, r4 = st.columns(2)
    with r3:
        st.markdown("<div class='info-box-blue' style='background:#E8F5E9; border-left:8px solid #2E7D32; padding:15px; border-radius:10px;'><b>✅ Inclusion Criteria (納入標準)</b></div>", unsafe_allow_html=True)
        for inc in t['inclusion']: st.write(f"• **{inc}**")
    with r4:
        st.markdown("<div class='info-box-blue' style='background:#FFEBEE; border-left:8px solid #C62828; padding:15px; border-radius:10px;'><b>❌ Exclusion Criteria (排除標準)</b></div>", unsafe_allow_html=True)
        for exc in t['exclusion']: st.write(f"• **{exc}**")
    st.markdown("</div>", unsafe_allow_html=True)
