import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床導航與實證圖書館 (2026 最終全功能整合版) ---
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

    /* 大階段方塊：高度自適應，零留白 */
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

    /* 按鈕樣式：深黑色加粗 (#1A1A1A) */
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
    .hr-big-val { font-family: 'Roboto', sans-serif; font-size: 50px !important; font-weight: 900; color: #D84315; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 指引導航數據：包含子宮頸癌、MOC 與 PSOC/PROC 分流 ---
guidelines_nested = {
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "MMRd / MSI-H", "content": "一線首選：Chemo + PD-1 (GY018/RUBY)。"},
            {"title": "NSMP / pMMR", "content": "排除 MMRd/p53/POLE。視 ER/Grade 加權：ER-neg/G3 為高風險建議加強輔助。"},
            {"title": "POLEmut / p53abn", "content": "POLE: 最佳預後，早期可降階治療；p53: 最差預後，建議化放療併用。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "IO Maintenance", "content": "延續一線使用的免疫藥物維持至進展 (PD)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "Recurrent EC", "content": "二線標準：Pembro + Lenva (pMMR) 或單藥 IO (MMRd)。"}]}
    ],
    "Ovarian": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "HGSC / Endometrioid", "content": "Surgery + Carbo/Pacli ± Bevacizumab。"},
            {"title": "Mucinous (MOC) 鑑別", "content": "判定：CK7+/SATB2-。1. Expansile: 預後佳，早期可保守。 2. Infiltrative: 易微轉移，建議積極化療。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "BRCA mutated", "content": "Olaparib 單藥維持 2年。"}, {"title": "HRD positive (wt)", "content": "Olaparib+Bev (2年) 或 Niraparib 單藥 (3年)。"}]},
        {"id": "R-TX (PROC)", "header": "復發治療 (Resistant)", "css": "r-tx", "subs": [{"title": "PROC (PFI < 6m)", "content": "單藥化療 ± Bev 或 FRα ADC (Elahere)。"}]},
        {"id": "R-TX (PSOC)", "header": "復發治療 (Sensitive)", "css": "r-tx", "subs": [{"title": "PSOC (PFI > 6m)", "content": "含鉑複方化療 ± Bev。評估二次手術獲益。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Platinum Sensitive Maint", "content": "救援緩解後選 PARPi 維持治療。"}]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "Early Stage (SHAPE/LACC)", "content": "低風險選單純全切除；高風險選開腹根治術。"},
            {"title": "Locally Advanced (CCRT)", "content": "CCRT ± 同步 IO (A18) 或 6週誘導化療 (INTERLACE)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Metastatic Maint", "content": "1L IO + 化療後續用 IO 維持直到 PD。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "Recurr / Metastatic", "content": "一線 Pembro + 化療 ± Bev。二線 ADC (Tivdak)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "維持當前有效方案直到進展。"}]}
    ]
}

# --- 2. 實證里程碑 (📚 Milestone Library - 深度擴充) ---
milestone_db = [
    # Endometrial
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H"], "name": "📚 RUBY (Dostarlimab)", "drug": "Dostarlimab + CP", 
     "summary": "族群：晚期/復發 EC (含 Serous/Clear cell)。結果：dMMR 死亡風險降 68% (HR 0.32)；全人群 mOS 44.6m (vs 28.2m, HR 0.69)。"},
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H", "NSMP / pMMR"], "name": "📚 NRG-GY018 (Pembro)", "drug": "Pembrolizumab + CP", 
     "summary": "族群：III-IVB/復發 EC。結果：dMMR PFS HR 0.30；pMMR HR 0.54。FDA 已核准用於所有晚期患者。"},
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["NSMP / pMMR"], "name": "📚 DUO-E", "drug": "Durvalumab ± Olaparib", 
     "summary": "結果：三藥組 (IO+PARPi) PFS HR 0.57；單藥 IO 組 HR 0.77。建立 pMMR 一線維持新視角。"},
    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["NSMP / pMMR"], "name": "📚 KEYNOTE-775", "drug": "Pembro + Lenvatinib", 
     "summary": "二線(曾含鉑)全體：OS 18.3m vs 11.4m (HR 0.62)。pMMR 5年 OS 率 16.7% vs 7.3%。"},

    # Cervical
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Locally Advanced (CCRT)"], "name": "📚 KEYNOTE-A18", "drug": "Pembro + CCRT", 
     "summary": "族群：IB2-IVA 高風險。結果：36個月 OS 顯著提升 (82.6% vs 74.8%, HR 0.67)。確立 LACC 標準。"},
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Locally Advanced (CCRT)"], "name": "📚 INTERLACE", "drug": "Induction Chemo", 
     "summary": "結果：Carbo/Pacli 週療 x6 接 CCRT。5年 OS 改善 (80% vs 72%, HR 0.60)。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["1L Recurrent"], "name": "📚 KEYNOTE-826", "drug": "Pembro + Chemo ± Bev", 
     "summary": "R/M 一線。全人群 OS HR 0.63；CPS≥1 HR 0.60。支持一線免疫全面覆蓋。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["2L / 3L Therapy"], "name": "📚 innovaTV 301", "drug": "Tivdak (TF-ADC)", 
     "summary": "二/三線 ADC。OS 11.5m vs 9.5m (HR 0.70)，ORR 17.8%。眼表毒性需監測。"},

    # Ovarian
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutated"], "name": "📚 SOLO-1 (Olaparib)", "drug": "Olaparib", 
     "summary": "一線維持。7年 survival 67% (vs 46.5%, HR 0.33)。確立 BRCAm 治癒潛力。"},
    {"cancer": "Ovarian", "pos": "R-TX (PROC)", "sub_pos": ["PROC (PFI < 6m)"], "name": "📚 MIRASOL (FRα ADC)", "drug": "Mirvetuximab", 
     "summary": "FRα+ PROC。OS 16.4m vs 12.7m (HR 0.67)，ORR 42.3%。PROC 歷史突破。"},
    {"cancer": "Ovarian", "pos": "R-TX (PSOC)", "sub_pos": ["PSOC (PFI > 6m)"], "name": "📚 DESKTOP III", "drug": "Secondary Surgery", 
     "summary": "符合 AGO Score 的 PSOC 患者二次手術 mOS 53.7m (vs 46.0m, HR 0.75)。"}
]

# --- 3. 進行中試驗 (📍 Ongoing - 極量化細節補完) ---
ongoing_trials = [
    {"cancer": "Ovarian", "name": "FRAmework-01 (LY4170156)", "pharma": "Eli Lilly", "drug": "LY4170156 + Bevacizumab", "pos": "R-TX (PROC)", "sub_pos": ["PROC (PFI < 6m)"], 
     "rationale": "標靶 FRα ADC，搭載類微管蛋白 Payload。聯用 Bevacizumab 可產生血管調節協同作用 (Synergy)，提升 ADC 在實體腫瘤內的滲透深度，解決 PARPi 耐藥後 PROC 之需求。",
     "dosing": {"Exp Arm": "LY4170156 3 mg/kg IV + Bevacizumab 15 mg/kg IV Q3W。", "Control Arm": "醫師選擇單藥化療 (Pacli, PLD, Gem) 或 MIRV。"},
     "inclusion": ["High-grade Serous / Carcinosarcoma 之卵巢/輸卵管癌。", "中央實驗室確認 FRα 表達陽性。", "最後一劑鉑類後 90–180 天內惡化 (PROC)。", "先前接受過 1–3 線系統治療。"],
     "exclusion": ["先前曾用過帶有 Topoisomerase I 抑制劑 Payload 之 ADC (如 Enhertu)。", "活動性間質性肺病 (ILD) 或肺炎病史。", "蛋白尿 UPCR ≥ 2.0。"], "ref": "NCT06536348"},
    
    {"cancer": "Ovarian", "name": "REJOICE-Ovarian01", "pharma": "Daiichi Sankyo", "drug": "R-DXd", "pos": "R-TX (PROC)", "sub_pos": ["PROC (PFI < 6m)"], 
     "rationale": "標靶 Cadherin-6 (CDH6) ADC，搭載強效 DXd 載荷。具備極高 DAR (8) 與強力旁觀者效應 (Bystander effect)，專攻高度異質性且 CDH6 表達之 PROC，挑戰二/三線生存標竿。",
     "dosing": {"Exp Arm": "R-DXd 5.6mg/kg IV Q3W。", "Control Arm": "研究者選擇單藥化療。"},
     "inclusion": ["HG Serous 或 Endometrioid PROC。", "先前接受 1-4 線系統治療。", "必須提供組織切片進行 CDH6 分層。", "需曾用過 Bevacizumab。"],
     "exclusion": ["Low-grade / Clear cell / Mucinous (原發)。", "LVEF < 50% 或基線 Grade ≥2 周邊神經病變。"], "ref": "JCO 2024"},
    
    {"cancer": "Ovarian", "name": "TroFuse-021", "pharma": "MSD", "drug": "Sac-TMT (MK-2870)", "pos": "P-MT", "sub_pos": ["HRD negative / pHRD"], 
     "rationale": "標靶 Trop-2 ADC。透過結合 Beva 微環境調節與 ADC 誘導的 ICD 效應，旨在優化 pHRD 族群在一線含鉑化療後維持時的獲益。",
     "inclusion": ["新診斷 FIGO III/IV 卵巢癌。", "HRD negative 且 BRCA 野生型。", "一線含鉑化療後達 CR/PR 狀態。", "可供檢測 Trop-2 表達之檢體。"],
     "exclusion": ["BRCA 突變。", "先前用過 Trop-2 ADC。", "嚴重炎症性腸道疾病 (IBD) 病史。"], "ref": "ENGOT-ov85"},

    {"cancer": "Endometrial", "name": "MK2870-033", "pharma": "MSD", "drug": "Sac-TMT + Pembro", "pos": "P-MT", "sub_pos": ["IO Maintenance"], 
     "rationale": "標靶 Trop-2 ADC 協同 PD-1。透過免疫調節強化 Pembrolizumab 在 pMMR 或 NSMP 族群的長期應答。",
     "inclusion": ["pMMR 子宮內膜癌 (中心檢測)。", "FIGO III/IV 一線含鉑+Pembro後達 CR/PR。", "初次復發且未曾針對復發治療。"],
     "exclusion": ["子宮肉瘤 (Sarcoma)。", "先前接受過晚期系統性 IO 治療。"], "ref": "ESMO 2025"},
    
    {"cancer": "Endometrial", "name": "GU-US-682-6769", "pharma": "Gilead", "drug": "SG (Trodelvy)", "pos": "R-TX", "sub_pos": ["NSMP / pMMR", "Recurrent EC"], 
     "rationale": "標靶 Trop-2 ADC。利用 SN-38 載荷引發 DNA 損傷，解決鉑類與免疫失敗救援，具強力 Bystander 效應。",
     "inclusion": ["復發性 EC (不含肉瘤)。", "鉑類與 PD-1 失敗後進展。", "ANC ≥1500, Platelets ≥100k。"],
     "exclusion": ["先前用過 Trop-2 ADC。", "活動性 CNS 轉移。"], "ref": "JCO 2024"}
]

# --- 4. 動態模型巡邏與 AI 模型選擇 ---
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
    st.session_state.selected_trial = ongoing_trials[0]['name']

with st.sidebar:
    st.markdown("<h3 style='color: #6A1B9A;'>🤖 AI 實證決策助理</h3>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 患者數據深度媒合", expanded=True):
        p_notes = st.text_area("輸入摘要 (含期別/標記)", height=250)
        if st.button("🚀 開始分析"):
            if api_key and p_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = get_gemini_model()
                    if model:
                        prompt = f"分析：{p_notes}。參考實證：{milestone_db} 及進行中：{ongoing_trials}。提供最佳路徑與理由。"
                        st.write(model.generate_content(prompt).text)
                    else: st.error("找不到可用 AI 模型。")
                except Exception as e: st.error(f"AI 異常: {e}")

# --- 6. 主頁面：導航地圖 ---
st.markdown("<div class='main-title'>婦癌臨床導航儀表板 (FIGO 2023 & Milestone Edition)</div>", unsafe_allow_html=True)
cancer_type = st.radio("第一步：選擇癌症類型", ["Endometrial", "Ovarian", "Cervical"], horizontal=True)

# 標題與內容高度緊扣
cols = st.columns(len(guidelines_nested[cancer_type]))
stages_data = guidelines_nested[cancer_type]

for i, stage in enumerate(stages_data):
    with cols[i]:
        st.markdown(f"""<div class='big-stage-card card-{stage['css']}'><div class='big-stage-header header-{stage['css']}'>{stage['header']}</div>""", unsafe_allow_html=True)
        for sub in stage['subs']:
            st.markdown(f"""<div class='sub-block'><div class='sub-block-title'>📘 {sub['title']}</div><div class='sub-block-content'>{sub['content']}</div>""", unsafe_allow_html=True)
            
            # A. 里程碑實證 (📚)
            rel_milestones = [m for m in milestone_db if m["cancer"] == cancer_type and m["pos"] == stage["id"] and any(s in sub["title"] for s in m["sub_pos"])]
            for m in rel_milestones:
                with st.popover(f"📚 {m['name']}", use_container_width=True):
                    st.success(f"**藥物:** {m['drug']}\n\n**詳細數據:** {m['summary']}")
            
            # B. 招募中試驗 (📍)
            rel_trials = [t for t in ongoing_trials if t["cancer"] == cancer_type and t["pos"] == stage["id"] and any(s in sub["title"] for s in t["sub_pos"])]
            for t in rel_trials:
                label = f"📍 {t['pharma']} | {t['name']}"
                ukey = f"btn_{t['name']}_{stage['id']}_{sub['title'].replace(' ', '')}"
                with st.popover(label, use_container_width=True):
                    if st.button("📊 開啟極量化數據報告", key=ukey):
                        st.session_state.selected_trial = t['name']
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 7. 招募中試驗極量化報告 ---
st.divider()
all_ongoing = [t["name"] for t in ongoing_trials if t["cancer"] == cancer_type]
if all_ongoing:
    try: curr_idx = all_ongoing.index(st.session_state.selected_trial)
    except: curr_idx = 0
    selected_name = st.selectbox("🎯 切換招募中計畫詳細分析：", all_ongoing, index=curr_idx)
    t = next(it for it in ongoing_trials if it["name"] == selected_name)

    st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #E0E0E0; padding-bottom:10px; font-weight:900;'>📋 {t['name']} 招募中深度報告</h2>", unsafe_allow_html=True)

    r1, r2 = st.columns([1.3, 1])
    with r1:
        st.markdown("<div style='background:#E3F2FD; border-left:10px solid #1976D2; padding:15px; border-radius:10px;'><b>💉 Rationale & Dosing (機轉詳解)</b></div>", unsafe_allow_html=True)
        st.write(f"**核心藥物:** {t['drug']}")
        st.success(t['rationale'])
        

    with r2:
        st.markdown("<div style='background:#E8F5E9; border-left:8px solid #2E7D32; padding:15px; border-radius:10px;'><b>✅ Inclusion Criteria (納入標準)</b></div>", unsafe_allow_html=True)
        for inc in t.get('inclusion', []): st.write(f"• **{inc}**")

    st.markdown("<div style='background:#FFEBEE; border-left:8px solid #C62828; padding:15px; border-radius:10px; margin-top:10px;'><b>❌ Exclusion Criteria (排除標準)</b></div>", unsafe_allow_html=True)
    for exc in t.get('exclusion', []): st.write(f"• **{exc}**")
    st.markdown("</div>", unsafe_allow_html=True)
