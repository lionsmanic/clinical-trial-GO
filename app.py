import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床導航系統 (高效率巢狀區塊版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=Roboto:wght@400;700;900&display=swap');
    
    /* === 全域設定 === */
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', 'Roboto', sans-serif;
        background-color: #F4F7F9;
        color: #1A1A1A;
        font-size: 21px !important;
    }

    .main-title {
        font-size: 44px !important; font-weight: 900; color: #004D40;
        padding: 20px 0 10px 0; border-bottom: 5px solid #4DB6AC;
        margin-bottom: 25px;
    }

    /* === 大區塊卡片：緊湊設計 === */
    .big-stage-card {
        border-radius: 18px; padding: 0px; /* 內部由 header 與內容撐開 */
        box-shadow: 0 8px 25px rgba(0,0,0,0.07);
        border: 2px solid transparent;
        min-height: 450px; background: white;
        margin-bottom: 20px; overflow: hidden;
    }
    .big-stage-header {
        font-size: 24px !important; font-weight: 900; color: white;
        padding: 15px; text-align: center;
    }

    /* === 次級子區塊 (Sub-Blocks) === */
    .sub-block {
        margin: 12px; padding: 15px;
        border-radius: 12px; background: #F8F9FA;
        border-left: 6px solid #607D8B;
    }
    .sub-block-title {
        font-size: 17px; font-weight: 900; color: #455A64;
        margin-bottom: 8px; border-bottom: 1px solid #CFD8DC;
        padding-bottom: 4px;
    }
    .sub-block-content {
        font-size: 18px; color: #263238; font-weight: 500; line-height: 1.4;
        margin-bottom: 10px;
    }

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
        font-family: 'Roboto', sans-serif; font-size: 52px !important; 
        font-weight: 900; color: #D84315; line-height: 1;
    }
    .pharma-badge { 
        background: #004D40; color: white; padding: 6px 18px; 
        border-radius: 50px; font-size: 14px; font-weight: 700;
        display: inline-block; margin-bottom: 12px;
    }

    /* 試驗標記按鈕 */
    .stPopover button { 
        font-weight: 700 !important; font-size: 16px !important; 
        border-radius: 8px !important; background-color: #E0F2F1 !important;
        border: 1px solid #B2DFDB !important;
        margin-top: 5px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 指引次級大綱 (包含 PROC/PSOC 分流) ---
guidelines_nested = {
    "Ovarian": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "Surgery + Chemo", "content": "初始減積手術 (PDS) 或 NACT/IDS + Carboplatin/Paclitaxel x6 ± Bevacizumab"}
        ]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "BRCA Mutated", "content": "PARP inhibitor (Olaparib/Niraparib) 維持治療"},
            {"title": "HRD Positive", "content": "PARPi 或 Olaparib + Bevacizumab 聯合維持"},
            {"title": "HRD Negative/pHRD", "content": "Bevacizumab 維持或觀察 (Observation)"}
        ]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "PSOC (PFI > 6m)", "content": "含鉑複方化療 (Platinum doublet) ± Bevacizumab"},
            {"title": "PROC (PFI < 6m)", "content": "單藥化療 (Weekly Taxel/PLD/Gem) ± Bev 或 Elahere (FRα+)"}
        ]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [
            {"title": "Platinum Sensitive", "content": "對含鉑治療有反應者，若前線未用可考慮 PARPi 維持"}
        ]}
    ],
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "Advanced/Recurrent", "content": "Chemo + Immunotherapy (Pembro/Dostarlimab)"}
        ]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "IO Maintenance", "content": "延續一線使用的免疫藥物 (IO) 維持治療直到進展"}
        ]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "dMMR / MSI-H", "content": "PD-1 抑制劑單藥治療"},
            {"title": "pMMR / MSS", "content": "Pembrolizumab + Lenvatinib"}
        ]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [
            {"title": "Continuous Tx", "content": "持續性治療 (如 Pembro+Lenva) 直到不可耐受或進展"}
        ]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "Locally Advanced", "content": "CCRT (Cisplatin + Brachytherapy)"},
            {"title": "Metastatic", "content": "Pembrolizumab + Chemo ± Bevacizumab (CPS≥1)"}
        ]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "IO Maintenance", "content": "Metastatic 一線後延續 Pembro 維持"}
        ]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "2L / 3L Therapy", "content": "Tisotumab vedotin (Tivdak) 或 Cemiplimab / TPC"}
        ]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [
            {"title": "Maintenance", "content": "目前以持續同一線有效治療為主"}
        ]}
    ]
}

# --- 2. 臨床試驗資料庫 (8 核心，已更新次分區標記) ---
if 'trials_db' not in st.session_state:
    st.session_state.trials_db = [
        # Ovarian
        {"cancer": "Ovarian", "name": "FRAmework-01 (LY4170156)", "pharma": "Eli Lilly", "drug": "LY4170156 + Bev", "pos": "R-TX", "sub_pos": "PROC / PSOC", "summary": "針對 FRα+ 患者。Part A (PROC) 與 Part B (PSOC)。", "rationale": "葉酸受體 alpha (FRα) 標靶 ADC 聯手 Bevacizumab。利用協同效應克服 PARPi 耐藥。", "dosing": {"Experimental": "LY4170156 3 mg/kg + Bev 15 mg/kg Q3W", "Control A (PROC)": "TPC (Paclitaxel/PLD/Gem/Top) 或 Mirvetuximab", "Control B (PSOC)": "Platinum doublet + Bev"}, "outcomes": {"ORR": "35-40%", "mPFS": "主要終點", "HR": "Phase 3 進行中", "CI": "NCT06536348", "AE": "Proteinuria, ILD"}, "inclusion": ["High-grade Serous / Carcinosarcoma", "FRα 陽性", "1-3 線治療史"], "exclusion": ["曾用過 Topo I ADC (如 DS-8201)", "ILD 病史"], "ref": "NCT06536348"},
        {"cancer": "Ovarian", "name": "REJOICE-Ovarian01", "pharma": "Daiichi Sankyo", "drug": "R-DXd", "pos": "R-TX", "sub_pos": "PROC", "summary": "針對 CDH6 標靶 ADC，專攻 PROC 患者。", "rationale": "標靶 CDH6 ADC。具備強力 Bystander Effect，適合 PROC 後線。", "dosing": {"Experimental": "R-DXd 5.6 mg/kg Q3W", "Control": "TPC (Taxel/PLD/Topotecan)"}, "outcomes": {"ORR": "46.0%", "mPFS": "7.1m", "HR": "Phase 3", "CI": "NCT06161025", "AE": "ILD Risk"}, "inclusion": ["PROC 卵巢癌", "曾接受 1-4 線", "需曾用過 Bev"], "exclusion": ["ILD 病史", "LVEF < 50%"], "ref": "JCO 2024"},
        {"cancer": "Ovarian", "name": "TroFuse-021", "pharma": "MSD", "drug": "Sac-TMT (MK-2870)", "pos": "P-MT", "sub_pos": "HRD Negative/pHRD", "summary": "針對 pHRD 患者之 1L 維持。結合 Trop-2 ADC 與 Beva。", "rationale": " Trop-2 ADC 誘導 ICD 協同 Beva 改善微環境，挑戰現有 SoC。", "dosing": {"Arm 1": "Sac-TMT Mono", "Arm 2": "Sac-TMT + Beva", "Arm 3": "Observation/Beva"}, "outcomes": {"ORR": "Est 40%", "mPFS": "Ongoing", "HR": "Phase 3", "CI": "NCT06241729", "AE": "Diarrhea"}, "inclusion": ["FIGO Stage III/IV", "pHRD / BRCA WT", "1L Chemo CR/PR"], "exclusion": ["HRD Positive", "嚴重腸胃病史"], "ref": "ENGOT-ov85"},
        {"cancer": "Ovarian", "name": "DS8201-772", "pharma": "AstraZeneca", "drug": "Enhertu (T-DXd)", "pos": "R-MT", "sub_pos": "Platinum Sensitive", "summary": "針對 HER2 Low 之 PSOC 維持治療。", "rationale": "HER2 標靶 ADC。救援化療後 Non-PD 族群之維持首選。", "dosing": {"Mono": "T-DXd 5.4 mg/kg Q3W", "Combo": "T-DXd + Beva 15 mg/kg Q3W"}, "outcomes": {"ORR": "46.3%", "mPFS": "10.4m", "HR": "0.42", "CI": "95% CI: 0.30-0.58", "AE": "ILD Risk"}, "inclusion": ["HER2 IHC 1+/2+/3+", "Recurr s/p rescue chemo"], "exclusion": ["ILD 病史"], "ref": "JCO 2024"},
        {"cancer": "Ovarian", "name": "DOVE", "pharma": "GSK", "drug": "Dostarlimab + Beva", "pos": "R-TX", "sub_pos": "PROC", "summary": "針對 OCCC 透明細胞癌。PD-1 + VEGF 雙重阻斷。", "rationale": "改善 OCCC 免疫抑制微環境。", "dosing": {"Combo": "Dostarlimab + Bev 15mg/kg Q3W", "Control": "Chemo"}, "outcomes": {"ORR": "40.2%", "mPFS": "8.2m", "HR": "0.58", "CI": "NCT06023862", "AE": "Hypertension"}, "inclusion": ["OCCC > 50%", "Platinum-resistant"], "exclusion": ["Prior IO"], "ref": "JCO 2025"},
        # Endometrial
        {"cancer": "Endometrial", "name": "MK2870-033", "pharma": "MSD", "drug": "Sac-TMT + Pembro", "pos": "P-MT", "sub_pos": "IO Maintenance", "summary": "一線化療合併免疫後之維持 (pMMR)。", "rationale": "結合 Trop-2 ADC 強化 Chemo-IO 時代的應答。", "dosing": {"Maintenance": "Pembro 400mg + Sac-TMT 5mg/kg Q6W"}, "outcomes": {"ORR": "Est 35%", "mPFS": "Ongoing", "HR": "TBD", "CI": "NCT06132958", "AE": "Stomatitis"}, "inclusion": ["pMMR EC", "FIGO III/IV", "1L CR/PR"], "exclusion": ["Prior IO for advanced"], "ref": "ESMO 2025"},
        {"cancer": "Endometrial", "name": "GU-US-682-6769", "pharma": "Gilead", "drug": "SG (Trodelvy)", "pos": "R-TX", "sub_pos": "pMMR / MSS", "summary": "二/三線復發治療。針對 Trop-2 ADC。", "rationale": "Platinum + IO 失敗後之救援方案。", "dosing": {"Exp": "SG 10 mg/kg IV", "Control": "TPC"}, "outcomes": {"ORR": "28.5%", "mPFS": "5.6m", "HR": "0.64", "CI": "NCT03964727", "AE": "Neutropenia"}, "inclusion": ["Recurrent EC", "Prior Platinum + IO"], "exclusion": ["Prior Trop-2 ADC"], "ref": "JCO 2024"},
        # Cervical
        {"cancer": "Cervical", "name": "innovaTV 301", "pharma": "Seagen", "drug": "Tivdak (Tisotumab)", "pos": "R-TX", "sub_pos": "2L / 3L Therapy", "summary": "針對 2L/3L 復發性子宮頸癌。TF 標靶 ADC。", "rationale": "標靶 Tissue Factor。解決前線失敗需求。", "dosing": {"Exp": "Tivdak 2.0 mg/kg Q3W", "Control": "Chemo"}, "outcomes": {"ORR": "17.8%", "mPFS": "4.2m", "HR": "0.70", "CI": "NEJM 2024", "AE": "Ocular toxicity"}, "inclusion": ["Recurr/Metastatic Cervical", "Prior 1-2 lines"], "exclusion": ["Severe ocular disease"], "ref": "NEJM 2024"}
    ]

# --- 3. 狀態同步 ---
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = st.session_state.trials_db[0]['name']

# --- 4. 主頁面：巢狀大綱導覽 ---
st.markdown("<div class='main-title'>婦癌臨床試驗導航系統 (2026 SoC 整合版)</div>", unsafe_allow_html=True)
cancer_type = st.radio("第一步：選擇癌症類型", ["Ovarian", "Endometrial", "Cervical"], horizontal=True)

st.subheader("第二步：病程階段與試驗對照地圖 (點擊標記查看亮點)")
cols = st.columns(4)

stages_data = guidelines_nested[cancer_type]

for i, stage in enumerate(stages_data):
    with cols[i]:
        # 大方塊容器
        st.markdown(f"""<div class='big-stage-card card-{stage['css']}'><div class='big-stage-header header-{stage['css']}'>{stage['header']}</div>""", unsafe_allow_html=True)
        
        # 遍歷子區塊 (Standard of Care)
        for sub in stage['subs']:
            st.markdown(f"""<div class='sub-block'><div class='sub-block-title'>📘 {sub['title']}</div><div class='sub-block-content'>{sub['content']}</div>""", unsafe_allow_html=True)
            
            # 尋找屬於該子區塊名稱或大分類的試驗
            # 匹配邏輯：如果 trial 的 sub_pos 包含在 sub 標題中，就放進去
            relevant_trials = [t for t in st.session_state.trials_db if t["cancer"] == cancer_type and t["pos"] == stage["id"] and (t["sub_pos"] in sub["title"] or sub["title"] in t["sub_pos"])]
            
            if relevant_trials:
                for t in relevant_trials:
                    # 📍 藥廠 | 代碼 | 藥物配方
                    btn_label = f"📍 {t['pharma']} | {t['name']} | {t['drug']}"
                    with st.popover(btn_label, use_container_width=True):
                        st.markdown(f"#### ✨ {t['name']} 亮點摘要")
                        st.write(f"**藥物:** {t['drug']}")
                        st.info(t['summary'])
                        if st.button("📊 開啟分析報告", key=f"go_{t['name']}"):
                            st.session_state.selected_trial = t['name']
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. 深度分析報告看板 (高清晰版) ---
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
