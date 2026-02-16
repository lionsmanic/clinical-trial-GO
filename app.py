import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床導航與實證圖書館 (2026 終極實證救援版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=Roboto:wght@400;700;900&display=swap');
    
    /* === 極致緊緻化 UI 與 高對比度文字 === */
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

    /* 大階段方塊：零留白設計 */
    .big-stage-card {
        border-radius: 10px; padding: 0px; 
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        border: 2px solid transparent; background: white; 
        margin-bottom: 4px; overflow: hidden; height: auto !important;
    }
    .big-stage-header {
        font-size: 17px !important; font-weight: 900; color: white;
        padding: 4px; text-align: center;
    }

    /* 子區塊 (SoC 與 分子亞型) */
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

    /* --- 標記按鈕樣式：深黑色加粗 (#1A1A1A) --- */
    .stPopover button { 
        font-weight: 900 !important; font-size: 12px !important; 
        border-radius: 4px !important; margin-top: 1px !important;
        padding: 1px 6px !important; width: 100% !important; 
        text-align: left !important; color: #1A1A1A !important; 
        border: 1px solid rgba(0,0,0,0.15) !important;
    }
    
    /* 📚 里程碑實證背景 */
    .stPopover button[aria-label*="📚"] { background: #ECEFF1 !important; border-left: 5px solid #455A64 !important; }

    /* 📍 招募中試驗藥廠配色飾邊 */
    .stPopover button[aria-label*="Eli Lilly"] { background: #FCE4EC !important; border-left: 5px solid #E91E63 !important; } 
    .stPopover button[aria-label*="Daiichi Sankyo"] { background: #E8F5E9 !important; border-left: 5px solid #4CAF50 !important; } 
    .stPopover button[aria-label*="MSD"] { background: #E3F2FD !important; border-left: 5px solid #1976D2 !important; } 
    .stPopover button[aria-label*="AstraZeneca"] { background: #F3E5F5 !important; border-left: 5px solid #8E24AA !important; } 
    .stPopover button[aria-label*="GSK"] { background: #FFF3E0 !important; border-left: 5px solid #F57C00 !important; } 
    .stPopover button[aria-label*="Gilead"] { background: #E1F5FE !important; border-left: 5px solid #03A9F4 !important; } 
    .stPopover button[aria-label*="Seagen"] { background: #EEEEEE !important; border-left: 5px solid #212121 !important; } 

    .detail-section { background: white; border-radius: 18px; padding: 25px; border: 1px solid #CFD8DC; box-shadow: 0 10px 40px rgba(0,0,0,0.05); }
    .hr-big-val { font-family: 'Roboto', sans-serif; font-size: 48px !important; font-weight: 900; color: #D84315; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 里程碑實證資料庫 (📚 Milestone Library - 完整救回並擴充) ---
milestone_db = [
    # 子宮內膜癌
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H"], "name": "📚 RUBY (NCT03981796)", "drug": "Dostarlimab + CP", "summary": "dMMR 死亡風險降低 68% (HR 0.32)。全人群 mOS 延長至 44.6m (vs 28.2m)。"},
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H", "NSMP"], "name": "📚 NRG-GY018", "drug": "Pembrolizumab + CP", "summary": "dMMR PFS HR 0.30；pMMR 顯著改善 (HR 0.54)。支持一線不限 MMR 使用 IO+Chemo。"},
    {"cancer": "Endometrial", "pos": "P-MT", "sub_pos": ["IO Maintenance"], "name": "📚 DUO-E", "drug": "Durvalumab ± Olaparib", "summary": "pMMR 族群亮點：三藥聯合 (Durva+Ola) PFS HR 0.57。帶入「免疫+維持」概念。"},
    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["pMMR / NSMP"], "name": "📚 KEYNOTE-775", "drug": "Pembro + Lenvatinib", "summary": "5年長期追蹤：pMMR OS 獲益持久 (16.7% vs 7.3%)。確立二線標竿方案。"},
    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["MMRd / MSI-H"], "name": "📚 GARNET", "drug": "Dostarlimab", "summary": "dMMR/MSI-H ORR 45.5%。奠定多線後免疫單藥地位。"},

    # 子宮頸癌
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["CCRT (LA / 1L)"], "name": "📚 KEYNOTE-A18", "drug": "Pembrolizumab + CCRT", "summary": "36個月 OS 顯著提升至 82.6%。確立為局部晚期高風險新標準。"},
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["CCRT (LA / 1L)"], "name": "📚 INTERLACE", "drug": "Induction Chemo", "summary": "先給 6週 Carbo/Pacli 再 CCRT，5年 OS 改善 (80% vs 72%)。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["1L Recurrent"], "name": "📚 KEYNOTE-826", "drug": "Pembro + Chemo ± Bev", "summary": "R/M 一線 OS 持續改善。CPS≥1 族群 HR 0.60。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["1L Recurrent"], "name": "📚 BEATcc", "drug": "Atezolizumab + Chemo + Bev", "summary": "R/M 一線 PFS/OS 顯著改善。提供新的 IO 選項。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["2L / 3L Therapy"], "name": "📚 innovaTV 301", "drug": "Tisotumab vedotin", "summary": "後線 ADC 突破。OS 延長至 11.5m (vs 9.5m)。"},
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Early (Surgery)"], "name": "📚 LACC Trial", "drug": "Open vs MIS", "summary": "震驚實務：微創手術復發率/死亡率較高 (HR 6.00)。"},

    # 卵巢癌
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutated"], "name": "📚 SOLO-1 (Olaparib)", "drug": "Olaparib", "summary": "一線維持里程碑：7年存活率 67%。具備治癒潛力 (HR 0.33)。"},
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive (wt)"], "name": "📚 PRIMA / PAOLA-1", "drug": "PARPi Maintenance", "summary": "確立不限 BRCA 之一線維持價值。PAOLA-1 HRD+ OS HR 0.62。"},
    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["Platinum Sensitive"], "name": "📚 NOVA / ARIEL3 / SOLO2", "drug": "PARPi R-Maint", "summary": "復發維持 PFS 顯著改善。SOLO2 顯示具臨床意義之 OS 獲益。"},
    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PROC (Resistant)"], "name": "📚 MIRASOL", "drug": "Mirvetuximab", "summary": "PROC 歷史突破：首個證明 ADC 在此族群有 OS 獲益 (HR 0.67)。"},
    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 van Driel HIPEC", "drug": "HIPEC", "summary": "NACT 後之 IDS 手術加 HIPEC 改善 OS/RFS。"},
    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["Secondary Surgery"], "name": "📚 DESKTOP III", "drug": "Surgery", "summary": "嚴選 AGO Score 合格者，二次減積手術可顯著延長 OS (53.7m)。"}
]

# --- 2. 招募中試驗資料庫 (📍 Ongoing - 8 核心詳盡細節) ---
ongoing_db = [
    {"cancer": "Ovarian", "name": "FRAmework-01 (LY4170156)", "pharma": "Eli Lilly", "drug": "LY4170156 + Bevacizumab", "pos": "R-TX", "sub_pos": ["PROC (Resistant)", "PSOC"], 
     "rationale": "標靶 Folate Receptor alpha (FRα) ADC。搭載類微管蛋白載荷。利用 ADC 精準傳遞與 Bevacizumab 抗血管生成的協同作用 (Synergy)，旨在克服 PARP 抑制劑或化療耐藥後之 PROC/PSOC 患者需求。",
     "inclusion": ["High-grade Serous 卵巢癌。", "經中央實驗室確認 FRα 表達陽性。", "Part A: 最後一劑鉑類後 90–180 天內惡化。", "Part B: 最後一劑鉑類後 >180 天惡化且必須曾用過 PARPi。"],
     "exclusion": ["先前曾用過帶有 Topoisomerase I 抑制劑載荷之 ADC (如 Enhertu)。", "具有臨床顯著蛋白尿 (UPCR ≥ 2.0)。", "活動性 ILD 肺部病史。"], "ref": "NCT06536348"},
    
    {"cancer": "Ovarian", "name": "REJOICE-Ovarian01", "pharma": "Daiichi Sankyo", "drug": "R-DXd", "pos": "R-TX", "sub_pos": ["PROC (Resistant)"], 
     "rationale": "標靶 Cadherin-6 (CDH6) ADC，搭載強效 DXd 載荷。具備極高 DAR (8) 與強力旁觀者效應 (Bystander Effect)，專攻高度異質性的 PROC 腫瘤環境，挑戰後線生存標準。",
     "inclusion": ["HG Serous 或 Endometrioid PROC 卵巢癌。", "先前接受 1-4 線系統治療。", "需曾用過 Bevacizumab (除非有臨床禁忌)。"],
     "exclusion": ["Low-grade 腫瘤。", "基線 Grade ≥2 Peripheral Neuropathy。", "LVEF < 50%。"], "ref": "JCO 2024"},
    
    {"cancer": "Ovarian", "name": "TroFuse-021", "pharma": "MSD", "drug": "Sac-TMT (MK-2870)", "pos": "P-MT", "sub_pos": ["HRD negative / pHRD"], 
     "rationale": "標靶 Trop-2 ADC。結合 Bevacizumab 微環境調節，旨在優化 pHRD 族群在一線維持治療時的獲益，填補 PARPi 對此族群效果有限的缺口。",
     "inclusion": ["新診斷 FIGO Stage III/IV 卵巢癌。", "HRD 狀態經檢測確認為陰性且 BRCA 為野生型。", "一線含鉑化療後達 CR 或 PR 狀態。"],
     "exclusion": ["BRCA 突變。", "嚴重腸胃病史 (IBD)。", "先前曾用過針對 Trop-2 之 ADC。"], "ref": "ENGOT-ov85"},

    {"cancer": "Ovarian", "name": "DS8201-772 (Enhertu)", "pharma": "AstraZeneca", "drug": "T-DXd", "pos": "R-MT", "sub_pos": ["Platinum Sensitive"], 
     "rationale": "標靶 HER2 ADC。作為救援化療穩定後之精準維持首選。超高 DAR 優勢能有效對抗 HER2 表現者 (含 IHC 1+/2+) 之微小殘留病灶，延長緩解時間。",
     "inclusion": ["HER2 IHC 1+/2+/3+ 確認。", "PSOC 救援化療後達 Non-PD 狀態。", "LVEF ≥ 50%。"],
     "exclusion": ["曾患有需類固醇治療之非感染性 ILD 肺部病史。"], "ref": "JCO 2024"},

    {"cancer": "Endometrial", "name": "MK2870-033", "pharma": "MSD", "drug": "Sac-TMT + Pembro", "pos": "P-MT", "sub_pos": ["IO Maintenance", "NSMP (最大宗亞型)"], 
     "rationale": "標靶 Trop-2 ADC 協同 PD-1 抑制劑。透過免疫原性調節強化 Pembrolizumab 在 pMMR 或 NSMP 族群的應答深度與持續時間。",
     "inclusion": ["pMMR 子宮內膜癌 (中心檢測確認)。", "FIGO III/IV 一線含鉑+Pembro後達 CR/PR。"],
     "exclusion": ["先前接受過任何系統性 IO 治療。"], "ref": "ESMO 2025"},
    
    {"cancer": "Endometrial", "name": "GU-US-682-6769", "pharma": "Gilead", "drug": "SG (Trodelvy)", "pos": "R-TX", "sub_pos": ["pMMR / NSMP", "p53abn"], 
     "rationale": "針對 Trop-2 ADC。利用 SN-38 載荷引發 DNA 損傷，專攻鉑類與免疫失敗救援，具備強大 Bystander Effect。",
     "inclusion": ["復發性內膜癌 (不含肉瘤)。", "鉑類與 PD-1 失敗後進展。"],
     "exclusion": ["先前用過 Trop-2 ADC。", "活動性 CNS 轉移。"], "ref": "JCO 2024"},

    {"cancer": "Cervical", "name": "innovaTV 301", "pharma": "Seagen", "drug": "Tivdak (Tisotumab)", "pos": "R-TX", "sub_pos": ["2L / 3L Therapy"], 
     "rationale": "標靶 Tissue Factor ADC。搭載 MMAE 載荷，旨在克服後線子宮頸癌化療耐藥性，改善生存 OS。",
     "inclusion": ["復發/轉移子宮頸癌。", "先前 1–2 線治療後進展。"],
     "exclusion": ["嚴重眼疾或角膜炎。", "活動性出血傾向。"], "ref": "NEJM 2024"}
]

# --- 3. 指引導航架構：包含子宮頸癌回歸與復發維持 ---
guidelines_nested = {
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "MMRd / MSI-H", "content": "一線首選：Chemo + PD-1 (GY018/RUBY)。"},
            {"title": "NSMP / pMMR", "content": "視 ER/Grade 加權。"},
            {"title": "POLEmut / p53abn", "content": "POLE: 降階；p53: 積極輔助化放療。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "IO Maintenance", "content": "延續一線 IO 直至 PD。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "pMMR / NSMP / p53abn", "content": "標準：Pembro + Lenva 或 Trop-2 ADC。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "維持有效治療直到 PD。"}]}
    ],
    "Ovarian": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [{"title": "HGSC / Endometrioid", "content": "Surgery + Carbo/Pacli ± Bev。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "BRCA mutated", "content": "Olaparib 單藥維持。"}, {"title": "HRD positive (wt)", "content": "Olaparib+Bev 或 Niraparib。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "PROC (Resistant)", "content": "單藥化療 ± Bev 或 FRα ADC。"}, {"title": "PSOC (Sensitive)", "content": "含鉑複方化療 ± Bev。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Platinum Sensitive", "content": "救援緩解後 PARPi 維持治療。"}]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "Locally Advanced (CCRT)", "content": "CCRT ± 同步 IO (A18) 或誘導化療。"},
            {"title": "Early Stage", "content": "開腹根治術。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Metastatic Maint", "content": "1L IO 維持直至進展。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "1L Recurrent", "content": "Pembro + 化療 ± Bev。"},
            {"title": "2L / 3L Therapy", "content": "Tivdak (TF-ADC)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "持續有效之二/三線治療。"}]}
    ]
}

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
    st.session_state.selected_trial = ongoing_db[0]['name']

with st.sidebar:
    st.markdown("<h3 style='color: #6A1B9A;'>🤖 AI 實證決策助理</h3>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 病歷數據分析", expanded=True):
        p_notes = st.text_area("輸入病歷 (含分子標記)", height=250)
        if st.button("🚀 開始分析"):
            if api_key and p_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = get_gemini_model()
                    if model:
                        prompt = f"分析：{p_notes}。參考里程碑：{milestone_db} 及招募中：{ongoing_db}。建議最佳路徑。"
                        st.write(model.generate_content(prompt).text)
                    else: st.error("找不到可用 AI 模型。")
                except Exception as e: st.error(f"AI 異常: {e}")

# --- 6. 主頁面：導航地圖 ---
st.markdown("<div class='main-title'>婦癌臨床導航儀表板 (2026 最終全功能版)</div>", unsafe_allow_html=True)
cancer_type = st.radio("第一步：選擇癌症類型", ["Endometrial", "Ovarian", "Cervical"], horizontal=True)

st.subheader("第二步：點擊 📚 實證里程碑 或 📍 招募中試驗 (與 SoC 同步對照)")
cols = st.columns(4)
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
                    st.success(f"**藥物:** {m['drug']}\n\n**核心結論:** {m['summary']}")
            
            # B. 招募中試驗 (📍)
            rel_trials = [t for t in ongoing_db if t["cancer"] == cancer_type and t["pos"] == stage["id"] and any(s in sub["title"] for s in t["sub_pos"])]
            for t in rel_trials:
                label = f"📍 {t['pharma']} | {t['name']}"
                ukey = f"btn_{t['name']}_{stage['id']}_{sub['title'].replace(' ', '')}"
                with st.popover(label, use_container_width=True):
                    st.info(f"**Rationale:** {t['rationale'][:150]}...")
                    if st.button("📊 開啟深度分析報告", key=ukey):
                        st.session_state.selected_trial = t['name']
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 7. 招募中試驗深度報告 ---
st.divider()
t_options = [t["name"] for t in ongoing_db if t["cancer"] == cancer_type]
if t_options:
    try: curr_idx = t_options.index(st.session_state.selected_trial)
    except: curr_idx = 0
    selected_name = st.selectbox("🎯 切換招募中試驗報告：", t_options, index=curr_idx)
    t = next(it for it in ongoing_db if it["name"] == selected_name)

    st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #E0E0E0; padding-bottom:10px; font-weight:900;'>📋 {t['name']} 招募中深度解析</h2>", unsafe_allow_html=True)

    r1, r2 = st.columns([1.3, 1])
    with r1:
        st.markdown("<div style='background:#E3F2FD; border-left:10px solid #1976D2; padding:15px; border-radius:10px;'><b>💉 Rationale & 機轉</b></div>", unsafe_allow_html=True)
        st.write(f"**核心藥物:** {t['drug']}")
        st.success(t['rationale'])

    with r2:
        st.markdown("<div style='background:#E8F5E9; border-left:8px solid #2E7D32; padding:15px; border-radius:10px;'><b>✅ Inclusion Criteria (納入標準)</b></div>", unsafe_allow_html=True)
        for inc in t.get('inclusion', []): st.write(f"• **{inc}**")

    st.markdown("<div style='background:#FFEBEE; border-left:8px solid #C62828; padding:15px; border-radius:10px; margin-top:10px;'><b>❌ Exclusion Criteria (排除標準)</b></div>", unsafe_allow_html=True)
    for exc in t.get('exclusion', []): st.write(f"• **{exc}**")
    st.markdown("</div>", unsafe_allow_html=True)
