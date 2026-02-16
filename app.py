import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床導航與實證圖書館 (2026 旗艦全功能整合版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

# 初始化 session_state
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = "📚 RUBY"

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=Roboto:wght@400;700;900&display=swap');
    
    /* === 極致緊緻化 UI === */
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', 'Roboto', sans-serif;
        background-color: #F4F7F9; color: #1A1A1A;
        font-size: 19px !important; line-height: 1.1;
    }

    .main-title {
        font-size: 30px !important; font-weight: 900; color: #004D40;
        padding: 5px 0; border-bottom: 3px solid #4DB6AC; margin-bottom: 5px;
    }

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

    .sub-block {
        margin: 2px 4px; padding: 4px; border-radius: 6px; 
        background: #F8F9FA; border-left: 5px solid #546E7A;
    }
    .sub-block-title {
        font-size: 13px; font-weight: 900; color: #37474F;
        margin-bottom: 1px; border-bottom: 1.1px solid #CFD8DC; padding-bottom: 1px;
    }

    /* 按鈕樣式：深黑色加粗 (#1A1A1A) */
    .stPopover button { 
        font-weight: 900 !important; font-size: 11px !important; 
        border-radius: 4px !important; margin-top: 1px !important;
        padding: 1px 6px !important; width: 100% !important; 
        text-align: left !important; color: #1A1A1A !important; 
        border: 1px solid rgba(0,0,0,0.15) !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
    }
    
    .stPopover button[aria-label*="📚"] { background: #ECEFF1 !important; border-left: 5px solid #455A64 !important; }
    .stPopover button[aria-label*="📍"] { background: #E1F5FE !important; border-left: 5px solid #0288D1 !important; } 

    .detail-section { background: white; border-radius: 18px; padding: 25px; border: 1px solid #CFD8DC; box-shadow: 0 10px 40px rgba(0,0,0,0.05); }
    .hr-big-val { font-family: 'Roboto', sans-serif; font-size: 40px !important; font-weight: 900; color: #D84315; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 指引導航數據庫：全階段、MOC、PSOC/PROC ---
guidelines_nested = {
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "MMRd / MSI-H / dMMR", "content": "一線首選：Chemo + PD-1 (RUBY/GY018/AtTEnd)。"},
            {"title": "NSMP / pMMR / MSS", "content": "排除分型。視 ER/Grade 決策；一線加維持 (DUO-E)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "IO Maintenance", "content": "一線 IO 治療後延續維持至進展 (PD)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "Recurrent EC", "content": "標靶+免疫 (MSS) 或 IO 單藥 (GARNET/MMRd)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "維持有效治療直到 PD。"}]}
    ],
    "Ovarian": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "HGSC / Endometrioid", "content": "Surgery + Carbo/Pacli ± Bev。考慮 IDS + HIPEC (van Driel)。"},
            {"title": "Mucinous (MOC) 鑑別", "content": "判定：CK7+/SATB2- (原發)。1. Expansile: 預後佳。 2. Infiltrative: 建議化療。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "BRCA mutated", "content": "Olaparib 維持 2年 (SOLO-1)。"}, {"title": "HRD positive (wt)", "content": "PAOLA-1 (Ola+Bev) 或 PRIMA (Nira)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "PSOC (Sensitive)", "content": "PFI > 6m。評估二次手術 (DESKTOP III) 或含鉑雙藥。"},
            {"title": "PROC (Resistant)", "content": "PFI < 6m。單藥化療 ± Bev 或標靶 ADC (MIRASOL)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Platinum Sensitive Maint", "content": "救援緩解後選 PARPi 維持 (NOVA/ARIEL3/SOLO2)。"}]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "Locally Advanced (CCRT)", "content": "同步化放療 ± IO (A18) 或 誘導化療 (INTERLACE)。"},
            {"title": "Early Stage (Surgery)", "content": "根治術 (LACC) 或單純切除 (SHAPE)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "Recurr / Metastatic", "content": "一線 Pembro+化療±Bev (KN826) 或 Atezo組合 (BEATcc)。二線 ADC (innovaTV 301)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "維持有效治療直到 PD。"}]}
    ]
}

# --- 2. 綜合實證里程碑資料庫 (25項全數歸納) ---
milestone_db = [
    # --- Endometrial ---
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H / dMMR"], "name": "📚 RUBY", "pharma": "GSK", "drug": "Dostarlimab + CP", 
     "rationale": "PD-1 阻斷與含鉑化療具備協同 ICD 效應。", 
     "regimen": "Dostarlimab 500mg Q3W + CP x6週期 -> 維持 1000mg Q6W 最長 3年。",
     "inclusion": ["FIGO III-IV 期或首次復發 EC。", "包含 Carcinosarcoma 型態。"],
     "results": "dMMR: HR 0.32; mOS 44.6m (vs 28.2m, HR 0.69)."},
    
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["NSMP / pMMR / MSS"], "name": "📚 DUO-E", "pharma": "AZ", "drug": "Durvalumab + CP -> 維持 ± Olaparib", 
     "rationale": "探索 PARPi 於 pMMR 患者免疫維持之協同效應。",
     "results": "三藥組 PFS HR 0.57 (vs CP); dMMR 組 HR 0.42."},

    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H / dMMR"], "name": "📚 AtTEnd", "pharma": "Roche", "drug": "Atezolizumab + CP", 
     "results": "dMMR PFS HR 0.36; ITT OS HR 0.82 (P=0.048)."},

    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "name": "📚 KEYNOTE-775", "pharma": "MSD/Eisai", "drug": "Lenvatinib + Pembro", 
     "results": "pMMR OS HR 0.68; mOS 17.4m vs 12.0m. 確立 MSS 二線標準。"},

    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "name": "📚 GARNET", "pharma": "GSK", "drug": "Dostarlimab (Single)", 
     "results": "dMMR/MSI-H ORR 45.5%; DOR 未達到。"},

    # --- Cervical ---
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Locally Advanced (CCRT)"], "name": "📚 KEYNOTE-A18", "pharma": "MSD", "drug": "Pembrolizumab + CCRT", 
     "results": "OS HR 0.67; 36m OS 82.6% (vs 74.8%)."},

    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Locally Advanced (CCRT)"], "name": "📚 INTERLACE", "pharma": "UCL", "drug": "Induction Carbo/Pacli x6", 
     "results": "5yr OS 80% (vs 72%, HR 0.60)."},

    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Locally Advanced (CCRT)"], "name": "📚 CALLA", "pharma": "AZ", "drug": "Durvalumab + CCRT", 
     "results": "PFS HR 0.84 (P=NS). 陰性試驗提醒需更精準分流。"},

    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 KEYNOTE-826", "pharma": "MSD", "drug": "Pembro + 化療 ± Bev", 
     "results": "OS HR 0.63 (ITT); HR 0.60 (CPS≥1)."},

    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 BEATcc", "pharma": "Roche", "drug": "Atezo + Chemo + Bev", 
     "results": "PFS HR 0.62; OS HR 0.68."},

    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 EMPOWER-Cx 1", "pharma": "Regeneron", "drug": "Cemiplimab", 
     "results": "OS HR 0.69; mOS 12.0m vs 8.5m."},

    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 innovaTV 301", "pharma": "Seagen", "drug": "Tisotumab Vedotin (ADC)", 
     "results": "OS HR 0.70; ORR 17.8% (vs 5.2%)."},

    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Early Stage (Surgery)"], "name": "📚 SHAPE trial", "pharma": "UCL/CCTG", "drug": "Simple Hysterectomy", 
     "results": "3yr Recurrence: 2.5% vs 2.2% (不劣性達成)。"},

    # --- Ovarian ---
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutated"], "name": "📚 SOLO-1", "pharma": "AZ", "drug": "Olaparib 維持", 
     "results": "7yr survival 67% (HR 0.33); ITT 未達到。"},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive (wt)", "HRD negative / pHRD"], "name": "📚 PRIMA", "pharma": "GSK", "drug": "Niraparib 維持", 
     "results": "HRD+ PFS HR 0.43; 全人群 HR 0.62."},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive (wt)"], "name": "📚 PAOLA-1", "pharma": "AZ", "drug": "Olaparib + Bevacizumab", 
     "results": "HRD+ OS HR 0.62; 5yr OS 75.2%."},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutated", "HRD positive (wt)"], "name": "📚 ATHENA–MONO", "pharma": "Clovis", "drug": "Rucaparib 維持", 
     "results": "ITT PFS HR 0.52 (28.7m vs 11.3m)."},

    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], "name": "📚 NOVA", "pharma": "GSK", "drug": "Niraparib 維持", 
     "results": "gBRCA HR 0.27; Non-gBRCA HR 0.45."},

    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], "name": "📚 ARIEL3", "pharma": "Clovis", "drug": "Rucaparib 維持", 
     "results": "BRCAm HR 0.23; HRD+ HR 0.32."},

    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], "name": "📚 SOLO2", "pharma": "AZ", "drug": "Olaparib 維持", 
     "results": "mOS 51.7m vs 38.8m; HR 0.74."},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive (wt)"], "name": "📚 DUO-O", "pharma": "AZ", "drug": "Durva+Ola+Bev 維持", 
     "results": "HRD+ PFS HR 0.49."},

    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PROC (Resistant)"], "name": "📚 MIRASOL", "pharma": "ImmunoGen", "drug": "Mirvetuximab", 
     "results": "OS HR 0.67; ORR 42.3%. PROC 歷史性突破。"},

    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 van Driel HIPEC", "pharma": "NEJM 2018", "drug": "Surgery + HIPEC", 
     "results": "mOS 45.7m vs 33.9m (HR 0.67)."},

    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PSOC (Sensitive)"], "name": "📚 DESKTOP III", "pharma": "NEJM 2021", "drug": "Secondary Surgery", 
     "results": "mOS 53.7m vs 46.0m (HR 0.75)."},

    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 LION", "pharma": "NEJM 2019", "drug": "No Lymphadenectomy", 
     "results": "OS HR 1.06 (P=0.65)。臨床 LN 陰性免清掃。"},
]

# --- 3. 招募中臨床試驗資料庫 (8核心補齊) ---
ongoing_trials = [
    {"cancer": "Ovarian", "name": "📍 FRAmework-01", "pharma": "Eli Lilly", "drug": "LY4170156 + Bevacizumab", "pos": "R-TX", "sub_pos": ["PROC (Resistant)"], "type": "Ongoing",
     "rationale": "標靶 FRα ADC。聯用 Bevacizumab 產生血管調節協同作用 (Synergy)，提升藥物滲透深度並透過旁觀者效應殺傷低表達細胞。",
     "regimen": "LY4170156 3mg/kg IV + Bevacizumab 15mg/kg IV Q3W。",
     "inclusion": ["HG Serous / Carcinosarcoma 卵巢癌。", "經檢測確認 FRα 表達陽性。", "最後一劑鉑類後 90–180 天內惡化 (PROC)。"],
     "exclusion": ["曾用過 Topo I ADC (Enhertu)。", "活動性間質性肺病 (ILD)。"], "results": "Ongoing Recruitment."},

    {"cancer": "Ovarian", "name": "📍 REJOICE-Ovarian01", "pharma": "Daiichi Sankyo", "drug": "R-DXd", "pos": "R-TX", "sub_pos": ["PROC (Resistant)"], "type": "Ongoing",
     "rationale": "標靶 Cadherin-6 (CDH6) ADC。具極高 DAR (8) 與強力旁觀者效應，專攻異質性 PROC。",
     "regimen": "R-DXd 5.6mg/kg IV Q3W。",
     "inclusion": ["HG Serous 或 Endometrioid PROC。", "提供切片判定 CDH6 分層。"],
     "exclusion": ["Low-grade 腫瘤。", "LVEF < 50%。"], "results": "ORR ~46% in Phase 1 Expansion."},

    {"cancer": "Ovarian", "name": "📍 TroFuse-021", "pharma": "MSD", "drug": "Sac-TMT (MK-2870)", "pos": "P-MT", "sub_pos": ["HRD positive (wt)", "HRD negative / pHRD"], "type": "Ongoing",
     "rationale": "標靶 Trop-2 ADC。透過結合 Beva 微環境調節與 ADC 誘導之 ICD 效應，優化維持階段獲益。",
     "regimen": "Sac-TMT Q3W + Bevacizumab 維持。",
     "inclusion": ["新診斷 Stage III/IV 卵巢癌。", "一線含鉑化療後達 CR 或 PR。"],
     "exclusion": ["BRCA 變異者。", "先前用過針對 Trop-2 之 ADC 藥物。"], "results": "Phase 3 Recruitment."},

    {"cancer": "Endometrial", "name": "📍 MK2870-033", "pharma": "MSD", "drug": "Sac-TMT + Pembrolizumab", "pos": "P-MT", "sub_pos": ["IO Maintenance"], "type": "Ongoing",
     "rationale": "標靶 Trop-2 ADC 協同 PD-1。透過免疫原性調節強化 Pembro 在 pMMR 或 NSMP 族群應答。",
     "regimen": "Pembro 400mg Q6W + Sac-TMT 5mg/kg Q6W。",
     "inclusion": ["pMMR 子宮內膜癌 (中心檢測)。", "FIGO III/IV 一線含鉑+Pembro後達 CR/PR。"],
     "exclusion": ["先前接受過晚期系統性 IO 治療。"], "results": "Phase 3 Recruiting."},
    
    {"cancer": "Endometrial", "name": "📍 GU-US-682-6769", "pharma": "Gilead", "drug": "SG (Trodelvy)", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "type": "Ongoing",
     "rationale": "標靶 Trop-2 ADC。利用 SN-38 載荷引發 DNA 損傷，專攻鉑類與免疫失敗救援。",
     "regimen": "SG 10mg/kg (D1, D8 Q21D)。",
     "inclusion": ["復發性 EC (不含肉瘤)。", "鉑類與 PD-1 失敗後進展。"],
     "exclusion": ["先前用過 Trop-2 ADC。"], "results": "ORR ~28% in Phase 2."},

    {"cancer": "Ovarian", "name": "📍 DS8201-772 (Enhertu)", "pharma": "AstraZeneca", "drug": "T-DXd (HER2 ADC)", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], "type": "Ongoing",
     "rationale": "標靶 HER2 ADC。救援化療穩定後精準維持，清除 HER2 表現癌細胞殘留病灶。",
     "regimen": "T-DXd 5.4mg/kg IV Q3W。",
     "inclusion": ["HER2 IHC 1+/2+/3+ 確認。", "PSOC 救援化療達穩定 (Non-PD)。"],
     "exclusion": ["ILD 肺部病史。"], "results": "Phase 3 Access."},

    {"cancer": "Ovarian", "name": "📍 DOVE", "pharma": "GSK", "drug": "Dostarlimab + Bevacizumab", "pos": "R-TX", "sub_pos": ["PROC (Resistant)"], "type": "Ongoing",
     "rationale": "針對 OCCC 透明細胞癌。利用 IO + anti-VEGF 雙重打擊，改善其特有免疫抑制環境。",
     "regimen": "Dostarlimab 1000mg Q6W + Bev Q3W。",
     "inclusion": ["組織學 OCCC > 50%。", "鉑類抗藥性 (PFI < 12m)。"],
     "exclusion": ["先前用過任何免疫治療。"], "results": "Phase 2 Recruiting."},

    {"cancer": "Cervical", "name": "📍 innovaTV 301 Access", "pharma": "Seagen", "drug": "Tisotumab Vedotin (Tivdak)", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "type": "Ongoing",
     "rationale": "標靶 Tissue Factor (TF) ADC。旨在克服後線子宮頸癌化療耐藥性。",
     "inclusion": ["復發/轉移子宮頸癌。", "先前接受 1–2 線治療後進展。"],
     "exclusion": ["嚴重眼疾或角膜炎。"], "results": "Post-FDA Access Trial."},
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
with st.sidebar:
    st.markdown("<h3 style='color: #6A1B9A;'>🤖 AI 實證媒合助理</h3>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 病歷分析", expanded=True):
        p_notes = st.text_area("輸入摘要 (分型/標記)", height=250)
        if st.button("🚀 開始分析"):
            if api_key and p_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = get_gemini_model()
                    prompt = f"分析：{p_notes}。參考：{milestone_db} 及 {ongoing_trials}。提供治療建議。"
                    st.write(model.generate_content(prompt).text)
                except Exception as e: st.error(f"AI 異常: {e}")

# --- 6. 主頁面：導航地圖 ---
st.markdown("<div class='main-title'>婦癌臨床導航儀表板 (2026 實證與收案整合版)</div>", unsafe_allow_html=True)
cancer_type = st.radio("第一步：選擇癌症類型", ["Endometrial", "Ovarian", "Cervical"], horizontal=True)

cols = st.columns(len(guidelines_nested[cancer_type]))
stages_data = guidelines_nested[cancer_type]

for i, stage in enumerate(stages_data):
    with cols[i]:
        st.markdown(f"""<div class='big-stage-card card-{stage['css']}'><div class='big-stage-header header-{stage['css']}'>{stage['header']}</div>""", unsafe_allow_html=True)
        for sub in stage['subs']:
            st.markdown(f"""<div class='sub-block'><div class='sub-block-title'>📘 {sub['title']}</div><div class='sub-block-content'>{sub['content']}</div>""", unsafe_allow_html=True)
            
            # 顯示對應試驗 (📚 & 📍)
            rel_trials = [t for t in (milestone_db + ongoing_trials) if t["cancer"] == cancer_type and t["pos"] == stage["id"] and any(s in sub["title"] for s in t["sub_pos"])]
            for t in rel_trials:
                label = f"{t.get('pharma', 'N/A')} | {t['name']} | {t['drug']}"
                with st.popover(label, use_container_width=True):
                    st.success(f"**核心結論:** {t.get('results', '招募中')}")
                    # 使用唯一鍵值聯動，點選後 rerun 同步下方看板
                    ukey = f"sync_{t['name']}_{cancer_type}_{stage['id']}_{sub['title'].replace(' ', '')}"
                    if st.button("📊 同步看板細節", key=ukey):
                        st.session_state.selected_trial = t['name']
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 7. 臨床試驗深度數據庫 (Bottom Selector) ---
st.divider()
st.subheader("📋 臨床試驗深度數據庫 (Published Milestones & Ongoing Trials)")
all_list = milestone_db + ongoing_trials
filtered_names = [t["name"] for t in all_list if t["cancer"] == cancer_type]

try: curr_idx = filtered_names.index(st.session_state.selected_trial)
except: curr_idx = 0

selected_name = st.selectbox("🎯 快速選擇研究計畫以查閱詳細內容：", filtered_names, index=curr_idx, key="trial_selector")
st.session_state.selected_trial = selected_name # 同步選中的計畫

t = next(it for it in all_list if it["name"] == selected_name)

st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #E0E0E0; padding-bottom:10px; font-weight:900;'>📋 {t['name']} 深度數據分析報告</h2>", unsafe_allow_html=True)

r1, r2 = st.columns([1.3, 1])
with r1:
    st.markdown("<div style='background:#E3F2FD; border-left:10px solid #1976D2; padding:15px; border-radius:10px;'><b>💉 Rationale & Regimen (機轉與配方)</b></div>", unsafe_allow_html=True)
    st.write(f"**核心介入:** {t['drug']}")
    st.write(f"**詳細給藥:** {t.get('regimen', t.get('dosing', '詳見招募細則'))}")
    st.success(t.get('rationale', '該研究主要針對特定分子分型，透過前沿標靶或免疫機制挑戰現有 SoC 瓶頸。'))
    
with r2:
    st.markdown("<div style='background:#FFF8E1; border-left:8px solid #FBC02D; padding:15px; border-radius:10px;'><b>📈 Key Outcomes (生存與緩解數據)</b></div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style='text-align:center; background:white; padding:15px; border:2px solid #FFE082; border-radius:12px;'>
            <div style='font-size: 14px; color: #795548; font-weight:700; margin-bottom:5px;'>Survival Metrics (PFS/OS/HR/ORR)</div>
            <div class='hr-big-val'>{t.get('results', 'Recruiting...')}</div>
        </div>
    """, unsafe_allow_html=True)
    
st.divider()
r3, r4 = st.columns(2)
with r3:
    st.markdown("<div style='background:#E8F5E9; border-left:8px solid #2E7D32; padding:15px; border-radius:10px;'><b>✅ Inclusion Criteria (納入條件)</b></div>", unsafe_allow_html=True)
    for inc in t.get('inclusion', ['詳見全文 Protocol。']): st.write(f"• **{inc}**")
with r4:
    st.markdown("<div style='background:#FFEBEE; border-left:8px solid #C62828; padding:15px; border-radius:10px;'><b>❌ Exclusion Criteria (排除標準)</b></div>", unsafe_allow_html=True)
    for exc in t.get('exclusion', ['詳見全文 Protocol。']): st.write(f"• **{exc}**")
st.markdown("</div>", unsafe_allow_html=True)
