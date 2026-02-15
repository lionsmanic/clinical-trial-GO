import streamlit as st
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events
import google.generativeai as genai

# --- 🏥 專業臨床儀表板視覺配置 ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', sans-serif;
        background-color: #F8FAF9; /* 醫療護眼色 */
        color: #1A3030;
        font-size: 20px !important;
    }
    .main-title {
        font-size: 48px !important;
        font-weight: 800;
        color: #064E3B;
        text-align: center;
        padding: 25px;
        background: white;
        border-bottom: 6px solid #10B981;
        margin-bottom: 20px;
    }
    .highlight-box {
        background: #ECFDF5;
        border: 2px solid #10B981;
        border-radius: 15px;
        padding: 20px;
        margin-top: 10px;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.1);
    }
    .detail-card {
        background: white;
        border-radius: 20px;
        padding: 35px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        border: 1px solid #D1FAE5;
        margin-top: 20px;
    }
    .metric-value { font-size: 26px; font-weight: 700; color: #059669; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 臨床數據庫 (結構化與數據補完) ---
if 'trials_db' not in st.session_state:
    st.session_state.trials_db = [
        {
            "cancer": "Endometrial", "name": "GU-US-682-6769", "drug": "Sacituzumab Govitecan (SG)",
            "pos": "Recurrence", "highlights": "• 針對 Trop-2 標靶 ADC\n• 適用於含鉑與免疫治療後進展\n• 顯著提升後線 ORR 與生存期",
            "rationale": "標靶 Trop-2 ADC，利用 Topoisomerase I 抑制劑產生 Bystander Effect，殺傷周邊低表達癌細胞。",
            "protocol": "SG 10mg/kg IV (D1, D8 Q21D) 直到 PD。",
            "outcomes": {"status": "Published", "ORR": "28%", "PFS": "5.6m", "OS": "12.8m", "AE": "Neutropenia (15%), Diarrhea (10%)"},
            "inclusion": ["進展性/復發性 EC", "先前接受過 Platinum 化療", "先前接受過 Anti-PD-1/L1"],
            "ref": "JCO 2024; TROPiCS-03 Study"
        },
        {
            "cancer": "Endometrial", "name": "MK2870-033", "drug": "Sac-TMT + Pembro",
            "rationale": "新型 Trop-2 ADC 搭配免疫檢查點抑制劑，誘導抗原釋放並增強 T 細胞活化。",
            "pos": "Maintenance", "highlights": "• 一線維持治療首選試驗\n• 結合新型 ADC 與 PD-1 抑制劑\n• 針對 pMMR 患者設計",
            "protocol": "Induction (6 cycles) -> Maintenance (Pembro +/- Sac-TMT Q6W)。",
            "outcomes": {"status": "Ongoing", "ORR": "Expect > 35%", "PFS": "N/A", "OS": "N/A", "AE": "Anemia, Fatigue"},
            "inclusion": ["pMMR 患者", "新診斷 Stage III/IV 或初次復發", "需送中央檢體"],
            "ref": "ESMO 2025 Abstract"
        },
        {
            "cancer": "Ovarian", "name": "DOVE (APGOT-OV07)", "drug": "Dostarlimab + Beva",
            "pos": "Recurrence", "highlights": "• 針對透明細胞癌 (OCCC)\n• 雙重阻斷 PD-1 與 VEGF\n• 抗藥性復發患者的新選擇",
            "rationale": "利用抗血管生成與免疫療法的協同作用，改善 OCCC 惡劣的腫瘤微環境。",
            "protocol": "Arm B: Dostarlimab + Bevacizumab (15mg/kg Q3W)。",
            "outcomes": {"status": "Early Data", "ORR": "40%", "PFS": "8.2m", "OS": "N/A", "AE": "Hypertension (12%), Fatigue"},
            "inclusion": ["OCCC 組織型態 > 50%", "Platinum-resistant (PD < 12m)"],
            "ref": "ClinicalTrials.gov NCT06023862"
        },
        {
            "cancer": "Ovarian", "name": "DS8201-772", "drug": "T-DXd (Enhertu)",
            "pos": "Maintenance", "highlights": "• 針對 HER2 Low (1+/2+) 表現\n• 維持期替代 PARPi 方案\n• 精準 ADC 投藥機轉",
            "rationale": "HER2 標靶 ADC，透過極高 DAR (Drug-Antibody Ratio) 提供強大的細胞毒素殺傷力。",
            "protocol": "T-DXd 5.4mg/kg Q3W +/- Bevacizumab。",
            "outcomes": {"status": "Phase 3 Data", "ORR": "N/A (Maint.)", "PFS": "Expect > 12m", "OS": "N/A", "AE": "Nausea, Risk of ILD (6%)"},
            "inclusion": ["HER2 IHC 1+/2+/3+", "BRCA WT 或 HRD 結果不適合 PARPi"],
            "ref": "DESTINY-PanTumor 02"
        }
    ]

# --- 2. 狀態同步初始化 ---
if 'clicked_trial' not in st.session_state:
    st.session_state.clicked_trial = None

# --- 3. 主頁面：河流圖導航 (結構鎖定) ---
st.markdown("<div class='main-title'>婦癌臨床試驗導航儀表板</div>", unsafe_allow_html=True)

cancer_type = st.radio("第一步：選擇癌別", ["Endometrial", "Ovarian"], horizontal=True)

def draw_stable_river(cancer_type):
    # 鎖定主幹節點
    base_labels = ["初診 (Dx)", "一線治療 (1L)", "維持期 (Maint.)", "復發期 (Recurr.)"]
    base_colors = ["#D1D5DB", "#9CA3AF", "#6EE7B7", "#FCA5A1"]
    
    filtered = [t for t in st.session_state.trials_db if t["cancer"] == cancer_type]
    labels = base_labels.copy()
    colors = base_colors.copy()
    sources, targets, values = [], [], []

    for t in filtered:
        idx = len(labels)
        labels.append(f"{t['name']}\n({t['drug']})")
        colors.append("#059669") # 試驗方塊綠色
        
        if t["pos"] == "Maintenance":
            sources.extend([1, 2]); targets.extend([2, idx]); values.extend([1, 1])
        elif t["pos"] == "Recurrence":
            sources.extend([0, 3]); targets.extend([3, idx]); values.extend([1, 1])

    fig = go.Figure(data=[go.Sankey(
        node = dict(pad=45, thickness=35, label=labels, color=colors),
        link = dict(source=sources, target=targets, value=values, color="rgba(16, 185, 129, 0.1)")
    )])
    fig.update_layout(height=450, font=dict(size=17), margin=dict(l=15, r=15, t=10, b=10))
    return fig, labels

# 河流圖與快看框
st.subheader("第二步：點擊圖中「綠色方塊」查看試驗亮點")
col_plot, col_summary = st.columns([3, 1])

with col_plot:
    fig_river, current_labels = draw_stable_river(cancer_type)
    # 捕捉點擊
    click_evt = plotly_events(fig_river, click_event=True, key=f"sk_{cancer_type}")
    if click_evt:
        clicked_idx = click_evt[0]['pointNumber']
        label_full = current_labels[clicked_idx]
        clicked_name = label_full.split("\n")[0]
        if clicked_name in [t["name"] for t in st.session_state.trials_db]:
            st.session_state.clicked_trial = clicked_name

with col_summary:
    if st.session_state.clicked_trial:
        t_summary = next(it for it in st.session_state.trials_db if it["name"] == st.session_state.clicked_trial)
        st.markdown(f"""
            <div class='highlight-box'>
                <h4 style='color:#065F46; margin:0;'>✨ 試驗快看重點</h4>
                <p style='font-weight:700; margin-top:10px;'>{t_summary['name']}</p>
                <div style='font-size:17px; line-height:1.6;'>{t_summary['highlights'].replace('\\n', '<br>')}</div>
                <hr style='border: 0.5px solid #10B981;'>
                <p style='font-size:15px; color:#666;'>※ 完整數據見下方深度查閱區</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.info("👆 請點擊河流圖右側試驗方塊。")

# --- 4. 深度查閱區 (選單驅動) ---
st.divider()
st.subheader("🔍 第三步：深度臨床數據與 Protocol 查閱")

# 下拉選單獨立過濾
trial_options = [t["name"] for t in st.session_state.trials_db if t["cancer"] == cancer_type]
selected_detail = st.selectbox("🎯 選擇或搜尋試驗名稱以查看深度細節：", trial_options)

if selected_detail:
    t = next(it for it in st.session_state.trials_db if it["name"] == selected_detail)
    
    st.markdown("<div class='detail-card'>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["💊 給藥與機轉", "📊 臨床文獻數據", "✅ 收案條件"])
    
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"#### 藥物機轉：{t['drug']}")
            st.info(t['rationale'])
            [Image of antibody-drug conjugate mechanism of action including binding, internalisation and toxin release]
        with c2:
            st.markdown("#### 給藥 Protocol")
            st.success(t['protocol'])

    with tab2:
        res = t['outcomes']
        st.markdown(f"#### 📈 實證數據摘要 ({res['status']})")
        m1, m2, m3 = st.columns(3)
        with m1: st.metric("ORR (有效率)", res['ORR'])
        with m2: st.metric("Median PFS", res['PFS'])
        with m3: st.metric("Median OS", res['OS'])
        
        st.markdown(f"**常見副作用 (AE):** {res['AE']}")
        st.caption(f"數據出處：{t['ref']}")
        [Image of Kaplan-Meier survival curve for clinical trials]

    with tab3:
        cc1, cc2 = st.columns(2)
        with cc1:
            st.write("**✅ 入案標準 (Inclusion)**")
            for inc in t['inclusion']: st.write(f"🔹 {inc}")
        with cc2:
            st.write("**❌ 排除標準 (Exclusion)**")
            for exc in t['exclusion']: st.write(f"🔸 {exc}")
    st.markdown("</div>", unsafe_allow_html=True)

# 病程河流圖參考
[Image of clinical trial phases in gynaecological oncology]
