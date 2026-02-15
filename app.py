import streamlit as st
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events
import google.generativeai as genai

# --- 🏥 醫學專業導航風格配置 ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', sans-serif;
        background-color: #F7F9F9;
        font-size: 19px !important;
    }
    .main-title {
        font-size: 46px !important;
        font-weight: 800;
        color: #004D40;
        text-align: center;
        padding: 30px;
        background: #FFFFFF;
        border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .info-section {
        background: #FFFFFF;
        border-radius: 15px;
        padding: 25px;
        border: 1px solid #E0F2F1;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .highlight-box {
        background: #E0F2F1;
        border-left: 8px solid #00897B;
        padding: 20px;
        border-radius: 10px;
    }
    .section-label {
        font-size: 24px;
        font-weight: 700;
        color: #00695C;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 完整臨床數據庫 (修復所有漏掉的 Key) ---
if 'trials_db' not in st.session_state:
    st.session_state.trials_db = [
        {
            "cancer": "Endometrial", "name": "GU-US-682-6769", "drug": "Sacituzumab Govitecan (SG)",
            "pos": "Recurrence", "summary": "針對 Trop-2 標靶 ADC，適用於含鉑與免疫治療後進展之患者。",
            "rationale": "標靶 Trop-2 ADC，利用 Topoisomerase I 抑制劑產生 Bystander Effect，殺傷周邊癌細胞。",
            "protocol": "SG 10mg/kg IV (D1, D8 Q21D) 直到 PD。",
            "outcomes": {"ORR": "28%", "PFS": "5.6m", "OS": "12.8m", "AE": "Neutropenia, Diarrhea"},
            "inclusion": ["進展性/復發性 EC", "曾用過 Platinum 化療", "曾用過 Anti-PD-1/L1"],
            "exclusion": ["子宮肉瘤 (Uterine Sarcoma)", "先前接受過 Trop-2 ADC", "活動性 CNS 轉移"],
            "ref": "JCO 2024; Phase 2 TROPiCS-03"
        },
        {
            "cancer": "Endometrial", "name": "MK2870-033", "drug": "Sac-TMT + Pembro",
            "pos": "Maintenance", "summary": "新型 Trop-2 ADC 搭配免疫檢查點抑制劑，強化一線化療後的緩解效果。",
            "rationale": "ADC 誘導細胞死亡釋放抗原，協同提升 Pembrolizumab 之免疫活化效果。",
            "protocol": "Induction (6 cycles) -> Maintenance (Pembro +/- Sac-TMT Q6W)。",
            "outcomes": {"ORR": "Expect > 35%", "PFS": "N/A", "OS": "N/A", "AE": "Anemia, Fatigue"},
            "inclusion": ["pMMR 患者", "新診斷 Stage III/IV", "需送中央檢體至英國"],
            "exclusion": ["先前用過 Pembro", "活動性自體免疫疾病", "Sarcoma"],
            "ref": "ESMO 2025 Abstract"
        },
        {
            "cancer": "Ovarian", "name": "DOVE", "drug": "Dostarlimab + Beva",
            "pos": "Recurrence", "summary": "針對透明細胞癌 (OCCC)，雙重阻斷 PD-1 與 VEGF。",
            "rationale": "Dostarlimab 恢復 T 細胞功能，Bevacizumab 改善腫瘤微環境之血管化。",
            "protocol": "Arm B: Dostarlimab + Beva (15mg/kg Q3W)。",
            "outcomes": {"ORR": "40%", "PFS": "8.2m", "OS": "N/A", "AE": "Hypertension (12%)"},
            "inclusion": ["OCCC > 50%", "Platinum-resistant (PD < 12m)"],
            "exclusion": ["先前用過 PD-1 抑制劑", "臨床顯著腸阻塞"],
            "ref": "NCT06023862"
        },
        {
            "cancer": "Ovarian", "name": "DS8201-772", "drug": "T-DXd (Enhertu)",
            "pos": "Maintenance", "summary": "針對 HER2 Low 表現之維持治療，旨在替代 PARPi。",
            "rationale": "標靶 HER2 之 ADC，透過極高 DAR 載荷提供強大殺傷力。",
            "protocol": "T-DXd 5.4mg/kg Q3W +/- Bevacizumab。",
            "outcomes": {"ORR": "N/A (Maint.)", "PFS": "Expect > 12m", "OS": "N/A", "AE": "Nausea, ILD (6%)"},
            "inclusion": ["HER2 IHC 1+/2+/3+", "BRCA WT / HRD 不適合 PARPi"],
            "exclusion": ["ILD 肺纖維化病史", "先前接受過 HER2 標靶治療", "LVEF < 50%"],
            "ref": "DESTINY-PanTumor 02"
        }
    ]

# --- 2. 狀態同步 ---
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = st.session_state.trials_db[0]['name']

# --- 3. 主頁面：河流圖導航 ---
st.markdown("<div class='main-title'>婦癌臨床試驗導航儀表板</div>", unsafe_allow_html=True)

cancer_type = st.radio("第一步：選擇癌症類型", ["Endometrial", "Ovarian"], horizontal=True)

def draw_locked_river(cancer_type):
    # 鎖定病程主幹節點: 0:Dx, 1:1L, 2:Maint, 3:Recurr
    base_labels = ["初診 (Dx)", "一線治療 (1L)", "維持期 (Maint.)", "復發期 (Recurr.)"]
    base_colors = ["#D1D5DB", "#9CA3AF", "#80CBC4", "#EF9A9A"]
    
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

# 河流圖與快看摘要
st.subheader("第二步：點擊圖中「深青色」試驗方塊 或 下方選單選擇")
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
    t_quick = next(it for it in st.session_state.trials_db if it["name"] == st.session_state.selected_trial)
    st.markdown(f"""
        <div class='highlight-box'>
            <h4 style='color:#004D40; margin:0;'>✨ 試驗快速亮點</h4>
            <p style='font-weight:700; margin-top:10px;'>{t_quick['name']}</p>
            <p style='font-size:17px;'>{t_quick['summary']}</p>
            <hr>
            <p style='font-size:15px; color:#555;'>詳細 Protocol 於下方全覽區呈現</p>
        </div>
    """, unsafe_allow_html=True)

# --- 4. 深度資訊看板 (全覽呈現，不分標籤頁) ---
st.divider()
st.subheader("🔍 第三步：深度臨床數據、機轉與入案全覽")

# 雙軌選單
trial_options = [t["name"] for t in st.session_state.trials_db if t["cancer"] == cancer_type]
try:
    current_idx = trial_options.index(st.session_state.selected_trial)
except ValueError:
    current_idx = 0
    st.session_state.selected_trial = trial_options[0]

selected_name = st.selectbox("🎯 搜尋或選擇試驗：", trial_options, index=current_idx)
t = next(it for it in st.session_state.trials_db if it["name"] == selected_name)

# --- 資訊全覽區 (Grid Layout) ---
st.markdown(f"<div class='info-section'>", unsafe_allow_html=True)
st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #00897B; padding-bottom:10px;'>📋 {t['name']} 完整報告</h2>", unsafe_allow_html=True)

# 第一列：藥物機轉與實證數據
r1_c1, r1_c2 = st.columns([1.2, 1])
with r1_c1:
    st.markdown("<div class='section-label'>💊 藥物給藥與機轉</div>", unsafe_allow_html=True)
    st.info(f"**藥物配方:** {t['drug']}\n\n**機轉簡介:** {t['rationale']}")
    
    st.success(f"**給藥方式 (Protocol):**\n{t['protocol']}")

with r1_c2:
    st.markdown("<div class='section-label'>📊 實證文獻數據</div>", unsafe_allow_html=True)
    m1, m2 = st.columns(2)
    m1.metric("ORR (有效率)", t['outcomes']['ORR'])
    m2.metric("Median PFS", t['outcomes']['PFS'])
    
    st.markdown(f"**Median OS:** {t['outcomes']['OS']}")
    st.markdown(f"**常見副作用 (AE):** {t['outcomes']['AE']}")
    st.caption(f"數據出處：{t['ref']}")
    

[Image of Kaplan-Meier survival curve]


st.divider()

# 第二列：收案條件
r2_c1, r2_c2 = st.columns(2)
with r2_c1:
    st.markdown("<div class='section-label'>✅ 入案標準 (Inclusion)</div>", unsafe_allow_html=True)
    for inc in t['inclusion']:
        st.write(f"🔹 {inc}")

with r2_c2:
    st.markdown("<div class='section-label'>❌ 排除標準 (Exclusion)</div>", unsafe_allow_html=True)
    for exc in t['exclusion']:
        st.write(f"🔸 {exc}")

st.markdown("</div>", unsafe_allow_html=True)

# 底部病程參考圖
