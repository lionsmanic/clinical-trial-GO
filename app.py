import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床導航與實證圖書館 (2026 旗艦全功能版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

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
        padding: 4px; text-align: center;
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

# --- 1. 指引導航數據庫：包含 PSOC/PROC、MOC 與全階段 ---
guidelines_nested = {
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "MMRd / MSI-H / dMMR", "content": "一線標竿：Chemo + PD-1 (RUBY/GY018/AtTEnd)。"},
            {"title": "NSMP / pMMR / MSS", "content": "一線考慮 Chemo + IO 維持 (DUO-E)。二線選標靶免疫 (KN775)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "IO Maintenance", "content": "1L Chemo-IO 後延續維持。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "Recurrent EC", "content": "二線標靶+免疫 (MSS) 或單藥 IO (GARNET)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "維持有效治療直至進展。"}]}
    ],
    "Ovarian": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "HGSC / Endometrioid", "content": "Surgery + Carbo/Pacli ± Bev。考慮 IDS + HIPEC (van Driel)。"},
            {"title": "Mucinous (MOC) 鑑別", "content": "判定：CK7+/SATB2-。1. Expansile (IA可保守)。 2. Infiltrative (建積極化療)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "BRCA mutated", "content": "Olaparib 維持 2年 (SOLO-1)。"}, {"title": "HRD positive (wt)", "content": "PAOLA-1 (Ola+Bev)、PRIMA (Nira) 或 ATHENA-MONO (Ruca)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "PSOC (Sensitive Recurrence)", "content": "PFI > 6m。評估二次手術 (DESKTOP III) 或含鉑複方化療。"},
            {"title": "PROC (Resistant Recurrence)", "content": "PFI < 6m。單藥化療 ± Bev 或 FRα ADC (MIRASOL)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Platinum Sensitive Maint", "content": "救援緩解後選 PARPi 維持 (NOVA/ARIEL3/SOLO2)。"}]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "Locally Advanced (CCRT)", "content": "CCRT ± 同步免疫 (A18) 或誘導化療 (INTERLACE)。"},
            {"title": "Early Stage (Surgery)", "content": "根治術 (LACC) 或單純切除 (SHAPE)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "Recurr / Metastatic", "content": "一線 Pembro+化療±Bev (KN826) 或 Atezo組合 (BEATcc)。二線 ADC (innovaTV 301)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "維持有效治療直至進展。"}]}
    ]
}

# --- 2. 實證資料庫 (📚 Published & 📍 Ongoing 終極整合) ---
trials_db = [
    # --- 📚 Endometrial Published ---
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H / dMMR"], "name": "📚 RUBY", "pharma": "GSK", "drug": "Dostarlimab + CP", 
     "results": "dMMR: HR 0.32; mOS 44.6m (vs 28.2m).", "rationale": "PD-1 阻斷協同化療誘導抗原。"},
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["NSMP / pMMR / MSS"], "name": "📚 NRG-GY018", "pharma": "MSD", "drug": "Pembrolizumab + CP", 
     "results": "dMMR HR 0.30; pMMR HR 0.54.", "rationale": "支持一線不論 MMR 狀態之 IO 獲益。"},
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["NSMP / pMMR / MSS"], "name": "📚 DUO-E", "pharma": "AZ", "drug": "Durvalumab + CP →維持 Durva ± Ola", 
     "results": "三藥組 PFS HR 0.57 (vs CP).", "rationale": "探索 PARPi 對 pMMR 的協同維持效應。"},
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H / dMMR"], "name": "📚 AtTEnd", "pharma": "Roche", "drug": "Atezolizumab + CP", 
     "results": "dMMR PFS HR 0.36; ITT OS HR 0.82.", "rationale": "確認 PD-L1 併化療在一線晚期之價值。"},
    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "name": "📚 KEYNOTE-775", "pharma": "MSD/Eisai", "drug": "Lenvatinib + Pembro", 
     "results": "pMMR OS HR 0.68; mOS 17.4m vs 12.0m.", "rationale": "MSS 後線標靶免疫之關鍵證據。"},
    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "name": "📚 GARNET", "pharma": "GSK", "drug": "Dostarlimab (Single-agent)", 
     "results": "dMMR ORR 45.5%.", "rationale": "奠定 MSI-H/dMMR 後線免疫地位。"},

    # --- 📚 Cervical Published ---
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Locally Advanced (CCRT)"], "name": "📚 KEYNOTE-A18", "pharma": "MSD", "drug": "Pembrolizumab + CCRT", 
     "results": "OS HR 0.67; 36m OS 82.6%.", "rationale": "將免疫正式併入局部晚期根治性 CCRT。"},
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Locally Advanced (CCRT)"], "name": "📚 INTERLACE", "pharma": "UCL", "drug": "Induction Carbo/Pacli x6 -> CCRT", 
     "results": "5yr OS 80% (vs 72%, HR 0.60).", "rationale": "老藥新用：誘導化療提升長期存活。"},
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Locally Advanced (CCRT)"], "name": "📚 CALLA (陰性)", "pharma": "AZ", "drug": "Durvalumab + CCRT", 
     "results": "PFS HR 0.84 (P=NS).", "rationale": "陰性試驗提醒分流標記重要性。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 KEYNOTE-826", "pharma": "MSD", "drug": "Pembro + Chemo ± Bev", 
     "results": "OS HR 0.63; R/M 一線標準。", "rationale": "確立持續復發性一線 IO 地位。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 BEATcc", "pharma": "Roche", "drug": "Atezo + Chemo + Bev", 
     "results": "PFS HR 0.62; OS HR 0.68.", "rationale": "提供另一個一線免疫併用方案。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 EMPOWER-Cx 1", "pharma": "Regeneron", "drug": "Cemiplimab vs Chemo", 
     "results": "OS HR 0.69; mOS 12.0m.", "rationale": "二線後單藥免疫之 OS 實證。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 innovaTV 301", "pharma": "Seagen/Genmab", "drug": "Tisotumab Vedotin vs Chemo", 
     "results": "OS HR 0.70; ORR 17.8%.", "rationale": "首個後線 OS 獲益之 ADC 試驗。"},
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Early Stage (Surgery)"], "name": "📚 SHAPE trial", "pharma": "UCL", "drug": "Simple Hysterectomy", 
     "results": "3yr Recurrence: 2.5% vs 2.2%.", "rationale": "支持低風險早期手術降階。"},

    # --- 📚 Ovarian Published ---
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutated"], "name": "📚 SOLO-1", "pharma": "AZ", "drug": "Olaparib Maintenance", 
     "results": "7yr survival 67% (HR 0.33).", "rationale": "BRCAm 一線維持里程碑研究。"},
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive (wt)", "HRD negative / pHRD"], "name": "📚 PRIMA", "pharma": "GSK", "drug": "Niraparib Maintenance", 
     "results": "HRD+ PFS HR 0.43; 全人群 PFS HR 0.62.", "rationale": "支持不限 BRCA 之一線維持。"},
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutated", "HRD positive (wt)"], "name": "📚 ATHENA-MONO", "pharma": "Clovis", "drug": "Rucaparib Maintenance", 
     "results": "ITT PFS HR 0.52.", "rationale": "擴充 PARPi 一線維持實證。"},
    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], "name": "📚 NOVA", "pharma": "GSK", "drug": "Niraparib Maintenance", 
     "results": "gBRCA HR 0.27; Non-gBRCA HR 0.45.", "rationale": "復發維持之基石研究。"},
    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], "name": "📚 ARIEL3", "pharma": "Clovis", "drug": "Rucaparib Maintenance", 
     "results": "BRCAm HR 0.23; HRD+ HR 0.32.", "rationale": "支持鉑敏復發後之維持策略。"},
    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], "name": "📚 SOLO2", "pharma": "AZ", "drug": "Olaparib Maintenance", 
     "results": "mOS 51.7m (vs 38.8m, HR 0.74).", "rationale": "BRCAm 復發維持之長期 OS 實證。"},
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive (wt)"], "name": "📚 DUO-O", "pharma": "AZ", "drug": "Durva + CP + Bev ->維持 Durva+Ola+Bev", 
     "results": "HRD+ PFS HR 0.49.", "rationale": "組合 IO, PARPi 與 VEGF 之維持優勢。"},
    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PROC (Resistant Recurrence)"], "name": "📚 MIRASOL", "pharma": "ImmunoGen", "drug": "Mirvetuximab Soravtansine", 
     "results": "OS HR 0.67; ORR 42.3%.", "rationale": "FRα 高表現 PROC 歷史突破研究。"},
    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 van Driel HIPEC", "pharma": "NEJM 2018", "drug": "Surgery + HIPEC", 
     "results": "mOS 45.7m vs 33.9m (HR 0.67).", "rationale": "IDS 時加溫熱化療改善 OS。"},
    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PSOC (Sensitive Recurrence)"], "name": "📚 DESKTOP III", "pharma": "NEJM 2021", "drug": "Secondary Surgery", 
     "results": "mOS 53.7m vs 46.0m (HR 0.75).", "rationale": "嚴選 AGO 患者二次減積具 OS 獲益。"},
    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 LION", "pharma": "NEJM 2019", "drug": "No Lymphadenectomy", 
     "results": "OS HR 1.06.", "rationale": "臨床 LN 陰性者免清掃以降併發症。"},

    # --- 📍 Ongoing Trials (8核心救回) ---
    {"cancer": "Ovarian", "name": "📍 FRAmework-01 (LY4170156)", "pharma": "Eli Lilly", "drug": "LY4170156 + Bevacizumab", "pos": "R-TX", "sub_pos": ["PROC (Resistant Recurrence)"], "type": "Ongoing",
     "rationale": "標靶 FRα ADC。搭載類微管 Payload 協同 Bev 血管調節。",
     "regimen": "LY4170156 3mg/kg IV + Bevacizumab 15mg/kg IV Q3W。",
     "inclusion": ["FRα 表達陽性。", "最後一劑鉑類後 90–180 天內惡化 (PROC)。"],
     "exclusion": ["曾用過 Topo I ADC。", "活動性 ILD。"]},
    {"cancer": "Ovarian", "name": "📍 REJOICE-Ovarian01", "pharma": "Daiichi Sankyo", "drug": "R-DXd", "pos": "R-TX", "sub_pos": ["PROC (Resistant Recurrence)"], "type": "Ongoing",
     "rationale": "標靶 Cadherin-6 (CDH6) ADC。具強力旁觀者效應。",
     "regimen": "R-DXd 5.6mg/kg IV Q3W。",
     "inclusion": ["HG Serous 或 Endometrioid PROC。", "提供切片判定 CDH6。"]},
    {"cancer": "Ovarian", "name": "📍 TroFuse-021", "pharma": "MSD", "drug": "Sac-TMT (MK-2870)", "pos": "P-MT", "sub_pos": ["HRD positive (wt)", "HRD negative / pHRD"], "type": "Ongoing",
     "rationale": "標靶 Trop-2 ADC。結合 Beva 微環境調節優化維持獲益。",
     "inclusion": ["新診斷 FIGO Stage III/IV 卵巢癌。", "一線含鉑化療後達 CR 或 PR。"]},
]

# --- 3. AI 模型選擇器 ---
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
    st.session_state.selected_trial = trials_db[0]['name']

with st.sidebar:
    st.markdown("<h3 style='color: #6A1B9A;'>🤖 AI 實證媒合助理</h3>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 病歷數據比對", expanded=True):
        p_notes = st.text_area("輸入摘要 (含細胞型態/標記)", height=250)
        if st.button("🚀 開始分析", key="sidebar_analyze"):
            if api_key and p_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = get_gemini_model()
                    prompt = f"分析病歷：{p_notes}。參考實證：{trials_db}。提供路徑建議與理由。"
                    st.write(model.generate_content(prompt).text)
                except Exception as e: st.error(f"AI 異常: {e}")

# --- 5. 主頁面：導航地圖 ---
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
            rel_trials = [t for t in trials_db if t["cancer"] == cancer_type and t["pos"] == stage["id"] and any(s in sub["title"] for s in t["sub_pos"])]
            for t in rel_trials:
                with st.popover(t["name"], use_container_width=True):
                    st.success(f"**介入:** {t['drug']}\n\n**重要結論:** {t.get('results', 'Ongoing')}")
                    unique_key = f"sync_{t['name']}_{cancer_type}_{stage['id']}_{sub['title'].replace(' ', '')}"
                    if st.button("📊 同步看板細節", key=unique_key):
                        st.session_state.selected_trial = t['name']
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 6. 臨床試驗深度數據庫 (Bottom Selector) ---
st.divider()
st.subheader("📋 臨床試驗深度數據庫 (點選以查閱詳細 Dosing/Criteria 與生存數據)")
filtered_list = [t for t in trials_db if t["cancer"] == cancer_type]
selected_name = st.selectbox("🎯 快速選擇研究計畫：", [t["name"] for t in filtered_list], key="trial_selector")

# 同步選中的計畫數據
t = next(it for it in trials_db if it["name"] == selected_name)

st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #E0E0E0; padding-bottom:10px; font-weight:900;'>📋 {t['name']} 深度分析報告</h2>", unsafe_allow_html=True)

r1, r2 = st.columns([1.3, 1])
with r1:
    st.markdown("<div style='background:#E3F2FD; border-left:10px solid #1976D2; padding:15px; border-radius:10px;'><b>💉 Rationale & Regimen (機轉與給藥)</b></div>", unsafe_allow_html=True)
    st.write(f"**藥廠:** {t.get('pharma', 'N/A')}")
    st.write(f"**核心介入:** {t['drug']}")
    st.write(f"**詳細給藥:** {t.get('regimen', t.get('dosing', '詳見 Protocol'))}")
    st.success(t.get('rationale', '該研究主要針對特定分子分型，透過前沿標靶或免疫機制挑戰現有 SoC。'))
    

with r2:
    st.markdown("<div style='background:#FFF8E1; border-left:8px solid #FBC02D; padding:15px; border-radius:10px;'><b>📈 Key Evidence (存活與緩解數據)</b></div>", unsafe_allow_html=True)
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
