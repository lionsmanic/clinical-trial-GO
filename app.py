import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床導航與實證圖書館 (2026 旗艦最終整合版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

# 初始化 session_state 用於聯動
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = "📚 RUBY"

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=Roboto:wght@400;700;900&display=swap');
    
    /* === UI 高對比度與緊緻化 === */
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', 'Roboto', sans-serif;
        background-color: #F4F7F9; color: #1A1A1A;
        font-size: 19px !important; line-height: 1.1;
    }

    .main-title {
        font-size: 32px !important; font-weight: 900; color: #004D40;
        padding: 5px 0; border-bottom: 3px solid #4DB6AC; margin-bottom: 5px;
    }

    /* 階段方塊：修正背景色對比度，確保標題可讀 */
    .big-stage-card {
        border-radius: 10px; padding: 0px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: 2px solid transparent; background: white; 
        margin-bottom: 4px; overflow: hidden; height: auto !important;
    }
    .big-stage-header {
        font-size: 18px !important; font-weight: 900; color: white !important;
        padding: 8px; text-align: center; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }

    /* 配色強化 */
    .card-p-tx { border-color: #1B5E20; }
    .header-p-tx { background: linear-gradient(135deg, #2E7D32, #1B5E20); } /* 深綠 */
    .card-p-mt { border-color: #0D47A1; }
    .header-p-mt { background: linear-gradient(135deg, #1565C0, #0D47A1); } /* 深藍 */
    .card-r-tx { border-color: #E65100; }
    .header-r-tx { background: linear-gradient(135deg, #EF6C00, #BF360C); } /* 深橘紅 */
    .card-r-mt { border-color: #4A148C; }
    .header-r-mt { background: linear-gradient(135deg, #6A1B9A, #4A148C); } /* 深紫 */

    .sub-block {
        margin: 2px 4px; padding: 4px; border-radius: 6px; 
        background: #F8F9FA; border-left: 5px solid #455A64;
    }
    .sub-block-title {
        font-size: 14px; font-weight: 900; color: #263238;
        margin-bottom: 1px; border-bottom: 1.1px solid #CFD8DC; padding-bottom: 1px;
    }

    /* 按鈕：深黑色加粗 (#1A1A1A) */
    .stPopover button { 
        font-weight: 900 !important; font-size: 11px !important; 
        border-radius: 4px !important; margin-top: 1px !important;
        padding: 1px 6px !important; width: 100% !important; 
        text-align: left !important; color: #1A1A1A !important; 
        border: 1px solid rgba(0,0,0,0.15) !important;
    }
    
    .stPopover button[aria-label*="📚"] { background: #ECEFF1 !important; border-left: 5px solid #455A64 !important; }
    .stPopover button[aria-label*="📍"] { background: #E1F5FE !important; border-left: 5px solid #0288D1 !important; } 

    .detail-section { background: white; border-radius: 18px; padding: 25px; border: 1px solid #CFD8DC; box-shadow: 0 10px 40px rgba(0,0,0,0.05); }
    .hr-big-val { font-family: 'Roboto', sans-serif; font-size: 38px !important; font-weight: 900; color: #D84315; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 指引導航數據庫：包含全癌症精確分型 ---
guidelines_nested = {
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "MMRd / MSI-H / dMMR", "content": "一線首選：含鉑化療併用 PD-1 抑制劑 (RUBY/GY018)。"},
            {"title": "pMMR / NSMP / MSS", "content": "排除分型。視 ER/Grade 決策；一線加維持 (DUO-E)。"},
            {"title": "POLE mutation (超突變)", "content": "預後極佳，早期可降階治療；晚期仍屬 rare。"},
            {"title": "p53 mutation (高拷貝)", "content": "預後最差。建議化放療積極介入。Serous 型需驗 HER2。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "IO Maintenance", "content": "一線 IO 治療後延續維持至 PD。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "Recurrent EC", "content": "標靶+免疫 (pMMR) 或單藥 IO (MMRd/GARNET)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "維持有效治療直到 PD。"}]}
    ],
    "Ovarian": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "HGSC / Endometrioid", "content": "手術 (PDS/IDS) + Carbo/Pacli ± Bev。IDS 考慮 HIPEC。"},
            {"title": "Mucinous (MOC) 鑑別", "content": "鑑定：CK7+/SATB2-。1. Expansile (IA可保守)。 2. Infiltrative (建積極化療)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "BRCA mutation", "content": "Olaparib 單藥維持 2年 (SOLO-1)。"}, 
            {"title": "HRD positive / BRCA wt", "content": "PAOLA-1 (Ola+Bev) 或 PRIMA (Nira)。"},
            {"title": "HRD negative (pHRD)", "content": "Niraparib 維持 (PRIMA ITT) 或 Bev。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "PSOC (Sensitive)", "content": "PFI > 6m。評估二次手術 (DESKTOP III) 或含鉑雙藥。"},
            {"title": "PROC (Resistant)", "content": "PFI < 6m。單藥化療 ± Bev 或 FRα ADC (MIRASOL)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Platinum Sensitive Maint", "content": "救援緩解後選 PARPi 維持 (NOVA/ARIEL3/SOLO2)。"}]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "Locally Advanced (CCRT)", "content": "同步化放療 ± IO (A18) 或 誘導化療 (INTERLACE)。"},
            {"title": "Early Stage (Surgery)", "content": "根治術 (LACC) 或單純切除 (SHAPE)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "Recurr / Metastatic", "content": "一線 Pembro+化療±Bev (KN826) 或 Atezo組合 (BEATcc)。二線 ADC。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "維持當前有效方案直到進展。"}]}
    ]
}

# --- 2. 全量實證資料庫 (25項全數歸納) ---
trials_db = [
    # --- Endometrial Milestones ---
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H / dMMR"], "name": "📚 RUBY", "pharma": "GSK", "drug": "Dostarlimab + CP", 
     "pop_results": "dMMR 死亡風險降 68% (HR 0.32)",
     "rationale": "透過 PD-1 阻斷 (PD-1 blockade) 釋放免疫制動，協同化療誘導的免疫原性細胞死亡 (ICD)，旨在提高晚期或復發內膜癌的長期存活率。",
     "regimen": "Dostarlimab 500mg Q3W + CP x6 週期 -> 維持 Dostarlimab 1000mg Q6W 最長 3年。",
     "inclusion": ["FIGO III-IV 期或首次復發之子宮內膜癌 (EC)。", "包含癌肉瘤 (Carcinosarcoma) 組織型態。"],
     "exclusion": ["先前接受過系統性抗癌治療。", "活動性自體免疫疾病。"],
     "outcomes": "dMMR PFS HR 0.32; mOS 44.6m (vs 28.2m)."},

    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["pMMR / NSMP / MSS"], "name": "📚 DUO-E", "pharma": "AZ", "drug": "Durvalumab + CP →維持 ± Ola", 
     "pop_results": "三藥組 PFS HR 0.57 (vs CP)",
     "rationale": "探索 PARP 抑制劑與免疫檢查點抑制劑 (ICI) 在 pMMR 患者中是否具有協同維持效益 (Synergy)。",
     "regimen": "Durvalumab + CP -> 維持 Durvalumab + Olaparib 300mg bid。",
     "inclusion": ["新診斷晚期或復發 EC。", "提供 MMR 檢測報告。"],
     "exclusion": ["先前用過 PARPi 或 IO。"],
     "outcomes": "pMMR Cohort: PFS HR 0.57 (Ola+Durva vs CP)."},

    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "name": "📚 KEYNOTE-775", "pharma": "MSD/Eisai", "drug": "Lenvatinib + Pembro", 
     "pop_results": "pMMR OS 17.4m vs 12.0m",
     "rationale": "結合抗血管新生 (VEGF-TKI) 與免疫抑制劑，重塑腫瘤微環境，克服 MSS 患者對免疫治療的耐藥性。",
     "regimen": "Lenvatinib 20mg qd + Pembrolizumab 200mg Q3W。",
     "inclusion": ["含鉑治療後進展之晚期 EC。", "不論 MMR 狀態 (重點在 pMMR)。"],
     "exclusion": ["顯著心血管疾病。", "臨床活動性腸阻塞。"],
     "outcomes": "pMMR: OS HR 0.68; mOS 17.4m. 確立二線標準。"},

    # --- Ovarian Milestones ---
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutation"], "name": "📚 SOLO-1", "pharma": "AZ", "drug": "Olaparib Maint", 
     "pop_results": "7年 OS 率 67% (HR 0.33)",
     "rationale": "利用 PARP 抑制劑的合成致死 (Synthetic Lethality) 機制，精準打擊 BRCA 缺失之癌細胞，延緩一線復發。",
     "regimen": "Olaparib 300mg bid 維持 2年。",
     "inclusion": ["新診斷 FIGO III-IV 期、BRCAm、含鉑化療反應者。"],
     "exclusion": ["先前用過 PARPi。"],
     "outcomes": "PFS HR 0.30; 7yr Survival 67% (vs 46.5%)."},

    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PROC (Resistant)"], "name": "📚 MIRASOL", "pharma": "ImmunoGen", "drug": "Mirvetuximab", 
     "pop_results": "OS 16.4m (vs 12.7m, HR 0.67)",
     "rationale": "標靶葉酸受體 alpha (FRα) 之 ADC，精準輸送類微管蛋白載荷殺傷鉑類抗藥型 (PROC) 細胞。",
     "regimen": "Mirvetuximab 6.0 mg/kg (AIBW) IV Q3W。",
     "inclusion": ["FRα 高表達 (≥75% IHC 3+)。", "1-3 線前線治療後之 PROC。"],
     "exclusion": ["曾用過針對 FRα 之 ADC。", "顯著角膜病變。"],
     "outcomes": "OS HR 0.67; ORR 42.3%. 首個 PROC OS 獲益研究。"},

    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 HIPEC (van Driel)", "pharma": "NEJM 2018", "drug": "Surgery + HIPEC", 
     "pop_results": "mOS 延長 12 個月 (HR 0.67)",
     "rationale": "間歇減積手術 (IDS) 時同步加熱腹腔化療，強化鉑類對微小殘留病灶之殺傷。",
     "regimen": "IDS 手術結束前灌注 Cisplatin (100 mg/m²) 溫熱化療 90 分鐘。",
     "inclusion": ["Stage III 期上皮性卵巢癌。", "接受 NACT 且符合 IDS 條件。"],
     "exclusion": ["先前接受過腹膜切除術。"],
     "outcomes": "mOS 45.7m vs 33.9m (HR 0.67)."},

    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PSOC (Sensitive)"], "name": "📚 DESKTOP III", "pharma": "NEJM 2021", "drug": "Secondary Debulking", 
     "pop_results": "mOS 53.7m (vs 46.0m, HR 0.75)",
     "rationale": "評估二次減積手術在鉑類敏感型復發患者中的生存獲益。",
     "regimen": "Secondary Cytoreduction + Chemo vs Chemo alone。",
     "inclusion": ["首次鉑敏復發 (PFI > 6m)。", "AGO Score 陽性 (完全切除可能性高者)。"],
     "exclusion": ["廣泛轉移無法達成 R0 者。"],
     "outcomes": "mOS 53.7m vs 46.0m. 必須達成完全切除才有 OS 獲益。"},
]

# --- 3. 招募中計畫 (8核心) ---
ongoing_trials = [
    {"cancer": "Ovarian", "name": "📍 FRAmework-01", "pharma": "Eli Lilly", "drug": "LY4170156 + Bevacizumab", "pos": "R-TX", "sub_pos": ["PROC (Resistant)"], 
     "rationale": "FRα ADC 協同 anti-VEGF 血管調節，提升藥物在腫瘤內的滲透深度。",
     "inclusion": ["FRα IHC 陽性。", "最後鉑類後 90-180 天內進展之 PROC。"],
     "exclusion": ["曾用過 Topo I ADC。", "活動性 ILD。"], "outcomes": "Phase 3 Recruitment ongoing."},
    {"cancer": "Ovarian", "name": "📍 REJOICE-Ovarian01", "pharma": "Daiichi Sankyo", "drug": "R-DXd", "pos": "R-TX", "sub_pos": ["PROC (Resistant)"], 
     "rationale": "標靶 CDH6 ADC，具強力旁觀者效應解決高度異質性之 PROC。",
     "inclusion": ["HG Serous 或 Endometrioid PROC。", "提供 CDH6 分層檢體。"],
     "exclusion": ["Low-grade 腫瘤。", "LVEF < 50%。"], "outcomes": "Ongoing (NCT06161025)."}
]

# --- 4. 動態模型與 AI 選擇器 ---
def get_gemini_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target_model = next((m for m in available_models if 'gemini-1.5-flash' in m), None)
        if not target_model:
            target_model = next((m for m in available_models if 'gemini-pro' in m), None)
        if target_model: return genai.GenerativeModel(target_model)
    except: return None

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
            
            # 合併 Published & Ongoing 進行區塊顯示
            rel_trials = [t for t in (trials_db + ongoing_trials) if t["cancer"] == cancer_type and t["pos"] == stage["id"] and any(s in sub["title"] for s in t["sub_pos"])]
            for t in rel_trials:
                label = f"{t.get('pharma', 'N/A')} | {t['name']} | {t['drug']}"
                with st.popover(label, use_container_width=True):
                    st.success(f"**核心結論:** {t.get('pop_results', '招募中')}")
                    unique_key = f"sync_{t['name']}_{cancer_type}_{stage['id']}_{sub['title'].replace(' ', '')}"
                    if st.button("📊 同步看板細節", key=unique_key):
                        st.session_state.selected_trial = t['name']
                        st.rerun() # 圖四修復：強制 rerun 以聯動
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 6. 臨床試驗深度數據庫 (同步清單) ---
st.divider()
st.subheader("📋 臨床研究深度數據庫 ( Published Milestones & Ongoing Trials )")
all_list = trials_db + ongoing_trials
filtered_names = [t["name"] for t in all_list if t["cancer"] == cancer_type]

try: current_idx = filtered_names.index(st.session_state.selected_trial)
except: current_idx = 0

selected_name = st.selectbox("🎯 快速選擇研究以查閱詳細內容：", filtered_names, index=current_idx, key="trial_selector")
st.session_state.selected_trial = selected_name # 保持雙向一致性

# 抓取選中對象
t = next((it for it in all_list if it["name"] == selected_name), all_list[0])

st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #E0E0E0; padding-bottom:10px; font-weight:900;'>📋 {t['name']} 深度分析報告</h2>", unsafe_allow_html=True)

r1, r2 = st.columns([1.3, 1])
with r1:
    st.markdown("<div style='background:#E3F2FD; border-left:10px solid #1976D2; padding:15px; border-radius:10px;'><b>💉 Rationale & Regimen (理據與給藥)</b></div>", unsafe_allow_html=True)
    st.write(f"**核心配方:** {t['drug']}")
    st.write(f"**給藥細節 (Protocol):** {t.get('regimen', '詳見招募細則。')}")
    st.success(f"**科學理據 (Rationale):** {t['rationale']}")
    

with r2:
    st.markdown("<div style='background:#FFF8E1; border-left:8px solid #FBC02D; padding:15px; border-radius:10px;'><b>📈 Key Evidence (實證數據摘要)</b></div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style='text-align:center; background:white; padding:15px; border:2px solid #FFE082; border-radius:12px;'>
            <div style='font-size: 14px; color: #795548; font-weight:700; margin-bottom:5px;'>Survival Metrics (PFS/OS/HR)</div>
            <div class='hr-big-val'>{t.get('outcomes', 'Ongoing Recruitment')}</div>
        </div>
    """, unsafe_allow_html=True)
    

st.divider()
r3, r4 = st.columns(2)
with r3:
    st.markdown("<div style='background:#E8F5E9; border-left:8px solid #2E7D32; padding:15px; border-radius:10px;'><b>✅ Inclusion Criteria (納入條件)</b></div>", unsafe_allow_html=True)
    for inc in t.get('inclusion', ['詳見全文。']): st.write(f"• **{inc}**")
with r4:
    st.markdown("<div style='background:#FFEBEE; border-left:8px solid #C62828; padding:15px; border-radius:10px;'><b>❌ Exclusion Criteria (排除標準)</b></div>", unsafe_allow_html=True)
    for exc in t.get('exclusion', ['詳見全文。']): st.write(f"• **{exc}**")
st.markdown("</div>", unsafe_allow_html=True)
