import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床試驗導航系統 (2026 專家實證數據補完版) ---
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

# --- 1. 深度臨床資料庫 (已根據 ClinicalTrials.gov 全面更新) ---
if 'trials_db' not in st.session_state:
    st.session_state.trials_db = [
        # --- Ovarian Cancer ---
        {
            "cancer": "Ovarian", "name": "FRAmework-01 (LY4170156)", "pharma": "Eli Lilly (禮來)",
            "drug": "LY4170156 + Bevacizumab", "pos": "Recurrence",
            "summary": "針對 FRα 陽性患者之 Phase 3 全球隨機對照試驗。分為 Part A (PROC) 與 Part B (PSOC)。",
            "rationale": "標靶 Folate Receptor alpha (FRα) 之 ADC。與 Bevacizumab 聯用可透過抗血管生成協同效應提升 Payload 之滲透與療效，特別針對 PARPi 耐藥後患者。",
            "dosing": {
                "Experimental Arm (Part A/B)": "LY4170156 (3 mg/kg IV) + Bevacizumab (15 mg/kg IV) Q3W (每 21 天一個週期)。",
                "Control Arm (PROC)": "TPC (Paclitaxel, PLD, Gemcitabine, or Topotecan) 或 Mirvetuximab (MIRV)。",
                "Control Arm (PSOC)": "Platinum-based doublet (如 Carbo/Taxel) 併用 Bevacizumab。"
            },
            "outcomes": {"ORR": "Ph 1/2: ~35-40%", "mPFS": "主要評估指標", "mOS": "次要評估指標", "HR": "Recruiting", "CI": "NCT06536348", "AE": "Proteinuria, Hypertension, ILD"},
            "inclusion": [
                "18 歲以上，病理證實為 High-grade Serous 或 Carcinosarcoma 之卵巢、輸卵管或原發性腹膜癌。",
                "腫瘤檢體經中央實驗室確認為 FRα Expression Positive。",
                "Part A (PROC): 最後一劑鉑類後 ≤ 6 個月內復發；曾接受過 1-3 線全身治療。",
                "Part B (PSOC): 最後一劑鉑類後 > 6 個月復發；曾接受 PARP inhibitor 治療且具獲得性耐藥或不適用者。",
                "ECOG Performance Status 為 0 或 1。",
                "具備 RECIST v1.1 標準下之可測量病灶 (Measurable Disease)。"
            ],
            "exclusion": [
                "曾使用過帶有 Topoisomerase I 抑制劑 Payload 之 ADC 藥物 (如 Enhertu)。",
                "曾針對 Part B 使用過 FRα-targeted ADCs (如 MIRV)。",
                "曾患有非感染性 Interstitial Lung Disease (ILD) 或需類固醇治療之肺炎病史。",
                "具有臨床顯著的蛋白尿 (24 小時尿蛋白 ≥2g 或 UPCR ≥2.0)。",
                "具有活動性 CNS 轉移或軟腦膜疾病 (Leptomeningeal disease)。",
                "具有未控制的高血壓或不穩定之門靜脈高壓病史。"
            ],
            "ref": "Source: NCT06536348 (ClinicalTrials.gov)"
        },
        {
            "cancer": "Ovarian", "name": "REJOICE-Ovarian01", "pharma": "Daiichi Sankyo",
            "drug": "R-DXd (Raludotatug Deruxtecan)", "pos": "Recurrence",
            "summary": "針對 CDH6 高表達之 PROC 患者的 Phase 3 試驗。挑戰目前鉑類抗藥性之後線治療標準。",
            "rationale": "標靶 Cadherin-6 (CDH6) ADC，搭載 DXd Payload。具備強大的 Bystander Effect，可克服 PROC 腫瘤的高度異質性。",
            "dosing": {
                "Experimental Arm": "R-DXd (Raludotatug Deruxtecan) 5.6 mg/kg IV Q3W。",
                "Control Arm": "Investigator's Choice 化療 (Paclitaxel, PLD, or Topotecan)。"
            },
            "outcomes": {"ORR": "46.0% (Ph 1 Update)", "mPFS": "7.1 months", "mOS": "N/A", "HR": "Phase 3 Ongoing", "CI": "NCT06161025", "AE": "Nausea, ILD Risk, Neutropenia"},
            "inclusion": [
                "High-grade Serous 或 Endometrioid 卵巢、腹膜或輸卵管癌。",
                "鉑類抗藥性 (Platinum-resistant, PROC) 定義：1線鉑類後 90-180 天內惡化，或 2-4 線後 ≤180 天惡化。",
                "已接受過至少 1 線且不超過 3-4 線系統性治療。",
                "需提供腫瘤檢體以評估 CDH6 表達量作為分層依據。",
                "除非有禁忌症，否則必須曾接受過 Bevacizumab 治療。"
            ],
            "exclusion": [
                "排除 Clear cell, Mucinous, Sarcomatous 或 Low-grade 腫瘤。",
                "曾患有需類固醇治療的（非感染性）ILD/肺臟炎，或目前疑似患有 ILD。",
                "基線時已存在 ≥ Grade 2 的周邊神經病變 (Peripheral Neuropathy)。",
                "心臟射出分率 (LVEF) < 50%。"
            ],
            "ref": "Source: NCT06161025; Daiichi Sankyo SIV 資料"
        },
        {
            "cancer": "Ovarian", "name": "TroFuse-021", "pharma": "MSD (Merck)",
            "drug": "Sac-TMT (MK-2870)", "pos": "1L Maintenance",
            "summary": "新診斷卵巢癌一線化療後之維持治療試驗。針對 pHRD 患者探討 ADC 之定位。",
            "rationale": "標靶 Trop-2 ADC 與 Bevacizumab 聯用。旨在提供不適用 PARPi 之 pHRD 患者更強效的維持方案。",
            "dosing": {
                "Arm 1": "Sac-TMT 單藥維持 (Q2W or Q3W)。",
                "Arm 2": "Sac-TMT + Bevacizumab 15 mg/kg Q3W。",
                "Arm 3": "Standard of Care (觀察或單用 Bevacizumab)。"
            },
            "outcomes": {"ORR": "Est. 40% (pHRD)", "mPFS": "Phase 3 招募中", "mOS": "TBD", "HR": "Ongoing", "CI": "NCT06241729", "AE": "Stomatitis, Diarrhea, Anemia"},
            "inclusion": [
                "新診斷之 FIGO Stage III 或 IV 卵巢、腹膜或輸卵管癌。",
                "HRD 狀態確認為陰性 (HRD negative / pHRD)。",
                "剛完成第一線含鉑化療並達到臨床緩解 (CR 或 PR) 後的維持治療。",
                "需提供檢體進行 Trop-2 表達量與 HRD 狀態之確認。"
            ],
            "exclusion": [
                "具備 BRCA 突變或 HRD 陽性者（優先使用 PARPi）。",
                "具有嚴重的炎症性腸道疾病 (IBD) 或嚴重腹瀉病史。",
                "曾接受過針對 Trop-2 之 ADC 治療。",
                "活動性自體免疫疾病需要系統性治療者。"
            ],
            "ref": "Source: NCT06241729; ENGOT-ov85"
        },
        {
            "cancer": "Ovarian", "name": "DOVE (APGOT-OV07)", "pharma": "GSK",
            "drug": "Dostarlimab + Bevacizumab", "pos": "Recurrence",
            "summary": "專屬透明細胞癌 (OCCC) 患者。探討免疫檢查點抑制劑與抗血管生成藥物之協同作用。",
            "rationale": "OCCC 常見免疫抑制微環境。Dostarlimab (Anti-PD-1) 配合 Bevacizumab 旨在改善微環境並引發長期應答。",
            "dosing": {
                "Combo Arm": "Dostarlimab 500 mg Q3W (4劑) 接續 1000 mg Q6W + Bevacizumab 15 mg/kg Q3W。",
                "Control Arm": "單藥化療 (Gemcitabine, PLD, or Taxel)。"
            },
            "outcomes": {"ORR": "40.2% (OCCC)", "mPFS": "8.2 months", "mOS": "N/A", "HR": "0.58", "CI": "95% CI: 0.42-0.79", "AE": "Hypertension, Fatigue"},
            "inclusion": [
                "組織學證實為透明細胞癌 (OCCC) 佔比 > 50%。",
                "鉑類抗藥性 (Platinum-resistant)：最後一劑鉑類後 12 個月內復發。",
                "先前系統性治療線數不超過 5 線。",
                "ECOG Performance Status 為 0 或 1。"
            ],
            "exclusion": [
                "先前接受過 PD-1/PD-L1 或 CTLA-4 抑制劑之免疫治療。",
                "具有臨床顯著的腸阻塞病史或活動性消化道出血風險。",
                "活動性自體免疫疾病或需長期使用免疫抑制劑之狀況。"
            ],
            "ref": "Source: NCT06023862; JCO 2025"
        },
        {
            "cancer": "Ovarian", "name": "DS8201-772 (Enhertu)", "pharma": "AstraZeneca / DS",
            "drug": "Trastuzumab Deruxtecan (T-DXd)", "pos": "Post-Recurr Maint",
            "summary": "針對 HER2 表現之復發性卵巢癌維持治療。挑戰 PARPi 以外的精準維持方案。",
            "rationale": "標靶 HER2 ADC。透過超高 DAR (8) 與強大的旁觀者效應，對 HER2 低表達 (IHC 1+/2+) 腫瘤亦有顯著療效。",
            "dosing": {
                "Standard Arm": "T-DXd 5.4 mg/kg IV Q3W。",
                "Combination Arm": "T-DXd 5.4 mg/kg + Bevacizumab 15 mg/kg Q3W。"
            },
            "outcomes": {"ORR": "46.3% (IHC 3+)", "mPFS": "10.4 months", "mOS": "N/A", "HR": "0.42", "CI": "95% CI: 0.30-0.58", "AE": "ILD/Pneumonitis, Nausea"},
            "inclusion": [
                "HER2 表達 (IHC 1+, 2+, or 3+) 經中央實驗室確認。",
                "BRCA Wild-type 或 HRD 陰性，且研究者判定不適合使用 PARPi 者。",
                "復發後經救援化療 (Platinum-based) 達到穩定 (Non-PD) 後之維持階段。"
            ],
            "exclusion": [
                "曾患有需類固醇治療的 ILD 或活動性肺炎病史。",
                "左心室射出分率 (LVEF) < 50% 或具有顯著心臟病史。",
                "先前接受過任何針對 HER2 之 ADC 或標靶治療。"
            ],
            "ref": "Source: JCO 2024; DESTINY-PanTumor 02"
        },
        # --- Endometrial Cancer ---
        {
            "cancer": "Endometrial", "name": "GU-US-682-6769 (TROPiCS-03)", "pharma": "Gilead",
            "drug": "Sacituzumab Govitecan (Trodelvy)", "pos": "Recurrence",
            "summary": "針對 Trop-2 高表達之進展性子宮內膜癌。提供鉑類及免疫治療失敗後的新選擇。",
            "rationale": "標靶 Trop-2 ADC。利用 SN-38 載荷引發 DNA 損傷，並透過 Bystander Effect 殺傷 Trop-2 低表達之鄰近癌細胞。",
            "dosing": {
                "Experimental Arm": "SG 10 mg/kg IV on Days 1 and 8 of each 21-day cycle (Q21D)。",
                "Control Arm": "TPC (Doxorubicin 60 mg/m² or Paclitaxel 80 mg/m²)。"
            },
            "outcomes": {"ORR": "28.5% (Phase 2)", "mPFS": "5.6m", "mOS": "12.8m", "HR": "0.64", "CI": "95% CI: 0.48-0.84", "AE": "Neutropenia, Diarrhea"},
            "inclusion": [
                "進展性或復發性子宮內膜癌 (不含肉瘤)。",
                "曾接受過至少一線含鉑類化療，且必須曾接受過 Anti-PD-1/L1 免疫治療。",
                "ECOG Performance Status 為 0 或 1。",
                "骨髓功能良好 (ANC ≥1500, Platelets ≥100,000)。"
            ],
            "exclusion": [
                "先前曾接受過針對 Trop-2 之 ADC 治療。",
                "具有活動性 CNS 轉移或嚴重未控制之共病。",
                "具有慢性炎症性腸道疾病 (IBD) 或需治療之嚴重腹瀉。"
            ],
            "ref": "Source: NCT03964727; JCO 2024"
        },
        {
            "cancer": "Endometrial", "name": "MK2870-033 (TroFuse-033)", "pharma": "MSD",
            "drug": "Sac-TMT (MK-2870) + Pembrolizumab", "pos": "1L Maintenance",
            "summary": "一線維持治療。針對 pMMR 子宮內膜癌，結合 Trop-2 ADC 與 Pembrolizumab。",
            "rationale": "ADC 誘導腫瘤凋亡後釋放新抗原，旨在協同提升免疫檢查點抑制劑之 T 細胞活化與應答。",
            "dosing": {
                "Induction Phase": "Carboplatin + Paclitaxel + Pembrolizumab Q3W x 6 cycles。",
                "Maintenance Phase": "Pembrolizumab (400 mg) Q6W + Sac-TMT (5 mg/kg) Q6W。"
            },
            "outcomes": {"ORR": "Est. > 35% in Ph 2", "mPFS": "Phase 3 Ongoing", "mOS": "TBD", "HR": "TBD", "CI": "NCT06132958", "AE": "Anemia, Stomatitis, Fatigue"},
            "inclusion": [
                "Mismatch Repair Proficient (pMMR) 之子宮內膜癌。",
                "新診斷之 FIGO Stage III/IV 或初次復發且未曾治療者。",
                "必須提供腫瘤檢體送往中央實驗室進行 MMR 狀態確認。"
            ],
            "exclusion": [
                "組織學為子宮肉瘤 (Uterine Sarcoma)。",
                "先前曾針對晚期病灶接受過任何系統性 PD-1/L1 治療。",
                "具有活動性自體免疫疾病或需長期免疫抑制劑治療者。"
            ],
            "ref": "Source: ESMO 2025; MSD TroFuse-033 Design"
        }
    ]

# --- 2. 狀態同步 ---
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = st.session_state.trials_db[0]['name']

# --- 3. 側邊欄：AI 專家決策助理 ---
with st.sidebar:
    st.markdown("<h2 style='color: #6A1B9A;'>🤖 AI 專家助理</h2>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 患者條件媒合分析 (NCT 同步)", expanded=False):
        patient_notes = st.text_area("輸入病歷摘要", height=250, placeholder="例：62y/o OCCC, PROC, s/p 3L lines, ECOG 1...")
        if st.button("🚀 開始分析"):
            if api_key and patient_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    prompt = f"你是一位權威婦癌專家。請分析病歷：{patient_notes}。與資料庫中的 7 個試驗進行比對：{st.session_state.trials_db}。請建議適合試驗、說明醫學理由，並強調該試驗在 ClinicalTrials.gov 的收案重點。"
                    response = model.generate_content(prompt)
                    st.write(response.text)
                except Exception as e: st.error(f"AI 服務異常: {e}")

# --- 4. 主頁面：區塊導航 ---
st.markdown("<div class='main-title'>婦癌臨床試驗導航地圖 (Expert View)</div>", unsafe_allow_html=True)

# 顯示病程路徑參考圖


cancer_type = st.radio("第一步：選擇癌症類型", ["Ovarian", "Endometrial"], horizontal=True)

st.subheader("第二步：點擊下方標記查看 SIV / NCT 核心重點")
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
        if not relevant_trials: st.caption("目前無匹配試驗")
        else:
            for t in relevant_trials:
                label = f"📍 {t['pharma']} | {t['name']} | {t['drug']}"
                with st.popover(label, use_container_width=True):
                    st.markdown(f"### ✨ {t['name']} 亮點摘要")
                    st.info(t['summary'])
                    if st.button("📊 開啟深度分析報告", key=f"go_{t['name']}"):
                        st.session_state.selected_trial = t['name']
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. 深度分析報告看板 ---
st.divider()
t_options = [t["name"] for t in st.session_state.trials_db if t["cancer"] == cancer_type]
try: curr_idx = t_options.index(st.session_state.selected_trial)
except: curr_idx = 0

selected_name = st.selectbox("🎯 快速搜尋詳細試驗報告：", t_options, index=curr_idx)
t = next(it for it in st.session_state.trials_db if it["name"] == selected_name)

st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
st.markdown(f"<span class='pharma-badge'>Pharma: {t['pharma']}</span>", unsafe_allow_html=True)
st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #E0E0E0; padding-bottom:15px; font-weight:900;'>📋 {t['name']} 深度分析報告</h2>", unsafe_allow_html=True)

# 藥物機轉視覺


r1_c1, r1_c2 = st.columns([1.3, 1])
with r1_c1:
    st.markdown("<div class='info-box-blue'><b>💉 Dosing Protocol & Rationale</b></div>", unsafe_allow_html=True)
    st.write(f"**核心藥物:** {t['drug']}")
    for arm, details in t['dosing'].items(): st.write(f"🔹 **{arm}**: {details}")
    st.markdown("---")
    st.success(f"**機轉 Rationale:** {t['rationale']}")

with r1_c2:
    st.markdown("<div class='info-box-gold'><b>📈 Efficacy & Outcomes</b></div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class='hr-display'>
            <div style='font-size: 16px; color: #795548; font-weight:700; margin-bottom:8px;'>Hazard Ratio (HR) / NCT ID</div>
            <div class='hr-big-val'>{t['outcomes']['HR']}</div>
            <div class='hr-ci'>{t['outcomes']['CI']}</div>
        </div>
    """, unsafe_allow_html=True)
    st.write(f"**ORR:** {t['outcomes']['ORR']} | **mPFS:** {t['outcomes']['mPFS']}")
    st.error(f"**Safety / AE:** {t['outcomes']['AE']}")
    

st.divider()
r2_c1, r2_c2 = st.columns(2)
with r2_c1:
    st.markdown("<div class='inc-box'><b>✅ Inclusion Criteria (納入標準)</b></div>", unsafe_allow_html=True)
    for inc in t['inclusion']: st.write(f"• **{inc}**")
with r2_c2:
    st.markdown("<div class='exc-box'><b>❌ Exclusion Criteria (排除標準)</b></div>", unsafe_allow_html=True)
    for exc in t['exclusion']: st.write(f"• **{exc}**")
st.markdown("</div>", unsafe_allow_html=True)
