import streamlit as st
import plotly.graph_objects as go
import google.generativeai as genai
import pandas as pd

# --- 頁面配置與自定義 CSS ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

st.markdown("""
    <style>
    .main-title { font-size: 42px !important; font-weight: 700; color: #008080; padding-bottom: 20px; }
    html, body, [class*="css"] { font-size: 19px !important; line-height: 1.6; }
    .stAlert { border-radius: 12px; border: 1px solid #d1d9e6; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #eee; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; font-size: 20px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 臨床試驗資料庫 ---
TRIALS_DATA = [
    {
        "cancer_type": "Endometrial cancer",
        "name": "GU-US-682-6769 (SG vs Chemo)",
        "phase": "Phase 2/3",
        "stage": "Recurrence",
        "treatment_line": "2nd or 3rd Line",
        "drug_name": "Sacituzumab Govitecan (SG)",
        "rationale": "SG 是一種標靶 Trop-2 的抗體藥物複合體 (ADC)。其機轉係利用 Anti-Trop-2 Antibody 將強效的 Topoisomerase I Inhibitor (SN-38) 直接送入腫瘤細胞內，透過 Bystander Effect (旁觀者效應) 同時殺傷周邊低表達 Trop-2 的癌細胞。",
        "protocol": "SG 10mg/kg 靜脈注射 (D1, D8 Q21D) 直到 PD 或不可耐受之毒性；對照組為醫師選擇之化療 (Doxo 或 Taxel)。",
        "inclusion": ["經組織學證實為進展性或復發性 EC", "先前接受過 Platinum 化療", "先前接受過 Anti-PD-1/L1", "ECOG 0-1"],
        "exclusion": ["Uterine Sarcoma", "先前接受過 Trop-2 ADC", "活動性 CNS 轉移"]
    },
    {
        "cancer_type": "Endometrial cancer",
        "name": "MK2870-033 (TroFuse-033)",
        "phase": "Phase 3",
        "stage": "Stage III/IV",
        "treatment_line": "1st Line / Maintenance",
        "drug_name": "Sacituzumab Tirumotecan (Sac-TMT) + Pembro",
        "rationale": "新型 Trop-2 ADC (Sac-TMT) 結合 PD-1 抑制劑。ADC 誘導細胞死亡釋放抗原，協同提升免疫療法之療效。",
        "protocol": "Induction: Carbo + Taxel + Pembro (Q3W x 6)。Maintenance: Pembro 400mg Q6W +/- Sac-TMT。",
        "inclusion": ["pMMR 患者", "新診斷 Stage III/IV 或初次復發未治療者", "需提供腫瘤檢體送中央實驗室", "肝腎功能正常"],
        "exclusion": ["Uterine Sarcoma", "先前用過 Pembro", "自體免疫疾病"]
    },
    {
        "cancer_type": "Ovarian cancer",
        "name": "DOVE (APGOT-OV07)",
        "phase": "Phase 2",
        "stage": "Recurrence",
        "treatment_line": "Later Line (<5th)",
        "drug_name": "Dostarlimab + Bevacizumab",
        "rationale": "針對 Ovarian Clear Cell Carcinoma (OCCC)。Dostarlimab 阻斷 PD-1，Bevacizumab 抑制 VEGF 改善腫瘤血管化，兩者具協同作用。",
        "protocol": "Arm A: Dostarlimab 單用; Arm B: Dostarlimab + Beva (15mg/kg Q3W); Arm C: 非鉑類化療。",
        "inclusion": ["Ovarian Clear Cell Carcinoma (>50%)", "Platinum-resistant (PD < 12m)", "先前治療線數 <= 5線"],
        "exclusion": ["先前用過 Anti-PD-1/L1/L2", "非透明細胞癌", "腸阻塞症狀"]
    },
    {
        "cancer_type": "Ovarian cancer",
        "name": "DS8201-772 (T-DXd)",
        "phase": "Phase 2/3",
        "stage": "1st Line Maintenance",
        "treatment_line": "Post-Platinum Maintenance",
        "drug_name": "Trastuzumab Deruxtecan (Enhertu)",
        "rationale": "標靶 HER2 之 ADC。對於 HER2 低表達腫瘤具有強大殺傷力，探討作為一線維持治療的潛力。",
        "protocol": "T-DXd 5.4mg/kg Q3W +/- Bevacizumab 15mg/kg。",
        "inclusion": ["HER2 表現 (IHC 3+/2+/1+) 經確認", "BRCA WT 或 HRD 不適合使用 PARPi 者", "一線 Platinum+Beva 治療後 Non-PD"],
        "exclusion": ["曾患有 ILD/肺炎", "先前接受過 HER2 標靶治療", "LVEF < 50%"]
    }
]

# --- 2. 側邊欄：AI 決策區 ---
with st.sidebar:
    st.markdown("### 🤖 Gemini AI 決策輔助")
    api_key = st.text_input("Gemini API Key", type="password")
    patient_notes = st.text_area("輸入患者臨床摘要", height=250)
    if st.button("🚀 開始媒合試驗"):
        if api_key and patient_notes:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-pro')
                prompt = f"你是一位台灣婦癌專家。根據資料：{TRIALS_DATA}，分析患者：{patient_notes}。建議適合試驗與理由。"
                response = model.generate_content(prompt)
                st.markdown("---")
                st.write(response.text)
            except Exception as e:
                st.error(f"AI 連線失敗：{e}")

# --- 3. 主頁面：河流圖與動態連動 ---
st.markdown("<div class='main-title'>🎗️ 婦癌臨床試驗導航系統</div>", unsafe_allow_html=True)

# 使用 Tabs 來區分癌別，並儲存當前選擇的癌別到 Session State
tab_ec, tab_oc = st.tabs(["子宮內膜癌 (Endometrial)", "卵巢癌 (Ovarian)"])

def create_sankey(cancer_type):
    nodes = ["初診 (Dx)", "一線治療 (1st Line)", "維持期 (Maint.)", "復發期 (Recurr.)", "臨床試驗 (Trial)"]
    sources, targets, values, labels = [], [], [], []
    for t in TRIALS_DATA:
        if t["cancer_type"] == cancer_type:
            if "1st Line" in t["treatment_line"] and "Maintenance" not in t["treatment_line"]:
                sources.extend([0, 1]); targets.extend([1, 4]); values.extend([1, 1]); labels.extend(["標準治療", t["name"]])
            elif "Maintenance" in t["treatment_line"]:
                sources.extend([1, 2]); targets.extend([2, 4]); values.extend([1, 1]); labels.extend(["化療穩定", t["name"]])
            elif "Recurrence" in t["stage"]:
                sources.extend([0, 3]); targets.extend([3, 4]); values.extend([1, 1]); labels.extend(["復發", t["name"]])
    fig = go.Figure(data=[go.Sankey(
        node = dict(pad = 30, thickness = 25, label = nodes, color = "#008080"),
        link = dict(source = sources, target = targets, value = values, label = labels, color = "rgba(0, 128, 128, 0.15)")
    )])
    fig.update_layout(height=350, margin=dict(l=10, r=10, t=20, b=20))
    return fig

# 決定目前選中的癌別
current_cancer = "Endometrial cancer"
with tab_ec:
    st.plotly_chart(create_sankey("Endometrial cancer"), use_container_width=True)
    current_cancer = "Endometrial cancer"

with tab_oc:
    st.plotly_chart(create_sankey("Ovarian cancer"), use_container_width=True)
    # 這裡的邏輯：如果使用者切換到第二個 Tab，我們需要偵測並更新 current_cancer
    # 在 Streamlit 中，Tabs 內容是並行的，所以我們透過連動選單來過濾

# --- 4. 試驗詳情（動態選單） ---
st.divider()
st.subheader("🔍 臨床試驗詳情")

# 過濾出符合當前癌別的試驗清單
# 技巧：透過下拉選單過濾，使用者切換癌別後，選單只會出現該癌別的試驗
available_trials = [t for t in TRIALS_DATA if t["cancer_type"] in [current_cancer]]

# 如果在 Tab1，顯示 EC 試驗；如果在 Tab2，顯示 OC 試驗
# 這裡我們用一個技巧：讓使用者選擇癌別來連動選單，或是直接顯示所有試驗但分類
all_cancer_types = ["Endometrial cancer", "Ovarian cancer"]
selected_cancer_type = st.radio("請先確認癌別以過濾試驗：", all_cancer_types, horizontal=True)

filtered_trial_names = [t["name"] for t in TRIALS_DATA if t["cancer_type"] == selected_cancer_type]

selected_name = st.selectbox("請選擇試驗名稱：", filtered_trial_names)

# 顯示選中試驗的詳細資訊
t = next(item for item in TRIALS_DATA if item["name"] == selected_name)

# 顯示藥物機轉與詳情

st.markdown(f"### 🧪 藥物機轉：{t['drug_name']}")
with st.expander("查看機轉詳解", expanded=True):
    st.info(t['rationale'])

col1, col2 = st.columns(2)
with col1:
    st.markdown("#### 💉 給藥 Protocol")
    st.success(t['protocol'])
    st.write(f"**分期/階段:** {t['stage']} ({t['phase']})")

with col2:
    st.markdown("#### ✅ 入案條件 (Inclusion)")
    for inc in t['inclusion']: st.write(f"🔹 {inc}")
    st.markdown("#### ❌ 排除條件 (Exclusion)")
    for exc in t['exclusion']: st.write(f"🔸 {exc}")
