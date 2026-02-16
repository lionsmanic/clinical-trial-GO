import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床導航與實證圖書館 (2026 旗艦最終整合版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

# 初始化 session_state
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = "📚 RUBY"

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=Roboto:wght@400;700;900&display=swap');
    
    /* === UI 高對比度與緊緻化 === */
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
    .header-p-tx { background: linear-gradient(135deg, #2E7D32, #1B5E20); } /* 深綠 */
    .card-p-mt { border-color: #0D47A1; }
    .header-p-mt { background: linear-gradient(135deg, #1565C0, #0D47A1); } /* 深藍 */
    .card-r-tx { border-color: #E65100; }
    .header-r-tx { background: linear-gradient(135deg, #EF6C00, #BF360C); } /* 深橘紅 */
    .card-r-mt { border-color: #4A148C; }
    .header-r-mt { background: linear-gradient(135deg, #6A1B9A, #4A148C); } /* 深紫 */

    .sub-block {
        margin: 2px 4px; padding: 4px; border-radius: 6px; 
        background: #F8F9FA; border-left: 5px solid #455A64;
    }
    .sub-block-title {
        font-size: 14px; font-weight: 900; color: #263238;
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

# --- 1. 指引導航數據庫：全階段、MOC、PSOC/PROC 與 復發維持救援 ---
guidelines_nested = {
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "dMMR / MSI-H", "content": "一線首選方案：含鉑化療 + PD-1 抑制劑 (RUBY/GY018/AtTEnd)。"},
            {"title": "pMMR / NSMP", "content": "預後取決於 ER/Grade。一線化療加維持 (DUO-E)。二線標靶免疫 (KN775)。"},
            {"title": "POLE mutation", "content": "預後極佳。早期可考慮治療降階 (De-escalation) 以降低併發症。"},
            {"title": "p53 mutation", "content": "侵襲性最強。建議化放療積極介入。Serous 型需驗 HER2。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Maintenance Therapy", "content": "一線 IO 治療後延續維持直到疾病進展 (PD)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "Recurrent EC", "content": "標準二線：Pembro + Lenva (MSS) 或單藥 IO (GARNET)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "救援治療後維持當前有效方案直至進展。"}]}
    ],
    "Ovarian": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "HGSC / Endometrioid", "content": "手術 (PDS/IDS) + Carbo/Pacli ± Bev。IDS 加 HIPEC (van Driel)。"},
            {"title": "Mucinous (MOC) 鑑定", "content": "判定：CK7+/SATB2- (原發)。IA期可保守。侵襲型建議積極化療。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "BRCA mutation", "content": "Olaparib 單藥維持 2年 (SOLO-1)。"}, 
            {"title": "HRD positive / BRCA wt", "content": "PAOLA-1 (Ola+Bev) 或 PRIMA (Nira)。"},
            {"title": "HRD negative", "content": "Niraparib 維持 (PRIMA ITT) 或 Bevacizumab。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "PSOC (Sensitive Recur)", "content": "PFI > 6m。評估二次手術 (DESKTOP III) 或含鉑複方。"},
            {"title": "PROC (Resistant Recur)", "content": "PFI < 6m。單藥化療 ± Bev 或標靶 ADC (MIRASOL)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "PARPi Maint", "content": "救援緩解後選 PARPi 維持 (NOVA/ARIEL3/SOLO2)。"}]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "Locally Advanced (CCRT)", "content": "同步化放療 ± IO (A18) 或 誘導化療 (INTERLACE)。"},
            {"title": "Early Stage (Surgery)", "content": "根治術 (LACC) 或單純切除 (SHAPE)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Maintenance", "content": "1L 方案後接續維持 (KEYNOTE-826)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "Recurr / Metastatic", "content": "一線 Pembro+化療±Bev (KN826) 或 Atezo組合 (BEATcc)。二線 ADC。"}]}
    ]
}

# --- 2. 實證里程碑資料庫 (25項極量化補完) ---
milestone_db = [
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["dMMR / MSI-H"], "name": "📚 RUBY", "pharma": "GSK", "drug": "Dostarlimab + Carboplatin/Paclitaxel", 
     "pop_summary": "dMMR 族群核心研究：死亡風險降 68% (HR 0.32)。",
     "rationale": "PD-1 阻斷 (PD-1 blockade) 與含鉑化療具備協同免疫原性細胞死亡 (ICD) 效應，針對 MMRd 族群達成極高反應與持久應答 (Durable Response)。",
     "regimen": "誘導期 (Induction): Dostarlimab 500mg Q3W + CP x6週期 -> 維持期 (Maintenance): Dostarlimab 1000mg Q6W 最長 3年。",
     "inclusion": ["新診斷 FIGO Stage III-IV 或首次復發之子宮內膜癌 (EC)。", "包含癌肉瘤 (Carcinosarcoma) 型態。"],
     "exclusion": ["先前接受過系統性抗癌治療。", "活動性自體免疫疾病。"],
     "results": "dMMR: HR 0.32 (PFS), HR 0.30 (OS); ITT 全人群 mOS 44.6m (vs 28.2m)."},
    
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["dMMR / MSI-H", "pMMR / NSMP"], "name": "📚 NRG-GY018", "pharma": "MSD", "drug": "Pembrolizumab + CP", 
     "pop_summary": "一線不分 MMR 標竿：dMMR PFS HR 0.30; pMMR HR 0.54。",
     "rationale": "利用 ICI 與傳統化療聯用，擴大一線介入之生存獲益。",
     "regimen": "Pembrolizumab 200mg Q3W + CP x6週期 -> 維持 400mg Q6W 最長 2年。",
     "outcomes": "dMMR PFS HR 0.30; pMMR PFS HR 0.54."},

    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["pMMR / NSMP"], "name": "📚 DUO-E", "pharma": "AZ", "drug": "Durvalumab + CP →維持 ± Olaparib", 
     "pop_summary": "一線維持策略：三藥組 (Ola) pMMR PFS HR 0.57。",
     "rationale": "探索 PARPi 對於 pMMR 患者在免疫維持階段的增敏與協同作用。"},

    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["dMMR / MSI-H"], "name": "📚 AtTEnd", "pharma": "Roche", "drug": "Atezolizumab + CP", 
     "pop_summary": "一線晚期研究：dMMR PFS HR 0.36; ITT OS HR 0.82。",
     "outcomes": "dMMR PFS HR 0.36; ITT OS HR 0.82 (P=0.048)."},

    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "name": "📚 KEYNOTE-775", "pharma": "MSD/Eisai", "drug": "Lenvatinib + Pembro", 
     "pop_summary": "pMMR/MSS 二線標準：OS 17.4m vs 12.0m (HR 0.68)。",
     "rationale": "結合 VEGF-TKI 與免疫抑制劑，克服 MSS 腫瘤之免疫冷狀態。"},

    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "name": "📚 GARNET", "pharma": "GSK", "drug": "Dostarlimab 單藥", 
     "pop_summary": "MSI-H 後線單藥免疫：ORR 達 45.5%。",
     "outcomes": "dMMR ORR 45.5%; DOR (反應持續時間) 未達到。"},

    # --- Cervical Published ---
    {"cancer": "Cervical", "pos": "Locally Advanced (CCRT)", "sub_pos": ["Locally Advanced (CCRT)"], "name": "📚 KEYNOTE-A18", "pharma": "MSD", "drug": "Pembrolizumab + CCRT", 
     "pop_summary": "LACC 標準方案：36個月 OS 率 82.6% (HR 0.67)。",
     "rationale": "將免疫檢查點抑制劑整合入局部晚期 (LACC) 根治標準。"},

    {"cancer": "Cervical", "pos": "Locally Advanced (CCRT)", "sub_pos": ["Locally Advanced (CCRT)"], "name": "📚 INTERLACE", "pharma": "UCL", "drug": "Induction Carbo/Pacli x6", 
     "pop_summary": "誘導化療價值：5年 OS 率 80% vs 72% (HR 0.60)。",
     "outcomes": "5yr OS 80% (vs 72%); PFS HR 0.60."},

    {"cancer": "Cervical", "pos": "Locally Advanced (CCRT)", "sub_pos": ["Locally Advanced (CCRT)"], "name": "📚 CALLA", "pharma": "AZ", "drug": "Durvalumab + CCRT", 
     "pop_summary": "陰性試驗提醒：Durva+CCRT 未達 PFS 改善 (HR 0.84)。",
     "outcomes": "PFS HR 0.84 (P=NS)."},

    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 KEYNOTE-826", "pharma": "MSD", "drug": "Pembro + Chemo ± Bev", 
     "pop_summary": "R/M 一線黃金標準：全人群死亡風險降 37% (OS HR 0.63)。",
     "outcomes": "OS HR 0.63 (ITT); HR 0.60 (CPS≥1)."},

    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 BEATcc", "pharma": "Roche", "drug": "Atezo + Chemo + Bev", 
     "pop_summary": "一線復發/轉移：PFS HR 0.62; OS HR 0.68。"},

    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 EMPOWER-Cx 1", "pharma": "Regeneron", "drug": "Cemiplimab 單藥", 
     "pop_summary": "二線後 OS 基石：OS 12.0m vs 8.5m (HR 0.69)。"},

    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 innovaTV 301", "pharma": "Genmab", "drug": "Tisotumab Vedotin (ADC)", 
     "pop_summary": "後線 ADC 突破：OS HR 0.70; ORR 17.8% (vs 5.2%)。",
     "rationale": "標靶組織因子 (TF) 之 ADC，解決後線化療耐藥瓶頸。"},

    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Early Stage (Surgery)"], "name": "📚 SHAPE trial", "pharma": "CCTG", "drug": "Simple Hysterectomy", 
     "pop_summary": "手術降階實證：單純切除不劣於根治術 (3yr 復發 2.5%)。"},

    # --- Ovarian Published ---
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutation"], "name": "📚 SOLO-1", "pharma": "AZ", "drug": "Olaparib 維持", 
     "pop_summary": "BRCAm 里程碑：7年存活率 67% (HR 0.33)。"},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive / BRCA wt", "HRD negative"], "name": "📚 PRIMA", "pharma": "GSK", "drug": "Niraparib 維持", 
     "pop_summary": "全人群一線維持：HRD+ PFS HR 0.43。"},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive / BRCA wt"], "name": "📚 PAOLA-1", "pharma": "AZ", "drug": "Olaparib + Bevacizumab", 
     "pop_summary": "HRD+ 黃金組合：5年 OS 率 75.2% (HR 0.62)。"},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutation", "HRD positive / BRCA wt"], "name": "📚 ATHENA–MONO", "pharma": "Clovis", "drug": "Rucaparib 維持", 
     "pop_summary": "ITT PFS 28.7m (HR 0.52)。"},

    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["PARPi Maint"], "name": "📚 NOVA", "pharma": "GSK", "drug": "Niraparib 復發維持", 
     "pop_summary": "復發維持基石：gBRCA HR 0.27; non-gBRCA HR 0.45。"},

    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["PARPi Maint"], "name": "📚 ARIEL3", "pharma": "Clovis", "drug": "Rucaparib 復發維持", 
     "pop_summary": "維持治療獲益：HRD+ PFS HR 0.32。"},

    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["PARPi Maint"], "name": "📚 SOLO2", "pharma": "AZ", "drug": "Olaparib 復發維持", 
     "pop_summary": "BRCAm 長期 OS：mOS 51.7m vs 38.8m (HR 0.74)。"},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive / BRCA wt"], "name": "📚 DUO-O", "pharma": "AZ", "drug": "Durva+Ola+Bev 維持", 
     "pop_summary": "免疫組合潛力：HRD+ PFS HR 0.49。"},

    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PROC (Resistant)"], "name": "📚 MIRASOL", "pharma": "ImmunoGen", "drug": "Mirvetuximab", 
     "pop_summary": "PROC OS 突破：mOS 16.4m vs 12.7m (HR 0.67)。"},

    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 HIPEC (van Driel)", "pharma": "NEJM 2018", "drug": "Surgery + HIPEC", 
     "pop_summary": "IDS 時加熱化療：mOS 45.7m vs 33.9m (HR 0.67)。"},

    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PSOC (Sensitive)"], "name": "📚 DESKTOP III", "pharma": "NEJM 2021", "drug": "Secondary Surgery", 
     "pop_summary": "二次減積價值：完全切除者 mOS 達 53.7m。"},

    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 LION", "pharma": "NEJM 2019", "drug": "No Lymphadenectomy", 
     "pop_summary": "臨床 LN 陰性免清掃：OS 無差異 (HR 1.06)。"},
]

# --- 3. 招募中臨床試驗資料庫 (8項核心極量化) ---
ongoing_trials = [
    {"cancer": "Endometrial", "name": "📍 MK2870-033", "pharma": "MSD", "drug": "Sac-TMT + Pembrolizumab", "pos": "P-MT", "sub_pos": ["Maintenance Therapy"], "type": "Ongoing",
     "pop_summary": "標靶 Trop-2 ADC 協同免疫：針對 pMMR 族群挑戰一線維持標準。",
     "rationale": "利用 Trop-2 ADC (Sac-TMT) 引發之 ICD 調節腫瘤微環境，強化 PD-1 抑制劑 (Pembrolizumab) 在 pMMR 或 NSMP 患者中的應答深度與持續時間。",
     "regimen": "Pembrolizumab 400mg Q6W + Sac-TMT 5mg/kg Q6W 直至進展。",
     "inclusion": ["新診斷 pMMR 子宮內膜癌 (中心檢測)。", "FIGO III/IV 期、含鉑化療 + Pembro 後達 CR/PR。"],
     "exclusion": ["先前接受過針對晚期病灶之系統 IO 治療。", "子宮肉瘤 (Sarcoma)。"]},

    {"cancer": "Endometrial", "name": "📍 GU-US-682-6769", "pharma": "Gilead", "drug": "SG (Trodelvy)", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "type": "Ongoing",
     "pop_summary": "Trop-2 ADC 救援治療：解決鉑類與免疫失敗之臨床困境。",
     "rationale": "利用 SN-38 載荷引發 DNA 損傷，專攻鉑類及免疫檢查點抑制劑失敗後之復發性內膜癌患者。",
     "regimen": "Sacituzumab govitecan 10mg/kg (Day 1, Day 8) Q21D。",
     "inclusion": ["復發性 EC (不含肉瘤)。", "先前曾接受鉑類化療及 PD-1/L1 失敗。"],
     "exclusion": ["先前用過針對 Trop-2 之 ADC 藥物。", "活動性 CNS 轉移。"]},

    {"cancer": "Ovarian", "name": "📍 FRAmework-01", "pharma": "Eli Lilly", "drug": "LY4170156 + Bevacizumab", "pos": "R-TX", "sub_pos": ["PROC (Resistant)", "PSOC (Sensitive)"], "type": "Ongoing",
     "pop_summary": "FRα ADC 跨組臨床：聯用 VEGF 抑制劑提升腫瘤滲透與殺傷力。",
     "rationale": "透過 LY4170156 (FRα ADC) 精準標靶與 Bevacizumab 產生血管重塑協同作用，增強藥物在 PROC/PSOC 患者腫瘤基質中的濃度。",
     "regimen": "LY4170156 3mg/kg IV + Bevacizumab 15mg/kg IV Q3W。",
     "inclusion": ["經檢測 FRα 表達陽性。", "最後一劑鉑類後 90–180 天內進展 (PROC)。"]},

    {"cancer": "Ovarian", "name": "📍 DOVE", "pharma": "GSK", "drug": "Dostarlimab + Bevacizumab", "pos": "R-TX", "sub_pos": ["PROC (Resistant)"], "type": "Ongoing",
     "pop_summary": "針對 OCCC 透明細胞癌：利用雙重阻斷改善其特有免疫抑制微環境。",
     "rationale": "OCCC 具備獨特基因圖譜與高度免疫抑制，組合 IO + anti-VEGF 旨在誘導免疫應答。"},

    {"cancer": "Ovarian", "name": "📍 DS8201-772 (Enhertu)", "pharma": "AstraZeneca", "drug": "T-DXd", "pos": "P-MT", "sub_pos": ["HRD negative"], "type": "Ongoing",
     "pop_summary": "HER2 ADC 進入維持階段：旨在清除 HER2 表現之微小殘留病灶。",
     "rationale": "標靶 HER2 ADC 之極高 DAR (8) 優勢，於化療穩定後精準清除殘存病灶。"},
]

# --- 4. 動態模型與 AI 媒合助理 ---
def get_gemini_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target_model = next((m for m in available_models if 'gemini-1.5-flash' in m), None)
        if not target_model: target_model = next((m for m in available_models if 'gemini-pro' in m), None)
        if target_model: return genai.GenerativeModel(target_model)
    except: return None

# 側邊欄 AI 助理
with st.sidebar:
    st.markdown("<h3 style='color: #6A1B9A;'>🤖 AI 實證媒合助理</h3>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 患者數據深度分析", expanded=True):
        p_notes = st.text_area("輸入摘要 (含分期/細胞/標記)", placeholder="例如：EC III期, p53 mutation, HER2 2+...", height=220)
        if st.button("🚀 開始分析"):
            if api_key and p_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = get_gemini_model()
                    prompt = f"分析病歷：{p_notes}。請參考實證庫：{milestone_db} 及招募中：{ongoing_trials}。提供治療建議理由。"
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
            rel_trials = [t for t in (milestone_db + ongoing_trials) if t["cancer"] == cancer_type and t["pos"] == stage["id"] and any(s in sub["title"] for s in t["sub_pos"])]
            for t in rel_trials:
                label = f"{t.get('pharma', 'N/A')} | {t['name']} | {t['drug']}"
                with st.popover(label, use_container_width=True):
                    st.success(f"**核心結論:** {t.get('pop_summary', '詳見詳細看板。')}")
                    unique_key = f"sync_{t['name']}_{cancer_type}_{stage['id']}_{sub['title'].replace(' ', '')}"
                    if st.button("📊 同步看板細節", key=unique_key):
                        st.session_state.selected_trial = t['name']
                        st.rerun() # 無縫聯動修復
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 6. 深度數據看板 (Bottom Selector) ---
st.divider()
st.subheader("📋 臨床研究極量化數據庫 (Published Milestones & Ongoing Trials)")
all_list = milestone_db + ongoing_trials
filtered_names = [t["name"] for t in all_list if t["cancer"] == cancer_type]

try: curr_idx = filtered_names.index(st.session_state.selected_trial)
except: curr_idx = 0

selected_name = st.selectbox("🎯 快速點選研究以查閱詳細數據：", filtered_names, index=curr_idx, key="trial_selector")
st.session_state.selected_trial = selected_name
t = next(it for it in all_list if it["name"] == selected_name)

st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #E0E0E0; padding-bottom:10px; font-weight:900;'>📋 {t['name']} 深度分析報告</h2>", unsafe_allow_html=True)

r1, r2 = st.columns([1.3, 1])
with r1:
    st.markdown("<div style='background:#E3F2FD; border-left:10px solid #1976D2; padding:15px; border-radius:10px;'><b>💉 Rationale & Regimen (機轉與給藥)</b></div>", unsafe_allow_html=True)
    st.write(f"**核心藥物:** {t['drug']}")
    st.write(f"**詳細給藥方案 (Dosing Protocol):** {t.get('regimen', '請參考特定試驗分組劑量說明。')}")
    st.success(f"**科學理據 (Scientific Rationale):** {t['rationale']}")
    

with r2:
    st.markdown("<div style='background:#FFF8E1; border-left:8px solid #FBC02D; padding:15px; border-radius:10px;'><b>📈 Key Evidence (生存與緩解數據)</b></div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style='text-align:center; background:white; padding:15px; border:2px solid #FFE082; border-radius:12px;'>
            <div style='font-size: 14px; color: #795548; font-weight:700; margin-bottom:5px;'>Survival Metrics (PFS/OS/HR/ORR)</div>
            <div class='hr-big-val'>{t.get('results', t.get('outcomes', 'Ongoing'))}</div>
        </div>
    """, unsafe_allow_html=True)
    

st.divider()
r3, r4 = st.columns(2)
with r3:
    st.markdown("<div style='background:#E8F5E9; border-left:8px solid #2E7D32; padding:15px; border-radius:10px;'><b>✅ Inclusion Criteria (關鍵納入標準)</b></div>", unsafe_allow_html=True)
    for inc in t.get('inclusion', ['符合分子分型 (MMR/BRCA/HRD) 與前線治療規定。']): st.write(f"• **{inc}**")
with r4:
    st.markdown("<div style='background:#FFEBEE; border-left:8px solid #C62828; padding:15px; border-radius:10px;'><b>❌ Exclusion Criteria (關鍵排除標準)</b></div>", unsafe_allow_html=True)
    for exc in t.get('exclusion', ['排除顯著臟器功能不全、活動性自體免疫疾病或肺部纖維化史。']): st.write(f"• **{exc}**")
st.markdown("</div>", unsafe_allow_html=True)
