import streamlit as st
import plotly.graph_objects as go
import google.generativeai as genai
import pandas as pd

# --- 頁面配置與自定義 CSS ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

# 修正：將 unsafe_allow_stdio 改回 unsafe_allow_html
st.markdown("""
    <style>
    .main-title { font-size: 42px !important; font-weight: 700; color: #008080; padding-bottom: 20px; }
    html, body, [class*="css"] { font-size: 19px !important; line-height: 1.6; }
    .stAlert { border-radius: 12px; border: 1px solid #d1d9e6; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #eee; }
    .reportview-container .main .block-container { padding-top: 2rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 臨床試驗資料庫 ---
TRIALS_DATA = [
    {
        "cancer_type": "Endometrial cancer (子宮內膜癌)",
        "name": "GU-US-682-6769 (SG vs Chemo)",
        "phase": "Phase 2/3",
        "stage": "Recurrence (復發性)",
        "treatment_line": "2nd or 3rd Line (二/三線治療)",
        "drug_name": "Sacituzumab Govitecan (SG)",
        "rationale": "SG 是一種標靶 Trop-2 的抗體藥物複合體 (ADC)。其機轉係利用 Anti-Trop-2 Antibody 將強效的 Topoisomerase I Inhibitor (SN-38) 直接送入腫瘤細胞內，透過 Bystander Effect (旁觀者效應) 同時殺傷周邊低表達 Trop-2 的癌細胞。",
        "protocol": "SG 10mg/kg 靜脈注射 (D1, D8 Q21D) 直到 PD 或不可耐受之毒性；對照組為醫師選擇之化療 (Doxo 或 Taxel)。",
        "inclusion": [
            "經組織學證實為進展性或復發性 Endometrial Cancer",
            "先前必須至少接受過一次含 Platinum 之全身性化療",
            "先前必須接受過 Anti-PD-1/L1 免疫療法 (如 Pembro)",
            "ECOG Performance Status 0-1",
            "具備可測量之病灶 (RECIST 1.1)"
        ],
        "exclusion": [
            "Uterine Sarcoma (子宮肉瘤)",
            "先前接受過任何針對 Trop-2 之 ADC 治療",
            "具有活動性 CNS Metastasis (中樞神經轉移)",
            "治療前 2 週內接受過全身性類固醇治療"
        ]
    },
    {
        "cancer_type": "Endometrial cancer (子宮內膜癌)",
        "name": "MK2870-033 (TroFuse-033)",
        "phase": "Phase 3",
        "stage": "Stage III/IV or Recurrence",
        "treatment_line": "1st Line / Maintenance (一線維持)",
        "drug_name": "Sacituzumab Tirumotecan (Sac-TMT) + Pembro",
        "rationale": "此為 Combo Therapy，結合新型 Trop-2 ADC (Sac-TMT) 與 PD-1 抑制劑 (Pembro)。ADC 誘導腫瘤細胞死亡釋放抗原，可轉化腫瘤微環境，進而提升免疫療法之療效。",
        "protocol": "引導期 (Induction): Carbo + Taxel + Pembro (Q3W x 6 cycles)。維持期 (Maintenance): Pembro 400mg Q6W 搭配或不搭配 Sac-TMT。",
        "inclusion": [
            "Mismatch Repair Proficient (pMMR) 之患者",
            "新診斷之 Stage III/IV 或初次復發且未接受過全身治療者",
            "必須提供腫瘤檢體送至中央實驗室 (UK) 進行檢測",
            "適當之肝腎功能 (ANC ≥ 1,500/mm³, Platelets ≥ 100,000/mm³)"
        ],
        "exclusion": [
            "所有類型的 Uterine Sarcoma",
            "先前曾使用過 Pembro 或其他 PD-1/PD-L1 抑制劑",
            "具有活動性自體免疫疾病"
        ]
    },
    {
        "cancer_type": "Ovarian cancer (卵巢癌)",
        "name": "DOVE (APGOT-OV07)",
        "phase": "Phase 2",
        "stage": "Recurrence (復發性)",
        "treatment_line": "Later Line (<5th)",
        "drug_name": "Dostarlimab + Bevacizumab",
        "rationale": "針對 Ovarian Clear Cell Carcinoma (OCCC)。利用 Dostarlimab 阻斷 PD-1 路徑恢復 T 細胞殺傷力，輔以 Bevacizumab 抑制 VEGF 分子，改善腫瘤血管化並協同增強免疫反應。",
        "protocol": "Arm A: Dostarlimab 單獨使用；Arm B: Dostarlimab + Beva (15mg/kg Q3W)；Arm C: 醫師選擇之非鉑類化療 (Gem/Doxo/Taxel)。",
        "inclusion": [
            "經組織學確認為 Ovarian Clear Cell Carcinoma (>50%)",
            "Platinum-resistant (最近一次含鉑治療 12 個月內復發者)",
            "先前治療線數不超過 5 線",
            "年滿 20 歲且具備足夠器官功能"
        ],
        "exclusion": [
            "先前曾使用過 Anti-PD-1/L1/L2 或 CTLA-4 治療",
            "非透明細胞癌之組織型態 (如 High-grade Serous)",
            "臨床顯著之腹水或腸阻塞症狀"
        ]
    },
    {
        "cancer_type": "Ovarian cancer (卵巢癌)",
        "name": "DS8201-772 (T-DXd)",
        "phase": "Phase 2/3",
        "stage": "1st Line Maintenance (一線維持)",
        "treatment_line": "Post-Platinum Maintenance",
        "drug_name": "Trastuzumab Deruxtecan (Enhertu)",
        "rationale": "標靶 HER2 之 ADC。搭載強效 Topoisomerase I Inhibitor，對 HER2 低表達腫瘤具有極佳殺傷力。此試驗探討在第一線化療穩定後，作為維持治療替代 PARPi 的潛力。",
        "protocol": "T-DXd 5.4mg/kg 每 3 週給藥一次 (Q3W)，可搭配或不搭配 Bevacizumab 15mg/kg。",
        "inclusion": [
            "HER2 表現 (IHC 3+, 2+, 或 1+) 經中央實驗室確認",
            "BRCA Wild-type 或 HRD 結果顯示對 PARP Inhibitor 療效預期不佳者",
            "第一線 Platinum + Bevacizumab 治療 6-8 週期後達 Non-PD (CR/PR/SD)"
        ],
        "exclusion": [
            "患有或曾患有需類固醇治療之 Interstitial Lung Disease (ILD) 或肺炎",
            "先前接受過任何針對 HER2 之治療 (如 Trastuzumab)",
            "LVEF (左心室射出率) < 50%"
        ]
    }
]

# --- 2. 側邊欄 ---
with st.sidebar:
    st.markdown("### 🤖 Gemini AI 決策輔助")
    api_key = st.text_input("Gemini API Key", type="password")
    patient_notes = st.text_area("輸入患者臨床摘要", height=300, placeholder="例如：65y/o OCCC, stage IIIC, s/p IP chemo...")
    
    if st.button("🚀 開始媒合試驗"):
        if api_key and patient_notes:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-pro')
                prompt = f"你是一位台灣婦癌專家。請根據試驗資料：{TRIALS_DATA}，分析患者：{patient_notes}。請建議適合試驗，說明理由。"
                response = model.generate_content(prompt)
                st.markdown("---")
                st.write(response.text)
            except Exception as e:
                st.error(f"AI 連線失敗：{e}")

# --- 3. 主頁面 ---
st.markdown("<div class='main-title'>🎗️ 婦癌臨床試驗導航地圖</div>", unsafe_allow_html=True)

def create_sankey(cancer_type):
    nodes = ["初診 (Dx)", "一線 (1st Line)", "維持 (Maint.)", "復發 (Recurr.)", "試驗 (Trial)"]
    sources, targets, values, labels = [], [], [], []
    for t in TRIALS_DATA:
        if t["cancer_type"].startswith(cancer_type):
            if "1st Line" in t["treatment_line"] and "Maintenance" not in t["treatment_line"]:
                sources.extend([0, 1]); targets.extend([1, 4]); values.extend([1, 1]); labels.extend(["標準治療", t["name"]])
            elif "Maintenance" in t["treatment_line"]:
                sources.extend([1, 2]); targets.extend([2, 4]); values.extend([1, 1]); labels.extend(["化療穩定", t["name"]])
            elif "Recurrence" in t["stage"]:
                sources.extend([0, 3]); targets.extend([3, 4]); values.extend([1, 1]); labels.extend(["復發", t["name"]])
    fig = go.Figure(data=[go.Sankey(
        node = dict(pad = 30, thickness = 25, label = nodes, color = "#008080"),
        link = dict(source = sources, target = targets, value = values, label = labels, color = "rgba(0, 128, 128, 0.1)")
    )])
    fig.update_layout(height=400, margin=dict(l=10, r=10, t=20, b=20))
    return fig

t_ec, t_oc = st.tabs(["子宮內膜癌 (Endometrial)", "卵巢癌 (Ovarian)"])
with t_ec: st.plotly_chart(create_sankey("Endometrial"), use_container_width=True)
with t_oc: st.plotly_chart(create_sankey("Ovarian"), use_container_width=True)

# --- 4. 詳情卡片 ---
st.divider()
selected_name = st.selectbox("請選擇試驗名稱：", [t["name"] for t in TRIALS_DATA])
t = next(item for item in TRIALS_DATA if item["name"] == selected_name)

st.markdown(f"### 🧪 藥物機轉：{t['drug_name']}")
st.info(t['rationale'])

col1, col2 = st.columns(2)
with col1:
    st.markdown("#### 💉 給藥 Protocol")
    st.success(t['protocol'])
with col2:
    st.markdown("#### ✅ 入案條件 (Inclusion)")
    for inc in t['inclusion']: st.write(f"🔹 {inc}")
    st.markdown("#### ❌ 排除條件 (Exclusion)")
    for exc in t['exclusion']: st.write(f"🔸 {exc}")
