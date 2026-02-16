import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床導航與實證圖書館 (2026 旗艦終極整合版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

# 初始化 session_state
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = "📚 RUBY"

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=Roboto:wght@400;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', 'Roboto', sans-serif;
        background-color: #F4F7F9; color: #1A1A1A;
        font-size: 19px !important; line-height: 1.1;
    }

    .main-title {
        font-size: 32px !important; font-weight: 900; color: #004D40;
        padding: 5px 0; border-bottom: 3px solid #4DB6AC; margin-bottom: 5px;
    }

    /* 階段方塊：深色漸層背景確保對比度 (圖一修復) */
    .big-stage-card {
        border-radius: 10px; padding: 0px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: 2px solid transparent; background: white; margin-bottom: 4px; overflow: hidden;
    }
    .big-stage-header {
        font-size: 18px !important; font-weight: 900; color: white !important;
        padding: 8px; text-align: center; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }

    .card-p-tx { border-color: #1B5E20; }
    .header-p-tx { background: linear-gradient(135deg, #2E7D32, #1B5E20); }
    .card-p-mt { border-color: #0D47A1; }
    .header-p-mt { background: linear-gradient(135deg, #1565C0, #0D47A1); }
    .card-r-tx { border-color: #E65100; }
    .header-r-tx { background: linear-gradient(135deg, #EF6C00, #BF360C); }
    .card-r-mt { border-color: #4A148C; }
    .header-r-mt { background: linear-gradient(135deg, #6A1B9A, #4A148C); }

    .sub-block {
        margin: 2px 4px; padding: 4px; border-radius: 6px; 
        background: #F8F9FA; border-left: 5px solid #455A64;
    }
    .sub-block-title {
        font-size: 14px; font-weight: 900; color: #263238;
        margin-bottom: 1px; border-bottom: 1.1px solid #CFD8DC; padding-bottom: 1px;
    }

    .stPopover button { 
        font-weight: 900 !important; font-size: 11px !important; 
        border-radius: 4px !important; margin-top: 1px !important;
        padding: 1px 6px !important; width: 100% !important; 
        text-align: left !important; color: #1A1A1A !important; 
        border: 1px solid rgba(0,0,0,0.15) !important;
    }
    
    .stPopover button[aria-label*="📚"] { background: #ECEFF1 !important; border-left: 5px solid #455A64 !important; }
    .stPopover button[aria-label*="📍"] { background: #E1F5FE !important; border-left: 5px solid #0288D1 !important; } 

    .detail-section { background: white; border-radius: 18px; padding: 25px; border: 1px solid #CFD8DC; box-shadow: 0 10px 40px rgba(0,0,0,0.05); }
    .hr-big-val { font-family: 'Roboto', sans-serif; font-size: 38px !important; font-weight: 900; color: #D84315; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 指引數據庫：包含全分型與階段救援 ---
guidelines_nested = {
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "dMMR / MSI-H", "content": "一線標竿：Chemo + PD-1 (RUBY/GY018/AtTEnd)。"},
            {"title": "pMMR / NSMP", "content": "一線加維持 (DUO-E)。二線選標靶免疫 (KN775)。"},
            {"title": "POLE / p53 mut", "content": "POLE: 最佳預後；p53: 最差需積極化放療。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Maintenance", "content": "延續一線使用的免疫藥物 (MK2870-033/DUO-E)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "Recurrent EC", "content": "標準：標靶+免疫 (KN775) 或單藥 IO (GARNET/SG)。"}]}
    ],
    "Ovarian": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "HGSC / Endometrioid", "content": "PDS/IDS + Carbo/Pacli ± Bev。IDS 考慮加 HIPEC (van Driel)。"},
            {"title": "Mucinous (MOC)", "content": "判定：CK7+/SATB2-。IA可保守，侵襲性需化療。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "BRCA / HRD / pHRD", "content": "SOLO-1, PRIMA, PAOLA-1, DUO-O, DS8201。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "PSOC (Sensitive)", "content": "PFI > 6m。評估二次手術 (DESKTOP III) 或 PARPi。"},
            {"title": "PROC (Resistant)", "content": "PFI < 6m。單藥化療 ± Bev 或標靶 ADC (MIRASOL)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "PARPi Maint", "content": "救援緩解後續用 PARPi (NOVA/ARIEL3/SOLO2)。"}]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "Locally Advanced", "content": "CCRT ± 同步 IO (A18) 或 誘導化療 (INTERLACE)。"},
            {"title": "Early Stage", "content": "根治術 (LACC) 或單純切除 (SHAPE)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Maintenance", "content": "1L 方案後接續維持 (KN826)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "Recurr / Metastatic", "content": "一線 KN826/BEATcc。二線 ADC (innovaTV) 或 IO。"}]}
    ]
}

# --- 2. 綜合實證資料庫 (33項極量化) ---
all_trials_db = [
    # --- Endometrial Published ---
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["dMMR / MSI-H"], "name": "📚 RUBY", "pharma": "GSK", "drug": "Dostarlimab + CP", 
     "results": "dMMR HR 0.32; mOS 44.6m (vs 28.2m).", 
     "rationale": "透過 PD-1 阻斷與含鉑化療具協同 ICD 效應，針對 MMRd 族群達到持久應答。",
     "regimen": "Dosta 500mg Q3W + CP x6週期 -> 維持 1000mg Q6W 最長 3年。",
     "inclusion": ["新診斷 Stage III-IV 或首次復發 EC。", "包含 Carcinosarcoma 型態。"],
     "exclusion": ["先前接受過系統抗癌治療。", "活動性自體免疫疾病。"]},

    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["dMMR / MSI-H", "pMMR / NSMP"], "name": "📚 NRG-GY018", "pharma": "MSD", "drug": "Pembrolizumab + CP", 
     "results": "dMMR PFS HR 0.30; pMMR HR 0.54.", 
     "rationale": "支持一線不論 MMR 狀態之免疫介入生存獲益。"},

    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["pMMR / NSMP"], "name": "📚 DUO-E", "pharma": "AZ", "drug": "Durvalumab + CP →維持 ± Ola", 
     "results": "三藥組 PFS HR 0.57; 單藥維持 HR 0.71.", 
     "rationale": "探索 PARPi 與 ICI 在 pMMR 族群維持階段之協同價值。"},

    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["dMMR / MSI-H"], "name": "📚 AtTEnd", "pharma": "Roche", "drug": "Atezolizumab + CP", 
     "results": "dMMR PFS HR 0.36; ITT OS HR 0.82."},

    {"cancer": "Endometrial", "pos": "Recurrent EC", "sub_pos": ["Recurrent EC"], "name": "📚 KEYNOTE-775", "pharma": "MSD/Eisai", "drug": "Lenvatinib + Pembro", 
     "results": "pMMR OS HR 0.68; mOS 17.4m (vs 12.0m)."},

    {"cancer": "Endometrial", "pos": "Recurrent EC", "sub_pos": ["Recurrent EC"], "name": "📚 GARNET", "pharma": "GSK", "drug": "Dostarlimab (Single)", 
     "results": "dMMR ORR 45.5%; DOR 未達到。"},

    # --- Cervical Published ---
    {"cancer": "Cervical", "pos": "Locally Advanced", "sub_pos": ["Locally Advanced"], "name": "📚 KEYNOTE-A18", "pharma": "MSD", "drug": "Pembrolizumab + CCRT", 
     "results": "OS HR 0.67; 36m OS 82.6%."},

    {"cancer": "Cervical", "pos": "Locally Advanced", "sub_pos": ["Locally Advanced"], "name": "📚 INTERLACE", "pharma": "UCL", "drug": "Induction Carbo/Pacli x6", 
     "results": "5yr OS 80% (vs 72%, HR 0.60)."},

    {"cancer": "Cervical", "pos": "Locally Advanced", "sub_pos": ["Locally Advanced"], "name": "📚 CALLA", "pharma": "AZ", "drug": "Durvalumab + CCRT", 
     "results": "PFS HR 0.84 (P=NS)。"},

    {"cancer": "Cervical", "pos": "Recurr / Metastatic", "sub_pos": ["Recurr / Metastatic"], "name": "📚 KEYNOTE-826", "pharma": "MSD", "drug": "Pembro + Chemo ± Bev", 
     "results": "OS HR 0.63; CPS≥1 HR 0.60."},

    {"cancer": "Cervical", "pos": "Recurr / Metastatic", "sub_pos": ["Recurr / Metastatic"], "name": "📚 BEATcc", "pharma": "Roche", "drug": "Atezo + Chemo + Bev", 
     "results": "PFS HR 0.62; OS HR 0.68."},

    {"cancer": "Cervical", "pos": "Recurr / Metastatic", "sub_pos": ["Recurr / Metastatic"], "name": "📚 EMPOWER-Cx 1", "pharma": "Regeneron", "drug": "Cemiplimab", 
     "results": "OS HR 0.69; mOS 12.0m vs 8.5m."},

    {"cancer": "Cervical", "pos": "Recurr / Metastatic", "sub_pos": ["Recurr / Metastatic"], "name": "📚 innovaTV 301", "pharma": "Genmab", "drug": "Tisotumab Vedotin (ADC)", 
     "results": "OS HR 0.70; ORR 17.8% (vs 5.2%)."},

    {"cancer": "Cervical", "pos": "Early Stage", "sub_pos": ["Early Stage"], "name": "📚 SHAPE trial", "pharma": "CCTG", "drug": "Simple Hysterectomy", 
     "results": "3yr Recurrence: 2.5% vs 2.2% (HR 1.0)."},

    # --- Ovarian Published ---
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutation"], "name": "📚 SOLO-1", "pharma": "AZ", "drug": "Olaparib Maint", 
     "results": "7yr survival 67% (HR 0.33)."},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive / BRCA wt", "HRD negative"], "name": "📚 PRIMA", "pharma": "GSK", "drug": "Niraparib Maint", 
     "results": "HRD+ PFS HR 0.43; 全人群 HR 0.62."},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive / BRCA wt"], "name": "📚 PAOLA-1", "pharma": "AZ", "drug": "Olaparib + Bevacizumab", 
     "results": "HRD+ OS HR 0.62; 5yr OS 75.2%。"},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutation", "HRD positive / BRCA wt"], "name": "📚 ATHENA–MONO", "pharma": "Clovis", "drug": "Rucaparib Maint", 
     "results": "ITT PFS HR 0.52."},

    {"cancer": "Ovarian", "pos": "PARPi Maint", "sub_pos": ["PARPi Maint"], "name": "📚 NOVA / ARIEL3 / SOLO2", "pharma": "Various", "drug": "PARPi 復發維持", 
     "results": "SOLO2 mOS 51.7m (HR 0.74)."},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive / BRCA wt"], "name": "📚 DUO-O", "pharma": "AZ", "drug": "Durva+Ola+Bev 維持", 
     "results": "HRD+ PFS HR 0.49."},

    {"cancer": "Ovarian", "pos": "PROC (Resistant)", "sub_pos": ["PROC (Resistant)"], "name": "📚 MIRASOL", "pharma": "ImmunoGen", "drug": "Mirvetuximab", 
     "results": "OS HR 0.67; ORR 42.3%。"},

    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 HIPEC (van Driel)", "pharma": "NEJM 2018", "drug": "Surgery + HIPEC", 
     "results": "mOS 45.7m vs 33.9m (HR 0.67)."},

    {"cancer": "Ovarian", "pos": "PSOC (Sensitive)", "sub_pos": ["PSOC (Sensitive)"], "name": "📚 DESKTOP III", "pharma": "NEJM 2021", "drug": "Secondary Surgery", 
     "results": "mOS 53.7m (vs 46.0m, HR 0.75)."},

    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 LION", "pharma": "NEJM 2019", "drug": "No Lymphadenectomy", 
     "results": "OS HR 1.06."},

    # --- 📍 Ongoing Trials (救援 8 核心) ---
    {"cancer": "Ovarian", "name": "📍 FRAmework-01", "pharma": "Eli Lilly", "drug": "LY4170156 + Bevacizumab", "pos": "PROC (Resistant)", "sub_pos": ["PROC (Resistant)", "PSOC (Sensitive)"], "type": "Ongoing",
     "rationale": "標靶 FRα ADC 聯用 anti-VEGF 提升滲透挑戰耐藥。",
     "inclusion": ["FRα 表達陽性。", "最後鉑類後進展之 PROC/PSOC。"]},

    {"cancer": "Ovarian", "name": "📍 REJOICE-Ovarian01", "pharma": "Daiichi Sankyo", "drug": "R-DXd", "pos": "PROC (Resistant)", "sub_pos": ["PROC (Resistant)"], "type": "Ongoing",
     "rationale": "標靶 CDH6 ADC，具強力旁觀者效應挑戰異質性 PROC。"},

    {"cancer": "Endometrial", "name": "📍 MK2870-033", "pharma": "MSD", "drug": "Sac-TMT + Pembrolizumab", "pos": "P-MT", "sub_pos": ["Maintenance"], "type": "Ongoing",
     "rationale": "標靶 Trop-2 ADC 協同 PD-1。提升 Pembro 在 pMMR 族群應答。"},

    {"cancer": "Endometrial", "name": "📍 GU-US-682-6769", "pharma": "Gilead", "drug": "SG (Trodelvy)", "pos": "Recurrent EC", "sub_pos": ["Recurrent EC"], "type": "Ongoing",
     "rationale": "標靶 Trop-2 ADC 利用 SN-38 載荷對抗鉑類與免疫失敗。"},

    {"cancer": "Ovarian", "name": "📍 DS8201-772 (Enhertu)", "pharma": "AstraZeneca", "drug": "T-DXd", "pos": "P-MT", "sub_pos": ["BRCA / HRD path"], "type": "Ongoing",
     "rationale": "標靶 HER2 ADC 用於一線維持，清除微小殘留病灶。"},

    {"cancer": "Ovarian", "name": "📍 DOVE", "pharma": "GSK", "drug": "Dostarlimab + Bevacizumab", "pos": "PROC (Resistant)", "sub_pos": ["PROC (Resistant)"], "type": "Ongoing",
     "rationale": "針對 OCCC 透明細胞癌利用雙重阻斷改善微環境。"},
]

# --- 3. AI 模型巡邏 ---
def get_gemini_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target_model = next((m for m in available_models if 'gemini-1.5-flash' in m), None)
        if not target_model: target_model = next((m for m in available_models if 'gemini-pro' in m), None)
        if target_model: return genai.GenerativeModel(target_model)
    except: return None

# --- 4. 側邊欄：患者分析與 AI ---
with st.sidebar:
    st.markdown("<h3 style='color: #6A1B9A;'>🤖 AI 實證媒合助理</h3>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 患者數據深度分析", expanded=True):
        p_notes = st.text_area("輸入摘要 (含分期/細胞/標記)", placeholder="例如：EC III期, p53 mutation...", height=220)
        if st.button("🚀 開始媒合"):
            if api_key and p_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = get_gemini_model()
                    prompt = f"分析病歷：{p_notes}。參考：{all_trials_db}。建議適合路徑與理由。"
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
            rel_trials = [t for t in all_trials_db if t["cancer"] == cancer_type and t["pos"] == stage["id"] and any(s in sub["title"] for s in t["sub_pos"])]
            for t in rel_trials:
                label = f"{t.get('pharma', 'N/A')} | {t['name']} | {t['drug']}"
                with st.popover(label, use_container_width=True):
                    st.success(f"**核心摘要:** {t.get('results', '招募中')}")
                    unique_key = f"sync_{t['name']}_{cancer_type}_{stage['id']}_{sub['title'].replace(' ', '')}"
                    if st.button("📊 同步看板細節", key=unique_key):
                        st.session_state.selected_trial = t['name']
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 6. 深度數據看板 (Bottom Selector) ---
st.divider()
st.subheader("📋 臨床研究極量化數據庫 (Published Milestones & Ongoing Trials)")
filtered_list = [t for t in all_trials_db if t["cancer"] == cancer_type]
try: curr_idx = [t["name"] for t in filtered_list].index(st.session_state.selected_trial)
except: curr_idx = 0

selected_name = st.selectbox("🎯 快速選擇研究計畫：", [t["name"] for t in filtered_list], index=curr_idx, key="trial_selector")
st.session_state.selected_trial = selected_name
t = next(it for it in all_trials_db if it["name"] == selected_name)

st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #E0E0E0; padding-bottom:10px; font-weight:900;'>📋 {t['name']} 深度分析報告</h2>", unsafe_allow_html=True)

r1, r2 = st.columns([1.3, 1])
with r1:
    st.markdown("<div style='background:#E3F2FD; border-left:10px solid #1976D2; padding:15px; border-radius:10px;'><b>💉 Rationale & Regimen (機轉與給藥)</b></div>", unsafe_allow_html=True)
    st.write(f"**核心介入藥物:** {t['drug']}")
    st.write(f"**詳細給藥方案 (Dosing Protocol):** {t.get('regimen', '請查閱招募 Protocol 規定。')}")
    st.success(f"**科學理據 (Scientific Rationale):** {t['rationale']}")
    

with r2:
    st.markdown("<div style='background:#FFF8E1; border-left:8px solid #FBC02D; padding:15px; border-radius:10px;'><b>📈 Key Evidence (生存與緩解數據)</b></div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style='text-align:center; background:white; padding:15px; border:2px solid #FFE082; border-radius:12px;'>
            <div style='font-size: 14px; color: #795548; font-weight:700; margin-bottom:5px;'>Survival Metrics (PFS/OS/HR/ORR)</div>
            <div class='hr-big-val'>{t.get('results', 'Ongoing')}</div>
        </div>
    """, unsafe_allow_html=True)
    

st.divider()
r3, r4 = st.columns(2)
with r3:
    st.markdown("<div style='background:#E8F5E9; border-left:8px solid #2E7D32; padding:15px; border-radius:10px;'><b>✅ Inclusion Criteria (關鍵納入標準)</b></div>", unsafe_allow_html=True)
    for inc in t.get('inclusion', ['符合特定分子標記。']): st.write(f"• **{inc}**")
with r4:
    st.markdown("<div style='background:#FFEBEE; border-left:8px solid #C62828; padding:15px; border-radius:10px;'><b>❌ Exclusion Criteria (關鍵排除標準)</b></div>", unsafe_allow_html=True)
    for exc in t.get('exclusion', ['排除活動性自體免疫疾病或顯著功能異常。']): st.write(f"• **{exc}**")
st.markdown("</div>", unsafe_allow_html=True)
