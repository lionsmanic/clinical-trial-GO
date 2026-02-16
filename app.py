import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床導航與實證圖書館 (2026 最終全方位整合版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=Roboto:wght@400;700;900&display=swap');
    
    /* === 極致緊緻化 UI === */
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

    /* 大階段方塊：高度隨內容撐開，零留白 */
    .big-stage-card {
        border-radius: 10px; padding: 0px; 
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        border: 2px solid transparent; background: white; 
        margin-bottom: 4px; overflow: hidden; height: auto !important;
    }
    .big-stage-header {
        font-size: 17px !important; font-weight: 900; color: white;
        padding: 5px; text-align: center;
    }

    /* 子區塊 (SoC 與 分子亞型) */
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
    }

    /* 階段配色 */
    .card-p-tx { border-color: #2E7D32; }
    .header-p-tx { background: linear-gradient(135deg, #43A047, #2E7D32); }
    .card-p-mt { border-color: #1565C0; }
    .header-p-mt { background: linear-gradient(135deg, #1E88E5, #1565C0); }
    .card-r-tx { border-color: #E65100; }
    .header-r-tx { background: linear-gradient(135deg, #FB8C00, #E65100); }
    .card-r-mt { border-color: #6A1B9A; }
    .header-r-mt { background: linear-gradient(135deg, #8E24AA, #6A1B9A); }

    /* --- 標記按鈕樣式：深黑色加粗 (#1A1A1A) --- */
    .stPopover button { 
        font-weight: 900 !important; font-size: 12px !important; 
        border-radius: 4px !important; margin-top: 1px !important;
        padding: 1px 6px !important; width: 100% !important; 
        text-align: left !important; color: #1A1A1A !important; 
        border: 1px solid rgba(0,0,0,0.15) !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
    }
    
    /* 📚 里程碑實證背景 */
    .stPopover button[aria-label*="📚"] { background: #ECEFF1 !important; border-left: 5px solid #455A64 !important; }

    /* 📍 招募中試驗藥廠配色飾邊 */
    .stPopover button[aria-label*="Eli Lilly"] { background: #FCE4EC !important; border-left: 5px solid #E91E63 !important; } 
    .stPopover button[aria-label*="Daiichi Sankyo"] { background: #E8F5E9 !important; border-left: 5px solid #4CAF50 !important; } 
    .stPopover button[aria-label*="MSD"] { background: #E3F2FD !important; border-left: 5px solid #1976D2 !important; } 
    .stPopover button[aria-label*="AstraZeneca"] { background: #F3E5F5 !important; border-left: 5px solid #8E24AA !important; } 
    .stPopover button[aria-label*="GSK"] { background: #FFF3E0 !important; border-left: 5px solid #F57C00 !important; } 
    .stPopover button[aria-label*="Gilead"] { background: #E1F5FE !important; border-left: 5px solid #03A9F4 !important; } 
    .stPopover button[aria-label*="Seagen"] { background: #EEEEEE !important; border-left: 5px solid #212121 !important; } 

    .detail-section { background: white; border-radius: 18px; padding: 25px; border: 1px solid #CFD8DC; box-shadow: 0 10px 40px rgba(0,0,0,0.05); }
    .hr-big-val { font-family: 'Roboto', sans-serif; font-size: 48px !important; font-weight: 900; color: #D84315; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 里程碑實證資料庫 (📚 Milestone Library - 完整對應您提供的表格) ---
milestone_db = [
    # 子宮內膜癌
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H"], "name": "📚 RUBY (Dostarlimab)", "drug": "Dostarlimab + CP", "summary": "一線晚期/復發。dMMR PFS 獲益極顯著；全體亦有獲益，推動一線 Immuno-chemo 標準。"},
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H", "NSMP / pMMR"], "name": "📚 NRG-GY018 (Pembro)", "drug": "Pembrolizumab + CP", "summary": "一線晚期/復發。dMMR 大幅改善；pMMR 亦顯著改善 PFS，擴大一線適用面。"},
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H", "NSMP / pMMR"], "name": "📚 DUO-E", "drug": "Durvalumab ± Olaparib", "summary": "一線。Durva 併入與(或)加 PARPi 維持可改善 PFS，建立「免疫/維持」策略。"},
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H"], "name": "📚 AtTEnd", "drug": "Atezolizumab + CP", "summary": "一線晚期。整體 PFS 改善，dMMR 獲益更明顯，支持 PD-(L)1 併化療證據鏈。"},
    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["NSMP / pMMR"], "name": "📚 KEYNOTE-775", "drug": "Lenvatinib + Pembro", "summary": "二線(曾含鉑)。PFS/OS 均優於化療；pMMR/MSS 後線關鍵組合(需重視毒性)。"},
    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["MMRd / MSI-H"], "name": "📚 GARNET", "drug": "Dostarlimab (Mono)", "summary": "多線後。dMMR/MSI-H 反應較佳，奠定後線免疫單藥地位。"},

    # 子宮頸癌
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Locally Advanced (CCRT)"], "name": "📚 KEYNOTE-A18", "drug": "Pembrolizumab + CCRT", "summary": "局部晚期。OS/PFS 顯著改善：免疫正式併入根治性 CCRT 的新標準。"},
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Locally Advanced (CCRT)"], "name": "📚 INTERLACE", "drug": "Induction Carbo/Pacli", "summary": "局部晚期。先 6週誘導化療再 CCRT，5年 OS/PFS 改善，現成化療可快速落地。"},
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Locally Advanced (CCRT)"], "name": "📚 CALLA (陰性)", "drug": "Durvalumab + CCRT", "summary": "局部晚期。整體未達顯著改善：提醒需更精準族群分流。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["1L Recurrent"], "name": "📚 KEYNOTE-826", "drug": "Pembro + Chemo ± Bev", "summary": "R/M 一線。OS 持續改善：R/M 一線 Immuno-chemo (常併 Bev) 核心試驗。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["1L Recurrent"], "name": "📚 BEATcc", "drug": "Atezolizumab + Chemo + Bev", "summary": "R/M 一線。PFS/OS 皆改善：提供另一個一線免疫加成方案。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["2L / 3L Therapy"], "name": "📚 EMPOWER-Cx1", "drug": "Cemiplimab", "summary": "二線。OS 改善：後線免疫單藥的關鍵證據。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["2L / 3L Therapy"], "name": "📚 innovaTV 301", "drug": "Tisotumab Vedotin (ADC)", "summary": "二/三線。OS/PFS/ORR 改善：ADC 進入後線標準選項。"},

    # 卵巢癌
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutated"], "name": "📚 SOLO-1", "drug": "Olaparib", "summary": "一線維持。PFS 里程碑級提升：BRCA 族群一線維持核心標準。"},
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive (wt)", "HRD negative / pHRD"], "name": "📚 PRIMA", "drug": "Niraparib", "summary": "一線維持。整體 PFS 改善，HRD 最大：支持不限 BRCA 一線維持。"},
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive (wt)"], "name": "📚 PAOLA-1", "drug": "Olaparib + Bev", "summary": "一線維持(含Bev基礎)。HRD+ 獲益最大：確立 PARPi + anti-VEGF 維持路徑。"},
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive (wt)"], "name": "📚 DUO-O", "drug": "Durva+Chemo+Bev", "summary": "一線。組合維持顯示 PFS 改善：免疫需組合 PARPi/VEGF 較具潛力。"},
    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], "name": "📚 NOVA / ARIEL3", "drug": "Niraparib / Rucaparib", "summary": "復發維持。多分層族群 PFS 顯著改善：復發維持重要基石。"},
    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], "name": "📚 SOLO2", "drug": "Olaparib", "summary": "復發維持。BRCA 族群長期 OS 重要臨床效益。"},
    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PROC (Resistant)"], "name": "📚 MIRASOL", "drug": "Mirvetuximab (FRα ADC)", "summary": "後線(鉑類抗藥)。PFS/OS/ORR 改善：卵巢癌後線重大新武器。"},
    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 van Driel HIPEC", "drug": "Surgery + HIPEC", "summary": "NACT 後 IDS。RFS/OS 改善，特定情境下改變實務。"},
    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 LION Trial", "drug": "No LN Dissection", "summary": "初治手術。臨床 LN 陰性者，淋巴清掃無存活獲益且併發症增多。"},
    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["Platinum Sensitive"], "name": "📚 DESKTOP III", "drug": "Secondary Surgery", "summary": "復發手術。嚴選 AGO Score 患者二次手術可改善 OS。"}
]

# --- 2. 進行中臨床試驗資料庫 (📍 Ongoing - 完整救回並詳盡擴充) ---
ongoing_trials = [
    {"cancer": "Ovarian", "name": "FRAmework-01 (LY4170156)", "pharma": "Eli Lilly", "drug": "LY4170156 + Bevacizumab", "pos": "R-TX", "sub_pos": ["PROC (Resistant)", "Platinum Sensitive"], 
     "rationale": "標靶 FRα ADC，搭載類微管蛋白載荷。聯用 Bevacizumab 可產生血管重塑協同作用 (Synergy)，提升 ADC 滲透並透過旁觀者效應殺傷異質性腫瘤。",
     "inclusion": ["HG Serous 卵巢癌。", "經檢測確認 FRα 表達陽性。", "Part A: PROC (復發≤6m)。", "Part B: PSOC (復發>6m) 且曾用過 PARPi。"],
     "exclusion": ["曾用過 Topo I ADC (如 Enhertu)。", "具有臨床顯著蛋白尿。", "活動性 ILD 病史。"], "ref": "NCT06536348"},
    
    {"cancer": "Ovarian", "name": "REJOICE-Ovarian01", "pharma": "Daiichi Sankyo", "drug": "R-DXd", "pos": "R-TX", "sub_pos": ["PROC (Resistant)"], 
     "rationale": "標靶 Cadherin-6 (CDH6) ADC，搭載 DXd 載荷。具備極高 DAR (8) 與強力旁觀者效應，專攻高度異質性 PROC。",
     "inclusion": ["HG Serous 或 Endometrioid PROC。", "先前接受 1-4 線系統治療。", "需曾用過 Bevacizumab。"],
     "exclusion": ["Low-grade 腫瘤。", "LVEF < 50%。"], "ref": "JCO 2024"},
    
    {"cancer": "Ovarian", "name": "TroFuse-021", "pharma": "MSD", "drug": "Sac-TMT (MK-2870)", "pos": "P-MT", "sub_pos": ["HRD negative / pHRD"], 
     "rationale": "標靶 Trop-2 ADC。結合 Beva 微環境調節，優化 pHRD 族群在一線維持時獲益。",
     "inclusion": ["FIGO Stage III/IV 卵巢癌。", "HRD 狀態確認為陰性且 BRCA 為野生型。", "一線含鉑化療後達 CR 或 PR。"],
     "exclusion": ["BRCA 突變。", "先前用過 Trop-2 ADC。"], "ref": "ENGOT-ov85"},

    {"cancer": "Ovarian", "name": "DS8201-772 (Enhertu)", "pharma": "AstraZeneca", "drug": "T-DXd", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], 
     "rationale": "標靶 HER2 ADC。超高 DAR 優勢清除 HER2 表現癌細胞之殘留病灶。",
     "inclusion": ["HER2 IHC 1+/2+/3+ 確認。", "PSOC 救援化療達穩定 (Non-PD)。"],
     "exclusion": ["ILD 肺部病史。"], "ref": "JCO 2024"},

    {"cancer": "Endometrial", "name": "MK2870-033", "pharma": "MSD", "drug": "Sac-TMT + Pembro", "pos": "P-MT", "sub_pos": ["IO Maintenance", "NSMP / pMMR"], 
     "rationale": "標靶 Trop-2 ADC 協同 PD-1。強化 Pembrolizumab 在 NSMP 族群的應答。",
     "inclusion": ["pMMR 子宮內膜癌。", "FIGO III/IV 一線含鉑+Pembro後達 CR/PR。"],
     "exclusion": ["先前接受過晚期系統性 IO。"], "ref": "ESMO 2025"},
    
    {"cancer": "Endometrial", "name": "GU-US-682-6769", "pharma": "Gilead", "drug": "SG (Trodelvy)", "pos": "R-TX", "sub_pos": ["NSMP / pMMR", "p53abn (Copy-number high)"], 
     "rationale": "標靶 Trop-2 ADC。釋放 SN-38 載荷引發 DNA 損傷，專攻鉑類與免疫失敗救援。",
     "inclusion": ["復發性 EC (非肉瘤)。", "鉑類與 PD-1 失敗後進展。"],
     "exclusion": ["先前用過 Trop-2 ADC。"], "ref": "JCO 2024"},

    {"cancer": "Cervical", "name": "innovaTV 301", "pharma": "Seagen", "drug": "Tivdak (Tisotumab)", "pos": "R-TX", "sub_pos": ["2L / 3L Therapy"], 
     "rationale": "標靶 Tissue Factor ADC。用於克服後線子宮頸癌化療耐藥性。",
     "inclusion": ["復發/轉移子宮頸癌。", "先前 1–2 線治療後進展。"],
     "exclusion": ["嚴重眼疾/角膜炎。"], "ref": "NEJM 2024"}
]

# --- 3. 指引導航架構：包含所有癌症與四階段 ---
guidelines_nested = {
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "MMRd / MSI-H", "content": "一線首選：Chemo + PD-1 (GY018/RUBY)。"},
            {"title": "NSMP / pMMR", "content": "視 ER/Grade 加權。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "IO Maintenance", "content": "延續一線 IO 直至進展。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "NSMP / pMMR / p53abn", "content": "標靶+免疫 或 Trop-2 ADC。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "持續有效之系統治療。"}]}
    ],
    "Ovarian": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [{"title": "HGSC / Endometrioid", "content": "Surgery + Carbo/Pacli ± Bev。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "BRCA mutated", "content": "Olaparib 單藥。"}, {"title": "HRD positive (wt)", "content": "Olaparib+Bev 或 Niraparib。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "PROC (Resistant)", "content": "單藥化療 ± Bev 或 FRα ADC。"}, {"title": "Platinum Sensitive", "content": "含鉑複方化療 ± Bev。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Platinum Sensitive Maint", "content": "含鉑救援緩解後選 PARPi 維持。"}]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "Locally Advanced (CCRT)", "content": "CCRT ± 同步 IO (A18) 或誘導化療。"},
            {"title": "Early (Surgery)", "content": "開腹根治術。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Metastatic Maint", "content": "1L IO 維持直至進展。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "1L Recurrent", "content": "Pembro + 化療 ± Bev。"},
            {"title": "2L / 3L Therapy", "content": "ADC (Tivdak) 或 Cemiplimab。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "持續有效之二/三線方案。"}]}
    ]
}

# --- 4. 動態模型巡邏邏輯 ---
def get_gemini_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target_model = None
        for m in available_models:
            if 'gemini-1.5-flash' in m: target_model = m; break
        if not target_model:
            for m in available_models:
                if 'gemini-pro' in m or 'gemini-1.5-pro' in m: target_model = m; break
        if target_model: return genai.GenerativeModel(target_model)
    except: return None

# --- 5. 側邊欄 ---
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = ongoing_trials[0]['name']

with st.sidebar:
    st.markdown("<h3 style='color: #6A1B9A;'>🤖 AI 實證決策助理</h3>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 病歷深度分析", expanded=True):
        p_notes = st.text_area("輸入摘要 (含分子/病理)", height=250)
        if st.button("🚀 開始分析"):
            if api_key and p_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = get_gemini_model()
                    if model:
                        prompt = f"分析：{p_notes}。參考實證：{milestone_db} 及進行中：{ongoing_trials}。提供路徑建議。"
                        st.write(model.generate_content(prompt).text)
                    else: st.error("找不到 AI 模型。")
                except Exception as e: st.error(f"AI 異常: {e}")

# --- 6. 主頁面：導航地圖 ---
st.markdown("<div class='main-title'>婦癌臨床導航儀表板 (指引實證與研究全整合)</div>", unsafe_allow_html=True)
cancer_type = st.radio("第一步：選擇癌症類型", ["Endometrial", "Ovarian", "Cervical"], horizontal=True)

st.subheader("第二步：點擊 📚 實證里程碑 或 📍 招募中試驗 (與 SoC 同步對照)")
cols = st.columns(4)
stages_data = guidelines_nested[cancer_type]

for i, stage in enumerate(stages_data):
    with cols[i]:
        st.markdown(f"""<div class='big-stage-card card-{stage['css']}'><div class='big-stage-header header-{stage['css']}'>{stage['header']}</div>""", unsafe_allow_html=True)
        for sub in stage['subs']:
            st.markdown(f"""<div class='sub-block'><div class='sub-block-title'>📘 {sub['title']}</div><div class='sub-block-content'>{sub['content']}</div>""", unsafe_allow_html=True)
            
            # A. 實證里程碑 (📚)
            rel_milestones = [m for m in milestone_db if m["cancer"] == cancer_type and m["pos"] == stage["id"] and any(s in sub["title"] for s in m["sub_pos"])]
            for m in rel_milestones:
                with st.popover(f"📚 {m['name']}", use_container_width=True):
                    st.success(f"**介入:** {m['drug']}\n\n**結論:** {m['summary']}")
            
            # B. 招募中試驗 (📍)
            rel_trials = [t for t in ongoing_db if t["cancer"] == cancer_type and t["pos"] == stage["id"] and any(s in sub["title"] for s in t["sub_pos"])]
            for t in rel_trials:
                label = f"📍 {t['pharma']} | {t['name']}"
                ukey = f"btn_{t['name']}_{stage['id']}_{sub['title'].replace(' ', '')}"
                with st.popover(label, use_container_width=True):
                    if st.button("📊 詳細細節", key=ukey):
                        st.session_state.selected_trial = t['name']
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 7. 招募中試驗詳盡報告 ---
st.divider()
t_options = [t["name"] for t in ongoing_db if t["cancer"] == cancer_type]
if t_options:
    try: curr_idx = t_options.index(st.session_state.selected_trial)
    except: curr_idx = 0
    selected_name = st.selectbox("🎯 切換招募中計畫詳細分析：", t_options, index=curr_idx)
    t = next(it for it in ongoing_db if it["name"] == selected_name)

    st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #E0E0E0; padding-bottom:10px; font-weight:900;'>📋 {t['name']} 招募中極量化數據</h2>", unsafe_allow_html=True)

    r1, r2 = st.columns([1.3, 1])
    with r1:
        st.markdown("<div style='background:#E3F2FD; border-left:10px solid #1976D2; padding:15px; border-radius:10px;'><b>💉 Rationale & 機轉</b></div>", unsafe_allow_html=True)
        st.write(f"**核心藥物:** {t['drug']}")
        st.success(t['rationale'])

    with r2:
        st.markdown("<div style='background:#E8F5E9; border-left:8px solid #2E7D32; padding:15px; border-radius:10px;'><b>✅ Inclusion Criteria (納入門檻)</b></div>", unsafe_allow_html=True)
        for inc in t.get('inclusion', []): st.write(f"• **{inc}**")

    st.markdown("<div style='background:#FFEBEE; border-left:8px solid #C62828; padding:15px; border-radius:10px; margin-top:10px;'><b>❌ Exclusion Criteria (排除門檻)</b></div>", unsafe_allow_html=True)
    for exc in t.get('exclusion', []): st.write(f"• **{exc}**")
    st.markdown("</div>", unsafe_allow_html=True)
