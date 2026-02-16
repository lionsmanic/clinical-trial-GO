import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床導航與實證圖書館 (2026 最終全功能擴充版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=Roboto:wght@400;700;900&display=swap');
    
    /* === 極致緊緻化 UI === */
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

    /* 大階段方塊：高度隨內容撐開 */
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

    /* 子區塊 (SoC 與分子亞型)：緊貼標題 */
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
        margin-bottom: 2px;
    }

    /* 階段顏色定義 */
    .card-p-tx { border-color: #2E7D32; }
    .header-p-tx { background: linear-gradient(135deg, #43A047, #2E7D32); }
    .card-p-mt { border-color: #1565C0; }
    .header-p-mt { background: linear-gradient(135deg, #1E88E5, #1565C0); }
    .card-r-tx { border-color: #E65100; }
    .header-r-tx { background: linear-gradient(135deg, #FB8C00, #E65100); }
    .card-r-mt { border-color: #6A1B9A; }
    .header-r-mt { background: linear-gradient(135deg, #8E24AA, #6A1B9A); }

    /* --- 標記按鈕：深黑色字體 (#1A1A1A) 與 高對比淺底配色 --- */
    .stPopover button { 
        font-weight: 900 !important; font-size: 12px !important; 
        border-radius: 4px !important; margin-top: 1px !important;
        padding: 1px 6px !important; width: 100% !important; 
        text-align: left !important; color: #1A1A1A !important; 
        border: 1px solid rgba(0,0,0,0.15) !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
    }
    
    /* 📚 已發表實證 (Milestone) 色彩 */
    .stPopover button[aria-label*="📚"] { background: #ECEFF1 !important; border-left: 5px solid #455A64 !important; }

    /* 📍 招募中試驗 (Ongoing) 藥廠配色飾邊 */
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

# --- 1. 指引與分子路徑大綱 ---
guidelines_nested = {
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "POLEmut (超突變型)", "content": "預後極佳。早期可考慮治療降階 (De-escalation)，避免放化療之毒性。"},
            {"title": "MMRd / MSI-H", "content": "免疫高度敏感。晚期一線方案：Chemo + PD-1 (GY018/RUBY) 獲益顯著。"},
            {"title": "p53abn (Copy-number high)", "content": "侵襲性最強。早期建議升級治療；Serous 需驗 HER2。"},
            {"title": "NSMP (最大宗亞型)", "content": "<span style='color:#6A1B9A; font-weight:800;'>分子判定：IHC MMR Intact / p53 wt / POLE wt。</span><br>1. 分層關鍵：預後取決於 ER 狀態、Grade 3 與是否存在顯著 LVSI。<br>2. 決策重點：NSMP ER-negative 屬高風險；ER-positive 且進展慢者可考慮荷爾蒙治療 (Progestin/AI)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "IO Maintenance", "content": "一線 Chemo-IO 後，延續 IO 維持直至進展 (PD)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "MMRd / MSI-H", "content": "PD-1 抑制劑單藥高反應。"}, {"title": "pMMR / NSMP", "content": "標準二線方案：Pembrolizumab + Lenvatinib (SoC)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "維持當前有效標靶/免疫方案。"}]}
    ],
    "Ovarian": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "HGSC / Endometrioid", "content": "Surgery + Carboplatin/Paclitaxel x6 ± Bevacizumab"},
            {"title": "Mucinous (MOC) 鑑別", "content": "1. 判定：CK7+/SATB2-。 2. 型態：Expansile (早期可保守) vs Infiltrative (高復發風險)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "BRCA mutated", "content": "Olaparib 單藥或 Olaparib+Bev (若含Bev史)"},
            {"title": "HRD positive (wt)", "content": "優先選用 Olaparib+Bev 或 Niraparib 單藥維持"},
            {"title": "HRD negative / pHRD", "content": "有用 Bev 則續用；未用則觀察，視風險評估 Niraparib"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "PSOC / PROC 分流", "content": "依 PFI 判定。標靶檢測看 FRα 或 HER2。"},
            {"title": "MOC 晚期/復發", "content": "化療抗性強。考慮 GI-like 方案、Trial 或抗 HER2。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Platinum Sensitive", "content": "救援緩解後選 PARPi 維持治療。"}]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "Early (Surgery)", "content": "傳統開腹根治術 (LACC試驗)。低風險者可考慮 SHAPE 試驗之單純全子宮切除。"},
            {"title": "CCRT (LA / 1L)", "content": "同步化放療 (CCRT)。高風險者考慮同步 IO (KEYNOTE-A18) 或誘導化療 (INTERLACE)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Metastatic IO Maint", "content": "轉移性一線後延續 Pembro 維持直到 PD"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "1L Recurrent", "content": "Pembro + 化療 ± Bev (CPS≥1)。"},
            {"title": "2L / 3L Therapy", "content": "Tivdak (Tisotumab vedotin) 或 Cemiplimab"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "有效方案持續給藥直至進展"}]}
    ]
}

# --- 2. 實證里程碑資料庫 (📚 Milestone Library - 深度擴充) ---
milestone_db = [
    # Endometrial
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H"], "name": "📚 RUBY (Dostarlimab)", "drug": "Dostarlimab + CP", 
     "summary": "里程碑分析：dMMR 死亡風險顯著降低 68% (HR 0.32)。全人群 mOS 從 28.2 個月延長至 44.6 個月 (HR 0.69)。對於 pMMR 族群加入 Niraparib 維持可提升 PFS。"},
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H", "NSMP"], "name": "📚 NRG-GY018 (KEYNOTE-868)", "drug": "Pembrolizumab + CP", 
     "summary": "dMMR 族群疾病進展風險降低 70% (HR 0.30)。pMMR 族群同樣展示顯著 PFS 改善 (HR 0.54)。FDA 於 2024 年核准用於所有晚期患者。"},
    {"cancer": "Endometrial", "pos": "P-MT", "sub_pos": ["IO Maintenance"], "name": "📚 DUO-E", "drug": "Durvalumab +/- Olaparib", 
     "summary": "pMMR 族群亮點：Durvalumab+Olaparib 三藥聯合將 PFS HR 降至 0.57，優於單用 IO。提示 PARP 抑制劑在 pMMR 患者中具有協同效應。"},
    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["pMMR / NSMP"], "name": "📚 KEYNOTE-775", "drug": "Pembro + Lenvatinib", 
     "summary": "確立二線標準：5年追蹤顯示 pMMR 患者 OS 獲益持久 (16.7% vs 7.3%)。"},
    
    # Ovarian
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutated"], "name": "📚 SOLO-1 (Olaparib)", "drug": "Olaparib", 
     "summary": "7年追蹤數據：實驗組仍有 67% 患者存活，PFS HR 0.33，顯示對於 BRCAm 患者具備潛在「治癒」能力。"},
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive (wt)"], "name": "📚 PAOLA-1", "drug": "Olaparib + Bevacizumab", 
     "summary": "HRD+ 族群 (無論 BRCA) 獲益最大，5年 OS 顯著改善 (HR 0.62)。對於 HRD- 患者加入 Olaparib 無額外好處。"},
    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PSOC / PROC 分流"], "name": "📚 MIRASOL", "drug": "Mirvetuximab Soravtansine", 
     "summary": "PROC 歷史突破：首個證明在 FRα 高表現 PROC 患者中顯著延長 OS (HR 0.67) 的 ADC 試驗。"},
    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 DESKTOP III", "drug": "Secondary Cytoreduction", 
     "summary": "符合 AGO Score 的 PSOC 患者進行二次減積手術顯著延長 mOS 至 53.7 個月 (vs 46.0m)。"},

    # Cervical
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["CCRT (LA / 1L)"], "name": "📚 KEYNOTE-A18", "drug": "Pembrolizumab + CCRT", 
     "summary": "LACC 新標準：36個月總體存活率提升至 82.6% (HR 0.67)，死亡風險降低 33%。"},
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["CCRT (LA / 1L)"], "name": "📚 INTERLACE", "drug": "Induction Chemotherapy", 
     "summary": "老藥新用價值：標準 CCRT 前加 6週誘導化療顯著提升 5年 OS (HR 0.60)。"},
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Early (Surgery)"], "name": "📚 LACC Trial", "drug": "MIS vs Open", 
     "summary": "典範轉移：微創手術復發/死亡率顯著較高 (HR 6.00)，將開腹手術重新確立為根治標準。"},
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Early (Surgery)"], "name": "📚 SHAPE Trial", "drug": "Simple Hysterectomy", 
     "summary": "降階策略：針對腫瘤 <2cm 低風險者，單純切除在復發率上不劣於根治術，且副作用較低。"},
]

# --- 3. 進行中臨床試驗資料庫 (📍 Ongoing Trials - 8 核心) ---
ongoing_trials = [
    {"cancer": "Ovarian", "name": "FRAmework-01 (LY4170156)", "pharma": "Eli Lilly", "drug": "LY4170156 + Bev", "pos": "R-TX", "sub_pos": ["PSOC / PROC 分流"], 
     "rationale": "標靶 FRα ADC，搭載類微管蛋白載荷。聯用 Bevacizumab 可產生血管調節協同作用 (Synergy)，提升 ADC 滲透並透過旁觀者效應 (Bystander Effect) 殺傷異質性腫瘤，專攻 PARPi 耐藥後需求。",
     "dosing": {"Exp Arm (Part A/B)": "LY4170156 3 mg/kg IV + Bevacizumab 15 mg/kg IV Q3W。", "Control A (PROC)": "TPC (Pacli/PLD/Gem/Top) 或 MIRV。", "Control B (PSOC)": "Standard Platinum doublet + Bev 15 mg/kg Q3W。"},
     "outcomes": {"ORR": "Ph 1/2: ~35-40%", "HR": "Phase 3 Ongoing", "CI": "NCT06536348"},
     "inclusion": ["HG Serous / Carcinosarcoma 之卵巢/輸卵管癌。", "FRα Expression Positive (中央實驗室檢測)。", "Part A (PROC): 最後一劑鉑類後 90–180 天惡化。", "Part B (PSOC): 最後一劑鉑類後 >180 天惡化且曾用過 PARPi。"],
     "exclusion": ["先前用過 Topo I ADC (如 Enhertu)。", "具有臨床顯著蛋白尿 (UPCR ≥ 2.0)。", "活動性 ILD 病史。"], "ref": "NCT06536348"},
    
    {"cancer": "Ovarian", "name": "REJOICE-Ovarian01", "pharma": "Daiichi Sankyo", "drug": "R-DXd", "pos": "R-TX", "sub_pos": ["PSOC / PROC 分流"], 
     "rationale": "標靶 CDH6 ADC，搭載強效 DXd 載荷。具備極高 DAR (8) 與強力旁觀者效應，專攻高度異質性的 PROC 腫瘤環境，克服前線化療耐藥性並改善生存。",
     "dosing": {"Exp Arm": "R-DXd 5.6mg/kg IV Q3W。", "Control Arm": "Investigator's Choice 單藥化療 (Paclitaxel/PLD/Topotecan)。"},
     "outcomes": {"ORR": "46.0% (Ph1 Update)", "mPFS": "7.1m", "HR": "Phase 3", "CI": "NCT06161025"},
     "inclusion": ["HG Serous 或 Endometrioid PROC 卵巢癌。", "曾接受過 1-4 線系統性治療。", "需曾用過 Bevacizumab (除非有禁忌症)。"],
     "exclusion": ["Low-grade 腫瘤。", "具有 ILD 肺部病史或疑似症狀。", "LVEF < 50%。"], "ref": "JCO 2024"},
    
    {"cancer": "Ovarian", "name": "TroFuse-021 (MK-2870)", "pharma": "MSD", "drug": "Sac-TMT", "pos": "P-MT", "sub_pos": ["HRD negative / pHRD"], 
     "rationale": "標靶 Trop-2 ADC。結合 Beva 微環境調節與 ADC 誘導的 ICD 效應，旨在優化 pHRD 族群在一線維持時的獲益，填補 PARPi 反應不足之需求。",
     "dosing": {"Arm 1": "Sac-TMT 單藥維持。", "Arm 2": "Sac-TMT + Beva 15mg/kg Q3W。", "Arm 3": "Observation / Bevacizumab 獨自維持。"},
     "outcomes": {"ORR": "Est 40% (pHRD)", "mPFS": "招募中", "HR": "Phase 3", "CI": "NCT06241729"},
     "inclusion": ["新診斷 FIGO III/IV 卵巢癌。", "HRD negative (pHRD) 且 BRCA 野生型。", "一線含鉑化療後達 CR 或 PR 狀態。"],
     "exclusion": ["BRCA 突變或 HRD 陽性。", "嚴重炎症性腸道疾病 (IBD)。", "先前用過 Trop-2 ADC。"], "ref": "ENGOT-ov85"},
    
    {"cancer": "Ovarian", "name": "DOVE (APGOT-OV07)", "pharma": "GSK", "drug": "Dostarlimab + Bev", "pos": "R-TX", "sub_pos": ["PSOC / PROC 分流"], 
     "rationale": "針對透明細胞癌 (OCCC) 的免疫抑制環境。利用 PD-1 阻斷與 VEGF 抑制之雙重打擊，恢復 T 細胞浸潤並誘發應答。",
     "dosing": {"Combo": "Dostarlimab 500mg Q3W x4 -> 1000mg Q6W + Bev Q3W。", "Control": "醫師選擇單藥化療 (Gem/PLD/Taxel)。"},
     "outcomes": {"ORR": "40.2% (OCCC)", "mPFS": "8.2m", "HR": "0.58", "CI": "NCT06023862"},
     "inclusion": ["組織學 OCCC > 50%。", "鉑類抗藥性 (最後一劑後 12個月內復發)。", "先前治療線數 ≤ 5 線。"],
     "exclusion": ["先前用過任何免疫治療。", "臨床顯著腸阻塞史。"], "ref": "JCO 2025"},

    {"cancer": "Ovarian", "name": "DS8201-772 (Enhertu)", "pharma": "AstraZeneca", "drug": "T-DXd", "pos": "R-MT", "sub_pos": ["Platinum Sensitive"], 
     "rationale": "標靶 HER2 ADC. 作為救援化療穩定後之精準維持首選。超高 DAR (8) 優勢能有效清除 HER2 表現癌細胞之殘留病灶。",
     "dosing": {"Standard": "T-DXd 5.4mg/kg IV Q3W。", "Combo": "T-DXd 5.4mg/kg + Beva 15mg/kg Q3W。"},
     "outcomes": {"ORR": "46.3% (IHC 3+)", "mPFS": "10.4m", "HR": "0.42", "CI": "NCT04482309"},
     "inclusion": ["HER2 IHC 1+/2+/3+ 確認。", "PSOC 救援化療達穩定 (Non-PD)。", "LVEF ≥ 50%。"],
     "exclusion": ["ILD 肺部病史。", "先前接受過 HER2 ADC。"], "ref": "JCO 2024"},

    {"cancer": "Endometrial", "name": "MK2870-033", "pharma": "MSD", "drug": "Sac-TMT + Pembro", "pos": "P-MT", "sub_pos": ["IO Maintenance", "NSMP (最大宗亞型)"], 
     "rationale": "標靶 Trop-2 ADC 協同 PD-1. 透過免疫調節強化 Pembrolizumab 在 pMMR 或 NSMP 族群的長期應答與持續緩解。",
     "dosing": {"Induction": "Carbo+Pacli+Pembro Q3W。", "Maintenance": "Pembro 400 mg Q6W + Sac-TMT 5 mg/kg Q6W。"},
     "outcomes": {"ORR": "Est 35% Ph 2", "HR": "Ongoing", "CI": "NCT06132958"},
     "inclusion": ["pMMR 子宮內膜癌 (中心檢測)。", "FIGO III/IV 一線含鉑+Pembro後達 CR/PR。"],
     "exclusion": ["子宮肉瘤 (Sarcoma)。", "先前接受過晚期系統性 IO 治療。"], "ref": "ESMO 2025"},
    
    {"cancer": "Endometrial", "name": "GU-US-682-6769", "pharma": "Gilead", "drug": "SG (Trodelvy)", "pos": "R-TX", "sub_pos": ["pMMR / NSMP", "p53abn (Copy-number high)"], 
     "rationale": "標靶 Trop-2 ADC. 利用 SN-38 載荷引發 DNA 損傷，專攻鉑類與免疫失敗後之二/三線救援，具備強效旁觀者效應。",
     "dosing": {"Exp": "SG 10mg/kg (D1, D8 Q21D)。", "Control": "TPC (Doxo/Taxel)。"},
     "outcomes": {"ORR": "28.5%", "mPFS": "5.6m", "HR": "0.64", "CI": "NCT03964727"},
     "inclusion": ["復發性 EC (非肉瘤)。", "鉑類與 PD-1 失敗後進展。"],
     "exclusion": ["先前用過 Trop-2 ADC。", "活動性 CNS 轉移。"], "ref": "JCO 2024"},

    {"cancer": "Cervical", "name": "innovaTV 301", "pharma": "Seagen", "drug": "Tivdak", "pos": "R-TX", "sub_pos": ["2L / 3L Therapy"], 
     "rationale": "標靶 Tissue Factor (TF) ADC. 旨在克服後線子宮頸癌化療耐藥性，改善生存預後 (OS)。",
     "dosing": {"Exp Arm": "Tisotumab vedotin 2.0mg/kg Q3W。", "Control Arm": "醫師選擇單藥化療 (TPC)。"},
     "outcomes": {"ORR": "17.8%", "mPFS": "4.2m", "HR": "0.70 (OS)", "CI": "NEJM 2024"},
     "inclusion": ["復發/轉移子宮頸癌。", "先前接受 1–2 線治療後進展。"],
     "exclusion": ["嚴重眼疾/角膜炎。", "活動性出血傾向。"], "ref": "NEJM 2024"}
]

# --- 4. AI 穩定模型巡邏邏輯 ---
def get_gemini_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target_model = None
        for m in available_models:
            if 'gemini-1.5-flash' in m:
                target_model = m
                break
        if not target_model:
            for m in available_models:
                if 'gemini-1.5-pro' in m or 'gemini-pro' in m:
                    target_model = m
                    break
        if target_model: return genai.GenerativeModel(target_model)
    except: return None

# --- 5. 側邊欄 ---
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = ongoing_trials[0]['name']

with st.sidebar:
    st.markdown("<h3 style='color: #6A1B9A;'>🤖 AI 實證媒合助理</h3>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 患者數據深度分析", expanded=True):
        p_notes = st.text_area("輸入病歷摘要 (含分子/病理)", height=250)
        if st.button("🚀 開始分析"):
            if api_key and p_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = get_gemini_model()
                    if model:
                        prompt = f"分析病歷：{p_notes}。請參考里程碑實證：{milestone_db} 與招募中試驗：{ongoing_trials}。提供最佳路徑建議與理由。"
                        st.write(model.generate_content(prompt).text)
                    else: st.error("找不到可用 AI 模型。")
                except Exception as e: st.error(f"AI 異常: {e}")

# --- 6. 主頁面：緊湊導航儀表板 ---
st.markdown("<div class='main-title'>婦癌臨床試驗導航儀表板 (指引實證與研究整合版)</div>", unsafe_allow_html=True)
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
                    st.success(f"**藥物:** {m['drug']}\n\n**關鍵實證:** {m['summary']}")
            
            # B. 招募中試驗 (📍)
            rel_trials = [t for t in ongoing_trials if t["cancer"] == cancer_type and t["pos"] == stage["id"] and any(s in sub["title"] for s in t["sub_pos"])]
            for t in rel_trials:
                label = f"📍 {t['pharma']} | {t['name']} | {t['drug']}"
                ukey = f"btn_{t['name']}_{stage['id']}_{sub['title'].replace(' ', '')}"
                with st.popover(label, use_container_width=True):
                    st.markdown(f"#### ✨ {t['name']} 招募解析")
                    st.info(f"**Rationale:** {t['rationale'][:160]}...")
                    if st.button("📊 開啟深度分析報告", key=ukey):
                        st.session_state.selected_trial = t['name']
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 7. 深度分析看板 ---
st.divider()
t_options = [t["name"] for t in ongoing_trials if t["cancer"] == cancer_type]
if t_options:
    try: curr_idx = t_options.index(st.session_state.selected_trial)
    except: curr_idx = 0
    selected_name = st.selectbox("🎯 切換招募中試驗之詳細報告：", t_options, index=curr_idx)
    t = next(it for it in ongoing_trials if it["name"] == selected_name)

    st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #E0E0E0; padding-bottom:10px; font-weight:900;'>📋 {t['name']} 招募中試驗深度報告</h2>", unsafe_allow_html=True)

    r1, r2 = st.columns([1.3, 1])
    with r1:
        st.markdown("<div style='background:#E3F2FD; border-left:10px solid #1976D2; padding:15px; border-radius:10px;'><b>💉 Dosing Protocol & Rationale</b></div>", unsafe_allow_html=True)
        st.write(f"**核心藥物:** {t['drug']}")
        for arm, details in t['dosing'].items(): st.write(f"🔹 **{arm}**: {details}")
        st.markdown("---")
        st.success(f"**機轉實證 (Rationale):** {t['rationale']}")
        

    with r2:
        st.markdown("<div style='background:#FFF8E1; border-left:8px solid #FBC02D; padding:15px; border-radius:10px;'><b>📈 Efficacy & Outcomes (Ph1/2)</b></div>", unsafe_allow_html=True)
        st.markdown(f"""
            <div style='text-align:center; background:white; padding:15px; border:2px solid #FFE082; border-radius:12px;'>
                <div style='font-size: 14px; color: #795548; font-weight:700; margin-bottom:5px;'>Hazard Ratio (Expected) / NCT</div>
                <div class='hr-big-val'>{t['outcomes'].get('HR', 'Ongoing')}</div>
                <div style='font-size:18px; color:#5D4037; font-weight:700;'>{t['outcomes'].get('CI', t['outcomes'].get('CI', ''))}</div>
            </div>
        """, unsafe_allow_html=True)
        st.write(f"**ORR:** {t['outcomes'].get('ORR', 'TBD')} | **mPFS:** {t['outcomes'].get('mPFS', 'Ongoing')}")
        

    st.divider()
    r3, r4 = st.columns(2)
    with r3:
        st.markdown("<div style='background:#E8F5E9; border-left:8px solid #2E7D32; padding:15px; border-radius:10px;'><b>✅ Inclusion Criteria (納入標準)</b></div>", unsafe_allow_html=True)
        for inc in t.get('inclusion', []): st.write(f"• **{inc}**")
    with r4:
        st.markdown("<div style='background:#FFEBEE; border-left:8px solid #C62828; padding:15px; border-radius:10px;'><b>❌ Exclusion Criteria (排除標準)</b></div>", unsafe_allow_html=True)
        for exc in t.get('exclusion', []): st.write(f"• **{exc}**")
    st.markdown("</div>", unsafe_allow_html=True)
