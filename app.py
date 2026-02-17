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
            {"title": "HGSC / Endometrioid", "content": "手術 (PDS/IDS) + Carbo/Pacli ± Bev。IDS 加 HIPEC (van Driel)。"},
            {"title": "Low grade serous carcinoma", "content": "AI, MEK, CDK 4/6"},
            {"title": "Mucinous (MOC) 鑑定", "content": "判定：CK7+/SATB2- (原發)。IA 期可保守。侵襲型建議積極化療。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "BRCA mutation", "content": "Olaparib 單藥維持 2年 (SOLO-1)。"}, 
            {"title": "HRD positive (wt)", "content": "PAOLA-1 (Ola+Bev) 或 PRIMA (Nira)。"},
            {"title": "HRD negative (pHRD)", "content": "Niraparib 維持 (PRIMA ITT) 或 Bevacizumab。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "PSOC (Sensitive Recur)", "content": "PFI > 6m。評估二次手術 (DESKTOP III) 或含鉑複方。"},
            {"title": "PROC (Resistant Recur)", "content": "PFI < 6m。單藥化療 ± Bev 或標靶 ADC (MIRASOL)。"},
            {"title": "Low grade serous carcinoma", "content": "AI, MEK, CDK 4/6"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "PARPi Maint", "content": "救援緩解後續用 PARPi (NOVA/ARIEL3/SOLO2)。"}]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "Locally Advanced (CCRT)", "content": "同步化放療 ± 同步 IO (A18) 或 誘導化療 (INTERLACE)。"},
            {"title": "Early Stage (Surgery)", "content": "根治術 (LACC) 或單純切除 (SHAPE)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Maintenance", "content": "1L 方案後接續維持 (KEYNOTE-826)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "Recurr / Metastatic", "content": "一線 KN826/BEATcc。二線 ADC (innovaTV 301) 或 IO (EMPOWER)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "維持當前有效救援方案直至 PD。"}]}
    ]
}

# --- 2. 實證資料庫 (33 項試驗全量數據極量化補完) ---
all_trials_db = [
    # ==========================
    # === Endometrial Published ===
    # ==========================
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["dMMR / MSI-H / MMRd"], "name": "📚 RUBY (ENGOT-EN6/GOG-3031)", "pharma": "GSK", "drug": "Dostarlimab + Carboplatin/Paclitaxel", 
     "pop_results": "dMMR/MSS（pMMR）皆顯著延長PFS（dMMR：HR 0.28；全體：HR 0.64），且更新分析顯示OS亦改善（dMMR：HR 0.32；全體：HR 0.69），奠定一線「免疫＋化療」新標準。",
     "rationale": "PD-1 阻斷 (PD-1 blockade) 與含鉑化療 (Carbo/Pacli) 具備協同免疫原性細胞死亡 (ICD) 效應。藉由化療誘導腫瘤抗原釋放，釋放免疫微環境壓力並針對 MMRd 族群達成極高持久應答率。",
     "regimen": "Arm 1 (Dostarlimab 組): 誘導期: Dostarlimab 500mg Q3W + Carboplatin (AUC 5) + Paclitaxel (175 mg/m2) x6 週期；維持期: Dostarlimab 1000mg Q6W (持續 3年)。 Arm 2 (Placebo 組): 生理鹽水對照 + 同劑量 CP 化療 x6 週期。",
     "inclusion": ["新診斷 FIGO Stage III-IV 或首次復發之子宮內膜癌 (EC)。", "ECOG 0-1。", "含 Carcinosarcoma / Clear cell / Serous 等組織型態。"],
     "exclusion": ["既往接受 PD-1/PD-L1 治療。", "活動性/需系統性治療之自體免疫疾病。", "未控制感染。", "臨床上顯著 CNS 轉移等。"],
     "outcomes": "dMMR 族群 24個月 PFS 率: 61.4% vs 15.7% (HR 0.28, 95% CI 0.16-0.50); ITT 全人群 mOS HR 0.64 (95% CI 0.46-0.87, P=0.0021)。"},

    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["dMMR / MSI-H / MMRd", "pMMR / NSMP / MSS"], "name": "📚 NRG-GY018 (KEYNOTE-868)", "pharma": "MSD", "drug": "Pembrolizumab + Carboplatin/Paclitaxel", 
     "pop_results": "Pembrolizumab＋化療在一線顯著延長PFS（dMMR：HR 0.30；pMMR：HR 0.54），是另一個改變臨床實務的一線免疫＋化療關鍵試驗。",
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
     "pop_results": "Atezolizumab＋化療在dMMR族群PFS顯著改善（HR 0.36），訊息重點是「效益主要集中在dMMR」，pMMR整體效益相對不明顯，dMMR PFS HR 0.36; ITT OS HR 0.82",
     "rationale": "驗證一線 PD-L1 抑制劑併用化療對晚期或復發患者之生存優勢。",
     "regimen": "Arm A: Atezolizumab 1200mg Q3W + CP x6-8 週期 -> 維持 Atezolizumab 1200mg Q3W。 Arm B: Placebo + CP x6-8 週期。",
     "inclusion": ["advanced 或 recurrent endometrial carcinoma。", "一線接受 CP。", "評估 dMMR 亞群獲益。"],
     "exclusion": ["既往 PD-(L)1 抑制劑。", "活動性自體免疫需治療。", "未控制感染。", "其他研究者判定不適合等。"],
     "outcomes": "dMMR PFS: 未達到 vs 6.9m (HR 0.36, 95% CI 0.23-0.57); 全人群 mOS HR 0.82 (P=0.048)。"},
    
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
    
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Early Stage (Surgery)"], 
        "name": "📚 LACC", "pharma": "NEJM", "drug": "Open vs MIS Radical Hysterectomy", 
        "pop_results": "改變手術標準之研究：微創手術 (MIS) 相較於傳統開腹手術，其復發風險較高且三年存活率較低。",
        "rationale": "評估達文西/腹腔鏡微創手術在子宮頸癌根治術中，是否能達成與開腹手術同等的預後。",
        "outcomes": "DFS Rate: 91.2% (MIS) vs 97.1% (Open); HR for recurrence 3.74。"},
    
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Early Stage (Surgery)"], 
        "name": "📚 SHAPE", "pharma": "CCTG", "drug": "Simple vs Radical Hysterectomy", 
        "pop_results": "低風險降階選擇：對於腫瘤 <2cm 之低風險患者，單純子宮切除在三年盆腔復發率上不劣於廣泛性子宮切除。",
        "rationale": "旨在減少早期患者接受過度手術治療所導致的併發症與生活品質受損。",
        "outcomes": "3yr Pelvic Recurrence: 2.52% (Simple) vs 2.17% (Radical); P<0.05 (非劣性)。"},
    
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

    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 van Driel HIPEC", "pharma": "NEJM", "drug": "Surgery + HIPEC (Cisplatin)", 
     "pop_results": "間隔減積手術加入HIPEC可改善OS（死亡風險下降：OS HR 0.67），為「特定一線手術情境」引入HIPEC的重要證據，IDS 加溫：mOS 延長 12 個月 (HR 0.67)",
     "rationale": "術中加溫腹腔化療強化物理殺傷與滲透力。",
     "regimen": "stage III、NACT 後 間歇減積手術 (IDS) 時同步進行加溫 (42°C) 腹腔灌注 Cisplatin (100 mg/m2) 90 分鐘。Arm A：surgery + HIPEC cisplatin（常見 100 mg/m²、90 分鐘）+ 後續化療。Arm B：surgery（no HIPEC）+ 後續化療。",
     "inclusion": ["stage III epithelial ovarian cancer。", "NACT 後適合 interval debulking。"],
     "exclusion": ["不適合大手術或 HIPEC（腎功能、全身狀況等）。", "其他重大共病。"],
     "outcomes": "mOS: 45.7m vs 33.9m (HR 0.67, 95% CI 0.48-0.94)。recurrence-free survival 亦改善；Grade 3–4 AE 率相近。"},

    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 LION", "pharma": "NEJM", "drug": "No Lymphadenectomy", 
     "pop_results": "系統性淋巴清掃不改善存活（OS HR 1.06；PFS HR 1.11）且併發症增加，改變了「外觀正常淋巴結」患者的手術範式，臨床 LN 陰性免清掃：OS 無差異 (HR 1.06)",
     "regimen": "在「臨床/影像陰性淋巴結」且完成腫瘤切除的 advanced ovarian cancer。Arm A：systematic pelvic + para-aortic lymphadenectomy。Arm B：no lymphadenectomy。",
     "inclusion": ["advanced ovarian cancer。", "complete resection。", "淋巴結臨床陰性。"],
     "exclusion": ["明顯淋巴結病灶。", "無法耐受手術延長。"],
     "outcomes": "OS HR 1.06（無獲益）；PFS 亦無差；但手術併發症增加。mOS: 65.5m vs 69.2m (HR 1.06)。臨床 LN(-) 者免清掃。"},

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
    # === Ongoing Trials (8核心極量化) ===
    # ==========================
    {"cancer": "Endometrial", "name": "📍 MK2870-033", "pharma": "MSD", "drug": "Sac-TMT + Pembrolizumab", "pos": "P-MT", "sub_pos": ["Maintenance Therapy"], "type": "Ongoing",
     "pop_results": "用 TROP2-ADC增加腫瘤細胞殺傷並與 PD-1 抑制併用，目標是補足「pMMR 子宮內膜癌對免疫單藥反應較差、需要更強的一線/維持策略」的缺口。",
     "rationale": "標靶 Trop-2 ADC (Sac-TMT) 協同 PD-1。透過 ADC 誘導之 ICD 改善微環境，旨在提升 pMMR 或 NSMP 患者一線維持階段應答深度與持續時間。",
     "regimen": "Arm A (分組 1): Sac-TMT 5mg/kg Q6W + Pembrolizumab 400mg Q6W 維持治療直到 PD。 Arm B (分組 2): 醫師選擇維持方案 (對照組)。",
     "inclusion": ["新診斷 pMMR/MSS 子宮內膜癌 (中心 IHC 檢測確認)。", "FIGO III-IV 期、一線含鉑化療 + Pembrolizumab 後達 CR/PR。"],
     "exclusion": ["先前接受過針對復發病灶之系統 IO 治療。", "組織學為子宮肉瘤 (Sarcoma)。"]},

    {"cancer": "Ovarian", "name": "📍 FRAmework-01 (LY4170156)", "pharma": "Eli Lilly", "drug": "LY4170156 + Bevacizumab", "pos": "R-TX", "sub_pos": ["PROC (Resistant Recur)", "PSOC (Sensitive Recur)"], "type": "Ongoing",
     "pop_results": "以 FRα 標的 ADC（把細胞毒載荷精準送入腫瘤）攻克鉑抗藥卵巢癌，並嘗試擴大到更多 FRα 表現範圍/或搭配 bev，目的在彌補「鉑抗藥期有效且可耐受的系統治療仍不足、FRα-ADC 受惠族群仍有限」的缺口。",
     "rationale": "標靶 FRα ADC 聯用 anti-VEGF。利用 Bevacizumab 血管調節作用降低腫瘤間質壓，提升 ADC 於實體腫瘤內的滲透深度挑戰耐藥瓶頸。",
     "regimen": "PROC 隊列分組： Arm A: LY 3.0mg/kg + Bev 15mg/kg Q3W; Arm B: LY 4.0mg/kg + Bev 15mg/kg Q3W。 PSOC 隊列 (PFI 6-12m): Arm C: LY 3.0mg/kg + Bev 15mg/kg Q3W。 對照組 (Arm D): 醫師選擇化療 SoC。",
     "inclusion": ["經檢測確認 FRα 表達陽性 (IHC)。", "最後鉑類後進展之 PROC 或 PSOC (PFI 90d-365d)。"],
     "exclusion": ["曾用過針對 FRα 之 ADC (如 Enhertu 曾試過者需評估)。", "活動性間質性肺病 (ILD)。"]},

    {"cancer": "Endometrial", "name": "📍 GU-US-682-6769", "pharma": "Gilead", "drug": "SG (Trodelvy)", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "type": "Ongoing",
     "pop_results": "針對「鉑類化療+PD-(L)1 後仍進展、預後差且後線缺乏有效方案」的族群，評估 **TROP2-ADC（sacituzumab govitecan，載荷 SN-38）**能否在 PFS/OS 超越傳統單藥化療，填補後線治療空窗。",
     "rationale": "針對 Trop-2 標靶。利用 SN-38 載荷引發強力 DNA 損傷，專攻鉑類與免疫檢查點抑制劑 (ICI) 失敗後之復發救援。",
     "regimen": "Sacituzumab govitecan 10mg/kg (Day 1, Day 8) 每 21 天為一週期 (Q21D) 直至疾病進展。",
     "inclusion": ["復發性 EC (不含肉瘤)。", "先前曾接受過至少一次含鉑化療及 PD-1/L1 失敗進展者。", "ECOG 0-1。"]},

    {"cancer": "Ovarian", "name": "📍 DOVE", "pharma": "GSK", "drug": "Dostarlimab + Bevacizumab", "pos": "R-TX", "sub_pos": ["PROC (Resistant Recur)"], "type": "Ongoing",
     "pop_results": "用 **PD-1 抑制（dostarlimab）**單用或合併 抗血管新生（bevacizumab），想把「對化療特別不敏感、復發後選擇很少」的透明細胞癌，從傳統化療導向轉成免疫/免疫合併抗血管新生的新策略。",
     "rationale": "針對 OCCC 透明細胞癌。利用 PD-1 + anti-VEGF 雙重阻斷改善其特有且高度免疫抑制之微環境。",
     "regimen": "Dostarlimab 1000mg Q6W + Bevacizumab 15mg/kg Q3W 直至進展。"},

    {"cancer": "Ovarian", "name": "📍 DS8201-772 (Enhertu)", "pharma": "AstraZeneca", "drug": "T-DXd", "pos": "P-MT", "sub_pos": ["BRCA mutation", "HRD positive (wt)"], "type": "Ongoing",
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

# --- 4. 側邊欄：決策助理 ---
with st.sidebar:
    st.markdown("<h3 style='color: #6A1B9A;'>🤖 AI 實證媒合助理</h3>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 患者病歷數據深度分析", expanded=True):
        p_notes = st.text_area("輸入摘要 (含分期/細胞/標記)", placeholder="例如：EC Stage III, dMMR, p53 mutation, HER2 2+...", height=250)
        if st.button("🚀 開始媒合分析"):
            if api_key and p_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = get_gemini_model()
                    prompt = f"分析病歷：{p_notes}。請參考實證庫：{all_trials_db}。建議適合路徑與試驗理由。"
                    st.write(model.generate_content(prompt).text)
                except Exception as e: st.error(f"AI 異常: {e}")

# --- 5. 主頁面：導航地圖佈局 ---
st.markdown("<div class='main-title'>婦癌臨床導航儀表板 (2026 旗艦最終極量整合版)</div>", unsafe_allow_html=True)
cancer_type = st.radio("第一步：選擇癌症類型", ["Endometrial", "Ovarian", "Cervical"], horizontal=True)

cols = st.columns(len(guidelines_nested[cancer_type]))
stages_data = guidelines_nested[cancer_type]

for i, stage in enumerate(stages_data):
    with cols[i]:
        st.markdown(f"""<div class='big-stage-card card-{stage['css']}'><div class='big-stage-header header-{stage['css']}'>{stage['header']}</div>""", unsafe_allow_html=True)
        for sub in stage['subs']:
            st.markdown(f"""<div class='sub-block'><div class='sub-block-title'>📘 {sub['title']}</div><div class='sub-block-content'>{sub['content']}</div>""", unsafe_allow_html=True)
            
            # 合併實證渲染按鈕
            rel_trials = [t for t in (all_trials_db) if t["cancer"] == cancer_type and t["pos"] == stage["id"] and any(s in sub["title"] for s in t["sub_pos"])]
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
