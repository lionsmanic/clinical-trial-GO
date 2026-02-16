import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床導航與實證圖書館 (2026 旗艦全功能整合版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=Roboto:wght@400;700;900&display=swap');
    
    /* === 極致緊緻化 UI 與 高對比度文字 === */
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', 'Roboto', sans-serif;
        background-color: #F4F7F9; color: #1A1A1A;
        font-size: 19px !important; line-height: 1.1;
    }

    .main-title {
        font-size: 32px !important; font-weight: 900; color: #004D40;
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

# --- 1. 指引導航數據庫：全階段、MOC 與 PSOC/PROC 分流 ---
guidelines_nested = {
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "MMRd / MSI-H / dMMR", "content": "首選：Chemo + PD-1 (GY018/RUBY)。"},
            {"title": "NSMP / pMMR / MSS", "content": "排除分型。視 ER/Grade 權重決策；二線 Pembro+Lenva。"},
            {"title": "POLEmut / p53abn", "content": "POLE: 最佳預後；p53: 最差需積極化放。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "IO Maintenance", "content": "延續一線 IO 至 PD。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "Recurrent EC", "content": "標靶+免疫 (pMMR) 或 IO 單藥 (MMRd)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "維持有效治療直到進展。"}]}
    ],
    "Ovarian": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "HGSC / Endometrioid", "content": "Surgery + Carbo/Pacli ± Bev。"},
            {"title": "Mucinous (MOC) 鑑別", "content": "判定：CK7+/SATB2- (原發)。1. Expansile (IA可保守)。 2. Infiltrative (建議化療)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "BRCA mutated", "content": "Olaparib 維持 2年。"}, {"title": "HRD positive (wt)", "content": "Olaparib+Bev 或 Niraparib。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "PSOC (Sensitive Recurrence)", "content": "PFI > 6m。評估二次手術 (DESKTOP III)。"},
            {"title": "PROC (Resistant Recurrence)", "content": "PFI < 6m。單藥化療 ± Bev 或標靶 ADC (MIRASOL)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Platinum Sensitive Maint", "content": "救援緩解後選 PARPi 維持治療。"}]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "Locally Advanced (CCRT)", "content": "同步化放療。高風險者同步 IO (A18) 或誘導化療。"},
            {"title": "Early Stage (Surgery)", "content": "根治術 (LACC) 或單純切除 (SHAPE)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Metastatic Maint", "content": "1L IO 方案後延續維持至 PD。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "Recurr / Metastatic", "content": "一線 Pembro+化療±Bev。二線 ADC (Tivdak) 或 IO。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "維持當前有效方案直到進展。"}]}
    ]
}

# --- 2. 實證資料庫 (25 里程碑 + 8 招募中) ---
all_trials_db = [
    # --- 📚 Published Milestones ---
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H / dMMR"], "name": "📚 RUBY", "pharma": "GSK", "drug": "Dostarlimab + CP", 
     "results": "dMMR: HR 0.32; mOS 44.6m (vs 28.2m, HR 0.69).", "rationale": "PD-1 阻斷協同化療誘發抗原。"},
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["NSMP / pMMR / MSS"], "name": "📚 NRG-GY018", "pharma": "MSD", "drug": "Pembrolizumab + CP", 
     "results": "dMMR PFS HR 0.30; pMMR HR 0.54.", "rationale": "支持一線不論 MMR 狀態之 IO 獲益。"},
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["NSMP / pMMR / MSS"], "name": "📚 DUO-E", "pharma": "AZ", "drug": "Durvalumab + CP -> 維持 Durva ± Ola", 
     "results": "三藥組 PFS HR 0.57 (vs CP).", "rationale": "PARPi 對 pMMR 的協同維持效應。"},
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H / dMMR"], "name": "📚 AtTEnd", "pharma": "Roche", "drug": "Atezolizumab + CP", 
     "results": "dMMR PFS HR 0.36; ITT OS HR 0.82.", "rationale": "PD-L1 併化療一線晚期價值。"},
    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "name": "📚 KEYNOTE-775", "pharma": "MSD/Eisai", "drug": "Lenvatinib + Pembro", 
     "results": "pMMR OS HR 0.68; mOS 17.4m.", "rationale": "MSS 後線標靶免疫關鍵證據。"},
    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "name": "📚 GARNET", "pharma": "GSK", "drug": "Dostarlimab (Single-agent)", 
     "results": "dMMR ORR 45.5%.", "rationale": "奠定 MSI-H/dMMR 後線地位。"},
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Locally Advanced (CCRT)"], "name": "📚 KEYNOTE-A18", "pharma": "MSD", "drug": "Pembrolizumab + CCRT", 
     "results": "OS HR 0.67; 36m OS 82.6%.", "rationale": "免疫併入局部晚期根治標準。"},
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Locally Advanced (CCRT)"], "name": "📚 INTERLACE", "pharma": "UCL", "drug": "Induction Carbo/Pacli x6", 
     "results": "5yr OS 80% (vs 72%, HR 0.60).", "rationale": "誘導化療提升根治性存活。"},
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Locally Advanced (CCRT)"], "name": "📚 CALLA", "pharma": "AZ", "drug": "Durvalumab + CCRT", 
     "results": "陰性 (HR 0.84)。提醒需精準分流。", "rationale": "探索放化療與 IO 組合限制。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 KEYNOTE-826", "pharma": "MSD", "drug": "Pembro + Chemo ± Bev", 
     "results": "OS HR 0.63; R/M 一線標準。", "rationale": "確立持續復發性一線地位。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 BEATcc", "pharma": "Roche", "drug": "Atezo + Chemo + Bev", 
     "results": "PFS HR 0.62; OS HR 0.68.", "rationale": "一線轉移性免疫併用新路徑。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 EMPOWER-Cx 1", "pharma": "Regeneron", "drug": "Cemiplimab", 
     "results": "OS HR 0.69; mOS 12.0m.", "rationale": "二線後單藥免疫之 OS 基石。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 innovaTV 301", "pharma": "Seagen", "drug": "Tisotumab Vedotin (ADC)", 
     "results": "OS HR 0.70; ORR 17.8%.", "rationale": "首個後線 OS 獲益之 ADC。"},
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Early Stage (Surgery)"], "name": "📚 SHAPE trial", "pharma": "UCL", "drug": "Simple Hysterectomy", 
     "results": "3yr Recurrence: 2.5% vs 2.2%.", "rationale": "支持低風險早期手術降階。"},
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutated"], "name": "📚 SOLO-1", "pharma": "AZ", "drug": "Olaparib Maintenance", 
     "results": "7yr survival 67% (HR 0.33).", "rationale": "BRCAm 一線維持里程碑。"},
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive (wt)"], "name": "📚 PRIMA", "pharma": "GSK", "drug": "Niraparib Maintenance", 
     "results": "HRD+ PFS HR 0.43.", "rationale": "支持不限 BRCA 之一線維持。"},
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive (wt)"], "name": "📚 PAOLA-1", "pharma": "AZ", "drug": "Olaparib + Bevacizumab", 
     "results": "HRD+ OS HR 0.62; 5yr OS 75.2%.", "rationale": "確立組合維持黃金路徑。"},
    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], "name": "📚 NOVA / ARIEL3 / SOLO2", "pharma": "Various", "drug": "PARPi Maint", 
     "results": "SOLO2 mOS 51.7m (HR 0.74).", "rationale": "復發維持之核心實證群。"},
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive (wt)"], "name": "📚 DUO-O", "pharma": "AZ", "drug": "Durva+Chemo+Bev ->維持 3藥", 
     "results": "HRD+ PFS HR 0.49.", "rationale": "顯示組合免疫策略潛力。"},
    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PROC (Resistant Recurrence)"], "name": "📚 MIRASOL", "pharma": "ImmunoGen", "drug": "Mirvetuximab", 
     "results": "OS HR 0.67; ORR 42.3%.", "rationale": "FRα+ PROC 歷史性 OS 突破。"},
    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 van Driel HIPEC", "pharma": "NEJM 2018", "drug": "Surgery + HIPEC", 
     "results": "mOS 45.7m (HR 0.67).", "rationale": "溫熱化療改善腹膜病灶殺傷。"},
    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PSOC (Sensitive Recurrence)"], "name": "📚 DESKTOP III", "pharma": "NEJM 2021", "drug": "Secondary Surgery", 
     "results": "mOS 53.7m (HR 0.75).", "rationale": "二次手術對嚴選 PSOC 之獲益。"},
    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 LION", "pharma": "NEJM 2019", "drug": "No Lymphadenectomy", 
     "results": "OS HR 1.06.", "rationale": "臨床 LN 陰性者免清掃。"},

    # --- 📍 Ongoing Trials (8核心救回) ---
    {"cancer": "Ovarian", "name": "📍 FRAmework-01 (LY4170156)", "pharma": "Eli Lilly", "drug": "LY4170156 + Bevacizumab", "pos": "R-TX", "sub_pos": ["PROC (Resistant Recurrence)"], "type": "Ongoing",
     "rationale": "標靶 FRα ADC。搭載類微管 Payload 協同 Bev 血管調節，挑戰耐藥瓶頸。",
     "inclusion": ["FRα 表達陽性。", "最後一劑鉑類後 90–180 天內惡化 (PROC)。"],
     "exclusion": ["曾用過 Topo I ADC。", "活動性 ILD。"]},
    {"cancer": "Ovarian", "name": "📍 REJOICE-Ovarian01", "pharma": "Daiichi Sankyo", "drug": "R-DXd (CDH6 ADC)", "pos": "R-TX", "sub_pos": ["PROC (Resistant Recurrence)"], "type": "Ongoing",
     "rationale": "標靶 Cadherin-6 (CDH6) ADC。具極高 DAR (8) 與強力旁觀者效應。",
     "inclusion": ["HG Serous 或 Endometrioid PROC。", "提供切片判定 CDH6 分層。"],
     "exclusion": ["Low-grade 腫瘤。", "LVEF < 50%。"]},
    {"cancer": "Ovarian", "name": "📍 TroFuse-021", "pharma": "MSD", "drug": "Sac-TMT (MK-2870) + Bev", "pos": "P-MT", "sub_pos": ["HRD positive (wt)", "HRD negative / pHRD"], "type": "Ongoing",
     "rationale": "標靶 Trop-2 ADC。結合 Beva 微環境調節與 ADC 誘導之 ICD 效應。",
     "inclusion": ["新診斷 Stage III/IV 卵巢癌。", "一線含鉑化療後達 CR 或 PR。"]},
    {"cancer": "Endometrial", "name": "📍 MK2870-033", "pharma": "MSD", "drug": "Sac-TMT + Pembrolizumab", "pos": "P-MT", "sub_pos": ["IO Maintenance"], "type": "Ongoing",
     "rationale": "標靶 Trop-2 ADC 協同 PD-1。提升 Pembrolizumab 在 pMMR/NSMP 族群的應答深度。",
     "inclusion": ["pMMR 子宮內膜癌。", "FIGO III/IV 一線含鉑+Pembro後達 CR/PR。"]},
    {"cancer": "Endometrial", "name": "📍 GU-US-682-6769", "pharma": "Gilead", "drug": "SG (Trodelvy)", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "type": "Ongoing",
     "rationale": "標靶 Trop-2 ADC。利用 SN-38 Payload 殺傷，專攻鉑類與免疫失敗救援。",
     "inclusion": ["復發性 EC。", "鉑類與 PD-1 失敗後進展。"]},
    {"cancer": "Ovarian", "name": "📍 DS8201-772 (Enhertu)", "pharma": "AstraZeneca", "drug": "T-DXd (HER2 ADC)", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], "type": "Ongoing",
     "rationale": "標靶 HER2 ADC。救援化療穩定後精準維持，清除微小殘留病灶。",
     "inclusion": ["HER2 IHC 1+/2+/3+ 確認。", "PSOC 救援化療達穩定。"]},
    {"cancer": "Ovarian", "name": "📍 DOVE", "pharma": "GSK", "drug": "Dostarlimab + Bevacizumab", "pos": "R-TX", "sub_pos": ["PROC (Resistant Recurrence)"], "type": "Ongoing",
     "rationale": "針對 OCCC 透明細胞癌。利用雙重阻斷改善其特有免疫抑制環境。",
     "inclusion": ["組織學 OCCC > 50%。", "鉑類抗藥性 (PFI < 12m)。"]},
    {"cancer": "Cervical", "name": "📍 innovaTV 301 Access", "pharma": "Seagen", "drug": "Tisotumab Vedotin", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "type": "Ongoing",
     "rationale": "標靶 Tissue Factor ADC。旨在克服後線子宮頸癌化療耐藥性。",
     "inclusion": ["復發/轉移子宮頸癌。", "先前接受 1–2 線治療後進展。"]},
]

# --- 3. AI 動態模型巡邏與唯一鍵值邏輯 ---
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

# --- 4. 側邊欄 ---
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = all_trials_db[0]['name']

with st.sidebar:
    st.markdown("<h3 style='color: #6A1B9A;'>🤖 AI 實證媒合助理</h3>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 病歷分析", expanded=True):
        p_notes = st.text_area("輸入摘要 (含分型/標記)", height=250)
        if st.button("🚀 開始分析", key="sidebar_analyze"):
            if api_key and p_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = get_gemini_model()
                    prompt = f"分析：{p_notes}。參考實證：{all_trials_db}。建議適合路徑與理由。"
                    st.write(model.generate_content(prompt).text)
                except Exception as e: st.error(f"AI 異常: {e}")

# --- 5. 主頁面：導航地圖 ---
st.markdown("<div class='main-title'>婦癌臨床導航儀表板 (2026 旗艦實證整合版)</div>", unsafe_allow_html=True)
cancer_type = st.radio("第一步：選擇癌症類型", ["Endometrial", "Ovarian", "Cervical"], horizontal=True)

cols = st.columns(len(guidelines_nested[cancer_type]))
stages_data = guidelines_nested[cancer_type]

for i, stage in enumerate(stages_data):
    with cols[i]:
        st.markdown(f"""<div class='big-stage-card card-{stage['css']}'><div class='big-stage-header header-{stage['css']}'>{stage['header']}</div>""", unsafe_allow_html=True)
        for sub in stage['subs']:
            st.markdown(f"""<div class='sub-block'><div class='sub-block-title'>📘 {sub['title']}</div><div class='sub-block-content'>{sub['content']}</div>""", unsafe_allow_html=True)
            
            # 顯示該區塊對應的試驗 (📚 & 📍)
            rel_trials = [t for t in all_trials_db if t["cancer"] == cancer_type and t["pos"] == stage["id"] and any(s in sub["title"] for s in t["sub_pos"])]
            for t in rel_trials:
                label = f"{t.get('pharma', 'N/A')} | {t['name']} | {t['drug']}"
                with st.popover(label, use_container_width=True):
                    st.success(f"**結論/摘要:** {t.get('results', 'Ongoing')}")
                    unique_key = f"sync_{t['name']}_{cancer_type}_{stage['id']}_{sub['title'].replace(' ', '')}"
                    if st.button("📊 同步看板細節", key=unique_key):
                        st.session_state.selected_trial = t['name']
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 6. 臨床試驗深度數據庫 (Bottom Selector) ---
st.divider()
st.subheader("📋 臨床試驗深度數據庫 (請由下拉清單選擇以查閱詳細數據)")
filtered_list = [t for t in all_trials_db if t["cancer"] == cancer_type]
selected_name = st.selectbox("🎯 快速選擇研究計畫：", [t["name"] for t in filtered_list], key="trial_selector")

# 同步選中的計畫數據
t = next(it for it in all_trials_db if it["name"] == selected_name)

st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #E0E0E0; padding-bottom:10px; font-weight:900;'>📋 {t['name']} 深度分析報告</h2>", unsafe_allow_html=True)

r1, r2 = st.columns([1.3, 1])
with r1:
    st.markdown("<div style='background:#E3F2FD; border-left:10px solid #1976D2; padding:15px; border-radius:10px;'><b>💉 Rationale & Regimen (機轉與給藥)</b></div>", unsafe_allow_html=True)
    st.write(f"**核心藥物:** {t['drug']}")
    st.write(f"**詳細給藥:** {t.get('regimen', t.get('dosing', '詳見招募細則'))}")
    st.success(t.get('rationale', '該研究主要挑戰現有 SoC 瓶頸，提升存活獲益。'))
    

with r2:
    st.markdown("<div style='background:#FFF8E1; border-left:8px solid #FBC02D; padding:15px; border-radius:10px;'><b>📈 Key Outcomes (存活與緩解指標)</b></div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style='text-align:center; background:white; padding:15px; border:2px solid #FFE082; border-radius:12px;'>
            <div style='font-size: 14px; color: #795548; font-weight:700; margin-bottom:5px;'>Survival Metrics (PFS/OS/HR)</div>
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
