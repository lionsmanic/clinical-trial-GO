import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床導航與 AI 決策系統 (專業版 - 2026 SoC 精準版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=Roboto:wght@400;700;900&display=swap');
    
    /* === 全域與清晰度優化 === */
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', 'Roboto', sans-serif;
        background-color: #F4F7F9;
        color: #1A1A1A;
        font-size: 21px !important;
        line-height: 1.4;
    }

    .main-title {
        font-size: 42px !important; font-weight: 900; color: #004D40;
        padding: 15px 0 10px 0; border-bottom: 3px solid #4DB6AC;
        margin-bottom: 20px;
    }

    /* === 緊湊大區塊卡片：最小留白設計 === */
    .big-stage-card {
        border-radius: 14px; padding: 0px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.06);
        border: 2px solid transparent;
        background: white;
        margin-bottom: 10px; overflow: hidden;
    }
    .big-stage-header {
        font-size: 22px !important; font-weight: 900; color: white;
        padding: 10px; text-align: center;
    }

    /* === 子區塊 (Standard of Care) === */
    .sub-block {
        margin: 8px; padding: 10px;
        border-radius: 10px; background: #F8F9FA;
        border-left: 5px solid #607D8B;
    }
    .sub-block-title {
        font-size: 16px; font-weight: 900; color: #455A64;
        margin-bottom: 4px; border-bottom: 1px solid #CFD8DC;
        padding-bottom: 2px;
    }
    .sub-block-content {
        font-size: 17px; color: #263238; font-weight: 500; line-height: 1.3;
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

    /* === 深度數據呈現 === */
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

    /* 按鈕樣式強化：緊縮寬度 */
    .stPopover button { 
        font-weight: 700 !important; font-size: 15px !important; 
        border-radius: 6px !important; background-color: #E0F2F1 !important;
        border: 1px solid #B2DFDB !important;
        margin-top: 2px !important; padding: 1px 8px !important;
        width: 100% !important; text-align: left !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 指引大綱架構 (更新 Ovarian Maintenance 邏輯) ---
guidelines_nested = {
    "Ovarian": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "Surgery + Chemo", "content": "PDS 或 NACT/IDS + Carboplatin/Paclitaxel x6 ± Bevacizumab"}
        ]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "BRCA Mutated (變異)", "content": "1. Olaparib 單藥維持 (1L含鉑後CR/PR)<br>2. 一線含Bev且HRD+者：Olaparib + Bev 聯合維持"},
            {"title": "HRD Positive (BRCA wt)", "content": "1. 一線含Bev：Olaparib + Bev 聯合維持<br>2. 一線沒用Bev：Niraparib 單藥維持"},
            {"title": "HRD Negative / Unknown", "content": "前段用Bev則續用Bev；其餘多為觀察或視情況選Niraparib"}
        ]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "PSOC (Platinum Sensitive)", "content": "含鉑複方化療 (Platinum doublet) ± Bevacizumab"},
            {"title": "PROC (Platinum Resistant)", "content": "單藥化療 (Taxel/PLD/Gem) ± Bev 或 Elahere (FRα+)"}
        ]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [
            {"title": "Platinum Sensitive Maint", "content": "對含鉑救援有反應者，若 1L 未用可考慮 PARPi 維持"}
        ]}
    ],
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [{"title": "Advanced / Metastatic", "content": "一線趨勢：Chemo + IO (Pembro/Dostarlimab)"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "IO Maintenance", "content": "延續一線使用的免疫藥物 (Pembro / Dostarlimab) 持續維持"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "pMMR / MSS", "content": "Pembrolizumab + Lenvatinib"}, {"title": "dMMR / MSI-H", "content": "PD-1 抑制劑單藥治療"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "持續性標靶或免疫治療直到進展"}]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [{"title": "LA / Metastatic", "content": "CCRT 或 Pembro + Chemo ± Bevacizumab (CPS≥1)"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Metastatic Maint", "content": "轉移性一線後延續免疫維持治療"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "2L+ Therapy", "content": "Tisotumab vedotin (Tivdak) 或 Cemiplimab / TPC"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Maintenance", "content": "目前以同一線有效治療持續給藥為主"}]}
    ]
}

# --- 2. 臨床試驗數據庫 (8 核心完整保留) ---
if 'trials_db' not in st.session_state:
    st.session_state.trials_db = [
        # Ovarian
        {"cancer": "Ovarian", "name": "FRAmework-01", "pharma": "Eli Lilly", "drug": "LY4170156 + Bev", "pos": "R-TX", "sub_pos": ["PSOC", "PROC"], "summary": "針對 FRα+ 患者。LY4170156 3mg/kg + Bev 15mg/kg Q3W。", "rationale": "標靶 FRα ADC 聯手 Bevacizumab。利用協同效應克服 PARPi 耐藥。", "dosing": {"Exp": "LY4170156 3 mg/kg + Bev 15 mg/kg Q3W", "Control A (PROC)": "TPC or Mirvetuximab", "Control B (PSOC)": "Platinum doublet + Bev"}, "outcomes": {"ORR": "35-40%", "mPFS": "Endpoint", "HR": "Recruiting", "CI": "NCT06536348", "AE": "Proteinuria"}, "inclusion": ["High-grade Serous / Carcinosarcoma", "FRα 陽性", "1-3 線治療史"], "exclusion": ["曾用過 Topo I ADC", "ILD 病史"], "ref": "ClinicalTrials.gov"},
        {"cancer": "Ovarian", "name": "REJOICE-Ovarian01", "pharma": "Daiichi Sankyo", "drug": "R-DXd", "pos": "R-TX", "sub_pos": ["PROC"], "summary": "針對 CDH6 標靶 ADC，專攻 PROC 患者。", "rationale": "標靶 CDH6 ADC。具備強力 Bystander Effect，適合 PROC 後線。", "dosing": {"Exp": "R-DXd 5.6 mg/kg Q3W", "Control": "TPC (Taxel/PLD/Topotecan)"}, "outcomes": {"ORR": "46.0%", "mPFS": "7.1m", "HR": "Phase 3", "CI": "NCT06161025", "AE": "ILD Risk"}, "inclusion": ["PROC 卵巢癌", "曾接受 1-4 線", "需曾用過 Bev"], "exclusion": ["ILD 病史"], "ref": "JCO 2024"},
        {"cancer": "Ovarian", "name": "TroFuse-021", "pharma": "MSD", "drug": "Sac-TMT (MK-2870)", "pos": "P-MT", "sub_pos": ["HRD Negative", "pHRD"], "summary": "針對 pHRD 之 1L 維持。結合 Trop-2 ADC 與 Beva。", "rationale": "Trop-2 ADC 誘導 ICD 協同 Beva 改善微環境，挑戰 SoC。", "dosing": {"Arm 1": "Sac-TMT Mono", "Arm 2": "Sac-TMT + Beva", "Arm 3": "Observation/Beva"}, "outcomes": {"ORR": "Est 40%", "mPFS": "Ongoing", "HR": "Phase 3", "CI": "NCT06241729", "AE": "Diarrhea"}, "inclusion": ["Stage III/IV", "pHRD / BRCA WT"], "exclusion": ["HRD Positive"], "ref": "ENGOT-ov85"},
        {"cancer": "Ovarian", "name": "DS8201-772", "pharma": "AstraZeneca", "drug": "T-DXd", "pos": "R-MT", "sub_pos": ["Platinum Sensitive"], "summary": "針對 HER2 Low 之 PSOC 維持。救援化療後穩定族群首選。", "rationale": "HER2 標靶 ADC。超高 DAR 優勢克服腫瘤異質性。", "dosing": {"Mono": "T-DXd 5.4 mg/kg Q3W", "Combo": "T-DXd + Beva 15 mg/kg Q3W"}, "outcomes": {"ORR": "46.3%", "mPFS": "10.4m", "HR": "0.42", "CI": "95% CI: 0.30-0.58", "AE": "ILD Risk"}, "inclusion": ["HER2 IHC 1+/2+/3+", "Recurr s/p rescue chemo"], "exclusion": ["ILD 病史"], "ref": "JCO 2024"},
        {"cancer": "Ovarian", "name": "DOVE", "pharma": "GSK", "drug": "Dostarlimab + Beva", "pos": "R-TX", "sub_pos": ["PROC"], "summary": "針對 OCCC 透明細胞癌。PD-1 + VEGF 雙重阻斷。", "rationale": "改善 OCCC 免疫抑制微環境。", "dosing": {"Combo": "Dostarlimab + Bev 15mg/kg Q3W", "Control": "Chemo"}, "outcomes": {"ORR": "40.2%", "mPFS": "8.2m", "HR": "0.58", "CI": "NCT06023862", "AE": "Hypertension"}, "inclusion": ["OCCC > 50%", "Platinum-resistant"], "exclusion": ["Prior IO"], "ref": "JCO 2025"},
        # Endometrial
        {"cancer": "Endometrial", "name": "MK2870-033", "pharma": "MSD", "drug": "Sac-TMT + Pembro", "pos": "P-MT", "sub_pos": ["IO Maintenance"], "summary": "一線化療後之維持。針對 pMMR 族群。", "rationale": "結合 Trop-2 ADC 強化 Chemo-IO 時代應答。", "dosing": {"Maintenance": "Pembro 400mg + Sac-TMT 5mg/kg"}, "outcomes": {"ORR": "Est 35%", "mPFS": "Ongoing", "HR": "TBD", "CI": "NCT06132958", "AE": "Anemia"}, "inclusion": ["pMMR Endometrial", "FIGO III/IV"], "exclusion": ["Prior IO for advanced"], "ref": "ESMO 2025"},
        {"cancer": "Endometrial", "name": "GU-US-682-6769", "pharma": "Gilead", "drug": "SG (Trodelvy)", "pos": "R-TX", "sub_pos": ["pMMR / MSS"], "summary": "二/三線復發治療。針對 Trop-2 ADC。", "rationale": "Platinum + IO 失敗後之救援方案。", "dosing": {"Exp": "SG 10 mg/kg IV", "Control": "TPC"}, "outcomes": {"ORR": "28.5%", "mPFS": "5.6m", "HR": "0.64", "CI": "NCT03964727", "AE": "Neutropenia"}, "inclusion": ["復發性 EC", "先前 Platinum + IO 失敗"], "exclusion": ["Prior Trop-2 ADC"], "ref": "JCO 2024"},
        # Cervical
        {"cancer": "Cervical", "name": "innovaTV 301", "pharma": "Seagen", "drug": "Tivdak", "pos": "R-TX", "sub_pos": ["2L / 3L Therapy"], "summary": "針對 2L/3L 復發性子宮頸癌。TF 標靶 ADC。", "rationale": "標靶 Tissue Factor。解決前線失敗需求。", "dosing": {"Exp": "Tivdak 2.0 mg/kg Q3W", "Control": "Chemo"}, "outcomes": {"ORR": "17.8%", "mPFS": "4.2m", "HR": "0.70", "CI": "NEJM 2024", "AE": "Ocular toxicity"}, "inclusion": ["復發性子宮頸癌", "先前 1-2 線進展"], "exclusion": ["嚴重眼疾"], "ref": "NEJM 2024"}
    ]

# --- 3. 狀態管理與側邊欄 ---
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = st.session_state.trials_db[0]['name']

with st.sidebar:
    st.markdown("<h2 style='color: #6A1B9A;'>🤖 AI 專家決策助理</h2>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 患者試驗媒合分析", expanded=True):
        patient_notes = st.text_area("輸入病歷摘要", height=250, placeholder="例：62y/o OCCC, PROC, ECOG 1...")
        if st.button("🚀 開始深度分析"):
            if api_key and patient_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    prompt = f"分析病歷：{patient_notes}。參考試驗數據：{st.session_state.trials_db}。根據指引病程大綱，建議最適合試驗與醫學理由。"
                    st.write(model.generate_content(prompt).text)
                except Exception as e: st.error(f"AI 異常: {e}")

# --- 4. 主頁面：病程導航 ---
st.markdown("<div class='main-title'>婦癌臨床試驗導航系統 (SoC 精準對照版)</div>", unsafe_allow_html=True)
cancer_type = st.radio("選擇癌症類型", ["Ovarian", "Endometrial", "Cervical"], horizontal=True)

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
                    unique_key = f"btn_{t['name']}_{stage['id']}_{sub['title']}"
                    with st.popover(f"📍 {t['pharma']} | {t['name']} | {t['drug']}", use_container_width=True):
                        st.markdown(f"#### ✨ {t['name']} 亮點")
                        st.info(t['summary'])
                        if st.button("📊 開啟分析報告", key=unique_key):
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
