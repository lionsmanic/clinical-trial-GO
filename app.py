import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床導航與實證圖書館 (2026 旗艦最終版) ---
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

    /* 階段方塊：深色漸層背景 */
    .big-stage-card {
        border-radius: 10px; padding: 0px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: 2px solid transparent; background: white; 
        margin-bottom: 4px; overflow: hidden; height: auto !important;
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
    .hr-big-val { font-family: 'Roboto', sans-serif; font-size: 36px !important; font-weight: 900; color: #D84315; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 指引與路徑數據庫 ---
guidelines_nested = {
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "dMMR / MSI-H", "content": "首選：含鉑化療 + PD-1 (RUBY/GY018/AtTEnd)。"},
            {"title": "pMMR / NSMP", "content": "視 ER/Grade 決策；一線加維持 (DUO-E)。二線選標靶免疫 (KN775)。"},
            {"title": "POLE mutation", "content": "預後極佳，早期可降階治療；晚期仍屬 Rare 分型。"},
            {"title": "p53 mutation", "content": "預後最差。建議化放療積極介入。Serous 型需驗 HER2。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "IO Maintenance", "content": "一線 IO 後接續維持至 PD (DUO-E/RUBY)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "Recurrent EC", "content": "標準二線：Pembro + Lenva (MSS) 或單藥 IO (GARNET)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "維持有效治療直到進展。"}]}
    ],
    "Ovarian": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "HGSC / Endometrioid", "content": "Surgery + Carbo/Pacli ± Bev。考慮 IDS + HIPEC (van Driel)。"},
            {"title": "Mucinous (MOC) 鑑定", "content": "判定：CK7+/SATB2- (原發)。Expansile (預後佳) vs Infiltrative (易轉移)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "BRCA mutation", "content": "Olaparib 單藥維持 2年 (SOLO-1)。"}, 
            {"title": "HRD positive / BRCA wt", "content": "PAOLA-1 (Ola+Bev) 或 PRIMA (Nira)。"},
            {"title": "HRD negative", "content": "Niraparib 維持 (PRIMA ITT) 或 Bev。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "PSOC (Sensitive Recur)", "content": "PFI > 6m。評估二次手術 (DESKTOP III) 或含鉑雙藥。"},
            {"title": "PROC (Resistant Recur)", "content": "PFI < 6m。單藥化療 ± Bev 或標靶 ADC (MIRASOL)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Platinum Sensitive Maint", "content": "救援緩解後選 PARPi 維持 (NOVA/ARIEL3/SOLO2)。"}]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "Locally Advanced (CCRT)", "content": "同步化放療 ± IO (A18) 或 誘導化療 (INTERLACE/CALLA)。"},
            {"title": "Early Stage (Surgery)", "content": "根治術 (LACC) 或單純切除 (SHAPE)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Maintenance Therapy", "content": "一線轉移性方案後續用 IO 維持 (KN826)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "Recurr / Metastatic", "content": "一線 Pembro+化療±Bev (KN826) 或 Atezo組合 (BEATcc)。二線 ADC (innovaTV)。"}]}
    ]
}

# --- 2. 綜合實證資料庫 (33+ 研究全方位整合) ---
all_trials_db = [
    # --- 📚 Published Milestones ---
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["dMMR / MSI-H"], "name": "📚 RUBY", "pharma": "GSK", "drug": "Dostarlimab + CP", 
     "popover_summary": "dMMR 族群核心研究：死亡風險降 68% (HR 0.32)，奠定一線免疫加化療標準。",
     "rationale": "PD-1 阻斷與化療具協同 ICD 效應，針對 MMRd 族群達到極高持久應答率。",
     "regimen": "Dosta 500mg Q3W + CP x6 週期 -> 維持 Dosta 1000mg Q6W 最長 3年。",
     "inclusion": ["新診斷 Stage III-IV 或首次復發 EC。", "包含 Carcinosarcoma 組織型態。"],
     "exclusion": ["先前接受過系統抗癌治療。", "活動性自體免疫疾病。"],
     "outcomes": "dMMR: HR 0.32 (PFS); mOS 44.6m (vs 28.2m, HR 0.69)."},

    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["dMMR / MSI-H", "pMMR / NSMP / MSS"], "name": "📚 NRG-GY018", "pharma": "MSD", "drug": "Pembrolizumab + CP", 
     "popover_summary": "不限 MMR 分型一線免疫：dMMR PFS HR 0.30; pMMR HR 0.54。",
     "regimen": "Pembro 200mg Q3W + CP x6 -> 維持 400mg Q6W 最長 2年。",
     "outcomes": "dMMR PFS HR 0.30; pMMR HR 0.54."},

    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["pMMR / NSMP / MSS"], "name": "📚 DUO-E", "pharma": "AZ", "drug": "Durvalumab + CP →維持 ± Ola", 
     "popover_summary": "一線維持策略：三藥組將 pMMR PFS HR 降至 0.57，探索維持階段之協同價值。",
     "results": "三藥組 PFS HR 0.57 (vs CP)."},

    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["dMMR / MSI-H"], "name": "📚 AtTEnd", "pharma": "Roche", "drug": "Atezolizumab + CP", 
     "popover_summary": "一線晚期/復發：dMMR PFS HR 0.36，確認 PD-L1 併用化療價值。",
     "outcomes": "dMMR PFS HR 0.36; ITT OS HR 0.82."},

    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "name": "📚 KEYNOTE-775", "pharma": "MSD/Eisai", "drug": "Lenvatinib + Pembro", 
     "popover_summary": "MSS/pMMR 二線標準：OS 17.4m vs 12.0m，確立後線標靶免疫領先地位。",
     "outcomes": "pMMR OS HR 0.68; mOS 17.4m (vs 12.0m)."},

    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "name": "📚 GARNET", "pharma": "GSK", "drug": "Dostarlimab 單藥", 
     "popover_summary": "MSI-H 後線免疫單藥：ORR 45.5%，提供持久緩解數據。",
     "outcomes": "dMMR ORR 45.5%; DOR 未達到。"},

    # --- Cervical Published ---
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Locally Advanced (CCRT)"], "name": "📚 KEYNOTE-A18", "pharma": "MSD", "drug": "Pembrolizumab + CCRT", 
     "popover_summary": "LACC 同步免疫標準：36個月 OS 82.6% (vs 74.8%)，顯著改善根治存活。",
     "outcomes": "OS HR 0.67; 36m OS 82.6%."},

    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Locally Advanced (CCRT)"], "name": "📚 INTERLACE", "pharma": "UCL", "drug": "Induction Carbo/Pacli x6", 
     "popover_summary": "誘導化療價值：先 6週誘導化療再 CCRT 顯著提升 5年 OS (HR 0.60)。",
     "outcomes": "5yr OS 80% (vs 72%)."},

    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Locally Advanced (CCRT)"], "name": "📚 CALLA", "pharma": "AZ", "drug": "Durvalumab + CCRT", 
     "popover_summary": "陰性試驗提醒：Durva + CCRT 整體未達標 (HR 0.84)。",
     "outcomes": "PFS HR 0.84 (P=NS)."},

    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 KEYNOTE-826", "pharma": "MSD", "drug": "Pembro + Chemo ± Bev", 
     "popover_summary": "R/M 一線核心方案：全人群死亡風險降 37%，CPS≥1 獲益極顯著。",
     "outcomes": "OS HR 0.63; CPS≥1 HR 0.60."},

    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 BEATcc", "pharma": "Roche", "drug": "Atezo + Chemo + Bev", 
     "popover_summary": "一線復發/轉移：PFS/OS 皆改善，提供 Atezo 併用新選項。",
     "outcomes": "PFS HR 0.62; OS HR 0.68."},

    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 EMPOWER-Cx 1", "pharma": "Regeneron", "drug": "Cemiplimab", 
     "popover_summary": "二線免疫 OS 證據：OS 12.0m vs 8.5m，獲益不依賴 PD-L1 表現。",
     "outcomes": "OS HR 0.69; mOS 12.0m."},

    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 innovaTV 301", "pharma": "Genmab", "drug": "Tisotumab Vedotin (ADC)", 
     "popover_summary": "後線 ADC 突破：OS HR 0.70; ORR 17.8%，ADC 正式進入後線標準。",
     "outcomes": "OS HR 0.70; ORR 17.8%."},

    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Early Stage (Surgery)"], "name": "📚 SHAPE trial", "pharma": "CCTG", "drug": "Simple Hysterectomy", 
     "popover_summary": "手術降階實證：低風險患者單純全子宮切除復發率與根治術相當。",
     "outcomes": "3yr Recurrence: 2.5% vs 2.2%."},

    # --- Ovarian ---
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutation"], "name": "📚 SOLO-1", "pharma": "AZ", "drug": "Olaparib 維持", 
     "popover_summary": "BRCAm 里程碑：7年存活率 67%，確立一線 PARPi 維持治癒潛力。",
     "outcomes": "7yr survival 67% (HR 0.33)."},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive / BRCA wt"], "name": "📚 PRIMA", "pharma": "GSK", "drug": "Niraparib 維持", 
     "popover_summary": "全人群維持：HRD+ PFS HR 0.43，支持不限 BRCA 之維持策略。",
     "outcomes": "HRD+ PFS HR 0.43; ITT HR 0.62."},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive / BRCA wt"], "name": "📚 PAOLA-1", "pharma": "AZ", "drug": "Olaparib + Bevacizumab", 
     "popover_summary": "HRD+ 黃金組合：5年 OS 率 75.2%，確立組合維持勝於 Bev 單藥。",
     "outcomes": "HRD+ OS HR 0.62; 5yr OS 75.2%."},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutation", "HRD positive / BRCA wt"], "name": "📚 ATHENA–MONO", "pharma": "Clovis", "drug": "Rucaparib 維持", 
     "popover_summary": "一線全人群維持：ITT PFS HR 0.52 (28.7m vs 11.3m)。",
     "outcomes": "ITT PFS HR 0.52."},

    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], "name": "📚 NOVA", "pharma": "GSK", "drug": "Niraparib 維持", 
     "popover_summary": "復發維持基石：gBRCA HR 0.27; 非 gBRCA HR 0.45。",
     "outcomes": "gBRCA HR 0.27; Non-gBRCA HR 0.45."},

    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], "name": "📚 ARIEL3", "pharma": "Clovis", "drug": "Rucaparib 維持", 
     "popover_summary": "所有分層獲益：BRCAm HR 0.23; HRD+ HR 0.32。",
     "outcomes": "BRCAm HR 0.23; HRD+ HR 0.32."},

    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], "name": "📚 SOLO2", "pharma": "AZ", "drug": "Olaparib 維持", 
     "popover_summary": "BRCAm 復發 OS：mOS 51.7m vs 38.8m (HR 0.74)。",
     "outcomes": "mOS 51.7m vs 38.8m."},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive / BRCA wt"], "name": "📚 DUO-O", "pharma": "AZ", "drug": "Durva+Ola+Bev 維持", 
     "popover_summary": "免疫組合優勢：HRD+ PFS HR 0.49，顯示 IO 組合策略潛力。",
     "outcomes": "HRD+ PFS HR 0.49."},

    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PROC (Resistant Recur)"], "name": "📚 MIRASOL", "pharma": "ImmunoGen", "drug": "Mirvetuximab", 
     "popover_summary": "PROC OS 突破：OS HR 0.67; ORR 42.3%，改變抗藥型治療標準。",
     "outcomes": "OS HR 0.67; ORR 42.3%."},

    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 HIPEC (van Driel)", "pharma": "NEJM 2018", "drug": "Surgery + HIPEC", 
     "popover_summary": "IDS 手術加溫：mOS 延長 12 個月 (HR 0.67)，強化微小病灶殺傷。",
     "outcomes": "mOS 45.7m vs 33.9m."},

    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PSOC (Sensitive Recur)"], "name": "📚 DESKTOP III", "pharma": "NEJM 2021", "drug": "Secondary Surgery", 
     "popover_summary": "二次減積價值：嚴選患者 (AGO+) mOS 53.7m vs 46.0m。",
     "outcomes": "mOS 53.7m vs 46.0m (HR 0.75)."},

    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 LION", "pharma": "NEJM 2019", "drug": "No Lymphadenectomy", 
     "popover_summary": "手術減輕負擔：臨床 LN 陰性免清掃，OS 無差異 (HR 1.06)。",
     "outcomes": "OS HR 1.06."},

    # --- 📍 Ongoing Trials (救援 8 核心) ---
    {"cancer": "Ovarian", "name": "📍 FRAmework-01", "pharma": "Eli Lilly", "drug": "LY4170156 + Bevacizumab", "pos": "R-TX", "sub_pos": ["PROC (Resistant Recur)"], "type": "Ongoing",
     "popover_summary": "FRα ADC 併用血管新生抑制劑：提升滲透殺傷。",
     "rationale": "標靶 FRα ADC 聯用 anti-VEGF 產生血管重塑協同作用 (Synergy)，提升藥物滲透深度。",
     "regimen": "LY4170156 3mg/kg IV + Bevacizumab 15mg/kg IV Q3W。",
     "inclusion": ["FRα 表達陽性。", "最後鉑類後 90–180 天內惡化 (PROC)。"]},

    {"cancer": "Ovarian", "name": "📍 REJOICE-Ovarian01", "pharma": "Daiichi Sankyo", "drug": "R-DXd", "pos": "R-TX", "sub_pos": ["PROC (Resistant Recur)"], "type": "Ongoing",
     "popover_summary": "標靶 CDH6 ADC：專攻高度異質性之 PROC 環境。",
     "rationale": "標靶 Cadherin-6 (CDH6) ADC，具強力旁觀者效應克服前線化療耐藥性。",
     "regimen": "R-DXd 5.6mg/kg IV Q3W。",
     "inclusion": ["HG Serous 或 Endometrioid PROC。", "提供切片進行 CDH6 分層。"]},

    {"cancer": "Ovarian", "name": "📍 TroFuse-021", "pharma": "MSD", "drug": "Sac-TMT (MK-2870) + Bev", "pos": "P-MT", "sub_pos": ["HRD negative"], "type": "Ongoing",
     "popover_summary": "標靶 Trop-2 ADC 組合：旨在優化維持階段獲益。",
     "rationale": "標靶 Trop-2 ADC 協同 Beva 微環境調節與 ADC 誘導之 ICD 效應挑戰一線維持標準。"},

    {"cancer": "Endometrial", "name": "📍 MK2870-033", "pharma": "MSD", "drug": "Sac-TMT + Pembrolizumab", "pos": "P-MT", "sub_pos": ["Maintenance"], "type": "Ongoing",
     "popover_summary": "Trop-2 ADC 協同 PD-1：提升 pMMR/NSMP 應答深度。",
     "regimen": "Pembro 400mg Q6W + Sac-TMT 5mg/kg Q6W。"},

    {"cancer": "Endometrial", "name": "📍 GU-US-682-6769", "pharma": "Gilead", "drug": "SG (Trodelvy)", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "type": "Ongoing",
     "popover_summary": "標靶 Trop-2 ADC 利用 SN-38 載荷對抗鉑類免疫失敗。",
     "regimen": "SG 10mg/kg (D1, D8 Q21D)。"},

    {"cancer": "Ovarian", "name": "📍 DS8201-772 (Enhertu)", "pharma": "AstraZeneca", "drug": "T-DXd", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], "type": "Ongoing",
     "popover_summary": "HER2 ADC 救援後維持：清除 HER2 表現殘留病灶。",
     "inclusion": ["HER2 IHC 1+/2+/3+ 確認。", "PSOC 救援化療達穩定 (Non-PD)。"]},

    {"cancer": "Ovarian", "name": "📍 DOVE", "pharma": "GSK", "drug": "Dostarlimab + Bevacizumab", "pos": "R-TX", "sub_pos": ["PROC (Resistant Recur)"], "type": "Ongoing",
     "popover_summary": "針對 OCCC 透明細胞癌利用雙重阻斷改善微環境。",
     "inclusion": ["組織學 OCCC > 50%。", "鉑類抗藥性 (PFI < 12m)。"]},
]

# --- 3. 動態模型與 AI 媒合 ---
def get_gemini_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target_model = next((m for m in available_models if 'gemini-1.5-flash' in m), None)
        if not target_model: target_model = next((m for m in available_models if 'gemini-pro' in m), None)
        if target_model: return genai.GenerativeModel(target_model)
    except: return None

# --- 4. 側邊欄：患者分析與看板同步 ---
with st.sidebar:
    st.markdown("<h3 style='color: #6A1B9A;'>🤖 AI 實證媒合助理</h3>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 患者病歷深度媒合", expanded=True):
        p_notes = st.text_area("輸入摘要 (含細胞型態/標記)", placeholder="例如：EC III期, dMMR, p53 mutation...", height=220)
        if st.button("🚀 開始媒合"):
            if api_key and p_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = get_gemini_model()
                    prompt = f"分析病歷：{p_notes}。請參考實證庫：{all_trials_db}。建議適合路徑與理由。"
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
                    st.success(f"**核心摘要:** {t.get('popover_summary', '招募中')}")
                    unique_key = f"sync_{t['name']}_{cancer_type}_{stage['id']}_{sub['title'].replace(' ', '')}"
                    if st.button("📊 同步看板細節", key=unique_key):
                        st.session_state.selected_trial = t['name']
                        st.rerun() # 強制同步
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 6. 深度數據看板 (Bottom Selector) ---
st.divider()
st.subheader("📋 臨床研究極量化數據庫 (Published Milestones & Ongoing Trials)")
filtered_list = [t for t in all_trials_db if t["cancer"] == cancer_type]
try: curr_idx = [t["name"] for t in filtered_list].index(st.session_state.selected_trial)
except: curr_idx = 0

selected_name = st.selectbox("🎯 快速選擇研究計畫以查閱詳細內容：", [t["name"] for t in filtered_list], index=curr_idx, key="trial_selector")
st.session_state.selected_trial = selected_name
t = next(it for it in all_trials_db if it["name"] == selected_name)

st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #E0E0E0; padding-bottom:10px; font-weight:900;'>📋 {t['name']} 深度數據分析報告</h2>", unsafe_allow_html=True)

r1, r2 = st.columns([1.3, 1])
with r1:
    st.markdown("<div style='background:#E3F2FD; border-left:10px solid #1976D2; padding:15px; border-radius:10px;'><b>💉 Rationale & Regimen (機轉與給藥)</b></div>", unsafe_allow_html=True)
    st.write(f"**核心介入:** {t['drug']}")
    st.write(f"**詳細給藥方案:** {t.get('regimen', '詳見招募細則。')}")
    st.success(f"**科學理據 (Scientific Rationale):** {t.get('rationale', '旨在挑戰現有 SoC 瓶頸，提升生存獲益。')}")
    

with r2:
    st.markdown("<div style='background:#FFF8E1; border-left:8px solid #FBC02D; padding:15px; border-radius:10px;'><b>📈 Key Outcomes (最新生存與緩解指標)</b></div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style='text-align:center; background:white; padding:15px; border:2px solid #FFE082; border-radius:12px;'>
            <div style='font-size: 14px; color: #795548; font-weight:700; margin-bottom:5px;'>Survival Metrics (PFS/OS/HR/ORR)</div>
            <div class='hr-big-val'>{t.get('outcomes', 'Ongoing')}</div>
        </div>
    """, unsafe_allow_html=True)
    

st.divider()
r3, r4 = st.columns(2)
with r3:
    st.markdown("<div style='background:#E8F5E9; border-left:8px solid #2E7D32; padding:15px; border-radius:10px;'><b>✅ Inclusion Criteria (關鍵納入標準)</b></div>", unsafe_allow_html=True)
    for inc in t.get('inclusion', ['詳見全文。']): st.write(f"• **{inc}**")
with r4:
    st.markdown("<div style='background:#FFEBEE; border-left:8px solid #C62828; padding:15px; border-radius:10px;'><b>❌ Exclusion Criteria (關鍵排除標準)</b></div>", unsafe_allow_html=True)
    for exc in t.get('exclusion', ['詳見全文。']): st.write(f"• **{exc}**")
st.markdown("</div>", unsafe_allow_html=True)
