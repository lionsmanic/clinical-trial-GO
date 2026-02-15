import streamlit as st
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events
import google.generativeai as genai

# --- 🏥 醫學專業視覺配置 ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', sans-serif;
        background-color: #F0F2F2; /* 護眼紙質感 */
        color: #1A3030;
        font-size: 20px !important;
    }
    .main-title {
        font-size: 46px !important;
        font-weight: 800;
        color: #004D40;
        text-align: center;
        padding: 30px;
        background: white;
        border-bottom: 5px solid #00796B;
        margin-bottom: 25px;
    }
    .detail-card {
        background: white;
        border-radius: 20px;
        padding: 40px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        border: 2px solid #B2DFDB;
        margin-top: 20px;
    }
    .section-header {
        font-size: 30px;
        font-weight: 700;
        color: #00796B;
        margin-bottom: 20px;
        border-left: 10px solid #00796B;
        padding-left: 15px;
    }
    .stTabs [data-baseweb="tab"] { font-size: 22px !important; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 資料庫與狀態初始化 ---
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = None

TRIALS_DB = [
    {
        "cancer": "Endometrial", "name": "GU-US-682-6769", 
        "pos": "Recurrence", "drug": "Sacituzumab Govitecan (SG)",
        "rationale": "標靶 **Trop-2** 的 ADC 藥物。透過抗體引導 SN-38 載荷進入細胞，並具備旁觀者效應 (Bystander effect)。",
        "protocol": "SG 10mg/kg IV (D1, D8 Q21D) 直到 PD。",
        "inclusion": ["進展性/復發性 EC", "曾接受 Platinum 化療", "曾接受 Anti-PD-1/L1", "ECOG 0-1"],
        "exclusion": ["子宮肉瘤 (Uterine Sarcoma)", "曾用過 Trop-2 ADC"]
    },
    {
        "cancer": "Endometrial", "name": "MK2870-033", 
        "pos": "Maintenance", "drug": "Sac-TMT + Pembro",
        "rationale": "結合新型 Trop-2 ADC 與 PD-1 抑制劑。ADC 誘導細胞死亡釋放抗原，提升免疫療法之效果。",
        "protocol": "引導期: Carbo+Taxel+Pembro -> 維持期: Pembro +/- Sac-TMT。",
        "inclusion": ["pMMR 患者", "新診斷 Stage III/IV", "需中央實驗室檢測"],
        "exclusion": ["先前用過 Pembro", "自體免疫疾病"]
    },
    {
        "cancer": "Ovarian", "name": "DOVE (APGOT-OV07)", 
        "pos": "Recurrence", "drug": "Dostarlimab + Bevacizumab",
        "rationale": "針對 **透明細胞癌 (OCCC)**。Dostarlimab 恢復 T 細胞活力，Bevacizumab 抑制血管增生。",
        "protocol": "Arm B: Dostarlimab + Beva (15mg/kg Q3W)。",
        "inclusion": ["OCCC 組織型態 > 50%", "Platinum-resistant (PD < 12m)"],
        "exclusion": ["先前用過 PD-1 抑制劑", "腸阻塞病史"]
    },
    {
        "cancer": "Ovarian", "name": "DS8201-772", 
        "pos": "Maintenance", "drug": "T-DXd (Enhertu)",
        "rationale": "標靶 **HER2** 之 ADC。對於 HER2 低表達 (1+/2+) 同樣有效。",
        "protocol": "T-DXd 5.4mg/kg Q3W +/- Bevacizumab。",
        "inclusion": ["HER2 表現 (IHC 1+/2+/3+)", "BRCA WT / HRD", "一線穩定後"],
        "exclusion": ["肺纖維化病史 (ILD)", "LVEF < 50%"]
    }
]

# --- 2. 側邊欄 AI ---
with st.sidebar:
    st.markdown("### 🤖 專家 AI 媒合")
    api_key = st.text_input("Gemini API Key", type="password")
    patient_notes = st.text_area("患者臨床背景", height=250)
    if st.button("🚀 進行分析"):
        if api_key and patient_notes:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-pro')
                prompt = f"你是一位婦癌專家。資料：{TRIALS_DB}。分析患者：{patient_notes}。建議試驗與理由。"
                response = model.generate_content(prompt)
                st.info(response.text)
            except Exception as e: st.error(f"AI 異常: {e}")

# --- 3. 主頁面：雙軌制導航 ---
st.markdown("<div class='main-title'>婦癌臨床試驗導航系統</div>", unsafe_allow_html=True)

# 選擇癌別 (作為過濾基礎)
cancer_type = st.radio("第一步：選擇癌別 (Cancer Type)", ["Endometrial", "Ovarian"], horizontal=True)

# 河流圖繪製函數
def draw_river_map(cancer_type):
    base_nodes = ["初診 (Dx)", "一線治療 (1L)", "維持期 (Maint.)", "復發期 (Recurr.)"]
    base_colors = ["#FFE082", "#FFB74D", "#81C784", "#E57373"]
    
    filtered_trials = [t for t in TRIALS_DB if t["cancer"] == cancer_type]
    labels = base_nodes.copy()
    colors = base_colors.copy()
    sources, targets, values = [], [], []

    for t in filtered_trials:
        idx = len(labels)
        labels.append(t["name"])
        colors.append("#00897B") # 試驗節點深綠色
        if t["pos"] == "Maintenance":
            sources.extend([1, 2]); targets.extend([2, idx]); values.extend([1, 1])
        elif t["pos"] == "Recurrence":
            sources.extend([0, 3]); targets.extend([3, idx]); values.extend([1, 1])

    fig = go.Figure(data=[go.Sankey(
        node = dict(pad=50, thickness=35, label=labels, color=colors),
        link = dict(source=sources, target=targets, value=values, color="rgba(0, 137, 123, 0.15)")
    )])
    fig.update_layout(height=450, font=dict(size=18), margin=dict(l=15, r=15, t=10, b=10))
    return fig, labels

# 呈現圖表
st.subheader(f"第二步：從河流圖點選 或 下方選單選擇")
col_plot, col_select = st.columns([3, 1])

with col_plot:
    fig, current_labels = draw_river_map(cancer_type)
    # 捕捉點擊事件
    clicked_data = plotly_events(fig, click_event=True, key=f"river_{cancer_type}")
    if clicked_data:
        clicked_idx = clicked_data[0]['pointNumber']
        if clicked_idx < len(current_labels):
            potential_name = current_labels[clicked_idx]
            if potential_name in [t["name"] for t in TRIALS_DB]:
                st.session_state.selected_trial = potential_name

with col_select:
    st.write(" ")
    # 下拉選單同步過濾
    trial_options = [t["name"] for t in TRIALS_DB if t["cancer"] == cancer_type]
    
    # 如果點擊了圖表，同步更新下拉選單的 index
    try:
        current_index = trial_options.index(st.session_state.selected_trial) if st.session_state.selected_trial in trial_options else 0
    except ValueError:
        current_index = 0

    select_val = st.selectbox("🎯 直接搜尋試驗", trial_options, index=current_index)
    if select_val:
        st.session_state.selected_trial = select_val

# --- 4. 詳情呈現區 ---
st.divider()

if st.session_state.selected_trial:
    t = next(it for it in TRIALS_DB if it["name"] == st.session_state.selected_trial)
    st.markdown("<div class='detail-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='section-header'>📋 {t['name']} 完整 Protocol</div>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"### 🧪 藥物機轉：{t['drug']}")
        st.info(t['rationale'])
        
        st.markdown("### 💉 給藥方式")
        st.success(t['protocol'])
        st.write(f"**臨床階段:** {t['pos']}")
    
    with c2:
        st.markdown("### ✅ 入案標準 (Inclusion)")
        for inc in t['inclusion']: st.markdown(f"- **{inc}**")
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### ❌ 排除標準 (Exclusion)")
        for exc in t['exclusion']: st.markdown(f"- {exc}")
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("👆 請從河流圖點擊試驗方塊，或從選單中選擇一個試驗來檢視內容。")

# 病程河流圖參考
