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

    /* 大階段方塊：零留白設計 */
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
    .stPopover button[aria-label*="📍"] { background: #E3F2FD !important; border-left: 5px solid #1976D2 !important; } 

    .detail-section { background: white; border-radius: 18px; padding: 25px; border: 1px solid #CFD8DC; box-shadow: 0 10px 40px rgba(0,0,0,0.05); }
    .hr-big-val { font-family: 'Roboto', sans-serif; font-size: 45px !important; font-weight: 900; color: #D84315; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 指引導航數據庫：包含全癌症階段、MOC 與 PSOC/PROC 分流 ---
guidelines_nested = {
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "MMRd / MSI-H / dMMR", "content": "一線標竿：Chemo + PD-1 (GY018/RUBY)。Dostarlimab 獲益極顯著。"},
            {"title": "NSMP / pMMR / MSS", "content": "排除分型。視 ER/Grade 權重決策；二線考慮 Pembro+Lenva。"},
            {"title": "POLEmut / p53abn", "content": "POLE: 最佳預後；p53: 最差預後，需積極輔助治療。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "IO Maintenance", "content": "一線 IO 治療後接續維持直到疾病進展 (PD)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "Recurrent EC", "content": "二線方案：標靶+免疫 (pMMR) 或 IO 單藥 (MMRd/GARNET)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "維持有效治療直到不可耐受或進展。"}]}
    ],
    "Ovarian": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "HGSC / Endometrioid", "content": "手術 (PDS/IDS) + Carboplatin/Paclitaxel ± Bevacizumab。"},
            {"title": "Mucinous (MOC) 鑑別", "content": "判定：CK7+/SATB2- (原發)。1. Expansile: 預後佳。 2. Infiltrative: 高復發風險，建議積極化療。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "BRCA mutated", "content": "Olaparib 單藥維持 2年。"}, {"title": "HRD positive (wt)", "content": "Olaparib+Bev (2年) 或 Niraparib 單藥 (3年)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "PSOC (Sensitive Recurrence)", "content": "PFI > 6m。含鉑雙藥 ± Bev。評估二次手術 (DESKTOP III)。"},
            {"title": "PROC (Resistant Recurrence)", "content": "PFI < 6m。單藥化療 ± Bev 或標靶 ADC (MIRASOL/FRAmework)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Platinum Sensitive Maint", "content": "救援緩解後續以 PARPi 維持治療。"}]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "CCRT (Locally Advanced)", "content": "同步化放療。高風險者同步 IO (A18) 或誘導化療 (INTERLACE)。"},
            {"title": "Early Stage (Surgery)", "content": "根治性開腹術 (LACC)。低風險者選單純切除 (SHAPE)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Metastatic Maint", "content": "1L 轉移性 IO 方案後延續維持至進展。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "Recurr / Metastatic", "content": "一線 Pembro + 化療 ± Bev。二線 ADC (Tivdak) 或 IO (EMPOWER)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "維持有效治療直到進展。"}]}
    ]
}

# --- 2. 綜合試驗資料庫 (25 里程碑 + 8 招募中) ---
all_trials_db = [
    # --- 📚 Published Milestones ---
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H / dMMR"], "name": "📚 RUBY", "type": "Milestone", "drug": "Dostarlimab + CP", 
     "rationale": "透過 PD-1 阻斷釋放免疫制動，針對 MMRd 族群達到持久應答。",
     "regimen": "Induction: Dostarlimab 500mg Q3W + CP x6 -> Maint: Dostarlimab 1000mg Q6W 最長 3年。",
     "inclusion": ["FIGO III-IV 期晚期或首次復發 EC。", "包含 Carcinosarcoma / Serous 等。"],
     "exclusion": ["先前接受過系統性抗癌治療。", "活動性自體免疫疾病。"],
     "results": "dMMR: HR 0.32; mOS 44.6m (vs 28.2m)."},
    
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H / dMMR", "NSMP / pMMR / MSS"], "name": "📚 NRG-GY018", "type": "Milestone", "drug": "Pembrolizumab + CP", 
     "regimen": "Pembro 200mg Q3W + CP x6 -> 維持 400mg Q6W 最長 2年。",
     "results": "dMMR PFS HR 0.30; pMMR PFS HR 0.54."},

    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H / dMMR"], "name": "📚 AtTEnd", "type": "Milestone", "drug": "Atezolizumab + CP", 
     "results": "dMMR PFS HR 0.36; ITT OS HR 0.82 (P=0.048)."},

    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "name": "📚 KEYNOTE-775", "type": "Milestone", "drug": "Lenvatinib + Pembro", 
     "results": "pMMR OS HR 0.68; mOS 17.4m vs 12.0m."},

    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["CCRT (Locally Advanced)"], "name": "📚 KEYNOTE-A18", "type": "Milestone", "drug": "Pembrolizumab + CCRT", 
     "results": "OS HR 0.67; 36m OS 82.6%."},

    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["CCRT (Locally Advanced)"], "name": "📚 CALLA", "type": "Milestone", "drug": "Durvalumab + CCRT", 
     "results": "整體陰性 (HR 0.84)。提醒需更精準分流。"},

    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 KEYNOTE-826", "type": "Milestone", "drug": "Pembro + 化療 ± Bev", 
     "results": "OS HR 0.63 (ITT); HR 0.60 (CPS≥1)."},

    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 BEATcc", "type": "Milestone", "drug": "Atezo + Chemo + Bev", 
     "results": "PFS HR 0.62; OS HR 0.68."},

    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 EMPOWER-Cx 1", "type": "Milestone", "drug": "Cemiplimab", 
     "results": "OS HR 0.69; mOS 12.0m vs 8.5m."},

    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 innovaTV 301", "type": "Milestone", "drug": "Tisotumab Vedotin", 
     "results": "OS 11.5m vs 9.5m (HR 0.70); ORR 17.8%."},

    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Early Stage (Surgery)"], "name": "📚 SHAPE trial", "type": "Milestone", "drug": "Simple Hysterectomy", 
     "results": "3yr Pelvic Recurrence: 2.5% vs 2.2%. 支持降階。"},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive (wt)"], "name": "📚 PAOLA-1", "type": "Milestone", "drug": "Olaparib + Bevacizumab", 
     "results": "HRD+ OS HR 0.62; 5yr OS 75.2%."},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutated", "HRD positive (wt)"], "name": "📚 ATHENA–MONO", "type": "Milestone", "drug": "Rucaparib", 
     "results": "ITT PFS HR 0.52 (28.7m vs 11.3m)."},

    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], "name": "📚 NOVA", "type": "Milestone", "drug": "Niraparib 維持", 
     "results": "gBRCA HR 0.27; Non-gBRCA HR 0.45."},

    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], "name": "📚 ARIEL3", "type": "Milestone", "drug": "Rucaparib 維持", 
     "results": "BRCAm HR 0.23; HRD+ HR 0.32."},

    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], "name": "📚 SOLO2", "type": "Milestone", "drug": "Olaparib (BRCA)", 
     "results": "mOS 51.7m vs 38.8m; HR 0.74."},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive (wt)"], "name": "📚 DUO-O", "type": "Milestone", "drug": "Durva+Ola+Bev", 
     "results": "HRD+ PFS HR 0.49."},

    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 LION (NEJM 2019)", "type": "Milestone", "drug": "No Lymphadenectomy", 
     "results": "OS HR 1.06. 支持 LN 陰性免清掃。"},

    # --- 📍 Ongoing Trials ---
    {"cancer": "Ovarian", "name": "📍 FRAmework-01 (LY4170156)", "pharma": "Eli Lilly", "drug": "LY4170156 + Bevacizumab", "pos": "R-TX", "sub_pos": ["PROC (Resistant Recurrence)"], "type": "Ongoing",
     "rationale": "標靶 FRα ADC。聯用 Bevacizumab 提升藥物滲透並透過旁觀者效應殺傷低表達細胞。",
     "regimen": "LY4170156 3mg/kg IV + Bevacizumab 15mg/kg IV Q3W。",
     "inclusion": ["中央實驗室確認 FRα 表達陽性。", "最後一劑鉑類後 90–180 天內惡化 (PROC)。"],
     "exclusion": ["曾用過 Topo I ADC (Enhertu)。", "活動性間質性肺病 (ILD)。"], "results": "Ongoing (NCT06536348)."},

    {"cancer": "Ovarian", "name": "📍 REJOICE-Ovarian01", "pharma": "Daiichi Sankyo", "drug": "R-DXd", "pos": "R-TX", "sub_pos": ["PROC (Resistant Recurrence)"], "type": "Ongoing",
     "rationale": "標靶 Cadherin-6 (CDH6) ADC，具強力旁觀者效應，專攻異質性 PROC。",
     "regimen": "R-DXd 5.6mg/kg IV Q3W。",
     "inclusion": ["HG Serous 或 Endometrioid PROC。", "提供切片進行 CDH6 分層判定。"],
     "exclusion": ["Low-grade 腫瘤。", "LVEF < 50%。"], "results": "Phase 3 recruitment ongoing."},

    {"cancer": "Ovarian", "name": "📍 TroFuse-021", "pharma": "MSD", "drug": "Sac-TMT (MK-2870)", "pos": "P-MT", "sub_pos": ["HRD positive (wt)", "HRD negative / pHRD"], "type": "Ongoing",
     "rationale": "標靶 Trop-2 ADC。結合 Beva 微環境調節，優化維持獲益。",
     "regimen": "Sac-TMT 5mg/kg Q3W + Bevacizumab 15mg/kg Q3W。",
     "inclusion": ["新診斷 FIGO Stage III/IV 卵巢癌。", "一線含鉑化療後達 CR 或 PR。"],
     "exclusion": ["BRCA 變異者。", "先前用過 Trop-2 ADC。"], "results": "Phase 3 ongoing."},

    {"cancer": "Endometrial", "name": "📍 MK2870-033", "pharma": "MSD", "drug": "Sac-TMT + Pembrolizumab", "pos": "P-MT", "sub_pos": ["IO Maintenance"], "type": "Ongoing",
     "rationale": "標靶 Trop-2 ADC 協同 PD-1。透過免疫重塑提升 Pembro 在 pMMR 族群應答。",
     "regimen": "Pembro 400mg Q6W + Sac-TMT 5mg/kg Q6W。",
     "inclusion": ["pMMR 子宮內膜癌 (中心檢測)。", "FIGO III/IV 一線含鉑+Pembro後達 CR/PR。"],
     "exclusion": ["子宮肉瘤 (Sarcoma)。"], "results": "Phase 3 recruiting."},
]

# --- 4. 動態模型巡邏與 AI 修復 ---
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
    st.session_state.selected_trial = all_trials_db[0]['name']

with st.sidebar:
    st.markdown("<h3 style='color: #6A1B9A;'>🤖 AI 實證決策助理</h3>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 病歷數據比對", expanded=True):
        p_notes = st.text_area("輸入病歷 (細胞型態/標記)", height=250)
        if st.button("🚀 開始分析"):
            if api_key and p_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = get_gemini_model()
                    if model:
                        prompt = f"分析病歷：{p_notes}。參考實證：{all_trials_db}。建議適合路徑與理由。"
                        st.write(model.generate_content(prompt).text)
                    else: st.error("找不到可用 AI。")
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
            
            # 顯示該區塊對應的所有試驗 (📚 & 📍)
            rel_trials = [t for t in all_trials_db if t["cancer"] == cancer_type and t["pos"] == stage["id"] and any(s in sub["title"] for s in t["sub_pos"])]
            for t in rel_trials:
                label = t["name"] if t["type"] == "Milestone" else t["name"]
                with st.popover(label, use_container_width=True):
                    st.success(f"**介入:** {t['drug']}\n\n**結論摘要:** {t.get('results', '詳見報告')}")
                    if st.button("📊 同步看板細節", key=f"sync_{t['name']}_{stage['id']}"):
                        st.session_state.selected_trial = t['name']
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 7. 臨床試驗深度數據庫 (選擇器與清單) ---
st.divider()
st.subheader("📋 臨床研究深度數據庫 (Published Milestones & Ongoing Trials)")
filtered_list = [t for t in all_trials_db if t["cancer"] == cancer_type]
selected_name = st.selectbox("🎯 快速點選研究計畫：", [t["name"] for t in filtered_list], key="trial_selector")

# 同步選中的計畫數據
t = next(it for it in all_trials_db if it["name"] == selected_name)

st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #E0E0E0; padding-bottom:10px; font-weight:900;'>📋 {t['name']} 深度分析報告</h2>", unsafe_allow_html=True)

r1, r2 = st.columns([1.3, 1])
with r1:
    st.markdown("<div style='background:#E3F2FD; border-left:10px solid #1976D2; padding:15px; border-radius:10px;'><b>💉 Rationale & Regimen (機轉與給藥)</b></div>", unsafe_allow_html=True)
    st.write(f"**核心藥物/方案:** {t['drug']}")
    st.write(f"**詳細給藥:** {t.get('regimen', t.get('dosing', '詳見招募細則'))}")
    st.success(t.get('rationale', '該研究機轉主要透過前沿標靶或免疫調節挑戰現有 SoC。'))
    

with r2:
    st.markdown("<div style='background:#FFF8E1; border-left:8px solid #FBC02D; padding:15px; border-radius:10px;'><b>📈 Key Evidence (生存與緩解數據)</b></div>", unsafe_allow_html=True)
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
