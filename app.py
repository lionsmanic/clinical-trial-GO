import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床導航系統 (2026 最終全功能修復版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=Roboto:wght@400;700;900&display=swap');
    
    /* === 極致緊緻化 UI 與 高對比度標記 === */
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', 'Roboto', sans-serif;
        background-color: #F4F7F9;
        color: #1A1A1A;
        font-size: 19px !important;
        line-height: 1.1;
    }

    .main-title {
        font-size: 32px !important; font-weight: 900; color: #004D40;
        padding: 5px 0; border-bottom: 3px solid #4DB6AC; margin-bottom: 5px;
    }

    /* 大階段方塊：零留白設計，高度隨內容自適應 */
    .big-stage-card {
        border-radius: 10px; padding: 0px; 
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        border: 2px solid transparent;
        background: white; margin-bottom: 4px; overflow: hidden;
        height: auto !important; min-height: 0 !important;
    }
    .big-stage-header {
        font-size: 17px !important; font-weight: 900; color: white;
        padding: 4px; text-align: center; margin: 0 !important;
    }

    /* 子區塊 (SoC)：極小邊距 */
    .sub-block {
        margin: 2px 4px; padding: 4px;
        border-radius: 6px; background: #F8F9FA;
        border-left: 5px solid #546E7A;
    }
    .sub-block-title {
        font-size: 13px; font-weight: 900; color: #37474F;
        margin-bottom: 1px; border-bottom: 1.1px solid #CFD8DC; padding-bottom: 1px;
    }
    .sub-block-content {
        font-size: 14px; color: #263238; font-weight: 500; line-height: 1.15;
        margin-bottom: 2px;
    }

    /* 階段顏色定義 */
    .card-p-tx { border-color: #2E7D32; }
    .header-p-tx { background: linear-gradient(135deg, #43A047, #2E7D32); }
    .card-p-mt { border-color: #1565C0; }
    .header-p-mt { background: linear-gradient(135deg, #1E88E5, #1565C0); }
    .card-r-tx { border-color: #E65100; }
    .header-r-tx { background: linear-gradient(135deg, #FB8C00, #E65100); }
    .card-r-mt { border-color: #6A1B9A; }
    .header-r-mt { background: linear-gradient(135deg, #8E24AA, #6A1B9A); }

    /* --- 試驗按鈕標記：深黑色粗體字、藥廠配色飾邊 --- */
    .stPopover button { 
        font-weight: 900 !important; font-size: 12px !important; 
        border-radius: 4px !important; margin-top: 1px !important;
        padding: 1px 6px !important; width: 100% !important; 
        text-align: left !important; color: #1A1A1A !important; /* 深色字體 */
        border: 1px solid rgba(0,0,0,0.15) !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
    }
    
    /* 藥廠淺色背景對比邏輯 */
    .stPopover button[aria-label*="Eli Lilly"] { background: #FCE4EC !important; border-left: 5px solid #E91E63 !important; } 
    .stPopover button[aria-label*="Daiichi Sankyo"] { background: #E8F5E9 !important; border-left: 5px solid #4CAF50 !important; } 
    .stPopover button[aria-label*="MSD"] { background: #E3F2FD !important; border-left: 5px solid #1976D2 !important; } 
    .stPopover button[aria-label*="AstraZeneca"] { background: #F3E5F5 !important; border-left: 5px solid #8E24AA !important; } 
    .stPopover button[aria-label*="GSK"] { background: #FFF3E0 !important; border-left: 5px solid #F57C00 !important; } 
    .stPopover button[aria-label*="Gilead"] { background: #E1F5FE !important; border-left: 5px solid #03A9F4 !important; } 
    .stPopover button[aria-label*="Seagen"] { background: #EEEEEE !important; border-left: 5px solid #212121 !important; } 

    .detail-section { background: white; border-radius: 15px; padding: 25px; border: 1px solid #CFD8DC; box-shadow: 0 10px 40px rgba(0,0,0,0.05); }
    .hr-big-val { font-family: 'Roboto', sans-serif; font-size: 50px !important; font-weight: 900; color: #D84315; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 指引導航數據：NSMP 深度臨床路徑補完 ---
guidelines_nested = {
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "POLEmut (超突變型)", "content": "預後最佳族群。早期(I-II)建議治療降階 (De-escalation)，可避免放化療之長期毒性。"},
            {"title": "MMRd / MSI-H", "content": "免疫敏感。晚期一線方案：Chemo + PD-1 (RUBY/GY018) 顯著改善 OS，接續 PD-1 維持治療。"},
            {"title": "p53abn (Copy-number high)", "content": "侵襲性最強。早期即需積極升級治療 (化放療併用)；Serous 亞型務必檢測 HER2 評估標靶介入。"},
            {"title": "NSMP (No Specific Molecular Profile)", "content": "<span style='color:#6A1B9A; font-weight:800;'>分子判定：IHC MMR Intact、p53 wt 且 POLE wt。</span><br>1. 分層指標：預後取決於 ER 狀態、Grade 3 與是否存在顯著 LVSI。<br>2. 臨床決策：NSMP ER-negative 屬高風險；ER-positive 且進展慢者可考慮荷爾蒙治療 (Progestin/AI)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "IO Maintenance", "content": "針對晚期/復發一線完成 Chemo-IO 後，延續免疫藥物維持直到進展 (PD)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "MMRd / MSI-H", "content": "PD-1 抑制劑單藥 (Keytruda/Jemperli) 高反應。"}, {"title": "pMMR / NSMP", "content": "標準二線方案：Pembrolizumab + Lenvatinib (SoC)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "維持當前有效方案 (標靶或免疫) 直到進展。"}]}
    ],
    "Ovarian": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "HGSC / Endometrioid", "content": "手術 (PDS/IDS) + Carboplatin/Paclitaxel x6 ± Bevacizumab"},
            {"title": "Mucinous (MOC) 鑑別", "content": "1. 判定：CK7+/SATB2- (原發) 排除GI轉移。 2. 型態：Expansile (預後佳) vs Infiltrative (高復發風險)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "BRCA mutated", "content": "Olaparib 單藥或 Olaparib+Bev (若一線已含Bev)"},
            {"title": "HRD positive (wt)", "content": "優先選用 Olaparib+Bev 或 Niraparib 單藥維持"},
            {"title": "HRD negative / pHRD", "content": "用過 Bev 則續用；未用則觀察，視風險評估用 Niraparib"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "PSOC / PROC 分流", "content": "依 PFI 判定。標靶檢測看 FRα (Elahere) 或 HER2 狀態。"},
            {"title": "MOC 晚期/復發", "content": "化療抗性強。考慮 GI-like 方案、Trial 或抗 HER2 策略。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Platinum Sensitive", "content": "救援緩解後選 PARPi 維持治療。"}]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [{"title": "Surgery / CCRT / 1L", "content": "Surgery(早期), CCRT(LA), Pembro+Chemo±Bev (轉移)"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Metastatic IO Maint", "content": "轉移性一線後延續 Pembro 維持直到 PD"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "2L / 3L Therapy", "content": "Tisotumab vedotin (Tivdak) 或 Cemiplimab"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "同一線有效方案持續給藥直至進展"}]}
    ]
}

# --- 2. 核心試驗資料庫 (8 核心 極量化數據) ---
if 'trials_db' not in st.session_state:
    st.session_state.trials_db = [
        {"cancer": "Ovarian", "name": "FRAmework-01 (LY4170156)", "pharma": "Eli Lilly", "drug": "LY4170156 + Bevacizumab", "pos": "R-TX", "sub_pos": ["PSOC", "PROC", "MOC 晚期/復發"], 
         "rationale": "標靶 FRα ADC，搭載類微管蛋白載荷。聯用 Bevacizumab 可產生血管調節協同作用，提升 ADC 滲透並透過旁觀者效應殺傷異質性腫瘤，專攻 PARPi 耐藥後需求。",
         "dosing": {"Exp Arm": "LY4170156 3mg/kg + Bev 15mg/kg Q3W", "Control A (PROC)": "TPC (Pacli/PLD/Gem/Top) 或 MIRV", "Control B (PSOC)": "Standard Platinum doublet + Bev"},
         "outcomes": {"ORR": "35-40%", "mPFS": "Primary Endpoint", "HR": "Phase 3 Recruiting", "CI": "NCT06536348", "AE": "Proteinuria, Hypertension"},
         "inclusion": ["HG Serous / Carcinosarcoma / MOC", "FRα Expression Positive", "符合 Part A (PROC) 或 Part B (PSOC) PFI 限制"],
         "exclusion": ["先前用過 Topo I ADC", "具有臨床顯著蛋白尿", "活動性 ILD"], "ref": "ClinicalTrials.gov"},
        
        {"cancer": "Ovarian", "name": "REJOICE-Ovarian01", "pharma": "Daiichi Sankyo", "drug": "R-DXd (Raludotatug Deruxtecan)", "pos": "R-TX", "sub_pos": ["PROC"], 
         "rationale": "標靶 CDH6 ADC，搭載強效 DXd 載荷。具備極高 DAR 與強力旁觀者效應，能針對異質性強的 PROC 腫瘤產生顯著殺傷效果，克服前線化療耐藥性。",
         "dosing": {"Exp Arm": "R-DXd 5.6mg/kg IV Q3W", "Control Arm": "Investigator's Choice 單藥化療。"},
         "outcomes": {"ORR": "46.0%", "mPFS": "7.1m", "HR": "Phase 3 Ongoing", "CI": "NCT06161025", "AE": "ILD Risk, Nausea"},
         "inclusion": ["PROC 卵巢癌", "曾接受 1-4 線系統性治療", "需曾用過 Bevacizumab"],
         "exclusion": ["Low-grade 腫瘤", "基線 Grade ≥2 Neuropathy", "LVEF < 50%"], "ref": "JCO 2024"},
        
        {"cancer": "Ovarian", "name": "TroFuse-021 (MK-2870)", "pharma": "MSD", "drug": "Sac-TMT (MK-2870)", "pos": "P-MT", "sub_pos": ["HRD negative / Unknown"], 
         "rationale": "標靶 Trop-2 ADC。結合 Beva 微環境調節與 ADC 誘導的 ICD 效應，旨在優化 pHRD 族群在一線維持時的獲益，填補此族群對 PARPi 反應不足之需求。",
         "dosing": {"Arm 1": "Sac-TMT Mono Q2W/Q3W", "Arm 2": "Sac-TMT + Beva 15mg/kg Q3W", "Arm 3": "Observation / Beva。"},
         "outcomes": {"ORR": "Est 40%", "mPFS": "Ongoing", "HR": "Phase 3", "CI": "NCT06241729", "AE": "口腔炎, 腹瀉"},
         "inclusion": ["FIGO III/IV 卵巢癌", "HRD negative (pHRD) / BRCA WT", "1L含鉑後達 CR/PR"],
         "exclusion": ["BRCA 突變", "先前用過 Trop-2 ADC"], "ref": "ENGOT-ov85"},
        
        {"cancer": "Endometrial", "name": "MK2870-033", "pharma": "MSD", "drug": "Sac-TMT + Pembro", "pos": "P-MT", "sub_pos": ["IO Maintenance", "MMRd", "NSMP"], 
         "rationale": "標靶 Trop-2 ADC 協同 PD-1. 透過免疫調節強化 Pembrolizumab 在 pMMR 或 NSMP 族群的長期應答與持續緩解。",
         "dosing": {"Maintenance Phase": "Pembro 400 mg Q6W + Sac-TMT 5 mg/kg Q6W。"},
         "outcomes": {"ORR": "Est 35% Ph 2", "mPFS": "Phase 3", "HR": "Ongoing", "CI": "NCT06132958", "AE": "貧血, 口腔炎"},
         "inclusion": ["pMMR 子宮內膜癌 (中心檢測)", "FIGO III/IV 一線含鉑+Pembro後達 CR/PR"],
         "exclusion": ["子宮肉瘤", "先前用過晚期系統性 IO 治療"], "ref": "ESMO 2025"},
        
        {"cancer": "Endometrial", "name": "GU-US-682-6769", "pharma": "Gilead", "drug": "SG (Trodelvy)", "pos": "R-TX", "sub_pos": ["pMMR", "p53abn", "NSMP"], 
         "rationale": "標靶 Trop-2 ADC. 利用 SN-38 載荷引發 DNA 損傷，專攻鉑類與免疫進展後之二/三線救援，具備強效旁觀者效應。",
         "dosing": {"Exp": "Sacituzumab Govitecan 10mg/kg (D1, D8 Q21D)", "Control": "TPC (Doxo/Taxel)。"},
         "outcomes": {"ORR": "28.5%", "mPFS": "5.6m", "HR": "0.64", "CI": "NCT03964727", "AE": "Neutropenia"},
         "inclusion": ["復發性 EC (非肉瘤)", "鉑類與 PD-1 失敗後進展"],
         "exclusion": ["先前用過 Trop-2 ADC", "活動性 CNS 轉移"], "ref": "JCO 2024"},

        {"cancer": "Ovarian", "name": "DS8201-772 (Enhertu)", "pharma": "AstraZeneca", "drug": "T-DXd", "pos": "R-MT", "sub_pos": ["Platinum Sensitive"], 
         "rationale": "標靶 HER2 ADC. 救援化療穩定後之精準維持首選。超高 DAR 優勢能有效清除 HER2 表現癌細胞之殘留病灶。",
         "dosing": {"Standard": "T-DXd 5.4mg/kg IV Q3W", "Combo": "T-DXd + Beva 15mg/kg。"},
         "outcomes": {"ORR": "46.3% (IHC 3+)", "mPFS": "10.4m", "HR": "0.42", "CI": "NCT04482309", "AE": "ILD Risk"},
         "inclusion": ["HER2 IHC 1+/2+/3+", "PSOC 救援化療達穩定 (Non-PD)", "LVEF ≥ 50%"],
         "exclusion": ["ILD 肺部病史", "先前接受過 HER2 ADC"], "ref": "JCO 2024"}
    ]

# --- 3. 側邊欄：AI 媒合助理 (修正 404 模型路徑) ---
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = st.session_state.trials_db[0]['name']

with st.sidebar:
    st.markdown("<h3 style='color: #6A1B9A;'>🤖 AI 臨床媒合助理</h3>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 患者數據深度分析", expanded=True):
        p_notes = st.text_area("輸入病歷摘要 (含分子標記)", height=250, placeholder="Example: 62y/o female, OCCC, PROC, FRα+, ECOG 1...")
        if st.button("🚀 開始分析"):
            if api_key and p_notes:
                try:
                    genai.configure(api_key=api_key)
                    # 修正：直接使用 'gemini-1.5-flash' 不帶 models/ 前綴
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"分析病歷：{p_notes}。參考這 8 個試驗：{st.session_state.trials_db}。請依據 FIGO 2023 或 MOC 分流邏輯建議適合試驗與理由。"
                    response = model.generate_content(prompt)
                    st.write(response.text)
                except Exception as e: 
                    st.error(f"AI 異常: {e}")
            else:
                st.warning("請輸入 API Key 與 病歷摘要。")

# --- 4. 主頁面：緊湊導航儀表板 ---
st.markdown("<div class='main-title'>婦癌臨床試驗導航儀表板 (2026 SoC & Molecular)</div>", unsafe_allow_html=True)
cancer_type = st.radio("第一步：選擇癌症類型", ["Endometrial", "Ovarian", "Cervical"], horizontal=True)

st.subheader("第二步：點擊標記查看亮點 (SoC 與試驗對應)")
cols = st.columns(4)
stages_data = guidelines_nested[cancer_type]

for i, stage in enumerate(stages_data):
    with cols[i]:
        # 大階段容器：零餘白
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
        st.markdown("<div style='background:#E3F2FD; border-left:10px solid #1976D2; padding:15px; border-radius:10px;'><b>💉 Dosing Protocol & Rationale</b></div>", unsafe_allow_html=True)
        st.write(f"**核心藥物:** {t['drug']}")
        for arm, details in t['dosing'].items(): st.write(f"🔹 **{arm}**: {details}")
        st.markdown("---")
        st.success(f"**機轉實證 (Rationale):** {t['rationale']}")

    with r2:
        st.markdown("<div style='background:#FFF8E1; border-left:8px solid #FBC02D; padding:15px; border-radius:10px;'><b>📈 Efficacy & Outcomes</b></div>", unsafe_allow_html=True)
        st.markdown(f"""
            <div style='text-align:center; background:white; padding:15px; border:2px solid #FFE082; border-radius:12px;'>
                <div style='font-size: 14px; color: #795548; font-weight:700; margin-bottom:5px;'>Hazard Ratio (HR) / NCT ID</div>
                <div class='hr-big-val'>{t['outcomes']['HR']}</div>
                <div style='font-size:18px; color:#5D4037; font-weight:700;'>{t['outcomes']['CI']}</div>
            </div>
        """, unsafe_allow_html=True)
        st.write(f"**ORR:** {t['outcomes']['ORR']} | **mPFS:** {t['outcomes']['mPFS']}")
        st.error(f"**Safety / AE:** {t['outcomes']['AE']}")

    st.divider()
    r3, r4 = st.columns(2)
    with r3:
        st.markdown("<div style='background:#E8F5E9; border-left:8px solid #2E7D32; padding:15px; border-radius:10px;'><b>✅ Inclusion Criteria (納入標準)</b></div>", unsafe_allow_html=True)
        for inc in t['inclusion']: st.write(f"• **{inc}**")
    with r4:
        st.markdown("<div style='background:#FFEBEE; border-left:8px solid #C62828; padding:15px; border-radius:10px;'><b>❌ Exclusion Criteria (排除標準)</b></div>", unsafe_allow_html=True)
        for exc in t['exclusion']: st.write(f"• **{exc}**")
    st.markdown("</div>", unsafe_allow_html=True)
