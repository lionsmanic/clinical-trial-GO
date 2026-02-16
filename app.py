import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床試驗專家導航系統 (完整全集版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=Roboto:wght@400;700;900&display=swap');
    
    /* === 全域 UI 高清晰度設定 === */
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', 'Roboto', sans-serif;
        background-color: #F0F4F8;
        color: #1A1A1A;
        font-size: 21px !important;
        line-height: 1.6;
    }

    /* 主標題 */
    .main-title {
        font-size: 48px !important; font-weight: 900; color: #005662;
        padding: 25px 0 15px 0; border-bottom: 4px solid #4DB6AC;
        margin-bottom: 25px;
    }

    /* === 區塊卡片視覺 === */
    .stage-card-base {
        border-radius: 16px; padding: 15px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.08);
        border: 2.5px solid transparent;
        min-height: 180px; background: white;
        transition: all 0.2s ease;
    }
    
    .stage-header {
        font-size: 26px !important; font-weight: 900; color: white;
        margin: -15px -15px 15px -15px; padding: 12px;
        border-radius: 14px 14px 0 0; text-align: center;
    }

    /* 配色編碼 */
    .card-1l { border-color: #66BB6A; }
    .header-1l { background: linear-gradient(135deg, #43A047, #2E7D32); }
    .card-1lm { border-color: #29B6F6; }
    .header-1lm { background: linear-gradient(135deg, #0288D1, #01579B); }
    .card-rc { border-color: #FFA726; }
    .header-rc { background: linear-gradient(135deg, #FB8C00, #EF6C00); }
    .card-prm { border-color: #AB47BC; }
    .header-prm { background: linear-gradient(135deg, #8E24AA, #6A1B9A); }

    /* === 深度分析看板 === */
    .detail-section {
        background: white; border-radius: 20px; padding: 40px;
        margin-top: 35px; box-shadow: 0 12px 40px rgba(0,0,0,0.1);
        border: 1px solid #CFD8DC;
    }

    .info-box-blue {
        background: #E3F2FD; border-radius: 15px; padding: 25px;
        border-left: 8px solid #1976D2; color: #0D47A1;
    }
    .info-box-gold {
        background: #FFF8E1; border-radius: 15px; padding: 25px;
        border-left: 8px solid #FBC02D; color: #5F4B09;
    }
    
    /* Hazard Ratio 核心指標極大化 */
    .hr-display {
        background: white; border-radius: 15px; padding: 20px;
        text-align: center; border: 3px solid #FFE082;
    }
    .hr-big-val {
        font-family: 'Roboto', sans-serif; font-size: 50px !important; 
        font-weight: 900; color: #D84315; line-height: 1;
    }
    .hr-ci { font-size: 20px !important; color: #5D4037; margin-top: 10px; font-weight: 700; }

    .pharma-badge { 
        background: #004D40; color: white; padding: 6px 18px; 
        border-radius: 50px; font-size: 14px; font-weight: 700;
        display: inline-block; margin-bottom: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 完整臨床資料庫 (已救回舊試驗並加入新 SIV 試驗) ---
if 'trials_db' not in st.session_state:
    st.session_state.trials_db = [
        # --- Ovarian Cancer ---
        {
            "cancer": "Ovarian", "name": "REJOICE-Ovarian01", "pharma": "Daiichi Sankyo",
            "drug": "R-DXd (Raludotatug Deruxtecan)", "pos": "Recurrence",
            "summary": "針對 CDH6 標靶 ADC，專攻鉑類抗藥性 (PROC) 患者。",
            "rationale": "標靶 CDH6 ADC。具備強力 Bystander Effect，特別適合 PROC 後線治療。",
            "dosing": {"Experimental": "R-DXd 5.6 mg/kg IV Q3W.", "Control": "TPC (Paclitaxel/PLD/Topotecan)"},
            "outcomes": {"ORR": "46.0%", "mPFS": "7.1m", "mOS": "N/A", "HR": "Phase 3", "CI": "NCT06161025", "AE": "ILD Risk, Nausea"},
            "inclusion": ["PROC 卵巢癌", "曾接受 1-4 線治療", "需曾用過 Bevacizumab"],
            "exclusion": ["Low-grade 腫瘤", "ILD/肺臟炎病史"],
            "ref": "JCO 2024; SIV Topic 1"
        },
        {
            "cancer": "Ovarian", "name": "TroFuse-021", "pharma": "MSD",
            "drug": "Sac-TMT (MK-2870)", "pos": "1L Maintenance",
            "summary": "一線維持治療。針對 pHRD 患者，結合 Trop-2 ADC 與 Beva。",
            "rationale": "針對 Trop-2 高表達之 pHRD 患者，旨在優化一線化療後的維持方案。",
            "dosing": {"Arm 1": "Sac-TMT Mono", "Arm 2": "Sac-TMT + Beva", "Arm 3": "SoC (Observation/Beva)"},
            "outcomes": {"ORR": "Est. 40%", "mPFS": "TBD", "mOS": "TBD", "HR": "Ongoing", "CI": "NCT06241729", "AE": "Diarrhea, Stomatitis"},
            "inclusion": ["新診斷 FIGO III/IV", "HRD Negative (pHRD)", "1L Chemo CR/PR"],
            "exclusion": ["HRD Positive", "嚴重腸胃道疾病史"],
            "ref": "ENGOT-ov85; SIV Topic 2"
        },
        {
            "cancer": "Ovarian", "name": "DOVE (APGOT-OV07)", "pharma": "GSK",
            "drug": "Dostarlimab + Beva", "pos": "Recurrence",
            "summary": "針對透明細胞癌 (OCCC)，雙重阻斷 PD-1 與 VEGF。",
            "rationale": "透過抗血管生成藥物改善 OCCC 免疫抑制環境。",
            "dosing": {"Arm B": "Dostarlimab + Beva 15mg/kg Q3W", "Arm C": "Standard Chemo"},
            "outcomes": {"ORR": "40.2%", "mPFS": "8.2m", "mOS": "N/A", "HR": "0.58", "CI": "95% CI: 0.42-0.79", "AE": "Hypertension"},
            "inclusion": ["OCCC > 50%", "Platinum-resistant", "Up to 5 prior lines"],
            "exclusion": ["Prior Immunotherapy", "Bowel obstruction"],
            "ref": "JCO 2025 Data"
        },
        {
            "cancer": "Ovarian", "name": "DS8201-772", "pharma": "AstraZeneca",
            "drug": "Enhertu (T-DXd)", "pos": "Post-Recurr Maint",
            "summary": "復發救援化療後的維持治療。針對 HER2 Low 族群。",
            "rationale": "標靶 HER2 ADC。具備強力旁觀者效應。",
            "dosing": {"Mono": "T-DXd 5.4 mg/kg IV Q3W", "Combo": "T-DXd + Beva 15 mg/kg Q3W"},
            "outcomes": {"ORR": "46.3% (IHC 3+)", "mPFS": "10.4m", "mOS": "N/A", "HR": "0.42", "CI": "95% CI: 0.30-0.58", "AE": "ILD Risk"},
            "inclusion": ["HER2 IHC 1+/2+/3+", "Recurrent s/p rescue chemo"],
            "exclusion": ["ILD 病史", "LVEF < 50%"],
            "ref": "JCO 2024 Final"
        },
        # --- Endometrial Cancer ---
        {
            "cancer": "Endometrial", "name": "GU-US-682-6769", "pharma": "Gilead",
            "drug": "SG (Trodelvy)", "pos": "Recurrence",
            "summary": "針對 Trop-2 ADC。用於二/三線 EC 患者。",
            "rationale": "釋放 SN-38 載荷引發 DNA 損傷。適合先前 Platinum + PD-1 失敗者。",
            "dosing": {"Arm A": "SG 10 mg/kg IV (D1, D8)", "Arm B": "TPC weekly"},
            "outcomes": {"ORR": "28.5%", "mPFS": "5.6m", "mOS": "12.8m", "HR": "0.64", "CI": "95% CI: 0.48-0.84", "AE": "Neutropenia"},
            "inclusion": ["Recurrent EC", "≥1 prior Platinum line", "Prior Anti-PD-1/L1 required"],
            "exclusion": ["Prior Trop-2 ADC", "Active CNS 轉移"],
            "ref": "JCO 2024"
        },
        {
            "cancer": "Endometrial", "name": "MK2870-033", "pharma": "MSD",
            "drug": "Sac-TMT + Pembro", "pos": "1L Maintenance",
            "summary": "新型 ADC 聯手 PD-1。挑戰一線維持新標準。",
            "rationale": "ADC 誘導凋亡後釋放新抗原，增強免疫活化。",
            "dosing": {"Induction": "Carbo + Taxel + Pembro", "Maintenance": "Pembro + Sac-TMT Q6W"},
            "outcomes": {"ORR": "Est. > 35%", "mPFS": "Pending", "mOS": "Pending", "HR": "Ongoing", "CI": "Phase 3", "AE": "Stomatitis"},
            "inclusion": ["pMMR EC", "FIGO III/IV", "1L CR/PR"],
            "exclusion": ["Sarcoma", "Prior PD-1"],
            "ref": "ESMO 2025"
        }
    ]

# --- 2. 狀態管理 ---
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = st.session_state.trials_db[0]['name']

# --- 3. 側邊欄 ---
with st.sidebar:
    st.markdown("<h2 style='color: #6A1B9A;'>🤖 AI 專家助理</h2>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 患者條件媒合分析", expanded=False):
        patient_notes = st.text_area("輸入病歷摘要", height=250)
        if st.button("🚀 開始分析"):
            if api_key and patient_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    prompt = f"分析病歷：{patient_notes}。資料庫：{st.session_state.trials_db}。建議適合試驗與理由。"
                    response = model.generate_content(prompt)
                    st.write(response.text)
                except Exception as e: st.error(f"AI 異常: {e}")

# --- 4. 主頁面：區塊導航 ---
st.markdown("<div class='main-title'>婦癌臨床試驗專家導航地圖</div>", unsafe_allow_html=True)
cancer_type = st.radio("第一步：選擇癌症類型", ["Ovarian", "Endometrial"], horizontal=True)

st.subheader("第二步：點擊下方階段標記按鈕查看摘要")
c1, c2, c3, c4 = st.columns(4)

stages = {
    "1L": {"label": "第一線 (1L)", "col": c1, "pos": "1L", "css": "1l"},
    "1LM": {"label": "一線維持 (Maint)", "col": c2, "pos": "1L Maintenance", "css": "1lm"},
    "RC": {"label": "復發期 (Recurr)", "col": c3, "pos": "Recurrence", "css": "rc"},
    "PRM": {"label": "復發後維持 (PRM)", "col": c4, "pos": "Post-Recurr Maint", "css": "prm"}
}

for key, info in stages.items():
    with info["col"]:
        st.markdown(f"""<div class='stage-card-base card-{info['css']}'><div class='stage-header header-{info['css']}'>{info['label']}</div>""", unsafe_allow_html=True)
        relevant_trials = [t for t in st.session_state.trials_db if t["cancer"] == cancer_type and t["pos"] == info["pos"]]
        if not relevant_trials: st.caption("無匹配試驗")
        else:
            for t in relevant_trials:
                label = f"📍 {t['pharma']} | {t['name']} | {t['drug']}"
                with st.popover(label, use_container_width=True):
                    st.markdown(f"### ✨ {t['name']} 亮點")
                    st.info(t['summary'])
                    if st.button("📊 開啟深度報告", key=f"go_{t['name']}"):
                        st.session_state.selected_trial = t['name']
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. 深度分析看板 ---
st.divider()
t_options = [t["name"] for t in st.session_state.trials_db if t["cancer"] == cancer_type]
try: curr_idx = t_options.index(st.session_state.selected_trial)
except: curr_idx = 0

selected_name = st.selectbox("🎯 快速搜尋詳細試驗報告：", t_options, index=curr_idx)
t = next(it for it in st.session_state.trials_db if it["name"] == selected_name)

st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
st.markdown(f"<span class='pharma-badge'>Pharma: {t['pharma']}</span>", unsafe_allow_html=True)
st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #E0E0E0; padding-bottom:15px; font-weight:900;'>📋 {t['name']} 深度分析報告</h2>", unsafe_allow_html=True)



r1_c1, r1_c2 = st.columns([1.3, 1])
with r1_c1:
    st.markdown("<div class='info-box-blue'><b>💉 Dosing Protocol & Rationale</b></div>", unsafe_allow_html=True)
    st.write(f"**核心藥物:** {t['drug']}")
    for arm, details in t['dosing'].items(): st.write(f"🔹 **{arm}**: {details}")
    st.success(f"**機轉 Rationale:** {t['rationale']}")

with r1_c2:
    st.markdown("<div class='info-box-gold'><b>📈 Efficacy & Outcomes</b></div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class='hr-display'>
            <div style='font-size: 16px; color: #795548; font-weight:700; margin-bottom:8px;'>Hazard Ratio (HR) / NCT</div>
            <div class='hr-big-val'>{t['outcomes']['HR']}</div>
            <div class='hr-ci'>{t['outcomes']['CI']}</div>
        </div>
    """, unsafe_allow_html=True)
    st.write(f"**ORR:** {t['outcomes']['ORR']} | **mPFS:** {t['outcomes']['mPFS']}")
    st.error(f"**Safety / AE:** {t['outcomes']['AE']}")
    

st.divider()
r2_c1, r2_c2 = st.columns(2)
with r2_c1:
    st.markdown("<div class='inc-box'><b>✅ Inclusion Criteria</b></div>", unsafe_allow_html=True)
    for inc in t['inclusion']: st.write(f"• **{inc}**")
with r2_c2:
    st.markdown("<div class='exc-box'><b>❌ Exclusion Criteria</b></div>", unsafe_allow_html=True)
    for exc in t['exclusion']: st.write(f"• **{exc}**")
st.markdown("</div>", unsafe_allow_html=True)
