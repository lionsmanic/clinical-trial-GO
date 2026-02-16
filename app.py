import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床導航與實證圖書館 (2026 最終旗艦整合版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

# 初始化聯動狀態
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

    /* 階段方塊：深色漸層背景確保標題清晰 */
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

# --- 1. 指引導航數據庫：包含精確分子分型 ---
guidelines_nested = {
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "dMMR / MSI-H", "content": "首選方案：Chemo + PD-1 (RUBY/GY018/AtTEnd)。"},
            {"title": "pMMR / NSMP / MSS", "content": "預後取決於 ER/Grade。二線考慮標靶免疫 (KN775)。"},
            {"title": "POLE mutation", "content": "預後極佳。早期降階治療；晚期 Rare。"},
            {"title": "p53 mutation", "content": "預後最差。建議化放療積極輔助。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Maintenance Therapy", "content": "一線 IO 治療後延續維持至 PD (DUO-E)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "Recurrent EC", "content": "標靶+免疫 (MSS) 或 IO 單藥 (GARNET)。"}]}
    ],
    "Ovarian": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "HGSC / Endometrioid", "content": "Surgery + Carbo/Pacli ± Bev。IDS 考慮加 HIPEC。"},
            {"title": "Mucinous (MOC) 鑑別", "content": "判定：CK7+/SATB2-。Expansile (預後佳) vs Infiltrative。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "BRCA mutation", "content": "Olaparib 單藥維持 2年 (SOLO-1)。"}, 
            {"title": "HRD positive / BRCA wt", "content": "PAOLA-1 (Ola+Bev) 或 PRIMA (Nira)。"},
            {"title": "HRD negative (pHRD)", "content": "Niraparib 維持 (PRIMA ITT) 或觀察。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "PSOC (Sensitive)", "content": "PFI > 6m。評估二次手術 (DESKTOP III) 或含鉑。"},
            {"title": "PROC (Resistant)", "content": "PFI < 6m。單藥化療 ± Bev 或 FRα ADC (MIRASOL)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "救援緩解後選維持治療。"}]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "Locally Advanced (CCRT)", "content": "同步化放療 ± IO (A18) 或 誘導化療 (INTERLACE)。"},
            {"title": "Early Stage (Surgery)", "content": "根治術 (LACC) 或單純切除 (SHAPE)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Maintenance", "content": "1L 方案後接續維持 (KEYNOTE-826)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "Recurr / Metastatic", "content": "一線 Pembro+化療±Bev (KN826) 或 二線 ADC。"}]}
    ]
}

# --- 2. 綜合實證資料庫 (33+ 研究極量化整合) ---
all_trials_db = [
    # --- Endometrial Published ---
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["dMMR / MSI-H"], "name": "📚 RUBY", "pharma": "GSK", "drug": "Dostarlimab + CP", 
     "results": "dMMR PFS HR 0.32; mOS 44.6m (vs 28.2m).", 
     "rationale": "透過 PD-1 阻斷與化療協同 ICD 效應，針對 MMRd 族群達到持久應答。",
     "regimen": "Dosta 500mg Q3W + CP x6週期 -> 維持 Dosta 1000mg Q6W 最長 3年。",
     "inclusion": ["新診斷 Stage III-IV 或首次復發 EC。", "包含 Carcinosarcoma 型態。"],
     "exclusion": ["先前接受過系統抗癌治療。", "活動性自體免疫疾病。"]},

    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["dMMR / MSI-H", "pMMR / NSMP / MSS"], "name": "📚 NRG-GY018", "pharma": "MSD", "drug": "Pembrolizumab + CP", 
     "results": "dMMR PFS HR 0.30; pMMR PFS HR 0.54.", 
     "rationale": "支持一線不論 MMR 狀態之免疫介入獲益。",
     "regimen": "Pembro 200mg Q3W + CP x6週期 -> 維持 400mg Q6W 最長 2年。"},

    {"cancer": "Endometrial", "pos": "Maintenance Therapy", "sub_pos": ["pMMR / NSMP / MSS"], "name": "📚 DUO-E", "pharma": "AZ", "drug": "Durvalumab + CP →維持 ± Ola", 
     "results": "三藥組 PFS HR 0.57 (vs CP).", 
     "rationale": "探索 PARPi 與 ICI 在 pMMR 族群維持階段之協同效應。"},

    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["dMMR / MSI-H"], "name": "📚 AtTEnd", "pharma": "Roche", "drug": "Atezolizumab + CP", 
     "results": "dMMR PFS HR 0.36; ITT OS HR 0.82 (P=0.048).", 
     "rationale": "確認 PD-L1 抑制劑併用化療在一線晚期之價值。"},

    {"cancer": "Endometrial", "pos": "Recurrent EC", "sub_pos": ["Recurrent EC"], "name": "📚 KEYNOTE-775", "pharma": "MSD/Eisai", "drug": "Lenvatinib + Pembro", 
     "results": "pMMR OS HR 0.68; mOS 17.4m (vs 12.0m).", 
     "rationale": "結合 VEGF-TKI 與免疫抑制劑，克服 MSS 腫瘤之冷微環境。"},

    {"cancer": "Endometrial", "pos": "Recurrent EC", "sub_pos": ["Recurrent EC"], "name": "📚 GARNET", "pharma": "GSK", "drug": "Dostarlimab 單藥", 
     "results": "dMMR ORR 45.5%; DOR 未達到。", 
     "rationale": "奠定 MSI-H/dMMR 患者後線單藥免疫之治療地位。"},

    # --- Cervical Published ---
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Locally Advanced (CCRT)"], "name": "📚 KEYNOTE-A18", "pharma": "MSD", "drug": "Pembrolizumab + CCRT", 
     "results": "OS HR 0.67; 36m OS 82.6%.", 
     "rationale": "將免疫正式併入高風險局部晚期之根治標準。"},

    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Locally Advanced (CCRT)"], "name": "📚 INTERLACE", "pharma": "UCL", "drug": "Induction Carbo/Pacli x6", 
     "results": "5yr OS 80% (vs 72%, HR 0.60).", 
     "rationale": "誘導化療透過老藥新用提升長期生存。"},

    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Locally Advanced (CCRT)"], "name": "📚 CALLA", "pharma": "AZ", "drug": "Durvalumab + CCRT", 
     "results": "PFS HR 0.84 (P=NS)。未達標。", 
     "rationale": "提醒免疫組合放化療之複雜度與分流必要性。"},

    {"cancer": "Cervical", "pos": "Recurr / Metastatic", "sub_pos": ["Recurr / Metastatic"], "name": "📚 KEYNOTE-826", "pharma": "MSD", "drug": "Pembro + Chemo ± Bev", 
     "results": "OS HR 0.63; CPS≥1 HR 0.60.", 
     "rationale": "確立持續復發一線 Immuno-chemo 標準。"},

    {"cancer": "Cervical", "pos": "Recurr / Metastatic", "sub_pos": ["Recurr / Metastatic"], "name": "📚 BEATcc", "pharma": "Roche", "drug": "Atezo + Chemo + Bev", 
     "results": "PFS HR 0.62; OS HR 0.68.", 
     "rationale": "提供一線復發轉移性之另一個免疫選項。"},

    {"cancer": "Cervical", "pos": "Recurr / Metastatic", "sub_pos": ["Recurr / Metastatic"], "name": "📚 EMPOWER-Cx 1", "pharma": "Regeneron", "drug": "Cemiplimab", 
     "results": "OS HR 0.69; mOS 12.0m.", 
     "rationale": "二線後單藥免疫之 OS 基石實證。"},

    {"cancer": "Cervical", "pos": "Recurr / Metastatic", "sub_pos": ["Recurr / Metastatic"], "name": "📚 innovaTV 301", "pharma": "Genmab", "drug": "Tisotumab Vedotin (ADC)", 
     "results": "OS HR 0.70; ORR 17.8%。", 
     "rationale": "首個後線 OS 獲益之 ADC 試驗。"},

    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Early Stage (Surgery)"], "name": "📚 SHAPE trial", "pharma": "CCTG", "drug": "Simple Hysterectomy", 
     "results": "3yr Recurrence: 2.5% vs 2.2% (HR 1.0).", 
     "rationale": "支持低風險早期患者進行手術降階。"},

    # --- Ovarian Published ---
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutation"], "name": "📚 SOLO-1", "pharma": "AZ", "drug": "Olaparib 維持", 
     "results": "7yr survival 67% (HR 0.33)."},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive / BRCA wt", "HRD negative (pHRD)"], "name": "📚 PRIMA", "pharma": "GSK", "drug": "Niraparib 維持", 
     "results": "HRD+ PFS HR 0.43; 全人群 HR 0.62."},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive / BRCA wt"], "name": "📚 PAOLA-1", "pharma": "AZ", "drug": "Olaparib + Bevacizumab", 
     "results": "HRD+ OS HR 0.62; 5yr OS 75.2%."},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutation", "HRD positive / BRCA wt"], "name": "📚 ATHENA–MONO", "pharma": "Clovis", "drug": "Rucaparib 維持", 
     "results": "ITT PFS HR 0.52 (28.7m vs 11.3m)."},

    {"cancer": "Ovarian", "pos": "Platinum Sensitive Maint", "sub_pos": ["Platinum Sensitive Maint"], "name": "📚 NOVA / ARIEL3 / SOLO2", "pharma": "Various", "drug": "PARPi 維持", 
     "results": "SOLO2 mOS 51.7m (HR 0.74)."},

    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive / BRCA wt"], "name": "📚 DUO-O", "pharma": "AZ", "drug": "Durva+Ola+Bev 維持", 
     "results": "HRD+ PFS HR 0.49."},

    {"cancer": "Ovarian", "pos": "PROC (Resistant)", "sub_pos": ["PROC (Resistant)"], "name": "📚 MIRASOL", "pharma": "ImmunoGen", "drug": "Mirvetuximab", 
     "results": "OS HR 0.67; ORR 42.3%。"},

    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 HIPEC (van Driel)", "pharma": "NEJM 2018", "drug": "Surgery + HIPEC", 
     "results": "mOS 45.7m vs 33.9m (HR 0.67)."},

    {"cancer": "Ovarian", "pos": "PSOC (Sensitive)", "sub_pos": ["PSOC (Sensitive)"], "name": "📚 DESKTOP III", "pharma": "NEJM 2021", "drug": "Secondary Surgery", 
     "results": "mOS 53.7m (vs 46.0m, HR 0.75)."},

    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 LION", "pharma": "NEJM 2019", "drug": "No Lymphadenectomy", 
     "results": "OS HR 1.06. 臨床 LN 陰性免清掃。"},

    # --- 📍 Ongoing Trials (8核心計畫救援) ---
    {"cancer": "Ovarian", "name": "📍 FRAmework-01", "pharma": "Eli Lilly", "drug": "LY4170156 + Bevacizumab", "pos": "PROC (Resistant)", "sub_pos": ["PROC (Resistant)"], "type": "Ongoing",
     "rationale": "標靶 FRα ADC 聯用 anti-VEGF 提升藥物滲透深度挑戰耐藥。",
     "inclusion": ["FRα 表達陽性。", "最後鉑類後 90–180 天內進展 (PROC)。"],
     "exclusion": ["曾用過 Topo I ADC。", "活動性間質性肺病 (ILD)。"]},

    {"cancer": "Ovarian", "name": "📍 REJOICE-Ovarian01", "pharma": "Daiichi Sankyo", "drug": "R-DXd", "pos": "PROC (Resistant)", "sub_pos": ["PROC (Resistant)"], "type": "Ongoing",
     "rationale": "標靶 CDH6 ADC，具強力旁觀者效應挑戰異質性 PROC 腫瘤。",
     "inclusion": ["HG Serous 或 Endometrioid PROC。", "提供切片進行 CDH6 分層判定。"]},

    {"cancer": "Ovarian", "name": "📍 TroFuse-021", "pharma": "MSD", "drug": "Sac-TMT (MK-2870) + Bev", "pos": "P-MT", "sub_pos": ["HRD positive / BRCA wt", "HRD negative (pHRD)"], "type": "Ongoing",
     "rationale": "標靶 Trop-2 ADC 協同 Beva 微環境調節旨在優化維持獲益。",
     "inclusion": ["新診斷 Stage III/IV 卵巢癌。", "一線含鉑化療後達 CR 或 PR。"]},

    {"cancer": "Endometrial", "name": "📍 MK2870-033", "pharma": "MSD", "drug": "Sac-TMT + Pembrolizumab", "pos": "P-MT", "sub_pos": ["IO Maintenance"], "type": "Ongoing",
     "rationale": "標靶 Trop-2 ADC 協同 PD-1。提升 Pembro 在 pMMR 族群的應答深度。",
     "inclusion": ["pMMR 子宮內膜癌 (中心檢測)。", "FIGO III/IV 一線含鉑+Pembro後達 CR/PR。"]},

    {"cancer": "Endometrial", "name": "📍 GU-US-682-6769", "pharma": "Gilead", "drug": "SG (Trodelvy)", "pos": "Recurrent EC", "sub_pos": ["Recurrent EC"], "type": "Ongoing",
     "rationale": "標靶 Trop-2 ADC 利用 SN-38 載荷殺傷對抗鉑類與免疫失敗救援。",
     "inclusion": ["復發性 EC。", "鉑類與 PD-1 失敗後進展。"]},

    {"cancer": "Ovarian", "name": "📍 DS8201-772 (Enhertu)", "pharma": "AstraZeneca", "drug": "T-DXd (HER2 ADC)", "pos": "PR-Maint", "sub_pos": ["Platinum Sensitive Maint"], "type": "Ongoing",
     "rationale": "標靶 HER2 ADC 救援穩定後維持清除微小殘留病灶。",
     "inclusion": ["HER2 IHC 1+/2+/3+ 確認。", "PSOC 救援化療達穩定。"]},

    {"cancer": "Ovarian", "name": "📍 DOVE", "pharma": "GSK", "drug": "Dostarlimab + Bevacizumab", "pos": "PROC (Resistant)", "sub_pos": ["PROC (Resistant)"], "type": "Ongoing",
     "rationale": "針對 OCCC 透明細胞癌利用雙重阻斷改善免疫抑制微環境。",
     "inclusion": ["組織學 OCCC > 50%。", "鉑類抗藥性 (PFI < 12m)。"]},

    {"cancer": "Cervical", "name": "📍 innovaTV 301 Access", "pharma": "Seagen", "drug": "Tisotumab Vedotin (Tivdak)", "pos": "Recurr / Metastatic", "sub_pos": ["Recurr / Metastatic"], "type": "Ongoing",
     "rationale": "標靶 TF ADC 旨在克服後線子宮頸癌化療耐藥性。",
     "inclusion": ["復發/轉移子宮頸癌。", "先前接受 1–2 線治療後進展。"]},
]

# --- 3. AI 模型巡邏 ---
def get_gemini_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target_model = next((m for m in available_models if 'gemini-1.5-flash' in m), None)
        if not target_model: target_model = next((m for m in available_models if 'gemini-pro' in m), None)
        if target_model: return genai.GenerativeModel(target_model)
    except: return None

# --- 4. 側邊欄：患者資訊與 AI 分析 ---
with st.sidebar:
    st.markdown("<h3 style='color: #6A1B9A;'>🤖 AI 實證媒合助理</h3>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 患者數據深度媒合", expanded=True):
        p_notes = st.text_area("輸入摘要 (含分期/分型/標記)", placeholder="例如：Ovarian HGSC, BRCA wt, HRD+...", height=220)
        if st.button("🚀 開始分析", key="sidebar_analyze"):
            if api_key and p_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = get_gemini_model()
                    prompt = f"分析：{p_notes}。請參考：{all_trials_db}。建議適合路徑與理由。"
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
            rel_trials = [t for t in all_trials_db if t["cancer"] == cancer_type and t["pos"] == stage["id"] and any(s in sub["title"] for s in t["sub_pos"])]
            for t in rel_trials:
                label = f"{t.get('pharma', 'N/A')} | {t['name']} | {t['drug']}"
                with st.popover(label, use_container_width=True):
                    st.success(f"**核心結論:** {t.get('results', '招募中')}")
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

selected_name = st.selectbox("🎯 快速選擇研究計畫以查閱詳細內容：", [t["name"] for t in filtered_list], index=curr_idx, key="trial_selector")
st.session_state.selected_trial = selected_name
t = next(it for it in all_trials_db if it["name"] == selected_name)

st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #E0E0E0; padding-bottom:10px; font-weight:900;'>📋 {t['name']} 深度分析報告</h2>", unsafe_allow_html=True)

r1, r2 = st.columns([1.3, 1])
with r1:
    st.markdown("<div style='background:#E3F2FD; border-left:10px solid #1976D2; padding:15px; border-radius:10px;'><b>💉 Rationale & Regimen (機轉與給藥)</b></div>", unsafe_allow_html=True)
    st.write(f"**核心介入:** {t['drug']}")
    st.write(f"**詳細給藥細節 (Regimen Details):** {t.get('regimen', '詳見招募細則。')}")
    st.success(f"**科學理據 (Scientific Rationale):** {t.get('rationale', '旨在挑戰現有 SoC 瓶頸，提升生存獲益。')}")
    

with r2:
    st.markdown("<div style='background:#FFF8E1; border-left:8px solid #FBC02D; padding:15px; border-radius:10px;'><b>📈 Key Outcomes (生存與緩解數據)</b></div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style='text-align:center; background:white; padding:15px; border:2px solid #FFE082; border-radius:12px;'>
            <div style='font-size: 14px; color: #795548; font-weight:700; margin-bottom:5px;'>Survival Metrics (PFS/OS/HR/ORR)</div>
            <div class='hr-big-val'>{t.get('results', 'Recruiting...')}</div>
        </div>
    """, unsafe_allow_html=True)
    

st.divider()
r3, r4 = st.columns(2)
with r3:
    st.markdown("<div style='background:#E8F5E9; border-left:8px solid #2E7D32; padding:15px; border-radius:10px;'><b>✅ Inclusion Criteria (關鍵納入標準)</b></div>", unsafe_allow_html=True)
    for inc in t.get('inclusion', ['詳見全文。']): st.write(f"• **{inc}**")
with r4:
    st.markdown("<div style='background:#FFEBEE; border-left:8px solid #C62828; padding:15px; border-radius:10px;'><b>❌ Exclusion Criteria (關鍵排除標準)</b></div>", unsafe_allow_html=True)
    for exc in t.get('exclusion', ['詳見全文。']): st.write(f"• **{exc}**")
st.markdown("</div>", unsafe_allow_html=True)
