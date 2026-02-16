import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床導航與 AI 決策系統 (2026 專家實證數據全方位擴充版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=Roboto:wght@400;700;900&display=swap');
    
    /* === 極致緊緻化 UI：徹底消除留白 === */
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', 'Roboto', sans-serif;
        background-color: #F0F4F7;
        color: #1A1A1A;
        font-size: 19px !important;
        line-height: 1.1;
    }

    .main-title {
        font-size: 32px !important; font-weight: 900; color: #004D40;
        padding: 5px 0; border-bottom: 3px solid #4DB6AC; margin-bottom: 5px;
    }

    /* 大階段方塊：高度自適應，消除標題下方留白 */
    .big-stage-card {
        border-radius: 10px; padding: 0px; 
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 2px solid transparent;
        background: white; margin-bottom: 4px; overflow: hidden;
        height: auto !important; min-height: 0 !important;
    }
    .big-stage-header {
        font-size: 17px !important; font-weight: 900; color: white;
        padding: 4px; text-align: center;
    }

    /* 子區塊：間距極小化 */
    .sub-block {
        margin: 2px 4px; padding: 4px;
        border-radius: 6px; background: #F8F9FA;
        border-left: 5px solid #607D8B;
    }
    .sub-block-title {
        font-size: 14px; font-weight: 900; color: #455A64;
        margin-bottom: 1px; border-bottom: 1px solid #CFD8DC; padding-bottom: 1px;
    }
    .sub-block-content {
        font-size: 14px; color: #263238; font-weight: 500; line-height: 1.15;
        margin-bottom: 2px;
    }

    /* 亞型標籤 */
    .tag-pole { color: #2E7D32; font-weight: 800; }
    .tag-mmrd { color: #1565C0; font-weight: 800; }
    .tag-p53 { color: #C62828; font-weight: 800; }
    .tag-nsmp { color: #6A1B9A; font-weight: 800; }

    /* 階段配色 */
    .card-p-tx { border-color: #43A047; }
    .header-p-tx { background: linear-gradient(135deg, #66BB6A, #43A047); }
    .card-p-mt { border-color: #0288D1; }
    .header-p-mt { background: linear-gradient(135deg, #29B6F6, #0288D1); }
    .card-r-tx { border-color: #FB8C00; }
    .header-r-tx { background: linear-gradient(135deg, #FFB74D, #F57C00); }
    .card-r-mt { border-color: #8E24AA; }
    .header-r-mt { background: linear-gradient(135deg, #BA68C8, #7B1FA2); }

    /* --- 上色臨床試驗標記按鈕 (藥廠配色) --- */
    .stPopover button { font-weight: 800 !important; font-size: 12px !important; border-radius: 4px !important; margin-top: 1px !important; padding: 0px 5px !important; width: 100% !important; text-align: left !important; color: white !important; }
    
    .stPopover button[aria-label*="Eli Lilly"] { background-color: #E91E63 !important; } 
    .stPopover button[aria-label*="Daiichi Sankyo"] { background-color: #4CAF50 !important; } 
    .stPopover button[aria-label*="MSD"] { background-color: #003366 !important; } 
    .stPopover button[aria-label*="AstraZeneca"] { background-color: #800080 !important; } 
    .stPopover button[aria-label*="GSK"] { background-color: #F36D21 !important; } 
    .stPopover button[aria-label*="Gilead"] { background-color: #00A9E0 !important; } 
    .stPopover button[aria-label*="Seagen"] { background-color: #512D6D !important; } 

    /* 深度看板 */
    .detail-section { background: white; border-radius: 15px; padding: 25px; margin-top: 10px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); border: 1px solid #CFD8DC; }
    .hr-big-val { font-family: 'Roboto', sans-serif; font-size: 48px !important; font-weight: 900; color: #D84315; }
    .pharma-badge { background: #004D40; color: white; padding: 3px 12px; border-radius: 50px; font-size: 13px; font-weight: 700; display: inline-block; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 指引導航數據：NSMP 與 MOC 深度補完 ---
guidelines_nested = {
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "POLEmut (超突變型)", "content": "<span class='tag-pole'>最佳預後。</span> 早期(I-II)建議治療降階 (De-escalation)，可避免 Adjuvant chemo-RT。"},
            {"title": "MMRd / MSI-H", "content": "<span class='tag-mmrd'>免疫敏感。</span> 晚期一線標竿：Chemo + PD-1 (RUBY/GY018) → IO 維持治療。"},
            {"title": "p53abn (Copy-number high)", "content": "<span class='tag-p53'>極高風險。</span> 早期亦需積極輔助治療 (化放療)；Serous需驗HER2考慮標靶。"},
            {"title": "NSMP (最大宗亞型)", "content": "<span class='tag-nsmp'>No Specific Molecular Profile.</span> 排除性診斷：MMR intact、p53 wild-type 且 POLE wild-type。<br>1. <span class='tag-nsmp'>風險因子:</span> 預後受 ER 狀態、Grade 3 與 LVSI 高度影響。<br>2. <span class='tag-nsmp'>治療方向:</span> ER-negative 為高風險子群；ER-positive 且病程慢者，可評估荷爾蒙治療(AI/Progestin)之角色。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "IO Maintenance", "content": "針對晚期/復發一線化療後，延續使用 Pembro 或 Dostarlimab 維持直到 PD。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "MMRd / MSI-H", "content": "PD-1 抑制劑單藥 (Keytruda/Jemperli) 為核心。"}, {"title": "pMMR / NSMP", "content": "標準二線方案：Pembrolizumab + Lenvatinib。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Tx", "content": "維持當前有效治療(如 Pembro+Lenva) 直到不可耐受或 PD。"}]}
    ],
    "Ovarian": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "HGSC / Endometrioid", "content": "PDS/IDS 手術 + Carboplatin/Paclitaxel x6 ± Bevacizumab"},
            {"title": "Mucinous (MOC) 鑑別", "content": "1. <span class='subtype-label'>鑑定:</span> CK7+/SATB2- 原發。排除GI轉移。<br>2. <span class='subtype-label'>型態:</span> Expansile (預後佳) vs Infiltrative (高復發風險)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "BRCA mutated", "content": "Olaparib 單藥或 Olaparib+Bev (若1L已含Bev)"},
            {"title": "HRD positive (wt)", "content": "1L有Bev選 Olaparib+Bev；沒用Bev選 Niraparib"},
            {"title": "HRD negative / pHRD", "content": "用過Bev者續用；未用者觀察或視風險選用 Niraparib"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "PSOC (Sensitive)", "content": "鉑類雙藥化療 ± Bevacizumab；維持看 BRCA/HER2。"},
            {"title": "PROC (Resistant)", "content": "單藥化療 ± Bev 或 Elahere (FRα+) 或 Trial。"},
            {"title": "MOC 晚期/復發", "content": "化療抗性高。考慮 <span class='subtype-label'>GI-like</span> 或 Anti-HER2 策略。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Platinum Sensitive Maint", "content": "救援緩解後選 PARPi 維持治療。"}]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [{"title": "Primary Protocols", "content": "Surgery(早期), CCRT(LA), Pembro+Chemo±Bev(轉移)"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Metastatic 1L Maint", "content": "1L 轉移性方案後延續 Pembro 維持直到 PD"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "2L / 3L Therapy", "content": "Tivdak (Tisotumab vedotin) 或 Cemiplimab"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Tx", "content": "維持當前有效治療直到進展"}]}
    ]
}

# --- 2. 深度臨床試驗資料庫 (8 核心 極大化細節補完) ---
if 'trials_db' not in st.session_state:
    st.session_state.trials_db = [
        # Ovarian Cancer
        {"cancer": "Ovarian", "name": "FRAmework-01 (LY4170156)", "pharma": "Eli Lilly (禮來)", "drug": "LY4170156 + Bevacizumab", "pos": "R-TX", "sub_pos": ["PSOC (Sensitive)", "PROC (Resistant)", "MOC 晚期/復發"], 
         "rationale": "標靶 Folate Receptor alpha (FRα) ADC，搭載類微管蛋白載荷。利用 ADC 的精準殺傷結合 Bevacizumab 的抗血管生成協同作用 (Synergy)，旨在克服 PARP 抑制劑耐藥後患者之需求。此機制能顯著提升 Payload 在腫瘤組織內的穿透力，並引發免疫調節效應。",
         "dosing": {
             "Experimental Arm (Part A/B)": "LY4170156 3 mg/kg IV + Bevacizumab 15 mg/kg IV on Day 1 of each 21-day cycle (Q3W)。",
             "Control Arm Part A (PROC)": "研究者選擇化療 (Paclitaxel, PLD, Gemcitabine, Topotecan) 或 Mirvetuximab (MIRV)。",
             "Control Arm Part B (PSOC)": "標準鉑類雙藥化療 (Platinum doublet) + Bevacizumab 15 mg/kg Q3W。"
         },
         "outcomes": {"ORR": "Ph 1/2: ~35-40%", "mPFS": "主要終點 (Primary Endpoint)", "HR": "Phase 3 進行中", "CI": "NCT06536348", "AE": "蛋白尿 (Proteinuria), 高血壓, 疲勞"},
         "inclusion": [
             "18歲以上，組織學證實為 HG Serous 或 Carcinosarcoma 之卵巢/輸卵管/原發腹膜癌。",
             "腫瘤檢體經中央實驗室確認為 FRα Expression Positive。",
             "Part A (PROC): 最後一劑鉑類後 90–180 天內惡化；曾接受過 1–3 線系統性治療。",
             "Part B (PSOC): 最後一劑鉑類後 >180 天惡化；必須曾用過 PARPi 或不適用者。",
             "ECOG Performance Status (PS) 為 0 或 1。",
             "具備 RECIST v1.1 可測量病灶。"
         ],
         "exclusion": [
             "先前曾用過帶有 Topoisomerase I 抑制劑 Payload 之 ADC (如 Enhertu)。",
             "具有臨床顯著的蛋白尿 (24h尿蛋白 ≥2g 或 UPCR ≥2.0)。",
             "曾有非感染性 ILD/肺臟炎病史需類固醇治療者。",
             "活動性 CNS 轉移或軟腦膜轉移 (Leptomeningeal disease)。"
         ], "ref": "ClinicalTrials.gov 2026"},
        
        {"cancer": "Ovarian", "name": "REJOICE-Ovarian01", "pharma": "Daiichi Sankyo (DS)", "drug": "R-DXd (Raludotatug Deruxtecan)", "pos": "R-TX", "sub_pos": ["PROC (Resistant)", "MOC 晚期/復發"], 
         "rationale": "標靶 Cadherin-6 (CDH6) ADC，搭載強效 DXd (Topo I inhibitor) 載荷。具備極高 DAR (Drug-Antibody Ratio) 與強力 Bystander Effect，能精準識別高度異質性的 PROC 腫瘤，並透過載荷的膜通透性殺傷周邊低表達 CDH6 之癌細胞。",
         "dosing": {
             "Experimental Arm": "R-DXd 5.6 mg/kg IV Q3W (每三週一次)。",
             "Control Arm": "Investigator's Choice 單藥化療 (Paclitaxel, PLD, or Topotecan)。"
         },
         "outcomes": {"ORR": "46.0% (Update)", "mPFS": "7.1 months", "HR": "Phase 3 Ongoing", "CI": "NCT06161025", "AE": "ILD Risk, 噁心, 嗜中性球減少"},
         "inclusion": [
             "HG Serous 或 Endometrioid 卵巢/腹膜/輸卵管癌。",
             "鉑類抗藥性 (PROC) 定義：1線鉑類後 90-180 天惡化，或 2-4 線後 ≤180 天惡化。",
             "曾接受過至少 1 線且 ≤ 4 線系統性治療。",
             "需提供組織以評估 CDH6 表達量 (分層依據)。",
             "必須曾接受過 Bevacizumab (除非有禁忌症)。"
         ],
         "exclusion": [
             "排除 Clear cell, Mucinous (非原發), Sarcomatous 或 Low-grade 腫瘤。",
             "曾患有需類固醇治療之 ILD/肺臟炎或疑似 ILD。",
             "Grade ≥ 2 的周邊神經病變 (Peripheral Neuropathy)。",
             "左心室射出分率 (LVEF) < 50%。"
         ], "ref": "JCO 2024"},
        
        {"cancer": "Ovarian", "name": "TroFuse-021 (MK-2870)", "pharma": "MSD (Merck)", "drug": "Sac-TMT (MK-2870)", "pos": "P-MT", "sub_pos": ["HRD negative / Unknown", "pHRD"], 
         "rationale": "標靶 Trop-2 ADC。結合 Bevacizumab 微環境調節與 ADC 誘導的免疫原性細胞死亡 (ICD) 效應，旨在優化 pHRD 族群在一線含鉑化療後的維持策略，填補此族群對 PARPi 反應不佳的缺口。",
         "dosing": {
             "Arm 1": "Sac-TMT 單藥維持治療 (Q2W 或 Q3W 依劑量組)。",
             "Arm 2": "Sac-TMT + Bevacizumab 15 mg/kg Q3W。",
             "Arm 3": "Standard of Care (臨床觀察或單用 Bevacizumab)。"
         },
         "outcomes": {"ORR": "Est 40% (pHRD)", "mPFS": "Phase 3 招募中", "HR": "Ongoing", "CI": "NCT06241729", "AE": "口腔炎 (Stomatitis), 腹瀉, 貧血"},
         "inclusion": [
             "新診斷 FIGO Stage III 或 IV 卵巢/腹膜/輸卵管癌。",
             "HRD 狀態確認為陰性 (HRD negative / pHRD) 且 BRCA 野生型 (Wild-type)。",
             "完成一線含鉑化療後達臨床緩解 (CR/PR)。",
             "具備可評估 Trop-2 與 HRD 狀態之組織樣本。"
         ],
         "exclusion": [
             "BRCA 突變或 HRD 陽性患者。",
             "嚴重的炎症性腸道疾病 (IBD) 或嚴重腹瀉病史。",
             "先前接受過針對 Trop-2 之 ADC 治療。",
             "充分器官功能不佳 (ANC <1500, Platelets <100k)。"
         ], "ref": "ENGOT-ov85"},

        {"cancer": "Endometrial", "name": "MK2870-033", "pharma": "MSD", "drug": "Sac-TMT + Pembro", "pos": "P-MT", "sub_pos": ["IO Maintenance", "MMRd / MSI-H", "NSMP"], 
         "rationale": "標靶 Trop-2 ADC 協同 PD-1 抑制劑。利用 ADC 誘導之免疫原性調節強化 Pembrolizumab 在 pMMR 或 NSMP 族群的應答深度與持續性，挑戰一線維持標準。",
         "dosing": {
             "Induction Phase": "Carbo + Pacli + Pembrolizumab Q3W x 6 cycles。",
             "Maintenance Phase": "Pembrolizumab 400 mg Q6W + Sac-TMT 5 mg/kg Q6W。"
         },
         "outcomes": {"ORR": "Est 35% in Ph 2", "mPFS": "Phase 3 Ongoing", "HR": "TBD", "CI": "NCT06132958", "AE": "貧血, 口腔炎, 疲勞"},
         "inclusion": [
             "pMMR 子宮內膜癌 (經中心實驗室確認)。",
             "FIGO III/IV 一線含鉑化療併用 Pembro 後達 CR/PR。",
             "初次復發且未曾針對復發進行治療者。",
             "ECOG PS 0 或 1。"
         ],
         "exclusion": [
             "組織學為子宮肉瘤 (Uterine Sarcoma)。",
             "先前接受過針對晚期病灶之任何系統性 IO 治療。",
             "活動性自體免疫疾病需長期免疫抑制劑者。"
         ], "ref": "ESMO 2025"},

        {"cancer": "Ovarian", "name": "DS8201-772 (Enhertu)", "pharma": "AstraZeneca", "drug": "T-DXd (Enhertu)", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], 
         "rationale": "標靶 HER2 ADC。作為救援化療穩定後之維持策略。超高 DAR (8) 優勢能有效對抗 HER2 表現者(含 IHC 1+/2+)之微小殘留病灶，延長緩解時間。",
         "dosing": {
             "Mono Arm": "Trastuzumab Deruxtecan 5.4 mg/kg IV Q3W。",
             "Combo Arm": "T-DXd 5.4 mg/kg + Bevacizumab 15 mg/kg Q3W。"
         },
         "outcomes": {"ORR": "46.3% (IHC 3+)", "mPFS": "10.4 months", "HR": "0.42", "CI": "95% CI: 0.30-0.58", "AE": "ILD Risk (6.2%), 噁心"},
         "inclusion": [
             "HER2 IHC 1+/2+/3+ (由中央實驗室確認)。",
             "PSOC 復發後經含鉑救援化療達穩定 (Non-PD) 狀態。",
             "LVEF ≥ 50%。",
             "不適合或不願意使用 PARP 抑制劑者。"
         ],
         "exclusion": [
             "曾患有需類固醇治療之非感染性 ILD/肺臟炎。",
             "先前曾接受過任何 HER2 ADC 治療。",
             "控制不佳之心血管疾病。"
         ], "ref": "JCO 2024"},

        {"cancer": "Ovarian", "name": "DOVE", "pharma": "GSK", "drug": "Dostarlimab + Beva", "pos": "R-TX", "sub_pos": ["PROC (Resistant)"], 
         "rationale": "針對透明細胞癌 (OCCC) 特有的免疫抑制微環境。利用 PD-1 阻斷與 VEGF 抑制之雙重打擊，恢復 T 細胞浸潤並引發持續應答。",
         "dosing": {
             "Experimental": "Dostarlimab 500mg (Q3W x4) 接續 1000mg (Q6W) + Bevacizumab 15mg/kg Q3W。",
             "Control": "單藥化療 (Gemcitabine / PLD / Taxel)。"
         },
         "outcomes": {"ORR": "40.2% (OCCC)", "mPFS": "8.2 months", "HR": "0.58", "CI": "NCT06023862", "AE": "高血壓, 蛋白尿"},
         "inclusion": ["組織學 OCCC > 50%", "鉑類抗藥性 (PFI < 12m)", "先前線數 ≤ 5 線"],
         "exclusion": ["先前接受過任何免疫治療", "臨床顯著腸阻塞病史"], "ref": "JCO 2025"},

        {"cancer": "Endometrial", "name": "GU-US-682-6769", "pharma": "Gilead", "drug": "SG (Trodelvy)", "pos": "R-TX", "sub_pos": ["pMMR / NSMP", "p53abn"], 
         "rationale": "針對 Trop-2 ADC。利用 SN-38 強效載荷引發 DNA 損傷，專攻鉑類與免疫治療失敗後之救援治療，具強大旁觀者效應。",
         "dosing": {"Experimental": "Sacituzumab Govitecan 10mg/kg IV (Day 1, 8 of Q21D)", "Control": "TPC (Doxo/Taxel)"},
         "outcomes": {"ORR": "28.5%", "mPFS": "5.6m", "HR": "0.64", "CI": "NCT03964727", "AE": "Neutropenia"},
         "inclusion": ["復發性 EC (非肉瘤)", "鉑類與 PD-1 失敗後進展"],
         "exclusion": ["先前用過 Trop-2 ADC", "活動性 CNS 轉移"], "ref": "JCO 2024"},

        {"cancer": "Cervical", "name": "innovaTV 301", "pharma": "Seagen", "drug": "Tivdak (Tisotumab)", "pos": "R-TX", "sub_pos": ["2L / 3L Therapy"], 
         "rationale": "標靶 Tissue Factor (TF) ADC。旨在克服後線子宮頸癌化療耐藥性，改善總生存預後 (OS)。",
         "dosing": {"Exp": "Tisotumab vedotin 2.0mg/kg Q3W", "Control": "Chemo (TPC)"},
         "outcomes": {"ORR": "17.8%", "mPFS": "4.2m", "HR": "0.70 (OS)", "CI": "NEJM 2024", "AE": "眼表毒性, 鼻衄"},
         "inclusion": ["復發/轉移子宮頸癌", "先前接受 1–2 線治療後進展"],
         "exclusion": ["嚴重眼疾/角膜炎", "活動性出血傾向"], "ref": "NEJM 2024"}
    ]

# --- 3. 狀態與側邊欄 AI ---
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = st.session_state.trials_db[0]['name']

with st.sidebar:
    st.markdown("<h3 style='color: #6A1B9A;'>🤖 AI 臨床媒合助理</h3>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 患者數據深度分析", expanded=True):
        p_notes = st.text_area("輸入病歷 (含分子標記)", height=250, placeholder="例：62y/o EC, NSMP, ER-negative, FIGO III...")
        if st.button("🚀 開始深度比對"):
            if api_key and p_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    prompt = f"分析病歷：{p_notes}。參考這 8 個試驗：{st.session_state.trials_db}。請依據 FIGO 2023 內膜癌亞型或 MOC 分流建議試驗與理由。"
                    st.write(model.generate_content(prompt).text)
                except Exception as e: st.error(f"AI 異常: {e}")

# --- 4. 主頁面：緊湊大綱導覽 ---
st.markdown("<div class='main-title'>婦癌臨床試驗導航系統 (2026 SoC 整合版)</div>", unsafe_allow_html=True)
cancer_type = st.radio("第一步：選擇癌症類型", ["Endometrial", "Ovarian", "Cervical"], horizontal=True)

# 分子分型演算法圖示


st.subheader("第二步：點擊標記查看亮點 (SoC 與試驗對應)")
cols = st.columns(4)
stages_data = guidelines_nested[cancer_type]

for i, stage in enumerate(stages_data):
    with cols[i]:
        # 大階段卡片：高度隨內容撐開，取消 min-height
        st.markdown(f"""<div class='big-stage-card card-{stage['css']}'><div class='big-stage-header header-{stage['css']}'>{stage['header']}</div>""", unsafe_allow_html=True)
        
        for sub in stage['subs']:
            st.markdown(f"""<div class='sub-block'><div class='sub-block-title'>📘 {sub['title']}</div><div class='sub-block-content'>{sub['content']}</div>""", unsafe_allow_html=True)
            
            # 尋找匹配試驗
            relevant_trials = [t for t in st.session_state.trials_db if t["cancer"] == cancer_type and t["pos"] == stage["id"] and any(s in sub["title"] for s in t["sub_pos"])]
            
            if relevant_trials:
                for t in relevant_trials:
                    # 使用藥廠名觸發 CSS 配色
                    unique_id = f"{t['pharma']} | {t['name']} | {t['drug']}"
                    ukey = f"btn_{t['name']}_{stage['id']}_{sub['title'].replace(' ', '')}"
                    
                    with st.popover(unique_id, use_container_width=True):
                        st.markdown(f"#### ✨ {t['name']} 臨床解析")
                        st.info(f"**Rationale:** {t['rationale'][:150]}...")
                        if st.button("📊 開啟深度分析報告", key=ukey):
                            st.session_state.selected_trial = t['name']
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. 深度分析看板 (高清晰) ---
st.divider()
t_options = [t["name"] for t in st.session_state.trials_db if t["cancer"] == cancer_type]
try: curr_idx = t_options.index(st.session_state.selected_trial)
except: curr_idx = 0

if t_options:
    selected_name = st.selectbox("🎯 切換詳細試驗報告：", t_options, index=curr_idx)
    t = next(it for it in st.session_state.trials_db if it["name"] == selected_name)

    st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
    st.markdown(f"<span class='pharma-badge'>{t['pharma']}</span>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #E0E0E0; padding-bottom:10px; font-weight:900;'>📋 {t['name']} 深度分析報告</h2>", unsafe_allow_html=True)

    r1_c1, r1_c2 = st.columns([1.3, 1])
    with r1_c1:
        st.markdown("<div class='info-box-blue' style='background:#E3F2FD; border-left:10px solid #1976D2; padding:15px; border-radius:10px;'><b>💉 Dosing Protocol & Rationale</b></div>", unsafe_allow_html=True)
        st.write(f"**核心藥物:** {t['drug']}")
        for arm, details in t['dosing'].items(): st.write(f"🔹 **{arm}**: {details}")
        st.markdown("---")
        st.success(f"**機轉實證 (Rationale):** {t['rationale']}")
        

    with r1_c2:
        st.markdown("<div class='info-box-gold' style='background:#FFF8E1; border-left:10px solid #FBC02D; padding:15px; border-radius:10px;'><b>📈 Efficacy & Outcomes</b></div>", unsafe_allow_html=True)
        st.markdown(f"""
            <div class='hr-display' style='text-align:center; background:white; padding:15px; border:2px solid #FFE082; border-radius:12px;'>
                <div style='font-size: 14px; color: #795548; font-weight:700; margin-bottom:5px;'>Hazard Ratio (HR) / NCT ID</div>
                <div class='hr-big-val'>{t['outcomes']['HR']}</div>
                <div class='hr-ci' style='font-size:18px; color:#5D4037; font-weight:700;'>{t['outcomes']['CI']}</div>
            </div>
        """, unsafe_allow_html=True)
        st.write(f"**ORR:** {t['outcomes']['ORR']} | **mPFS:** {t['outcomes']['mPFS']}")
        st.error(f"**Safety / AE:** {t['outcomes']['AE']}")
        

    st.divider()
    r2_c1, r2_c2 = st.columns(2)
    with r2_c1:
        st.markdown("<div class='info-box-blue' style='background:#E8F5E9; border-left:8px solid #2E7D32; padding:15px; border-radius:10px;'><b>✅ Inclusion Criteria (納入標準)</b></div>", unsafe_allow_html=True)
        for inc in t['inclusion']: st.write(f"• **{inc}**")
    with r2_c2:
        st.markdown("<div class='info-box-blue' style='background:#FFEBEE; border-left:8px solid #C62828; padding:15px; border-radius:10px;'><b>❌ Exclusion Criteria (排除標準)</b></div>", unsafe_allow_html=True)
        for exc in t['exclusion']: st.write(f"• **{exc}**")
    st.markdown("</div>", unsafe_allow_html=True)
