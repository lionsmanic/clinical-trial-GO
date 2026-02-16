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

    /* 大階段方塊：零留白，高度隨內容撐開 */
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

    /* 按鈕樣式：深黑色加粗 (#1A1A1A) 確保字體清晰 */
    .stPopover button { 
        font-weight: 900 !important; font-size: 12px !important; 
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
    .hr-big-val { font-family: 'Roboto', sans-serif; font-size: 50px !important; font-weight: 900; color: #D84315; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 指引導航數據庫：包含 MOC 與 PSOC/PROC 分流 ---
guidelines_nested = {
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "MMRd / MSI-H / dMMR", "content": "一線首選：Chemo + PD-1 (GY018/RUBY)。Dostarlimab 獲益顯著。"},
            {"title": "NSMP / pMMR / MSS", "content": "排除分型。視 ER/Grade 權重決策；二線考慮 Pembro+Lenva。"},
            {"title": "POLEmut / p53abn", "content": "POLE: 最佳預後可降階；p53abn: 最差預後，需積極化放療。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "IO Maintenance", "content": "一線 IO 治療後接續維持直到疾病進展 (PD)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "Recurrent EC", "content": "二線方案：標靶+免疫 (pMMR) 或 IO 單藥 (MMRd/GARNET)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "維持有效治療直到進展。"}]}
    ],
    "Ovarian": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "HGSC / Endometrioid", "content": "手術 (PDS/IDS) + Carboplatin/Paclitaxel ± Bevacizumab。"},
            {"title": "Mucinous (MOC) 鑑別", "content": "判定：CK7+/SATB2- (原發)。1. Expansile: 預後佳。 2. Infiltrative: 高復發風險，建議積極化療。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "BRCA mutated", "content": "Olaparib 單藥維持 2年。"}, {"title": "HRD positive (wt)", "content": "Olaparib+Bev (2年) 或 Niraparib 單藥 (3年)。"}]},
        {"id": "R-TX (PROC)", "header": "復發治療 (PROC)", "css": "r-tx", "subs": [{"title": "Platinum-Resistant", "content": "PFI < 6m。單藥化療 ± Bev 或標靶 ADC (MIRASOL)。"}]},
        {"id": "R-TX (PSOC)", "header": "復發治療 (PSOC)", "css": "r-tx", "subs": [{"title": "Platinum-Sensitive", "content": "PFI > 6m。含鉑雙藥化療 ± Bev。評估二次手術。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Platinum Sensitive Maint", "content": "含鉑救援緩解後續以 PARPi 維持。"}]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "CCRT (Locally Advanced)", "content": "同步化放療。高風險者同步 IO (A18) 或誘導化療 (INTERLACE)。"},
            {"title": "Early Stage (Surgery)", "content": "根治性開腹術 (LACC)。低風險者選單純切除 (SHAPE)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Metastatic Maint", "content": "1L 轉移性 IO 方案後延續維持。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "Recurrent / Metastatic", "content": "一線 Pembro + 化療 ± Bev。二線 ADC (Tivdak) 或 IO (EMPOWER)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "維持有效治療直至進展。"}]}
    ]
}

# --- 2. 實證里程碑 (📚 Milestone Library - 完整對應 24 項已發表研究) ---
milestone_db = [
    # Endometrial
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H / dMMR"], "name": "📚 RUBY (Dostarlimab)", "type": "Milestone", "summary": "一線晚期/復發。dMMR 死亡風險降 68% (HR 0.32)；全人群 mOS 44.6m vs 28.2m (HR 0.69)。", "details": "FIGO III-IV/Recurrent。dMMR PFS 獲益極顯著，確立一線免疫標準。"},
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H / dMMR", "NSMP / pMMR / MSS"], "name": "📚 NRG-GY018 (KEYNOTE-868)", "type": "Milestone", "summary": "一線晚期/復發。dMMR PFS HR 0.30；pMMR 顯著改善 (HR 0.54)。", "details": "支持一線不論 MMR 狀態之 IO 獲益，擴大適用面。"},
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["NSMP / pMMR / MSS"], "name": "📚 DUO-E (Durvalumab)", "type": "Milestone", "summary": "一線晚期。三藥組 (IO+Chemo+PARPi) PFS HR 0.57；單藥 IO 組 HR 0.77。", "details": "建立「免疫+維持」策略，對 pMMR 有額外加成。"},
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H / dMMR"], "name": "📚 AtTEnd", "type": "Milestone", "summary": "一線。dMMR PFS HR 0.36，獲益顯著；全體 OS HR 0.82 (P=0.048)。", "details": "含 Carcinosarcoma 族群，支持 PD-(L)1 併化療證據鏈。"},
    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "name": "📚 KEYNOTE-775", "type": "Milestone", "summary": "二線(曾含鉑)。pMMR OS 17.4m vs 12.0m (HR 0.68)；5年 OS 16.7% vs 7.3%。", "details": "確立 pMMR/MSS 後線標靶+免疫標準，需注意毒性。"},
    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "name": "📚 GARNET", "type": "Milestone", "summary": "多線後。dMMR/MSI-H ORR 達 45.5%，反應持久。", "details": "單臂試驗，奠定後線免疫單藥地位。"},

    # Cervical
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["CCRT (Locally Advanced)"], "name": "📚 KEYNOTE-A18", "type": "Milestone", "summary": "局部晚期。36個月 OS 82.6% vs 74.8% (HR 0.67)。", "details": "高風險 LACC 患者免疫正式併入根治性 CCRT 之新標準。"},
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["CCRT (Locally Advanced)"], "name": "📚 INTERLACE", "type": "Milestone", "summary": "局部晚期。先 6週誘導化療再 CCRT，5年 OS 80% vs 72% (HR 0.60)。", "details": "利用現成化療方案提升生存，具備落地價值。"},
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["CCRT (Locally Advanced)"], "name": "📚 CALLA (陰性試驗)", "type": "Milestone", "summary": "局部晚期。Durva+CCRT 整體未達顯著改善。", "details": "提示局部晚期需更精準族群分流。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["1L Recurrent"], "name": "📚 KEYNOTE-826", "type": "Milestone", "summary": "R/M 一線。全人群 OS HR 0.63；CPS≥1 HR 0.60。", "details": "OS 持續改善，R/M 一線核心試驗。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["1L Recurrent"], "name": "📚 BEATcc", "type": "Milestone", "summary": "R/M 一線。PFS HR 0.62，OS HR 0.68。改善生存預後。", "details": "提供一線免疫(Atezolizumab)加化療新選項。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["2L / 3L Therapy"], "name": "📚 EMPOWER-Cervical 1", "type": "Milestone", "summary": "二線。OS 延長 (12.0m vs 8.5m)，且效益不依賴 PD-L1。", "details": "後線免疫單藥(Cemiplimab)之關鍵 OS 證據。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["2L / 3L Therapy"], "name": "📚 innovaTV 301", "type": "Milestone", "summary": "二/三線。OS 11.5m vs 9.5m (HR 0.70)，ORR 17.8%。", "details": "ADC (Tisotumab) 進入後線標準選項，需監測眼表毒性。"},
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Early Stage (Surgery)"], "name": "📚 SHAPE trial", "type": "Milestone", "summary": "早期(<2cm)。單純全切除 3年復發率與根治術相當 (2.5% vs 2.2%)。", "details": "支持早期低風險患者手術降階，降低副作用。"},

    # Ovarian
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutated"], "name": "📚 SOLO-1 (Olaparib)", "type": "Milestone", "summary": "一線維持。7年 survival 67% (vs 46.5%, HR 0.33)。", "details": "BRCA1/2 變異對含鉑反應者，確立治癒潛力里程碑。"},
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive (wt)"], "name": "📚 PAOLA-1", "type": "Milestone", "summary": "一線維持(含Bev)。HRD+ 族群 5年 OS 顯著改善 (HR 0.62)。", "details": "確立「PARPi + anti-VEGF」維持路徑，HRD- 無額外獲益。"},
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive (wt)", "HRD negative / pHRD"], "name": "📚 PRIMA", "type": "Milestone", "summary": "一線維持。HRD+ 獲益最大 (PFS HR 0.43)；支持不限 BRCA 維持。", "details": "高復發風險族群，建立全人群維持價值。"},
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutated", "HRD positive (wt)"], "name": "📚 ATHENA–MONO", "type": "Milestone", "summary": "一線維持。ITT 人群 PFS 延長兩倍以上 (HR 0.52)。", "details": "新診斷晚期對含鉑反應，擴充 Rucaparib 維持證據。"},
    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], "name": "📚 NOVA", "type": "Milestone", "summary": "復發維持。gBRCA (HR 0.27) 與非 gBRCA (HR 0.45) 均 PFS 改善。", "details": "復發維持之重要基石研究。"},
    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], "name": "📚 ARIEL3", "type": "Milestone", "summary": "復發維持。Rucaparib 顯著改善多個分層族群 PFS。", "details": "支持鉑類敏感復發後之二線維持。"},
    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], "name": "📚 SOLO2", "type": "Milestone", "summary": "復發維持。OS 51.7m vs 38.8m (HR 0.74)，具臨床意義獲益。", "details": "BRCA 變異族群復發維持代表性數據。"},
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive (wt)"], "name": "📚 DUO-O", "type": "Milestone", "summary": "一線組合。PFS 顯著改善：提示 IO 需併用 PARPi/VEGF 組合。", "details": "非 tBRCAm 族群。顯示組合拳在卵巢癌免疫之潛力。"},
    {"cancer": "Ovarian", "pos": "R-TX (PROC)", "sub_pos": ["Platinum-Resistant"], "name": "📚 MIRASOL (FRα ADC)", "type": "Milestone", "summary": "後線(PROC)。OS 16.4m vs 12.7m (HR 0.67)，ORR 42.3%。", "details": "FRα 高表現 PROC。首個證明 OS 獲益之 ADC，改變指引。"},
    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 LION (NEJM 2019)", "type": "Milestone", "summary": "初治手術。完全切除且臨床 LN 陰性，清掃無 OS/PFS 獲益。", "details": "降低併發症，不建議對臨床淋巴結陰性者常規清掃。"},
]

# --- 3. 進行中試驗 (📍 Ongoing - 極量化細節 + 標籤優化) ---
ongoing_trials = [
    {"cancer": "Ovarian", "name": "FRAmework-01 (LY4170156)", "pharma": "Eli Lilly", "drug": "LY4170156 + Bevacizumab", "pos": "R-TX (PROC)", "sub_pos": ["Platinum-Resistant"], "type": "Ongoing",
     "rationale": "標靶 FRα ADC，搭載類微管蛋白 Payload。透過聯用 Bevacizumab 產生血管重塑協同作用 (Synergy)，提升 ADC 在實體腫瘤內的滲透深度，並透過旁觀者效應殺傷 FRα 低表達鄰近細胞，旨在克服 PARPi 耐藥後 PROC 患者之 Unmet Needs。",
     "dosing": "實驗組：LY4170156 3mg/kg IV + Bevacizumab 15mg/kg IV Q3W。對照組：醫師選擇單藥化療 (Pacli, PLD, Gem) 或 MIRV。",
     "inclusion": ["18歲以上 HG Serous / Carcinosarcoma 卵巢癌。", "中央實驗室確認 FRα 表達陽性。", "最後一劑鉑類後 90–180 天內惡化 (PROC)。", "先前接受過 1–3 線全身治療線數。"],
     "exclusion": ["先前用過帶有 Topoisomerase I 抑制劑 Payload 之 ADC (如 Enhertu)。", "活動性間質性肺病 (ILD) 或需類固醇治療之肺炎病史。", "具有臨床顯著蛋白尿 (UPCR ≥ 2.0)。"], "ref": "NCT06536348"},
    
    {"cancer": "Ovarian", "name": "REJOICE-Ovarian01", "pharma": "Daiichi Sankyo", "drug": "R-DXd (Raludotatug Deruxtecan)", "pos": "R-TX (PROC)", "sub_pos": ["Platinum-Resistant"], "type": "Ongoing",
     "rationale": "標靶 Cadherin-6 (CDH6) ADC，搭載強效 DXd (Topo I inhibitor) 載荷。具備極高 DAR (8) 與強力旁觀者效應，專攻高度異質性且 CDH6 高表達之 PROC 腫瘤，解決傳統化療反應率低落之瓶頸。",
     "dosing": "實驗組：R-DXd 5.6mg/kg IV Q3W。對照組：研究者選擇單藥化療 (Pacli, PLD, or Topo)。",
     "inclusion": ["組織學 HG Serous 或 Endometrioid PROC。", "先前接受 1-4 線系統性治療。", "需提供切片以進行中央實驗室 CDH6 判定分層。", "需曾用過 Bevacizumab (除非有禁忌症)。"],
     "exclusion": ["Low-grade / Clear cell / Mucinous 腫瘤。", "基線 Grade ≥2 周邊神經病變。", "心功能不全 (LVEF < 50%)。", "ILD/肺部病史。"], "ref": "JCO 2024"},
    
    {"cancer": "Ovarian", "name": "TroFuse-021", "pharma": "MSD", "drug": "Sac-TMT (MK-2870)", "pos": "P-MT", "sub_pos": ["HRD positive (wt)", "HRD negative / pHRD"], "type": "Ongoing",
     "rationale": "標靶 Trop-2 ADC。結合 Beva 微環境調節與 ADC 誘導之免疫原性細胞死亡 (ICD) 效應，優化 pHRD/HRD+ 族群在一線含鉑化療後維持獲益，填補 PARPi 對此族群效果有限的缺口。",
     "dosing": "實驗臂1：Sac-TMT 單藥維持。實驗臂2：Sac-TMT + Beva 15mg/kg Q3W。對照臂：Standard Bevacizumab 維持。",
     "inclusion": ["新診斷 FIGO Stage III/IV 卵巢/輸卵管癌。", "HRD 狀態由中央實驗室判定 (包含 pHRD)。", "一線含鉑化療後達 CR 或 PR 狀態。", "可供檢測之 Trop-2 組織。"],
     "exclusion": ["BRCA 突變。", "先前用過針對 Trop-2 之 ADC 藥物。", "嚴重的自體免疫疾病或 IBD 病史。"], "ref": "ENGOT-ov85"},

    {"cancer": "Endometrial", "name": "MK2870-033", "pharma": "MSD", "drug": "Sac-TMT + Pembrolizumab", "pos": "P-MT", "sub_pos": ["IO Maintenance"], "type": "Ongoing",
     "rationale": "標靶 Trop-2 ADC 協同 PD-1 抑制劑。透過免疫重塑提升 Pembrolizumab 在 pMMR 或 NSMP 族群的應答深度，挑戰一線維持之 OS 標竿。",
     "inclusion": ["pMMR 子宮內膜癌 (中心檢測確認)。", "FIGO III/IV 一線含鉑+Pembro後達 CR/PR。", "先前未針對復發進行過系統性治療。"],
     "exclusion": ["先前接受過晚期系統性 IO 治療。", "自體免疫疾病史。"], "ref": "ESMO 2025"},
    
    {"cancer": "Endometrial", "name": "GU-US-682-6769", "pharma": "Gilead", "drug": "SG (Trodelvy)", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "type": "Ongoing",
     "rationale": "標靶 Trop-2 ADC。利用 SN-38 載荷引發 DNA 損傷，專攻鉑類與免疫失敗救援，具強力旁觀者效應對抗異質性病灶。",
     "inclusion": ["復發性 EC (不含肉瘤)。", "鉑類與 PD-1 失敗後進展。", "充分器官功能 (ANC ≥1500, PLT ≥100k)。"],
     "exclusion": ["先前用過 Trop-2 ADC。", "活動性 CNS 轉移。"], "ref": "JCO 2024"},

    {"cancer": "Ovarian", "name": "DS8201-772 (Enhertu)", "pharma": "AstraZeneca", "drug": "T-DXd (Trastuzumab Deruxtecan)", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], "type": "Ongoing",
     "rationale": "標靶 HER2 ADC。救援化療穩定後之精準維持首選。超高 DAR (8) 優勢清除 HER2 表現殘留病灶，延長緩解時間。",
     "inclusion": ["HER2 IHC 1+/2+/3+ 確認。", "PSOC 救援化療達穩定 (Non-PD)。", "LVEF ≥ 50%。"],
     "exclusion": ["ILD 肺部病史或疑似肺部纖維化。"], "ref": "JCO 2024"},

    {"cancer": "Ovarian", "name": "DOVE (APGOT-OV07)", "pharma": "GSK", "drug": "Dostarlimab + Bevacizumab", "pos": "R-TX (PROC)", "sub_pos": ["Platinum-Resistant"], "type": "Ongoing",
     "rationale": "針對透明細胞癌 (OCCC)。利用 IO + anti-VEGF 雙重打擊，改善其特有之免疫抑制環境。",
     "inclusion": ["組織學 OCCC > 50%。", "鉑類抗藥性 (PFI < 12m)。", "RECIST v1.1 可測量病灶。"],
     "exclusion": ["先前用過任何免疫治療 (PD-1/L1)。"], "ref": "JCO 2025"},

    {"cancer": "Cervical", "name": "innovaTV 301", "pharma": "Seagen", "drug": "Tisotumab Vedotin (Tivdak)", "pos": "R-TX", "sub_pos": ["2L / 3L Therapy"], "type": "Ongoing",
     "rationale": "標靶 Tissue Factor (TF) ADC。搭載 MMAE 載荷，旨在克服後線子宮頸癌化療耐藥性，改善生存期。",
     "inclusion": ["復發/轉移子宮頸癌。", "先前接受 1–2 線治療後進展。"],
     "exclusion": ["嚴重眼疾或角膜炎。", "活動性出血風險。"], "ref": "NEJM 2024"}
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
    st.session_state.selected_trial = ongoing_trials[0]['name']

with st.sidebar:
    st.markdown("<h3 style='color: #6A1B9A;'>🤖 AI 實證媒合助理</h3>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 病歷深度數據比對", expanded=True):
        p_notes = st.text_area("輸入病歷 (期別/標記/組織學)", height=250)
        if st.button("🚀 開始分析"):
            if api_key and p_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = get_gemini_model()
                    if model:
                        prompt = f"分析病歷：{p_notes}。參考實證：{milestone_db} 及進行中：{ongoing_trials}。請判定階段並建議適合治療路徑與理由。"
                        st.write(model.generate_content(prompt).text)
                    else: st.error("找不到可用 AI 模型。")
                except Exception as e: st.error(f"AI 異常: {e}")

# --- 6. 主頁面：導航儀表板 ---
st.markdown("<div class='main-title'>婦癌臨床導航儀表板 (2026 實證與研究全整合)</div>", unsafe_allow_html=True)
cancer_type = st.radio("第一步：選擇癌症類型", ["Endometrial", "Ovarian", "Cervical"], horizontal=True)

st.subheader("第二步：點擊 📚 實證里程碑 或 📍 招募中試驗 (與 SoC 同步對照)")
cols = st.columns(len(guidelines_nested[cancer_type]))
stages_data = guidelines_nested[cancer_type]

for i, stage in enumerate(stages_data):
    with cols[i]:
        st.markdown(f"""<div class='big-stage-card card-{stage['css']}'><div class='big-stage-header header-{stage['css']}'>{stage['header']}</div>""", unsafe_allow_html=True)
        for sub in stage['subs']:
            st.markdown(f"""<div class='sub-block'><div class='sub-block-title'>📘 {sub['title']}</div><div class='sub-block-content'>{sub['content']}</div>""", unsafe_allow_html=True)
            
            # A. 顯示實證里程碑 (📚)
            rel_milestones = [m for m in milestone_db if m["cancer"] == cancer_type and m["pos"] == stage["id"] and any(s in sub["title"] for s in m["sub_pos"])]
            for m in rel_milestones:
                with st.popover(f"📚 {m['name']}", use_container_width=True):
                    st.success(f"**藥物:** {m['drug']}\n\n**詳細數據:** {m['summary']}\n\n**臨床意義:** {m['details']}")
            
            # B. 顯示招募中試驗 (📍)
            rel_trials = [t for t in ongoing_trials if t["cancer"] == cancer_type and t["pos"] == stage["id"] and any(s in sub["title"] for s in t["sub_pos"])]
            for t in rel_trials:
                label = f"📍 {t['pharma']} | {t['name']} | {t['drug']}"
                ukey = f"btn_{t['name']}_{stage['id']}_{sub['title'].replace(' ', '')}"
                with st.popover(label, use_container_width=True):
                    if st.button("📊 詳細細節報告", key=ukey):
                        st.session_state.selected_trial = t['name']
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 7. 招募中試驗深度報告看板 ---
st.divider()
all_list = milestone_db + ongoing_trials
selected_name = st.selectbox("🎯 切換試驗深度分析報告：", [t["name"] for t in all_list if t["cancer"] == cancer_type], index=0)
t = next(it for it in all_list if it["name"] == selected_name)

st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #E0E0E0; padding-bottom:10px; font-weight:900;'>📋 {t['name']} 深度數據分析</h2>", unsafe_allow_html=True)

if t["type"] == "Milestone":
    r1, r2 = st.columns([1, 1])
    with r1:
        st.markdown("<div style='background:#ECEFF1; border-left:10px solid #455A64; padding:15px; border-radius:10px;'><b>📈 實證摘要 (Summary)</b></div>", unsafe_allow_html=True)
        st.write(f"**藥物配方:** {t['drug']}")
        st.success(t['summary'])
    with r2:
        st.markdown("<div style='background:#FFF8E1; border-left:10px solid #FBC02D; padding:15px; border-radius:10px;'><b>💡 臨床解析 (Insights)</b></div>", unsafe_allow_html=True)
        st.info(t['details'])
else:
    r1, r2 = st.columns([1.3, 1])
    with r1:
        st.markdown("<div style='background:#E3F2FD; border-left:10px solid #1976D2; padding:15px; border-radius:10px;'><b>💉 Rationale & Dosing (機轉與給藥)</b></div>", unsafe_allow_html=True)
        st.write(f"**核心藥物:** {t['drug']}")
        st.write(f"**劑量方案:** {t.get('dosing', '詳見 Protocol')}")
        st.success(t['rationale'])
        
    with r2:
        st.markdown("<div style='background:#E8F5E9; border-left:8px solid #2E7D32; padding:15px; border-radius:10px;'><b>✅ Inclusion Criteria (納入標準)</b></div>", unsafe_allow_html=True)
        for inc in t.get('inclusion', []): st.write(f"• **{inc}**")
        st.markdown("<div style='background:#FFEBEE; border-left:8px solid #C62828; padding:15px; border-radius:10px; margin-top:10px;'><b>❌ Exclusion Criteria (排除標準)</b></div>", unsafe_allow_html=True)
        for exc in t.get('exclusion', []): st.write(f"• **{exc}**")
st.markdown("</div>", unsafe_allow_html=True)
