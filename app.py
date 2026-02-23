import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床導航與實證圖書館 (2026 旗艦最終極量整合版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

# 初始化 session_state 用於聯動與持久化
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = "📚 RUBY (ENGOT-EN6)"

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=Roboto:wght@400;700;900&display=swap');
    
    /* === UI 高對比度與視覺救援 === */
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', 'Roboto', sans-serif;
        background-color: #F4F7F9; color: #1A1A1A;
        font-size: 19px !important; line-height: 1.1;
    }

    .main-title {
        font-size: 34px !important; font-weight: 900; color: #004D40;
        padding: 10px 0; border-bottom: 4px solid #4DB6AC; margin-bottom: 10px;
    }

    /* 圖一修復：大階段 Header 飽和漸層背景，確保白色文字清晰 */
    .big-stage-card {
        border-radius: 12px; padding: 0px; box-shadow: 0 6px 25px rgba(0,0,0,0.15);
        border: 2.5px solid transparent; background: white; margin-bottom: 8px; overflow: hidden; height: auto !important;
    }
    .big-stage-header {
        font-size: 20px !important; font-weight: 900; color: white !important;
        padding: 14px; text-align: center; text-shadow: 1px 1px 3px rgba(0,0,0,0.5);
    }

    /* 階段配色飽和化 */
    .card-p-tx { border-color: #1B5E20; }
    .header-p-tx { background: linear-gradient(135deg, #2E7D32, #1B5E20); } /* 初治: 深綠 */
    .card-p-mt { border-color: #0D47A1; }
    .header-p-mt { background: linear-gradient(135deg, #1565C0, #0D47A1); } /* 維持: 深藍 */
    .card-r-tx { border-color: #BF360C; }
    .header-r-tx { background: linear-gradient(135deg, #E65100, #BF360C); } /* 復發: 深橘紅 */
    .card-r-mt { border-color: #4A148C; }
    .header-r-mt { background: linear-gradient(135deg, #6A1B9A, #4A148C); } /* 復後維持: 深紫 */

    .sub-block {
        margin: 4px 8px; padding: 8px; border-radius: 10px; 
        background: #F8F9FA; border-left: 6px solid #455A64;
    }
    .sub-block-title {
        font-size: 16px; font-weight: 900; color: #263238;
        margin-bottom: 2px; border-bottom: 1.2px solid #CFD8DC; padding-bottom: 2px;
    }

    /* 按鈕樣式：深黑色加粗 (#1A1A1A) */
    .stPopover button { 
        font-weight: 900 !important; font-size: 12px !important; 
        border-radius: 6px !important; margin-top: 3px !important;
        padding: 4px 10px !important; width: 100% !important; 
        text-align: left !important; color: #1A1A1A !important; 
        border: 1.5px solid rgba(0,0,0,0.2) !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
    }
    
    .stPopover button[aria-label*="📚"] { background: #ECEFF1 !important; border-left: 6px solid #455A64 !important; }
    .stPopover button[aria-label*="📍"] { background: #E1F5FE !important; border-left: 6px solid #0288D1 !important; } 

    .detail-section { background: white; border-radius: 24px; padding: 35px; border: 1.5px solid #CFD8DC; box-shadow: 0 15px 50px rgba(0,0,0,0.1); }
    .hr-big-val { font-family: 'Roboto', sans-serif; font-size: 34px !important; font-weight: 900; color: #D84315; }
    .regimen-box { background: #F1F8E9; border-left: 6px solid #689F38; padding: 15px; border-radius: 8px; font-size: 15px; margin: 10px 0; line-height: 1.4; }
    .results-box { background: #FFF8E1; border: 1px solid #FFE082; padding: 10px; border-radius: 8px; margin-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 指引數據庫：分型、階段與跨組導航 ---
guidelines_nested = {
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "dMMR / MSI-H / MMRd", "content": "一線首選：含鉑化療 + PD-1 (RUBY/GY018/AtTEnd)。"},
            {"title": "pMMR / NSMP / MSS", "content": "一線維持：Chemo + Durva/Ola (DUO-E)。二線標靶免疫 (KN775)。"},
            {"title": "POLE mutation (超突變型)", "content": "預後極佳。早期可考慮治療降階 (De-escalation)。"},
            {"title": "p53 mutation (高拷貝型)", "content": "侵襲性最強。建議化放療積極介入。Serous 型需檢測 HER2。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Maintenance Therapy", "content": "一線 IO 治療後延續維持至 PD (MK2870-033/DUO-E)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "Recurrent EC", "content": "標準二線：標靶+免疫 (KN775) 或單藥 IO (GARNET)。救援 ADC (SG)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "救援治療後維持當前有效方案直到疾病進展。"}]}
    ],
    "Ovarian": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "Neoadjuvant Setting", "content": "NAC + IDS + HIPEC (van Driel)。"},
            {"title": "DDCT Setting", "content": "Dose-Dense Chemotherapy。"},
            {"title": "IP Setting", "content": "NAC-IDS/PDS + IP chemo。"},
            {"title": "HGSC / Endometrioid", "content": "手術 (PDS/IDS) + Carbo/Pacli ± Bev。"},
            {"title": "Clear Cell Carcinoma", "content": "OCCC。"},
            {"title": "Low grade serous carcinoma", "content": "AI, MEK, CDK 4/6"},
            {"title": "Mucinous (MOC) 鑑定", "content": "判定：CK7+/SATB2- (原發)。IA 期可保守。侵襲型建議積極化療。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "BRCA mutation", "content": "Olaparib 單藥維持 2年 (SOLO-1)。"}, 
            {"title": "HRD positive (wt)", "content": "PAOLA-1 (Ola+Bev) 或 PRIMA (Nira)。"},
            {"title": "HRD negative (pHRD)", "content": "Niraparib 維持 (PRIMA ITT) 或 Bevacizumab。"},
            {"title": "Clear Cell Carcinoma", "content": "OCCC。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "PSOC (Sensitive Recur)", "content": "PFI > 6m。評估二次手術 (DESKTOP III) 或含鉑複方。"},
            {"title": "PROC (Resistant Recur)", "content": "PFI < 6m。單藥化療 ± Bev 或標靶 ADC (MIRASOL)。"},
            {"title": "Low grade serous carcinoma", "content": "AI, MEK, CDK 4/6"},
            {"title": "Clear Cell Carcinoma", "content": "OCCC。"},
            {"title": "Mucinous (MOC) 鑑定", "content": "判定：CK7+/SATB2- (原發)。IA 期可保守。侵襲型建議積極化療。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [
            {"title": "PARPi Maint", "content": "救援緩解後續用 PARPi (NOVA/ARIEL3/SOLO2)。"},
            {"title": "ADC/other Maint", "content": "其他藥物。"}]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "Locally Advanced (CCRT)", "content": "同步化放療 ± 同步 IO (A18) 或 誘導化療 (INTERLACE)。"},
            {"title": "Locally Advanced (NIC)", "content": "MIC then Surgery。"},
            {"title": "Early Stage (Surgery)", "content": "根治術 (LACC) 或單純切除 (SHAPE)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Maintenance", "content": "1L 方案後接續維持 (KEYNOTE-826)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "Recurr / Metastatic", "content": "一線 KN826/BEATcc。二線 ADC (innovaTV 301) 或 IO (EMPOWER)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "維持當前有效救援方案直至 PD。"}]}
    ],
    "Uterine Sarcoma": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "Primary Sarcoma", "content": "術後輔助或轉移性不可切除。"},
            {"title": "Carcinosarcoma", "content": "癌肉瘤。"},
            {"title": "Low grade ESS", "content": "LGESS"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Maintenance", "content": "1L 方案後接續維持。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "Recurr / Metastatic", "content": "復發治療。"},
            {"title": "Carcinosarcoma", "content": "癌肉瘤。"},
            {"title": "Low grade ESS", "content": "LGESS"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "維持當前有效救援方案直至 PD。"}]}
    ],
}

# --- 2. 實證資料庫 (33 項試驗全量數據極量化補完) ---
all_trials_db = [
    # ==========================
    # === Endometrial Published ===
    # ==========================
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["dMMR / MSI-H / MMRd"], "name": "📚 RUBY (ENGOT-EN6/GOG-3031)", "pharma": "GSK", "drug": "Dostarlimab + Carboplatin/Paclitaxel", 
     "pop_results": "晚期轉移第一線或復發者，dMMR/MSS（pMMR）皆顯著延長PFS（dMMR：HR 0.28；全體：HR 0.64），且更新分析顯示OS亦改善（dMMR：HR 0.32；全體：HR 0.69），奠定一線「免疫＋化療」新標準。",
     "rationale": "PD-1 阻斷 (PD-1 blockade) 與含鉑化療 (Carbo/Pacli) 具備協同免疫原性細胞死亡 (ICD) 效應。藉由化療誘導腫瘤抗原釋放，釋放免疫微環境壓力並針對 MMRd 族群達成極高持久應答率。",
     "regimen": "Arm 1 (Dostarlimab 組): 誘導期: Dostarlimab 500mg Q3W + Carboplatin (AUC 5) + Paclitaxel (175 mg/m2) x6 週期；維持期: Dostarlimab 1000mg Q6W (持續 3年)。 Arm 2 (Placebo 組): 生理鹽水對照 + 同劑量 CP 化療 x6 週期。",
     "inclusion": ["新診斷 FIGO Stage III-IV 或首次復發之子宮內膜癌 (EC)。", "ECOG 0-1。", "含 Carcinosarcoma / Clear cell / Serous 等組織型態。"],
     "exclusion": ["既往接受 PD-1/PD-L1 治療。", "活動性/需系統性治療之自體免疫疾病。", "未控制感染。", "臨床上顯著 CNS 轉移等。"],
     "outcomes": "dMMR 族群 24個月 PFS 率: 61.4% vs 15.7% (HR 0.28, 95% CI 0.16-0.50); ITT 全人群 mOS HR 0.64 (95% CI 0.46-0.87, P=0.0021)。"},

    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "name": "📚 RUBY (ENGOT-EN6/GOG-3031)", "pharma": "GSK", "drug": "Dostarlimab + Carboplatin/Paclitaxel", 
     "pop_results": "晚期轉移第一線或復發者，dMMR/MSS（pMMR）皆顯著延長PFS（dMMR：HR 0.28；全體：HR 0.64），且更新分析顯示OS亦改善（dMMR：HR 0.32；全體：HR 0.69），奠定一線「免疫＋化療」新標準。",
     "rationale": "PD-1 阻斷 (PD-1 blockade) 與含鉑化療 (Carbo/Pacli) 具備協同免疫原性細胞死亡 (ICD) 效應。藉由化療誘導腫瘤抗原釋放，釋放免疫微環境壓力並針對 MMRd 族群達成極高持久應答率。",
     "regimen": "Arm 1 (Dostarlimab 組): 誘導期: Dostarlimab 500mg Q3W + Carboplatin (AUC 5) + Paclitaxel (175 mg/m2) x6 週期；維持期: Dostarlimab 1000mg Q6W (持續 3年)。 Arm 2 (Placebo 組): 生理鹽水對照 + 同劑量 CP 化療 x6 週期。",
     "inclusion": ["新診斷 FIGO Stage III-IV 或首次復發之子宮內膜癌 (EC)。", "ECOG 0-1。", "含 Carcinosarcoma / Clear cell / Serous 等組織型態。"],
     "exclusion": ["既往接受 PD-1/PD-L1 治療。", "活動性/需系統性治療之自體免疫疾病。", "未控制感染。", "臨床上顯著 CNS 轉移等。"],
     "outcomes": "dMMR 族群 24個月 PFS 率: 61.4% vs 15.7% (HR 0.28, 95% CI 0.16-0.50); ITT 全人群 mOS HR 0.64 (95% CI 0.46-0.87, P=0.0021)。"},

    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["dMMR / MSI-H / MMRd", "pMMR / NSMP / MSS"], "name": "📚 NRG-GY018 (KEYNOTE-868)", "pharma": "MSD", "drug": "Pembrolizumab + Carboplatin/Paclitaxel", 
     "pop_results": "晚期轉移第一線或復發者，Pembrolizumab＋化療在一線顯著延長PFS（dMMR：HR 0.30；pMMR：HR 0.54），是另一個改變臨床實務的一線免疫＋化療關鍵試驗。",
     "rationale": "利用免疫檢查點抑制劑 (ICI) 重塑腫瘤微環境，Pembrolizumab 強化一線含鉑化療反應後的持久性。",
     "regimen": "Arm A: Pembrolizumab 200mg Q3W + Carboplatin (AUC 5) + Paclitaxel (175 mg/m2) x6 週期 -> 維持期: Pembrolizumab 400mg Q6W (持續 2年)。 Arm B: Placebo + CP x6 週期。",
     "inclusion": ["Stage III/IV 或復發 EC。", "提供 MMR 檢測 (IHC) 報告，分為 dMMR vs pMMR 兩個主要分析 cohort。", "ECOG 0-1。"],
     "exclusion": ["既往 anti–PD-(L)1。", "活動性自體免疫需治療。", "不可控制共病（感染/心血管等）。", "CNS 活動性病灶等。"],
     "outcomes": "dMMR PFS HR 0.30 (95% CI 0.19-0.48); pMMR PFS HR 0.54 (95% CI 0.41-0.71, P<0.001)。"},

    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "name": "📚 NRG-GY018 (KEYNOTE-868)", "pharma": "MSD", "drug": "Pembrolizumab + Carboplatin/Paclitaxel", 
     "pop_results": "晚期轉移第一線或復發者，Pembrolizumab＋化療在一線顯著延長PFS（dMMR：HR 0.30；pMMR：HR 0.54），是另一個改變臨床實務的一線免疫＋化療關鍵試驗。",
     "rationale": "利用免疫檢查點抑制劑 (ICI) 重塑腫瘤微環境，Pembrolizumab 強化一線含鉑化療反應後的持久性。",
     "regimen": "Arm A: Pembrolizumab 200mg Q3W + Carboplatin (AUC 5) + Paclitaxel (175 mg/m2) x6 週期 -> 維持期: Pembrolizumab 400mg Q6W (持續 2年)。 Arm B: Placebo + CP x6 週期。",
     "inclusion": ["Stage III/IV 或復發 EC。", "提供 MMR 檢測 (IHC) 報告，分為 dMMR vs pMMR 兩個主要分析 cohort。", "ECOG 0-1。"],
     "exclusion": ["既往 anti–PD-(L)1。", "活動性自體免疫需治療。", "不可控制共病（感染/心血管等）。", "CNS 活動性病灶等。"],
     "outcomes": "dMMR PFS HR 0.30 (95% CI 0.19-0.48); pMMR PFS HR 0.54 (95% CI 0.41-0.71, P<0.001)。"},

    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["pMMR / NSMP / MSS"], "name": "📚 DUO-E (ENGOT-EN9)", "pharma": "AZ", "drug": "Durvalumab + CP →維持 ± Olaparib", 
     "pop_results": "一線治療中，Durvalumab＋化療可改善PFS（HR 0.71），而「Durvalumab＋化療→維持加上Olaparib」效益更大（PFS HR 0.55）；pMMR亦有PFS獲益（Durva+Ola vs control：HR 0.57），且OS期中分析支持（Durva+Ola vs control：HR 0.59），三藥組 pMMR PFS HR 0.57 (vs CP)",
     "rationale": "探索 PARP 抑制劑 (PARPi) 與 PD-L1 抑制劑在維持階段的協同效果，PARPi 誘導的 DNA 損傷可增加新抗原負荷，強化免疫應答。",
     "regimen": "Arm 1: carboplatin/paclitaxel + placebo → placebo maintenance 僅化療 (對照組); Arm 2: CP+Durvalumab -> Durva 1500mg Q4W 維持; Arm 3: CP+Durvalumab -> Durva 1500mg Q4W + Olaparib 300mg bid 維持直到疾病進展。",
     "inclusion": ["newly diagnosed advanced 或 recurrent endometrial cancer。", "適合 CP。", "ECOG 0-1。"],
     "exclusion": ["既往免疫治療 / PARP inhibitor。", "活動性自體免疫需治療。", "未控制感染。", "其他研究者判定不適合等。"],
     "outcomes": ["pMMR Arm 3 (Ola+Durva) vs Arm 1: PFS HR 0.57 (95% CI 0.42-0.79); dMMR Arm 2 vs Arm 1: HR 0.42 (95% CI 0.22-0.80)。", 
                  "PFS：durvalumab vs control HR 0.71；durvalumab+olaparib vs control HR 0.55。", 
                  "AE（臨床重點）：加上 olaparib 後，需特別注意 貧血/血球下降、疲倦 等 PARP 典型毒性疊加。"]},

    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["dMMR / MSI-H / MMRd"], "name": "📚 AtTEnd (ENGOT-EN7)", "pharma": "Roche", "drug": "Atezolizumab + CP", 
     "pop_results": "晚期轉移第一線或復發者，Atezolizumab＋化療在dMMR族群PFS顯著改善（HR 0.36），訊息重點是「效益主要集中在dMMR」，pMMR整體效益相對不明顯，dMMR PFS HR 0.36; ITT OS HR 0.82",
     "rationale": "驗證一線 PD-L1 抑制劑併用化療對晚期或復發患者之生存優勢。",
     "regimen": "Arm A: Atezolizumab 1200mg Q3W + CP x6-8 週期 -> 維持 Atezolizumab 1200mg Q3W。 Arm B: Placebo + CP x6-8 週期。",
     "inclusion": ["advanced 或 recurrent endometrial carcinoma。", "一線接受 CP。", "評估 dMMR 亞群獲益。"],
     "exclusion": ["既往 PD-(L)1 抑制劑。", "活動性自體免疫需治療。", "未控制感染。", "其他研究者判定不適合等。"],
     "outcomes": "dMMR PFS: 未達到 vs 6.9m (HR 0.36, 95% CI 0.23-0.57); 全人群 mOS HR 0.82 (P=0.048)。"},

    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "name": "📚 AtTEnd (ENGOT-EN7)", "pharma": "Roche", "drug": "Atezolizumab + CP", 
     "pop_results": "晚期轉移第一線或復發者，Atezolizumab＋化療在dMMR族群PFS顯著改善（HR 0.36），訊息重點是「效益主要集中在dMMR」，pMMR整體效益相對不明顯，dMMR PFS HR 0.36; ITT OS HR 0.82",
     "rationale": "驗證一線 PD-L1 抑制劑併用化療對晚期或復發患者之生存優勢。",
     "regimen": "Arm A: Atezolizumab 1200mg Q3W + CP x6-8 週期 -> 維持 Atezolizumab 1200mg Q3W。 Arm B: Placebo + CP x6-8 週期。",
     "inclusion": ["advanced 或 recurrent endometrial carcinoma。", "一線接受 CP。", "評估 dMMR 亞群獲益。"],
     "exclusion": ["既往 PD-(L)1 抑制劑。", "活動性自體免疫需治療。", "未控制感染。", "其他研究者判定不適合等。"],
     "outcomes": "dMMR PFS: 未達到 vs 6.9m (HR 0.36, 95% CI 0.23-0.57); 全人群 mOS HR 0.82 (P=0.048)。"},

    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["p53 mutation (高拷貝型)", "pMMR / NSMP / MSS", "dMMR / MSI-H / MMRd"], 
        "name": "📚 KEYNOTE-B21 (ENGOT-en11)", "pharma": "MSD", "drug": "Pembrolizumab + Chemo ± RT", 
        "pop_results": "高風險輔助治療挑戰：手術清完後輔助化療（±放療）中加入 Pembrolizumab 並未顯著改善 DFS (HR 1.02)，目前不建議常規加入。",
        "rationale": "旨在驗證對於高風險、已手術切除的新診斷 EC 患者，在標準輔助化療基礎上加上免疫檢查點抑制劑是否能進一步降低復發風險。",
        "regimen": "試驗組: Pembrolizumab (200mg Q3W x6 週期) 併用化療 (CP) ± 放射治療，隨後 Pembrolizumab (400mg Q6W) 維持至 14 週期。",
        "inclusion": [
            "新診斷、高風險且已完全切除之子宮內膜癌",
            "FIGO 2009 Stage I/II (Serous 或 Clear cell) 或 Stage III/IV (已切除者)",
            "ECOG 0-1"],
        "exclusion": [
            "先前受過針對此癌症之全身性治療",
            "活動性自體免疫疾病",
            "具有多發性原發癌症病史"],
        "outcomes": "2yr DFS Rate: 75.2% (Pembro) vs 74.2% (Placebo); HR 1.02 (95% CI 0.79-1.32), P=0.57 (未達顯著差異)。"},
    
    {"cancer": "Endometrial", 
    "pos": "P-MT", 
    "sub_pos": ["Maintenance Therapy"], 
    "name": "📚 DUO-E (Maint)", 
    "pharma": "AstraZeneca", 
    "drug": "Durvalumab ± Olaparib",
    "pop_results": "一線治療中，Durvalumab＋化療可改善PFS（HR 0.71），而「Durvalumab＋化療→維持加上Olaparib」效益更大（PFS HR 0.55）；pMMR亦有PFS獲益（Durva+Ola vs control：HR 0.57），且OS期中分析支持（Durva+Ola vs control：HR 0.59）",
    "rationale": "探索 PARP 抑制劑與 PD-L1 抑制劑在維持階段對 pMMR 患者的協同增敏效應。",
    "regimen": "Arm 2: Durvalumab 1500mg Q4W 維持; Arm 3: Durvalumab + Olaparib 300mg bid 維持。",
    "inclusion": ["一線含鉑化療後達 CR/PR 之晚期 EC。", "提供 MMR IHC 狀態。"],
    "exclusion": ["先前接受過系統性 IO 治療。"],
    "outcomes": "pMMR 三藥組 (Ola+Durva) PFS HR 0.57 (95% CI 0.42-0.79)。"},

{"cancer": "Endometrial", 
        "pos": "P-MT", 
        "sub_pos": ["Maintenance Therapy"], 
        "name": "📚 SIENDO (ENGOT-EN5/GOG-3055)", 
        "pharma": "Karyopharm", 
        "drug": "Selinexor", 
        "pop_results": "TP53 wild-type 族群獲益極佳：維持治療顯著延長 PFS 達 5 倍以上 (27.4m vs 5.2m, HR 0.41)。",
        "rationale": "利用 XPO1 抑制劑 Selinexor 在 TP53 wild-type 患者中誘導細胞核內抑癌蛋白蓄積，進而引發腫瘤細胞凋亡。",
        "regimen": "Selinexor 80 mg 每週口服一次，持續治療直到疾病進展或不可耐受之毒性。",
        "inclusion": [
            "完成一線含鉑化療後達 CR 或 PR 之晚期/復發性子宮內膜癌",
            "ECOG 0-1",
            "需提供組織學樣本進行 p53 狀態判定"],
        "exclusion": [
            "先前接受過 XPO1 抑制劑治療",
            "活動性腦轉移",
            "無法吞嚥口服藥物者"],
        "outcomes": "TP53 wild-type PFS: 27.4m (vs 5.2m, HR 0.41, 95% CI 0.23-0.73)。"},
    
    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "name": "📚 KEYNOTE-775 (Study 309)", "pharma": "MSD/Eisai", "drug": "Lenvatinib + Pembrolizumab", 
     "pop_results": "Lenvatinib＋Pembrolizumab在復發/晚期子宮內膜癌相較化療同時改善PFS與OS（pMMR：PFS HR 0.60、OS HR 0.68；全體：PFS HR 0.56、OS HR 0.62），確立二線以後的重要組合",
     "rationale": "結合 VEGF-TKI 重塑血管並減輕免疫抑制，克服 MSS 腫瘤之免疫冷微環境。",
     "regimen": "Lenvatinib 20mg QD (每日口服) + Pembrolizumab 200mg Q3W (靜脈滴注) 直至疾病進展或不可耐受。",
     "inclusion": ["advanced/recurrent endometrial cancer。", "先前接受過至少一次含鉑化療進展之晚期 EC (最多前線 2 次)。", "ECOG 0-1。", "不限 MMR 狀態，但pMMR 為主要族群之一。"],
     "exclusion": ["既往 PD-1/PD-L1。", "活動性自體免疫需治療。", "未控制高血壓/重大心血管風險（lenvatinib 相關）。", "出血/廔管高風險等。"],
     "outcomes": "pMMR OS: 17.4m vs 12.0m (HR 0.68, 95% CI 0.56-0.84, P<0.001); ITT OS: 18.3m vs 11.4m (HR 0.62)，PFS HR ~0.56; 反應率亦優於化療，但毒性較高，臨床常見：HTN、腹瀉、疲倦、體重下降、甲狀腺功能異常 等。"},

    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "name": "📚 GARNET", "pharma": "GSK", "drug": "Dostarlimab 單藥", 
     "pop_results": "屬單臂Dostarlimab研究（主要報ORR/持續反應），無隨機比較HR可填（HR：N/A），dMMR ORR 45.5%; DOR 持久",
     "rationale": "針對 MSI-H/dMMR 高免疫原性患者，單藥 PD-1 阻斷即可達成持久應答。",
     "regimen": "Dostarlimab 500mg Q3W x4 劑 -> 1000mg Q6W 維持直到進展。",
     "inclusion": ["recurrent/advanced endometrial cancer，先前治療後。", "分 dMMR/MSI-H 與 pMMR cohort。"],
     "exclusion": ["既往 PD-1/PD-L1。", "活動性自體免疫需治療。", "CNS 活動性病灶等"],
     "outcomes": "dMMR/MSI-H ORR 45.5%、且 DoR 長; DOR 未達到。pMMR ORR 較低（約 10–15% 等級，依分析集而異）"},

    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["dMMR / MSI-H / MMRd", "pMMR / NSMP / MSS", "POLE mutation (超突變型)", "p53 mutation (高拷貝型)"], 
        "name": "📚 RAINBO Program", "pharma": "ENGOT / GOG", "drug": "分子分型導航輔助治療", 
        "pop_results": "精準輔助治療新標準：根據四大分子分型進行治療降階或增益 (Escalation/De-escalation)，旨在優化術後預後並減少過度治療。",
        "rationale": "RAINBO 由四個平台組成：RED (p53abn 加化放療)、GREEN (NSMP 加激素維持)、AMBER (MMRd 加免疫維持) 及 BLUE (POLE 觀察)，將分子分型落實於臨床決策。",
        "regimen": "RED: 化放療 + Olaparib 維持治療; GREEN: 骨盆放療 + Letrozole 維持治療; AMBER: 骨盆放療 + Dostarlimab 維持治療; BLUE: 術後觀察 (De-escalation)。",
        "inclusion": ["FIGO Stage I-III 子宮內膜癌", "術後完成分子分型鑑定 (POLE, MMR, p53)", "具備中高風險特徵者"],
        "outcomes": "試驗進行中 (Ongoing)，部分平台如 BLUE 旨在驗證 POLE 突變極佳之預後可否免除輔助治療。"},
    
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["pMMR / NSMP / MSS"], 
        "name": "📚 PORTEC-4a", "pharma": "Leiden University", "drug": "Molecular-integrated Risk Profile", 
        "pop_results": "分子整合風險導航：比較『分子風險模型』與『傳統臨床病理風險』導航的輔助放療，達成更精準的患者分流。",
        "rationale": "驗證基於分子特徵（如 p53, POLE, MMR, CTNNB1, L1CAM）的風險評估是否優於傳統臨床分期，以決定放療範圍。",
        "regimen": "試驗組: 依據分子風險模型決定 (觀察/陰道殘端放療/骨盆放療); 對照組: 依傳統臨床風險標準進行陰道殘端放療 (VBT)。",
        "inclusion": ["FIGO Stage I 子宮內膜癌", "具備中度風險病理特徵", "完成完整分子分型標記檢測"],
        "outcomes": "主要終點為陰道復發率 (Vaginal Recurrence Rate)，預期分子導航組能減少 15% 的過度放療。"},
    
    # ==========================
    # === Cervical Published ===
    # ==========================
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Locally Advanced (CCRT)"], "name": "📚 KEYNOTE-A18 (ENGOT-cx11)", "pharma": "MSD", "drug": "Pembrolizumab + CCRT", 
     "pop_results": "與同步化放療相比，加入Pembrolizumab可帶來整體存活改善的趨勢/早期訊號（期中OS HR 0.67），核心意義在於把免疫治療推進到「根治意圖」同步化放療場景，LACC 標準：36m OS 82.6% (HR 0.67)",
     "rationale": "將免疫整合入高風險局部晚期之根治同步化放療。",
     "regimen": "Arm A: CCRT (Cisplatin 40mg/m2 週服 + RT 45-50.4 Gy) 同步 Pembro 200mg Q3W x5 週期 -> 維持 Pembro 400mg Q6W x15 週期。 Arm B: CCRT + Placebo。",
     "inclusion": ["新診斷 Stage IB2-IIB LN(+) 或 Stage III-IVA 局部晚期。"],
     "exclusion": ["既往系統性治療/免疫治療。", "活動性自體免疫需治療。", "不可控感染", "放療禁忌等"],
     "outcomes": "24m PFS: 68% vs 57% (HR 0.70); 36m OS: 82.6% vs 74.8% (HR 0.67)。"},

    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Locally Advanced (CCRT)"], "name": "📚 INTERLACE", "pharma": "UCL", "drug": "Induction Carbo/Pacli x6 -> CCRT", 
     "pop_results": "以「誘導化療→再同步化放療」策略改善預後，報告顯示PFS與OS皆提升（PFS HR 0.65；OS HR 0.60），代表「治療序列」本身也能帶來存活增益，5年 OS 80% (vs 72%, HR 0.60)",
     "rationale": "利用誘導化療 (Induction Chemo) 解決放療前的微小轉移。",
     "regimen": "Arm A：誘導期: induction chemotherapy（短療程）Paclitaxel 80mg/m2 + Carboplatin AUC2 每週一次 x6 週期 -> 接續標準 CCRT (Cisplatin + RT)。Arm B：標準 CCRT alone",
     "inclusion": ["treatment-naïve、locally advanced cervical cancer，適合根治性 CCRT。"],
     "exclusion": ["無法接受化療或根治性放療。", "重大共病/感染。", "懷孕等"],
     "outcomes": "5yr OS: 80% vs 72% (HR 0.60); 5yr PFS: 73% vs 64% (HR 0.65)。"},
    
    {"cancer": "Cervical", "pos": "P-MT", "sub_pos": ["Maintenance"], 
        "name": "📚 KEYNOTE-826", "pharma": "MSD", "drug": "Pembrolizumab + Chemo ± Bev", 
        "pop_results": "一線 R/M 子宮頸癌黃金標準：在化療基礎上併用免疫治療顯著改善 OS (HR 0.63)。完成誘導化療後，免疫藥物接續維持治療直至 PD 或滿 24 個月。",
        "rationale": "利用免疫檢查點抑制劑與化療產生協同效應，並透過後續單藥免疫維持治療，持續活化免疫系統以控制腫瘤進展。",
        "regimen": "Arm 1: Pembrolizumab 200mg Q3W + Chemo (Pacli+Cis/Carbo) ± Bevacizumab 15mg/kg Q3W。 Arm 2: Placebo + Chemo ± Bev。",
        "inclusion": ["persistent/recurrent/metastatic cervical cancer", "1L systemic therapy", "可接受 ± bev", "主要分析常以 PD-L1 CPS 分層"],
        "exclusion": ["既往免疫治療。", "活動性自體免疫需治療。", "不可控感染等"],
        "outcomes": "CPS≥1 族群 mOS: 28.6m vs 16.5m (HR 0.60); ITT 全人群 OS HR 0.63; Grade ≥3 AE 比例高（化療背景為主；加 pembro 後免疫相關 AE 增加）"},

    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 innovaTV 301 (ENGOT-cx12)", "pharma": "Genmab", "drug": "Tisotumab Vedotin (ADC)", 
     "pop_results": "Tisotumab vedotin相較醫師選擇化療改善OS（OS HR 0.70），代表ADC在復發/轉移頸癌的里程碑，後線 ADC 突破：OS HR 0.70; ORR 17.8%",
     "rationale": "標靶組織因子 (Tissue Factor) ADC，解決後線化療耐藥。",
     "regimen": "Arm A: Tisotumab Vedotin 2.0 mg/kg IV Q3W。 Arm B: 醫師選擇化療 (Chemo SoC)。",
     "inclusion": ["recurrent/metastatic cervical cancer。", "2L/3L 治療情境（依試驗）"],
     "exclusion": ["不適合 ADC/既往相關藥物限制。", "嚴重角膜/眼部風險需評估（TV 常見眼毒性管理）。", "其他共病等"],
     "outcomes": "mOS: 11.5m vs 9.5m (HR 0.70); ORR 17.8% vs 5.2%。AE包括出血、周邊神經病變、眼部 AE（需預防性眼藥水/眼科監測）"},

    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Locally Advanced (CCRT)"], 
        "name": "📚 CALLA", "pharma": "AZ", "drug": "Durvalumab + CCRT", 
        "pop_results": "整體試驗結果為陰性。在局部晚期子宮頸癌中，同步化放療加入 Durvalumab 並未顯著改善 PFS (HR 0.84; P=0.174)。",
        "rationale": "探索 PD-L1 抑制劑與同步化放療 (CCRT) 聯用是否能產生協同免疫效應。",
        "regimen": "Arm A：durvalumab + CCRT（並於 CCRT 後持續 durvalumab）。 Arm B：placebo + CCRT（並於後續持續 placebo）。",
        "inclusion": ["untreated locally advanced cervical cancer，接受根治性 CCRT。"],
        "exclusion": ["既往免疫治療。", "活動性自體免疫需治療。", "放療/化療禁忌等"],
        "outcomes": "PFS未達顯著，HR 0.84 (95% CI 0.65-1.08)，顯示「all-comers」下加 durvalumab 未能成為新標準（可能需 biomarker 精選）。"},
    
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], 
        "name": "📚 GOG-240", "pharma": "NCI / GOG", "drug": "Chemo + Bevacizumab", 
        "pop_results": "轉移性子宮頸癌里程碑：首個證明加入 Bevacizumab 能顯著延長 OS (16.8m vs 13.3m, HR 0.71) 的研究。",
        "rationale": "利用抗血管新生藥物協同雙標靶化療，強化對晚期子宮頸癌的系統性控制。",
        "regimen": "Cisplatin + Paclitaxel (或 Topotecan + Paclitaxel) 聯用 Bevacizumab 15mg/kg Q3W。",
        "inclusion": ["復發、持久性或轉移性子宮頸癌", "先前未接受過針對 R/M 之化療", "ECOG 0-1"],
        "exclusion": ["臨床顯著之心血管疾病", "曾受過全身性血管抑制劑治療"],
        "outcomes": "mOS: 16.8m (vs 13.3m, HR 0.71, P=0.004)。"},

    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Locally Advanced (CCRT)"], 
        "name": "📚 GOG-240", "pharma": "NCI / GOG", "drug": "Chemo + Bevacizumab", 
        "pop_results": "轉移性子宮頸癌里程碑：首個證明加入 Bevacizumab 能顯著延長 OS (16.8m vs 13.3m, HR 0.71) 的研究。",
        "rationale": "利用抗血管新生藥物協同雙標靶化療，強化對晚期子宮頸癌的系統性控制。",
        "regimen": "Cisplatin + Paclitaxel (或 Topotecan + Paclitaxel) 聯用 Bevacizumab 15mg/kg Q3W。",
        "inclusion": ["復發、持久性或轉移性子宮頸癌", "先前未接受過針對 R/M 之化療", "ECOG 0-1"],
        "exclusion": ["臨床顯著之心血管疾病", "曾受過全身性血管抑制劑治療"],
        "outcomes": "mOS: 16.8m (vs 13.3m, HR 0.71, P=0.004)。"},
    
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], 
        "name": "📚 EMPOWER-Cervical 1", "pharma": "Regeneron", "drug": "Cemiplimab 單藥", 
        "pop_results": "二線後單藥免疫治療重要指標：相較化療顯著延長 OS (mOS 12.0m vs 8.5m; HR 0.69)，不論組織型態均有獲益。",
        "rationale": "針對一線鉑類化療失敗後之患者，利用 PD-1 阻斷提供持久緩解與生存優勢。",
        "regimen": "Arm A：cemiplimab。 Arm B：physician’s choice single-agent chemo。",
        "inclusion": ["recurrent/metastatic cervical cancer。", "progressed after 1L platinum"],
        "exclusion": ["既往免疫治療。", "活動性自體免疫需治療。", "不可控感染等"],
        "outcomes": "OS 顯著改善，ITT 全人群 OS HR 0.69 (95% CI 0.56-0.84)。"},
    
    { "cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], 
        "name": "📚 BEATcc", "pharma": "Roche", "drug": "Atezolizumab + Chemo + Bev", 
        "pop_results": "一線 R/M 子宮頸癌：在化療+標靶基礎上加入 Atezolizumab，顯著延長 PFS (13.7m vs 10.4m) 與 OS (32.1m vs 22.8m)，PFS HR 0.62；OS HR 0.68）。",
        "rationale": "PD-L1 阻斷併用 VEGF 抑制劑與化療，三軌聯用強化腫瘤微環境之殺傷力。",
        "regimen": "Arm A：atezolizumab + bevacizumab + platinum chemo（含 paclitaxel） → atezolizumab + bev maintenance。 Arm B：bevacizumab + platinum chemo → bev maintenance。",
        "inclusion": ["untreated metastatic/persistent/recurrent cervical cancer。", "可接受含 bev 的標準一線"],
        "exclusion": ["既往免疫治療。", "活動性自體免疫需治療。", "不適合 bev（出血/廔管/血栓高風險等）"],
        "outcomes": "mPFS HR 0.62; mOS HR 0.68 (95% CI 0.52-0.88)。PFS 與 OS 皆顯著改善，建立「PD-L1 inhibitor + GOG240 backbone」的新一線選項"},
    
    {"cancer": "Cervical", 
        "pos": ["P-TX"], 
        "sub_pos": ["Early Stage (Surgery)"], 
        "name": "📚 LACC Trial", "pharma": "NEJM / Academic", "drug": "Open vs MIS Radical Hysterectomy", 
        "pop_results": "手術黃金準則：證實微創手術 (MIS) 相較於傳統開腹手術，其復發風險顯著較高且三年存活率較低。",
        "rationale": "評估在子宮頸癌根治術中，達文西或腹腔鏡微創手術是否能達成與開腹手術同等的腫瘤學預後。",
        "regimen": "對照組: 傳統開腹根治性子宮切除術 (Open Radical Hysterectomy); 試驗組: 微創根治性子宮切除術 (MIS Radical Hysterectomy)。",
        "inclusion": [
            "FIGO 2009 Stage IA1 (有 LVSI), IA2, 或 IB1 子宮頸癌",
            "組織學分型為鱗癌、腺癌或腺鱗癌",
            "ECOG 0-1"],
        "exclusion": [
            "腫瘤直徑 > 4cm",
            "已知有淋巴結轉移或遠端轉移"],
        "outcomes": "3yr DFS Rate: 91.2% (MIS) vs 97.1% (Open); HR for recurrence 3.74 (P=0.002)。"},
    
    {"cancer": "Cervical", 
        "pos": ["P-TX"], 
        "sub_pos": ["Early Stage (Surgery)"], 
        "name": "📚 SHAPE Trial (CCTG CX.5)", "pharma": "CCTG / Academic", "drug": "Simple vs Radical Hysterectomy", 
        "pop_results": "低風險手術降階：針對低風險早期患者，單純子宮切除 (Simple) 的三年盆腔復發率不劣於廣泛性子宮切除 (Radical)。",
        "rationale": "探討對於預後極佳的低風險早期患者，是否能透過減少切除範圍來降低術後併發症並維持生存率。",
        "regimen": "對照組: 廣泛性子宮切除 (Radical Hysterectomy) + 盆腔淋巴結清掃; 試驗組: 單純子宮切除 (Simple Hysterectomy) + 盆腔淋巴結清掃。",
        "inclusion": [
            "FIGO 2018 Stage IA2 或 IB1 (≤ 2cm)",
            "間質浸潤深度 < 10mm",
            "Grade 1-3 鱗癌、腺癌或腺鱗癌"],
        "exclusion": [
            "影像學懷疑淋巴結轉移",
            "小細胞神經內分泌癌"],
        "outcomes": "3yr Pelvic Recurrence: 2.52% (Simple) vs 2.17% (Radical); 符合非劣效性標準 (P<0.05)。"},

    {"cancer": "Cervical", 
        "pos": ["P-TX"], 
        "sub_pos": ["Locally Advanced (NIC)"], 
        "name": "📚 NACI Study", "pharma": "Henlius", "drug": "Camrelizumab + NACT", 
        "pop_results": "新輔助免疫強效應：針對局部晚期 (LACC)，pCR（病理完全緩解）率高達 38.6%，顯著優於傳統新輔助化療。",
        "rationale": "利用 PD-1 抑制劑與化療聯用作為手術前的前導治療，旨在縮小腫瘤體積並清除微小轉移病灶，提高手術切除率與長期存活。",
        "regimen": "Camrelizumab 200mg + Cisplatin/Paclitaxel 每 3 週一週期，共 2-3 週期，隨後進行根治性手術。",
        "inclusion": ["Stage IB3, IIA2, IIB (FIGO 2018) 局部晚期子宮頸癌", "ECOG 0-1", "未曾接受過化放療"],
        "outcomes": "pCR Rate: 38.6%; ORR: 97.7%; 主要終點為病理緩解率與手術轉化率。"},
    
    {"cancer": "Cervical", 
        "pos": ["P-TX"], 
        "sub_pos": ["Locally Advanced (CCRT)"], 
        "name": "📚 OUTBACK (ANZGOG 0902)", "pharma": "GOG / ANZGOG", "drug": "CCRT + Adjuvant Chemo", 
        "pop_results": "輔助化療負向結論：在標準 CCRT 後額外增加 4 週期輔助化療，並『未』改善 5 年 OS 或 PFS (HR 0.91)。",
        "rationale": "驗證在同步化放療完成後加入全身性化療，是否能進一步清除遠端轉移，結果證明其毒性較高且無額外益處。",
        "regimen": "標準同步化放療 (CCRT) 結束後，接續 Carboplatin/Paclitaxel 每 3 週一週期，共 4 週期。",
        "inclusion": ["Stage IB2-IVA 局部晚期子宮頸癌", "適合接受 CCRT 與隨後之化療"],
        "outcomes": "5yr OS: 72% (CCRT+Chemo) vs 71% (CCRT); PFS HR: 0.91 (P=0.61)。"},
    
    {"cancer": "Cervical", 
        "pos": ["P-TX"], 
        "sub_pos": ["Locally Advanced (NIC)"], 
        "name": "📚 NATIC Trial", "pharma": "BeiGene / SYSU", "drug": "Tislelizumab + NACT", 
        "pop_results": "新輔助免疫新選擇：Tislelizumab 聯用化療達成 41% 的 pCR 率，展現強大的術前腫瘤降階能力。",
        "rationale": "探索 PD-1 抑制劑 Tislelizumab 在局部晚期患者手術前的應用，以評估其對後續手術病理結果的改善程度。",
        "regimen": "Tislelizumab 200mg + Paclitaxel/Cisplatin Q3W，共 3 週期，隨後進行廣泛性子宮切除術。",
        "inclusion": ["FIGO 2018 Stage IB3-IIB 局部晚期鱗癌/腺癌/腺鱗癌", "ECOG 0-1"],
        "outcomes": "pCR Rate: 41%; ORR: 94.7%; 3 級以上治療相關不良反應率約 25.6%。"},
    
    {"cancer": "Cervical", 
        "pos": ["P-TX"], 
        "sub_pos": ["Locally Advanced (NIC)"], 
        "name": "📍 Cadonilimab + NACT → Surgery", "pharma": "Akeso", "drug": "Cadonilimab + NACT", 
        "pop_results": "雙特異性抗體領航：PD-1/CTLA-4 雙特異性抗體聯用化療作為新輔助治療，展現出比單免疫更高的臨床獲益潛力。",
        "rationale": "利用雙靶點阻斷機制強化腫瘤微環境的免疫活化，為高復發風險的 LACC 患者提供手術前的強力介入方案。",
        "regimen": "Cadonilimab (10mg/kg) + Carboplatin/Paclitaxel Q3W x 3 週期，評估後進行手術或放療。",
        "inclusion": ["新診斷 FIGO Stage IB3-IIA2 (需含巨大腫瘤) 或 IIB-IVA 期患者"],
        "outcomes": "初步研究顯示 ORR 表現優異，病理緩解數據正在追蹤中 (Ongoing)。"},
    
    # ==========================
    # === Ovarian Published ===
    # ==========================
    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PROC (Resistant Recur)"], "name": "📚 MIRASOL (GOG-3045)", "pharma": "ImmunoGen", "drug": "Mirvetuximab Soravtansine", 
     "pop_results": "在FRα高表現、鉑抗藥卵巢癌中，Mirvetuximab較化療改善PFS與OS（PFS HR 0.65；OS HR 0.67），確立FRα ADC的關鍵地位，PROC OS 突破：OS HR 0.67; ORR 42.3%",
     "rationale": "針對 FRα 高表現 PROC 患者，首個 ADC 生存獲益研究。",
     "regimen": "族群：FRα-high、platinum-resistant（依 IHC 門檻）。Arm A: Mirvetuximab 6.0 mg/kg (AIBW) IV Q3W 直至進展。 Arm B: 醫師選擇化療 如 weekly paclitaxel / PLD / topotecan）。",
     "inclusion": ["platinum-resistant 高級別漿液性為主。", "FRα 高表現。", "既往治療線數依試驗。"],
     "exclusion": ["不符合 FRα 門檻。", "不可控眼部/神經毒性風險。"],
     "outcomes": "mOS: 16.4m vs 12.7m (HR 0.67); mPFS 5.6m vs 4.0m (HR 0.65)。ORR 亦顯著較佳；Grade ≥3 AE 較少"},

    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], 
        "name": "📚 GOG-0218", "pharma": "Roche / GOG", "drug": "Chemo + Bevacizumab", 
        "pop_results": "一線標靶基石：首個證明在化療基礎上加入 Bevacizumab 並接續維持治療，能顯著延長 PFS (HR 0.72)，奠定標靶維持標準。",
        "rationale": "透過抗血管新生藥物阻斷 VEGF 通路，在一線化療期間與之後抑制腫瘤新生血管，達到長期控制。",
        "regimen": "Bevacizumab (15mg/kg Q3W) 聯用 Carbo/Pacli x6 週期，隨後單藥 Bevacizumab 維持治療至第 22 週期。",
        "inclusion": ["新診斷 FIGO Stage III (不全切除) 或 Stage IV 上皮性卵巢癌", "ECOG 0-2", "接受過減積手術"],
        "exclusion": ["非上皮性卵巢癌", "有腸穿孔病史或高風險者", "傷口未癒合"],
        "outcomes": "mPFS: 14.1m (vs 10.3m, HR 0.717, P<0.001)。"},
    
    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], 
        "name": "📚 ICON7", "pharma": "Roche / ENGOT", "drug": "Chemo + Bevacizumab (Low Dose)", 
        "pop_results": "一線標靶證實：確認 Bev 聯用化療具備 PFS 獲益 (HR 0.81)，且在『高風險族群』觀察到 OS 延長獲益。",
        "rationale": "驗證較低劑量的 Bevacizumab (7.5mg/kg) 聯用化療與維持治療對全球卵巢癌患者的有效性與安全性。",
        "regimen": "Bevacizumab (7.5mg/kg Q3W) 聯用 Carbo/Pacli x6 週期，隨後單藥維持治療共 12 週期。",
        "inclusion": ["FIGO Stage I-II (高風險) 或 Stage III-IV 上皮性卵巢癌", "不限手術切除程度"],
        "exclusion": ["臨床顯著之心血管疾病", "近期有重大手術史"],
        "outcomes": "PFS HR: 0.81; 高風險族群 mOS: 39.7m (vs 30.2m, HR 0.64)。"},
    
    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], 
        "name": "📚 BOOST / ENGOT-ov15", "pharma": "Roche / ENGOT", "drug": "Bev 15m vs 30m", 
        "pop_results": "維持時程定案：比較 Bev 維持 15 個月與 30 個月，結果顯示延長至 30 個月並『無額外生存獲益』(HR 0.99)。",
        "rationale": "旨在確定 Bevacizumab 在一線維持治療的最佳持續時間，探討延長給藥是否能更有效延緩復發。",
        "regimen": "控制組: Bev (15mg/kg Q3W) 維持 15 個月; 試驗組: Bev (15mg/kg Q3W) 維持至 30 個月。",
        "inclusion": ["新診斷 FIGO Stage IIB-IV 上皮性卵巢癌", "完成化療併用 Bev 誘導治療者"],
        "exclusion": ["誘導期間疾病已進展者", "對 Bevacizumab 不耐受者"],
        "outcomes": "mPFS: 24.2m (15m) vs 26.0m (30m) (HR 0.99, P=0.90)。"},

    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["Low grade serous carcinoma"], 
        "name": "📍 NRG-GY019", "pharma": "NRG Oncology", "drug": "Letrozole vs Chemo→Letrozole", 
        "pop_results": "一線去化療挑戰：評估對於新診斷 LGSOC 患者，單用 Letrozole 是否不劣於傳統化療後接續維持治療。",
        "rationale": "低惡性度漿液性癌 (LGSOC) 對傳統化療反應率較低，此研究旨在驗證初期即使用內分泌治療的臨床效益。",
        "regimen": "Arm 1: Letrozole (2.5mg QD) 單藥治療直到進展；Arm 2: 傳統 6 週期化療 (CP) 後接續 Letrozole 維持治療。",
        "inclusion": ["新診斷 Stage II-IV 低惡性度漿液性卵巢癌/腹膜癌", "ECOG 0-2", "需提供組織學判定報告"],
        "exclusion": ["曾受過針對此疾病之全身性化療或標靶治療", "計畫接受維持性 PARPi 治療者"],
        "outcomes": "招募中 (Ongoing Recruitment)。"},
    
    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PSOC (Sensitive Recur)"], "name": "📚 DESKTOP III", "pharma": "AGO", "drug": "Secondary Cytoreduction Surgery", 
     "pop_results": "復發卵巢癌在嚴格選人（如AGO score）下，次減積手術帶來OS改善（死亡HR 0.75），奠定「選對人做手術」的價值，二次手術價值：R0 切除 mOS 53.7m",
     "rationale": "證明嚴選患者 (AGO Score+) 二次手術具生存獲益。",
     "regimen": "platinum-sensitive recurrent ovarian cancer（以 AGO score 等條件篩選可完全切除者）。手術組: 腫瘤完全切除手術後接續含鉑化療。 化療組: 單純含鉑複方化療。",
     "inclusion": ["首次鉑類敏感復發 (PFI > 6m)。", "可望達到 complete resection，AGO Score 陽性 (ECOG 0/大量腹水除外/R0 完全切除潛力)。"],
     "exclusion": ["無法達到 R0 或手術風險過高。", "其他重大共病。"],
     "outcomes": "ITT mOS: 53.7m vs 46.0m (HR 0.75, 95% CI 0.59-0.96); R0 切除者 mOS 達 61.9m（手術組較佳，前提是高比例 R0）。"},

    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["Neoadjuvant Setting"], "name": "📚 van Driel HIPEC", "pharma": "NEJM", "drug": "Surgery + HIPEC (Cisplatin)", 
     "pop_results": "間隔減積手術加入HIPEC可改善OS（死亡風險下降：OS HR 0.67），為「特定一線手術情境」引入HIPEC的重要證據，IDS 加溫：mOS 延長 12 個月 (HR 0.67)",
     "rationale": "術中加溫腹腔化療強化物理殺傷與滲透力。",
     "regimen": "stage III、NACT 後 間歇減積手術 (IDS) 時同步進行加溫 (42°C) 腹腔灌注 Cisplatin (100 mg/m2) 90 分鐘。Arm A：surgery + HIPEC cisplatin（常見 100 mg/m²、90 分鐘）+ 後續化療。Arm B：surgery（no HIPEC）+ 後續化療。",
     "inclusion": ["stage III epithelial ovarian cancer。", "NACT 後適合 interval debulking。"],
     "exclusion": ["不適合大手術或 HIPEC（腎功能、全身狀況等）。", "其他重大共病。"],
     "outcomes": "mOS: 45.7m vs 33.9m (HR 0.67, 95% CI 0.48-0.94)。recurrence-free survival 亦改善；Grade 3–4 AE 率相近。"},

    {"cancer": "Ovarian", 
        "pos": ["P-TX"], 
        "sub_pos": ["Neoadjuvant Setting"], 
        "name": "📚 EORTC 55971 (NEJM 2010)", "pharma": "EORTC", "drug": "PDS vs NACT", 
        "pop_results": "NACT 非劣效性里程碑：首個證明 NACT 隨後進行 IDS 與 PDS 相比，總生存期 (OS) 相當，且手術併發症與死亡率顯著降低。",
        "rationale": "針對 Stage IIIC/IV 患者，探討先給予化療縮小腫瘤體積後再手術，是否能達成與直接大範圍手術同等的預後並降低風險。",
        "regimen": "PDS 組: 直接減積手術 -> 含鉑化療; NACT 組: 3 週期化療 -> IDS 手術 -> 3 週期化療。",
        "inclusion": ["FIGO Stage IIIC 或 IV 上皮性卵巢癌/腹膜癌", "ECOG 0-2", "具備組織學證據"],
        "outcomes": "mOS: 30m (NACT) vs 29m (PDS)；NACT 組重大併發症顯著較少。"},
    
    {"cancer": "Ovarian", 
        "pos": ["P-TX"], 
        "sub_pos": ["Neoadjuvant Setting"], 
        "name": "📚 CHORUS (Lancet 2015)", "pharma": "MRC", "drug": "PDS vs NACT (UK Standard)", 
        "pop_results": "NACT 標準再次確立：確認 NACT 非劣於 PDS，且顯著減少術後 28 天內的死亡率與嚴重併發症。",
        "rationale": "在英國醫療體系下驗證 EORTC 55971 的結果，旨在評估 NACT 是否應成為晚期高風險患者的常規選擇。",
        "regimen": "NACT 組: 3 週期 CP 方案 -> IDS -> 3 週期 CP；PDS 組: 直接手術 -> 6 週期 CP。",
        "inclusion": ["晚期上皮性卵巢癌", "CT 顯示腫瘤負荷大或體能狀況較差者"],
        "outcomes": "mOS: 24.1m (NACT) vs 22.6m (PDS)；NACT 顯著改善生活品質與手術安全性。"},
    
    {"cancer": "Ovarian", 
        "pos": ["P-TX"], 
        "sub_pos": ["Neoadjuvant Setting"], 
        "name": "📚 EORTC+CHORUS Pooled / Long-term", "pharma": "Lancet Oncol 2018", "drug": "NACT vs PDS Meta-analysis", 
        "pop_results": "精準分流指引：長期隨訪顯示 Stage IV 或腫瘤負荷極大 (>5cm) 者，NACT 具備顯著生存獲益優勢。",
        "rationale": "合併兩大試驗數據進行亞組分析，回答「哪些人更適合先做 NACT」這個核心臨床問題。",
        "regimen": "對 EORTC 55971 與 CHORUS 共 1,220 名患者進行長期存活與病灶特徵分析。",
        "inclusion": ["Stage IIIC/IV 患者", "腫瘤直徑 >5cm 或 Stage IV 轉移者"],
        "outcomes": "Stage IV 族群: NACT 顯著提升 OS (HR 0.76)；Stage IIIC 且轉移灶較小者 PDS 可能略優。"},
    
    {"cancer": "Ovarian", 
        "pos": ["P-TX"], 
        "sub_pos": ["Neoadjuvant Setting"], 
        "name": "📚 SCORPION (Phase III, 2020)", "pharma": "Fagotti et al.", "drug": "NACT vs PDS (High Tumor Burden)", 
        "pop_results": "高腫瘤負荷對策：針對 Fagotti 評分 ≥8 者，NACT 顯著降低圍術期發病率且不影響 PFS/OS。",
        "rationale": "利用腹腔鏡 Fagotti 評分精準篩選「無法達成 R0」的高風險患者，探討 NACT 的介入價值。",
        "regimen": "NACT 組: 先行化療後進行 IDS；PDS 組: 強力嘗試直接減積手術。",
        "inclusion": ["晚期卵巢癌", "腹腔鏡預估 Fagotti 評分 ≥8（腫瘤分布極廣）"],
        "outcomes": "重大併發症率: NACT 組顯著較低；PFS 與 OS 兩組無顯著統計學差異。"},
    
    {"cancer": "Ovarian", 
        "pos": ["P-TX"], 
        "sub_pos": ["Neoadjuvant Setting"], 
        "name": "📚 JCOG0602 (Phase III)", "pharma": "Japan Oncology", "drug": "NACT vs PDS (Japanese Data)", 
        "pop_results": "日本實證支持：證實 NACT 可顯著縮短手術時間、減少失血量，並達成與 PDS 相當的生存預後。",
        "rationale": "在亞洲人群中驗證 NACT 的非劣效性，特別觀察手術侵襲性的降低程度。",
        "regimen": "NACT 組: 4 週期 CP -> IDS -> 4 週期 CP；PDS 組: 直接手術 -> 8 週期 CP。",
        "inclusion": ["FIGO Stage III/IV 卵巢癌/腹膜癌", "預估手術難度高者"],
        "outcomes": "mOS: 44.3m (NACT) vs 49.0m (PDS)；達到非劣效性終點且 NACT 手術負擔極輕。"},
    
    {"cancer": "Ovarian", 
        "pos": ["P-TX"], 
        "sub_pos": ["Neoadjuvant Setting"], 
        "name": "📍 TRUST (Ongoing)", "pharma": "ENGOT-ov33", "drug": "Quality-controlled PDS vs NACT", 
        "pop_results": "高品質手術挑戰：在全球高品質手術中心重新評估 PDS 是否優於 NACT，備受學界期待。",
        "rationale": "批評者認為早期試驗的 PDS 手術品質不一，TRUST 要求極高的 R0 率，旨在為 PDS 重新正名。",
        "regimen": "由經過認證的「高品質手術中心」進行隨機分配，嚴格執行根治性 PDS 手術。",
        "inclusion": ["新診斷 Stage IIIB-IVB 卵巢癌", "體能狀況良好 (ECOG 0-1)"],
        "outcomes": "試驗進行中 (Ongoing)；主要終點為總生存期 (OS)，預計將提供 PDS 最終地位的關鍵證據。"},

    {"cancer": "Ovarian", 
        "pos": ["P-TX"], 
        "sub_pos": ["DDCT Setting"], 
        "name": "📚 JGOG 3016", "pharma": "JGOG", "drug": "Dose-dense Paclitaxel", 
        "pop_results": "劑量密集化療重大突破：在亞洲人群中，每週 Paclitaxel 顯著延長 PFS (28m vs 17m) 與 OS (HR 0.75)。",
        "rationale": "利用更頻繁的給藥頻率（每週一次）來抑制腫瘤血管新生並減少腫瘤細胞在化療間期的修復機會。",
        "regimen": "Dose-dense: Paclitaxel 80mg/m2 (D1, 8, 15) + Carboplatin (AUC 6, D1) 每 21 天一週期，共 6 週期。",
        "inclusion": ["Stage II-IV 上皮性卵巢癌/腹膜癌", "完成初步減積手術者", "ECOG 0-2"],
        "outcomes": "mPFS: 28.2m (vs 17.5m, HR 0.71, P=0.0015)；mOS: 100.5m (vs 62.2m, HR 0.75, P=0.039)。"},
    
    {"cancer": "Ovarian", 
        "pos": ["P-TX"], 
        "sub_pos": ["DDCT Setting"], 
        "name": "📚 GOG-262", "pharma": "GOG", "drug": "Weekly Paclitaxel ± Bev", 
        "pop_results": "標靶併用之權衡：在『不使用』Bevacizumab 的患者中，每週給藥顯著延長 PFS；但若併用標靶，則無額外獲益。",
        "rationale": "在北美人群中驗證 JGOG 3016 的結果，並探討併用 Bevacizumab 是否會影響每週化療方案的優勢。",
        "regimen": "Weekly: Paclitaxel 80mg/m2 每週連續給藥 + Carboplatin (AUC 6) 每 3 週一次，± Bevacizumab。",
        "inclusion": ["Stage II-IV 上皮性卵巢癌", "不限手術切除程度 (PDS 或 NACT/IDS 均可)"],
        "outcomes": "不含 Bev 族群 PFS: 14.2m (Weekly) vs 10.3m (Q3W)；含 Bev 族群則兩組無差異。"},
    
    {"cancer": "Ovarian", 
        "pos": ["P-TX"], 
        "sub_pos": ["DDCT Setting"], 
        "name": "📚 ICON8", "pharma": "GCIG / MRC", "drug": "Standard vs Weekly Pacli vs Weekly Carbo/Pacli", 
        "pop_results": "歐洲大型實證：在歐洲人群中，每週化療方案 (Arm 2/3) 相較於標準 Q3W 方案『並未』延長 PFS。",
        "rationale": "旨在利用三臂隨機試驗確定每週單藥或雙藥化療是否應成為上皮性卵巢癌的新標準輔助治療。",
        "regimen": "Arm 1: Q3W (Standard); Arm 2: Weekly Pacli (80mg/m2) + Q3W Carbo; Arm 3: Weekly Pacli (70mg/m2) + Weekly Carbo (AUC 2)。",
        "inclusion": ["Stage IC-IV 上皮性卵巢癌", "計畫接受輔助化療或 NACT 者"],
        "outcomes": "mPFS: Arm 1 (17.7m), Arm 2 (20.8m), Arm 3 (21.0m)；三組間無統計學顯著差異。"},
    
    {"cancer": "Ovarian", 
        "pos": ["P-TX"], 
        "sub_pos": ["DDCT Setting"], 
        "name": "📚 MITO-7", "pharma": "MITO / ENGOT", "drug": "Low-dose Weekly Carbo/Pacli", 
        "pop_results": "去毒強化標準：每週低劑量組合雖未延長 PFS，但顯著提升生活品質並降低血液與神經毒性。",
        "rationale": "針對體能狀況或擔心毒性的患者，探討使用更溫和的每週低劑量組合是否能維持療效並改善耐受性。",
        "regimen": "Weekly: Paclitaxel 60mg/m2 + Carboplatin (AUC 2) 同時每週給藥一次，共 18 週。",
        "inclusion": ["Stage I-IV 上皮性卵巢癌", "ECOG 0-2", "適合接受一線鉑類化療者"],
        "outcomes": "mPFS: 17.3m (Weekly) vs 18.3m (Q3W, P=0.66)；生活品質量表數據顯著優於 Q3W 組。"},
    
    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 LION", "pharma": "NEJM", "drug": "No Lymphadenectomy", 
     "pop_results": "系統性淋巴清掃不改善存活（OS HR 1.06；PFS HR 1.11）且併發症增加，改變了「外觀正常淋巴結」患者的手術範式，臨床 LN 陰性免清掃：OS 無差異 (HR 1.06)",
     "regimen": "在「臨床/影像陰性淋巴結」且完成腫瘤切除的 advanced ovarian cancer。Arm A：systematic pelvic + para-aortic lymphadenectomy。Arm B：no lymphadenectomy。",
     "inclusion": ["advanced ovarian cancer。", "complete resection。", "淋巴結臨床陰性。"],
     "exclusion": ["明顯淋巴結病灶。", "無法耐受手術延長。"],
     "outcomes": "OS HR 1.06（無獲益）；PFS 亦無差；但手術併發症增加。mOS: 65.5m vs 69.2m (HR 1.06)。臨床 LN(-) 者免清掃。"},

    {"cancer": "Ovarian", 
        "pos": ["P-TX"], 
        "sub_pos": ["IP Setting"], 
        "name": "📚 SWOG-8501 / GOG-104 (NEJM 1996)", "pharma": "GOG / SWOG", "drug": "IP Cisplatin vs IV Cisplatin", 
        "pop_results": "IP 化療首個里程碑：針對 Stage III 減積手術後殘餘病灶 <2cm 患者，IP Cisplatin 顯著改善 OS (HR 0.76)。",
        "rationale": "利用腹腔內直接給藥，增加腹膜病灶處的局部藥物濃度，並減少全身性毒性。",
        "regimen": "IP 組: Cisplatin 100mg/m2 (IP) + Cyclophosphamide 600mg/m2 (IV) Q3W x6 週期。",
        "inclusion": ["Stage III 上皮性卵巢癌", "減積手術後殘餘腫瘤直徑 <2cm", "ECOG 0-2"],
        "outcomes": "mOS: 49m (IP) vs 41m (IV)；死亡風險降低 24%。"},
    
    {"cancer": "Ovarian", 
        "pos": ["P-TX"], 
        "sub_pos": ["IP Setting"], 
        "name": "📚 GOG-114", "pharma": "GOG", "drug": "IP Cisplatin/Pacli vs IV Standard", 
        "pop_results": "IP 強化方案探索：證實 IP Cisplatin 聯用 Paclitaxel 維持了生存獲益，但毒性顯著增加 (血液毒性與神經毒性)。",
        "rationale": "探討在 IP Cisplatin 的基礎上加入現代化療藥物 Paclitaxel 是否能進一步提升 PFS 與 OS。",
        "regimen": "IP 組: Carboplatin (IV) 誘導 -> IP Cisplatin 100mg/m2 + IV Paclitaxel -> 維持期 IP Paclitaxel。",
        "inclusion": ["Stage III 上皮性卵巢癌", "殘餘病灶 ≤1cm", "具備良好的腎功能與體能"],
        "outcomes": "mPFS: 27.9m (IP) vs 22.2m (IV, P=0.01)；mOS 亦有顯著獲益趨勢。"},
    
    {"cancer": "Ovarian", 
        "pos": ["P-TX"], 
        "sub_pos": ["IP Setting"], 
        "name": "📚 GOG-172 (NEJM 2006)", "pharma": "GOG", "drug": "The IP Gold Standard", 
        "pop_results": "IP 化療黃金標準：奠定 Stage III 殘餘病灶 ≤1cm 患者使用 IP 化療的地位，OS 驚人延長達 16 個月。",
        "rationale": "確認在 R0/R1 手術後，合併使用 IV 與 IP Paclitaxel/Cisplatin 是目前最有效的輔助化療策略。",
        "regimen": "D1: Paclitaxel 135mg/m2 (IV 24h); D2: Cisplatin 100mg/m2 (IP); D8: Paclitaxel 60mg/m2 (IP) Q3W x6。",
        "inclusion": ["Stage III 上皮性卵巢癌/腹膜癌", "最優減積手術後 (殘餘病灶 ≤1cm)", "ECOG 0-1"],
        "outcomes": "mOS: 65.6m (IP) vs 49.7m (IV, P=0.03)；mPFS: 23.8m (IP) vs 18.3m (IV)。"},
    
    {"cancer": "Ovarian", 
        "pos": ["P-TX"], 
        "sub_pos": ["IP Setting"], 
        "name": "📚 GOG-252", "pharma": "GOG", "drug": "IP vs IV with Bevacizumab", 
        "pop_results": "IP 地位重檢視：在所有組別均併用 Bevacizumab 的情況下，IP 與 IV 組的 PFS 並無顯著差異且 IP 組毒性較高。",
        "rationale": "探討在標靶時代 (Bevacizumab)，IP 投藥模式是否仍能維持其優於傳統 IV 投藥的生存優勢。",
        "regimen": "三組均加 Bev: 1. IV Carbo/Pacli; 2. IP Carbo/IV Pacli; 3. IP Cis/Pacli (按 GOG-172 修改)。",
        "inclusion": ["Stage II-III 上皮性卵巢癌", "殘餘病灶 ≤1cm", "適合使用標靶藥物 Bevacizumab"],
        "outcomes": "mPFS: 三組均落在 27-28 個月左右 (無統計差異)；IP 組導管相關併發症較多。"},
    
    {"cancer": "Ovarian", 
        "pos": ["P-TX"], 
        "sub_pos": ["IP Setting", "Neoadjuvant Setting"], 
        "name": "📚 OV21/PETROC (GCIG)", "pharma": "NCIC / GCIG", "drug": "IP Carboplatin vs IV Carboplatin", 
        "pop_results": "IP 藥物改良研究：證明 IP Carboplatin 具有良好耐受性，且在 PFS 上展現出與 IP Cisplatin 競爭的潛力 (Phase II)。",
        "rationale": "旨在利用毒性較低的 Carboplatin 取代 Cisplatin 進行腹腔給藥，以解決 GOG-172 方案的高毒性與低完成率問題。",
        "regimen": "IP 組: Carboplatin (AUC 6) IP Q3W x6 週期；對照組為 IV Carboplatin。",
        "inclusion": ["Stage II-III 卵巢癌/腹膜癌", "新輔助化療 (NACT) 隨後接受 IDS 者亦可入案"],
        "outcomes": "PFS HR: 0.82 (P=0.20)；對於 NACT 患者，IP 組顯示出較佳的腹膜控制趨勢。"},
    
    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["Low grade serous carcinoma"], 
        "name": "📚 GOG-281 / LOGS", "pharma": "Targeted", "drug": "Trametinib", 
        "pop_results": "LGSOC 標靶重大突破：與醫師選擇化療相比，Trametinib 顯著降低 52% 疾病進展風險 (HR 0.48)，ORR 達 26%。",
        "rationale": "針對低惡性度漿液性卵巢癌 (LGSOC) 中常見的 MAPK 路徑異常活化，利用 MEK 抑制劑進行精準標靶阻斷。",
        "regimen": "Trametinib 2.0 mg 每日口服一次，持續治療直到疾病進展或不可耐受之毒性。",
        "inclusion": ["復發性低惡性度漿液性卵巢癌/腹膜癌", "先前接受過至少一次含鉑化療", "ECOG 0-1"],
        "exclusion": ["曾受過其他 MEK 抑制劑治療", "臨床顯著的心臟功能異常"],
        "outcomes": "mPFS: 13.0m (vs 7.2m, HR 0.48, 95% CI 0.36-0.64)。"},
    
    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["Low grade serous carcinoma"], 
        "name": "📍 RAMP-201", "pharma": "Verastem Oncology", "drug": "Avutometinib + Defactinib", 
        "pop_results": "LGSOC 雙重阻斷新高度：KRAS 突變族群 ORR 高達 55%；全體族群 ORR 達 45%。",
        "rationale": "結合 RAF/MEK 雙重抑制劑 (Avutometinib) 與 FAK 抑制劑 (Defactinib)，旨在克服單一通路阻斷後產生的補償性耐藥機制。",
        "regimen": "Avutometinib 3.2 mg (兩次/週) + Defactinib 200 mg (兩次/日)，採 3 週給藥 1 週休息之週期設計。",
        "inclusion": ["復發性 LGSOC (不限 KRAS 狀態)", "先前接受過含鉑化療及標靶治療", "提供腫瘤組織樣品"],
        "exclusion": ["活動性腦轉移", "曾受過同類 FAK 抑制劑治療"],
        "outcomes": "KRAS mut ORR: 55%; 全體 ORR: 45% (初步數據亮眼)。"},
    
    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["Low grade serous carcinoma"], 
        "name": "📚 GOG-3026", "pharma": "Novartis", "drug": "Ribociclib + Letrozole", 
        "pop_results": "LGSOC 去化療組合：CDK4/6 抑制劑併用芳香環轉化酶抑制劑，達成 ORR 23% 與 79% 的臨床獲益率 (CBR)。",
        "rationale": "利用內分泌治療阻斷激素受體，並協同 CDK4/6 抑制劑達成更強的細胞週期停滯效應。",
        "regimen": "Ribociclib 400 mg QD (連服 3 週休息 1 週) + Letrozole 2.5 mg QD (持續每日口服)。",
        "inclusion": ["復發性 LGSOC", "ER/PR 陽性表達者優先", "不限先前治療線數"],
        "exclusion": ["無法吞嚥口服藥物者", "併用強效 CYP3A4 誘導劑"],
        "outcomes": "mPFS: 19.1m; ORR: 23%; CBR: 79%。"},
    
    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["Low grade serous carcinoma"], 
        "name": "📚 MILO / ENGOT-ov11", "pharma": "Array BioPharma", "drug": "Binimetinib", 
        "pop_results": "LGSOC 標靶探索：比較 MEK 抑制劑 Binimetinib 與化療，雖試驗因無效性早期停止，但仍為 LGSOC 重要研究數據。",
        "rationale": "針對低惡性度漿液性癌 (LGSOC) 常見之 MAPK 通路激活，嘗試利用單藥 MEK 抑制劑達成控制。",
        "regimen": "Binimetinib 45 mg 每日口服兩次，對比醫師選擇之化療 (PLD/Pacli/Topo)。",
        "inclusion": ["復發性低惡性度漿液性卵巢癌", "先前接受過至少一線含鉑化療", "不限 KRAS/BRAF 狀態"],
        "outcomes": "mPFS: 9.1m (Binimetinib) vs 10.6m (Chemo)，HR 1.21 (未達預期獲益)。"},

    {"cancer": "Ovarian", 
        "pos": ["P-TX"], 
        "sub_pos": ["Clear Cell Carcinoma"], 
        "name": "📚 JGOG3017 / GCIG", "pharma": "JGOG", "drug": "Irinotecan + Cisplatin vs TC", 
        "pop_results": "OCCC 一線標準挑戰：比較 Irinotecan/Cisplatin (CP) 與傳統 TC 方案，結果顯示在 PFS 或 OS 上無顯著差異。",
        "rationale": "考量明細胞癌 (OCCC) 對 Paclitaxel 較不敏感，嘗試利用對 OCCC 具潛在活性的 Irinotecan 方案進行一線挑戰。",
        "regimen": "Arm A: Irinotecan (60mg/m2 D1, 8, 15) + Cisplatin (60mg/m2 D1) Q4W; Arm B: Carboplatin (AUC 6) + Paclitaxel (175mg/m2) Q3W。",
        "inclusion": ["新診斷 FIGO Stage I-IV 明細胞癌 (OCCC)", "ECOG 0-2", "手術後病理證實"],
        "outcomes": "2yr PFS: 63.0% (CP) vs 67.3% (TC); mOS HR: 1.06 (P=0.72)。"},
    
    {"cancer": "Ovarian", 
        "pos": ["P-MT"], 
        "sub_pos": ["Clear Cell Carcinoma"], 
        "name": "📚 Temsirolimus + TC (Phase II)", "pharma": "GOG / NCI", "drug": "TC + Temsirolimus → Maint", 
        "pop_results": "OCCC 維持治療探索：在一線 TC 化療基礎上加入 mTOR 抑制劑並接續維持，結果顯示耐受性良好但未達預期之顯著 PFS 延長。",
        "rationale": "明細胞癌常伴隨 PI3K/Akt/mTOR 通路活化，利用 Temsirolimus 進行標靶干預並透過整合與鞏固策略強化療效。",
        "regimen": "誘導期: TC + Temsirolimus (25mg IV 每週) x6 週期; 維持期: Temsirolimus 單藥持續治療直至進展。",
        "inclusion": ["新診斷 FIGO Stage III-IV 明細胞癌", "ECOG 0-1", "完成初步減積手術"],
        "outcomes": "12m PFS Rate: 48%; mPFS: 11.2m; 證實 OCCC 仍具備極強的抗藥性瓶頸。"},
    
    {"cancer": "Ovarian", 
        "pos": ["R-TX"], 
        "sub_pos": ["Clear Cell Carcinoma"], 
        "name": "📚 GOG-254", "pharma": "GOG / NCI", "drug": "Sunitinib", 
        "pop_results": "OCCC 標靶救援：多靶點 TKI Sunitinib 在經治的明細胞癌中展現中等活性，PFS 達 2.7 個月。",
        "rationale": "針對 OCCC 高度表達 VEGF 的特性，利用口服多靶點 TKI 阻斷血管新生以尋求二線後的緩解機會。",
        "regimen": "Sunitinib 50 mg 每日口服一次，採 4 週給藥 2 週休息之週期 (Schedule 4/2)。",
        "inclusion": ["復發或持久性明細胞卵巢癌", "先前接受過 1-2 線含鉑治療失敗者", "ECOG 0-2"],
        "outcomes": "ORR: 6.7%; PFS-6 Rate: 23.3%; mPFS: 2.7m。"},
    
    {"cancer": "Ovarian", 
        "pos": ["R-TX"], 
        "sub_pos": ["Clear Cell Carcinoma"], 
        "name": "📚 MoST-CIRCUIT (Non-randomized)", "pharma": "Garvan Institute", "drug": "Nivolumab + Ipilimumab", 
        "pop_results": "OCCC 免疫雙阻斷：針對難治型 OCCC，Nivo+Ipi 組合展現亮眼的 ORR (24%) 與持久的疾病控制。",
        "rationale": "考量 OCCC 具備特定的免疫抑制環境，透過 PD-1 與 CTLA-4 雙重阻斷激發更強的 T 細胞抗腫瘤反應。",
        "regimen": "Nivolumab 3mg/kg + Ipilimumab 1mg/kg 每 3 週一次 x4 週期，隨後 Nivolumab 維持治療。",
        "inclusion": ["復發性明細胞卵巢癌", "先前接受過至少一線化療", "具備可測量病灶"],
        "outcomes": "ORR: 24%; 臨床獲益率 (CBR): 52%; 展現免疫治療在 OCCC 亞型中的特殊潛力。"},
    
    {"cancer": "Ovarian", 
        "pos": ["R-TX"], 
        "sub_pos": ["Clear Cell Carcinoma"], 
        "name": "📚 BrUOG 354 (Randomized Phase II)", "pharma": "Brown University", "drug": "Nivolumab vs Nivo+Ipi", 
        "pop_results": "OCCC 免疫方案對比：隨機對照顯示，雙免疫 (Nivo+Ipi) 在 ORR 與 PFS 上均優於單藥 Nivolumab。",
        "rationale": "旨在確定針對明細胞癌亞型，是否必須聯用 CTLA-4 抑制劑才能克服其免疫冷腫瘤的特徵。",
        "regimen": "Arm A: Nivolumab 單藥; Arm B: Nivolumab + Ipilimumab (1mg/kg) Q3W。",
        "inclusion": ["復發或轉移性明細胞卵巢癌", "ECOG 0-1", "允許先前接受過抗血管新生治療"],
        "outcomes": "Nivo+Ipi 組 ORR 顯著提升；中位 PFS 與持續緩解時間亦佔優勢。"},
    
    {"cancer": "Ovarian", 
        "pos": ["R-TX"], 
        "sub_pos": ["Clear Cell Carcinoma"], 
        "name": "📍 ATARI (ceralasertib ± olaparib)", "pharma": "ENGOT-ov58 / AstraZeneca", "drug": "Ceralasertib ± Olaparib", 
        "pop_results": "ARID1A 靶點精準醫療：針對 ARID1A 突變的 OCCC，ATR 抑制劑展現出 14% 的 ORR 與良好的疾病控制潛力。",
        "rationale": "ARID1A 突變導致 DNA 損傷修復壓力增加，利用 ATR 抑制劑 (Ceralasertib) 誘導合成致死，並探索與 PARPi 的協同效應。",
        "regimen": "Cohort 1 (ARID1A def): Ceralasertib 單藥; Cohort 2: Ceralasertib + Olaparib。",
        "inclusion": ["復發性明細胞癌或子宮內膜樣癌", "經 NGS 證實具備 ARID1A 缺失/突變", "鉑類耐藥或不適合含鉑治療者"],
        "outcomes": "ARID1A 缺失組 ORR: 14%; 臨床獲益率 (CBR) at 16w: 47%。"},

    {"cancer": "Ovarian", 
        "pos": ["P-TX", "R-TX"], 
        "sub_pos": ["Mucinous (MOC) 鑑定"], 
        "name": "📚 mEOC / GOG-0241", "pharma": "NRG Oncology / GOG", "drug": "Pac-Carbo vs Oxal-Cape ± Bev", 
        "pop_results": "罕見癌別標誌性研究：雖然因收案困難提前終止 (N=50)，但在確認為原發性 mEOC 的亞組中，GI 方案 (Oxal-Cape) 展現較佳的生存獲益趨勢。",
        "rationale": "第一個針對 mEOC 進行的多國隨機試驗，對比傳統婦癌化療 (Gyn-type) 與腸胃道癌化療 (GI-type) 方案，並探索 Bevacizumab 的角色。",
        "regimen": "1. Paclitaxel + Carboplatin ± Bevacizumab (15mg/kg) Q3W; 2. Oxaliplatin (130mg/m2) + Capecitabine (850mg/m2 bid D1-14) ± Bevacizumab。",
        "inclusion": ["新診斷 FIGO Stage II-IV 或 Stage I 復發之原發黏液性上皮性卵巢癌", "先前未接受過針對 R/M 之化療"],
        "outcomes": "原發性 mEOC 亞組 OS HR: 0.36 (p=0.14); PFS HR: 0.62 (p=0.40)。"},
    
    {"cancer": "Ovarian", 
        "pos": ["R-TX"], 
        "sub_pos": ["Mucinous (MOC) 鑑定"], 
        "name": "📍 mFOLFIRINOX + Bev (NCT05665023)", "pharma": "Yonsei University", "drug": "modified FOLFIRINOX + Bevacizumab", 
        "pop_results": "GI-style 方案前瞻探索：針對難治型 mEOC，利用高強度的三藥化療聯用標靶，旨在克服傳統化療的耐藥性。",
        "rationale": "考量 mEOC 的 GI 遺傳特性，此試驗將轉移性胰臟癌/大腸癌的標準方案 (FOLFIRINOX) 應用於卵巢癌，並透過 Bevacizumab 強化療效。",
        "regimen": "Bevacizumab (5mg/kg) + Oxaliplatin (85mg/m2) + Leucovorin (400mg/m2) + Irinotecan (150mg/m2) + 5-FU (2400mg/m2 46h) Q2W。",
        "inclusion": ["復發或轉移性卵巢黏液性腺癌", "先前接受過 2 線以下之全身性治療", "排除經內視鏡診斷為 GI 來源之腫瘤"],
        "outcomes": "試驗進行中 (Ongoing)，預計 2025 年 2 月完成主要指標收案。"},

    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PSOC (Sensitive Recur)"], 
        "name": "📚 Calypso Trial", "pharma": "ENGOT / GOG", "drug": "Carboplatin + PLD", 
        "pop_results": "鉑敏復發去毒標準：證實 Carbo/PLD 在 PFS 上優於傳統 Carbo/Pacli，且具備更佳的耐受性 (較少掉髮與神經毒性)。",
        "rationale": "旨在為鉑類敏感復發患者尋找一個與傳統方案療效相當、但毒性較低的化療組合。",
        "regimen": "Carboplatin (AUC 5) + Pegylated Liposomal Doxorubicin (30mg/m2) 每 4 週給藥一次，共 6 週期。",
        "inclusion": ["鉑類敏感復發 (PFI > 6m) 上皮性卵巢癌", "先前僅接受過一線含鉑輔助化療"],
        "outcomes": "mPFS: 11.3m (vs 9.4m, HR 0.82, P=0.005)。"},
    
    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PSOC (Sensitive Recur)"], 
        "name": "📚 OCEANS", "pharma": "Roche / GOG", "drug": "Chemo + Bevacizumab (PSOC)", 
        "pop_results": "鉑敏復發標靶標準：在化療基礎上加入 Bevacizumab 維持治療，顯著延長 PFS 達 4 個月 (HR 0.48)。",
        "rationale": "針對首次鉑類敏感復發患者，利用抗血管新生藥物強化含鉑複方化療 (Gem/Carbo) 的療效並延緩二次復發。",
        "regimen": "Bevacizumab (15mg/kg Q3W) 聯用 Gemcitabine/Carboplatin 6-10 週期，隨後單藥維持直至進展。",
        "inclusion": ["首次鉑類敏感復發 (PFI > 6m) 上皮性卵巢癌", "先前未接受過抗血管新生治療", "具備可測量病灶"],
        "exclusion": ["曾受過 VEGF 抑制劑治療", "有腸梗阻症狀或病史"],
        "outcomes": "mPFS: 12.4m (vs 8.4m, HR 0.484, P<0.0001)。"},
    
    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PSOC (Sensitive Recur)"], 
        "name": "📚 GOG-0213", "pharma": "Roche / GOG", "drug": "Chemo + Bevacizumab (OS Benefit)", 
        "pop_results": "鉑敏復發 OS 突破：證實加入 Bevacizumab 維持治療能為 PSOC 患者帶來顯著的生存获益 (mOS 延長約 5 個月)。",
        "rationale": "評估 Bevacizumab 聯用 Paclitaxel/Carboplatin 對於鉑敏復發患者的 Overall Survival (OS) 影響。",
        "regimen": "Bevacizumab (15mg/kg Q3W) 聯用 Pacli/Carbo，隨後單藥維持直至進展。",
        "inclusion": ["鉑類敏感復發上皮性卵巢癌", "ECOG 0-1", "適合再次接受鉑類化療"],
        "outcomes": "mOS: 42.6m (vs 37.3m, HR 0.829, P=0.0447)。"},
    
    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PSOC (Sensitive Recur)"], 
        "name": "📚 MITO16B / MaNGO OV2B / ENGOT-ov17", "pharma": "Roche / ENGOT", "drug": "Bevacizumab Beyond Bevacizumab", 
        "pop_results": "標靶跨線治療首選：證明一線用過 Bev 後，復發時『持續使用 Bev』仍具備顯著 PFS 獲益 (HR 0.51)。",
        "rationale": "挑戰抗血管新生治療的耐藥概念，驗證跨線維持 (Beyond PD) 是否能持續抑制腫瘤血管新生。",
        "regimen": "含鉑複方化療聯用 Bevacizumab (15mg/kg Q3W)，隨後單藥維持直至進展。",
        "inclusion": ["一線接受過標靶 (Bev) 治療之鉑敏復發患者", "ECOG 0-1"],
        "outcomes": "mPFS: 11.8m (vs 8.8m, HR 0.51, 95% CI 0.41-0.65)。"},
    
    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PROC (Resistant Recur)"], 
        "name": "📚 AURELIA", "pharma": "Roche", "drug": "Bev + non-Platinum Chemo (PROC)", 
        "pop_results": "鉑抗復發基石：首個證明 Bev 聯用單藥化療能使 PFS 翻倍 (6.7m vs 3.4m) 且改善生活品質。",
        "rationale": "針對預後極差的鉑類抗藥型患者，利用 Bev 協同傳統單藥化療克服化療耐藥性。",
        "regimen": "Bevacizumab (10mg/kg Q2W 或 15mg/kg Q3W) 聯用單藥化療 (Pacli/PLD/Topotecan)。",
        "inclusion": ["鉑類抗藥型 (PFI < 6m) 上皮性卵巢癌", "先前治療線數 ≤ 2 線", "無腸道受累風險"],
        "exclusion": ["先前一線即進展者", "活動性腸道疾病"],
        "outcomes": "mPFS: 6.7m (vs 3.4m, HR 0.48, P<0.001)。"},
    
    {"cancer": "Ovarian", 
    "pos": "P-MT", 
    "sub_pos": ["HRD positive (wt)", "HRD negative (pHRD)"], 
    "name": "📚 DUO-O (ENGOT-OV46)", 
    "pharma": "AstraZeneca", 
    "drug": "Durvalumab + Olaparib + Bev",
    "pop_results": "一線合併免疫/抗血管/（部分族群加PARPi）帶來PFS改善；發表資料顯示「Durvalumab＋Bev」組合對比對照PFS HR 0.49，加入Olaparib後PFS HR 0.61，凸顯多機轉一線策略的方向，HRD+ 三藥組 PFS HR 0.49; ITT HR 0.63",
    "rationale": "利用 IO + PARPi + anti-VEGF 三藥聯用，於一線反應後清除微小殘留病灶並延緩復發。",
    "regimen": "backbone：carboplatin/paclitaxel + bevacizumab; 隨機加入 durvalumab（與化療併用）並在維持期合併 durvalumab + bev ± olaparib; Arm 3: Bevacizumab + Durvalumab + Olaparib (300mg bid) 維持直至疾病進展。",
    "inclusion": ["新診斷 FIGO III-IV 期上皮性卵巢癌。", "接受 PDS 或 IDS 且對鉑類有反應。", "特別針對 non–tumor BRCA-mut（non-tBRCAm）、並以 HRD/ITT 做主要分析。"],
    "exclusion": ["不適合 bev。", "既往免疫治療 / PARP。"],
    "outcomes": "在 HRD+ 與 ITT（non-tBRCAm） 族群，含 durvalumab+olaparib 的策略達成 PFS 主要終點；OS 仍需更長追蹤，HRD+ (non-BRCAm) PFS HR 0.49 (95% CI 0.34-0.69); ITT ITT HR 0.63。"},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutation"], 
        "name": "📚 SOLO-1", "pharma": "AZ", "drug": "Olaparib", 
        "pop_results": "BRCAm 一線維持金標準：7 年存活率達 67% (HR 0.33)。",
        "rationale": "針對一線含鉑化療反應良好之 BRCA 突變患者，利用 PARPi 達成『合成致死』效果以延緩復發。",
        "regimen": "Arm A：olaparib 300 mg BID maintenance（通常至 2 年或進展）。Arm B：placebo maintenance。",
        "inclusion": ["newly diagnosed advanced ovarian cancer。", "germline 或 somatic BRCA1/2 mutation。", "一線 platinum 化療後 CR/PR。"],
        "exclusion": ["先前接受過 PARP 抑制劑。", "持續性骨髓抑制未恢復。"],
        "outcomes": "mPFS: 56.0m vs 13.8m (HR 0.30)。AE：貧血、噁心、疲倦常見；需監測血球。"},
    
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive / BRCA wt", "HRD negative (pHRD)"], 
        "name": "📚 PRIMA", "pharma": "GSK", "drug": "Niraparib", 
        "pop_results": "不限 BRCA 狀態的全人群一線維持：HRD+ PFS HR 0.43；全體 ITT HR 0.62，確立「不需限縮到BRCA」的一線維持策略。",
        "rationale": "不論 HRD 狀態，透過 PARPi 強化一線化療後的維持獲益，特別是針對高風險族群。",
        "regimen": "Arm A：niraparib maintenance（起始劑量可依體重/血小板調整；至 36 個月或進展）。Arm B：placebo maintenance。",
        "inclusion": ["newly diagnosed stage III/IV、高復發風險。", "一線 platinum 化療後 CR/PR。"],
        "exclusion": ["MDS/AML 風險評估等。", "先前接受過 PARP 抑制劑。", "持續性骨髓抑制未恢復。"],
        "outcomes": "HRD+ PFS HR 0.43 (95% CI 0.31-0.59)。overall PFS HR 0.62。AE：Grade ≥3 常見 血小板下降、貧血、中性球低下。"},
    
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive / BRCA wt"], 
        "name": "📚 PAOLA-1", "pharma": "AZ", "drug": "Olaparib + Bevacizumab", 
        "pop_results": "Olaparib＋Bevacizumab維持在全體改善PFS（HR 0.59），在HRD陽性族群效益更大（HR 0.33），奠定「HRD導向」合併維持的標準，HRD+ 黃金組合維持：5 年 OS 率達 75.2%。",
        "rationale": "結合 anti-VEGF（Bev）重塑血管環境與 PARPi（Ola）抑制 DNA 修復之雙重機轉。",
        "regimen": "所有患者先接受含 bevacizumab 的一線化療; Arm A：olaparib + bevacizumab maintenance。Arm B：bevacizumab maintenance（對照）。",
        "inclusion": ["newly diagnosed stage III/IV、高復發風險。", "化療 + bev 後 CR/PR。", "並分層 HRD/BRCA。"],
        "exclusion": ["不適合 bev（出血/廔管/血栓風險）。", "先前接受過 PARP 抑制劑。", "持續性骨髓抑制未恢復。"],
        "outcomes": "PFS 顯著改善（尤其 HRD+）。HRD+ 5yr OS: 75.2% vs 58.3% (HR 0.62)具臨床意義的 OS 改善。AE：PARP（貧血）+ bev（高血壓/蛋白尿）毒性需並行管理。"},
    
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutation", "HRD positive / BRCA wt"], 
        "name": "📚 ATHENA–MONO", "pharma": "Clovis", "drug": "Rucaparib", 
        "pop_results": "Rucaparib一線維持改善PFS（ITT：HR 0.52；HRD：HR 0.47；HRD-negative亦有訊號：HR 0.65），擴充了一線PARPi維持的證據版圖。",
        "rationale": "證實 Rucaparib 在一線含鉑化療反應後的單藥維持價值，不論其 HRD 狀態。",
        "regimen": "Arm A：rucaparib maintenance。Arm B：placebo maintenance（對照）。",
        "inclusion": ["newly diagnosed advanced（多為 III/IV）。", "一線 platinum 後 CR/PR。", "涵蓋 HRD/HRP。"],
        "exclusion": ["肝功能異常。", "先前接受過 PARP 抑制劑。", "持續性骨髓抑制未恢復。"],
        "outcomes": "主要終點為 PFS，在 HRD 與 ITT 均呈現顯著獲益: ITT PFS: 28.7m vs 11.3m (HR 0.52)。AE：貧血、肝酵素上升等 PARP 典型毒性。"},
    
    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["PARPi Maint"], 
        "name": "📚 NOVA", "pharma": "GSK", "drug": "Niraparib", 
        "pop_results": "復發、鉑敏感情境下Niraparib維持顯著延長PFS（gBRCA：HR 0.27；non-gBRCA：HR 0.45），是「復發維持PARPi」的經典試驗",
        "rationale": "首個證明 PARPi 在鉑類敏感復發（PSOC）患者中，不論 BRCA 是否突變皆有獲益的研究。",
        "regimen": "Arm A：niraparib maintenance。Arm B：placebo maintenance（對照）。",
        "inclusion": ["platinum-sensitive recurrent ovarian cancer。", "對最近一次 platinum 有反應。", "分 gBRCA 與 non-gBRCA cohort。"],
        "exclusion": ["MDS/AML 風險。", "先前接受過 PARP 抑制劑。", "持續性骨髓抑制未恢復。"],
        "outcomes": "gBRCAm mPFS: 21.0m vs 5.5m (HR 0.27)。non-gBRCA HR 0.45。AE：血小板下降/貧血/中性球低下常見。"},
    
    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["PARPi Maint"], 
        "name": "📚 ARIEL3", "pharma": "Clovis", "drug": "Rucaparib", 
        "pop_results": "Rucaparib維持改善PFS（意向治療全體：HR 0.36；BRCA突變：HR 0.23），支持以分層族群方式使用PARPi，精確分流維持獲益：BRCAm PFS HR 0.23；HRD+ HR 0.32。",
        "rationale": "利用 LOH（雜合性丟失）檢測輔助判定 HRD 狀態，導航 PARPi 在復發階段的使用。",
        "regimen": "Arm A：rucaparib maintenance。Arm B：placebo maintenance（對照）。",
        "inclusion": ["platinum-sensitive recurrent ovarian cancer。", "對 platinum 有反應。", "分層 BRCA-mut / HRD / ITT。"],
        "exclusion": ["重大共病。", "先前接受過 PARP 抑制劑。", "持續性骨髓抑制未恢復。"],
        "outcomes": "BRCAm mPFS 16.6m vs 5.4m (HR 0.23)；HRD HR ~0.32；ITT HR ~0.36。AE：貧血、肝酵素上升等。"},
    
    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["PARPi Maint"], 
        "name": "📚 SOLO2", "pharma": "AZ", "drug": "Olaparib", 
        "pop_results": "Olaparib維持可延長PFS（HR 0.30），但最終OS優勢不明顯（OS HR 0.74、未達顯著），是解讀「交叉治療/後線PARPi使用」影響OS的代表案例，復發維持生存突破：BRCAm 族群 mOS 顯著延長至 51.7m (HR 0.74)。",
        "rationale": "確認 Olaparib 在復發維持階段能將 PFS 獲益轉化為最終 OS 獲益。",
        "regimen": "Arm A：olaparib tablets maintenance。Arm B：placebo maintenance（對照）。",
        "inclusion": ["platinum-sensitive recurrent ovarian cancer。", "對 platinum 有反應。", "BRCA1/2 mutation。"],
        "exclusion": ["重大共病。", "先前接受過 PARP 抑制劑。", "持續性骨髓抑制未恢復。"],
        "outcomes": "mOS: 51.7m vs 38.8m (HR 0.74)。PFS 顯著改善，HR 約 0.30，最終 OS 分析顯示 median OS +12.9 months。AE：貧血、噁心、疲倦。 "},

    # ==========================
    # === Uterine Sarcoma Published ===
    # ==========================

    {"cancer": "Uterine Sarcoma", 
        "pos": ["P-TX"], 
        "sub_pos": ["Primary Sarcoma"], 
        "name": "📚 GOG-0277", "pharma": "GOG / NCI", "drug": "Gem/Doce vs Observation", 
        "pop_results": "高惡性度 LMS 輔助治療：Gemcitabine + Docetaxel 輔助化療相較於觀察組，雖有 PFS 獲益趨勢但未達顯著差異。",
        "rationale": "針對完全切除的高惡性度子宮平滑肌肉瘤 (uLMS)，探討輔助化療是否能降低極高的復發率。",
        "regimen": "Gemcitabine (900mg/m2 D1, D8) + Docetaxel (75mg/m2 D8) 每 21 天一週期，共 4 週期。",
        "inclusion": ["完全切除之 Stage I 子宮平滑肌肉瘤 (uLMS)", "ECOG 0-1"],
        "outcomes": "由於收案困難提前終止，未達顯著統計學差異。"},
    
    {"cancer": "Uterine Sarcoma", 
        "pos": ["P-TX"], 
        "sub_pos": ["Primary Sarcoma"], 
        "name": "📚 EORTC 55874", "pharma": "EORTC", "drug": "Adjuvant Radiotherapy", 
        "pop_results": "術後放療價值：對於早期子宮肉瘤，輔助性骨盆放療能降低局部復發率，但無法改善 PFS 與 OS。",
        "rationale": "探討 Stage I/II 子宮肉瘤患者術後接受骨盆體外放射治療 (EBRT) 的臨床獲益。",
        "regimen": "骨盆腔體外放射治療 (EBRT)，總劑量 50.4 Gy 分 28 次照射。",
        "inclusion": ["Stage I/II 子宮平滑肌肉瘤 (LMS) 或子宮肉瘤 (uS)", "手術完全切除後"],
        "outcomes": "局部復發率降低；OS HR 0.94 (P=0.69) 無顯著差異。"},
    
    {"cancer": "Uterine Sarcoma", 
        "pos": ["P-TX"], 
        "sub_pos": ["Primary Sarcoma"], 
        "name": "📚 EORTC 62012", "pharma": "EORTC", "drug": "Doxorubicin + Ifosfamide", 
        "pop_results": "晚期一線組合：聯用方案顯著提升 ORR (26%) 與 PFS，但在總生存期 (OS) 上與單藥 Dox 相比無顯著差異。",
        "rationale": "針對不可切除或轉移性肉瘤，比較『加強型聯用化療』與『單藥化療』的療效權衡。",
        "regimen": "Doxorubicin (75mg/m2) 聯用 Ifosfamide (5g/m2 + Mesna) Q3W。",
        "inclusion": ["晚期/轉移性軟組織肉瘤 (含子宮肉瘤)", "先前未接受過系統化療"],
        "outcomes": "mPFS: 7.4m vs 4.6m (HR 0.74); ORR: 26% vs 14%。"},
    
    {"cancer": "Uterine Sarcoma", 
        "pos": ["P-TX"], 
        "sub_pos": ["Primary Sarcoma"], 
        "name": "📚 GeDDiS (Phase III)", "pharma": "CRUK", "drug": "Gem/Doce vs Doxorubicin", 
        "pop_results": "一線標準對照：Gem/Doce 與 Doxorubicin 作為一線治療，在 PFS 上無顯著差異，Dox 具備更佳的用藥便利性。",
        "rationale": "旨在確定 Gem/Doce 是否能取代 Doxorubicin 成為晚期肉瘤的一線首選標準。",
        "regimen": "Gemcitabine (675mg/m2 D1, D8) + Docetaxel (75mg/m2 D8) vs Doxorubicin (75mg/m2 D1) Q3W。",
        "inclusion": ["不可切除或轉移性軟組織肉瘤", "ECOG 0-1"],
        "outcomes": "mPFS: 23.3 週 (Gem/Doce) vs 23.3 週 (Dox)，HR 1.14 (P=0.06)。"},
    
    {"cancer": "Uterine Sarcoma", 
        "pos": ["P-TX"], 
        "sub_pos": ["Primary Sarcoma"], 
        "name": "📚 LMS-04 (Phase III)", "pharma": "French Sarcoma Group", "drug": "Doxorubicin + Trabectedin", 
        "pop_results": "LMS 一線新高度：聯用 Trabectedin 顯著延長子宮平滑肌肉瘤中位 PFS 達兩倍 (12.2m vs 6.2m)。",
        "rationale": "專對平滑肌肉瘤 (LMS)，利用 Doxorubicin 聯用 Trabectedin 挑戰傳統單藥治療瓶頸。",
        "regimen": "Doxorubicin (60mg/m2) + Trabectedin (1.1mg/m2) Q3W，接續 Trabectedin 單藥維持。",
        "inclusion": ["晚期/轉移性子宮或非子宮平滑肌肉瘤 (LMS)", "一線治療"],
        "outcomes": "mPFS: 12.2m vs 6.2m (HR 0.37); mOS: 31.6m vs 24.1m。"},

    {"cancer": "Uterine Sarcoma", 
        "pos": ["P-TX", "R-TX"], 
        "sub_pos": ["Carcinosarcoma"], 
        "name": "📚 NRG/GOG-0261 (Phase III)", "pharma": "NRG Oncology", "drug": "Pacli/Carbo vs Pacli/Ifo", 
        "pop_results": "子宮癌肉瘤 (UCS) 的新標準：Paclitaxel + Carboplatin 在 PFS 上不劣於且略優於 Pacli/Ifo，且毒性顯著降低。",
        "rationale": "旨在確定 Pacli/Carbo (PC) 是否能取代毒性較大的 Ifosfamide 基礎方案，成為癌肉瘤一線治療的新標竿。",
        "regimen": "Arm A: Paclitaxel 175mg/m2 + Carboplatin (AUC 6) Q3W; Arm B: Paclitaxel 135mg/m2 + Ifosfamide 1.6g/m2 (D1-3) Q3W。",
        "inclusion": ["新診斷 Stage III-IV 或復發性子宮/卵巢癌肉瘤 (Carcinosarcoma)", "ECOG 0-2"],
        "outcomes": "PFS: 14.6m (PC) vs 10.3m (PI); OS: 37m vs 29m (非劣效性達成且具統計趨勢優勢)。"},
    
    {"cancer": "Uterine Sarcoma", 
        "pos": ["R-TX"], 
        "sub_pos": ["Carcinosarcoma"], 
        "name": "📚 GOG-161 (Phase III)", "pharma": "GOG / NCI", "drug": "Ifosfamide + Paclitaxel", 
        "pop_results": "雙藥聯用獲益：在癌肉瘤治療中，Ifosfamide 聯用 Paclitaxel 比單用 Ifosfamide 顯著延長 PFS (5.8m vs 3.6m) 與 OS。",
        "rationale": "早期試驗，驗證在 Ifosfamide 基礎上加入紫杉醇類藥物是否能克服 UCS 的化療抗藥性。",
        "regimen": "試驗組: Ifosfamide 1.6 g/m2 (D1-3) + Paclitaxel 135 mg/m2 (D1) Q3W; 對照組: Ifosfamide 單藥 2.0 g/m2 (D1-3)。",
        "inclusion": ["不可切除、持久性或復發性子宮癌肉瘤", "先前未接受過針對晚期疾病之化療"],
        "outcomes": "mPFS: 5.8m vs 3.6m (HR 0.71); mOS: 13.5m vs 8.4m。"},
    
    {"cancer": "Uterine Sarcoma", 
        "pos": ["R-TX"], 
        "sub_pos": ["Carcinosarcoma"], 
        "name": "📚 GOG-108 (Phase III)", "pharma": "GOG", "drug": "Ifosfamide vs Cisplatin", 
        "pop_results": "早期單藥對比：針對晚期子宮肉瘤，Ifosfamide 展現出較高的緩解率與較佳的生存獲益趨勢。",
        "rationale": "在 1990 年代初期，旨在確定哪種含鉑或烷化劑類藥物最適合處理惡性程度極高的子宮癌肉瘤。",
        "regimen": "Ifosfamide 1.5 g/m2 (D1-5) 每 21 天一週期; 或 Cisplatin 50 mg/m2 每 21 天一週期。",
        "inclusion": ["晚期或復發性子宮肉瘤 (以癌肉瘤為主)", "ECOG 0-2"],
        "outcomes": "Ifosfamide 組緩解率 (ORR) 顯著優於 Cisplatin 組。"},
    
    {"cancer": "Uterine Sarcoma", 
        "pos": ["P-TX"], 
        "sub_pos": ["Carcinosarcoma"], 
        "name": "📚 GOG-150 (Phase III)", "pharma": "GOG / NCI", "drug": "Adjuvant AP Chemo vs WAI", 
        "pop_results": "術後輔助策略：比較全腹部放射治療 (WAI) 與化療 (AP)，雖然 OS 無顯著差異，但化療對於 Stage I-II 癌肉瘤的系統控制力更佳。",
        "rationale": "探討 Stage I-II 癌肉瘤完全切除後，局部放療與全身化療哪種能更有效降低高復發率。",
        "regimen": "化療組: Doxorubicin 60mg/m2 + Cisplatin 50mg/m2 (AP) Q3W x8; 放療組: WAI 30 Gy 分 20 次照射。",
        "inclusion": ["完全切除之 Stage I 或 II 子宮癌肉瘤", "手術探查證實無腹膜內轉移"],
        "outcomes": "兩組間 OS 無顯著統計學差異，但 AP 化療組之復發風險比率 (HR) 呈下降趨勢。"},

    {"cancer": "Uterine Sarcoma", 
        "pos": ["R-TX"], 
        "sub_pos": ["Recurr / Metastatic"], 
        "name": "📚 ET743-SAR-3007", "pharma": "Janssen", "drug": "Trabectedin vs Dacarbazine", 
        "pop_results": "LMS 救援二線標準：Trabectedin 相比 Dacarbazine 可顯著降低 45% 的疾病進展風險 (HR 0.55)。",
        "rationale": "針對先前接受過含 Anthracycline 化療失敗的晚期平滑肌肉瘤 (LMS)，驗證 Trabectedin 的療效。",
        "regimen": "Trabectedin 1.5 mg/m2 (24小時持續靜脈滴注) Q3W；對照組 Dacarbazine 1000 mg/m2 Q3W。",
        "inclusion": ["不可切除或轉移性平滑肌肉瘤 (LMS) 或脂肪肉瘤", "先前接受過含 Anthracycline 方案治療"],
        "outcomes": "LMS 族群 mPFS: 4.2m vs 1.5m (HR 0.55, P<0.001)；ITT OS 無顯著差異。"},
    
    {"cancer": "Uterine Sarcoma", 
        "pos": ["R-TX"], 
        "sub_pos": ["Recurr / Metastatic"], 
        "name": "📚 PALETTE", "pharma": "Novartis / GSK", "drug": "Pazopanib (TKI)", 
        "pop_results": "非脂肪肉瘤二線標準：Pazopanib 顯著延長中位 PFS 達三倍 (4.6m vs 1.6m, HR 0.31)。",
        "rationale": "利用多靶點 TKI 抑制 VEGF、PDGFR 與 c-Kit 通路，阻斷肉瘤的血管新生與生長訊號。",
        "regimen": "Pazopanib 800 mg 每日口服一次，持續治療直到疾病進展或不可耐受。",
        "inclusion": ["先前化療失敗之晚期非脂肪肉瘤性軟組織肉瘤 (含子宮 LMS)", "ECOG 0-1"],
        "outcomes": "mPFS: 4.6m vs 1.6m (HR 0.31, P<0.0001)；OS 呈現獲益趨勢但未達統計顯著。"},
    
    {"cancer": "Uterine Sarcoma", 
        "pos": ["R-TX"], 
        "sub_pos": ["Recurr / Metastatic"], 
        "name": "📚 REGOSARC", "pharma": "Bayer", "drug": "Regorafenib (TKI)", 
        "pop_results": "二線 TKI 新數據：在 LMS 族群中，Regorafenib 顯著延長 PFS (HR 0.46)，具備臨床救援價值。",
        "rationale": "隨機、雙盲、安慰劑對照之第 II 期試驗，驗證 Regorafenib 在各類肉瘤分型中的活性。",
        "regimen": "Regorafenib 160 mg QD (服用 3 週休息 1 週)，每 28 天為一週期。",
        "inclusion": ["先前接受過含 Anthracycline 或多線治療失敗之晚期肉瘤", "包含子宮平滑肌肉瘤 (uLMS) 隊列"],
        "outcomes": "LMS 隊列 PFS: 4.4m vs 1.4m (HR 0.46, P=0.0045)。"},
    
    {"cancer": "Uterine Sarcoma", 
        "pos": ["R-TX"], 
        "sub_pos": ["Recurr / Metastatic"], 
        "name": "📚 Eribulin vs Dacarbazine", "pharma": "Eisai", "drug": "Eribulin", 
        "pop_results": "LMS/LPS 存活獲益：針對平滑肌肉瘤與脂肪肉瘤，Eribulin 顯著延長中位 OS (13.5m vs 11.5m)。",
        "rationale": "非微管蛋白解聚類藥物，旨在探索其在難治型肉瘤中對於總體生存率 (OS) 的貢獻。",
        "regimen": "Eribulin 1.4 mg/m2 (D1, D8) 每 21 天為一週期。",
        "inclusion": ["先前接受過至少 2 線治療 (須含 Anthracycline) 失敗之晚期 LMS 或 LPS", "ECOG 0-1"],
        "outcomes": "mOS: 13.5m vs 11.5m (HR 0.77, P=0.016)；LMS 族群數據穩定。"},

    {"cancer": "Uterine Sarcoma", 
        "pos": ["R-TX"], 
        "sub_pos": ["Low grade ESS"], 
        "name": "📚 PARAGON (ANZGOG 0903)", "pharma": "ANZGOG", "drug": "Anastrozole", 
        "pop_results": "LG-ESS 激素治療里程碑：針對 ER/PR 陽性患者，3 個月的臨床獲益率 (CBR) 高達 73.3%，且中位 PFS 尚未達到。",
        "rationale": "利用芳香環轉化酶抑制劑 (AI) 阻斷雌激素生成，針對具高度激素依賴性的 LG-ESS 提供去化療的長期控制選擇。",
        "regimen": "Anastrozole 1 mg 每日口服一次，持續治療直到疾病進展。",
        "inclusion": ["復發性或轉移性 ER/PR(+) 子宮內膜間質肉瘤 (LGESS)", "ECOG 0-2", "需具備可測量病灶"],
        "outcomes": "CBR at 3m: 73.3%; ORR: 26.7%; 25% 族群 PFS 超過 44 個月。"},

        {"cancer": "Uterine Sarcoma", 
        "pos": ["P-TX"], 
        "sub_pos": ["Low grade ESS"], 
        "name": "📚 PARAGON (ANZGOG 0903)", "pharma": "ANZGOG", "drug": "Anastrozole", 
        "pop_results": "LG-ESS 激素治療里程碑：針對 ER/PR 陽性患者，3 個月的臨床獲益率 (CBR) 高達 73.3%，且中位 PFS 尚未達到。",
        "rationale": "利用芳香環轉化酶抑制劑 (AI) 阻斷雌激素生成，針對具高度激素依賴性的 LG-ESS 提供去化療的長期控制選擇。",
        "regimen": "Anastrozole 1 mg 每日口服一次，持續治療直到疾病進展。",
        "inclusion": ["復發性或轉移性 ER/PR(+) 子宮內膜間質肉瘤 (LGESS)", "ECOG 0-2", "需具備可測量病灶"],
        "outcomes": "CBR at 3m: 73.3%; ORR: 26.7%; 25% 族群 PFS 超過 44 個月。"},
    
    {"cancer": "Uterine Sarcoma", 
        "pos": ["R-TX"], 
        "sub_pos": ["Primary Sarcoma", "Recurr / Metastatic"], 
        "name": "📚 NTRK Basket Trials", "pharma": "Bayer / Roche", "drug": "Larotrectinib / Entrectinib", 
        "pop_results": "跨癌別精準醫療：針對帶有 NTRK 基因融合的肉瘤，Larotrectinib 的客觀緩解率 (ORR) 高達 75%。",
        "rationale": "NTRK 融合雖在子宮肉瘤中罕見，但屬於高度致癌驅動因子，使用 TRK 抑制劑可達成極高且持久的臨床反應。",
        "regimen": "Larotrectinib 100 mg 每日兩次口服；或 Entrectinib 600 mg 每日一次口服。",
        "inclusion": ["經 NGS 證實具備 NTRK1/2/3 基因融合之晚期固體腫瘤", "無現有標準治療或治療失敗"],
        "outcomes": "ITT ORR: ~75%; 中位 PFS 顯著優於傳統化療。"},
    
    {"cancer": "Uterine Sarcoma", 
        "pos": ["R-TX"], 
        "sub_pos": ["Primary Sarcoma", "Recurr / Metastatic"], 
        "name": "📚 Olaparib + Temozolomide (NCT03880019)", "pharma": "NCI / Columbia", "drug": "Olaparib + TMZ", 
        "pop_results": "uLMS 二線新組合：針對經治的晚期子宮平滑肌肉瘤，ORR 達 27%，中位 PFS 為 6.9 個月。",
        "rationale": "利用 TMZ 誘導 DNA 損傷，併用 PARP 抑制劑 (Olaparib) 阻斷修復路徑，針對 uLMS 產生合成致死效應。",
        "regimen": "Temozolomide 75mg/m2 QD (D1-7) + Olaparib 300mg bid (D1-21)，每 21 天為一週期。",
        "inclusion": ["組織學證實之晚期子宮平滑肌肉瘤 (uLMS)", "先前至少接受過一線系統治療後進展"],
        "outcomes": "ORR: 27%; mPFS: 6.9m; 臨床獲益率 (CBR): 68%。"},
    
    {"cancer": "Uterine Sarcoma", 
        "pos": ["P-TX", "R-TX"], 
        "sub_pos": ["Low grade ESS"], 
        "name": "📍 Letrozole (NCT05649956)", "pharma": "Investigator-Initiated", "drug": "Letrozole", 
        "pop_results": "LG-ESS 長期維持新實證：評估 Letrozole 在早期術後輔助或晚期維持中的長期療效與安全性。",
        "rationale": "針對高度表達 ER/PR 的間質肉瘤，Letrozole 作為一線或二線內分泌治療已顯示出極佳的緩解率與低毒性。",
        "regimen": "Letrozole 2.5 mg 每日口服一次，長期服用直至疾病進展。",
        "inclusion": ["新診斷或復發性低惡性度子宮內膜間質肉瘤 (LGESS)", "ER/PR 陽性"],
        "outcomes": "部分個案顯示可達 7 年以上之穩定緩解 (Stable Disease)。"},
    
    {"cancer": "Uterine Sarcoma", 
        "pos": ["P-TX"], 
        "sub_pos": ["Primary Sarcoma"], 
        "name": "📍 NCT07076186 (Adjuvant Doxo + Trab)", "pharma": "Decentralized Pragmatic Trial", "drug": "Doxorubicin + Trabectedin", 
        "pop_results": "早期輔助強化研究：探索 Stage Ib/2 uLMS 術後使用 Doxo+Trab 是否能顯著延長無病生存期。",
        "rationale": "基於 LMS-04 試驗在晚期一線的成功，將 Doxo 聯用 Trabectedin 提前至輔助治療階段以降低高復發風險。",
        "regimen": "Doxorubicin (60mg/m2) + Trabectedin (1.1mg/m2) 每 21 天一次，隨後進行 Trabectedin 維持治療。",
        "inclusion": ["Stage Ib 或 II 期子宮平滑肌肉瘤 (uLMS)", "手術完全切除 (R0) 後 3 個月內"],
        "outcomes": "試驗進行中 (Ongoing)，預計 2025 年底開始正式收案。"},

    # ==========================
    # === Ongoing Trials (8核心極量化) ===
    # ==========================
    {"cancer": "Endometrial", "name": "📍 MK2870-033/TroFuse-033/GOG-3119/ENGOT-en29", "pharma": "MSD", "drug": "Sac-TMT + Pembrolizumab", "pos": "P-MT", "sub_pos": ["Maintenance Therapy"], "type": "Ongoing",
     "pop_results": "用 TROP2-ADC增加腫瘤細胞殺傷並與 PD-1 抑制併用，目標是補足「pMMR 子宮內膜癌對免疫單藥反應較差、需要更強的一線/維持策略」的缺口。",
     "rationale": "標靶 Trop-2 ADC (Sac-TMT) 協同 PD-1。透過 ADC 誘導之 ICD 改善微環境，旨在提升 pMMR 或 NSMP 患者一線維持階段應答深度與持續時間。",
     "regimen": "Arm A (分組 1): Sac-TMT 5mg/kg Q6W + Pembrolizumab 400mg Q6W 維持治療直到 PD。 Arm B (分組 2): 醫師選擇維持方案 (對照組)。",
     "inclusion": ["新診斷 pMMR/MSS 子宮內膜癌 (中心 IHC 檢測確認)。", "FIGO III-IV 期、一線含鉑化療 + Pembrolizumab 後達 CR/PR。"],
     "exclusion": ["先前接受過針對復發病灶之系統 IO 治療。", "組織學為子宮肉瘤 (Sarcoma)。"],
     "outcomes": "進行中 (Ongoing)；早期數據顯示 sac-TMT 於經治 EC 患者之 ORR 達 34.1%、mPFS 為 5.7 個月。"},

    {"cancer": "Endometrial", 
        "pos": ["R-TX"], 
        "sub_pos": ["Recurrent EC"], "type": "Ongoing",
        "name": "📍 BLUESTAR (NCT05123482)", "pharma": "AstraZeneca", "drug": "Puxitatug samrotecan (AZD8205)", 
        "pop_results": "B7-H4 ADC 突破訊號：在晚期/轉移性子宮內膜癌擴展隊列中，ORR 達 34.6-38.5%，中位 PFS 達 7.0 個月。",
        "rationale": "利用 B7-H4 (於婦癌高度表現之免疫調控分子) 作為導引，搭載 DAR 8 的 TOP1i 載荷，透過旁觀者效應克服腫瘤異質性。",
        "regimen": "AZD8205 1.6 - 2.4 mg/kg IV Q3W；單藥或聯用 Rilvegostomig (PD-1/TIGIT) 或 Saruparib (PARPi)。",
        "inclusion": ["晚期/轉移性子宮內膜癌 (或 HR+/HER2- 乳癌)，先前標準治療進展者",
            "B7-H4 IHC 陽性 (定義為 >25% 腫瘤細胞表現)",
            "ECOG 0-1"],
        "exclusion": ["先前接受過 TOP1 抑制劑 (如其他 TOP1i-ADC) 治療者",
            "具有 ILD/肺炎病史需類固醇治療者"],
        "outcomes": "EC 擴展隊列 ORR: 34.6% (2.0mg/kg) / 38.5% (2.4mg/kg); mPFS: 7.0m；常見 ≥G3 AE 為貧血與嗜中性球低下。"},

    {"cancer": "Ovarian", "name": "📍 FRAmework-01 (LY4170156)", "pharma": "Eli Lilly", "drug": "LY4170156 + Bevacizumab", "pos": "R-TX", "sub_pos": ["PROC (Resistant Recur)", "PSOC (Sensitive Recur)"], "type": "Ongoing",
     "pop_results": "以 FRα 標的 ADC（把細胞毒載荷精準送入腫瘤）攻克鉑抗藥卵巢癌，並嘗試擴大到更多 FRα 表現範圍/或搭配 bev，目的在彌補「鉑抗藥期有效且可耐受的系統治療仍不足、FRα-ADC 受惠族群仍有限」的缺口。",
     "rationale": "標靶 FRα ADC 聯用 anti-VEGF。利用 Bevacizumab 血管調節作用降低腫瘤間質壓，提升 ADC 於實體腫瘤內的滲透深度挑戰耐藥瓶頸。",
     "regimen": "PROC 隊列分組： Arm A: LY 3.0mg/kg + Bev 15mg/kg Q3W; Arm B: LY 4.0mg/kg + Bev 15mg/kg Q3W。 PSOC 隊列 (PFI 6-12m): Arm C: LY 3.0mg/kg + Bev 15mg/kg Q3W。 對照組 (Arm D): 醫師選擇化療 SoC。",
     "inclusion": ["經檢測確認 FRα 表達陽性 (IHC)。", "最後鉑類後進展之 PROC 或 PSOC (PFI 90d-365d)。"],
     "exclusion": ["曾用過針對 FRα 之 ADC (如 Enhertu 曾試過者需評估)。", "活動性間質性肺病 (ILD)。"]},

    {"cancer": "Endometrial", "name": "📍 ASCENT-GYN-01/GS-US-682-6769", "pharma": "Gilead", "drug": "SG (Trodelvy)", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "type": "Ongoing",
     "pop_results": "針對「鉑類化療+PD-(L)1 後仍進展、預後差且後線缺乏有效方案」的族群，評估 **TROP2-ADC（sacituzumab govitecan，載荷 SN-38）**能否在 PFS/OS 超越傳統單藥化療，填補後線治療空窗。",
     "rationale": "針對 Trop-2 標靶。利用 SN-38 載荷引發強力 DNA 損傷，專攻鉑類與免疫檢查點抑制劑 (ICI) 失敗後之復發救援。",
     "regimen": "Sacituzumab govitecan 10mg/kg (Day 1, Day 8) 每 21 天為一週期 (Q21D) 直至疾病進展。",
     "inclusion": ["復發性 EC (不含肉瘤)。", "先前曾接受過至少一次含鉑化療及 PD-1/L1 失敗進展者。", "ECOG 0-1。"],
     "exclusion": ["先前接受過 TROP2 ADC 治療者",
            "活動性腦轉移或嚴重間質性肺病 (ILD) 史"],
     "outcomes": "進行中 (Ongoing)；參考 TROPiCS-03 研究，SG 在 EC 隊列展現出可觀的抗腫瘤活性與可管理的安全性。"},
    
    {"cancer": "Cervical", 
        "pos": ["P-MT"], 
        "sub_pos": ["Maintenance"], "type": "Ongoing",
        "name": "📍 eVOLVE-Cervical (NCT06079671)", "pharma": "AstraZeneca", "drug": "Volrustomig (PD-1/CTLA-4)", 
        "pop_results": "LACC 輔助強化探索：針對局部晚期高風險患者，於 CCRT 完結且未進展後，評估雙特異性抗體維持治療之價值。",
        "rationale": "利用 PD-1/CTLA-4 雙重阻斷 (Volrustomig) 作為序列免疫治療，旨在於化放療後之免疫原性空窗期進一步降低復發風險。",
        "regimen": "Arm A: Volrustomig (IV) 維持治療; Arm B: Placebo (IV) 維持治療。(對象為 CCRT 後達 CR/PR/SD 之患者)。",
        "inclusion": ["FIGO 2018 IIIA–IVA 高風險局部晚期子宮頸癌 (鱗/腺/腺鱗癌)",
            "完成 Platinum-based CCRT 後未進展者",
            "需提供樣本評估 PD-L1 狀態"],
        "exclusion": ["CCRT 治療期間已發生疾病進展",
            "活動性自體免疫疾病或不可控制之感染"],
        "outcomes": "進行中 (Ongoing)；主要終點為 PFS 與 OS，需嚴格監測 PD-1/CTLA-4 雙阻斷之 irAEs 發生率。"},

    {"cancer": "Ovarian", "name": "📍 DOVE", "pharma": "GSK", "drug": "Dostarlimab + Bevacizumab", "pos": "R-TX", "sub_pos": ["Clear Cell Carcinoma"], "type": "Ongoing",
     "pop_results": "用 **PD-1 抑制（dostarlimab）**單用或合併 抗血管新生（bevacizumab），想把「對化療特別不敏感、復發後選擇很少」的透明細胞癌，從傳統化療導向轉成免疫/免疫合併抗血管新生的新策略。",
     "rationale": "針對 OCCC 透明細胞癌。利用 PD-1 + anti-VEGF 雙重阻斷改善其特有且高度免疫抑制之微環境。",
     "regimen": "Dostarlimab 1000mg Q6W + Bevacizumab 15mg/kg Q3W 直至進展。"},

{"cancer": "Ovarian", 
        "pos": ["P-MT"], 
        "sub_pos": ["BRCA mutation", "HRD positive (wt)"], "type": "Ongoing",
        "name": "📍 TroFuse-021 (GOG-3102 / ENGOT-ov85)", "pharma": "MSD (Merck)", "drug": "sac-TMT (MK-2870) ± Bev", 
        "pop_results": "HRD- 族群維持新解：針對 PARPi 獲益有限的 HRD 陰性族群，探索 ADC 維持治療能否優於標準觀察或標靶維持。",
        "rationale": "HRD 陰性腫瘤對 PARPi 反應差，TROP2 ADC 提供與修復路徑無關的殺傷機制，並可能與 Bevacizumab 具備協同抗血管效應。",
        "regimen": "Arm A: sac-TMT 維持; Arm B: sac-TMT + Bevacizumab 維持; Arm C: SoC 維持 (Bev 或 觀察)。",
        "inclusion": ["新診斷晚期上皮性卵巢癌/輸卵管癌，完成一線含鉑治療後未進展者",
            "經檢測證實為 HRD-negative",
            "ECOG 0-1"],
        "exclusion": ["先前接受過 TROP2 ADC 或其他 Topo-I ADC 治療者",
            "無法耐受維持期用藥安全性要求"],
        "outcomes": "進行中 (Ongoing)；旨在填補 HRD 陰性族群在一線維持治療上的臨床需求空白。"},

    {"cancer": "Ovarian", 
        "pos": ["R-MT"], 
        "sub_pos": ["ADC/other Maint"], "type": "Ongoing",
        "name": "📍 TroFuse-022 (GOG-3103 / ENGOT-ov84)", "pharma": "MSD (Merck)", "drug": "sac-TMT (MK-2870) ± Bev", 
        "pop_results": "PSOC 維持治療新機制：針對含鉑敏感復發且完成化療後，探索 TROP2 ADC 作為非鉑類機制維持治療的潛力。",
        "rationale": "PSOC 在含鉑治療後的微小病灶期，利用不同於鉑類的 ADC 載荷 (Payload) 達成更深層的細胞毒殺，延緩復發。",
        "regimen": "Arm A: sac-TMT 維持; Arm B: sac-TMT + Bevacizumab 維持; Arm C: SoC 維持 (Bev 或 觀察)。",
        "inclusion": ["鉑類敏感復發 (PSOC) 之卵巢/輸卵管/原發腹膜癌",
            "完成含鉑治療後進入維持期",
            "ECOG 0-1"],
        "outcomes": "進行中 (Ongoing)；此試驗旨在確認 sac-TMT 是否能提供優於現有 Bevacizumab 或 PARPi 維持的臨床獲益。"},

{"cancer": "Ovarian", 
        "pos": ["R-TX"], 
        "sub_pos": ["PROC (Resistant Recur)"], "type": "Ongoing",
        "name": "📍 REJOICE-Ovarian01 (R-DXd)", "pharma": "Daiichi Sankyo / MSD", "drug": "Raludotatug Deruxtecan (R-DXd)", 
        "pop_results": "PROC 救星：針對鉑類抗藥復發，Phase II 實證 ORR 高達 50.5% (DCR 77.6%)，打破以往單藥化療僅 10-15% 的瓶頸。",
        "rationale": "針對上皮性卵巢癌高度表現的 CDH6 標靶，利用 DXd 載荷達成強效細胞殺傷，為 PROC 提供全新的精準打擊方案。",
        "regimen": "Phase III 劑量: 5.6 mg/kg Q3W (對比醫師選擇化療 TPC: Pacli, PLD, Gem, Topo)。",
        "inclusion": ["鉑類抗藥復發 (PROC) 高惡性度卵巢癌",
            "先前接受過 1-3 線治療",
            "高 FRα 患者通常需曾用過 Mirvetuximab"],
        "outcomes": "Phase II Confirmed ORR: 50.5%; 5.6mg/kg 劑量組 ORR 亦達 50.0%；需警惕 ILD/Pneumonitis (約 3.7%) 風險。"},
    
    {"cancer": "Ovarian", "name": "📍 DESTINY-Ovarian01/DS8201-772 (Enhertu)", "pharma": "AstraZeneca", "drug": "T-DXd", "pos": "P-MT", "sub_pos": ["BRCA mutation", "HRD positive (wt)"], "type": "Ongoing",
     "pop_results": "用 **HER2-ADC（T-DXd）**在一線治療後做維持，並合併 bevacizumab，瞄準「HER2 表現的卵巢癌亞群缺乏明確的標靶維持標準、仍易復發」這個 unmet need，希望延長維持期控制與存活。",
     "rationale": "標靶 HER2 ADC 用於維持。利用 T-DXd 極高 DAR (8) 優勢清除化療後殘餘之 HER2 表現微小病灶。",
     "regimen": "Trastuzumab deruxtecan 5.4mg/kg IV Q3W 維持至進展。"},    
]

# --- 3. AI 模型巡邏與聯動功能 ---
def get_gemini_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target_model = next((m for m in available_models if 'gemini-1.5-flash' in m), None)
        if not target_model: target_model = next((m for m in available_models if 'gemini-pro' in m), None)
        if target_model: return genai.GenerativeModel(target_model)
    except: return None

# --- 4. 側邊欄：決策助理 (複製功能與排版優化版) ---
with st.sidebar:
    st.markdown("<h3 style='color: #6A1B9A;'>🤖 AI 實證媒合助理</h3>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    
    with st.expander("✨ 患者病歷數據深度分析", expanded=True):
        p_notes = st.text_area("輸入摘要 (含分期/細胞/標記)", placeholder="例如：EC Stage III, dMMR, p53 mutation...", height=200)
        
        if st.button("🚀 開始媒合分析", use_container_width=True):
            if api_key and p_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = get_gemini_model()
                    
                    # --- [優化 Prompt] 限制 AI 不要輸出過多 Markdown 符號 ---
                    prompt = f"""
                    請作為專業婦癌專家分析以下病歷：{p_notes}。
                    參考實證庫：{all_trials_db}。
                    
                    【輸出要求】：
                    1. 請使用『純文字』專業醫療報告格式。
                    2. 嚴禁使用過多的星號(**)或井字號(###)。
                    3. 使用簡單的標題與點列式(•)即可。
                    4. 內容需包含：病歷摘要、推薦試驗、推薦理由與 Decision Tree 步驟。
                    """
                    
                    response = model.generate_content(prompt)
                    # 將結果存入暫存
                    st.session_state['ai_matching_report'] = response.text
                except Exception as e: 
                    st.error(f"AI 異常: {e}")
            else:
                st.warning("請輸入 Key 與病歷摘要")

        # --- [重點：穩定複製區塊] ---
        if 'ai_matching_report' in st.session_state:
            st.markdown("---")
            st.info("📋 **分析完成！點擊下方方框右上角圖示即可『一鍵複製』：**")
            
            # 使用 st.code 顯示，右上角會自動出現一個官方的複製按鈕，保證 100% 成功
            st.code(st.session_state['ai_matching_report'], language=None)
            
            # 提供清空按鈕，方便下一次分析
            if st.button("🗑️ 清空目前的分析內容", use_container_width=True):
                del st.session_state['ai_matching_report']
                st.rerun()

# --- 5. 主頁面：導航地圖佈局 ---
st.markdown("<div class='main-title'>婦癌臨床導航儀表板 (2026 旗艦最終極量整合版)</div>", unsafe_allow_html=True)
cancer_type = st.radio("第一步：選擇癌症類型", ["Endometrial", "Ovarian", "Cervical", "Uterine Sarcoma"], horizontal=True)

cols = st.columns(len(guidelines_nested[cancer_type]))
stages_data = guidelines_nested[cancer_type]

for i, stage in enumerate(stages_data):
    with cols[i]:
        st.markdown(f"""<div class='big-stage-card card-{stage['css']}'><div class='big-stage-header header-{stage['css']}'>{stage['header']}</div>""", unsafe_allow_html=True)
        for sub in stage['subs']:
            st.markdown(f"""<div class='sub-block'><div class='sub-block-title'>📘 {sub['title']}</div><div class='sub-block-content'>{sub['content']}</div>""", unsafe_allow_html=True)
            
            # 合併實證渲染按鈕
            rel_trials = [t for t in all_trials_db if t["cancer"] == cancer_type and stage["id"] in t["pos"] and any(s in sub["title"] for s in t["sub_pos"])]
            
            for t in rel_trials:
                label = f"{t.get('pharma', 'N/A')} | {t['name']} | {t['drug']}"
                with st.popover(label, use_container_width=True):
                    # 展示簡單療效小結論 (圖三修復)
                    st.success(f"**核心結論摘要:** {t.get('pop_results', '招募中/詳見深度看板')}")
                    # 同步聯動邏輯：點擊觸發 rerun 同步看板
                    unique_key = f"sync_{t['name']}_{cancer_type}_{stage['id']}_{sub['title'].replace(' ', '')}"
                    if st.button("📊 同步看板細節", key=unique_key):
                        st.session_state.selected_trial = t['name']
                        st.rerun() 
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 6. 深度數據看板 (極量化資訊展示區) ---
st.divider()
st.subheader("📋 臨床研究極量化數據庫 (Published Milestones & Ongoing Trials)")
filtered_names = [t["name"] for t in all_trials_db if t["cancer"] == cancer_type]

if not filtered_names:
    st.info("該癌症類別下目前無適用實證或計畫。")
else:
    try: curr_idx = filtered_names.index(st.session_state.selected_trial)
    except: curr_idx = 0

    selected_name = st.selectbox("🎯 快速選擇研究計畫以查閱分組與數據：", filtered_names, index=curr_idx, key="trial_selector")
    st.session_state.selected_trial = selected_name
    t_obj = next(it for it in all_trials_db if it["name"] == selected_name)

    st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #E0E0E0; padding-bottom:10px; font-weight:900;'>📋 {t_obj['name']} 深度分析報告</h2>", unsafe_allow_html=True)

    r1, r2 = st.columns([1.3, 1])
    with r1:
        st.markdown("<div style='background:#E3F2FD; border-left:10px solid #1976D2; padding:15px; border-radius:10px;'><b>💉 Rationale & Regimen (機轉與分組給藥)</b></div>", unsafe_allow_html=True)
        st.write(f"**藥廠:** {t_obj.get('pharma', 'N/A')} | **核心配方:** {t_obj['drug']}")
        
        # 極量化給藥方案 (Dosing Protocol) - 補齊分組細節
        st.markdown("<div class='regimen-box'><b>分組給藥方式 (Regimen per Arm):</b><br>" + t_obj.get('regimen', '正在補齊分組給藥細節。') + "</div>", unsafe_allow_html=True)
        
        st.success(f"**科學理據 (Scientific Rationale):** {t_obj.get('rationale', '旨在挑戰 SoC 瓶頸提升獲益。')}")

    with r2:
        st.markdown("<div style='background:#FFF8E1; border-left:8px solid #FBC02D; padding:15px; border-radius:10px;'><b>📈 Key Outcomes (最新生存與緩解指標)</b></div>", unsafe_allow_html=True)
        st.markdown(f"""
            <div style='text-align:center; background:white; padding:15px; border:2px solid #FFE082; border-radius:12px;'>
                <div style='font-size: 14px; color: #795548; font-weight:700; margin-bottom:5px;'>Survival Metrics (PFS/OS/HR/ORR)</div>
                <div class='hr-big-val'>{t_obj.get('outcomes', t_obj.get('results_short', 'Ongoing Recruitment'))}</div>
            </div>
        """, unsafe_allow_html=True)
        

    st.divider()
    r3, r4 = st.columns(2)
    with r3:
        st.markdown("<div style='background:#E8F5E9; border-left:8px solid #2E7D32; padding:15px; border-radius:10px;'><b>✅ Inclusion Criteria (關鍵納入標準)</b></div>", unsafe_allow_html=True)
        for inc in t_obj.get('inclusion', ['符合分子標記分型與前線規定。']): st.write(f"• **{inc}**")
    with r4:
        st.markdown("<div style='background:#FFEBEE; border-left:8px solid #C62828; padding:15px; border-radius:10px;'><b>❌ Exclusion Criteria (關鍵排除標準)</b></div>", unsafe_allow_html=True)
        for exc in t_obj.get('exclusion', ['排除臟器功能異常或活動性自體免疫疾病。']): st.write(f"• **{exc}**")
    st.markdown("</div>", unsafe_allow_html=True)
