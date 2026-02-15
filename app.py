import streamlit as st
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events
import google.generativeai as genai

# --- 🏥 專業醫療視覺風格配置 ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&family=Roboto:wght@400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', 'Roboto', sans-serif;
        background-color: #F9FBFB; /* 護眼淺青灰 */
        color: #1A3030;
        font-size: 21px !important;
    }

    .main-title {
        font-size: 50px !important;
        font-weight: 800;
        color: #004D40;
        text-align: center;
        padding: 35px 0;
        background: linear-gradient(135deg, #E0F2F1 0%, #F9FBFB 100%);
        border-radius: 20px;
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(0,77,64,0.05);
    }

    .info-card {
        background: white;
        border-radius: 24px;
        padding: 40px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.03);
        border: 1px solid #B2DFDB;
        margin-top: 25px;
    }

    .section-header {
        font-size: 32px;
        font-weight: 700;
        color: #00695C;
        border-left: 12px solid #00695C;
        padding-left: 18px;
        margin-bottom: 25px;
    }

    /* Tab 字體優化 */
    .stTabs [data-baseweb="tab"] {
        font-size: 24px !important;
        font-weight: 700;
        padding: 10px 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 臨床試驗資料庫 ---
if 'trials_db' not in st.session_state:
    st.session_state.trials_db = [
        {
            "cancer": "Endometrial", "name": "GU-US-682-6769", 
            "pos": "Recurrence", "drug": "Sacituzumab Govitecan (SG)",
            "rationale": "標靶 **Trop-2** 的抗體藥物複合體 (ADC)。其核心機轉係利用 Anti-Trop-2 Antibody 將強效的 Topoisomerase I Inhibitor 直接送入腫瘤細胞，並透過 **Bystander Effect (旁觀者效應)** 殺傷鄰近癌細胞。",
            "protocol": "SG 10mg/kg 靜脈注射 (D1, D8 Q21D) 直到疾病進展 (PD)。",
            "inclusion": ["進展性/復發性 EC", "先前接受過 Platinum 化療", "先前接受過 Anti-PD-1/L1", "ECOG PS 0-1"],
            "exclusion": ["子宮肉瘤 (Uterine Sarcoma)", "先前用過 Trop-2 ADC", "活動性 CNS 轉移"]
        },
        {
            "cancer": "Endometrial", "name": "MK2870-033", 
            "pos": "Maintenance", "drug": "Sac-TMT + Pembro",
            "rationale": "結合新型 Trop-2 ADC 與 PD-1 抑制劑。ADC 誘導細胞死亡釋放抗原，協同提升 **Pembrolizumab** 之免疫活化效果。",
            "protocol": "引導期: Carbo+Taxel+Pembro (Q3W x6) -> 維持期: Pembro 400mg Q6W +/- Sac-TMT。",
            "inclusion": ["pMMR 患者", "新診斷 Stage III/IV", "需提供檢體至中央實驗室檢測"],
            "exclusion": ["Sarcoma", "先前用過 Pembro", "活動性自體免疫疾病"]
        },
        {
            "cancer": "Ovarian", "name": "DOVE (APGOT-OV07)", 
            "pos": "Recurrence", "drug": "Dostarlimab + Bevacizumab",
            "rationale": "針對 **透明細胞癌 (OCCC)**。Dostarlimab 阻斷 PD-1 路徑，結合 Bevacizumab 抑制血管增生，共同改善腫瘤微環境。",
            "protocol": "Arm A: Dostarlimab 單用; Arm B: Dostarlimab + Beva (15mg/kg Q3W)。",
            "inclusion": ["OCCC 組織型態 > 50%", "Platinum-resistant (PD < 12m)", "治療線數不超過 5 線"],
            "exclusion": ["先前用過免疫檢查點抑制劑", "臨床顯著腸阻塞"]
        },
        {
            "cancer": "Ovarian", "name": "DS8201-772 (T-DXd)", 
            "pos": "Maintenance", "drug": "Trastuzumab Deruxtecan (Enhertu)",
            "rationale": "標靶 **HER2** 之 ADC。搭載強效載荷，對 **HER2 Low (1+/2+/3+)** 患者均展現強大臨床效益，探討作為一線維持治療的潛力。",
            "protocol": "T-DXd 5.4mg/kg Q3W 搭配或不搭配 Bevacizumab 15mg/kg。",
            "inclusion": ["HER2 表現 (IHC 3+/2+/1+)", "BRCA WT 或 HRD 不適合 PARPi", "一線化療後穩定"],
            "exclusion": ["ILD 肺纖維化病史", "先前接受過 HER2 標靶治療", "LVEF < 50%"]
        }
    ]

# --- 2. 側邊欄 AI ---
with st.sidebar:
    st.markdown("### 🤖 專家 AI 決策輔助")
    api_key = st.text_input("Gemini API Key", type="password")
    patient_notes = st.text_area("請輸入患者臨床資訊", height=300, placeholder="例：65y/o female, EC stage IV, pMMR, now PD...")
    if st.button("🚀 開始分析"):
        if api_key and patient_notes:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-pro')
                prompt = f"你是一位台灣婦癌專家。現有試驗：{st.session_state.trials_db}。分析患者：{patient_notes}。請建議適合試驗與理由，使用繁體中文。"
                response = model.generate_content(prompt)
                st.info(response.text)
            except Exception as e: st.error(f"AI 連線失敗: {e}")

# --- 3. 主頁面河流圖 (核心修正) ---
st.markdown("<div class='main-title'>婦癌臨床試驗導航地圖</div>", unsafe_allow_html=True)

tab_ec, tab_oc = st.tabs(["子宮內膜癌 (EC)", "卵巢癌 (OC)"])

def draw_robust_sankey(cancer_type):
    labels = ["初診 (Dx)", "一線治療 (1L)", "維持期 (Maint.)", "復發期 (Recurr.)"]
    # 護眼莫蘭迪色系
    colors = ["#D4E157", "#9CCC65", "#4DB6AC", "#FF8A65"]
    
    filtered = [t for t in st.session_state.trials_db if t["cancer"] == cancer_type]
    sources, targets, values = [], [], []

    for t in filtered:
        trial_idx = len(labels)
        labels.append(t["name"])
        colors.append("#26A69A") # 試驗節點深青色
        
        if t["pos"] == "Maintenance":
            sources.extend([1, 2]); targets.extend([2, trial_idx]); values.extend([1, 1])
        elif t["pos"] == "Recurrence":
            sources.extend([0, 3]); targets.extend([3, trial_idx]); values.extend([1, 1])

    if not sources:
        st.warning(f"目前 {cancer_type} 分類下尚無試驗路徑資料。")
        return None, labels

    try:
        # 修正：移除 node 中的 font，改在 update_layout 設定
        fig = go.Figure(data=[go.Sankey(
            node = dict(pad=50, thickness=30, label=labels, color=colors),
            link = dict(source=sources, target=targets, value=values, color="rgba(38, 166, 154, 0.15)")
        )])
        
        # 在這裡統一設定字體大小
        fig.update_layout(
            font=dict(size=20, color="#234E52"),
            height=480, 
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor="rgba(0,0,0,0)"
        )
        
        return plotly_events(fig, click_event=True, key=f"s_k_{cancer_type}"), labels
    except Exception as e:
        st.error(f"繪圖引擎發生錯誤: {e}")
        return None, labels

# 處理選擇狀態
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

# --- 4. 詳情呈現區 ---
st.divider()

if selected_name:
    t = next(it for it in st.session_state.trials_db if it["name"] == selected_name)
    st.markdown("<div class='info-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='section-header'>📋 臨床試驗詳情：{t['name']}</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"### 🧪 藥物機轉：{t['drug']}")
        st.info(t['rationale'])
        
        st.markdown("### 💉 給藥 Protocol")
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
        <div style='text-align: center; padding: 100px; color: #78909C; border: 3px dashed #B2DFDB; border-radius: 30px; background: #F0F4F4;'>
            <h2 style='font-size: 36px;'>👋 請點擊河流圖右方的「試驗方塊」</h2>
            <p style='font-size: 22px;'>系統將為您呈現詳細的藥物機轉、給藥方式與收案條件。</p>
        </div>
    """, unsafe_allow_html=True)

# 病程河流圖參考
