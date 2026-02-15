import streamlit as st
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events
import google.generativeai as genai

# --- 🏥 臨床決策導航與 AI 媒合系統 ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', sans-serif;
        background-color: #F8FAF9;
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
    /* 修正 HR 跑版與文字溢出 */
    .metric-container {
        background: #F0F4F8; border-radius: 12px; padding: 15px;
        text-align: center; border: 1px solid #D1D9E0;
    }
    .hr-value {
        font-size: 24px; font-weight: 700; color: #2C3E50;
        word-wrap: break-word; overflow-wrap: break-word;
    }
    .section-label { font-size: 26px; font-weight: 700; color: #00695C; border-left: 10px solid #00695C; padding-left: 15px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 深度臨床數據庫 ---
if 'trials_db' not in st.session_state:
    st.session_state.trials_db = [
        {
            "cancer": "Endometrial", "name": "GU-US-682-6769 (TROPiCS-03)", "pharma": "Gilead Sciences",
            "drug": "Sacituzumab Govitecan (SG)", "pos": "Recurrence",
            "summary": "針對 Trop-2 ADC，用於含鉑與免疫治療後進展之二/三線患者。",
            "rationale": "標靶 Trop-2 ADC。利用抗體引導 SN-38 載荷引發 DNA 損傷，並具備強大 Bystander Effect。",
            "dosing": {
                "Experimental (Arm A)": "SG 10 mg/kg IV on Days 1 and 8 (Q21D).",
                "Control (Arm B)": "TPC (Doxorubicin 60 mg/m² or Paclitaxel 80 mg/m²)."
            },
            "outcomes": {"ORR": "28.5%", "mPFS": "5.6m", "mOS": "12.8m", "HR": "0.64 (95% CI: 0.48-0.84)", "AE": "Neutropenia (15%)"},
            "inclusion": ["Recurrent EC (excluding Sarcoma)", "Prior Platinum chemo line", "Prior Anti-PD-1/L1 required", "ECOG 0-1"],
            "exclusion": ["Prior Trop-2 directed ADC", "Uterine Sarcoma", "Active CNS metastasis"],
            "ref": "JCO 2024; TROPiCS-03 Study"
        },
        {
            "cancer": "Ovarian", "name": "DS8201-772 (T-DXd)", "pharma": "AstraZeneca / Daiichi Sankyo",
            "drug": "Enhertu (T-DXd)", "pos": "Post-Recurr Maint",
            "summary": "復發後救援化療達穩定後之維持治療，針對 HER2 表現者。",
            "rationale": "標靶 HER2 之 ADC。搭載強效 Topoisomerase I 抑制劑，具備極高 DAR 對低表達者亦有效。",
            "dosing": {
                "Experimental Arm": "T-DXd 5.4 mg/kg IV Q3W.",
                "Combination Arm": "T-DXd + Bevacizumab 15 mg/kg Q3W."
            },
            "outcomes": {"ORR": "46.3% (IHC 3+)", "mPFS": "10.4m", "mOS": "N/A", "HR": "0.42 (95% CI: 0.30-0.58)", "AE": "ILD Risk (6%)"},
            "inclusion": ["HER2 IHC 1+/2+/3+", "Recurrent disease s/p rescue chemo", "Non-PD after 6 cycles"],
            "exclusion": ["History of ILD", "LVEF < 50%", "Prior HER2 ADC"],
            "ref": "JCO 2024; DESTINY-PanTumor 02"
        },
        {
            "cancer": "Endometrial", "name": "MK2870-033", "pharma": "MSD",
            "drug": "Sac-TMT + Pembro", "pos": "1L Maintenance",
            "summary": "一線維持治療，結合新型 ADC 與 PD-1 抑制劑。",
            "rationale": "ADC 誘導腫瘤凋亡後釋放抗原，協同提升 Pembrolizumab 之免疫活化效果。",
            "dosing": {
                "Induction": "Carbo + Taxel + Pembro Q3W x6.",
                "Maintenance": "Pembro 400mg Q6W + Sac-TMT 5mg/kg Q6W."
            },
            "outcomes": {"ORR": "Est. > 35%", "mPFS": "Pending", "mOS": "Pending", "HR": "Pending (Phase 3)", "AE": "Anemia"},
            "inclusion": ["pMMR EC", "FIGO Stage III/IV or 1st Recurr (Untreated)", "Measurable disease"],
            "exclusion": ["Sarcoma", "Prior PD-1/L1 inhibitor", "Autoimmune disease"],
            "ref": "ESMO 2025 Abstract"
        }
    ]

# --- 2. 側邊欄：AI 媒合判定區 (收納設計) ---
with st.sidebar:
    st.markdown("### 🤖 專家決策支援")
    api_key = st.text_input("Gemini API Key", type="password")
    
    with st.expander("✨ AI 患者試驗媒合判定 (點開輸入)", expanded=False):
        patient_notes = st.text_area("請輸入患者臨床資訊", height=300, 
                                     placeholder="例：65y/o female, EC stage IIIC, s/p Platinum/Pembro, now PD...")
        if st.button("🚀 開始 AI 媒合分析"):
            if api_key and patient_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    prompt = f"你是一位台灣婦癌權威。資料：{st.session_state.trials_db}。分析患者：{patient_notes}。請建議適合試驗、說明理由及 HR 數據意義。"
                    response = model.generate_content(prompt)
                    st.success("AI 建議如下：")
                    st.write(response.text)
                except Exception as e: st.error(f"AI 異常: {e}")
            else: st.warning("請輸入 API Key 與患者病歷。")

# --- 3. 主頁面：河流圖導航 (結構鎖定) ---
st.markdown("<div class='main-title'>婦癌臨床試驗導航地圖</div>", unsafe_allow_html=True)

cancer_type = st.radio("第一步：選擇癌症類型", ["Endometrial", "Ovarian"], horizontal=True)

def draw_locked_river(cancer_type):
    # 鎖定 5 大主幹節點: 0:Dx, 1:1L, 2:1L Maint, 3:Recurr, 4:Post-Recurr Maint
    base_labels = ["初診 (Dx)", "一線治療 (1L)", "一線維持 (1L Maint.)", "復發期 (Recurrence)", "復發後維持 (PR-Maint.)"]
    base_colors = ["#CFD8DC", "#90A4AE", "#80CBC4", "#EF9A9A", "#CE93D8"]
    
    filtered = [t for t in st.session_state.trials_db if t["cancer"] == cancer_type]
    labels = base_labels.copy()
    colors = base_colors.copy()
    sources, targets, values = [], [], []

    # 建立主幹連結
    sources.extend([0, 1, 0, 3]); targets.extend([1, 2, 3, 4]); values.extend([1, 1, 1, 1])

    for t in filtered:
        idx = len(labels)
        labels.append(f"{t['name']}\n({t['drug']})")
        colors.append("#00796B")
        if "1L Maintenance" in t["pos"]:
            sources.append(2); targets.append(idx); values.append(1)
        elif "Post-Recurr Maint" in t["pos"]:
            sources.append(4); targets.append(idx); values.append(1)
        elif "Recurrence" in t["pos"]:
            sources.append(3); targets.append(idx); values.append(1)

    fig = go.Figure(data=[go.Sankey(
        node = dict(pad=50, thickness=35, label=labels, color=colors),
        link = dict(source=sources, target=targets, value=values, color="rgba(0, 121, 107, 0.1)")
    )])
    fig.update_layout(height=450, font=dict(size=18), margin=dict(l=15, r=15, t=10, b=10))
    return fig, labels

# 河流圖渲染
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = st.session_state.trials_db[0]['name']

st.subheader("第二步：點擊圖中方塊 或 搜尋下方清單")
fig_river, nodes_river = draw_locked_river(cancer_type)
click_evt = plotly_events(fig_river, click_event=True, key=f"sk_{cancer_type}")

if click_evt:
    idx = click_evt[0]['pointNumber']
    clicked_name = nodes_river[idx].split("\n")[0]
    if clicked_name in [t["name"] for t in st.session_state.trials_db]:
        st.session_state.selected_trial = clicked_name

# --- 4. 深度數據看板 (全覽呈現) ---
st.divider()
trial_options = [t["name"] for t in st.session_state.trials_db if t["cancer"] == cancer_type]
try: curr_idx = trial_options.index(st.session_state.selected_trial)
except: curr_idx = 0

selected_name = st.selectbox("🎯 搜尋試驗名稱：", trial_options, index=curr_idx)
t = next(it for it in st.session_state.trials_db if it["name"] == selected_name)

st.markdown(f"<div class='info-card'>", unsafe_allow_html=True)
st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #00897B; padding-bottom:10px;'>📋 {t['name']} 分析報告 ({t['pharma']})</h2>", unsafe_allow_html=True)

c1, c2 = st.columns([1.2, 1])
with c1:
    st.markdown("<div class='section-label'>💊 Dosing & Rationale</div>", unsafe_allow_html=True)
    for arm, details in t['dosing'].items(): st.write(f"🔹 **{arm}**: {details}")
    st.success(f"**機轉說明:** {t['rationale']}")
    

with c2:
    st.markdown("<div class='section-label'>📈 Efficacy & Outcomes</div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class='metric-container'>
            <div style='font-size: 15px; color: #5D6D7E;'>Hazard Ratio (HR)</div>
            <div class='hr-value'>{t['outcomes']['HR']}</div>
        </div>
    """, unsafe_allow_html=True)
    st.write(f"**ORR:** {t['outcomes']['ORR']} | **mPFS:** {t['outcomes']['mPFS']}")
    st.error(f"**Safety/AEs:** {t['outcomes']['AE']}")
    st.caption(f"Source: {t['ref']}")
    

st.divider()
c3, c4 = st.columns(2)
with c3:
    st.markdown("<div class='section-label'>✅ Inclusion</div>", unsafe_allow_html=True)
    for inc in t['inclusion']: st.write(f"🟢 {inc}")
with c4:
    st.markdown("<div class='section-label'>❌ Exclusion</div>", unsafe_allow_html=True)
    for exc in t['exclusion']: st.write(f"🔴 {exc}")
st.markdown("</div>", unsafe_allow_html=True)
