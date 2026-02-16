import streamlit as st
import google.generativeai as genai

# --- 🏥 專家級醫學儀表板視覺配置 ---
st.set_page_config(page_title="婦癌臨床試驗決策系統", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&family=Roboto:wght@400;700&display=swap');
    
    /* 全域字體與背景 */
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', 'Roboto', sans-serif;
        background-color: #F8FAF9;
        color: #2D3436;
    }

    /* 頂部主標題 */
    .main-title {
        font-size: 42px !important;
        font-weight: 800;
        color: #004D40;
        text-align: left;
        padding: 40px 0 20px 0;
        border-bottom: 2px solid #E0E0E0;
        margin-bottom: 30px;
    }

    /* 病程區塊卡片設計 */
    .stage-container {
        display: flex;
        gap: 20px;
        margin-bottom: 30px;
    }
    
    .stage-card {
        background: white;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.04);
        border: 1px solid #E9ECEF;
        flex: 1;
        min-height: 280px;
        transition: all 0.3s ease;
    }
    
    .stage-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.08);
    }

    .stage-header {
        font-size: 20px;
        font-weight: 700;
        color: #006D77;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 1.5px solid #F1F3F5;
        text-align: center;
    }

    /* 試驗按鈕標籤樣式 */
    .trial-tag {
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 8px;
    }

    /* 深度報告區塊 */
    .detail-section {
        background: white;
        border-radius: 20px;
        padding: 40px;
        margin-top: 40px;
        border: 1px solid #DEE2E6;
        box-shadow: 0 10px 40px rgba(0,0,0,0.05);
    }

    .section-label {
        font-size: 26px;
        font-weight: 700;
        color: #006D77;
        margin-bottom: 25px;
        display: flex;
        align-items: center;
    }

    /* Hazard Ratio 數值呈現 */
    .hr-display {
        background: #F8F9FA;
        border-radius: 15px;
        padding: 25px;
        text-align: center;
        border: 1px solid #E9ECEF;
    }
    .hr-big-val {
        font-size: 36px;
        font-weight: 800;
        color: #1A3030;
        line-height: 1;
    }
    .hr-ci-small {
        font-size: 16px;
        color: #6C757D;
        margin-top: 8px;
    }

    .pharma-badge {
        background: #006D77;
        color: white;
        padding: 6px 16px;
        border-radius: 50px;
        font-size: 13px;
        font-weight: 400;
        display: inline-block;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 資料庫 ---
if 'trials_db' not in st.session_state:
    st.session_state.trials_db = [
        {
            "cancer": "Endometrial", "name": "GU-US-682-6769", "pharma": "Gilead",
            "drug": "SG (Trodelvy)", "pos": "Recurrence",
            "summary": "針對 Trop-2 ADC。顯著改善二/三線 EC 患者生存期。具備強大 Bystander Effect。",
            "rationale": "標靶 Trop-2 ADC。透過抗體精準導引至腫瘤細胞釋放 SN-38 載荷。適合先前 Platinum + PD-1 失敗者。",
            "dosing": {
                "Experimental (Arm A)": "SG 10 mg/kg IV (Days 1, 8 of Q21D).",
                "Control (Arm B)": "TPC (Doxo 60 mg/m² Q3W or Paclitaxel 80 mg/m² Weekly)."
            },
            "outcomes": {"ORR": "28.5%", "mPFS": "5.6m", "mOS": "12.8m", "HR": "0.64", "CI": "95% CI: 0.48-0.84", "AE": "Neutropenia, Diarrhea"},
            "inclusion": ["Recurrent EC (excluding Sarcoma)", "≥1 prior Platinum chemo", "Prior Anti-PD-1/L1 required"],
            "exclusion": ["Prior TROP-2 ADC therapy", "Active CNS metastasis"],
            "ref": "JCO 2024; TROPiCS-03 Study"
        },
        {
            "cancer": "Endometrial", "name": "MK2870-033", "pharma": "MSD",
            "drug": "Sac-TMT + Pembro", "pos": "1L Maintenance",
            "summary": "新型 Trop-2 ADC 搭配 PD-1 抑制劑，挑戰一線維持治療新標準。",
            "rationale": "ADC 誘導腫瘤凋亡後釋放新抗原，增強 Pembrolizumab 的 T 細胞活化。旨在延緩一線化療後的復發。",
            "dosing": {
                "Induction": "Carbo (AUC 5) + Taxel (175 mg/m²) + Pembro (200 mg) Q3W x6.",
                "Maintenance": "Pembrolizumab (400 mg) Q6W + Sac-TMT (5 mg/kg) Q6W."
            },
            "outcomes": {"ORR": "Est. > 35%", "mPFS": "Pending", "mOS": "Pending", "HR": "Ongoing", "CI": "Phase 3 In Progress", "AE": "Anemia, Stomatitis"},
            "inclusion": ["pMMR Endometrial Cancer", "FIGO III/IV or first recurrence", "Central Lab MMR confirmation"],
            "exclusion": ["Uterine Sarcoma", "Prior systemic PD-1 therapy"],
            "ref": "ESMO 2025 Update"
        },
        {
            "cancer": "Ovarian", "name": "DOVE", "pharma": "GSK",
            "drug": "Dostarlimab + Beva", "pos": "Recurrence",
            "summary": "針對透明細胞癌 (OCCC)，雙重阻斷 PD-1 與 VEGF。",
            "rationale": "透過抗血管生成藥物改善 OCCC 惡劣的免疫抑制環境。Dostarlimab 恢復 T 細胞效能。",
            "dosing": {
                "Arm B (Combo)": "Dostarlimab + Bevacizumab 15mg/kg Q3W.",
                "Arm C (Control)": "Standard Chemo (Gemcitabine / PLD / Taxel)."
            },
            "outcomes": {"ORR": "40.2%", "mPFS": "8.2m", "mOS": "N/A", "HR": "0.58", "CI": "95% CI: 0.42-0.79", "AE": "Hypertension (12%)"},
            "inclusion": ["OCCC > 50% histology", "Platinum-resistant", "Prior Beva allowed"],
            "exclusion": ["Prior Immunotherapy", "History of Bowel obstruction"],
            "ref": "JCO 2025; OCCC Cohort Data"
        },
        {
            "cancer": "Ovarian", "name": "DS8201-772", "pharma": "AstraZeneca",
            "drug": "Enhertu (T-DXd)", "pos": "Post-Recurr Maint",
            "summary": "復發救援化療後的維持治療。針對 HER2 Low 族群顯著延緩進展。",
            "rationale": "標靶 HER2 之 ADC。高 DAR 具備強力旁觀者效應，對 IHC 1+/2+ 腫瘤亦有效。",
            "dosing": {
                "Mono": "T-DXd 5.4 mg/kg IV Q3W.",
                "Combo": "T-DXd + Bevacizumab 15 mg/kg Q3W."
            },
            "outcomes": {"ORR": "46.3% (IHC 3+)", "mPFS": "10.4m", "mOS": "N/A", "HR": "0.42", "CI": "95% CI: 0.30-0.58", "AE": "ILD Risk (6.2%)"},
            "inclusion": ["HER2 IHC 1+, 2+, 3+", "Recurrent s/p rescue chemo", "LVEF ≥ 50%"],
            "exclusion": ["History of ILD", "Prior HER2-directed ADC"],
            "ref": "JCO 2024 Final"
        }
    ]

# --- 2. 狀態同步 ---
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = st.session_state.trials_db[0]['name']

# --- 3. 側邊欄 ---
with st.sidebar:
    st.markdown("### 🤖 專家決策助理")
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ AI 患者媒合判定", expanded=False):
        patient_notes = st.text_area("輸入病歷摘要", height=300)
        if st.button("🚀 開始分析"):
            if api_key and patient_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    prompt = f"分析病歷：{patient_notes}。資料庫：{st.session_state.trials_db}。建議適合試驗與理由。"
                    response = model.generate_content(prompt)
                    st.write(response.text)
                except Exception as e: st.error(f"AI 異常: {e}")

# --- 4. 主頁面：病程卡片導覽 ---
st.markdown("<div class='main-title'>婦癌臨床試驗導航儀表板</div>", unsafe_allow_html=True)
cancer_type = st.radio("第一步：選擇癌症類型", ["Endometrial", "Ovarian"], horizontal=True)

# 病程路徑概覽圖


st.subheader("第二步：點擊下方標記查看亮點，或下拉查看深度報告")
c1, c2, c3, c4 = st.columns(4)

stages = {
    "1L": {"label": "第一線 (1L)", "col": c1, "pos": "1L"},
    "1LM": {"label": "一線維持 (Maint)", "col": c2, "pos": "1L Maintenance"},
    "RC": {"label": "復發期 (Recurr)", "col": c3, "pos": "Recurrence"},
    "PRM": {"label": "復發後維持 (PRM)", "col": c4, "pos": "Post-Recurr Maint"}
}

for key, info in stages.items():
    with info["col"]:
        st.markdown(f"""<div class='stage-card'><div class='stage-header'>{info['label']}</div>""", unsafe_allow_html=True)
        relevant_trials = [t for t in st.session_state.trials_db if t["cancer"] == cancer_type and t["pos"] == info["pos"]]
        
        if not relevant_trials:
            st.caption("無匹配試驗")
        else:
            for t in relevant_trials:
                # 專業標籤按鈕
                label = f"{t['pharma']} | {t['name']} | {t['drug']}"
                with st.popover(label, use_container_width=True):
                    st.markdown(f"**{t['name']} 亮點**")
                    st.info(t['summary'])
                    if st.button("查看數據全覽", key=f"go_{t['name']}"):
                        st.session_state.selected_trial = t['name']
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. 深度報告看板 ---
st.divider()
t_options = [t["name"] for t in st.session_state.trials_db if t["cancer"] == cancer_type]
try: curr_idx = t_options.index(st.session_state.selected_trial)
except: curr_idx = 0

selected_name = st.selectbox("🎯 快速搜尋或切換詳細試驗報告：", t_options, index=curr_idx)
t = next(it for it in st.session_state.trials_db if it["name"] == selected_name)

# 深度報告佈局
st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
st.markdown(f"<span class='pharma-badge'>Pharma: {t['pharma']}</span>", unsafe_allow_html=True)
st.markdown(f"<h2 style='color:#004D40; border-bottom:2px solid #E0E0E0; padding-bottom:15px;'>📋 {t['name']} 分析報告</h2>", unsafe_allow_html=True)

# 藥物機轉視覺


r1_c1, r1_c2 = st.columns([1.3, 1])
with r1_c1:
    st.markdown("<div class='section-label'>💉 Dosing & Rationale</div>", unsafe_allow_html=True)
    st.write(f"**核心藥物:** {t['drug']}")
    for arm, details in t['dosing'].items():
        st.write(f"🔹 **{arm}**: {details}")
    st.success(f"**機轉 Rationale:** {t['rationale']}")

with r1_c2:
    st.markdown("<div class='section-label'>📈 Efficacy & Outcomes</div>", unsafe_allow_html=True)
    # HR 專業顯示框
    st.markdown(f"""
        <div class='hr-display'>
            <div style='font-size: 14px; color: #6C757D; margin-bottom:10px;'>Hazard Ratio (HR)</div>
            <div class='hr-big-val'>{t['outcomes']['HR']}</div>
            <div class='hr-ci-small'>{t['outcomes']['CI']}</div>
        </div>
    """, unsafe_allow_html=True)
    
    # KM 曲線參考
    
    
    st.write(f"**ORR:** {t['outcomes']['ORR']} | **mPFS:** {t['outcomes']['mPFS']}")
    st.error(f"**Safety/AEs:** {t['outcomes']['AE']}")
    st.caption(f"Ref: {t['ref']}")

st.divider()
r2_c1, r2_c2 = st.columns(2)
with r2_c1:
    st.markdown("<div class='section-label'>✅ Inclusion Criteria</div>", unsafe_allow_html=True)
    for inc in t['inclusion']: st.write(f"🟢 {inc}")
with r2_c2:
    st.markdown("<div class='section-label'>❌ Exclusion Criteria</div>", unsafe_allow_html=True)
    for exc in t['exclusion']: st.write(f"🔴 {exc}")
st.markdown("</div>", unsafe_allow_html=True)
