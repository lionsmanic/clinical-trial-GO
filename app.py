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
        font-size: 32px !important; font-weight: 900; color: #004D40;
        padding: 5px 0; border-bottom: 3px solid #4DB6AC; margin-bottom: 5px;
    }

    /* 階段方塊深色漸層背景 */
    .big-stage-card {
        border-radius: 12px; padding: 0px; box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        border: 2.5px solid transparent; background: white; margin-bottom: 6px; overflow: hidden; height: auto !important;
    }
    .big-stage-header {
        font-size: 19px !important; font-weight: 900; color: white !important;
        padding: 12px; text-align: center; text-shadow: 1px 1px 3px rgba(0,0,0,0.4);
    }

    /* 配色強化 */
    .card-p-tx { border-color: #1B5E20; }
    .header-p-tx { background: linear-gradient(135deg, #2E7D32, #1B5E20); } /* Primary Tx */
    .card-p-mt { border-color: #0D47A1; }
    .header-p-mt { background: linear-gradient(135deg, #1565C0, #0D47A1); } /* 1L Maint */
    .card-r-tx { border-color: #E65100; }
    .header-r-tx { background: linear-gradient(135deg, #EF6C00, #BF360C); } /* Recurr Tx */
    .card-r-mt { border-color: #4A148C; }
    .header-r-mt { background: linear-gradient(135deg, #6A1B9A, #4A148C); } /* PR-Maint */

    .sub-block {
        margin: 4px 6px; padding: 6px; border-radius: 8px; 
        background: #F8F9FA; border-left: 6px solid #455A64;
    }
    .sub-block-title {
        font-size: 15px; font-weight: 900; color: #263238;
        margin-bottom: 2px; border-bottom: 1.2px solid #CFD8DC; padding-bottom: 2px;
    }

    .stPopover button { 
        font-weight: 900 !important; font-size: 12px !important; 
        border-radius: 5px !important; margin-top: 2px !important;
        padding: 2px 8px !important; width: 100% !important; 
        text-align: left !important; color: #1A1A1A !important; 
        border: 1.2px solid rgba(0,0,0,0.18) !important;
        box-shadow: 0 1.5px 4px rgba(0,0,0,0.12) !important;
    }
    
    .stPopover button[aria-label*="📚"] { background: #ECEFF1 !important; border-left: 6px solid #455A64 !important; }
    .stPopover button[aria-label*="📍"] { background: #E1F5FE !important; border-left: 6px solid #0288D1 !important; } 

    .detail-section { background: white; border-radius: 20px; padding: 30px; border: 1.5px solid #CFD8DC; box-shadow: 0 10px 40px rgba(0,0,0,0.08); }
    .hr-big-val { font-family: 'Roboto', sans-serif; font-size: 34px !important; font-weight: 900; color: #D84315; }
    .regimen-box { background: #F1F8E9; border-left: 5px solid #689F38; padding: 10px; margin: 5px 0; border-radius: 5px; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 指引數據庫：精確分型與路徑救援 (EC/OC/CC) ---
guidelines_nested = {
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "dMMR / MSI-H / MMRd", "content": "一線標竿：Chemo + PD-1 (RUBY/GY018/AtTEnd)。"},
            {"title": "pMMR / NSMP / MSS", "content": "ER/Grade 分流。一線化療加維持 (DUO-E)。二線標靶免疫 (KN775)。"},
            {"title": "POLE mutation (超突變)", "content": "預後極佳，早期可降階治療。晚期實證持續累積中。"},
            {"title": "p53 mutation (高拷貝)", "content": "預後最差。建議化放療積極介入。Serous 型需檢測 HER2。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Maintenance", "content": "一線 IO 後延續維持至 PD (MK2870-033/DUO-E/RUBY)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "Recurrent EC", "content": "標靶+免疫 (KN775) 或單藥 IO (GARNET)。救援 ADC (SG)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Tx", "content": "復發緩解後維持有效方案直至進展。"}]}
    ],
    "Ovarian": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "HGSC / Endometrioid", "content": "PDS/IDS + Carbo/Pacli ± Bev。考慮 IDS 加 HIPEC (van Driel)。"},
            {"title": "Mucinous (MOC) 鑑定", "content": "判定：CK7+/SATB2-。Expansile (IA可保守) vs Infiltrative。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "BRCA mutation", "content": "Olaparib 維持 2年 (SOLO-1)。"}, 
            {"title": "HRD positive / BRCA wt", "content": "PAOLA-1 (Ola+Bev) 或 PRIMA (Nira) 或 DUO-O。"},
            {"title": "HRD negative (pHRD)", "content": "Niraparib 維持 (PRIMA ITT) 或 Bevacizumab。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "PSOC (Sensitive)", "content": "PFI > 6m。評估二次手術 (DESKTOP III) 或含鉑複方。"},
            {"title": "PROC (Resistant)", "content": "PFI < 6m。單藥化療 ± Bev 或標靶 ADC (MIRASOL/FRAmework)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "PARPi Maint", "content": "救援緩解後續用 PARPi (NOVA/ARIEL3/SOLO2)。"}]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "Locally Advanced (CCRT)", "content": "同步化放療 ± 同步 IO (A18) 或 誘導化療 (INTERLACE)。"},
            {"title": "Early Stage (Surgery)", "content": "根治術 (LACC) 或單純切除 (SHAPE)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Maintenance", "content": "1L 方案後接續維持 (KEYNOTE-826)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "Recurr / Metastatic", "content": "一線 KN826/BEATcc。二線 ADC (innovaTV 301) 或 IO。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "維持有效救援方案直至 PD。"}]}
    ]
}

# --- 2. 實證資料庫 (33 項試驗全量數據極緻化) ---
all_trials_db = [
    # ==========================
    # === Endometrial (已發表) ===
    # ==========================
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["dMMR / MSI-H / MMRd"], "name": "📚 RUBY (ENGOT-EN6/GOG-3031)", "pharma": "GSK", "drug": "Dostarlimab + CP", 
     "results_short": "dMMR 死亡風險降低 68% (HR 0.32)",
     "rationale": "PD-1 阻斷 (PD-1 blockade) 與含鉑化療 (Platinum-based Chemo) 具有協同免疫原性細胞死亡 (ICD) 效應。",
     "regimen": "Arm A: Dostarlimab 500mg Q3W + CP x6 週期 -> Maint: Dostarlimab 1000mg Q6W (3年)。 Arm B: Placebo + CP x6 週期。",
     "inclusion": ["新診斷 FIGO Stage III-IV 或首次復發之子宮內膜癌 (EC)。", "ECOG 0-1。", "含 Carcinosarcoma / Clear cell 等組織型態。"],
     "exclusion": ["先前接受過系統性化療。", "活動性自體免疫疾病。"],
     "outcomes": "dMMR 24m PFS: 61.4% vs 15.7% (HR 0.28); ITT OS HR 0.64 (95% CI 0.46-0.87, P=0.0021)."},

    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["dMMR / MSI-H / MMRd", "pMMR / NSMP / MSS"], "name": "📚 NRG-GY018 (KEYNOTE-868)", "pharma": "MSD", "drug": "Pembrolizumab + CP", 
     "results_short": "dMMR PFS HR 0.30; pMMR HR 0.54",
     "rationale": "利用免疫檢查點抑制劑 (ICI) 重塑腫瘤微環境，提升一線晚期患者不論 MMR 狀態之存活率。",
     "regimen": "Arm A: Pembrolizumab 200mg Q3W + CP x6 -> Maint: Pembro 400mg Q6W (2年)。 Arm B: Placebo + CP。",
     "inclusion": ["Stage III/IV 或復發 EC。", "測得 MMR 狀態。"],
     "outcomes": "dMMR PFS HR 0.30 (95% CI 0.19-0.48); pMMR PFS HR 0.54 (95% CI 0.41-0.71)."},

    {"cancer": "Endometrial", "pos": "P-MT", "sub_pos": ["pMMR / NSMP / MSS"], "name": "📚 DUO-E (ENGOT-EN9)", "pharma": "AZ", "drug": "Durvalumab + CP →維持 ± Olaparib", 
     "results_short": "三藥組 pMMR PFS HR 0.57 (vs CP)",
     "rationale": "探索 PARP 抑制劑 (PARPi) 在 pMMR 族群免疫維持階段的增敏與協同作用。",
     "regimen": "Arm 1: CP alone; Arm 2: CP+Durva -> Durva Maint; Arm 3: CP+Durva -> Durva+Ola Maint (300mg bid)。",
     "outcomes": "pMMR Arm 3 vs Arm 1: PFS HR 0.57 (95% CI 0.42-0.79); dMMR Arm 2 vs 1: HR 0.42."},

    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["dMMR / MSI-H / MMRd"], "name": "📚 AtTEnd (ENGOT-EN7)", "pharma": "Roche", "drug": "Atezolizumab + CP", 
     "results_short": "dMMR PFS HR 0.36; ITT OS HR 0.82",
     "outcomes": "dMMR PFS: 未達到 vs 6.9m (HR 0.36, 95% CI 0.23-0.57); 全人群 mOS HR 0.82 (P=0.048)."},

    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "name": "📚 KEYNOTE-775 (Study 309)", "pharma": "MSD/Eisai", "drug": "Lenvatinib + Pembrolizumab", 
     "results_short": "pMMR/MSS 二線標準：OS 17.4m vs 12.0m",
     "rationale": "結合 VEGF-TKI 重塑血管並減輕免疫抑制，克服 MSS 腫瘤對單藥免疫之冷微環境。",
     "regimen": "Lenvatinib 20mg QD + Pembrolizumab 200mg Q3W 直至疾病進展。",
     "inclusion": ["先前含鉑化療後進展之晚期 EC。", "ECOG 0-1。", "不限 MMR 狀態。"],
     "outcomes": "pMMR OS: 17.4m vs 12.0m (HR 0.68, 95% CI 0.56-0.84, P<0.001)."},

    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "name": "📚 GARNET", "pharma": "GSK", "drug": "Dostarlimab (Single-agent)", 
     "results_short": "dMMR ORR 45.5%; DOR 持久",
     "outcomes": "dMMR/MSI-H ORR 45.5%; 12個月反應持續率 83.7%。"},

    # ==========================
    # === Cervical (已發表) ===
    # ==========================
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Locally Advanced (CCRT)"], "name": "📚 KEYNOTE-A18 (ENGOT-cx11)", "pharma": "MSD", "drug": "Pembrolizumab + CCRT", 
     "results_short": "LACC 標準：36m OS 82.6% (HR 0.67)",
     "rationale": "將免疫正式併入高風險局部晚期之根治性同步化放療。",
     "regimen": "Cisplatin + RT 同步 Pembro 200mg Q3W x5 週期 -> 維持 Pembro 400mg Q6W x15 週期。",
     "inclusion": ["新診斷 FIGO 2014 Stage IB2-IIB LN+ 或 Stage III-IVA 局部晚期。"],
     "outcomes": "24m PFS: 68% vs 57% (HR 0.70); 36m OS: 82.6% vs 74.8% (HR 0.67)."},

    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Locally Advanced (CCRT)"], "name": "📚 INTERLACE", "pharma": "UCL", "drug": "Induction Carbo/Pacli x6 -> CCRT", 
     "results_short": "5年 OS 80% (vs 72%, HR 0.60)",
     "rationale": "利用誘導化療 (Induction Chemo) 解決根治性放療前的微小轉移病灶。",
     "regimen": "誘導期: Paclitaxel 80mg/m2 + Carboplatin AUC2 每週一次 x6 週期 -> 同步放化療。",
     "outcomes": "5yr OS: 80% vs 72% (HR 0.60, 95% CI 0.44-0.82); 5yr PFS: 73% vs 64% (HR 0.65)."},

    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Locally Advanced (CCRT)"], "name": "📚 CALLA", "pharma": "AZ", "drug": "Durvalumab + CCRT", 
     "results_short": "整體陰性結果 (HR 0.84)",
     "outcomes": "PFS HR 0.84 (95% CI 0.65-1.08, P=0.174)."},

    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 KEYNOTE-826", "pharma": "MSD", "drug": "Pembrolizumab + Chemo ± Bev", 
     "results_short": "R/M 一線標準：OS HR 0.63",
     "rationale": "一線轉移性子宮頸癌免疫加化療的黃金標準。",
     "outcomes": "CPS≥1 mOS: 28.6m vs 16.5m (HR 0.60, 95% CI 0.49-0.74); 全人群 OS HR 0.63."},

    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 BEATcc (ENGOT-Cx10)", "pharma": "Roche", "drug": "Atezolizumab + Chemo + Bev", 
     "results_short": "PFS 13.7m vs 10.4m (HR 0.62)",
     "outcomes": "mPFS: 13.7m vs 10.4m (HR 0.62); mOS: 32.1m vs 22.8m (HR 0.68)."},

    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 EMPOWER-Cervical 1", "pharma": "Regeneron", "drug": "Cemiplimab vs Chemo", 
     "results_short": "二線後單藥免疫 OS 基石：OS HR 0.69",
     "outcomes": "mOS ITT: 12.0m vs 8.5m (HR 0.69, 95% CI 0.56-0.84)."},

    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 innovaTV 301 (ENGOT-cx12)", "pharma": "Genmab", "drug": "Tisotumab Vedotin (ADC)", 
     "results_short": "首個 OS 獲益 ADC：OS HR 0.70; ORR 17.8%",
     "rationale": "標靶組織因子 (TF) ADC，精準輸送 MMAE 殺傷後線化療耐藥癌細胞。",
     "outcomes": "mOS: 11.5m vs 9.5m (HR 0.70, 95% CI 0.54-0.89); ORR 17.8% vs 5.2%."},

    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Early Stage (Surgery)"], "name": "📚 SHAPE trial", "pharma": "CCTG", "drug": "Simple Hysterectomy", 
     "results_short": "低風險降階：3yr 盆腔復發 2.5% vs 2.2%",
     "outcomes": "3yr Pelvic Recurrence: 2.5% (SH) vs 2.2% (RH) (HR 1.12, 90% CI 0.61-2.03)."},

    # ==========================
    # === Ovarian (已發表) ===
    # ==========================
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutation"], "name": "📚 SOLO-1", "pharma": "AZ", "drug": "Olaparib Maint", 
     "results_short": "BRCAm 治癒潛力：7yr存活率 67% (HR 0.33)",
     "outcomes": "mPFS: 56.0m vs 13.8m (HR 0.30); 7yr Survival 67.0% vs 46.5%."},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive / BRCA wt", "HRD negative (pHRD)"], "name": "📚 PRIMA (ENGOT-OV26)", "pharma": "GSK", "drug": "Niraparib Maint", 
     "results_short": "全人群一線維持：HRD+ PFS HR 0.43",
     "rationale": "不限 BRCA 突變，擴大 PARPi 在一線含鉑化療反應後的獲益群眾。",
     "outcomes": "HRD+ PFS HR 0.43 (95% CI 0.31-0.59); ITT HR 0.62."},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive / BRCA wt"], "name": "📚 PAOLA-1 (ENGOT-ov25)", "pharma": "AZ", "drug": "Olaparib + Bevacizumab", 
     "results_short": "HRD+ 黃金組合：5yr OS 75.2% (HR 0.62)",
     "rationale": "結合 PARPi 與 anti-VEGF 維持路徑，重塑 DNA 修復抑制與微血管微環境。",
     "outcomes": "HRD+ 5yr OS: 75.2% vs 58.3% (HR 0.62, 95% CI 0.45-0.85)."},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutation", "HRD positive / BRCA wt"], "name": "📚 ATHENA–MONO", "pharma": "Clovis", "drug": "Rucaparib Maint", 
     "results_short": "ITT PFS 28.7m (HR 0.52)",
     "outcomes": "HRD+ PFS: 28.7m vs 11.3m (HR 0.47); ITT HR 0.52."},

    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["PARPi Maint"], "name": "📚 NOVA", "pharma": "GSK", "drug": "Niraparib 復發維持", 
     "results_short": "gBRCA HR 0.27; non-gBRCA HR 0.45",
     "outcomes": "gBRCA PFS: 21.0m vs 5.5m (HR 0.27); non-gBRCA HR 0.45."},

    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["PARPi Maint"], "name": "📚 ARIEL3", "pharma": "Clovis", "drug": "Rucaparib 復發維持", 
     "results_short": "BRCAm PFS HR 0.23; HRD+ HR 0.32",
     "outcomes": "BRCAm mPFS 16.6m vs 5.4m (HR 0.23)."},

    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["PARPi Maint"], "name": "📚 SOLO2", "pharma": "AZ", "drug": "Olaparib 復發維持", 
     "results_short": "BRCAm 復發 OS：mOS 51.7m (HR 0.74)",
     "outcomes": "mOS: 51.7m vs 38.8m (HR 0.74, 95% CI 0.54-1.00)."},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive / BRCA wt"], "name": "📚 DUO-O", "pharma": "AZ", "drug": "Durva+Ola+Bev 維持", 
     "results_short": "三藥維持潛力：HRD+ PFS HR 0.49",
     "outcomes": "HRD+ PFS HR 0.49 (95% CI 0.34-0.69); non-HRD HR 0.68."},

    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PROC (Resistant)"], "name": "📚 MIRASOL", "pharma": "ImmunoGen", "drug": "Mirvetuximab", 
     "results_short": "PROC OS 突破：OS HR 0.67; ORR 42.3%",
     "rationale": "首個在鉑類抗藥性患者證明具備存活獲益 (Overall Survival) 之 ADC。",
     "regimen": "Mirvetuximab 6.0 mg/kg (Adjusted Ideal Body Weight) IV Q3W。",
     "outcomes": "mOS: 16.4m vs 12.7m (HR 0.67); mPFS 5.6m vs 4.0m (HR 0.65)."},

    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 van Driel HIPEC (van Driel trial)", "pharma": "NEJM 2018", "drug": "Surgery + HIPEC", 
     "results_short": "IDS 加溫：mOS 延長 12 個月 (HR 0.67)",
     "rationale": "術中加溫腹腔化療 (HIPEC) 強化對殘留微小病灶的穿透與殺傷力。",
     "regimen": "間歇減積手術 (IDS) 時同步加溫灌注 Cisplatin (100 mg/m2) 90 分鐘。",
     "outcomes": "mOS: 45.7m vs 33.9m (HR 0.67, 95% CI 0.48-0.94); mPFS HR 0.66."},

    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PSOC (Sensitive)"], "name": "📚 DESKTOP III", "pharma": "NEJM 2021", "drug": "Secondary Surgery", 
     "results_short": "二次手術價值：R0 切除 mOS 53.7m",
     "rationale": "證明嚴選患者 (AGO Score+) 二次手術能轉化為顯著 OS 獲益。",
     "regimen": "二次手術 (Secondary Cytoreduction) 接續鉑類複方化療。",
     "inclusion": ["首次鉑類敏感復發 (PFI > 6m)。", "AGO Score 陽性 (ECOG 0/大量腹水除外/R0潛力)。"],
     "outcomes": "ITT mOS: 53.7m vs 46.0m (HR 0.75); R0 完全切除者 mOS 達 61.9m."},

    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 LION", "pharma": "NEJM 2019", "drug": "No Lymphadenectomy", 
     "results_short": "臨床 LN 陰性免清掃：OS 無差異 (HR 1.06)",
     "outcomes": "mOS: 65.5m vs 69.2m (HR 1.06, P=0.65)。不建議臨床 LN(-) 者例行清掃。"},

    # ==========================
    # === Ongoing Trials (招募中) ===
    # ==========================
    {"cancer": "Ovarian", "name": "📍 FRAmework-01", "pharma": "Eli Lilly", "drug": "LY4170156 + Bevacizumab", "pos": "R-TX", "sub_pos": ["PROC (Resistant)", "PSOC (Sensitive)"], "type": "Ongoing",
     "pop_summary": "FRα ADC 併用 VEGF 抑制劑：跨組提升滲透與殺傷力。",
     "rationale": "透過 LY4170156 (FRα ADC) 精準標靶與 Bevacizumab 血管重塑作用產生協同效果。",
     "regimen": "Arm A (PROC): LY 3.0mg/kg + Bev 15mg/kg Q3W; Arm B (PSOC): LY 3.0mg/kg + Bev 15mg/kg Q3W; Arm C: 醫師選擇化療。",
     "inclusion": ["經中央檢測確認 FRα 表達陽性。", "最後鉑類後進展之 PROC 或 PSOC (PFI 6-12m)。"],
     "exclusion": ["曾用過針對 FRα 之 ADC。", "活動性間質性肺病 (ILD)。"]},

    {"cancer": "Ovarian", "name": "📍 REJOICE-Ovarian01", "pharma": "Daiichi Sankyo", "drug": "R-DXd", "pos": "R-TX", "sub_pos": ["PROC (Resistant)"], "type": "Ongoing",
     "rationale": "標靶 CDH6 ADC，具極高 DAR (8) 與強效旁觀者效應挑戰異質性 PROC。",
     "regimen": "Raludotatug deruxtecan 5.6mg/kg IV Q3W 直至進展。",
     "inclusion": ["組織學 HG Serous 或 Endometrioid PROC。", "提供切片判定 CDH6 分層。"]},

    {"cancer": "Endometrial", "name": "📍 MK2870-033", "pharma": "MSD", "drug": "Sac-TMT + Pembrolizumab", "pos": "P-MT", "sub_pos": ["Maintenance Therapy"], "type": "Ongoing",
     "rationale": "標靶 Trop-2 ADC 協同 PD-1。提升 Pembro 在 pMMR 或 NSMP 族群的應答深度。",
     "regimen": "Pembrolizumab 400mg Q6W + Sac-TMT 5mg/kg Q6W。",
     "inclusion": ["pMMR 子宮內膜癌 (中心檢測)。", "FIGO III/IV 一線含鉑+Pembro後達 CR/PR。"]},

    {"cancer": "Endometrial", "name": "📍 GU-US-682-6769", "pharma": "Gilead", "drug": "SG (Trodelvy)", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "type": "Ongoing",
     "rationale": "針對 Trop-2 ADC 利用 SN-38 載荷殺傷對抗鉑類與免疫失敗救援。",
     "regimen": "Sacituzumab govitecan 10mg/kg (Day 1, Day 8) Q21D。",
     "inclusion": ["復發性 EC (不含肉瘤)。", "鉑類與 PD-1 失敗後進展。"]},

    {"cancer": "Ovarian", "name": "📍 DOVE", "pharma": "GSK", "drug": "Dostarlimab + Bevacizumab", "pos": "R-TX", "sub_pos": ["PROC (Resistant)"], "type": "Ongoing",
     "rationale": "針對 OCCC 透明細胞癌利用雙重阻斷改善其特有免疫抑制微環境。",
     "regimen": "Dostarlimab 1000mg Q6W + Bevacizumab 15mg/kg Q3W。"},

    {"cancer": "Ovarian", "name": "📍 DS8201-772 (Enhertu)", "pharma": "AstraZeneca", "drug": "T-DXd", "pos": "P-MT", "sub_pos": ["BRCA / HRD path"], "type": "Ongoing",
     "rationale": "標靶 HER2 ADC 用於維持階段，清除 HER2 表現之微小殘留病灶。",
     "regimen": "T-DXd 5.4mg/kg IV Q3W。"},
]

# --- 3. AI 模型巡邏功能 ---
def get_gemini_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target_model = next((m for m in available_models if 'gemini-1.5-flash' in m), None)
        if not target_model: target_model = next((m for m in available_models if 'gemini-pro' in m), None)
        if target_model: return genai.GenerativeModel(target_model)
    except: return None

# --- 4. 側邊欄：患者分析助理 ---
with st.sidebar:
    st.markdown("<h3 style='color: #6A1B9A;'>🤖 AI 實證媒合助理</h3>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 患者病歷數據分析", expanded=True):
        p_notes = st.text_area("輸入摘要 (含分期/細胞/標記)", placeholder="例如：EC III期, p53 mutation, HER2 2+...", height=220)
        if st.button("🚀 開始分析"):
            if api_key and p_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = get_gemini_model()
                    prompt = f"分析病歷：{p_notes}。請參考實證庫：{all_trials_db}。建議適合路徑與理由。"
                    st.write(model.generate_content(prompt).text)
                except Exception as e: st.error(f"AI 異常: {e}")

# --- 5. 主頁面：導航地圖 ---
st.markdown("<div class='main-title'>婦癌臨床導航儀表板 (2026 旗艦極量整合版)</div>", unsafe_allow_html=True)
cancer_type = st.radio("第一步：選擇癌症類型", ["Endometrial", "Ovarian", "Cervical"], horizontal=True)

cols = st.columns(len(guidelines_nested[cancer_type]))
stages_data = guidelines_nested[cancer_type]

for i, stage in enumerate(stages_data):
    with cols[i]:
        st.markdown(f"""<div class='big-stage-card card-{stage['css']}'><div class='big-stage-header header-{stage['css']}'>{stage['header']}</div>""", unsafe_allow_html=True)
        for sub in stage['subs']:
            st.markdown(f"""<div class='sub-block'><div class='sub-block-title'>📘 {sub['title']}</div><div class='sub-block-content'>{sub['content']}</div>""", unsafe_allow_html=True)
            rel_trials = [t for t in (all_trials_db) if t["cancer"] == cancer_type and t["pos"] == stage["id"] and any(s in sub["title"] for s in t["sub_pos"])]
            for t in rel_trials:
                label = f"{t.get('pharma', 'N/A')} | {t['name']} | {t['drug']}"
                with st.popover(label, use_container_width=True):
                    st.success(f"**核心結論摘要:** {t.get('pop_results', t.get('results_short', '招募中'))}")
                    unique_key = f"sync_{t['name']}_{cancer_type}_{stage['id']}_{sub['title'].replace(' ', '')}"
                    if st.button("📊 同步看板細節", key=unique_key):
                        st.session_state.selected_trial = t['name']
                        st.rerun() # 強制同步刷新
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 6. 深度數據看板 (極量化資訊展示區) ---
st.divider()
st.subheader("📋 臨床研究極量化數據庫 (Published Milestones & Ongoing Trials)")
all_list = all_trials_db # 合併清單

# 根據目前選擇的癌症過濾選項
filtered_names = [t["name"] for t in all_list if t["cancer"] == cancer_type]

if not filtered_names:
    st.info("該癌症類別下無適用項目。")
else:
    try: curr_idx = filtered_names.index(st.session_state.selected_trial)
    except: curr_idx = 0

    selected_name = st.selectbox("🎯 快速選擇研究計畫以查閱詳細內容：", filtered_names, index=curr_idx, key="trial_selector")
    st.session_state.selected_trial = selected_name
    t = next(it for it in all_list if it["name"] == selected_name)

    st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #E0E0E0; padding-bottom:10px; font-weight:900;'>📋 {t['name']} 深度分析報告</h2>", unsafe_allow_html=True)

    r1, r2 = st.columns([1.3, 1])
    with r1:
        st.markdown("<div style='background:#E3F2FD; border-left:10px solid #1976D2; padding:15px; border-radius:10px;'><b>💉 Rationale & Regimen (機轉與分組給藥)</b></div>", unsafe_allow_html=True)
        st.write(f"**藥廠:** {t.get('pharma', 'N/A')}")
        st.write(f"**核心配方:** {t['drug']}")
        
        # 極量化給藥方案展示
        st.markdown("<div class='regimen-box'><b>詳細給藥方案 (Dosing Protocol):</b><br>" + t.get('regimen', '詳見 Protocol 具體劑量說明。') + "</div>", unsafe_allow_html=True)
        
        st.success(f"**科學理據 (Scientific Rationale):** {t.get('rationale', '旨在挑戰現有 SoC 瓶頸，提升存活獲益。')}")
        

    with r2:
        st.markdown("<div style='background:#FFF8E1; border-left:8px solid #FBC02D; padding:15px; border-radius:10px;'><b>📈 Key Outcomes (最新生存與緩解數據)</b></div>", unsafe_allow_html=True)
        st.markdown(f"""
            <div style='text-align:center; background:white; padding:15px; border:2px solid #FFE082; border-radius:12px;'>
                <div style='font-size: 14px; color: #795548; font-weight:700; margin-bottom:5px;'>Survival Metrics (PFS/OS/HR/ORR)</div>
                <div class='hr-big-val'>{t.get('outcomes', t.get('results', 'Ongoing Recruitment'))}</div>
            </div>
        """, unsafe_allow_html=True)
        

    st.divider()
    r3, r4 = st.columns(2)
    with r3:
        st.markdown("<div style='background:#E8F5E9; border-left:8px solid #2E7D32; padding:15px; border-radius:10px;'><b>✅ Inclusion Criteria (關鍵納入標準)</b></div>", unsafe_allow_html=True)
        for inc in t.get('inclusion', ['符合特定分子標記與分期規定。']): st.write(f"• **{inc}**")
    with r4:
        st.markdown("<div style='background:#FFEBEE; border-left:8px solid #C62828; padding:15px; border-radius:10px;'><b>❌ Exclusion Criteria (關鍵排除標準)</b></div>", unsafe_allow_html=True)
        for exc in t.get('exclusion', ['排除活動性自體免疫疾病或肺部纖維化史。']): st.write(f"• **{exc}**")
    st.markdown("</div>", unsafe_allow_html=True)
