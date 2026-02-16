import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床導航與實證圖書館 (2026 最終全功能整合版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=Roboto:wght@400;700;900&display=swap');
    
    /* === 極致緊緻化 UI 與 高對比度文字 === */
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
        border: 2px solid transparent;
        background: white; margin-bottom: 4px; overflow: hidden;
        height: auto !important;
    }
    .big-stage-header {
        font-size: 17px !important; font-weight: 900; color: white;
        padding: 5px; text-align: center; margin: 0 !important;
    }

    /* 子區塊 (SoC 與分子亞型) */
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
    
    /* 📚 已發表里程碑色彩 */
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
    .hr-big-val { font-family: 'Roboto', sans-serif; font-size: 50px !important; font-weight: 900; color: #D84315; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 指引導航數據：包含子宮頸癌回歸與復發維持 ---
guidelines_nested = {
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "MMRd / MSI-H", "content": "一線首選：Chemo + PD-1 (GY018/RUBY)。"},
            {"title": "NSMP / pMMR", "content": "視 ER/Grade 加權。"},
            {"title": "POLEmut / p53abn", "content": "POLE: 最佳預後/降階；p53: 最差/升階。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "IO Maintenance", "content": "延續一線使用的免疫藥物維持至 PD。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "pMMR / NSMP", "content": "二線標準：Pembrolizumab + Lenvatinib (SoC)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "維持當前有效治療直至進展。"}]}
    ],
    "Ovarian": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [{"title": "HGSC / Endometrioid", "content": "Surgery + Carbo/Pacli x6 ± Bev。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "BRCA mutated", "content": "Olaparib 單藥維持。"}, {"title": "HRD positive (wt)", "content": "Olaparib+Bev 或 Niraparib。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "PSOC / PROC 分流", "content": "依 PFI 區分。標靶檢測看 FRα 或 HER2。"},
            {"title": "Secondary Surgery", "content": "符合條件可評估二次手術獲益。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Platinum Sensitive Maint", "content": "救援緩解後 PARPi 維持治療。"}]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "Early Stage", "content": "傳統開腹根治術；低風險選單純切除。"},
            {"title": "CCRT (LA / 1L)", "content": "CCRT ± 同步 IO (A18) 或誘導化療。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Metastatic Maint", "content": "1L IO 維持至進展。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "1L Recurrent", "content": "Pembro + 化療 ± Bev (CPS≥1)。"},
            {"title": "2L / 3L Therapy", "content": "Tisotumab vedotin (Tivdak) 或 Cemiplimab。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "維持有效治療直到進展。"}]}
    ]
}

# --- 2. 實證里程碑 (📚 Milestone - 植入24項研究) ---
milestone_db = [
    # Endometrial
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H"], "name": "📚 RUBY", "drug": "Dostarlimab + CP", "summary": "一線晚期/復發。dMMR PFS 獲益極顯著；推動一線 Immuno-chemo 標準。"},
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H", "NSMP / pMMR"], "name": "📚 NRG-GY018", "drug": "Pembrolizumab + CP", "summary": "一線晚期/復發。dMMR、pMMR 均 PFS 改善，擴大一線適用面。"},
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H", "NSMP / pMMR"], "name": "📚 DUO-E", "drug": "Durvalumab ± Olaparib", "summary": "一線。加 PARPi 維持可改善 PFS，建立「免疫/維持」策略。"},
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H"], "name": "📚 AtTEnd", "drug": "Atezolizumab + CP", "summary": "一線。dMMR 獲益較大，支持 PD-(L)1 併化療證據鏈。"},
    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["NSMP / pMMR"], "name": "📚 KEYNOTE-775", "drug": "Lenvatinib + Pembro", "summary": "二線(曾含鉑)。PFS/OS 優於化療；pMMR/MSS 後線關鍵組合。"},
    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["MMRd / MSI-H"], "name": "📚 GARNET", "drug": "Dostarlimab", "summary": "多線後。奠定 dMMR/MSI-H 後線免疫單藥地位。"},

    # Cervical
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["CCRT (LA / 1L)"], "name": "📚 KEYNOTE-A18", "drug": "Pembro + CCRT", "summary": "局部晚期。OS/PFS 顯著改善：免疫正式併入根治性 CCRT。"},
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["CCRT (LA / 1L)"], "name": "📚 INTERLACE", "drug": "Induction Carbo/Pacli", "summary": "局部晚期。先 6週誘導化療再 CCRT，5 年 OS/PFS 改善。"},
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["CCRT (LA / 1L)"], "name": "📚 CALLA (陰性)", "drug": "Durvalumab + CCRT", "summary": "局部晚期。整體未達顯著改善：需更精準族群分流。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["1L Recurrent"], "name": "📚 KEYNOTE-826", "drug": "Pembro + Chemo ± Bev", "summary": "R/M 一線。OS 持續改善：一線 Immuno-chemo 核心試驗。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["1L Recurrent"], "name": "📚 BEATcc", "drug": "Atezolizumab + Chemo + Bev", "summary": "R/M 一線。PFS/OS 皆改善：提供另一個免疫選項。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["2L / 3L Therapy"], "name": "📚 EMPOWER-Cx1", "drug": "Cemiplimab", "summary": "二線。OS 改善：後線免疫單藥關鍵證據。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["2L / 3L Therapy"], "name": "📚 innovaTV 301", "drug": "Tivdak (ADC)", "summary": "二/三線。OS/PFS/ORR 改善：ADC 進入後線標準選項。"},
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Early Stage"], "name": "📚 LACC Trial", "drug": "Open vs MIS", "summary": "早期手術。微創復發/死亡率高，根治標準重回開腹。"},
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Early Stage"], "name": "📚 SHAPE Trial", "drug": "Simple Hysterectomy", "summary": "早期。針對低風險者，單純全切除不劣於根治術。"},

    # Ovarian
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutated"], "name": "📚 SOLO-1", "drug": "Olaparib", "summary": "一線維持。PFS 里程碑級提升：BRCA 族群核心標準。"},
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive (wt)", "HRD negative / pHRD"], "name": "📚 PRIMA", "drug": "Niraparib", "summary": "一線維持。整體 PFS 改善，支持「不限 BRCA」概念。"},
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive (wt)"], "name": "📚 PAOLA-1", "drug": "Olaparib + Bev", "summary": "一線維持。HRD+ 獲益最大：確立 PARPi + Bev 維持路徑。"},
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive (wt)"], "name": "📚 DUO-O", "drug": "Durva+Chemo+Bev", "summary": "一線。組合維持顯示 PFS 改善：組合策略具勝算。"},
    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], "name": "📚 NOVA / ARIEL3", "drug": "PARPi", "summary": "復發維持。兩者皆 PFS 顯著改善：重要基石試驗。"},
    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], "name": "📚 SOLO2", "drug": "Olaparib", "summary": "復發維持。BRCA 族群具臨床意義的 OS 獲益。"},
    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PROC (Resistant)"], "name": "📚 MIRASOL", "drug": "Mirvetuximab (FRα)", "summary": "後線(鉑類抗藥)。卵巢癌後線 ADC 重大新武器。"},
    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 van Driel HIPEC", "drug": "Surgery + HIPEC", "summary": "手術。NACT 後 IDS 加 HIPEC 改善 OS/RFS。"},
    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 LION Trial", "drug": "No Lymphadenectomy", "summary": "手術。臨床 LN 陰性者，清掃無存活獲益且併發症多。"},
    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["Secondary Surgery"], "name": "📚 DESKTOP III", "drug": "Secondary Cytoreduction", "summary": "復發手術。嚴選 AGO Score 合格者可改善 OS。"}
]

# --- 3. 進行中臨床試驗資料庫 (📍 Ongoing - 8 核心詳盡細節) ---
ongoing_trials = [
    {"cancer": "Ovarian", "name": "FRAmework-01 (LY4170156)", "pharma": "Eli Lilly", "drug": "LY4170156 + Bev", "pos": "R-TX", "sub_pos": ["PROC (Resistant)", "PSOC"], 
     "rationale": "標靶 FRα ADC，搭載類微管蛋白載荷。聯用 Bevacizumab 可產生血管調節協同作用 (Synergy)，提升 ADC 滲透並殺傷異質性腫瘤。",
     "dosing": {"Exp Arm": "LY4170156 3mg/kg + Bev 15mg/kg Q3W", "Control": "TPC 或 Platinum doublet + Bev"},
     "inclusion": ["High-grade Serous 卵巢癌。", "經檢測確認 FRα 表達陽性。", "Part A: PROC (復發≤6m)。", "Part B: PSOC (復發>6m)。"],
     "exclusion": ["先前用過 Topo I ADC (如 Enhertu)。", "具有臨床顯著蛋白尿。"], "ref": "NCT06536348"},
    
    {"cancer": "Ovarian", "name": "REJOICE-Ovarian01", "pharma": "Daiichi Sankyo", "drug": "R-DXd", "pos": "R-TX", "sub_pos": ["PROC (Resistant)"], 
     "rationale": "標靶 Cadherin-6 (CDH6) ADC。具備強力旁觀者效應 (Bystander effect)，專攻高度異質性 PROC。",
     "inclusion": ["HG Serous 或 Endometrioid PROC。", "需曾用過 Bevacizumab。", "先前接受 1-4 線系統治療。"],
     "exclusion": ["Low-grade 腫瘤。", "LVEF < 50%。"], "ref": "JCO 2024"},
    
    {"cancer": "Ovarian", "name": "TroFuse-021", "pharma": "MSD", "drug": "Sac-TMT (MK-2870)", "pos": "P-MT", "sub_pos": ["HRD negative / pHRD"], 
     "rationale": "標靶 Trop-2 ADC。結合 Beva 微環境調節，優化 pHRD 族群在一線維持獲益。",
     "inclusion": ["FIGO III/IV 卵巢癌。", "HRD negative 且 BRCA 野生型。", "一線含鉑化療後達 CR/PR。"],
     "exclusion": ["先前用過 Trop-2 ADC。"], "ref": "ENGOT-ov85"},

    {"cancer": "Endometrial", "name": "MK2870-033", "pharma": "MSD", "drug": "Sac-TMT + Pembro", "pos": "P-MT", "sub_pos": ["IO Maintenance", "NSMP / pMMR"], 
     "rationale": "標靶 Trop-2 ADC 協同 PD-1。強化 Pembrolizumab 在 NSMP 族群的應答。",
     "inclusion": ["pMMR 子宮內膜癌 (中心檢測)。", "FIGO III/IV 一線含鉑+Pembro後達 CR/PR。"],
     "exclusion": ["先前接受過晚期系統性 IO。"], "ref": "ESMO 2025"},
    
    {"cancer": "Endometrial", "name": "GU-US-682-6769", "pharma": "Gilead", "drug": "SG (Trodelvy)", "pos": "R-TX", "sub_pos": ["NSMP / pMMR", "p53abn"], 
     "rationale": "標靶 Trop-2 ADC。釋放 SN-38 載荷引發 DNA 損傷，專攻鉑類與免疫失敗救援。",
     "inclusion": ["復發性 EC (非肉瘤)。", "鉑類與 PD-1 失敗後進展。"],
     "exclusion": ["先前用過 Trop-2 ADC。"], "ref": "JCO 2024"},

    {"cancer": "Ovarian", "name": "DS8201-772 (Enhertu)", "pharma": "AstraZeneca", "drug": "T-DXd", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], 
     "rationale": "標靶 HER2 ADC。救援化療穩定後之維持首選。超高 DAR (8) 優勢清除 HER2 表現殘留病灶。",
     "inclusion": ["HER2 IHC 1+/2+/3+ 確認。", "PSOC 救援化療達穩定 (Non-PD)。"],
     "exclusion": ["ILD 肺部病史。"], "ref": "JCO 2024"},

    {"cancer": "Ovarian", "name": "DOVE", "pharma": "GSK", "drug": "Dostarlimab + Bev", "pos": "R-TX", "sub_pos": ["PROC (Resistant)"], 
     "rationale": "針對透明細胞癌 (OCCC)。PD-1 + VEGF 雙重阻斷改善微環境。",
     "inclusion": ["組織學 OCCC > 50%。", "鉑類抗藥性。"],
     "exclusion": ["先前用過任何免疫治療。"], "ref": "JCO 2025"},

    {"cancer": "Cervical", "name": "innovaTV 301", "pharma": "Seagen", "drug": "Tivdak", "pos": "R-TX", "sub_pos": ["2L / 3L Therapy"], 
     "rationale": "標靶 Tissue Factor ADC。用於克服後線子宮頸癌化療耐藥性。",
     "inclusion": ["復發/轉移子宮頸癌。", "先前 1–2 線治療後進展。"],
     "exclusion": ["嚴重眼疾。"], "ref": "NEJM 2024"}
]

# --- 4. 動態模型巡邏與 AI 模型選擇 ---
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
                        prompt = f"分析：{p_notes}。參考實證：{milestone_db} 及進行中：{ongoing_trials}。提供路徑建議與理由。"
                        st.write(model.generate_content(prompt).text)
                    else: st.error("找不到可用 AI 模型。")
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
                    st.success(f"**藥物:** {m['drug']}\n\n**核心結論:** {m['summary']}")
            
            # B. 招募中試驗 (📍)
            rel_trials = [t for t in ongoing_trials if t["cancer"] == cancer_type and t["pos"] == stage["id"] and any(s in sub["title"] for s in t["sub_pos"])]
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
t_options = [t["name"] for t in ongoing_trials if t["cancer"] == cancer_type]
if t_options:
    try: curr_idx = t_options.index(st.session_state.selected_trial)
    except: curr_idx = 0
    selected_name = st.selectbox("🎯 切換招募中計畫分析報告：", t_options, index=curr_idx)
    t = next(it for it in ongoing_trials if it["name"] == selected_name)

    st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #E0E0E0; padding-bottom:10px; font-weight:900;'>📋 {t['name']} 招募中深度數據</h2>", unsafe_allow_html=True)

    r1, r2 = st.columns([1.3, 1])
    with r1:
        st.markdown("<div style='background:#E3F2FD; border-left:10px solid #1976D2; padding:15px; border-radius:10px;'><b>💉 Dosing & Rationale (機轉詳解)</b></div>", unsafe_allow_html=True)
        st.write(f"**核心藥物:** {t['drug']}")
        st.success(t['rationale'])

    with r2:
        st.markdown("<div style='background:#E8F5E9; border-left:8px solid #2E7D32; padding:15px; border-radius:10px;'><b>✅ Inclusion Criteria (納入門檻)</b></div>", unsafe_allow_html=True)
        for inc in t.get('inclusion', []): st.write(f"• **{inc}**")

    st.markdown("<div style='background:#FFEBEE; border-left:8px solid #C62828; padding:15px; border-radius:10px; margin-top:10px;'><b>❌ Exclusion Criteria (排除門檻)</b></div>", unsafe_allow_html=True)
    for exc in t.get('exclusion', []): st.write(f"• **{exc}**")
    st.markdown("</div>", unsafe_allow_html=True)
