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

    .stPopover button[aria-label*="Eli Lilly"] { background: #FCE4EC !important; border-left: 5px solid #E91E63 !important; } 

    .stPopover button[aria-label*="Daiichi Sankyo"] { background: #E8F5E9 !important; border-left: 5px solid #4CAF50 !important; } 

    .stPopover button[aria-label*="MSD"] { background: #E3F2FD !important; border-left: 5px solid #1976D2 !important; } 

    .stPopover button[aria-label*="AstraZeneca"] { background: #F3E5F5 !important; border-left: 5px solid #8E24AA !important; } 

    .stPopover button[aria-label*="GSK"] { background: #FFF3E0 !important; border-left: 5px solid #F57C00 !important; } 

    .stPopover button[aria-label*="Gilead"] { background: #E1F5FE !important; border-left: 5px solid #03A9F4 !important; } 

    .stPopover button[aria-label*="Seagen"] { background: #EEEEEE !important; border-left: 5px solid #212121 !important; } 



    .detail-section { background: white; border-radius: 18px; padding: 25px; border: 1px solid #CFD8DC; box-shadow: 0 10px 40px rgba(0,0,0,0.05); }

    .hr-big-val { font-family: 'Roboto', sans-serif; font-size: 45px !important; font-weight: 900; color: #D84315; }

    </style>

    """, unsafe_allow_html=True)



# --- 1. 指引導航數據庫：包含 MOC 鑑別與 PSOC/PROC 分流 ---

guidelines_nested = {

    "Endometrial": [

        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [

            {"title": "MMRd / MSI-H / dMMR", "content": "一線標竿：Chemo + PD-1 (GY018/RUBY)。Dostarlimab 獲益極顯著。"},

            {"title": "NSMP / pMMR / MSS", "content": "排除分型。視 ER/Grade 權重決策；二線考慮 Pembro+Lenva。"},

            {"title": "POLEmut / p53abn", "content": "POLE: 最佳預後；p53abn: 最差預後，需積極輔助治療。"}]},

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

        {"id": "R-TX", "header": "復發治療 (R-TX)", "css": "r-tx", "subs": [

            {"title": "PSOC (Sensitive)", "content": "PFI > 6m。含鉑雙藥化療 ± Bev。評估二次手術 (DESKTOP)。"},

            {"title": "PROC (Resistant)", "content": "PFI < 6m。單藥化療 ± Bev 或標靶 ADC (MIRASOL/FRAmework)。"}]},

        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Platinum Sensitive Maint", "content": "救援緩解後續以 PARPi 維持治療。"}]}

    ],

    "Cervical": [

        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [

            {"title": "CCRT (Locally Advanced)", "content": "同步化放療。高風險者同步 IO (A18) 或誘導化療 (INTERLACE)。"},

            {"title": "Early Stage (Surgery)", "content": "根治性開腹術 (LACC)。低風險者選單純切除 (SHAPE)。"}]},

        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Metastatic Maint", "content": "1L 轉移性 IO 方案後延續維持至進展。"}]},

        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [

            {"title": "Recurrent / Metastatic", "content": "一線 Pembro + 化療 ± Bev。二線 ADC (Tivdak) 或 IO (EMPOWER)。"}]},

        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "維持有效治療直至進展。"}]}

    ]

}



# --- 2. 實證里程碑 (📚 Milestone Library - 完整 24 項深度對應) ---

milestone_db = [

    # Endometrial

    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H / dMMR"], "name": "📚 RUBY", "drug": "Dostarlimab + CP", "summary": "FIGO III-IV/Recurrent。dMMR 死亡風險降 68% (HR 0.32)；全人群 mOS 44.6m vs 28.2m (HR 0.69)。"},

    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H / dMMR", "NSMP / pMMR / MSS"], "name": "📚 NRG-GY018", "drug": "Pembrolizumab + CP", "summary": "FIGO III-IV/Recurrent。dMMR PFS HR 0.30；pMMR 亦顯著改善 (HR 0.54)。支持一線不論 MMR 之 IO 獲益。"},

    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["NSMP / pMMR / MSS"], "name": "📚 DUO-E", "drug": "Durvalumab ± Olaparib", "summary": "一線晚期。三藥組 PFS HR 0.57 (vs CP)；Durva 組 HR 0.77。建立免疫維持策略。"},

    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H / dMMR"], "name": "📚 AtTEnd", "drug": "Atezolizumab + CP", "summary": "一線晚期。dMMR PFS HR 0.36，獲益極大；全體 OS HR 0.82。支持 PD-(L)1 併化療證據鏈。"},

    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "name": "📚 KEYNOTE-775", "drug": "Lenvatinib + Pembro", "summary": "二線(曾含鉑)。pMMR OS 17.4m vs 12.0m (HR 0.68)；5年 OS 16.7% vs 7.3%。MSS 二線標準。"},



    # Cervical

    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["CCRT (Locally Advanced)"], "name": "📚 KEYNOTE-A18", "drug": "Pembrolizumab + CCRT", "summary": "高風險 LACC。36個月 OS 82.6% vs 74.8% (HR 0.67)。確立同步免疫標準。"},

    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["CCRT (Locally Advanced)"], "name": "📚 INTERLACE", "drug": "Induction Carbo/Pacli", "summary": "局部晚期。6週誘導化療後接 CCRT，5年 OS 80% vs 72% (HR 0.60)。現成化療可提升生存。"},

    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["CCRT (Locally Advanced)"], "name": "📚 CALLA (陰性)", "drug": "Durvalumab + CCRT", "summary": "局部晚期。整體未達統計學 PFS 改善。HR 0.84。提示需更精準分流。"},

    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurrent / Metastatic"], "name": "📚 KEYNOTE-826", "drug": "Pembro + Chemo ± Bev", "summary": "R/M 一線。全人群 OS HR 0.63；CPS≥1 HR 0.60。奠定 R/M 一線 IO 基礎。"},

    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurrent / Metastatic"], "name": "📚 BEATcc", "drug": "Atezolizumab + Chemo+Bev", "summary": "R/M 一線。PFS HR 0.62，OS HR 0.68。提供一線免疫併用新選項。"},

    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurrent / Metastatic"], "name": "📚 EMPOWER-Cx 1", "drug": "Cemiplimab", "summary": "二線。OS 12.0m vs 8.5m (HR 0.69)；獲益不依賴 PD-L1 表現。後線 IO 單藥證據。"},

    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurrent / Metastatic"], "name": "📚 innovaTV 301", "drug": "Tisotumab Vedotin", "summary": "二/三線。OS 11.5m vs 9.5m (HR 0.70)，ORR 17.8%。ADC 進入標準後線。"},

    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Early Stage (Surgery)"], "name": "📚 SHAPE trial", "drug": "Simple Hysterectomy", "summary": "早期低風險(<2cm)。3年復發率 2.5% (SH) vs 2.2% (RH)。支持手術降階。"},



    # Ovarian

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutated"], "name": "📚 SOLO-1", "drug": "Olaparib", "summary": "一線維持。7年 survival 67% (vs 46.5%, HR 0.33)。確立治癒潛力里程碑。"},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive (wt)"], "name": "📚 PAOLA-1", "drug": "Olaparib + Bevacizumab", "summary": "一線維持。HRD+ 族群 5年 OS 顯著改善 (HR 0.62)。確立「PARPi + anti-VEGF」路徑。"},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive (wt)", "HRD negative / pHRD"], "name": "📚 ATHENA–MONO", "drug": "Rucaparib", "summary": "一線維持。ITT PFS HR 0.52 (28.7m vs 11.3m)；支持廣泛 PARPi 應用。"},

    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], "name": "📚 NOVA", "drug": "Niraparib", "summary": "復發維持。gBRCA HR 0.27；非 gBRCA HR 0.45。顯著延緩復發。"},

    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], "name": "📚 ARIEL3", "drug": "Rucaparib", "summary": "復發維持。Rucaparib 在所有分層(BRCA/HRD+/ITT)均 PFS 改善。"},

    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], "name": "📚 SOLO2",
