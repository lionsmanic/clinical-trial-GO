import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床導航與實證圖書館 (2026 旗艦最終極量整合版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

# 初始化 session_state 用於聯動
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

    /* 圖一修復：大階段 Header 深色漸層，確保白色文字清晰 */
    .big-stage-card {
        border-radius: 10px; padding: 0px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: 2px solid transparent; background: white; margin-bottom: 4px; overflow: hidden;
    }
    .big-stage-header {
        font-size: 18px !important; font-weight: 900; color: white !important;
        padding: 8px; text-align: center; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }

    /* 階段配色飽和化 */
    .card-p-tx { border-color: #1B5E20; }
    .header-p-tx { background: linear-gradient(135deg, #2E7D32, #1B5E20); } /* 初治: 深綠 */
    .card-p-mt { border-color: #0D47A1; }
    .header-p-mt { background: linear-gradient(135deg, #1565C0, #0D47A1); } /* 維持: 深藍 */
    .card-r-tx { border-color: #E65100; }
    .header-r-tx { background: linear-gradient(135deg, #EF6C00, #BF360C); } /* 復發: 深橘紅 */
    .card-r-mt { border-color: #4A148C; }
    .header-r-mt { background: linear-gradient(135deg, #6A1B9A, #4A148C); } /* 復後維持: 深紫 */

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
    .hr-big-val { font-family: 'Roboto', sans-serif; font-size: 38px !important; font-weight: 900; color: #D84315; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 指引導航數據庫：全階段、精確分子分型、MOC/PSOC/PROC ---
guidelines_nested = {
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "dMMR / MSI-H / MMRd", "content": "一線首選方案：含鉑化療 + PD-1 (RUBY/GY018/AtTEnd)。"},
            {"title": "pMMR / NSMP / MSS", "content": "視 ER/Grade 權重決策；一線考慮 Chemo + 維持 (DUO-E)。二線標靶免疫 (KN775)。"},
            {"title": "POLE mutation (超突變)", "content": "預後極佳。早期可考慮治療降階 (De-escalation)，避免多餘毒性。"},
            {"title": "p53 mutation (高拷貝)", "content": "侵襲性最強。建議化放療積極併用介入。Serous 型需驗 HER2 (DS8201)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Maintenance Therapy", "content": "一線 IO 治療後延續維持直到疾病進展 (PD) (DUO-E/MK2870-033)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "Recurrent EC", "content": "標準二線：標靶+免疫 (MSS) 或 IO 單藥 (GARNET/MMRd/SG)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "救援治療後維持有效方案直至進展。"}]}
    ],
    "Ovarian": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "HGSC / Endometrioid", "content": "手術 (PDS/IDS) + Carbo/Pacli ± Bev。IDS 考慮加 HIPEC (van Driel)。"},
            {"title": "Mucinous (MOC) 鑑定", "content": "判定：CK7+/SATB2- (原發)。Expansile (預後佳) vs Infiltrative (易轉移)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "BRCA mutation", "content": "Olaparib 單藥維持 2年 (SOLO-1)。"}, 
            {"title": "HRD positive / BRCA wt", "content": "PAOLA-1 (Ola+Bev) 或 PRIMA (Nira)。"},
            {"title": "HRD negative", "content": "Niraparib 維持 (PRIMA ITT) 或 Bev。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "PSOC (Sensitive Recur)", "content": "PFI > 6m。評估二次手術 (DESKTOP III) 或含鉑複方化療。"},
            {"title": "PROC (Resistant Recur)", "content": "PFI < 6m。單藥化療 ± Bev 或標靶 ADC (MIRASOL/FRAmework)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "PARPi Maint", "content": "救援緩解後續用 PARPi (NOVA/ARIEL3/SOLO2/DS8201)。"}]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "Locally Advanced (CCRT)", "content": "同步化放療 ± 同步 IO (A18) 或 誘導化療 (INTERLACE)。"},
            {"title": "Early Stage (Surgery)", "content": "根治術 (LACC) 或單純切除 (SHAPE)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Maintenance Therapy", "content": "一線轉移性方案後續用 IO 維持 (KEYNOTE-826)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "Recurr / Metastatic", "content": "一線 Pembro+化療±Bev (KN826) 或 BEATcc。二線 ADC (innovaTV)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "維持當前有效方案直至進展。"}]}
    ]
}

# --- 2. 極量化資料庫：33 項試驗深度數據 (已發表 + 進行中) ---
all_trials_db = [
    # === Endometrial Milestones ===
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["dMMR / MSI-H / MMRd"], "name": "📚 RUBY (ENGOT-EN6)", "pharma": "GSK", "drug": "Dostarlimab + Carboplatin/Paclitaxel", 
     "pop_results": "dMMR 死亡風險降低 68% (HR 0.32)",
     "rationale": "PD-1 阻斷釋放免疫制動 (Immune checkpoint blockade)，協同化療誘發之免疫原性細胞死亡 (ICD)，針對 MMRd 族群達成極高反應。",
     "regimen": "Dostarlimab 500mg Q3W + CP x6 週期 -> 維持 Dostarlimab 1000mg Q6W 最長 3年。",
     "inclusion": ["新診斷 Stage III-IV 或首次復發之 EC。", "包含 Carcinosarcoma 組織學型態。"],
     "exclusion": ["先前接受過全身性抗癌治療。", "活動性自體免疫疾病。"],
     "outcomes": "dMMR: HR 0.32 (PFS); ITT 全人群 mOS 44.6m (vs 28.2m, HR 0.69)."},

    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["dMMR / MSI-H / MMRd", "pMMR / NSMP / MSS"], "name": "📚 NRG-GY018", "pharma": "MSD", "drug": "Pembrolizumab + Carboplatin/Paclitaxel", 
     "pop_results": "dMMR PFS HR 0.30; pMMR HR 0.54",
     "rationale": "支持一線不論 MMR 狀態之免疫介入生存獲益，重塑一線標準。",
     "regimen": "Pembrolizumab 200mg Q3W + CP x6 週期 -> 維持 400mg Q6W 最長 2年。",
     "outcomes": "dMMR PFS HR 0.30; pMMR PFS HR 0.54."},

    {"cancer": "Endometrial", "pos": "P-MT", "sub_pos": ["pMMR / NSMP / MSS"], "name": "📚 DUO-E", "pharma": "AZ", "drug": "Durvalumab + CP →維持 ± Olaparib", 
     "pop_results": "三藥組 pMMR PFS HR 0.57 (vs CP)",
     "rationale": "探索 PARP 抑制劑在 pMMR 族群免疫維持階段的協同增敏效應。",
     "outcomes": "pMMR 三藥組 (Durva+Ola) PFS HR 0.57; dMMR 單藥維持 HR 0.42."},

    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["dMMR / MSI-H / MMRd"], "name": "📚 AtTEnd (ENGOT-EN7)", "pharma": "Roche", "drug": "Atezolizumab + Carboplatin/Paclitaxel", 
     "pop_results": "dMMR PFS HR 0.36; ITT OS HR 0.82",
     "outcomes": "dMMR PFS HR 0.36; ITT OS HR 0.82 (P=0.048)。確認 PD-L1 併用價值。"},

    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "name": "📚 KEYNOTE-775 (Study 309)", "pharma": "MSD/Eisai", "drug": "Lenvatinib + Pembrolizumab", 
     "pop_results": "pMMR OS HR 0.68; mOS 17.4m",
     "rationale": "標靶 VEGF-TKI 重塑腫瘤微環境，克服 MSS 腫瘤對免疫治療的冷微環境。",
     "regimen": "Lenvatinib 20mg QD + Pembrolizumab 200mg Q3W。",
     "outcomes": "pMMR: OS HR 0.68; mOS 17.4m (vs 12.0m)."},

    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "name": "📚 GARNET", "pharma": "GSK", "drug": "Dostarlimab 單藥", 
     "pop_results": "dMMR ORR 45.5%",
     "outcomes": "dMMR ORR 45.5%; DOR 未達到。"},

    # === Cervical Milestones ===
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Locally Advanced (CCRT)"], "name": "📚 KEYNOTE-A18 (ENGOT-cx11)", "pharma": "MSD", "drug": "Pembrolizumab + CCRT", 
     "pop_results": "36個月 OS 率提升至 82.6% (HR 0.67)",
     "rationale": "將免疫整合入高風險局部晚期之根治標準。",
     "regimen": "Cisplatin + RT 同步 Pembro 200mg Q3W -> 維持 400mg Q6W。"},

    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Locally Advanced (CCRT)"], "name": "📚 INTERLACE", "pharma": "UCL", "drug": "Induction Carbo/Pacli x6 -> CCRT", 
     "pop_results": "5年 OS 率 80% (vs 72%, HR 0.60)",
     "rationale": "利用誘導化療解決根治性放療前的微小轉移病灶。"},

    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Locally Advanced (CCRT)"], "name": "📚 CALLA", "pharma": "AZ", "drug": "Durvalumab + CCRT", 
     "pop_results": "陰性結果 (HR 0.84)",
     "outcomes": "PFS HR 0.84 (P=NS)。提醒組合放化療之複雜度。"},

    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 KEYNOTE-826", "pharma": "MSD", "drug": "Pembrolizumab + Chemo ± Bev", 
     "pop_results": "R/M 一線黃金標準：全人群死亡風險降 37%",
     "outcomes": "OS HR 0.63 (ITT); HR 0.60 (CPS≥1)."},

    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 BEATcc (ENGOT-Cx10)", "pharma": "Roche", "drug": "Atezolizumab + Chemo + Bev", 
     "pop_results": "PFS 13.7m vs 10.4m (HR 0.62)",
     "outcomes": "PFS HR 0.62; OS HR 0.68."},

    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 EMPOWER-Cervical 1", "pharma": "Regeneron", "drug": "Cemiplimab", 
     "pop_results": "二線免疫 OS 基石：OS 12.0m vs 8.5m",
     "outcomes": "OS HR 0.69; mOS 12.0m."},

    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 innovaTV 301 (ENGOT-cx12)", "pharma": "Genmab", "drug": "Tisotumab Vedotin (ADC)", 
     "pop_results": "後線 ADC 突破：OS HR 0.70; ORR 17.8%",
     "rationale": "標靶組織因子 (Tissue Factor) ADC，解決後線化療耐藥性。"},

    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Early Stage (Surgery)"], "name": "📚 SHAPE trial", "pharma": "CCTG", "drug": "Simple Hysterectomy", 
     "pop_results": "低風險降階：3年復發率 2.5% vs 2.2%",
     "outcomes": "3yr Recurrence: 2.5% vs 2.2% (HR 1.0)。"},

    # === Ovarian Milestones ===
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutation"], "name": "📚 SOLO-1", "pharma": "AZ", "drug": "Olaparib 維持", 
     "pop_results": "7年存活率 67% (HR 0.33)",
     "rationale": "利用 PARP 抑制劑合成致死機制，延長一線維持生存期。"},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive / BRCA wt", "HRD negative"], "name": "📚 PRIMA (ENGOT-OV26)", "pharma": "GSK", "drug": "Niraparib 維持", 
     "pop_results": "全人群一線維持：HRD+ PFS HR 0.43",
     "outcomes": "HRD+ PFS HR 0.43; ITT HR 0.62."},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive / BRCA wt"], "name": "📚 PAOLA-1 (ENGOT-ov25)", "pharma": "AZ", "drug": "Olaparib + Bevacizumab", 
     "pop_results": "HRD+ 5年 OS 率 75.2% (HR 0.62)",
     "rationale": "確立 PARPi 與 anti-VEGF 於 HRD+ 患者之組合路徑。"},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutation", "HRD positive / BRCA wt"], "name": "📚 ATHENA–MONO", "pharma": "Clovis", "drug": "Rucaparib 維持", 
     "results": "ITT PFS HR 0.52 (28.7m vs 11.3m)."},

    {"cancer": "Ovarian", "pos": "PR-Maint", "sub_pos": ["PARPi Maint"], "name": "📚 NOVA", "pharma": "GSK", "drug": "Niraparib 復發維持", 
     "pop_results": "復發維持基石：gBRCA HR 0.27",
     "outcomes": "gBRCA HR 0.27; non-gBRCA HR 0.45."},

    {"cancer": "Ovarian", "pos": "PR-Maint", "sub_pos": ["PARPi Maint"], "name": "📚 ARIEL3", "pharma": "Clovis", "drug": "Rucaparib 復發維持", 
     "pop_results": "HRD+ PFS HR 0.32",
     "outcomes": "BRCAm HR 0.23; HRD+ HR 0.32."},

    {"cancer": "Ovarian", "pos": "PR-Maint", "sub_pos": ["PARPi Maint"], "name": "📚 SOLO2", "pharma": "AZ", "drug": "Olaparib 復發維持", 
     "pop_results": "BRCAm 長期 OS：mOS 51.7m (HR 0.74)",
     "outcomes": "mOS 51.7m vs 38.8m."},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive / BRCA wt"], "name": "📚 DUO-O", "pharma": "AZ", "drug": "Durva+Ola+Bev 維持", 
     "pop_results": "免疫組合潛力：HRD+ PFS HR 0.49",
     "outcomes": "HRD+ PFS HR 0.49."},

    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PROC (Resistant Recur)"], "name": "📚 MIRASOL", "pharma": "ImmunoGen", "drug": "Mirvetuximab Soravtansine", 
     "pop_results": "PROC OS 突破：OS HR 0.67; ORR 42.3%",
     "rationale": "首個證明 FRα ADC 在抗藥型患者中有生存獲益的研究。",
     "outcomes": "mOS 16.4m vs 12.7m (HR 0.67); ORR 42.3%。"},

    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 HIPEC (van Driel)", "pharma": "NEJM 2018", "drug": "Surgery + HIPEC", 
     "pop_results": "IDS 手術加溫：mOS 延長 12 個月 (HR 0.67)",
     "rationale": "加溫化療強化腹膜微小病灶殺傷。",
     "outcomes": "mOS 45.7m vs 33.9m."},

    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PSOC (Sensitive Recur)"], "name": "📚 DESKTOP III", "pharma": "NEJM 2021", "drug": "Secondary Surgery", 
     "pop_results": "二次手術價值：R0 切除者 mOS 53.7m",
     "rationale": "證明嚴選患者二次減積手術具 OS 獲益。",
     "outcomes": "mOS 53.7m (vs 46.0m, HR 0.75)。"},

    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 LION", "pharma": "NEJM 2019", "drug": "No Lymphadenectomy", 
     "pop_results": "臨床 LN 陰性免清掃：OS 無差異 (HR 1.06)",
     "outcomes": "OS HR 1.06."},

    # === 📍 Ongoing Trials (救援 8 核心) ===
    {"cancer": "Ovarian", "name": "📍 FRAmework-01", "pharma": "Eli Lilly", "drug": "LY4170156 + Bevacizumab", "pos": "R-TX", "sub_pos": ["PROC (Resistant Recur)", "PSOC (Sensitive Recur)"], "type": "Ongoing",
     "pop_summary": "FRα ADC 併用血管新生抑制劑：跨組提升滲透與殺傷力。",
     "rationale": "標靶 FRα ADC 聯用 anti-VEGF 產生血管重塑協同作用，提升藥物滲透深度挑戰耐藥瓶頸。",
     "regimen": "LY4170156 3mg/kg IV + Bevacizumab 15mg/kg IV Q3W。",
     "inclusion": ["經檢測 FRα 表達陽性。", "最後一劑鉑類後進展之 PROC 或 PSOC (PFI > 90d)。"],
     "exclusion": ["曾用過 Topo I ADC。", "活動性間質性肺病 (ILD)。"]},

    {"cancer": "Ovarian", "name": "📍 REJOICE-Ovarian01", "pharma": "Daiichi Sankyo", "drug": "R-DXd", "pos": "R-TX", "sub_pos": ["PROC (Resistant Recur)"], "type": "Ongoing",
     "rationale": "標靶 CDH6 ADC，具強力旁觀者效應挑戰異質性 PROC。",
     "inclusion": ["HG Serous 或 Endometrioid PROC。", "提供切片判定 CDH6。"]},

    {"cancer": "Endometrial", "name": "📍 MK2870-033", "pharma": "MSD", "drug": "Sac-TMT + Pembrolizumab", "pos": "P-MT", "sub_pos": ["Maintenance Therapy"], "type": "Ongoing",
     "rationale": "標靶 Trop-2 ADC 協同 PD-1。提升 Pembro 在 pMMR 或 NSMP 族群的應答。",
     "inclusion": ["pMMR 子宮內膜癌 (中心檢測)。", "FIGO III/IV 一線含鉑+Pembro後達 CR/PR。"]},

    {"cancer": "Endometrial", "name": "📍 GU-US-682-6769", "pharma": "Gilead", "drug": "SG (Trodelvy)", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "type": "Ongoing",
     "rationale": "針對 Trop-2 ADC 利用 SN-38 Payload 對抗鉑類與免疫失敗救援。",
     "inclusion": ["復發性 EC。", "鉑類與 PD-1 失敗後進展。"]},

    {"cancer": "Ovarian", "name": "📍 DOVE", "pharma": "GSK", "drug": "Dostarlimab + Bevacizumab", "pos": "R-TX", "sub_pos": ["PROC (Resistant Recur)"], "type": "Ongoing",
     "rationale": "針對 OCCC 透明細胞癌利用雙重阻斷改善微環境。"},

    {"cancer": "Ovarian", "name": "📍 DS8201-772 (Enhertu)", "pharma": "AstraZeneca", "drug": "T-DXd", "pos": "P-MT", "sub_pos": ["BRCA / HRD path"], "type": "Ongoing",
     "rationale": "標靶 HER2 ADC 用於一線維持，清除微小殘留病灶。"},
]

# --- 3. AI 模型巡邏 ---
def get_gemini_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target_model = next((m for m in available_models if 'gemini-1.5-flash' in m), None)
        if not target_model: target_model = next((m for m in available_models if 'gemini-pro' in m), None)
        if target_model: return genai.GenerativeModel(target_model)
    except: return None

# --- 4. 側邊欄：患者分析與 AI ---
with st.sidebar:
    st.markdown("<h3 style='color: #6A1B9A;'>🤖 AI 實證媒合助理</h3>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 患者數據深度分析", expanded=True):
        p_notes = st.text_area("輸入摘要 (含分期/標記/細胞型態)", placeholder="例如：EC III期, p53 mutation, dMMR...", height=220)
        if st.button("🚀 開始媒合分析"):
            if api_key and p_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = get_gemini_model()
                    prompt = f"分析病歷：{p_notes}。請參考：{all_trials_db}。建議適合路徑與理由。"
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
            
            # 顯示對應試驗
            rel_trials = [t for t in all_trials_db if t["cancer"] == cancer_type and t["pos"] == stage["id"] and any(s in sub["title"] for s in t["sub_pos"])]
            for t in rel_trials:
                label = f"{t.get('pharma', 'N/A')} | {t['name']} | {t['drug']}"
                with st.popover(label, use_container_width=True):
                    st.success(f"**核心結論摘要:** {t.get('pop_results', t.get('pop_summary', '招募中'))}")
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

selected_name = st.selectbox("🎯 快速選擇研究計畫以查閱理據與生存數據：", [t["name"] for t in filtered_list], index=curr_idx, key="trial_selector")
st.session_state.selected_trial = selected_name
t = next(it for it in all_trials_db if it["name"] == selected_name)

st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #E0E0E0; padding-bottom:10px; font-weight:900;'>📋 {t['name']} 深度分析報告</h2>", unsafe_allow_html=True)

r1, r2 = st.columns([1.3, 1])
with r1:
    st.markdown("<div style='background:#E3F2FD; border-left:10px solid #1976D2; padding:15px; border-radius:10px;'><b>💉 Rationale & Regimen (機轉與給藥)</b></div>", unsafe_allow_html=True)
    st.write(f"**核心配方:** {t['drug']}")
    st.write(f"**詳細給藥方案 (Regimen Details):** {t.get('regimen', '請查閱特定試驗分組劑量說明。')}")
    st.success(f"**科學理據 (Scientific Rationale):** {t.get('rationale', '旨在挑戰現有 SoC 瓶頸，提升存活獲益。')}")
    

with r2:
    st.markdown("<div style='background:#FFF8E1; border-left:8px solid #FBC02D; padding:15px; border-radius:10px;'><b>📈 Key Outcomes (生存與緩解數據)</b></div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style='text-align:center; background:white; padding:15px; border:2px solid #FFE082; border-radius:12px;'>
            <div style='font-size: 14px; color: #795548; font-weight:700; margin-bottom:5px;'>Survival Metrics (PFS/OS/HR/ORR)</div>
            <div class='hr-big-val'>{t.get('results', t.get('outcomes', 'Ongoing Recruitment'))}</div>
        </div>
    """, unsafe_allow_html=True)
    

st.divider()
r3, r4 = st.columns(2)
with r3:
    st.markdown("<div style='background:#E8F5E9; border-left:8px solid #2E7D32; padding:15px; border-radius:10px;'><b>✅ Inclusion Criteria (關鍵納入標準)</b></div>", unsafe_allow_html=True)
    for inc in t.get('inclusion', ['符合分子標記分型與前線治療規定。']): st.write(f"• **{inc}**")
with r4:
    st.markdown("<div style='background:#FFEBEE; border-left:8px solid #C62828; padding:15px; border-radius:10px;'><b>❌ Exclusion Criteria (關鍵排除標準)</b></div>", unsafe_allow_html=True)
    for exc in t.get('exclusion', ['排除顯著臟器功能異常或活動性肺部疾病史。']): st.write(f"• **{exc}**")
st.markdown("</div>", unsafe_allow_html=True)
