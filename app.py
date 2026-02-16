import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床導航與實證全景圖 (2026 最終整合版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=Roboto:wght@400;700;900&display=swap');
    
    /* === 極致緊緻化 UI 與 高對比度文字 === */
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', 'Roboto', sans-serif;
        background-color: #F8F9FA;
        color: #1A1A1A;
        font-size: 19px !important;
        line-height: 1.1;
    }

    .main-title {
        font-size: 32px !important; font-weight: 900; color: #004D40;
        padding: 5px 0; border-bottom: 3px solid #4DB6AC; margin-bottom: 5px;
    }

    /* 大階段方塊：高度隨內容撐開，零留白 */
    .big-stage-card {
        border-radius: 10px; padding: 0px; 
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        border: 2px solid transparent;
        background: white; margin-bottom: 4px; overflow: hidden;
        height: auto !important; min-height: 0 !important;
    }
    .big-stage-header {
        font-size: 17px !important; font-weight: 900; color: white;
        padding: 5px; text-align: center; margin: 0 !important;
    }

    /* 子區塊 (SoC 與分子亞型) */
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
        margin-bottom: 2px;
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

    /* --- 按鈕樣式：深黑色加粗 (#1A1A1A) --- */
    .stPopover button { 
        font-weight: 900 !important; font-size: 12px !important; 
        border-radius: 4px !important; margin-top: 1px !important;
        padding: 1px 6px !important; width: 100% !important; 
        text-align: left !important; color: #1A1A1A !important; 
        border: 1px solid rgba(0,0,0,0.15) !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
    }
    
    /* 📚 里程碑實證 (Evidence Milestone) 經典配色 */
    .stPopover button[aria-label*="📚"] { background: #ECEFF1 !important; border-left: 5px solid #455A64 !important; }

    /* 📍 招募中試驗 (Ongoing) 藥廠配色 */
    .stPopover button[aria-label*="Eli Lilly"] { background: #FCE4EC !important; border-left: 5px solid #E91E63 !important; } 
    .stPopover button[aria-label*="Daiichi Sankyo"] { background: #E8F5E9 !important; border-left: 5px solid #4CAF50 !important; } 
    .stPopover button[aria-label*="MSD"] { background: #E3F2FD !important; border-left: 5px solid #1976D2 !important; } 
    .stPopover button[aria-label*="AstraZeneca"] { background: #F3E5F5 !important; border-left: 5px solid #8E24AA !important; } 
    .stPopover button[aria-label*="GSK"] { background: #FFF3E0 !important; border-left: 5px solid #F57C00 !important; } 
    .stPopover button[aria-label*="Gilead"] { background: #E1F5FE !important; border-left: 5px solid #03A9F4 !important; } 
    .stPopover button[aria-label*="Seagen"] { background: #EEEEEE !important; border-left: 5px solid #212121 !important; } 

    .detail-section { background: white; border-radius: 18px; padding: 25px; border: 1px solid #CFD8DC; box-shadow: 0 10px 40px rgba(0,0,0,0.05); }
    .hr-big-val { font-family: 'Roboto', sans-serif; font-size: 50px !important; font-weight: 900; color: #D84315; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 里程碑實證資料庫 (📚 Milestone Library - 黃金十年) ---
milestone_db = [
    # 子宮內膜癌
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H", "pMMR / NSMP"], "name": "📚 RUBY (Dostarlimab)", "drug": "Dostarlimab + CP", 
     "summary": "族群：晚期或復發 EC。結果：dMMR 的 PFS 獲益顯著，死亡風險降低 68% (HR 0.32)。全人群 mOS 顯著延長至 44.6 個月 (vs 28.2m)。"},
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H", "NSMP"], "name": "📚 NRG-GY018 (Pembrolizumab)", "drug": "Pembrolizumab + CP", 
     "summary": "族群：晚期或復發 EC。結果：dMMR PFS HR 0.30；pMMR 亦有顯著改善 (HR 0.54)。確立一線 Immuno-chemo 地位。"},
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H", "pMMR / NSMP"], "name": "📚 DUO-E", "drug": "Durvalumab ± Olaparib", 
     "summary": "族群：晚期/復發 EC。結果：Durvalumab+Olaparib 三藥聯合將 PFS HR 降至 0.57，優於單用 IO。提示 pMMR 患者有協同效應。"},
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H"], "name": "📚 AtTEnd", "drug": "Atezolizumab + CP", 
     "summary": "族群：晚期/復發 EC。結果：dMMR 獲益更明顯。強化一線 dMMR 治療路徑。"},
    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["pMMR / NSMP"], "name": "📚 KEYNOTE-775", "drug": "Pembro + Lenvatinib", 
     "summary": "族群：既往含鉑進展之晚期 EC。結果：PFS 與 OS 均顯著優於化療，pMMR 二線標準。"},
    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["MMRd / MSI-H"], "name": "📚 GARNET", "drug": "Dostarlimab", 
     "summary": "單臂試驗，在 dMMR/MSI-H 患者中 ORR 達 45.5% 且反應持久。"},

    # 子宮頸癌
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["CCRT (LA / 1L)"], "name": "📚 KEYNOTE-A18", "drug": "Pembrolizumab + CCRT", 
     "summary": "族群：高風險局部晚期。結果：36個月存活率提升至 82.6% (HR 0.67)，支持為 LACC 新標準。"},
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["CCRT (LA / 1L)"], "name": "📚 INTERLACE", "drug": "Induction Chemo (6wk)", 
     "summary": "結果：先給 6週 Carbo/Pacli 再 CCRT，5年 OS 顯著改善 (80% vs 72%)。"},
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["CCRT (LA / 1L)"], "name": "📚 CALLA (陰性)", "drug": "Durvalumab + CCRT", 
     "summary": "提示局部晚期免疫併用需更精準族群分流。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["1L Recurrent"], "name": "📚 KEYNOTE-826", "drug": "Pembro + Chemo ± Bev", 
     "summary": "族群：持續性/復發/轉移。結果：OS 持續顯著改善，R/M 一線核心方案。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["1L Recurrent"], "name": "📚 BEATcc", "drug": "Atezolizumab + Chemo + Bev", 
     "summary": "R/M 一線 PFS 與 OS 皆顯著改善，成為新選項。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["2L / 3L Therapy"], "name": "📚 innovaTV 301", "drug": "Tisotumab vedotin", 
     "summary": "族群：二/三線 ADC。結果：OS 獲益顯著優於化療 (11.5m vs 9.5m)。"},
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Early (Surgery)"], "name": "📚 LACC Trial", "drug": "MIS vs Open", 
     "summary": "微創手術復發率與死亡率顯著較高 (HR 6.00)，根治標準重回開腹。"},
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Early (Surgery)"], "name": "📚 SHAPE Trial", "drug": "Simple Hysterectomy", 
     "summary": "低風險者單純全子宮切除不劣於根治術，且併發症少。"},

    # 卵巢癌
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutated"], "name": "📚 SOLO-1", "drug": "Olaparib", 
     "summary": "BRCAm 一線維持里程碑。PFS 巨幅改善，7年存活率 67%。"},
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive (wt)", "HRD negative / pHRD"], "name": "📚 PRIMA", "drug": "Niraparib", 
     "summary": "建立「不限 BRCA」維持概念。整體 PFS 改善，HRD 獲益最大。"},
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive (wt)"], "name": "📚 PAOLA-1", "drug": "Olaparib + Bevacizumab", 
     "summary": "HRD+ 族群 5年 OS 顯著改善 (HR 0.62)。"},
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive (wt)"], "name": "📚 DUO-O", "drug": "Durva+Chemo+Bev 維持", 
     "summary": "提示卵巢癌免疫需組合 VEGF 與 PARPi 策略較具勝算。"},
    {"cancer": "Ovarian", "pos": "R-MT", "sub_pos": ["Platinum Sensitive"], "name": "📚 NOVA / SOLO2", "drug": "PARPi Maintenance", 
     "summary": "復發維持 PFS 顯著改善。SOLO2 顯示具臨床意義的 OS 獲益。"},
    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PROC (Resistant)"], "name": "📚 MIRASOL", "drug": "Mirvetuximab (FRα ADC)", 
     "summary": "FRα 高表現 PROC 患者 OS 顯著獲益 (HR 0.67)，確立 FRα 檢測必要性。"},
    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 van Driel HIPEC", "drug": "Surgery + HIPEC", 
     "summary": "NACT 後之間歇減積手術加 HIPEC 改善 RFS/OS。"},
    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 LION Trial", "drug": "No Lymphadenectomy", 
     "summary": "臨床 LN 陰性者，系統性淋巴清掃無存活獲益且併發症增多。"},
]

# --- 2. 進行中臨床試驗資料庫 (📍 Ongoing Trials - 8 核心詳盡版) ---
ongoing_trials = [
    {"cancer": "Ovarian", "name": "FRAmework-01 (LY4170156)", "pharma": "Eli Lilly", "drug": "LY4170156 + Bev", "pos": "R-TX", "sub_pos": ["PSOC (Sensitive)", "PROC (Resistant)", "MOC 晚期/復發"], 
     "rationale": "標靶 FRα ADC。聯用 Bevacizumab 可產生血管重塑協同效應 (Synergy)，提升 ADC 滲透力，解決 PARPi 耐藥後或 MOC 族群需求。",
     "dosing": {"Exp Arm": "LY4170156 3mg/kg + Bev 15mg/kg Q3W", "Control": "TPC 或 Platinum doublet + Bev"},
     "inclusion": ["HG Serous / Carcinosarcoma / MOC", "FRα Expression Positive", "符合 Part A/B PFI 限制"],
     "exclusion": ["先前用過 Topo I ADC", "顯著蛋白尿"], "ref": "ClinicalTrials.gov"},
    
    {"cancer": "Ovarian", "name": "REJOICE-Ovarian01", "pharma": "Daiichi Sankyo", "drug": "R-DXd", "pos": "R-TX", "sub_pos": ["PROC (Resistant)"], 
     "rationale": "標靶 Cadherin-6 (CDH6) ADC。具備強力旁觀者效應，專攻高度異質性的 PROC 腫瘤環境，克服前線化療耐藥。",
     "dosing": {"Exp Arm": "R-DXd 5.6mg/kg IV Q3W", "Control Arm": "Investigator's Choice 單藥化療。"},
     "inclusion": ["HG Serous 或 Endometrioid PROC", "曾接受 1-4 線系統性治療", "需曾用過 Bevacizumab"],
     "exclusion": ["Low-grade 腫瘤", "LVEF < 50%"], "ref": "JCO 2024"},
    
    {"cancer": "Ovarian", "name": "TroFuse-021", "pharma": "MSD", "drug": "Sac-TMT (MK-2870)", "pos": "P-MT", "sub_pos": ["HRD negative / pHRD"], 
     "rationale": "標靶 Trop-2 ADC。透過 ADC 誘導的 ICD 效應協同 Beva，優化 pHRD 族群在一線維時獲益。",
     "inclusion": ["新診斷 FIGO III/IV 卵巢癌", "HRD negative (pHRD)", "1L含鉑後 CR/PR"],
     "exclusion": ["BRCA 突變", "先前用過 Trop-2 ADC"], "ref": "ENGOT-ov85"},

    {"cancer": "Endometrial", "name": "MK2870-033", "pharma": "MSD", "drug": "Sac-TMT + Pembro", "pos": "P-MT", "sub_pos": ["IO Maintenance", "NSMP (最大宗亞型)"], 
     "rationale": "標靶 Trop-2 ADC 協同 PD-1. 強化 Pembrolizumab 在 NSMP 族群的長期應答。",
     "inclusion": ["pMMR 子宮內膜癌 (中心檢測)", "FIGO III/IV 一線含鉑+Pembro後達 CR/PR"],
     "exclusion": ["先前接受過晚期系統性 IO 治療"], "ref": "ESMO 2025"},
    
    {"cancer": "Endometrial", "name": "GU-US-682-6769", "pharma": "Gilead", "drug": "SG (Trodelvy)", "pos": "R-TX", "sub_pos": ["pMMR / NSMP", "p53abn (Copy-number high)"], 
     "rationale": "標靶 Trop-2 ADC. 利用 SN-38 載荷引發 DNA 損傷，專攻鉑類與免疫失敗救援。",
     "inclusion": ["復發性 EC (非肉瘤)", "鉑類與 PD-1 失敗後進展"],
     "exclusion": ["先前用過 Trop-2 ADC"], "ref": "JCO 2024"}
]

# --- 3. 動態模型巡邏與 AI 修復 ---
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

# --- 4. 側邊欄 ---
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = ongoing_trials[0]['name']

with st.sidebar:
    st.markdown("<h3 style='color: #6A1B9A;'>🤖 AI 全方位決策助理</h3>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 患者數據深度分析", expanded=True):
        p_notes = st.text_area("輸入病歷 (含分子/病理)", height=250)
        if st.button("🚀 開始分析"):
            if api_key and p_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = get_gemini_model()
                    if model:
                        prompt = f"分析病歷：{p_notes}。參考實證圖書館：{milestone_db} 與招募中試驗：{ongoing_trials}。提供最佳路徑與理由。"
                        st.write(model.generate_content(prompt).text)
                    else: st.error("找不到可用 AI 模型。")
                except Exception as e: st.error(f"AI 異常: {e}")

# --- 5. 主頁面：緊湊導航儀表板 ---
st.markdown("<div class='main-title'>婦癌臨床導航儀表板 (指引實證與研究整合版)</div>", unsafe_allow_html=True)
cancer_type = st.radio("第一步：選擇癌症類型", ["Endometrial", "Ovarian", "Cervical"], horizontal=True)

# 標題與內容高度緊扣
cols = st.columns(4)
stages_data = guidelines_nested[cancer_type]

for i, stage in enumerate(stages_data):
    with cols[i]:
        st.markdown(f"""<div class='big-stage-card card-{stage['css']}'><div class='big-stage-header header-{stage['css']}'>{stage['header']}</div>""", unsafe_allow_html=True)
        for sub in stage['subs']:
            st.markdown(f"""<div class='sub-block'><div class='sub-block-title'>📘 {sub['title']}</div><div class='sub-block-content'>{sub['content']}</div>""", unsafe_allow_html=True)
            
            # A. 顯示實證里程碑 (📚 Milestone)
            rel_milestones = [m for m in milestone_db if m["cancer"] == cancer_type and m["pos"] == stage["id"] and any(s in sub["title"] for s in m["sub_pos"])]
            for m in rel_milestones:
                with st.popover(f"📚 {m['name']}", use_container_width=True):
                    st.success(f"**藥物:** {m['drug']}\n\n**關鍵實證:** {m['summary']}")
            
            # B. 顯示招募中試驗 (📍 Ongoing)
            rel_trials = [t for t in ongoing_trials if t["cancer"] == cancer_type and t["pos"] == stage["id"] and any(s in sub["title"] for s in t["sub_pos"])]
            for t in rel_trials:
                label = f"📍 {t['pharma']} | {t['name']}"
                ukey = f"btn_{t['name']}_{stage['id']}_{sub['title'].replace(' ', '')}"
                with st.popover(label, use_container_width=True):
                    st.info(f"**Rationale:** {t['rationale'][:150]}...")
                    if st.button("📊 開啟深度分析報告", key=ukey):
                        st.session_state.selected_trial = t['name']
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 6. 招募中試驗深度報告 ---
st.divider()
t_options = [t["name"] for t in ongoing_trials if t["cancer"] == cancer_type]
if t_options:
    try: curr_idx = t_options.index(st.session_state.selected_trial)
    except: curr_idx = 0
    selected_name = st.selectbox("🎯 切換招募中試驗之深度報告：", t_options, index=curr_idx)
    t = next(it for it in ongoing_trials if it["name"] == selected_name)

    st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='color:#004D40; border-bottom:2px solid #E0E0E0; padding-bottom:10px; font-weight:900;'>📋 {t['name']} 招募中試驗深度數據</h2>", unsafe_allow_html=True)

    r1, r2 = st.columns([1.3, 1])
    with r1:
        st.markdown("<div style='background:#E3F2FD; border-left:10px solid #1976D2; padding:15px; border-radius:10px;'><b>💉 Dosing & Rationale</b></div>", unsafe_allow_html=True)
        st.write(f"**核心藥物:** {t['drug']}")
        st.success(f"**機轉詳解:** {t['rationale']}")

    with r2:
        st.markdown("<div style='background:#E8F5E9; border-left:8px solid #2E7D32; padding:15px; border-radius:10px;'><b>✅ Inclusion Criteria</b></div>", unsafe_allow_html=True)
        for inc in t.get('inclusion', []): st.write(f"• **{inc}**")

    st.markdown("<div style='background:#FFEBEE; border-left:8px solid #C62828; padding:15px; border-radius:10px; margin-top:10px;'><b>❌ Exclusion Criteria</b></div>", unsafe_allow_html=True)
    for exc in t.get('exclusion', []): st.write(f"• **{exc}**")
    st.markdown("</div>", unsafe_allow_html=True)
