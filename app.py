import streamlit as st
import plotly.graph_objects as go
import google.generativeai as genai
import pandas as pd

# --- 頁面設定 ---
st.set_page_config(page_title="婦癌臨床試驗與藥物機轉地圖", layout="wide")

# --- 1. 臨床試驗與藥物機轉資料庫 ---
TRIALS_DATA = [
    {
        "cancer_type": "Endometrial cancer",
        "name": "GU-US-682-6769 (SG vs Chemo)",
        "phase": "Phase 2/3",
        "stage": "Recurrence",
        "treatment_line": "2nd or 3rd Line",
        "drug_name": "Sacituzumab Govitecan (SG)",
        "rationale": "SG 是一種靶向 Trop-2 的抗體藥物複合體 (ADC)。Trop-2 在子宮內膜癌中高度表達。藥物進入細胞後釋放高濃度的 SN-38 (Topoisomerase I inhibitor)，產生「旁觀者效應 (Bystander effect)」，殺傷鄰近腫瘤細胞。",
        "protocol": "SG 10mg/kg IV (D1, D8 Q21D) vs. Physician's Choice (Doxo or Taxel)",
        "inclusion": ["Advanced/Recurrent Endometrial Cancer", "Prior Platinum-based chemo", "Prior Anti-PD-1/L1 (e.g., Pembro)", "CT confirmed PD"],
        "exclusion": ["Sarcoma histology", "Prior Trop-2 directed ADC therapy"]
    },
    {
        "cancer_type": "Endometrial cancer",
        "name": "MK2870-033 (TroFuse-033)",
        "phase": "Phase 3",
        "stage": "Stage III/IV or Recurrence",
        "treatment_line": "1st Line / Maintenance",
        "drug_name": "Sacituzumab Tirumotecan (Sac-TMT) + Pembro",
        "rationale": "Sac-TMT 同樣為 Trop-2 ADC，結合 Pembrolizumab (PD-1 抑制劑)。此機轉利用 ADC 殺傷細胞釋放腫瘤抗原，進一步增強免疫檢查點抑制劑的抗腫瘤免疫反應。",
        "protocol": "Induction: Carbo + Taxel + Pembro. Maintenance: Pembro +/- Sac-TMT Q6W",
        "inclusion": ["pMMR status", "Newly diagnosed Stage III/IV", "Measurable disease", "Central lab verification required"],
        "exclusion": ["Uterine Sarcoma", "Prior treatment with Pembro"]
    },
    {
        "cancer_type": "Ovarian cancer",
        "name": "DOVE (APGOT-OV07)",
        "phase": "Phase 2",
        "stage": "Recurrence",
        "treatment_line": "Later Line (<5th)",
        "drug_name": "Dostarlimab + Bevacizumab",
        "rationale": "針對卵巢透明細胞癌 (CCC)。Dostarlimab (PD-1 inhibitor) 恢復 T 細胞活性；Bevacizumab (VEGF inhibitor) 改善腫瘤微環境，減少免疫抑制，兩者具有協同作用。",
        "protocol": "Arm A: Dostarlimab / Arm B: Dostarlimab + Beva / Arm C: Chemo",
        "inclusion": ["Clear Cell Carcinoma (CCC) >50%", "Platinum-resistant (PD < 12m)", "Up to 5 prior lines"],
        "exclusion": ["Prior Anti-PD-1/L1 therapy"]
    },
    {
        "cancer_type": "Ovarian cancer",
        "name": "DS8201-772 (T-DXd)",
        "phase": "Phase 2/3",
        "stage": "1st Line Maintenance",
        "treatment_line": "Post-Platinum Maintenance",
        "drug_name": "Trastuzumab Deruxtecan (Enhertu)",
        "rationale": "T-DXd 是一種標靶 HER2 的 ADC。其搭載的載荷為強效 Topoisomerase I 抑制劑，具備極高的藥物抗體比 (DAR)，對於 HER2 低表達 (Low expression) 的腫瘤亦有顯著療效。",
        "protocol": "T-DXd 5.4mg/kg +/- Bevacizumab 15mg/kg Q3W",
        "inclusion": ["HER2 expression (IHC 3+, 2+, or 1+)", "BRCA WT or HRD result not suitable for PARPi", "Post-Platinum Non-PD"],
        "exclusion": ["Active ILD/Pneumonitis"]
    }
]

# --- 2. 側邊欄：Gemini AI 決策區 ---
with st.sidebar:
    st.header("🤖 Gemini AI 臨床決策輔助")
    api_key = st.text_input("Gemini API Key", type="password")
    patient_notes = st.text_area("患者資訊 (病史、基因檢測、既往治療)", height=250)
    
    if st.button("分析推薦試驗"):
        if api_key and patient_notes:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-pro')
                prompt = f"你是一位婦產科腫瘤專家。現有試驗資料：{TRIALS_DATA}。請分析此患者：'{patient_notes}'。請列出推薦試驗及其藥物機轉與理由。"
                response = model.generate_content(prompt)
                st.markdown("---")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"AI 錯誤: {e}")

# --- 3. 主頁面：河流圖呈現 ---
st.title("🎗️ 婦癌臨床試驗導航與藥物機轉系統")

def create_sankey(cancer_type):
    nodes = ["初診 (Dx)", "一線 (1st Line)", "維持 (Maint.)", "復發 (Recurr.)", "臨床試驗 (Trial)"]
    sources, targets, values, labels = [], [], [], []
    
    for t in TRIALS_DATA:
        if t["cancer_type"] == cancer_type:
            if "1st Line" in t["treatment_line"]:
                sources.extend([0, 1]); targets.extend([1, 4]); values.extend([1, 1]); labels.extend(["Standard Care", t["name"]])
            elif "Maintenance" in t["treatment_line"]:
                sources.extend([1, 2]); targets.extend([2, 4]); values.extend([1, 1]); labels.extend(["Post-Platinum", t["name"]])
            elif "Recurrence" in t["stage"]:
                sources.extend([0, 3]); targets.extend([3, 4]); values.extend([1, 1]); labels.extend(["Follow up", t["name"]])

    fig = go.Figure(data=[go.Sankey(
        node = dict(pad = 30, thickness = 20, label = nodes, color = "teal"),
        link = dict(source = sources, target = targets, value = values, label = labels, color = "rgba(0, 128, 128, 0.2)")
    )])
    fig.update_layout(height=350, margin=dict(l=10, r=10, t=40, b=10))
    return fig

tab_ec, tab_oc = st.tabs(["子宮內膜癌", "卵巢癌"])
with tab_ec:
    st.plotly_chart(create_sankey("Endometrial cancer"), use_container_width=True)
with tab_oc:
    st.plotly_chart(create_sankey("Ovarian cancer"), use_container_width=True)

# --- 4. 試驗詳情與藥物機轉區 ---
st.divider()
st.subheader("🔍 臨床試驗與藥物機轉詳情")

selected_name = st.selectbox("請選擇臨床試驗：", [t["name"] for t in TRIALS_DATA])
trial_info = next(item for item in TRIALS_DATA if item["name"] == selected_name)

col1, col2 = st.columns([1, 1])
with col1:
    st.markdown(f"### 🧪 藥物機轉: {trial_info['drug_name']}")
    st.help(trial_info['rationale'])
    st.markdown(f"**給藥 Protocol:** \n> {trial_info['protocol']}")

with col2:
    st.success("**✅ 入案條件 (Inclusion)**")
    for inc in trial_info['inclusion']:
        st.write(f"- {inc}")
    st.error("**❌ 排除條件 (Exclusion)**")
    for exc in trial_info['exclusion']:
        st.write(f"- {exc}")
