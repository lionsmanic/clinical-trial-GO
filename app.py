import streamlit as st
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events
import google.generativeai as genai

# --- 護眼醫學視覺化配置 ---
st.set_page_config(page_title="婦癌臨床試驗導航", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', sans-serif;
        font-size: 20px !important;
        background-color: #F8FAFB;
        color: #2C3E50;
    }

    .main-title {
        font-size: 42px !important;
        font-weight: 800;
        color: #264653;
        border-left: 10px solid #2A9D8F;
        padding-left: 20px;
        margin-bottom: 30px;
    }

    /* 資訊卡片優化 */
    .detail-card {
        background-color: #FFFFFF;
        border-radius: 20px;
        padding: 35px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.04);
        border: 1px solid #E9EDF0;
        margin-top: 25px;
    }

    .stTabs [data-baseweb="tab"] {
        font-size: 24px !important;
        font-weight: 700;
        height: 65px;
    }
    
    .stTabs [aria-selected="true"] {
        color: #2A9D8F !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 臨床試驗資料庫 ---
if 'trials_db' not in st.session_state:
    st.session_state.trials_db = [
        {
            "cancer": "Endometrial", "name": "GU-US-682-6769", 
            "pos": "Recurrence", "drug": "Sacituzumab Govitecan (SG)",
            "rationale": "標靶 **Trop-2** 的抗體藥物複合體 (ADC)。其機轉係利用 Anti-Trop-2 Antibody 將強效的 Topoisomerase I Inhibitor 直接送入腫瘤細胞，透過 **Bystander Effect (旁觀者效應)** 殺傷鄰近 Trop-2 低表達的癌細胞。",
            "protocol": "SG 10mg/kg 靜脈注射 (D1, D8 Q21D)。直到疾病進展 (PD)。",
            "inclusion": ["進展性或復發性 EC", "先前接受過 Platinum 化療", "先前接受過 Anti-PD-1/L1", "ECOG 0-1"],
            "exclusion": ["子宮肉瘤 (Uterine Sarcoma)", "先前用過 Trop-2 ADC", "活動性 CNS 轉移"]
        },
        {
            "cancer": "Endometrial", "name": "MK2870-033", 
            "pos": "Maintenance", "drug": "Sac-TMT + Pembro",
            "rationale": "結合新型 Trop-2 ADC 與 PD-1 抑制劑。ADC 誘導腫瘤細胞死亡並釋放抗原，協同提升 **Pembrolizumab** 之免疫活化效果。",
            "protocol": "引導期: Carbo+Taxel+Pembro (Q3W x6) -> 維持期: Pembro +/- Sac-TMT。",
            "inclusion": ["pMMR 患者", "新診斷 Stage III/IV 或初次復發", "需提供檢體至中央實驗室檢測"],
            "exclusion": ["Sarcoma", "曾用過 Pembro", "自體免疫疾病"]
        },
        {
            "cancer": "Ovarian", "name": "DOVE (APGOT-OV07)", 
            "pos": "Recurrence", "drug": "Dostarlimab + Bevacizumab",
            "rationale": "針對 **透明細胞癌 (OCCC)**。Dostarlimab 阻斷 PD-1 路徑，結合 Bevacizumab 抑制血管增生，共同改善腫瘤微環境。",
            "protocol": "Arm A: Dostarlimab 單用; Arm B: Dostarlimab + Beva (15mg/kg Q3W)。",
            "inclusion": ["OCCC > 50%", "Platinum-resistant (PD < 12m)", "治療線數不超過 5 線"],
            "exclusion": ["先前接受過免疫檢查點抑制劑", "臨床顯著腸阻塞"]
        },
        {
            "cancer": "Ovarian", "name": "DS8201-772 (T-DXd)", 
            "pos": "Maintenance", "drug": "Trastuzumab Deruxtecan (Enhertu)",
            "rationale": "標靶 **HER2** 之 ADC。搭載強效載荷，對 **HER2 Low (1+/2+)** 同樣有效，旨在第一線穩定後替代或延後 PARPi 的使用。",
            "protocol": "T-DXd 5.4mg/kg Q3W 搭配或不搭配 Bevacizumab 15mg/kg。",
            "inclusion": ["HER2 表現 (IHC 3+/2+/1+)", "BRCA WT 或 HRD 不適合 PARPi", "一線化療後穩定"],
            "exclusion": ["ILD 肺纖維化病史", "曾接受 HER2 標靶治療", "LVEF < 50%"]
        }
    ]

# --- 2. 側邊欄 ---
with st.sidebar:
    st.markdown("### 🤖 AI 決策輔助")
    api_key = st.text_input("Gemini API Key", type="password")
    patient_info = st.text_area("患者臨床描述", height=250)
    if st.button("🚀 開始分析"):
        if api_key and patient_info:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-pro')
                prompt = f"你是一位台灣婦癌專家。現有試驗：{st.session_state.trials_db}。分析患者：{patient_info}。建議適合試驗與理由。"
                response = model.generate_content(prompt)
                st.info(response.text)
            except Exception as e: st.error(f"連線失敗: {e}")

# --- 3. 主頁面：河流圖呈現 ---
st.markdown("<div class='main-title'>婦癌臨床試驗路徑導航</div>", unsafe_allow_html=True)
st.write("💡 **操作指南**：點擊圖表右側的 **「試驗名稱」** 方塊，下方會顯示詳細資訊。")

tab_ec, tab_oc = st.tabs(["子宮內膜癌 (EC)", "卵巢癌 (OC)"])

def draw_sankey_fixed(cancer_type):
    # 修正索引：先定義基礎節點
    base_nodes = ["初診 (Dx)", "一線治療 (1L)", "維持期 (Maint.)", "復發/後線 (Recurr.)"]
    base_colors = ["#E9C46A", "#F4A261", "#8AB17D", "#E76F51"] 
    
    filtered_trials = [t for t in st.session_state.trials_db if t["cancer"].startswith(cancer_type)]
    
    nodes = base_nodes.copy()
    node_colors = base_colors.copy()
    sources, targets, values, labels = [], [], [], []
    
    # 修正後的索引邏輯：使用 len(nodes) 作為下一個可用的索引
    for t in filtered_trials:
        trial_node_idx = len(nodes) 
        nodes.append(t["name"])
        node_colors.append("#2A9D8F") # 試驗節點色
        
        if t["pos"] == "Maintenance":
            # 從 1L -> Maint (1->2), Maint -> Trial (2->Trial)
            sources.extend([1, 2]); targets.extend([2, trial_node_idx]); values.extend([1, 1]); labels.extend(["標準流程", t["name"]])
        elif t["pos"] == "Recurrence":
            # 從 Dx -> Recurr (0->3), Recurr -> Trial (3->Trial)
            sources.extend([0, 3]); targets.extend([3, trial_node_idx]); values.extend([1, 1]); labels.extend(["病情發展", t["name"]])

    fig = go.Figure(data=[go.Sankey(
        node = dict(pad=45, thickness=35, label=nodes, color=node_colors, font=dict(size=18, color="#2C3E50")),
        link = dict(source=sources, target=targets, value=values, color="rgba(42, 157, 143, 0.15)")
    )])
    fig.update_layout(height=450, margin=dict(l=15, r=15, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)")
    
    # 捕捉點擊事件
    selected = plotly_events(fig, click_event=True, key=f"sankey_{cancer_type}_{len(filtered_trials)}")
    return selected, nodes

# 邏輯判斷
selected_trial = None
with tab_ec:
    cl_ec, nodes_ec = draw_sankey_fixed("Endometrial")
    if cl_ec:
        idx = cl_ec[0]['pointNumber']
        if idx < len(nodes_ec) and nodes_ec[idx] in [t["name"] for t in st.session_state.trials_db]:
            selected_trial = nodes_ec[idx]

with tab_oc:
    cl_oc, nodes_oc = draw_sankey_fixed("Ovarian")
    if cl_oc:
        idx = cl_oc[0]['pointNumber']
        if idx < len(nodes_oc) and nodes_oc[idx] in [t["name"] for t in st.session_state.trials_db]:
            selected_trial = nodes_oc[idx]

# --- 4. 詳情呈現 ---
st.divider()

if selected_trial:
    t = next(it for it in st.session_state.trials_db if it["name"] == selected_trial)
    st.markdown("<div class='detail-card'>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='color:#264653;'>📋 {t['name']} 詳情</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(f"### 🧪 藥物機轉：{t['drug']}")
        st.info(t['rationale'])
        
        st.markdown("### 💉 給藥方式")
        st.success(t['protocol'])
    
    with col2:
        st.markdown("### ✅ 入案標準 (Inclusion)")
        for inc in t['inclusion']: st.markdown(f"- {inc}")
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### ❌ 排除標準 (Exclusion)")
        for exc in t['exclusion']: st.markdown(f"- {exc}")
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown("""
        <div style='text-align: center; padding: 60px; color: #95A5A6; border: 2px dashed #DCE4E8; border-radius: 20px;'>
            <h3>👋 請點擊圖表中右側的「試驗方塊」以檢視詳細 Protocol</h3>
        </div>
    """, unsafe_allow_html=True)
