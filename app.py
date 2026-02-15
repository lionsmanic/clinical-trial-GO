import streamlit as st
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events
import google.generativeai as genai

# --- 🏥 專業醫療視覺風格配置 ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', sans-serif;
        background-color: #F8F9FA; /* 柔和淺灰底，不反光 */
        color: #203030;
        font-size: 20px !important;
    }
    .main-title {
        font-size: 44px !important;
        font-weight: 800;
        color: #004D40;
        text-align: center;
        padding: 30px;
        background: #FFFFFF;
        border-radius: 15px;
        margin-bottom: 25px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    .detail-card {
        background: #FFFFFF;
        border-radius: 20px;
        padding: 40px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        border-top: 8px solid #00796B;
        margin-top: 20px;
    }
    .stTabs [data-baseweb="tab"] { font-size: 22px !important; font-weight: 700; height: 60px; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 資料庫與狀態初始化 ---
TRIALS_DB = [
    {
        "cancer": "Endometrial", "name": "GU-US-682-6769", 
        "pos": "Recurrence", "drug": "Sacituzumab Govitecan (SG)",
        "rationale": "標靶 **Trop-2** 的 ADC 藥物。搭載 Topoisomerase I 抑制劑，具備強大的殺傷力與旁觀者效應。",
        "protocol": "SG 10mg/kg IV (D1, D8 Q21D) 直到疾病進展。",
        "inclusion": ["進展性/復發性 EC", "曾用過 Platinum & Anti-PD-1", "ECOG 0-1"],
        "exclusion": ["子宮肉瘤 (Uterine Sarcoma)", "曾用過 Trop-2 ADC"]
    },
    {
        "cancer": "Endometrial", "name": "MK2870-033", 
        "pos": "Maintenance", "drug": "Sac-TMT + Pembro",
        "rationale": "新型 Trop-2 ADC 搭配免疫檢查點抑制劑，強化一線化療後的緩解效果。",
        "protocol": "Induction (6 cycles) -> Maintenance (Q6W) 療程。",
        "inclusion": ["pMMR 患者", "新診斷 Stage III/IV", "需中央實驗室確認"],
        "exclusion": ["先前用過 Pembro", "活動性自體免疫疾病"]
    },
    {
        "cancer": "Ovarian", "name": "DOVE (APGOT-OV07)", 
        "pos": "Recurrence", "drug": "Dostarlimab + Bevacizumab",
        "rationale": "針對 **透明細胞癌 (OCCC)**，結合免疫療法與抗血管生成藥物改善微環境。",
        "protocol": "Arm B: Dostarlimab + Beva (15mg/kg Q3W)。",
        "inclusion": ["OCCC 組織型態 > 50%", "Platinum-resistant (PD < 12m)"],
        "exclusion": ["先前用過 PD-1 抑制劑", "腸阻塞病史"]
    },
    {
        "cancer": "Ovarian", "name": "DS8201-772", 
        "pos": "Maintenance", "drug": "T-DXd (Enhertu)",
        "rationale": "標靶 **HER2** 之 ADC。對於 HER2 低表達 (1+/2+/3+) 均有臨床效益。",
        "protocol": "T-DXd 5.4mg/kg Q3W 搭配或不搭配 Bevacizumab。",
        "inclusion": ["HER2 表現 (IHC 1+/2+/3+)", "BRCA WT / HRD", "一線穩定後轉入"],
        "exclusion": ["間質性肺病 (ILD) 史", "LVEF < 50%"]
    }
]

# 初始化 Session State
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = TRIALS_DB[0]['name'] # 預設顯示第一個

# --- 2. 側邊欄 ---
with st.sidebar:
    st.header("🤖 AI 臨床媒合")
    api_key = st.text_input("Gemini API Key", type="password")
    patient_info = st.text_area("患者背景描述", height=250)
    if st.button("🚀 進行分析"):
        if api_key and patient_info:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-pro')
                prompt = f"你是一位台灣婦癌專家。現有試驗：{TRIALS_DB}。分析患者：{patient_info}。請建議適合試驗與理由。"
                response = model.generate_content(prompt)
                st.info(response.text)
            except Exception as e: st.error(f"AI 連線失敗: {e}")

# --- 3. 主頁面：河流圖與連動邏輯 ---
st.markdown("<div class='main-title'>婦癌臨床試驗導航系統</div>", unsafe_allow_html=True)

# 選擇癌別
cancer_type = st.radio("第一步：選擇癌症類別", ["Endometrial", "Ovarian"], horizontal=True)

def render_interactive_river(cancer_type):
    base_labels = ["初診 (Dx)", "一線治療 (1L)", "維持期 (Maint.)", "復發期 (Recurr.)"]
    base_colors = ["#E0E0E0", "#BDBDBD", "#81C784", "#FF8A65"] # 莫蘭迪灰綠橘
    
    filtered = [t for t in TRIALS_DB if t["cancer"] == cancer_type]
    labels = base_labels.copy()
    colors = base_colors.copy()
    sources, targets, values = [], [], []

    for t in filtered:
        idx = len(labels)
        labels.append(t["name"])
        colors.append("#00796B") # 試驗節點深青色
        if t["pos"] == "Maintenance":
            sources.extend([1, 2]); targets.extend([2, idx]); values.extend([1, 1])
        elif t["pos"] == "Recurrence":
            sources.extend([0, 3]); targets.extend([3, idx]); values.extend([1, 1])

    fig = go.Figure(data=[go.Sankey(
        node = dict(pad=50, thickness=35, label=labels, color=colors),
        link = dict(source=sources, target=targets, value=values, color="rgba(0, 121, 107, 0.1)")
    )])
    fig.update_layout(height=450, font=dict(size=18), margin=dict(l=15, r=15, t=10, b=10))
    
    # 捕捉點擊事件
    click_data = plotly_events(fig, click_event=True, key=f"sankey_{cancer_type}")
    return click_data, labels

# 渲染河流圖
st.subheader("第二步：點擊圖中「深青色」試驗方塊 或 從清單選擇")
col_chart, col_list = st.columns([3, 1])

with col_chart:
    selected_points, all_nodes = render_interactive_river(cancer_type)
    # 處理圖表點擊：當點擊發生時，更新 Session State
    if selected_points:
        clicked_idx = selected_points[0]['pointNumber']
        clicked_label = all_nodes[clicked_idx]
        # 只有點擊的是試驗名稱時才更新
        if clicked_label in [t["name"] for t in TRIALS_DB]:
            st.session_state.selected_trial = clicked_label

with col_list:
    st.write(" ") # 間距
    # 同步下拉清單
    available_options = [t["name"] for t in TRIALS_DB if t["cancer"] == cancer_type]
    
    # 計算下拉選單應該停留的位置
    try:
        default_index = available_options.index(st.session_state.selected_trial)
    except ValueError:
        default_index = 0
        st.session_state.selected_trial = available_options[0] # 若切換癌別則預設第一個

    selected_from_list = st.selectbox("🎯 試驗清單快速跳轉", available_options, index=default_index)
    # 如果使用者手動切換下拉選單，也更新 State
    if selected_from_list != st.session_state.selected_trial:
        st.session_state.selected_trial = selected_from_list

# --- 4. 詳情呈現區 (依據 Session State) ---
st.divider()

# 獲取當前選中的資料
current_data = next(it for it in TRIALS_DB if it["name"] == st.session_state.selected_trial)

st.markdown("<div class='detail-card'>", unsafe_allow_html=True)
st.markdown(f"<h2 style='color:#004D40; border-bottom: 2px solid #E0E0E0; padding-bottom:10px;'>📋 {current_data['name']} 詳情</h2>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown(f"### 🧪 藥物機轉：{current_data['drug']}")
    st.info(current_data['rationale'])
    
    
    
    st.markdown("### 💉 給藥 Protocol")
    st.success(current_data['protocol'])
    st.write(f"**臨床階段:** {current_data['pos']}")

with col2:
    st.markdown("### ✅ 入案標準 (Inclusion)")
    for inc in current_data['inclusion']: st.markdown(f"- **{inc}**")
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### ❌ 排除標準 (Exclusion)")
    for exc in current_data['exclusion']: st.markdown(f"- {exc}")
st.markdown("</div>", unsafe_allow_html=True)

# 頁尾提示

st.caption("註：本系統僅供醫師內部參考，具體入案條件請依據各試驗最新版本 Protocol 為準。")
