import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床導航與實證圖書館 (2026 最終全方位整合版) ---
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

    .detail-section { background: white; border-radius: 18px; padding: 25px; border: 1px solid #CFD8DC; box-shadow: 0 10px 40px rgba(0,0,0,0.05); }
    .hr-big-val { font-family: 'Roboto', sans-serif; font-size: 48px !important; font-weight: 900; color: #D84315; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 指引導航數據庫：包含 MOC、PSOC/PROC 分流與子宮頸癌 ---
guidelines_nested = {
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "MMRd / MSI-H / dMMR", "content": "一線首選：Chemo + PD-1 (GY018/RUBY)。Dostarlimab 獲益極顯著。"},
            {"title": "NSMP / pMMR / MSS", "content": "排除分型。視 ER/Grade 權重決策；二線考慮 Pembro+Lenva。"},
            {"title": "POLEmut / p53abn", "content": "POLE: 最佳預後可降階；p53abn: 最差預後，需積極化放療。"}]},
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
            {"title": "PSOC (PFI > 6m)", "content": "鉑類敏感。含鉑雙藥化療 ± Bev。評估二次手術獲益。"},
            {"title": "PROC (PFI < 6m)", "content": "鉑類抗藥。單藥化療 ± Bev 或標靶 ADC (MIRASOL)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Platinum Sensitive Maint", "content": "救援緩解後續以 PARPi 維持治療。"}]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "CCRT (Locally Advanced)", "content": "同步化放療。高風險者同步 IO (A18) 或誘導化療 (INTERLACE)。"},
            {"title": "Early Stage (Surgery)", "content": "開腹根治術 (LACC)。低風險者選單純切除 (SHAPE)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Metastatic Maint", "content": "1L 轉移性 IO 方案後延續維持至進展。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "Recurrent / Metastatic", "content": "一線 Pembro + 化療 ± Bev。二線 ADC (Tivdak) 或 IO (EMPOWER)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "維持有效治療直至進展。"}]}
    ]
}

# --- 2. 實證里程碑 (📚 Milestone Library - 完整 24 項深度擴充) ---
milestone_db = [
    # 子宮內膜癌
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H / dMMR"], "name": "📚 RUBY (Dostarlimab)", "type": "Milestone", "drug": "Dostarlimab + CP", "summary": "FIGO III-IV/Recurrent。dMMR 死亡風險降 68% (HR 0.32)；全人群 mOS 44.6m vs 28.2m (HR 0.69, P<0.001)。ORR 顯著提升。", "details": "里程碑研究：確立一線 dMMR 免疫+化療之標準地位。"},
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H / dMMR", "NSMP / pMMR / MSS"], "name": "📚 NRG-GY018", "type": "Milestone", "drug": "Pembrolizumab + CP", "summary": "dMMR 族群 PFS HR 0.30；pMMR 亦顯著改善 (HR 0.54)。FDA 於 2024 全面核准所有 MMR 狀態適應症。", "details": "擴大一線免疫獲益至全人群。"},
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["NSMP / pMMR / MSS"], "name": "📚 DUO-E", "type": "Milestone", "drug": "Durvalumab ± Olaparib", "summary": "PFS 改善：三藥組 HR 0.57 (vs CP)；單藥 IO 組 HR 0.77。提示 PARPi 與 IO 在 pMMR 的維持協同效應。", "details": "建立「免疫+維持」策略。"},
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H / dMMR"], "name": "📚 AtTEnd", "type": "Milestone", "drug": "Atezolizumab + CP", "summary": "dMMR 獲益顯著 (HR 0.36)；全人群 OS HR 0.82 (邊緣顯著)。含有約 10% 癌肉瘤族群。", "details": "支持一線 PD-(L)1 證據鏈。"},
    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "name": "📚 KEYNOTE-775", "type": "Milestone", "drug": "Lenvatinib + Pembro", "summary": "二線(曾含鉑) pMMR：OS 17.4m vs 12.0m (HR 0.68)；5年 OS 率 16.7% vs 7.3%。", "details": "確立二線標準，但需重視毒性管理 (如高血壓、疲勞)。"},
    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "name": "📚 GARNET", "type": "Milestone", "drug": "Dostarlimab (單臂)", "summary": "dMMR/MSI-H ORR 達 45.5%，反應持久。中位反應持續時間 (DOR) 未達到。", "details": "奠定後線免疫單藥加速核准之基礎。"},

    # 子宮頸癌
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["CCRT (Locally Advanced)"], "name": "📚 KEYNOTE-A18", "type": "Milestone", "drug": "Pembrolizumab + CCRT", "summary": "局部晚期。36個月 OS 82.6% vs 74.8% (HR 0.67)。PFS 同時顯著獲益。", "details": "LACC 高風險群之新標竿治療。"},
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["CCRT (Locally Advanced)"], "name": "📚 INTERLACE", "type": "Milestone", "drug": "Induction Chemo (6wk)", "summary": "誘導化療：5年 OS 80% vs 72% (HR 0.60)。5年 PFS 72% vs 64% (HR 0.65)。", "details": "現成老藥價值：Carbo/Pacli 週療大幅改善生存。"},
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["CCRT (Locally Advanced)"], "name": "📚 CALLA (陰性)", "type": "Milestone", "drug": "Durvalumab + CCRT", "summary": "局部晚期。整體未達統計學 PFS 改善。HR 0.84。", "details": "提示免疫與放化療組合仍需更精準族群識別。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["1L Recurrent"], "name": "📚 KEYNOTE-826", "type": "Milestone", "drug": "Pembro + Chemo ± Bev", "summary": "持續/復發一線。全人群 OS HR 0.63；CPS≥1 HR 0.60。支持一線免疫全面介入。", "details": "R/M 一線核心標準。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["1L Recurrent"], "name": "📚 BEATcc", "type": "Milestone", "drug": "Atezolizumab + Chemo+Bev", "summary": "一線 R/M。mPFS 13.7m vs 10.4m (HR 0.62)；OS HR 0.68。", "details": "提供一線免疫併用新選項。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["2L / 3L Therapy"], "name": "📚 EMPOWER-Cx 1", "type": "Milestone", "drug": "Cemiplimab", "summary": "二線(曾含鉑)。OS 12.0m vs 8.5m (HR 0.69)；獲益不依賴 PD-L1 表現。", "details": "後線免疫單藥之關鍵數據。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["2L / 3L Therapy"], "name": "📚 innovaTV 301", "type": "Milestone", "drug": "Tisotumab Vedotin (ADC)", "summary": "二/三線。OS 11.5m vs 9.5m (HR 0.70)，ORR 17.8% vs 5.2%。", "details": "ADC 進入標準後線。需注意眼表、神經與出血副作用。"},
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Early Stage (Surgery)"], "name": "📚 SHAPE", "type": "Milestone", "drug": "Simple Hysterectomy", "summary": "早期低風險。3年骨盆復發率 2.5% vs 2.2% (不劣性達成)。副作用顯著降低。", "details": "支持手術降階：早期低風險可免於根治術。"},

    # 卵巢癌
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutated"], "name": "📚 SOLO-1 (Olaparib)", "type": "Milestone", "drug": "Olaparib 維持", "summary": "一線維持。7年 survival 67% (vs 46.5%, HR 0.33)；mPFS 未達到 vs 13.8m。", "details": "確立 BRCAm 患者具備臨床治癒之可能性。"},
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive (wt)", "HRD negative / pHRD"], "name": "📚 PRIMA", "type": "Milestone", "drug": "Niraparib 維持", "summary": "一線維持。整體 PFS HR 0.62；HRD+ 獲益最大 (HR 0.43)。5年無惡化率 35% vs 16%。", "details": "支持不限 BRCA 之一線維持概念。"},
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive (wt)"], "name": "📚 PAOLA-1", "type": "Milestone", "drug": "Olaparib + Bev", "summary": "一線維持。HRD+ 族群 5年 OS 率 75.2% vs 58.3% (HR 0.62)。", "details": "確立「PARPi + anti-VEGF」為 HRD+ 維持路徑。"},
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutated", "HRD positive (wt)"], "name": "📚 ATHENA–MONO", "type": "Milestone", "drug": "Rucaparib 維持", "summary": "一線維持。ITT PFS HR 0.52 (28.7m vs 11.3m)；HRD+ HR 0.47。", "details": "擴充 PARPi 一線維持證據鏈。"},
    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], "name": "📚 NOVA", "type": "Milestone", "drug": "Niraparib 維持", "summary": "復發維持。gBRCA HR 0.27；非 gBRCA HR 0.45。顯著延緩疾病進展。", "details": "復發維持之核心基石研究。"},
    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], "name": "📚 ARIEL3", "type": "Milestone", "drug": "Rucaparib 維持", "summary": "復發維持。Rucaparib 在所有分層(BRCA/HRD+/ITT)均 PFS 改善。", "details": "提供鉑類敏感復發後之二線維持選項。"},
    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], "name": "📚 SOLO2", "type": "Milestone", "drug": "Olaparib 維持", "summary": "復發維持(BRCA)。OS 51.7m vs 38.8m (HR 0.74)。長期生存獲益顯著。", "details": "BRCA 變異復發維持代表性數據。"},
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive (wt)"], "name": "📚 DUO-O", "type": "Milestone", "drug": "Durva+Ola+Bev", "summary": "一線組合。HRD+ 組 PFS 顯著獲益 (HR 0.49)。IO 需組合 PARPi/VEGF 較具潛力。", "details": "卵巢癌免疫之突破性組合設計。"},
    {"cancer": "Ovarian", "pos": "R-TX (PROC)", "sub_pos": ["Platinum-Resistant"], "name": "📚 MIRASOL (FRα ADC)", "type": "Milestone", "drug": "Mirvetuximab", "summary": "後線(PROC)。OS 16.4m vs 12.7m (HR 0.67)；PFS HR 0.65；ORR 42.3%。", "details": "首個證明 OS 獲益之 ADC 研究，改變抗藥型治療標準。"},
    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 LION (NEJM 2019)", "type": "Milestone", "drug": "No Lymphadenectomy", "summary": "完全切除且臨床 LN 陰性，清掃無生存獲益 (OS/PFS HR ~1.0) 且併發症多。", "details": "支持降低醫源性傷害：臨床 LN 陰性免清掃。"},
]

# --- 3. 招募中試驗 (📍 Ongoing - 極量化細節 + 標記優化) ---
ongoing_trials = [
    {"cancer": "Ovarian", "name": "FRAmework-01 (LY4170156)", "pharma": "Eli Lilly", "drug": "LY4170156 + Bevacizumab", "pos": "R-TX (PROC)", "sub_pos": ["Platinum-Resistant"], "type": "Ongoing",
     "rationale": "標靶 Folate Receptor alpha (FRα) ADC。搭載類微管蛋白 Payload。透過聯用 Bevacizumab 產生血管重塑協同作用 (Synergy)，提升藥物滲透深度並透過旁觀者效應殺傷低表達細胞，旨在克服 PARPi 耐藥後 PROC 患者之需求。",
     "dosing": "實驗組：LY4170156 3mg/kg IV + Bevacizumab 15mg/kg IV Q3W。對照組：醫師選擇單藥化療 (Pacli, PLD, Gem) 或 MIRV。",
     "inclusion": ["組織學 HG Serous / Carcinosarcoma 卵巢癌。", "經中央實驗室檢測確認 FRα 表達陽性。", "最後一劑鉑類後 90–180 天內惡化 (PROC)。", "先前接受過 1–3 線系統治療。"],
     "exclusion": ["先前曾用過帶有 Topoisomerase I 抑制劑 Payload 之 ADC (如 Enhertu)。", "活動性間質性肺病 (ILD) 或需類固醇治療之肺炎病史。", "具有臨床顯著蛋白尿 (UPCR ≥ 2.0)。"], "ref": "NCT06536348"},
    
    {"cancer": "Ovarian", "name": "REJOICE-Ovarian01", "pharma": "Daiichi Sankyo", "drug": "R-DXd (Raludotatug Deruxtecan)", "pos": "R-TX (PROC)", "sub_pos": ["Platinum-Resistant"], "type": "Ongoing",
     "rationale": "標靶 Cadherin-6 (CDH6) ADC，搭載強效 DXd 載荷。具備極高 DAR (8) 與強力旁觀者效應，專攻高度異質性之 PROC 腫瘤，解決傳統化療反應率低落之瓶頸。",
     "dosing": "實驗組：R-DXd 5.6mg/kg IV Q3W。對照組：研究者選擇單藥化療 (Pacli, PLD, or Topo)。",
     "inclusion": ["組織學 HG Serous 或 Endometrioid PROC。", "先前接受 1-4 線系統性治療。", "提供中央實驗室 CDH6 判定判定分層。", "需曾用過 Bevacizumab。"],
     "exclusion": ["Low-grade / Clear cell / Mucinous (原發)。", "基線 Grade ≥2 周邊神經病變。", "心功能不全 (LVEF < 50%)。", "ILD/肺部病史。"], "ref": "JCO 2024"},
    
    {"cancer": "Ovarian", "name": "TroFuse-021", "pharma": "MSD", "drug": "Sac-TMT (MK-2870)", "pos": "P-MT", "sub_pos": ["HRD positive (wt)", "HRD negative / pHRD"], "type": "Ongoing",
     "rationale": "標靶 Trop-2 ADC。結合 Beva 微環境調節與 ADC 誘導之免疫原性細胞死亡 (ICD) 效應，旨在優化 pHRD/HRD+ 族群在一線含鉑化療後維持獲益。",
     "dosing": "實驗臂1：Sac-TMT 單藥維持。實驗臂2：Sac-TMT + Beva 15mg/kg Q3W。對照臂：Standard Bevacizumab 維持。",
     "inclusion": ["新診斷 FIGO Stage III/IV 卵巢/輸卵管癌。", "HRD 狀態由中央實驗室判定 (包含 pHRD)。", "一線含鉑化療後達 CR 或 PR 狀態。", "可供檢測之 Trop-2 組織。"],
     "exclusion": ["BRCA 突變。", "先前用過針對 Trop-2 之 ADC 藥物。", "嚴重自體免疫疾病或 IBD 病史。"], "ref": "ENGOT-ov85"},

    {"cancer": "Endometrial", "name": "MK2870-033", "pharma": "MSD", "drug": "Sac-TMT + Pembrolizumab", "pos": "P-MT", "sub_pos": ["IO Maintenance"], "type": "Ongoing",
     "rationale": "標靶 Trop-2 ADC 協同 PD-1 抑制劑。透過免疫重塑提升 Pembrolizumab 在 pMMR 或 NSMP 族群的應答深度與應答率。",
     "inclusion": ["pMMR 子宮內膜癌 (中心檢測)。", "FIGO III/IV 一線含鉑+Pembro後達 CR/PR。", "未針對復發進行過系統性治療。"],
     "exclusion": ["子宮肉瘤 (Sarcoma)。", "先前接受過晚期系統性 IO 治療。"], "ref": "ESMO 2025"},
    
    {"cancer": "Endometrial", "name": "GU-US-682-6769", "pharma": "Gilead", "drug": "SG (Trodelvy)", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "type": "Ongoing",
     "rationale": "標靶 Trop-2 ADC。利用 SN-38 載荷引發 DNA 損傷，專攻鉑類與免疫失敗救援，具強力 Bystander 效應對抗異質性病灶。",
     "inclusion": ["復發性 EC (不含肉瘤)。", "鉑類與 PD-1 失敗後進展。", "充分器官功能 (ANC ≥1500, PLT ≥100k)。"],
     "exclusion": ["先前用過 Trop-2 ADC。", "活動性 CNS 轉移。"], "ref": "JCO 2024"},

    {"cancer": "Ovarian", "name": "DS8201-772 (Enhertu)", "pharma": "AstraZeneca", "drug": "T-DXd (Trastuzumab Deruxtecan)", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], "type": "Ongoing",
     "rationale": "標靶 HER2 ADC。救援化療穩定後之精準維持首選。超高 DAR (8) 優勢清除 HER2 表現殘留病灶，延長緩解時間。",
     "inclusion": ["HER2 IHC 1+/2+/3+ 確認。", "PSOC 救援化療達穩定 (Non-PD)。", "LVEF ≥ 50%。"],
     "exclusion": ["曾患有需類固醇治療之非感染性 ILD 肺部病史。"], "ref": "JCO 2024"},

    {"cancer": "Ovarian", "name": "DOVE (APGOT-OV07)", "pharma": "GSK", "drug": "Dostarlimab + Bevacizumab", "pos": "R-TX (PROC)", "sub_pos": ["Platinum-Resistant"], "type": "Ongoing",
     "rationale": "針對透明細胞癌 (OCCC)。利用 IO + anti-VEGF 雙重打擊，改善其特有之免疫抑制環境，誘發應答。",
     "inclusion": ["組織學 OCCC > 50%。", "鉑類抗藥性 (PFI < 12m)。", "RECIST v1.1 可測量病灶。"],
     "exclusion": ["先前用過任何免疫治療 (PD-1/L1)。"], "ref": "JCO 2025"},

    {"cancer": "Cervical", "name": "innovaTV 301", "pharma": "Seagen", "drug": "Tisotumab Vedotin (Tivdak)", "pos": "R-TX", "sub_pos": ["2L / 3L Therapy"], "type": "Ongoing",
     "rationale": "標靶 Tissue Factor (TF) ADC。搭載 MMAE 載荷，旨在克服後線子宮頸癌化療耐藥性，改善生存期。",
     "inclusion": ["復發/轉移子宮頸癌。", "先前接受 1–2 線治療後進展。"],
     "exclusion": ["嚴重眼疾或角膜炎。", "活動性出血風險。"], "ref": "NEJM 2024"}
]

# --- 4. 動態模型巡邏邏輯 ---
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
    st.session_state.selected_trial = milestone_db[0]['name']

with st.sidebar:
    st.markdown("<h3 style='color: #6A1B9A;'>🤖 AI 實證決策助理</h3>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 病歷深度數據比對", expanded=True):
        p_notes = st.text_area("輸入摘要 (含細胞型態/標記)", height=250)
        if st.button("🚀 開始分析"):
            if api_key and p_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = get_gemini_model()
                    if model:
                        prompt = f"分析：{p_notes}。參考實證：{milestone_db} 及進行中：{ongoing_trials}。提供路徑建議與理由。"
                        st.write(model.generate_content(prompt).text)
                    else: st.error("找不到可用 AI 模型。")
                except Exception as e: st.error(f"AI 異常: {e}")

# --- 6. 主頁面：導航地圖 ---
st.markdown("<div class='main-title'>婦癌臨床導航儀表板 (2026 實證與收案全整合)</div>", unsafe_allow_html=True)
cancer_type = st.radio("第一步：選擇癌症類型", ["Endometrial", "Ovarian", "Cervical"], horizontal=True)

cols = st.columns(len(guidelines_nested[cancer_type]))
stages_data = guidelines_nested[cancer_type]

for i, stage in enumerate(stages_data):
    with cols[i]:
        st.markdown(f"""<div class='big-stage-card card-{stage['css']}'><div class='big-stage-header header-{stage['css']}'>{stage['header']}</div>""", unsafe_allow_html=True)
        for sub in stage['subs']:
            st.markdown(f"""<div class='sub-block'><div class='sub-block-title'>📘 {sub['title']}</div><div class='sub-block-content'>{sub['content']}</div>""", unsafe_allow_html=True)
            
            # A. 顯示里程碑 (📚)
            rel_milestones = [m for m in milestone_db if m["cancer"] == cancer_type and m["pos"] == stage["id"] and any(s in sub["title"] for s in m["sub_pos"])]
            for m in rel_milestones:
                with st.popover(f"📚 {m['name']}", use_container_width=True):
                    st.success(f"**藥物:** {m['drug']}\n\n**詳細數據:** {m['summary']}\n\n**臨床解析:** {m['details']}")
                    if st.button("📊 查看完整報告", key=f"btn_{m['name']}"):
                        st.session_state.selected_trial = m['name']
            
            # B. 顯示招募中 (📍)
            rel_trials = [t for t in ongoing_trials if t["cancer"] == cancer_type and t["pos"] == stage["id"] and any(s in sub["title"] for s in t["sub_pos"])]
            for t in rel_trials:
                label = f"📍 {t['pharma']} | {t['name']} | {t['drug']}"
                ukey = f"btn_{t['name']}_{stage['id']}_{sub['title'].replace(' ', '')}"
                with st.popover(label, use_container_width=True):
                    if st.button("📊 開啟深度分析報告", key=ukey):
                        st.session_state.selected_trial = t['name']
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 7. 深度報告看板 ---
st.divider()
all_list = milestone_db + ongoing_trials
try:
    t = next(it for it in all_list if it["name"] == st.session_state.selected_trial)
except:
    t = all_list[0]

st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #E0E0E0; padding-bottom:10px; font-weight:900;'>📋 {t['name']} 深度數據分析報告</h2>", unsafe_allow_html=True)

if t["type"] == "Milestone":
    r1, r2 = st.columns([1, 1])
    with r1:
        st.markdown("<div style='background:#ECEFF1; border-left:10px solid #455A64; padding:15px; border-radius:10px;'><b>📈 實證摘要 (Milestone)</b></div>", unsafe_allow_html=True)
        st.write(f"**藥物方案:** {t['drug']}")
        st.success(t['summary'])
    with r2:
        st.markdown("<div style='background:#FFF8E1; border-left:10px solid #FBC02D; padding:15px; border-radius:10px;'><b>💡 臨床解析 (Histology/FIGO)</b></div>", unsafe_allow_html=True)
        st.info(t['details'])
else:
    r1, r2 = st.columns([1.3, 1])
    with r1:
        st.markdown("<div style='background:#E3F2FD; border-left:10px solid #1976D2; padding:15px; border-radius:10px;'><b>💉 Rationale & Protocol (招募中)</b></div>", unsafe_allow_html=True)
        st.write(f"**核心藥物:** {t['drug']}")
        st.write(f"**給藥細節:** {t.get('dosing', '詳見 Protocol')}")
        st.success(t['rationale'])
        
    with r2:
        st.markdown("<div style='background:#E8F5E9; border-left:8px solid #2E7D32; padding:15px; border-radius:10px;'><b>✅ Inclusion Criteria (納入標準)</b></div>", unsafe_allow_html=True)
        for inc in t.get('inclusion', []): st.write(f"• **{inc}**")
        st.markdown("<div style='background:#FFEBEE; border-left:8px solid #C62828; padding:15px; border-radius:10px; margin-top:10px;'><b>❌ Exclusion Criteria (排除標準)</b></div>", unsafe_allow_html=True)
        for exc in t.get('exclusion', []): st.write(f"• **{exc}**")
st.markdown("</div>", unsafe_allow_html=True)
