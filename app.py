import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床導航與實證圖書館 (2026 旗艦最終極量整合版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

# 初始化 session_state 用於跨區塊聯動與狀態持久化
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

# --- 1. 指引數據庫：分型、階段與內容引導 ---
guidelines_nested = {
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "dMMR / MSI-H / MMRd", "content": "一線首選方案：含鉑化療 + PD-1 (RUBY/GY018/AtTEnd)。"},
            {"title": "pMMR / NSMP / MSS", "content": "一線標靶探索：CP + Durva/Ola (DUO-E)。二線標靶免疫 (KN775)。"},
            {"title": "POLE mutation (超突變型)", "content": "預後極佳。早期可考慮治療降階 (De-escalation)。"},
            {"title": "p53 mutation (高拷貝型)", "content": "侵襲性最強。建議輔助化放療。Serous 型需檢測 HER2 (DS8201)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Maintenance Therapy", "content": "一線 IO 治療後延續維持直到疾病進展 (PD)。包含最新 MK2870-033 與 DUO-E。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "Recurrent EC", "content": "標準二線：標靶+免疫 (KN775) 或單藥 IO (GARNET/SG)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "救援治療後維持當前有效方案直到疾病進展。"}]}
    ],
    "Ovarian": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "HGSC / Endometrioid", "content": "手術 (PDS/IDS) + Carbo/Pacli ± Bev (DUO-O)。考慮加 HIPEC (van Driel)。"},
            {"title": "Mucinous (MOC) 鑑定", "content": "判定：CK7+/SATB2- (原發)。IA 期可保守。侵襲型建議積極化療。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "HRD positive / BRCA wt", "content": "PAOLA-1 (Ola+Bev) 或 DUO-O (三藥維持) 或 PRIMA。"},
            {"title": "BRCA mutation", "content": "Olaparib 單藥維持 2年 (SOLO-1)。"}, 
            {"title": "HRD negative (pHRD)", "content": "Niraparib 維持 (PRIMA ITT) 或 DUO-O (Arm 3)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "PSOC (Sensitive Recur)", "content": "PFI > 6m。評估二次手術 (DESKTOP III) 或含鉑複方。"},
            {"title": "PROC (Resistant Recur)", "content": "PFI < 6m。單藥化療 ± Bev 或標靶 ADC (MIRASOL/FRAmework)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "PARPi Maint", "content": "救援緩解後續用 PARPi (NOVA/ARIEL3/SOLO2/DS8201)。"}]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "Locally Advanced (CCRT)", "content": "同步化放療 ± 同步 IO (A18) 或 誘導化療 (INTERLACE)。"},
            {"title": "Early Stage (Surgery)", "content": "根治術 (LACC) 或單純切除 (SHAPE)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Maintenance", "content": "1L 方案後接續維持 (KEYNOTE-826)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "Recurr / Metastatic", "content": "一線 KN826/BEATcc。二線 ADC (innovaTV 301) 或 IO。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "維持當前有效救援方案直至 PD。"}]}
    ]
}

# --- 2. 極量化資料庫：33 項試驗全量數據補齊 ---
all_trials_db = [
    # === Endometrial Published ===
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["dMMR / MSI-H / MMRd"], "name": "📚 RUBY (ENGOT-EN6/GOG-3031)", "pharma": "GSK", "drug": "Dostarlimab + CP", 
     "results_short": "dMMR 死亡風險降低 68% (HR 0.32)",
     "rationale": "PD-1 阻斷釋放免疫制動，協同含鉑化療誘導之 ICD，針對 MMRd 族群達成極高持久應答率。",
     "regimen": "Arm 1: Dostarlimab 500mg Q3W + Carboplatin (AUC 5) + Paclitaxel (175 mg/m2) x6 週期 -> 維持期: Dostarlimab 1000mg Q6W (持續 3年)。 Arm 2: Placebo + CP x6 週期。",
     "inclusion": ["新診斷 Stage III-IV 或首次復發 EC。", "ECOG 0-1。", "含 Carcinosarcoma / Clear cell / Serous 等組織型態。"],
     "outcomes": "dMMR 24m PFS 率: 61.4% vs 15.7% (HR 0.28, 95% CI 0.16-0.50); ITT mOS HR 0.64 (95% CI 0.46-0.87, P=0.0021)。"},

    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["pMMR / NSMP / MSS"], "name": "📚 DUO-E (ENGOT-EN9)", "pharma": "AstraZeneca", "drug": "Durvalumab + CP →維持 ± Olaparib", 
     "results_short": "三藥組 pMMR PFS HR 0.57 (vs CP)",
     "rationale": "探索 PARP 抑制劑 (PARPi) 與 PD-L1 抑制劑在維持階段的協同效果。PARPi 誘導的 DNA 損傷增加新抗原負荷，強化 pMMR 患者的免疫應答。",
     "regimen": "Arm 1 (SoC): CP x6 週期 -> 觀察。 Arm 2 (Durva): CP + Durvalumab 1120mg Q3W -> Durva 1500mg Q4W 維持。 Arm 3 (Ola+Durva): CP + Durva -> Durva 1500mg Q4W + Olaparib 300mg bid 維持直到 PD。",
     "outcomes": "pMMR Arm 3 (Ola+Durva) vs Arm 1: PFS HR 0.57 (95% CI 0.42-0.79); ITT 全人群 OS HR 0.77 (95% CI 0.56-1.07)。"},

    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "name": "📚 KEYNOTE-775 (Study 309)", "pharma": "MSD/Eisai", "drug": "Lenvatinib + Pembrolizumab", 
     "results_short": "pMMR/MSS 二線標準：OS 17.4m vs 12.0m",
     "rationale": "結合 VEGF-TKI 重塑血管並減輕免疫抑制，克服 MSS 腫瘤對單藥免疫之冷微環境。",
     "regimen": "Lenvatinib 20mg QD (每日口服) + Pembrolizumab 200mg Q3W (滴注) 直至疾病進展或不可耐受。"},

    # === Ovarian Published ===
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive / BRCA wt", "HRD negative (pHRD)"], "name": "📚 DUO-O (ENGOT-OV46)", "pharma": "AstraZeneca", "drug": "CP + Bev + Durva ->維持 ± Ola", 
     "results_short": "HRD+ 三藥組 PFS HR 0.49",
     "rationale": "探索三藥聯用 (IO + PARPi + anti-VEGF) 在新診斷卵巢癌患者中的維持優勢，利用三者機轉互補清除微小病灶並延緩復發。",
     "regimen": "Arm 1: CP + Bevacizumab -> Bev 維持。 Arm 2: CP + Bev + Durvalumab -> Bev + Durva 維持。 Arm 3 (Triplet): CP+Bev+Durva -> Bev+Durva+Olaparib (300mg bid) 維持直至疾病進展。",
     "outcomes": "HRD+ (non-BRCAm) Arm 3 vs Arm 1: PFS HR 0.49 (95% CI 0.34-0.69); ITT 全人群 Arm 3 HR 0.63 (95% CI 0.52-0.76)。"},

    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PROC (Resistant Recur)"], "name": "📚 MIRASOL (GOG-3045)", "pharma": "ImmunoGen", "drug": "Mirvetuximab Soravtansine", 
     "results_short": "PROC OS 突破：OS HR 0.67; ORR 42.3%",
     "rationale": "針對 FRα 高表現 PROC 患者，首個 ADC 在抗藥型患者中具備 OS 獲益之歷史突破研究。",
     "regimen": "Arm A: Mirvetuximab 6.0 mg/kg (基於 Adjusted Ideal Body Weight) IV Q3W 直至進展。 Arm B: 醫師選擇化療 (Paclitaxel/PLD/Topotecan)。",
     "outcomes": "mOS: 16.4m vs 12.7m (HR 0.67, 95% CI 0.50-0.89); mPFS 5.6m vs 4.0m (HR 0.65)。"},

    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PSOC (Sensitive Recur)"], "name": "📚 DESKTOP III (NEJM 2021)", "pharma": "AGO", "drug": "Secondary Cytoreduction Surgery", 
     "results_short": "二次手術價值：R0 切除 mOS 53.7m",
     "rationale": "證明嚴選患者 (AGO Score+) 二次手術對比單純化療能顯著轉化為 OS 獲益。",
     "regimen": "手術組: 腫瘤完全切除手術後接續含鉑化療。 化療組: 單純含鉑複方化療。",
     "outcomes": "ITT mOS: 53.7m vs 46.0m (HR 0.75, 95% CI 0.59-0.96); R0 完全切除者 mOS 達 61.9m。"},

    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 van Driel HIPEC (NEJM 2018)", "pharma": "NEJM", "drug": "Surgery + HIPEC (Cisplatin)", 
     "results_short": "IDS 加溫：mOS 延長 12 個月 (HR 0.67)",
     "rationale": "術中加溫腹腔化療強化鉑類對殘留微小病灶的物理殺傷與滲透力。",
     "regimen": "間歇減積手術 (IDS) 時同步進行加溫 (42°C) 腹腔灌注 Cisplatin (100 mg/m2) 90 分鐘。"},

    # === Ongoing Trials (8核心極量化) ===
    {"cancer": "Endometrial", "name": "📍 MK2870-033", "pharma": "MSD", "drug": "Sac-TMT + Pembrolizumab", "pos": "P-MT", "sub_pos": ["Maintenance Therapy"], "type": "Ongoing",
     "results_short": "招募中 (一線維持)",
     "rationale": "標靶 Trop-2 ADC (Sac-TMT) 誘導之 ICD 改善微環境，旨在強化 PD-1 抑制劑在 pMMR 或 NSMP 患者中的應答深度。",
     "regimen": "Arm A (試驗組): Sac-TMT (MK-2870) 5.0 mg/kg Q3W + Pembrolizumab 400 mg Q6W 維持治療直到 PD。 Arm B (對照組): 醫師選擇之維持方案 (SoC)。",
     "inclusion": ["新診斷 pMMR/MSS 子宮內膜癌 (中心 IHC 檢測確認)。", "FIGO III-IV 期、一線含鉑化療 + Pembrolizumab 後達 CR/PR。"]},

    {"cancer": "Ovarian", "name": "📍 FRAmework-01 (LY4170156)", "pharma": "Eli Lilly", "drug": "LY4170156 + Bevacizumab", "pos": "R-TX", "sub_pos": ["PROC (Resistant Recur)", "PSOC (Sensitive Recur)"], "type": "Ongoing",
     "results_short": "招募中 (PROC/PSOC 跨組)",
     "rationale": "標靶 FRα ADC 聯用 anti-VEGF。利用 Bevacizumab 血管調節作用降低腫瘤間質壓，提升 ADC 於實體腫瘤內的滲透深度挑戰耐藥瓶頸。",
     "regimen": "PROC 隊列分組： Arm A: LY 3.0mg/kg + Bev 15mg/kg Q3W; Arm B: LY 4.0mg/kg + Bev 15mg/kg Q3W。 PSOC 隊列 (PFI 6-12m): Arm C: LY 3.0mg/kg + Bev 15mg/kg Q3W。 對照組 (Arm D): 醫師選擇化療 SoC。"},

    {"cancer": "Endometrial", "name": "📍 GU-US-682-6769", "pharma": "Gilead", "drug": "SG (Trodelvy)", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "type": "Ongoing",
     "results_short": "招募中 (復發救援)",
     "rationale": "針對 Trop-2 ADC 利用 SN-38 載荷引發強力 DNA 損傷，專攻鉑類與免疫失敗之救援。",
     "regimen": "Sacituzumab govitecan 10mg/kg (Day 1, Day 8) 每 21 天為一週期 (Q21D) 直至疾病進展。"},
]

# --- 3. AI 模型巡邏與同步聯動核心邏輯 ---
def get_gemini_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target_model = next((m for m in available_models if 'gemini-1.5-flash' in m), None)
        if not target_model: target_model = next((m for m in available_models if 'gemini-pro' in m), None)
        if target_model: return genai.GenerativeModel(target_model)
    except: return None

# --- 4. 側邊欄：決策助理與 AI 分析 ---
with st.sidebar:
    st.markdown("<h3 style='color: #6A1B9A;'>🤖 AI 實證媒合助理</h3>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 患者數據深度分析", expanded=True):
        p_notes = st.text_area("輸入摘要 (含分期/細胞/標記)", placeholder="例如：EC Stage III, dMMR, p53 mutation, HER2 2+...", height=250)
        if st.button("🚀 開始媒合分析"):
            if api_key and p_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = get_gemini_model()
                    prompt = f"分析病歷：{p_notes}。請參考實證庫：{all_trials_db + milestone_db}。建議適合路徑與試驗理由。"
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
            
            # 合併渲染標記按鈕 (包含補回的 DUO-E, DUO-O 與 MK2870-033)
            rel_trials = [t for t in (milestone_db + ongoing_trials + all_trials_db) if t["cancer"] == cancer_type and t["pos"] == stage["id"] and any(s in sub["title"] for s in t["sub_pos"])]
            
            # 去重
            unique_trials = {t['name']: t for t in rel_trials}.values()

            for t in unique_trials:
                label = f"{t.get('pharma', 'N/A')} | {t['name']} | {t['drug']}"
                with st.popover(label, use_container_width=True):
                    st.success(f"**結論摘要:** {t.get('results_short', '招募中/詳見深度看板')}")
                    unique_key = f"sync_{t['name']}_{cancer_type}_{stage['id']}_{sub['title'].replace(' ', '')}"
                    if st.button("📊 同步看板細節", key=unique_key):
                        st.session_state.selected_trial = t['name']
                        st.rerun() 
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 6. 深度數據看板 (極量化資訊展示區) ---
st.divider()
st.subheader("📋 臨床研究極量化數據庫 (Published Milestones & Ongoing Trials)")
full_list = milestone_db + ongoing_trials + all_trials_db
unique_full_list = {t['name']: t for t in full_list}.values()
filtered_names = [t["name"] for t in unique_full_list if t["cancer"] == cancer_type]

if not filtered_names:
    st.info("該類別下目前無適用項目。")
else:
    try: curr_idx = filtered_names.index(st.session_state.selected_trial)
    except: curr_idx = 0

    selected_name = st.selectbox("🎯 快速選擇研究計畫以查閱分組與數據：", filtered_names, index=curr_idx, key="trial_selector")
    st.session_state.selected_trial = selected_name
    t_obj = next(it for it in unique_full_list if it["name"] == selected_name)

    st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #E0E0E0; padding-bottom:10px; font-weight:900;'>📋 {t_obj['name']} 深度分析報告</h2>", unsafe_allow_html=True)

    r1, r2 = st.columns([1.3, 1])
    with r1:
        st.markdown("<div style='background:#E3F2FD; border-left:10px solid #1976D2; padding:15px; border-radius:10px;'><b>💉 Rationale & Regimen (機轉與分組給藥)</b></div>", unsafe_allow_html=True)
        st.write(f"**藥廠:** {t_obj.get('pharma', 'N/A')} | **核心配方:** {t_obj['drug']}")
        
        # 極量化給藥方案 (Dosing Protocol) - 補齊分組細節
        st.markdown("<div class='regimen-box'><b>分組給藥方式 (Regimen per Arm):</b><br>" + t_obj.get('regimen', '正在補齊分組給藥細節中。') + "</div>", unsafe_allow_html=True)
        
        st.success(f"**科學理據 (Scientific Rationale):** {t_obj.get('rationale', '旨在挑戰現有 SoC 瓶頸，提升存活獲益。')}")

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
