import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床導航系統 (2026 專家實證數據補完版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=Roboto:wght@400;700;900&display=swap');
    
    /* === 全域字體與背景高度緊縮 === */
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', 'Roboto', sans-serif;
        background-color: #F0F4F7;
        color: #1A1A1A;
        font-size: 20px !important;
        line-height: 1.35;
    }

    .main-title {
        font-size: 40px !important; font-weight: 900; color: #004D40;
        padding: 15px 0 5px 0; border-bottom: 3px solid #4DB6AC;
        margin-bottom: 15px;
    }

    /* === 大階段方塊：緊湊設計 === */
    .big-stage-card {
        border-radius: 12px; padding: 0px; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        border: 2px solid transparent;
        background: white; margin-bottom: 8px; overflow: hidden;
    }
    .big-stage-header {
        font-size: 21px !important; font-weight: 900; color: white;
        padding: 8px; text-align: center;
    }

    /* === 子區塊 (Standard of Care) === */
    .sub-block {
        margin: 6px; padding: 8px;
        border-radius: 8px; background: #F8F9FA;
        border-left: 5px solid #607D8B;
    }
    .sub-block-title {
        font-size: 15px; font-weight: 900; color: #455A64;
        margin-bottom: 3px; border-bottom: 1px solid #CFD8DC; padding-bottom: 2px;
    }
    .sub-block-content {
        font-size: 16px; color: #263238; font-weight: 500; line-height: 1.25;
        margin-bottom: 5px;
    }

    /* 階段配色 */
    .card-p-tx { border-color: #43A047; }
    .header-p-tx { background: linear-gradient(135deg, #66BB6A, #43A047); }
    .card-p-mt { border-color: #0288D1; }
    .header-p-mt { background: linear-gradient(135deg, #29B6F6, #0288D1); }
    .card-r-tx { border-color: #FB8C00; }
    .header-r-tx { background: linear-gradient(135deg, #FFB74D, #F57C00); }
    .card-r-mt { border-color: #8E24AA; }
    .header-r-mt { background: linear-gradient(135deg, #BA68C8, #7B1FA2); }

    /* === 深度數據呈現 === */
    .detail-section {
        background: white; border-radius: 18px; padding: 30px;
        margin-top: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        border: 1px solid #CFD8DC;
    }
    .hr-big-val {
        font-family: 'Roboto', sans-serif; font-size: 48px !important; 
        font-weight: 900; color: #D84315; line-height: 1;
    }
    .pharma-badge { 
        background: #004D40; color: white; padding: 4px 15px; 
        border-radius: 50px; font-size: 13px; font-weight: 700;
        display: inline-block; margin-bottom: 8px;
    }

    /* Popover 按鈕字體與緊縮 */
    .stPopover button { 
        font-weight: 700 !important; font-size: 14px !important; 
        border-radius: 6px !important; margin-top: 2px !important;
        padding: 1px 6px !important; width: 100% !important; text-align: left !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 指引大綱：卵巢癌一線維持邏輯細分 ---
guidelines_nested = {
    "Ovarian": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [{"title": "Surgery + Chemo", "content": "PDS 或 NACT/IDS + Carboplatin/Paclitaxel x6 ± Bevacizumab"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "BRCA mutated", "content": "1. Olaparib 單藥維持 (CR/PR後)<br>2. 曾用Bev且HRD+: Olaparib + Bev 併用維持"},
            {"title": "HRD positive (BRCA wt)", "content": "1. 曾用Bev: Olaparib + Bev 併用維持<br>2. 未用Bev: Niraparib 單藥維持"},
            {"title": "HRD negative / Unknown", "content": "曾用Bev者續用；未用者多觀察，或視風險評估選用 Niraparib"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "PSOC (PFI > 6m)", "content": "鉑類雙藥化療 (Platinum doublet) ± Bevacizumab"},
            {"title": "PROC (PFI < 6m)", "content": "單藥化療 ± Bev 或 Elahere (FRα+)"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Platinum Sensitive Maint", "content": "對含鉑反應後，視前線用藥史選用 PARPi 維持"}]}
    ],
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [{"title": "Advanced/Metastatic", "content": "Chemo + Immunotherapy (Pembro/Dostarlimab)"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "IO Maintenance", "content": "延續一線使用之免疫藥物持續維持至 PD"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "pMMR / MSS", "content": "Pembrolizumab + Lenvatinib"}, {"title": "dMMR / MSI-H", "content": "PD-1 抑制劑單藥治療"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Tx", "content": "持續給藥直到不可耐受或疾病進展"}]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [{"title": "CCRT / Metastatic", "content": "CCRT 或 Pembro + Chemo ± Bev (CPS≥1)"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Metastatic 1L", "content": "轉移性一線後延續 Pembro 維持"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "2L / 3L Therapy", "content": "Tivdak (Tisotumab vedotin) 或 Cemiplimab"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Tx", "content": "同一線有效治療持續給藥"}]}
    ]
}

# --- 2. 深度臨床試驗資料庫 (8 核心深度補完) ---
if 'trials_db' not in st.session_state:
    st.session_state.trials_db = [
        {
            "cancer": "Ovarian", "name": "FRAmework-01 (LY4170156)", "pharma": "Eli Lilly (禮來)",
            "drug": "LY4170156 + Bevacizumab", "pos": "R-TX", "sub_pos": ["PSOC", "PROC"],
            "rationale": "標靶 Folate Receptor alpha (FRα) ADC。搭載類微管蛋白載荷 (Payload)，利用 ADC 的精準傳遞與 Bevacizumab 的抗血管生成作用產生協同效應 (Synergy)，旨在克服 PARP 抑制劑耐藥後或鉑類抗藥性 (PROC) 的 Unmet Needs。",
            "dosing": {
                "Experimental Arm": "LY4170156 $3 \text{ mg/kg IV}$ + Bevacizumab $15 \text{ mg/kg IV}$ 每 21 天一次 (Q3W)。",
                "Control Arm (Part A: PROC)": "研究者選擇之化療 (Paclitaxel, PLD, Gemcitabine, Topotecan) 或 Mirvetuximab (MIRV)。",
                "Control Arm (Part B: PSOC)": "標準鉑類雙藥化療 (Platinum doublet) 併用 Bevacizumab。"
            },
            "outcomes": {"ORR": "Phase 1/2: ~35-40%", "mPFS": "主要終點 (PFS per RECIST 1.1)", "HR": "Phase 3 招募中", "CI": "NCT06536348", "AE": "蛋白尿 (Proteinuria), 高血壓, ILD 監測"},
            "inclusion": [
                "18歲以上，病理證實為 High-grade Serous 或 Carcinosarcoma 之卵巢癌、輸卵管癌或原發性腹膜癌。",
                "必須提供腫瘤組織檢體以確認 FRα 表達狀態 (需符合中央實驗室陽性判定)。",
                "Part A (PROC): 最後一劑鉑類治療後 90–180 天內惡化；曾接受過 1–3 線系統性治療。",
                "Part B (PSOC): 最後一劑鉑類治療後 >180 天惡化；曾接受 PARP inhibitor 治療且產生獲得性耐藥或不適用者。",
                "ECOG Performance Status (PS) 為 0 或 1。",
                "具備 RECIST v1.1 標準下至少一個可測量病灶 (Measurable lesion)。",
                "充分的骨髓、肝臟及腎臟功能 (ANC ≥1500/mm³, Hb ≥9g/dL, Creatinine clearance ≥30mL/min)。"
            ],
            "exclusion": [
                "先前曾接受過帶有 Topoisomerase I 抑制劑載荷之 ADC 治療 (如 Enhertu)。",
                "先前曾患有需類固醇治療之非感染性間質性肺病 (ILD) 或肺炎病史。",
                "具有臨床顯著的蛋白尿 (24小時尿蛋白 ≥2g 或 UPCR ≥2.0)。",
                "活動性 CNS 轉移或軟腦膜轉移 (Leptomeningeal disease)。",
                "具有未控制的高血壓 (Systolic >150 mmHg 或 Diastolic >90 mmHg)。",
                "曾對 Bevacizumab 或相關賦形劑產生嚴重過敏反應。"
            ],
            "ref": "NCT06536348"
        },
        {
            "cancer": "Ovarian", "name": "REJOICE-Ovarian01", "pharma": "Daiichi Sankyo (DS)",
            "drug": "R-DXd (Raludotatug Deruxtecan)", "pos": "R-TX", "sub_pos": ["PROC"],
            "rationale": "標靶 Cadherin-6 (CDH6) ADC，搭載 DXd (Topo I inhibitor) 載荷。具備極高 DAR (Drug-Antibody Ratio) 與強力 Bystander Effect，可有效殺傷 CDH6 低表達之鄰近癌細胞，專攻高度異質性之 PROC。",
            "dosing": {
                "Experimental Arm": "R-DXd 5.6 mg/kg IV Q3W。",
                "Control Arm": "Investigator's Choice (Paclitaxel, PLD, or Topotecan)。"
            },
            "outcomes": {"ORR": "46.0% (Ph 1 update)", "mPFS": "7.1 months", "HR": "Phase 3 Ongoing", "CI": "NCT06161025", "AE": "Nausea, ILD Risk, Neutropenia"},
            "inclusion": [
                "High-grade (HG) Serous 或 Endometrioid 卵巢、腹膜或輸卵管癌。",
                "鉑類抗藥性 (PROC) 定義：1線鉑類後 90-180 天內惡化，或 2-4 線後 ≤180 天惡化。",
                "已接受過至少 1 線且不超過 3-4 線系統性治療。",
                "需提供腫瘤檢體評估 CDH6 表達量 (作為分層依據)。",
                "除非有醫學禁忌，否則必須曾接受過 Bevacizumab 治療。"
            ],
            "exclusion": [
                "排除 Clear cell, Mucinous, Sarcomatous 或 Low-grade/Borderline 腫瘤。",
                "曾患有需類固醇治療之 ILD/肺臟炎，或基線疑似患有 ILD。",
                "基線時存在 ≥ Grade 2 的周邊神經病變 (Peripheral Neuropathy)。",
                "心臟功能異常：LVEF < 50% 或具不穩定心絞痛病史。"
            ],
            "ref": "JCO 2024"
        },
        {
            "cancer": "Ovarian", "name": "TroFuse-021", "pharma": "MSD (Merck)",
            "drug": "Sac-TMT (MK-2870)", "pos": "P-MT", "sub_pos": ["HRD Negative", "pHRD"],
            "rationale": "標靶 Trop-2 ADC。透過誘導免疫原性細胞死亡 (ICD) 並結合 Bevacizumab 的微環境調節，旨在優化 pHRD 族群在一線化療後之維持療效。",
            "dosing": {
                "Arm 1": "Sac-TMT 單藥維持治療 (Q2W/Q3W)。",
                "Arm 2": "Sac-TMT + Bevacizumab 15 mg/kg Q3W。",
                "Arm 3 (SoC)": "臨床觀察 (Observation) 或 Bevacizumab 單藥維持。"
            },
            "outcomes": {"ORR": "Est 40%", "mPFS": "招募中", "HR": "Phase 3", "CI": "NCT06241729", "AE": "口腔炎 (Stomatitis), 腹瀉, 貧血"},
            "inclusion": [
                "新診斷之 FIGO Stage III 或 IV 卵巢、腹膜或輸卵管癌。",
                "HRD 狀態確認為陰性 (HRD negative / pHRD) 且 BRCA 野生型 (Wild-type)。",
                "剛完成第一線含鉑化療並達到臨床緩解 (CR 或 PR) 狀態。",
                "需提供組織樣品進行 Trop-2 表達與 HRD 狀態之中央實驗室判定。"
            ],
            "exclusion": [
                "具備 BRCA 基因突變或 HRD 陽性者 (通常應使用 PARP 抑制劑)。",
                "具有嚴重炎症性腸道疾病或嚴重骨髓抑制病史。",
                "先前曾接受過任何針對 Trop-2 之 ADC 治療。"
            ],
            "ref": "ENGOT-ov85"
        },
        {
            "cancer": "Ovarian", "name": "DOVE (APGOT-OV07)", "pharma": "GSK",
            "drug": "Dostarlimab + Beva", "pos": "R-TX", "sub_pos": ["PROC"],
            "rationale": "針對透明細胞癌 (OCCC) 特有的免疫抑制微環境。透過 PD-1 阻斷與 VEGF 抑制之雙重打擊，恢復 T 細胞浸潤並引發抗腫瘤應答。",
            "dosing": {
                "Experimental": "Dostarlimab 500mg (Q3W x4) 接續 1000mg (Q6W) + Bevacizumab 15mg/kg Q3W。",
                "Control": "單藥化療 (Gemcitabine / PLD / Taxel)。"
            },
            "outcomes": {"ORR": "40.2% (OCCC)", "mPFS": "8.2 months", "HR": "0.58", "CI": "95% CI: 0.42-0.79", "AE": "高血壓, 疲勞"},
            "inclusion": [
                "組織學證實為透明細胞癌 (OCCC) 佔比 > 50% 且具備 RECIST 可測量病灶。",
                "鉑類抗藥性 (Platinum-resistant)：最後一劑鉑類後 12 個月內惡化。",
                "先前系統性治療線數 ≤ 5 線。允許先前曾使用 Bevacizumab。"
            ],
            "exclusion": [
                "先前曾接受過 PD-1/L1 或 CTLA-4 抑制劑免疫治療。",
                "臨床顯著的腸阻塞病史或活動性消化道出血風險。"
            ],
            "ref": "JCO 2025"
        },
        {
            "cancer": "Ovarian", "name": "DS8201-772 (Enhertu)", "pharma": "AstraZeneca",
            "drug": "Trastuzumab Deruxtecan", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"],
            "rationale": "標靶 HER2 ADC。救援化療穩定後之維持策略，旨在透過 ADC 的精準殺傷延長 PFS，特別針對 HER2 表現族群。",
            "dosing": {"Mono": "T-DXd 5.4 mg/kg Q3W", "Combo": "T-DXd 5.4 mg/kg + Beva 15 mg/kg Q3W"},
            "outcomes": {"ORR": "46.3% (IHC 3+)", "mPFS": "10.4m", "HR": "0.42", "CI": "95% CI: 0.30-0.58", "AE": "ILD Risk (6.2%)"},
            "inclusion": ["HER2 IHC 1+/2+/3+ 確認", "PSOC 復發後救援化療達穩定 (Non-PD)"],
            "exclusion": ["曾有需類固醇治療之 ILD 病史", "LVEF < 50%"], "ref": "JCO 2024"
        },
        # Endometrial Cancer
        {"cancer": "Endometrial", "name": "MK2870-033", "pharma": "MSD", "drug": "Sac-TMT + Pembro", "pos": "P-MT", "sub_pos": ["IO Maintenance"], 
         "rationale": "標靶 Trop-2 ADC 協同 PD-1 抑制劑。利用 ADC 誘導的免疫原性調節強化 Pembrolizumab 在 pMMR 族群的長期應答。",
         "dosing": {"Maintenance": "Pembro 400mg + Sac-TMT 5mg/kg 每 6 週一次 (Q6W)。"},
         "outcomes": {"ORR": "Est 35%", "mPFS": "Phase 3 Ongoing", "HR": "TBD", "CI": "NCT06132958", "AE": "貧血, 口腔炎"},
         "inclusion": ["pMMR 子宮內膜癌 (中心實驗室確認)", "FIGO III/IV 一線化療後達 CR/PR"],
         "exclusion": ["子宮肉瘤 (Uterine Sarcoma)", "先前接受過任何晚期 IO 治療"], "ref": "ESMO 2025"},
        
        {"cancer": "Endometrial", "name": "GU-US-682-6769", "pharma": "Gilead", "drug": "SG (Trodelvy)", "pos": "R-TX", "sub_pos": ["pMMR / MSS"], 
         "rationale": "針對 Trop-2 ADC。利用 SN-38 載荷引發 DNA 損傷，專攻鉑類與免疫治療進展後之救援治療。",
         "dosing": {"Exp": "SG 10 mg/kg IV (D1, D8)", "Control": "TPC (Doxo/Taxel)"},
         "outcomes": {"ORR": "28.5%", "mPFS": "5.6m", "HR": "0.64", "CI": "NCT03964727", "AE": "嗜中性球減少 (Neutropenia)"},
         "inclusion": ["復發性內膜癌 (非肉瘤)", "鉑類與 PD-1/L1 失敗後進展"],
         "exclusion": ["先前曾用過 Trop-2 ADC", "活動性 CNS 轉移"], "ref": "JCO 2024"},

        # Cervical Cancer
        {"cancer": "Cervical", "name": "innovaTV 301", "pharma": "Seagen", "drug": "Tivdak", "pos": "R-TX", "sub_pos": ["2L / 3L Therapy"], 
         "rationale": "標靶 Tissue Factor (TF) ADC。搭載 MMAE 載荷，旨在克服後線子宮頸癌之化療耐藥性。",
         "dosing": {"Exp": "Tivdak 2.0 mg/kg Q3W", "Control": "化療 (TPC)"},
         "outcomes": {"ORR": "17.8%", "mPFS": "4.2m", "HR": "0.70", "CI": "NEJM 2024", "AE": "眼表毒性, 神經病變"},
         "inclusion": ["復發性/轉移性子宮頸癌", "先前接受 1–2 線治療後進展"],
         "exclusion": ["嚴重眼疾或角膜炎", "先前用過針對 TF 之藥物"], "ref": "NEJM 2024"}
    ]

# --- 3. 狀態同步與 AI 功能 ---
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = st.session_state.trials_db[0]['name']

with st.sidebar:
    st.markdown("<h3 style='color: #6A1B9A;'>🤖 AI 專家決策助理</h3>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 患者媒合判定分析", expanded=True):
        patient_notes = st.text_area("輸入病歷摘要", height=300, placeholder="例：62y/o female, OCCC, PROC, FRα+, ECOG 1...")
        if st.button("🚀 開始深度比對"):
            if api_key and patient_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    prompt = f"分析病歷：{patient_notes}。參考這 8 個試驗：{st.session_state.trials_db}。根據病程大綱，建議最適合試驗並說明醫學理由。"
                    st.write(model.generate_content(prompt).text)
                except Exception as e: st.error(f"AI 異常: {e}")

# --- 4. 主頁面：病程導航 ---
st.markdown("<div class='main-title'>婦癌臨床試驗導航系統 (2026 SoC 整合版)</div>", unsafe_allow_html=True)
cancer_type = st.radio("選擇癌症類型", ["Ovarian", "Endometrial", "Cervical"], horizontal=True)



cols = st.columns(4)
stages_data = guidelines_nested[cancer_type]

for i, stage in enumerate(stages_data):
    with cols[i]:
        st.markdown(f"""<div class='big-stage-card card-{stage['css']}'><div class='big-stage-header header-{stage['css']}'>{stage['header']}</div>""", unsafe_allow_html=True)
        for sub in stage['subs']:
            st.markdown(f"""<div class='sub-block'><div class='sub-block-title'>📘 {sub['title']}</div><div class='sub-block-content'>{sub['content']}</div>""", unsafe_allow_html=True)
            relevant_trials = [t for t in st.session_state.trials_db if t["cancer"] == cancer_type and t["pos"] == stage["id"] and any(s in sub["title"] for s in t["sub_pos"])]
            if relevant_trials:
                for t in relevant_trials:
                    # 使用唯一 Key
                    ukey = f"btn_{t['name']}_{stage['id']}_{sub['title']}"
                    with st.popover(f"📍 {t['pharma']} | {t['name']} | {t['drug']}", use_container_width=True):
                        st.markdown(f"#### ✨ {t['name']} 重點解析")
                        st.info(f"**Rationale:** {t['rationale'][:100]}...")
                        if st.button("📊 開啟深度分析報告", key=ukey):
                            st.session_state.selected_trial = t['name']
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. 深度分析報告看板 ---
st.divider()
t_options = [t["name"] for t in st.session_state.trials_db if t["cancer"] == cancer_type]
try: curr_idx = t_options.index(st.session_state.selected_trial)
except: curr_idx = 0

if t_options:
    selected_name = st.selectbox("🎯 快速搜尋詳細報告：", t_options, index=curr_idx)
    t = next(it for it in st.session_state.trials_db if it["name"] == selected_name)

    st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
    st.markdown(f"<span class='pharma-badge'>{t['pharma']}</span>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #E0E0E0; padding-bottom:15px; font-weight:900;'>📋 {t['name']} 深度分析報告</h2>", unsafe_allow_html=True)

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
            <div class='hr-display' style='text-align:center; background:white; padding:15px; border:2px solid #FFE082; border-radius:10px;'>
                <div style='font-size: 15px; color: #795548; font-weight:700; margin-bottom:5px;'>Hazard Ratio (HR) / NCT ID</div>
                <div class='hr-big-val'>{t['outcomes']['HR']}</div>
                <div class='hr-ci' style='font-size:18px; color:#5D4037; font-weight:700;'>{t['outcomes']['CI']}</div>
            </div>
        """, unsafe_allow_html=True)
        st.write(f"**ORR:** {t['outcomes']['ORR']} | **mPFS:** {t['outcomes']['mPFS']}")
        st.error(f"**Safety / AE:** {t['outcomes']['AE']}")
        

    st.divider()
    r2_c1, r2_c2 = st.columns(2)
    with r2_c1:
        st.markdown("<div class='info-box-blue' style='background:#E8F5E9; border-left:8px solid #2E7D32;'><b>✅ Inclusion Criteria (納入標準)</b></div>", unsafe_allow_html=True)
        for inc in t['inclusion']: st.write(f"• **{inc}**")
    with r2_c2:
        st.markdown("<div class='info-box-blue' style='background:#FFEBEE; border-left:8px solid #C62828;'><b>❌ Exclusion Criteria (排除標準)</b></div>", unsafe_allow_html=True)
        for exc in t['exclusion']: st.write(f"• **{exc}**")
    st.markdown("</div>", unsafe_allow_html=True)
