import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床導航與 AI 決策系統 (極致緊緻版 - 2026 SoC & Molecular) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=Roboto:wght@400;700;900&display=swap');
    
    /* === 極致緊緻化 CSS：徹底消除留白 === */
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', 'Roboto', sans-serif;
        background-color: #F0F4F7;
        color: #1A1A1A;
        font-size: 19px !important;
        line-height: 1.1; /* 縮減全域行高 */
    }

    .main-title {
        font-size: 32px !important; font-weight: 900; color: #004D40;
        padding: 5px 0; border-bottom: 2px solid #4DB6AC; margin-bottom: 5px;
    }

    /* 大階段方塊：高度隨內容變動，消除頂部留白 */
    .big-stage-card {
        border-radius: 10px; padding: 0px; 
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 2px solid transparent;
        background: white; margin-bottom: 5px; overflow: hidden;
        height: auto; /* 取消固定 min-height */
    }
    .big-stage-header {
        font-size: 17px !important; font-weight: 900; color: white;
        padding: 4px; text-align: center;
    }

    /* 子區塊：極小間距 */
    .sub-block {
        margin: 2px 4px; padding: 4px;
        border-radius: 6px; background: #F1F3F5;
        border-left: 5px solid #607D8B;
    }
    .sub-block-title {
        font-size: 13px; font-weight: 900; color: #455A64;
        margin-bottom: 1px; border-bottom: 1px solid #CFD8DC; padding-bottom: 1px;
    }
    .sub-block-content {
        font-size: 14px; color: #263238; font-weight: 500; line-height: 1.15;
        margin-bottom: 2px;
    }

    /* 分子亞型標籤 */
    .tag-pole { color: #2E7D32; font-weight: 800; }
    .tag-mmrd { color: #1565C0; font-weight: 800; }
    .tag-p53 { color: #C62828; font-weight: 800; }
    .tag-nsmp { color: #6A1B9A; font-weight: 800; }

    /* 階段配色 */
    .card-p-tx { border-color: #43A047; }
    .header-p-tx { background: linear-gradient(135deg, #66BB6A, #43A047); }
    .card-p-mt { border-color: #0288D1; }
    .header-p-mt { background: linear-gradient(135deg, #29B6F6, #0288D1); }
    .card-r-tx { border-color: #FB8C00; }
    .header-r-tx { background: linear-gradient(135deg, #FFB74D, #F57C00); }
    .card-r-mt { border-color: #8E24AA; }
    .header-r-mt { background: linear-gradient(135deg, #BA68C8, #7B1FA2); }

    /* 深度數據區 */
    .detail-section {
        background: white; border-radius: 15px; padding: 20px;
        margin-top: 10px; box-shadow: 0 8px 30px rgba(0,0,0,0.1);
        border: 1px solid #CFD8DC;
    }
    .hr-big-val { font-family: 'Roboto', sans-serif; font-size: 46px !important; font-weight: 900; color: #D84315; }

    /* --- 上色臨床試驗標記按鈕 --- */
    .trial-btn { font-weight: 800 !important; font-size: 12px !important; border-radius: 4px !important; margin-top: 1px !important; padding: 0px 4px !important; width: 100% !important; text-align: left !important; border: 1px solid rgba(0,0,0,0.1) !important; color: white !important; }
    
    /* 藥廠配色邏輯 */
    .stPopover button[aria-label*="Eli Lilly"] { background-color: #E91E63 !important; } /* 禮來：粉紅 */
    .stPopover button[aria-label*="Daiichi Sankyo"] { background-color: #4CAF50 !important; } /* DS：草綠 */
    .stPopover button[aria-label*="MSD"] { background-color: #003366 !important; } /* MSD：深藍 */
    .stPopover button[aria-label*="AstraZeneca"] { background-color: #800080 !important; } /* AZ：紫色 */
    .stPopover button[aria-label*="GSK"] { background-color: #F36D21 !important; } /* GSK：橘色 */
    .stPopover button[aria-label*="Gilead"] { background-color: #00A9E0 !important; } /* Gilead：天藍 */
    .stPopover button[aria-label*="Seagen"] { background-color: #512D6D !important; } /* Seagen：深紫 */
    </style>
    """, unsafe_allow_html=True)

# --- 1. 指引導航數據：NSMP 深度補完 & 分型路徑 ---
guidelines_nested = {
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "POLEmut (超突變型)", "content": "<span class='tag-pole'>最佳預後。</span> I-II期考慮治療降階 (De-escalation)；甚至可考慮單純觀察。"},
            {"title": "MMRd / MSI-H", "content": "<span class='tag-mmrd'>免疫敏感。</span> 一線首選：Chemo + PD-1 (RUBY/GY018) → IO 維持治療。"},
            {"title": "p53abn (Copy-number high)", "content": "<span class='tag-p53'>最差預後。</span> 早期亦需積極輔助治療(化放療)；Serous 需評估 HER2。"},
            {"title": "NSMP (最大宗亞型)", "content": "<span class='tag-nsmp'>No Specific Molecular Profile.</span> 判定流程：IHC MMR Intact、p53 wild-type 且 POLE 定序無致病突變。<br>1. <span class='tag-nsmp'>風險評估:</span> 分類為中間/高風險之關鍵在於 ER 狀態與 Grade。<br>2. <span class='tag-nsmp'>決策重點:</span> NSMP ER-negative (或 Grade 3) 屬較高風險；ER-positive 且病程緩慢者，可考慮荷爾蒙治療(如 Progestin/AI)作為輔助或序列治療方案。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "IO Maintenance", "content": "針對晚期/復發一線化療後，延續使用 Pembro 或 Dostarlimab 持續維持。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "MMRd / MSI-H", "content": "PD-1 抑制劑單藥 (高有效率)；pMMR / NSMP 則考慮 Pembro + Lenvatinib。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Tx", "content": "維持有效治療直到疾病進展 (PD)。"}]}
    ],
    "Ovarian": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "HGSC / Endometrioid", "content": "PDS/IDS 手術 + Carbo/Pacli ± Bevacizumab"},
            {"title": "Mucinous (MOC) 鑑別", "content": "1. <span class='subtype-label'>原發鑑別:</span> CK7+/SATB2-。排除GI轉移。<br>2. <span class='subtype-label'>型態:</span> Expansile (預後佳) vs Infiltrative (高風險)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "BRCA mutated", "content": "Olaparib 單藥或 Olaparib+Bev (若一線已含Bev)"},
            {"title": "HRD positive (wt)", "content": "有用Bev選 Olaparib+Bev；沒用Bev選 Niraparib"},
            {"title": "HRD negative / pHRD", "content": "用過Bev則續用；未用則觀察，視個案風險選Niraparib"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "PSOC / PROC 分流", "content": "依 PFI 判定。標靶檢測看 FRα (Elahere) 或 HER2。"},
            {"title": "MOC 晚期/復發", "content": "化療抗性強。優先 Trial 或 GI-like regimens / Anti-HER2。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Platinum Sensitive", "content": "救援緩解後選 PARPi 維持治療。"}]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [{"title": "Surgery / CCRT / 1L", "content": "Surgery(早期), CCRT(LA), Pembro+Chemo±Bev(轉移)"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "IO Maint", "content": "1L 轉移性後延續 Pembro 維持直到 PD"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "2L / 3L Therapy", "content": "Tivdak (Tisotumab vedotin) 或 Cemiplimab"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Tx", "content": "同一線有效治療持續給藥直到進展"}]}
    ]
}

# --- 2. 深度臨床試驗資料庫 (8 核心) ---
if 'trials_db' not in st.session_state:
    st.session_state.trials_db = [
        {"cancer": "Ovarian", "name": "FRAmework-01 (LY4170156)", "pharma": "Eli Lilly", "drug": "LY4170156 + Bev", "pos": "R-TX", "sub_pos": ["PSOC", "PROC", "MOC 晚期/復發"], 
         "rationale": "標靶 Folate Receptor alpha (FRα) ADC。聯用 Bevacizumab 可產生抗血管生成的協同作用 (Synergy)，專攻 PARPi 耐藥後或 MOC 等化療抗性族群。",
         "dosing": {"Exp": "LY4170156 3mg/kg + Bev 15mg/kg Q3W", "Control": "TPC / Platinum doublet + Bev"},
         "outcomes": {"ORR": "35-40%", "mPFS": "Primary Endpoint", "HR": "Phase 3 Ongoing", "CI": "NCT06536348", "AE": "Proteinuria"},
         "inclusion": ["HG Serous / Carcinosarcoma / MOC", "FRα Expression Positive", "Part A: PROC, Part B: PSOC"],
         "exclusion": ["先前用過 Topo I ADC (如 Enhertu)", "ILD病史", "UPCR ≥ 2.0"], "ref": "ClinicalTrials.gov"},
        
        {"cancer": "Ovarian", "name": "REJOICE-Ovarian01", "pharma": "Daiichi Sankyo", "drug": "R-DXd (5.6 mg/kg)", "pos": "R-TX", "sub_pos": ["PROC", "MOC 晚期/復發"], 
         "rationale": "標靶 Cadherin-6 (CDH6) ADC。搭載強效 DXd 載荷並具備強力 Bystander Effect，能克服 PROC 腫瘤高度異質性，提供後線精準救援。",
         "dosing": {"Exp": "R-DXd 5.6mg/kg IV Q3W", "Control": "TPC"},
         "outcomes": {"ORR": "46.0%", "mPFS": "7.1m", "HR": "Phase 3", "CI": "NCT06161025", "AE": "ILD Risk, Nausea"},
         "inclusion": ["HG Serous / Endometrioid", "Platinum-resistant (PROC)", "需曾接受過 Bevacizumab"],
         "exclusion": ["Low-grade 腫瘤", "Grade ≥2 Neuropathy"], "ref": "JCO 2024"},
        
        {"cancer": "Ovarian", "name": "TroFuse-021 (MK-2870)", "pharma": "MSD", "drug": "Sac-TMT (MK-2870)", "pos": "P-MT", "sub_pos": ["HRD negative / Unknown", "pHRD"], 
         "rationale": "標靶 Trop-2 ADC。透過 ADC 誘導的 ICD 效應協同 Bevacizumab 微環境調節，旨在優化 pHRD 族群在一線化療後的維持策略。",
         "dosing": {"Arm 1": "Sac-TMT Mono", "Arm 2": "Sac-TMT + Beva", "Arm 3": "Observation"},
         "outcomes": {"ORR": "Est 40%", "mPFS": "招募中", "HR": "Phase 3", "CI": "NCT06241729", "AE": "Diarrhea, Anemia"},
         "inclusion": ["FIGO Stage III/IV 卵巢癌", "HRD negative (pHRD) / BRCA WT", "完成一線化療後達 CR/PR"],
         "exclusion": ["BRCA 突變或 HRD 陽性", "先前用過 Trop-2 ADC"], "ref": "ENGOT-ov85"},
        
        {"cancer": "Endometrial", "name": "MK2870-033", "pharma": "MSD", "drug": "Sac-TMT + Pembro", "pos": "P-MT", "sub_pos": ["IO Maintenance", "MMRd / MSI-H", "NSMP"], 
         "rationale": "標靶 Trop-2 ADC 協同 PD-1。透過 ADC 誘導免疫原性調節強化 Pembrolizumab 在 pMMR 或 NSMP 族群的應答深度。",
         "dosing": {"Maintenance": "Pembro 400mg + Sac-TMT 5mg/kg Q6W"},
         "outcomes": {"ORR": "Est 35%", "mPFS": "Phase 3 Ongoing", "HR": "TBD", "CI": "NCT06132958", "AE": "Stomatitis"},
         "inclusion": ["pMMR 子宮內膜癌 (中心檢測)", "FIGO III/IV 一線化療後達 CR/PR"],
         "exclusion": ["先前用過晚期 IO 治療"], "ref": "ESMO 2025"},
        
        {"cancer": "Endometrial", "name": "GU-US-682-6769", "pharma": "Gilead", "drug": "SG (Trodelvy)", "pos": "R-TX", "sub_pos": ["pMMR / NSMP", "p53abn"], 
         "rationale": "針對 Trop-2 ADC。利用 SN-38 載荷引發 DNA 損傷，專攻鉑類與免疫治療失敗後之救援，具強大 Bystander Effect。",
         "dosing": {"Exp": "SG 10mg/kg", "Control": "TPC (Doxo/Taxel)"},
         "outcomes": {"ORR": "28.5%", "mPFS": "5.6m", "HR": "0.64", "CI": "NCT03964727", "AE": "嗜中性球減少"},
         "inclusion": ["復發性 EC (非肉瘤)", "鉑類與 PD-1 失敗後進展"],
         "exclusion": ["曾用過 Trop-2 ADC"], "ref": "JCO 2024"},

        {"cancer": "Ovarian", "name": "DS8201-772 (Enhertu)", "pharma": "AstraZeneca", "drug": "T-DXd", "pos": "R-MT", "sub_pos": ["Platinum Sensitive"], 
         "rationale": "標靶 HER2 ADC。超高 DAR (8) 優勢能有效對抗 HER2 表現者(含 IHC 1+)之微小病灶。",
         "dosing": {"Standard": "T-DXd 5.4mg/kg", "Combo": "T-DXd + Beva"},
         "outcomes": {"ORR": "46.3% (IHC 3+)", "mPFS": "10.4m", "HR": "0.42", "CI": "NCT04482309", "AE": "ILD Risk (6.2%)"},
         "inclusion": ["HER2 IHC 1+/2+/3+", "PSOC 救援化療達 Non-PD"],
         "exclusion": ["ILD 病史", "LVEF < 50%"], "ref": "JCO 2024"},

        {"cancer": "Ovarian", "name": "DOVE", "pharma": "GSK", "drug": "Dostarlimab + Beva", "pos": "R-TX", "sub_pos": ["PROC"], 
         "rationale": "針對 OCCC (透明細胞癌)。PD-1 + VEGF 雙重阻斷改善免疫抑制環境。",
         "dosing": {"Combo": "Dostarlimab + Bev Q3W", "Control": "Chemo"},
         "outcomes": {"ORR": "40.2%", "mPFS": "8.2m", "HR": "0.58", "CI": "NCT06023862", "AE": "Hypertension"},
         "inclusion": ["OCCC > 50%", "鉑類抗藥性 (PFI < 12m)"],
         "exclusion": ["先前用過 PD-1/L1"], "ref": "JCO 2025"},

        {"cancer": "Cervical", "name": "innovaTV 301", "pharma": "Seagen", "drug": "Tivdak", "pos": "R-TX", "sub_pos": ["2L / 3L Therapy"], 
         "rationale": "標靶 Tissue Factor (TF) ADC。旨在克服後線子宮頸癌化療耐藥性。",
         "dosing": {"Exp": "Tivdak 2.0mg/kg Q3W", "Control": "Chemo"},
         "outcomes": {"ORR": "17.8%", "mPFS": "4.2m", "HR": "0.70", "CI": "NEJM 2024", "AE": "眼表毒性"},
         "inclusion": ["復發/轉移子宮頸癌", "先前 1–2 線治療進展"],
         "exclusion": ["嚴重眼疾"], "ref": "NEJM 2024"}
    ]

# --- 3. 狀態管理與 AI 媒合助理 ---
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = st.session_state.trials_db[0]['name']

with st.sidebar:
    st.markdown("<h3 style='color: #6A1B9A;'>🤖 AI 分子亞型媒合助理</h3>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 患者數據深度分析", expanded=True):
        p_notes = st.text_area("輸入病歷 (含分子標記)", height=300, placeholder="例：62y/o EC, NSMP, ER-negative, FIGO III...")
        if st.button("🚀 開始深度比對"):
            if api_key and p_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    prompt = f"分析病歷：{p_notes}。參考這 8 個試驗：{st.session_state.trials_db}。請依據 FIGO 2023 內膜癌亞型(特別是NSMP分層與ER/Grade權重)建議試驗與理由。"
                    st.write(model.generate_content(prompt).text)
                except Exception as e: st.error(f"AI 異常: {e}")

# --- 4. 主頁面：極致緊緻導覽 ---
st.markdown("<div class='main-title'>婦癌臨床試驗導航系統 (FIGO 2023 & Molecular Edition)</div>", unsafe_allow_html=True)
cancer_type = st.radio("第一步：選擇癌症類型", ["Endometrial", "Ovarian", "Cervical"], horizontal=True)

# 分子分型算法圖標籤

st.subheader("第二步：點擊彩色標記查看亮點 (SoC 與試驗對應)")
cols = st.columns(4)
stages_data = guidelines_nested[cancer_type]

for i, stage in enumerate(stages_data):
    with cols[i]:
        # 大階段容器
        st.markdown(f"""<div class='big-stage-card card-{stage['css']}'><div class='big-stage-header header-{stage['css']}'>{stage['header']}</div>""", unsafe_allow_html=True)
        
        # 子區塊內容：緊貼標題
        for sub in stage['subs']:
            st.markdown(f"""<div class='sub-block'><div class='sub-block-title'>📘 {sub['title']}</div><div class='sub-block-content'>{sub['content']}</div>""", unsafe_allow_html=True)
            
            # 尋找匹配試驗：依 sub_pos 與標題關鍵字匹配
            relevant_trials = [t for t in st.session_state.trials_db if t["cancer"] == cancer_type and t["pos"] == stage["id"] and any(s in sub["title"] for s in t["sub_pos"])]
            
            if relevant_trials:
                for t in relevant_trials:
                    # 使用藥廠名作為 aria-label 以觸發 CSS 配色
                    unique_id = f"{t['pharma']} | {t['name']} | {t['drug']}"
                    ukey = f"btn_{t['name']}_{stage['id']}_{sub['title'].replace(' ', '')}"
                    
                    with st.popover(unique_id, use_container_width=True):
                        st.markdown(f"#### ✨ {t['name']} 分子解析")
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
