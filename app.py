import streamlit as st
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events
import google.generativeai as genai

# --- 🏥 晨曦醫療護眼風格配置 ---
st.set_page_config(page_title="婦癌臨床試驗導航", layout="wide")

st.markdown("""
    <style>
    /* 載入字體與設定暖色調背景 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', sans-serif;
        background-color: #FDFDFB; /* 暖白護眼底色 */
        color: #2F3640;
        font-size: 20px !important;
    }

    /* 頂部大標題 */
    .main-title {
        font-size: 48px !important;
        font-weight: 800;
        color: #1B4F72;
        padding: 20px 0;
        text-align: center;
        letter-spacing: 2px;
    }

    /* 專業資訊卡片 */
    .info-card {
        background: #FFFFFF;
        border-radius: 24px;
        padding: 40px;
        box-shadow: 0 12px 40px rgba(0,0,0,0.03);
        border: 1px solid #EAECEE;
        margin: 20px 0;
    }

    /* 強調標籤 */
    .section-header {
        font-size: 28px;
        font-weight: 700;
        color: #2874A6;
        border-bottom: 3px solid #AED6F1;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }

    /* 自定義按鈕 */
    .stButton>button {
        background-color: #2874A6;
        color: white;
        border-radius: 12px;
        font-size: 20px;
        padding: 10px 24px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 臨床試驗資料庫 (確保關鍵字對齊) ---
if 'trials_db' not in st.session_state:
    st.session_state.trials_db = [
        {
            "cancer": "Endometrial", "name": "GU-US-682-6769", 
            "pos": "Recurrence", "drug": "Sacituzumab Govitecan (SG)",
            "rationale": "標靶 **Trop-2** 的抗體藥物複合體 (ADC)。結合抗體的高選擇性與 Topoisomerase I 抑制劑的強大殺傷力，具備 **Bystander Effect**。",
            "protocol": "SG 10mg/kg IV (D1, D8 Q21D)。",
            "inclusion": ["進展性/復發性 EC", "曾接受 Platinum & Anti-PD-1", "ECOG 0-1"],
            "exclusion": ["子宮肉瘤", "曾用過 Trop-2 ADC"]
        },
        {
            "cancer": "Endometrial", "name": "MK2870-033", 
            "pos": "Maintenance", "drug": "Sac-TMT + Pembro",
            "rationale": "新型 ADC 與免疫檢查點抑制劑聯手，旨在提升一線化療後的長期緩解率。",
            "protocol": "Induction: 6 cycles -> Maint: Q6W 療程。",
            "inclusion": ["pMMR 患者", "新診斷 Stage III/IV", "需中央檢測"],
            "exclusion": ["先前用過 Pembro"]
        },
        {
            "cancer": "Ovarian", "name": "DOVE (APGOT-OV07)", 
            "pos": "Recurrence", "drug": "Dostarlimab + Bevacizumab",
            "rationale": "針對 **透明細胞癌 (OCCC)**，結合免疫療法與抗血管生成藥物。",
            "protocol": "Arm B: Dostarlimab + Beva (15mg/kg Q3W)。",
            "inclusion": ["OCCC > 50%", "Platinum-resistant"],
            "exclusion": ["先前用過 PD-1 抑制劑"]
        },
        {
            "cancer": "Ovarian", "name": "DS8201-772 (T-DXd)", 
            "pos": "Maintenance", "drug": "Enhertu",
            "rationale": "HER2 標靶 ADC，利用強效載荷對 HER2 低表達腫瘤進行精準打擊。",
            "protocol": "T-DXd 5.4mg/kg Q3W。",
            "inclusion": ["HER2 IHC 1+/2+/3+", "BRCA WT / HRD"],
            "exclusion": ["肺纖維化病史 (ILD)"]
        }
    ]

# --- 2. 側邊欄：AI 診斷區 ---
with st.sidebar:
    st.markdown("### 🤖 專家 AI 決策輔助")
    api_key = st.text_input("Gemini API Key", type="password")
    patient_notes = st.text_area("患者臨床描述", height=300, placeholder="例：62y/o pMMR EC, s/p Platinum, now PD...")
    if st.button("🚀 分析合適試驗"):
        if api_key and patient_notes:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-pro')
                prompt = f"你是一位台灣婦癌專家。現有試驗：{st.session_state.trials_db}。分析患者：{patient_notes}。建議適合試驗與藥物機轉理由。"
                response = model.generate_content(prompt)
                st.info(response.text)
            except Exception as e: st.error(f"AI 服務暫時無法連線: {e}")

# --- 3. 主頁面：河流圖呈現 ---
st.markdown("<div class='main-title'>婦癌臨床試驗路徑導航地圖</div>", unsafe_allow_html=True)

tab_ec, tab_oc = st.tabs(["子宮內膜癌 (EC)", "卵巢癌 (OC)"])

def draw_safe_sankey(cancer_type):
    # 基礎節點與配色
    base_labels = ["初診 (Dx)", "一線化療 (1L)", "維持期 (Maint.)", "復發期 (Recurr.)"]
    base_colors = ["#FAD7A0", "#F8C471", "#ABEBC6", "#F1948A"]
    
    filtered = [t for t in st.session_state.trials_db if t["cancer"] == cancer_type]
    
    labels = base_labels.copy()
    colors = base_colors.copy()
    sources, targets, values = [], [], []

    for t in filtered:
        trial_idx = len(labels)
        labels.append(t["name"])
        colors.append("#5DADE2") # 試驗節點藍色
        
        # 建立連線邏輯
        if t["pos"] == "Maintenance":
            sources.extend([1, 2]); targets.extend([2, trial_idx]); values.extend([1, 1])
        elif t["pos"] == "Recurrence":
            sources.extend([0, 3]); targets.extend([3, trial_idx]); values.extend([1, 1])

    # 🔥 重要修正：若無連線數據，不要調用 go.Sankey 否則會拋出 ValueError
    if not sources:
        st.warning(f"目前 {cancer_type} 分類下尚無臨床試驗連線數據。")
        return None, labels

    fig = go.Figure(data=[go.Sankey(
        node = dict(pad=50, thickness=30, label=labels, color=colors, font=dict(size=20, color="#212F3D")),
        link = dict(source=sources, target=targets, value=values, color="rgba(93, 173, 226, 0.2)")
    )])
    fig.update_layout(height=500, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor="rgba(0,0,0,0)")
    
    # 捕捉點擊事件
    click_data = plotly_events(fig, click_event=True, key=f"sankey_{cancer_type}")
    return click_data, labels

# 處理選擇狀態
selected_trial = None

with tab_ec:
    click_ec, nodes_ec = draw_safe_sankey("Endometrial")
    if click_ec:
        idx = click_ec[0]['pointNumber']
        if idx < len(nodes_ec) and nodes_ec[idx] in [t["name"] for t in st.session_state.trials_db]:
            selected_trial = nodes_ec[idx]

with tab_oc:
    click_oc, nodes_oc = draw_safe_sankey("Ovarian")
    if click_oc:
        idx = click_oc[0]['pointNumber']
        if idx < len(nodes_oc) and nodes_oc[idx] in [t["name"] for t in st.session_state.trials_db]:
            selected_trial = nodes_oc[idx]

# --- 4. 詳情呈現區 (卡片式 UI) ---
st.divider()

if selected_trial:
    t = next(it for it in st.session_state.trials_db if it["name"] == selected_trial)
    st.markdown("<div class='info-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='section-header'>📋 臨床試驗詳情：{t['name']}</div>", unsafe_allow_html=True)
    
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown(f"### 🧪 藥物機轉：{t['drug']}")
        st.info(t['rationale'])
        
        st.markdown("### 💉 給藥 Protocol")
        st.success(t['protocol'])
    
    with c2:
        st.markdown("### ✅ 入案標準 (Inclusion)")
        for inc in t['inclusion']: st.markdown(f"- **{inc}**")
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### ❌ 排除標準 (Exclusion)")
        for exc in t['exclusion']: st.markdown(f"- {exc}")
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown("""
        <div style='text-align: center; padding: 80px; color: #ABB2B9; border: 3px dashed #EBEDEF; border-radius: 30px; background: #FBFCFC;'>
            <h2 style='font-size: 32px;'>👋 請點擊圖表中右側的「試驗方塊」</h2>
            <p style='font-size: 20px;'>點擊後將為您呈現完整的 Protocol、藥物機轉與收案條件。</p>
        </div>
    """, unsafe_allow_html=True)

# 顯示病程河流參考圖
