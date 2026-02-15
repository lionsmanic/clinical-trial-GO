import streamlit as st
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events
import google.generativeai as genai
import urllib.parse

# --- 🏥 臨床決策與研究維護系統配置 ---
st.set_page_config(page_title="婦癌臨床試驗導航與 AI 決策系統", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', sans-serif;
        background-color: #F7F9F9;
        font-size: 19px !important;
    }
    .main-title {
        font-size: 46px !important; font-weight: 800; color: #004D40;
        text-align: center; padding: 25px; background: white;
        border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 20px;
    }
    .info-card {
        background: white; border-radius: 20px; padding: 35px;
        border: 1px solid #B2DFDB; box-shadow: 0 6px 18px rgba(0,0,0,0.06); margin-bottom: 25px;
    }
    .ai-box {
        background: #E0F2F1; border: 2px solid #00897B; border-radius: 20px; padding: 30px;
    }
    .section-label { font-size: 26px; font-weight: 700; color: #00695C; border-left: 10px solid #00695C; padding-left: 15px; margin-bottom: 20px; }
    .hr-box { background: #F0F4F8; border-radius: 12px; padding: 15px; text-align: center; border: 1px solid #D1D9E0; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 深度臨床資料庫 ---
if 'trials_db' not in st.session_state:
    st.session_state.trials_db = [
        {
            "cancer": "Endometrial", "name": "GU-US-682-6769 (TROPiCS-03)", "pharma": "Gilead Sciences",
            "drug": "Sacituzumab Govitecan (Trodelvy)", "pos": "Recurrence",
            "summary": "針對 Trop-2 ADC，適用於含鉑與免疫治療後進展之患者。",
            "rationale": "標靶 Trop-2 ADC。利用抗體精準導向釋放 SN-38 載荷，引發強大 Bystander Effect。",
            "dosing": {
                "Experimental (Arm A)": "SG 10 mg/kg IV on Days 1 and 8 (Q21D).",
                "Control (Arm B)": "TPC (Doxo 60 mg/m² or Paclitaxel 80 mg/m²)."
            },
            "outcomes": {"ORR": "28.5%", "mPFS": "5.6m", "mOS": "12.8m", "HR": "0.64 (95% CI: 0.48-0.84)", "AE": "Neutropenia (15%)"},
            "inclusion": ["進展性/復發性 EC", "曾接受過 Platinum 化療", "曾接受過 Anti-PD-1/L1", "ECOG 0-1"],
            "exclusion": ["先前用過 Trop-2 ADC", "子宮肉瘤 (Uterine Sarcoma)", "活動性 CNS 轉移"],
            "ref": "JCO 2024; TROPiCS-03 Study"
        },
        {
            "cancer": "Ovarian", "name": "DS8201-772 (DESTINY-PanTumor)", "pharma": "AstraZeneca / Daiichi Sankyo",
            "drug": "Enhertu (T-DXd)", "pos": "Maintenance",
            "summary": "HER2 表現之維持治療，旨在替代或補充 PARPi。",
            "rationale": "標靶 HER2 之 ADC。搭載強效 Topoisomerase I 抑制劑，具備極高藥物抗體比 (DAR)。",
            "dosing": {
                "Experimental": "T-DXd 5.4 mg/kg IV Q3W 直到 PD。",
                "Beva Combo": "T-DXd 5.4 mg/kg + Bevacizumab 15 mg/kg Q3W."
            },
            "outcomes": {"ORR": "46.3% (IHC 3+)", "mPFS": "10.4m", "mOS": "N/A", "HR": "0.42 (95% CI: 0.30-0.58)", "AE": "ILD (6%)"},
            "inclusion": ["HER2 IHC 1+/2+/3+", "BRCA WT / HRD 不適合 PARPi", "一線化療後穩定"],
            "exclusion": ["ILD 肺纖維化病史", "LVEF < 50%", "先前接受過 HER2 標靶藥物"],
            "ref": "JCO 2024; DESTINY-PanTumor 02"
        }
    ]

# --- 2. 狀態同步 ---
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = st.session_state.trials_db[0]['name']

# --- 3. 主頁面：河流圖導航 ---
st.markdown("<div class='main-title'>婦癌臨床試驗導航與 AI 決策輔助系統</div>", unsafe_allow_html=True)

cancer_type = st.radio("第一步：選擇癌症類型", ["Endometrial", "Ovarian"], horizontal=True)

def draw_locked_river(cancer_type):
    base_labels = ["初診 (Dx)", "一線治療 (1L)", "維持期 (Maint.)", "復發期 (Recurr.)"]
    base_colors = ["#CFD8DC", "#90A4AE", "#80CBC4", "#EF9A9A"]
    filtered = [t for t in st.session_state.trials_db if t["cancer"] == cancer_type]
    labels = base_labels.copy()
    node_colors = base_colors.copy()
    sources, targets, values = [], [], []

    for t in filtered:
        idx = len(labels)
        labels.append(f"{t['name']}\n({t['drug']})")
        node_colors.append("#00796B")
        if t["pos"] == "Maintenance":
            sources.extend([1, 2]); targets.extend([2, idx]); values.extend([1, 1])
        elif t["pos"] == "Recurrence":
            sources.extend([0, 3]); targets.extend([3, idx]); values.extend([1, 1])

    fig = go.Figure(data=[go.Sankey(
        node = dict(pad=50, thickness=35, label=labels, color=node_colors),
        link = dict(source=sources, target=targets, value=values, color="rgba(0, 121, 107, 0.1)")
    )])
    fig.update_layout(height=420, font=dict(size=18), margin=dict(l=15, r=15, t=10, b=10))
    return fig, labels

st.subheader("第二步：點選河流圖方塊查看快看摘要")
col_chart, col_quick = st.columns([2.5, 1])

with col_chart:
    fig, current_labels = draw_locked_river(cancer_type)
    clicked_data = plotly_events(fig, click_event=True, key=f"sankey_{cancer_type}")
    if clicked_data:
        clicked_idx = clicked_data[0]['pointNumber']
        label_text = current_labels[clicked_idx].split("\n")[0]
        if label_text in [t["name"] for t in st.session_state.trials_db]:
            st.session_state.selected_trial = label_text

with col_quick:
    t_q = next(it for it in st.session_state.trials_db if it["name"] == st.session_state.selected_trial)
    st.markdown(f"""
        <div style='background: #E0F2F1; border-left: 8px solid #00897B; padding: 20px; border-radius: 10px;'>
            <h4 style='margin:0; color:#004D40;'>📍 快速導航亮點</h4>
            <p style='font-weight:700; margin-top:10px; font-size:20px;'>{t_q['name']}</p>
            <p style='font-size:16px;'>{t_q['summary']}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # --- 1. PubMed 自動搜索按鍵 ---
    search_query = f"{t_q['name']} {t_q['drug']} gynecologic cancer clinical trial"
    pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/?term={urllib.parse.quote(search_query)}&sort=pubdate"
    st.link_button("🔍 搜尋 PubMed 最新文獻", pubmed_url)

# --- 4. 深度數據全覽看板 ---
st.divider()
st.subheader("🔍 第三步：深度數據、Protocol 與收案標準全覽")

trial_options = [t["name"] for t in st.session_state.trials_db if t["cancer"] == cancer_type]
try: current_idx = trial_options.index(st.session_state.selected_trial)
except ValueError: current_idx = 0

selected_name = st.selectbox("🎯 搜尋試驗名稱：", trial_options, index=current_idx)
t = next(it for it in st.session_state.trials_db if it["name"] == selected_name)

st.markdown(f"<div class='info-card'>", unsafe_allow_html=True)
st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #00897B; padding-bottom:10px;'>📋 {t['name']} 完整分析報告</h2>", unsafe_allow_html=True)

c1, c2 = st.columns([1.2, 1])
with c1:
    st.markdown("<div class='section-label'>💉 Dosing Protocol & Mechanism</div>", unsafe_allow_html=True)
    for arm, details in t['dosing'].items(): st.write(f"🔹 **{arm}**: {details}")
    st.success(f"**機轉說明:** {t['rationale']}")

with c2:
    st.markdown("<div class='section-label'>📈 Efficacy & Hazard Ratio</div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class='hr-box'>
            <div style='font-size: 14px; color: #5D6D7E;'>Hazard Ratio (HR)</div>
            <div style='font-size: 28px; font-weight: 700;'>{t['outcomes']['HR']}</div>
        </div>
    """, unsafe_allow_html=True)
    st.write(f"**mPFS:** {t['outcomes']['mPFS']} | **mOS:** {t['outcomes']['mOS']}")
    st.error(f"**Safety/AEs:** {t['outcomes']['AE']}")
    st.caption(f"Ref: {t['ref']}")

st.divider()
c3, c4 = st.columns(2)
with c3:
    st.markdown("<div class='section-label'>✅ Inclusion Criteria</div>", unsafe_allow_html=True)
    for inc in t['inclusion']: st.write(f"🟢 {inc}")
with c4:
    st.markdown("<div class='section-label'>❌ Exclusion Criteria</div>", unsafe_allow_html=True)
    for exc in t['exclusion']: st.write(f"🔴 {exc}")
st.markdown("</div>", unsafe_allow_html=True)

# --- 5. AI 患者媒合診斷區 ---
st.divider()
st.markdown("<div class='ai-box'>", unsafe_allow_html=True)
st.markdown("<div class='section-label'>🤖 Gemini AI 患者試驗媒合判定</div>", unsafe_allow_html=True)

col_ai_1, col_ai_2 = st.columns([1, 1])
with col_ai_1:
    api_key = st.text_input("輸入 Gemini API Key", type="password")
    patient_notes = st.text_area("請輸入醫師臨床觀察 / 患者病歷摘要", height=300, 
                                 placeholder="例：62y/o female, pMMR Endometrial Cancer, FIGO Stage IIIC, received Carbo/Taxel/Pembro, now suspected PD...")
    match_btn = st.button("🚀 開始 AI 媒合判定")

with col_ai_2:
    if match_btn:
        if api_key and patient_notes:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-pro')
                prompt = f"""你是一位婦產科腫瘤權威。請根據以下患者病歷：'{patient_notes}'，
                比對我們現有的試驗資料庫：{st.session_state.trials_db}。
                請判定：
                1. 該患者符合哪一個試驗的入案條件(Inclusion)且不具備排除條件(Exclusion)？
                2. 推薦優先順序為何？
                3. 請針對該試驗的 Hazard Ratio (HR) 解釋為什麼適合這位患者。
                4. 如果都不符合，請建議下一步檢測或治療。
                請用繁體中文回答，語氣專業嚴謹。"""
                
                with st.spinner('AI 正在分析病歷與試驗數據...'):
                    response = model.generate_content(prompt)
                    st.markdown("### 🧬 AI 媒合建議報告")
                    st.write(response.text)
            except Exception as e: st.error(f"AI 服務異常: {e}")
        else: st.warning("請確保已輸入 API Key 與患者病歷。")
    else:
        st.info("請在左側輸入患者資訊，AI 將根據目前的資料庫進行深度媒合分析。")
st.markdown("</div>", unsafe_allow_html=True)
