import streamlit as st
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events
import google.generativeai as genai

# --- 高級視覺化配置 (CSS) ---
st.set_page_config(page_title="婦癌臨床試驗導航", layout="wide")

st.markdown("""
    <style>
    /* 全域字體與背景 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', sans-serif;
        font-size: 20px !important;
        background-color: #F8F9FB;
        color: #2C3E50;
    }
    .main-title {
        font-size: 46px !important;
        font-weight: 800;
        color: #264653;
        border-left: 10px solid #2A9D8F;
        padding-left: 20px;
        margin-bottom: 30px;
    }
    /* 卡片式設計 */
    .stAlert, .detail-box {
        border-radius: 20px !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        padding: 30px !important;
        background-color: white !important;
    }
    .detail-box {
        border-top: 8px solid #2A9D8F !important;
    }
    /* 側邊欄優化 */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E0E0E0;
    }
    /* Tab 字體放大 */
    .stTabs [data-baseweb="tab"] {
        font-size: 24px !important;
        height: 60px;
        color: #666;
    }
    .stTabs [aria-selected="true"] {
        color: #2A9D8F !important;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 臨床試驗資料庫 (內容強化) ---
if 'trials_db' not in st.session_state:
    st.session_state.trials_db = [
        {
            "cancer": "Endometrial", "name": "GU-US-682-6769", 
            "pos": "二/三線復發", "drug": "Sacituzumab Govitecan (SG)",
            "rationale": "標靶 **Trop-2** 的抗體藥物複合體 (ADC)。其機轉係利用 Anti-Trop-2 Antibody 將強效的 Topoisomerase I Inhibitor 直接送入腫瘤細胞，透過 **Bystander Effect (旁觀者效應)** 殺傷鄰近 Trop-2 低表達的癌細胞。",
            "protocol": "SG 10mg/kg 靜脈注射 (D1, D8 Q21D) 每三週一循環。",
            "inclusion": ["進展性或復發性 EC", "先前接受過 Platinum 化療", "先前接受過 Anti-PD-1/L1 (如 Pembro)", "ECOG 0-1", "臟器功能良好"],
            "exclusion": ["Uterine Sarcoma (子宮肉瘤)", "先前曾用過 Trop-2 ADC", "活動性 CNS 轉移"]
        },
        {
            "cancer": "Endometrial", "name": "MK2870-033", 
            "pos": "一線維持治療", "drug": "Sac-TMT + Pembro",
            "rationale": "結合新型 Trop-2 ADC 與 PD-1 抑制劑。ADC 誘導細胞凋亡並釋放腫瘤抗原，與 **Pembrolizumab** 產生協同作用，強化 T 細胞對腫瘤的辨識力。",
            "protocol": "Induction: Carbo+Taxel+Pembro (Q3W x6) -> Maintenance: Pembro +/- Sac-TMT。",
            "inclusion": ["pMMR 患者", "新診斷 Stage III/IV 或初次復發", "需提供檢體送至英國中央實驗室檢測"],
            "exclusion": ["Sarcoma", "先前曾使用過 Pembro 治療", "活動性自體免疫疾病"]
        },
        {
            "cancer": "Ovarian", "name": "DOVE (APGOT-OV07)", 
            "pos": "抗藥性復發", "drug": "Dostarlimab + Bevacizumab",
            "rationale": "專對 **透明細胞癌 (OCCC)** 設計。Dostarlimab 恢復 T 細胞功能，搭配 Bevacizumab 阻斷 VEGF，改善腫瘤微環境之缺氧與免疫抑制。",
            "protocol": "Arm A: Dostarlimab 單用; Arm B: Dostarlimab + Beva (15mg/kg Q3W)。",
            "inclusion": ["OCCC 組織型態 > 50%", "Platinum-resistant (PD < 12m)", "先前治療線數不超過 5 線"],
            "exclusion": ["先前用過免疫檢查點抑制劑", "臨床顯著腸阻塞 (Bowel Obstruction)"]
        },
        {
            "cancer": "Ovarian", "name": "DS8201-772 (T-DXd)", 
            "pos": "一線維持治療", "drug": "Trastuzumab Deruxtecan (Enhertu)",
            "rationale": "標靶 **HER2** 之 ADC。搭載強效 Topoisomerase I 抑制劑，具備極高藥物抗體比 (DAR)，對於 **HER2 Low (1+/2+)** 患者亦展現強大臨床效益。",
            "protocol": "T-DXd 5.4mg/kg Q3W 搭配或不搭配 Bevacizumab 15mg/kg。",
            "inclusion": ["HER2 表現 (IHC 3+/2+/1+) 確認", "BRCA WT 或 HRD 結果不適合 PARPi", "一線治療後穩定者"],
            "exclusion": ["ILD/肺炎病史", "先前接受過 HER2 標靶藥物", "LVEF < 50%"]
        }
    ]

# --- 2. 側邊欄 ---
with st.sidebar:
    st.markdown("### 🤖 Gemini 決策建議")
    api_key = st.text_input("API Key", type="password")
    patient_info = st.text_area("患者臨床背景描述", height=250, placeholder="例：65y/o OCCC, stage IIIC, Platinum PD...")
    if st.button("🚀 開始分析"):
        if api_key and patient_info:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-pro')
                prompt = f"你是一位台灣婦癌專家。資料：{st.session_state.trials_db}。分析患者：{patient_info}。請建議適合試驗、藥物機轉理由及入案優勢。請用繁體中文回答。"
                response = model.generate_content(prompt)
                st.info(response.text)
            except Exception as e: st.error(f"連線異常: {e}")

# --- 3. 主頁面：河流圖與連動 ---
st.markdown("<div class='main-title'>婦癌病程發展與臨床試驗導航</div>", unsafe_allow_html=True)
st.write("請切換癌別，並點擊右側 **「試驗名稱」** 方塊獲取 Protocol 細節。")

tab_ec, tab_oc = st.tabs(["子宮內膜癌 (Endometrial)", "卵巢癌 (Ovarian)"])

def render_pretty_sankey(cancer_type):
    # 定義更直觀的病程節點
    nodes = ["初診 (Dx)", "一線治療 (1L)", "維持期 (Maint.)", "復發/後線 (Recurr.)"]
    node_colors = ["#E9C46A", "#F4A261", "#E76F51", "#264653"] # 莫蘭迪色系
    
    filtered_trials = [t for t in st.session_state.trials_db if t["cancer"].startswith(cancer_type)]
    
    sources, targets, values, link_labels = [], [], [], []
    
    for i, t in enumerate(filtered_trials):
        trial_node_idx = len(nodes) + i
        nodes.append(t["name"])
        node_colors.append("#2A9D8F") # 試驗節點統一使用青色
        
        if "維持" in t["pos"]:
            sources.extend([1, 2]); targets.extend([2, trial_node_idx]); values.extend([1, 1]); link_labels.extend(["標準流程", t["name"]])
        elif "復發" in t["pos"]:
            sources.extend([0, 3]); targets.extend([3, trial_node_idx]); values.extend([1, 1]); link_labels.extend(["病情發展", t["name"]])

    fig = go.Figure(data=[go.Sankey(
        node = dict(pad=40, thickness=35, label=nodes, color=node_colors, font=dict(size=18, color="#2C3E50")),
        link = dict(source=sources, target=targets, value=values, color="rgba(42, 157, 143, 0.2)")
    )])
    fig.update_layout(height=450, margin=dict(l=20, r=20, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)")
    
    # 使用 plotly_events 捕捉點擊
    selected = plotly_events(fig, click_event=True, key=f"sankey_{cancer_type}")
    return selected, nodes

selected_trial_name = None

with tab_ec:
    clicked_ec, nodes_ec = render_pretty_sankey("Endometrial")
    if clicked_ec:
        idx = clicked_ec[0]['pointNumber']
        if nodes_ec[idx] in [t["name"] for t in st.session_state.trials_db]:
            selected_trial_name = nodes_ec[idx]

with tab_oc:
    clicked_oc, nodes_oc = render_pretty_sankey("Ovarian")
    if clicked_oc:
        idx = clicked_oc[0]['pointNumber']
        if nodes_oc[idx] in [t["name"] for t in st.session_state.trials_db]:
            selected_trial_name = nodes_oc[idx]

# --- 4. 詳情呈現 (卡片式 UI) ---
st.divider()

if selected_trial_name:
    t = next(it for it in st.session_state.trials_db if it["name"] == selected_trial_name)
    st.markdown(f"<div class='detail-box'>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='color:#264653; border-bottom: 2px solid #E0E0E0; padding-bottom:10px;'>📋 {t['name']} 試驗詳情</h2>", unsafe_allow_html=True)
    
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown(f"### 🧪 藥物機轉：{t['drug']}")
        st.info(t['rationale'])
        
        st.markdown("### 💉 給藥 Protocol")
        st.success(t['protocol'])
        st.write(f"**臨床階段:** {t['pos']}")

    with col_img := st.empty(): # 用於預留圖片位置
        pass

    with c2:
        st.markdown("### ✅ 入案標準 (Inclusion)")
        for inc in t['inclusion']: st.markdown(f"- {inc}")
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### ❌ 排除標準 (Exclusion)")
        for exc in t['exclusion']: st.markdown(f"- {exc}")
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown("""
        <div style='text-align: center; padding: 50px; color: #95A5A6; border: 2px dashed #BDC3C7; border-radius: 20px;'>
            <h3>👋 請點擊上方圖表中右側的「試驗名稱」方塊</h3>
            <p>系統將為您帶出該試驗的完整藥物機轉、給藥方式與入案條件。</p>
        </div>
    """, unsafe_allow_html=True)
