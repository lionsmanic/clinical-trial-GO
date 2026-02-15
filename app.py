import streamlit as st
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events
import google.generativeai as genai
import sys

# --- 🏥 臨床護眼專業配色配置 ---
st.set_page_config(page_title="婦癌臨床試驗導航", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', sans-serif;
        background-color: #F7F9F9; /* 極淺灰色，減少反光 */
        color: #234E52;
        font-size: 21px !important;
    }

    .main-title {
        font-size: 50px !important;
        font-weight: 800;
        color: #004D40;
        text-align: center;
        padding: 30px 0;
        background: linear-gradient(to right, #E0F2F1, #F7F9F9);
        border-radius: 15px;
        margin-bottom: 25px;
    }

    .info-card {
        background: white;
        border-radius: 20px;
        padding: 40px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        border: 1px solid #B2DFDB;
        margin-top: 20px;
    }

    .section-header {
        font-size: 30px;
        font-weight: 700;
        color: #00796B;
        border-left: 10px solid #00796B;
        padding-left: 15px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 臨床試驗資料庫 (資料完整性檢查) ---
if 'trials_db' not in st.session_state:
    st.session_state.trials_db = [
        {
            "cancer": "Endometrial", "name": "GU-US-682-6769", 
            "pos": "Recurrence", "drug": "Sacituzumab Govitecan (SG)",
            "rationale": "標靶 **Trop-2** 的抗體藥物複合體 (ADC)。利用 SN-38 載荷殺傷腫瘤細胞，並具備 Bystander Effect。",
            "protocol": "SG 10mg/kg IV (D1, D8 Q21D)。",
            "inclusion": ["進展性/復發性 EC", "曾接受 Platinum & Anti-PD-1"],
            "exclusion": ["子宮肉瘤", "曾用過 Trop-2 ADC"]
        },
        {
            "cancer": "Endometrial", "name": "MK2870-033", 
            "pos": "Maintenance", "drug": "Sac-TMT + Pembro",
            "rationale": "新型 Trop-2 ADC 搭配免疫檢查點抑制劑，強化一線治療後的緩解維持。",
            "protocol": "Induction 6 cycles -> Maintenance Q6W。",
            "inclusion": ["pMMR 患者", "新診斷 Stage III/IV"],
            "exclusion": ["先前用過 Pembro"]
        },
        {
            "cancer": "Ovarian", "name": "DOVE (APGOT-OV07)", 
            "pos": "Recurrence", "drug": "Dostarlimab + Bevacizumab",
            "rationale": "針對 **透明細胞癌 (OCCC)**，結合免疫與抗血管生成機制。",
            "protocol": "Arm B: Dostarlimab + Beva (15mg/kg Q3W)。",
            "inclusion": ["OCCC > 50%", "Platinum-resistant"],
            "exclusion": ["先前用過免疫治療"]
        },
        {
            "cancer": "Ovarian", "name": "DS8201-772", 
            "pos": "Maintenance", "drug": "T-DXd (Enhertu)",
            "rationale": "HER2 標靶 ADC，對 HER2 Low 表現之腫瘤具備強大殺傷力。",
            "protocol": "T-DXd 5.4mg/kg Q3W。",
            "inclusion": ["HER2 IHC 1+/2+/3+", "BRCA WT / HRD"],
            "exclusion": ["間質性肺病 (ILD) 病史"]
        }
    ]

# --- 2. 側邊欄 AI ---
with st.sidebar:
    st.markdown("### 🤖 專家 AI 決策輔助")
    api_key = st.text_input("Gemini API Key", type="password")
    patient_notes = st.text_area("請輸入患者臨床資訊", height=250)
    if st.button("🚀 分析合適試驗"):
        if api_key and patient_notes:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-pro')
                prompt = f"你是一位台灣婦癌專家。現有試驗：{st.session_state.trials_db}。分析患者：{patient_notes}。請建議試驗並說明理由。"
                response = model.generate_content(prompt)
                st.info(response.text)
            except Exception as e: st.error(f"AI 出錯: {e}")

# --- 3. 主頁面河流圖 (核心修正) ---
st.markdown("<div class='main-title'>婦癌臨床試驗路徑導航地圖</div>", unsafe_allow_html=True)

tab_ec, tab_oc = st.tabs(["子宮內膜癌 (EC)", "卵巢癌 (OC)"])

def draw_robust_sankey(cancer_type):
    # 1. 預定義基礎節點
    labels = ["初診 (Dx)", "一線治療 (1L)", "維持期 (Maint.)", "復發期 (Recurr.)"]
    colors = ["#FFE082", "#FFB74D", "#81C784", "#E57373"]
    
    # 2. 過濾數據
    filtered = [t for t in st.session_state.trials_db if t["cancer"] == cancer_type]
    
    sources, targets, values = [], [], []

    # 3. 構建連線
    for t in filtered:
        trial_idx = len(labels)
        labels.append(t["name"])
        colors.append("#4DB6AC") # 試驗節點色
        
        if t["pos"] == "Maintenance":
            sources.extend([1, 2]); targets.extend([2, trial_idx]); values.extend([1, 1])
        elif t["pos"] == "Recurrence":
            sources.extend([0, 3]); targets.extend([3, trial_idx]); values.extend([1, 1])

    # 4. 防錯檢查：如果沒有連線數據，不要執行 Plotly
    if not sources:
        st.warning(f"目前 {cancer_type} 分類下尚無試驗路徑。")
        return None, labels

    try:
        fig = go.Figure(data=[go.Sankey(
            node = dict(pad=50, thickness=30, label=labels, color=colors, font=dict(size=20)),
            link = dict(source=sources, target=targets, value=values, color="rgba(77, 182, 172, 0.2)")
        )])
        fig.update_layout(height=450, margin=dict(l=20, r=20, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)")
        
        # 捕捉點擊事件
        return plotly_events(fig, click_event=True, key=f"s_k_{cancer_type}"), labels
    except Exception as e:
        st.error(f"繪圖引擎發生錯誤: {e}")
        return None, labels

# 處理選取邏輯
selected_name = None

with tab_ec:
    click_ec, nodes_ec = draw_robust_sankey("Endometrial")
    if click_ec:
        idx = click_ec[0]['pointNumber']
        if idx < len(nodes_ec) and nodes_ec[idx] in [t["name"] for t in st.session_state.trials_db]:
            selected_name = nodes_ec[idx]

with tab_oc:
    click_oc, nodes_oc = draw_robust_sankey("Ovarian")
    if click_oc:
        idx = click_oc[0]['pointNumber']
        if idx < len(nodes_oc) and nodes_oc[idx] in [t["name"] for t in st.session_state.trials_db]:
            selected_name = nodes_oc[idx]

# --- 4. 詳細資訊區 ---
st.divider()

if selected_name:
    t = next(it for it in st.session_state.trials_db if it["name"] == selected_name)
    st.markdown("<div class='info-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='section-header'>📋 臨床試驗詳情：{t['name']}</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"### 🧪 藥物機轉：{t['drug']}")
        st.info(t['rationale'])
        
        st.markdown("### 💉 給藥方式")
        st.success(t['protocol'])
    
    with col2:
        st.markdown("### ✅ 入案標準 (Inclusion)")
        for inc in t['inclusion']: st.markdown(f"- **{inc}**")
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### ❌ 排除標準 (Exclusion)")
        for exc in t['exclusion']: st.markdown(f"- {exc}")
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown("""
        <div style='text-align: center; padding: 80px; color: #78909C; border: 3px dashed #CFD8DC; border-radius: 30px;'>
            <h2 style='font-size: 32px;'>👋 請點擊圖表中右側的「試驗名稱」</h2>
            <p style='font-size: 20px;'>點擊方塊後將在此顯示該試驗的詳細 Protocol、機轉與收案標準。</p>
        </div>
    """, unsafe_allow_html=True)

# 顯示病程河流參考圖
