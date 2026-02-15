import streamlit as st
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events
import google.generativeai as genai

# --- 🏥 醫學儀表板視覺配置 ---
st.set_page_config(page_title="婦癌臨床試驗導航", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', sans-serif;
        background-color: #F4F7F6;
        color: #1F2937;
        font-size: 19px !important;
    }
    .main-title {
        font-size: 44px !important;
        font-weight: 800;
        color: #065F46;
        text-align: center;
        padding: 25px;
        background: white;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .summary-box {
        background: #ECFDF5;
        border-left: 10px solid #10B981;
        padding: 20px;
        border-radius: 10px;
        margin-top: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .result-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 15px;
        padding: 25px;
        margin-top: 15px;
    }
    .metric-text { font-size: 24px; font-weight: 700; color: #059669; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 擴充資料庫 (含已發表結果) ---
TRIALS_DB = [
    {
        "cancer": "Endometrial", "name": "GU-US-682-6769", "drug": "Sacituzumab Govitecan (SG)",
        "pos": "Recurrence", "summary": "針對 Trop-2 標靶 ADC，適用於含鉑與免疫治療後進展之患者。",
        "rationale": "標靶 Trop-2 ADC，透過 Topoisomerase I 抑制劑直接殺傷並具備 Bystander Effect。",
        "protocol": "SG 10mg/kg IV (D1, D8 Q21D) 直到 PD。",
        "inclusion": ["進展性/復發性 EC", "曾用過 Platinum & Anti-PD-1"],
        "exclusion": ["先前用過 Trop-2 ADC"],
        "results": {"status": "Published", "ORR": "28%", "PFS": "5.6m", "OS": "12.8m", "AE": "Neutropenia (15%), Diarrhea (10%)"},
        "ref": "JCO 2024; Phase 2 TROPiCS-03"
    },
    {
        "cancer": "Ovarian", "name": "DOVE (APGOT-OV07)", "drug": "Dostarlimab + Beva",
        "pos": "Recurrence", "summary": "針對透明細胞癌 (OCCC)，抗血管生成搭配 PD-1 抑制劑。",
        "rationale": "針對 OCCC 透明細胞癌之特殊免疫微環境進行雙重阻斷。",
        "protocol": "Dostarlimab + Bevacizumab (15mg/kg Q3W)。",
        "inclusion": ["OCCC > 50%", "Platinum-resistant"],
        "exclusion": ["先前用過 PD-1/L1"],
        "results": {"status": "Early Data", "ORR": "40%", "PFS": "8.2m", "OS": "N/A", "AE": "Hypertension (12%), Fatigue"},
        "ref": "ESMO 2025 Abstract"
    },
    {
        "cancer": "Ovarian", "name": "DS8201-772", "drug": "T-DXd (Enhertu)",
        "pos": "Maintenance", "summary": "HER2 低表達之維持治療，替代或補充 PARPi。",
        "rationale": "HER2 標靶 ADC 透過強效 Topo-I 抑制劑載荷精準殺傷。",
        "protocol": "T-DXd 5.4mg/kg Q3W +/- Beva。",
        "inclusion": ["HER2 IHC 1+/2+/3+", "BRCA WT / HRD"],
        "exclusion": ["ILD 肺纖維化病史"],
        "results": {"status": "Ongoing", "ORR": "N/A", "PFS": "Expect > 10m", "OS": "N/A", "AE": "Nausea, Risk of ILD"},
        "ref": "Phase 3 DESTINY-PanTumor"
    }
]

# --- 2. 狀態同步 ---
if 'active_trial' not in st.session_state:
    st.session_state.active_trial = None

# --- 3. 主頁面：河流圖導航 ---
st.markdown("<div class='main-title'>婦癌臨床試驗導航儀表板</div>", unsafe_allow_html=True)

cancer_type = st.radio("第一步：選擇癌症類型", ["Endometrial", "Ovarian"], horizontal=True)

# 繪製河流圖 (標籤含藥物)
def draw_detailed_river(cancer_type):
    nodes = ["初診 (Dx)", "一線 (1L)", "維持 (Maint.)", "復發 (Recurr.)"]
    colors = ["#D1D5DB", "#9CA3AF", "#6EE7B7", "#FCA5A1"]
    
    filtered = [t for t in TRIALS_DB if t["cancer"] == cancer_type]
    labels = nodes.copy()
    node_colors = colors.copy()
    sources, targets, values = [], [], []

    for t in filtered:
        idx = len(labels)
        labels.append(f"{t['name']}\n({t['drug']})") # 呈現試驗名稱 + 藥物
        node_colors.append("#059669")
        if t["pos"] == "Maintenance":
            sources.extend([1, 2]); targets.extend([2, idx]); values.extend([1, 1])
        elif t["pos"] == "Recurrence":
            sources.extend([0, 3]); targets.extend([3, idx]); values.extend([1, 1])

    fig = go.Figure(data=[go.Sankey(
        node = dict(pad=40, thickness=35, label=labels, color=node_colors),
        link = dict(source=sources, target=targets, value=values, color="rgba(16, 185, 129, 0.1)")
    )])
    fig.update_layout(height=400, font=dict(size=16), margin=dict(l=10, r=10, t=10, b=10))
    return fig, labels

# 河流圖點選區
st.subheader("第二步：點擊圖中「綠色方塊」查看快速摘要")
col_chart, col_quick = st.columns([2, 1])

with col_chart:
    fig, current_labels = draw_detailed_river(cancer_type)
    clicked = plotly_events(fig, click_event=True, key=f"sk_{cancer_type}")
    if clicked:
        idx = clicked[0]['pointNumber']
        label_text = current_labels[idx].split("\n")[0] # 還原成 Trial Name
        if label_text in [t["name"] for t in TRIALS_DB]:
            st.session_state.active_trial = label_text

with col_quick:
    if st.session_state.active_trial:
        t_summary = next(it for it in TRIALS_DB if it["name"] == st.session_state.active_trial)
        st.markdown(f"""
            <div class='summary-box'>
                <h4 style='color:#065F46; margin:0;'>✨ 試驗快速重點</h4>
                <p style='font-size:18px; margin-top:10px;'><b>{t_summary['name']}</b></p>
                <p style='font-size:17px;'>{t_summary['summary']}</p>
                <hr>
                <p style='font-size:16px; color:#065F46;'>欲看完整數據與 Protocol 請由下方選單拉取</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.info("👆 請點擊河流圖右側試驗方塊以顯示快速重點。")

# --- 4. 深度細節區 (選單驅動) ---
st.divider()
st.subheader("🔍 深度臨床數據與 Protocol 查閱")

# 下拉選單獨立控制深度查閱
all_trial_names = [t["name"] for t in TRIALS_DB if t["cancer"] == cancer_type]
selected_detail_name = st.selectbox("請選擇想要深入查閱的試驗：", all_trial_names)

if selected_detail_name:
    t = next(it for it in TRIALS_DB if it["name"] == selected_detail_name)
    
    tab1, tab2, tab3 = st.tabs(["💊 治療細節 & 機轉", "📊 已發表文獻數據", "✅ 收案標準"])
    
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"#### 藥物機轉：{t['drug']}")
            st.info(t['rationale'])
            
        with c2:
            st.markdown("#### 給藥 Protocol")
            st.success(t['protocol'])

    with tab2:
        res = t['results']
        st.markdown(f"#### 📈 臨床療效數據 ({res['status']})")
        m1, m2, m3 = st.columns(3)
        m1.metric("ORR (Response Rate)", res['ORR'])
        m2.metric("Median PFS", res['PFS'])
        m3.metric("Median OS", res['OS'])
        
        st.markdown(f"**常見副作用 (AE):** {res['AE']}")
        st.caption(f"數據來源：{t['ref']}")
        

    with tab3:
        cc1, cc2 = st.columns(2)
        with cc1:
            st.write("**✅ 入案標準 (Inclusion)**")
            for inc in t['inclusion']: st.write(f"- {inc}")
        with cc2:
            st.write("**❌ 排除標準 (Exclusion)**")
            for exc in t['exclusion']: st.write(f"- {exc}")

# --- 5. 底部：河流圖參考圖示 ---
