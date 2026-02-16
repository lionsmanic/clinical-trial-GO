import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床導航與實證圖書館 (2026 最終全功能版) ---
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

    /* 大階段方塊：高度隨內容撐開 */
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

    /* 子區塊 (SoC 與分子分型) */
    .sub-block {
        margin: 2px 4px; padding: 4px;
        border-radius: 6px; background: #F1F3F5;
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

    /* 階段顏色定義 */
    .card-p-tx { border-color: #2E7D32; }
    .header-p-tx { background: linear-gradient(135deg, #43A047, #2E7D32); }
    .card-p-mt { border-color: #1565C0; }
    .header-p-mt { background: linear-gradient(135deg, #1E88E5, #1565C0); }
    .card-r-tx { border-color: #E65100; }
    .header-r-tx { background: linear-gradient(135deg, #FB8C00, #E65100); }
    .card-r-mt { border-color: #6A1B9A; }
    .header-r-mt { background: linear-gradient(135deg, #8E24AA, #6A1B9A); }

    /* --- 試驗按鈕標記：高對比深色文字 --- */
    .stPopover button { 
        font-weight: 900 !important; font-size: 12px !important; 
        border-radius: 4px !important; margin-top: 1px !important;
        padding: 1px 6px !important; width: 100% !important; 
        text-align: left !important; color: #1A1A1A !important; 
        border: 1px solid rgba(0,0,0,0.15) !important;
    }

    /* 已發表實證 (Evidence Milestone) 色彩 */
    .stPopover button[aria-label*="📚"] { background: #ECEFF1 !important; border-left: 5px solid #455A64 !important; }

    /* 招募中藥廠背景配色 */
    .stPopover button[aria-label*="Eli Lilly"] { background: #FCE4EC !important; border-left: 5px solid #E91E63 !important; } 
    .stPopover button[aria-label*="Daiichi Sankyo"] { background: #E8F5E9 !important; border-left: 5px solid #4CAF50 !important; } 
    .stPopover button[aria-label*="MSD"] { background: #E3F2FD !important; border-left: 5px solid #1976D2 !important; } 
    .stPopover button[aria-label*="AstraZeneca"] { background: #F3E5F5 !important; border-left: 5px solid #8E24AA !important; } 
    .stPopover button[aria-label*="GSK"] { background: #FFF3E0 !important; border-left: 5px solid #F57C00 !important; } 

    .detail-section { background: white; border-radius: 18px; padding: 25px; margin-top: 10px; border: 1px solid #CFD8DC; box-shadow: 0 10px 40px rgba(0,0,0,0.05); }
    .hr-big-val { font-family: 'Roboto', sans-serif; font-size: 50px !important; font-weight: 900; color: #D84315; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 里程碑實證資料庫 (已發表與共識試驗) ---
milestone_db = [
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H"], "name": "RUBY (NCT03981796)", "drug": "Dostarlimab + CP", "summary": "死亡風險降低 68% (HR 0.32)。確立 dMMR 族群一線免疫治療地位。"},
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H", "NSMP"], "name": "NRG-GY018", "drug": "Pembrolizumab + CP", "summary": "dMMR 族群 HR 0.30，顯著降低疾病進展風險 70%。FDA 已核准用於所有晚期患者。"},
    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["pMMR / NSMP"], "name": "KEYNOTE-775", "drug": "Pembro + Lenvatinib", "summary": "5年追蹤顯示持久 OS 獲益 (16.7% vs 7.3%)。確立二線標準治療。"},
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Surgery / CCRT / 1L"], "name": "KEYNOTE-A18", "drug": "Pembro + CCRT", "summary": "36個月總體存活率提升至 82.6%。確立為 III-IVA 期患者新標準。"},
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutated"], "name": "SOLO-1", "drug": "Olaparib", "summary": "7年後仍有 67% 存活，具潛在「治癒」能力 (HR 0.33)。"},
    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PROC"], "name": "MIRASOL", "drug": "Mirvetuximab", "summary": "首個在 PROC 中證明 OS 獲益的 ADC 試驗 (HR 0.67)。"}
]

# --- 2. 進行中試驗資料庫 (8 核心) ---
ongoing_db = [
    {"cancer": "Ovarian", "name": "FRAmework-01", "pharma": "Eli Lilly", "drug": "LY4170156 + Bev", "pos": "R-TX", "sub_pos": ["PSOC", "PROC"], "summary": "針對 FRα+ 患者。利用 ADC 精準傳遞與 Bev 的血管協同作用克服耐藥。"},
    {"cancer": "Ovarian", "name": "REJOICE-Ovarian01", "pharma": "Daiichi Sankyo", "drug": "R-DXd", "pos": "R-TX", "sub_pos": ["PROC"], "summary": "標靶 CDH6 ADC，具強力旁觀者效應，解決 PROC 高度異質性。"},
    {"cancer": "Ovarian", "name": "TroFuse-021", "pharma": "MSD", "drug": "Sac-TMT", "pos": "P-MT", "sub_pos": ["HRD negative / Unknown"], "summary": "針對 pHRD 族群優化一線維持獲益。"},
    {"cancer": "Endometrial", "name": "MK2870-033", "pharma": "MSD", "drug": "Sac-TMT + Pembro", "pos": "P-MT", "sub_pos": ["IO Maintenance", "NSMP"], "summary": "結合 Trop-2 ADC 強化 Pembrolizumab 在 NSMP 族群的應答。"}
]

# --- 3. 指引導航數據：分子路徑 ---
guidelines_nested = {
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "POLEmut (超突變型)", "content": "預後最佳。早期考慮降階治療。"},
            {"title": "MMRd / MSI-H", "content": "免疫敏感。晚期標竿：Chemo + PD-1 (RUBY/GY018)。"},
            {"title": "NSMP (最大宗亞型)", "content": "IHC MMR Intact / p53 wt / POLE wt。<br>分層受 ER 狀態、Grade 與 LVSI 影響。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "IO Maintenance", "content": "延續一線免疫藥物 (Pembro/Dostarlimab) 直到 PD。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "MMRd / MSI-H", "content": "PD-1 單藥高反應率。"}, {"title": "pMMR / NSMP", "content": "標準二線方案：Pembrolizumab + Lenvatinib。"}]}
    ],
    "Ovarian": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [{"title": "HGSC / Endometrioid", "content": "PDS/IDS 手術 + Carbo/Pacli ± Bevacizumab。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "BRCA mutated", "content": "Olaparib 單藥或併用 Bev。"}, {"title": "HRD negative / Unknown", "content": "Bev 續用或觀察；評估 Niraparib 獲益。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "PROC (Resistant)", "content": "單藥化療 ± Bev 或 Elahere (FRα+)。"}]}
    ]
}

# --- 4. AI 模型選擇器 (最終修正版) ---
def get_gemini_model():
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model
    except:
        return None

# --- 5. 側邊欄 AI 媒合 ---
with st.sidebar:
    st.markdown("<h3 style='color: #6A1B9A;'>🤖 AI 臨床媒合助理</h3>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 患者實證深度分析", expanded=True):
        p_notes = st.text_area("輸入病歷摘要", height=200)
        if st.button("🚀 開始臨床分析"):
            if api_key and p_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = get_gemini_model()
                    prompt = f"分析病歷：{p_notes}。請參考里程碑資料：{milestone_db} 及進行中試驗：{ongoing_db} 提供媒合建議。"
                    st.write(model.generate_content(prompt).text)
                except Exception as e: st.error(f"AI 異常: {e}")

# --- 6. 主頁面：緊湊導航儀表板 ---
st.markdown("<div class='main-title'>婦癌臨床導航儀表板 (指引實證與研究整合版)</div>", unsafe_allow_html=True)
cancer_type = st.radio("第一步：選擇癌症類型", ["Endometrial", "Ovarian"], horizontal=True)

st.subheader("第二步：臨床實證 (📚) 與進行中試驗 (📍) 對照地圖")
cols = st.columns(4)
stages_data = guidelines_nested[cancer_type]

for i, stage in enumerate(stages_data):
    with cols[i]:
        st.markdown(f"""<div class='big-stage-card card-{stage['css']}'><div class='big-stage-header header-{stage['css']}'>{stage['header']}</div>""", unsafe_allow_html=True)
        for sub in stage['subs']:
            st.markdown(f"""<div class='sub-block'><div class='sub-block-title'>📘 {sub['title']}</div><div class='sub-block-content'>{sub['content']}</div>""", unsafe_allow_html=True)
            
            # A. 顯示里程碑實證 (Evidence Library)
            relevant_milestones = [m for m in milestone_db if m["cancer"] == cancer_type and m["pos"] == stage["id"] and any(s in sub["title"] for s in m["sub_pos"])]
            for m in relevant_milestones:
                with st.popover(f"📚 {m['name']} | {m['drug']}", use_container_width=True):
                    st.success(m["summary"])
            
            # B. 顯示進行中試驗 (Ongoing Trials)
            relevant_trials = [t for t in ongoing_db if t["cancer"] == cancer_type and t["pos"] == stage["id"] and any(s in sub["title"] for s in t["sub_pos"])]
            for t in relevant_trials:
                label = f"📍 {t['pharma']} | {t['name']} | {t['drug']}"
                with st.popover(label, use_container_width=True):
                    st.info(t["summary"])
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
