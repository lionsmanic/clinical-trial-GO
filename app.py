import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床導航與實證圖書館 (2026 最終全功能整合版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=Roboto:wght@400;700;900&display=swap');
    
    /* === 極致緊緻化 UI === */
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', 'Roboto', sans-serif;
        background-color: #F4F7F9;
        color: #1A1A1A;
        font-size: 19px !important;
        line-height: 1.1;
    }

    .main-title {
        font-size: 32px !important; font-weight: 900; color: #004D40;
        padding: 5px 0; border-bottom: 3px solid #4DB6AC; margin-bottom: 5px;
    }

    /* 大階段方塊：零留白設計 */
    .big-stage-card {
        border-radius: 10px; padding: 0px; 
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        border: 2px solid transparent; background: white; 
        margin-bottom: 4px; overflow: hidden; height: auto !important;
    }
    .big-stage-header {
        font-size: 17px !important; font-weight: 900; color: white;
        padding: 5px; text-align: center;
    }

    /* 子區塊 (SoC 與分子亞型) */
    .sub-block {
        margin: 2px 4px; padding: 4px;
        border-radius: 6px; background: #F8F9FA;
        border-left: 5px solid #546E7A;
    }
    .sub-block-title {
        font-size: 13px; font-weight: 900; color: #37474F;
        margin-bottom: 1px; border-bottom: 1.1px solid #CFD8DC; padding-bottom: 1px;
    }
    .sub-block-content {
        font-size: 14px; color: #263238; font-weight: 500; line-height: 1.15;
    }

    /* 階段配色 */
    .card-p-tx { border-color: #2E7D32; }
    .header-p-tx { background: linear-gradient(135deg, #43A047, #2E7D32); }
    .card-p-mt { border-color: #1565C0; }
    .header-p-mt { background: linear-gradient(135deg, #1E88E5, #1565C0); }
    .card-r-tx { border-color: #E65100; }
    .header-r-tx { background: linear-gradient(135deg, #FB8C00, #E65100); }
    .card-r-mt { border-color: #6A1B9A; }
    .header-r-mt { background: linear-gradient(135deg, #8E24AA, #6A1B9A); }

    /* 按鈕樣式：深黑色加粗 (#1A1A1A) */
    .stPopover button { 
        font-weight: 900 !important; font-size: 12px !important; 
        border-radius: 4px !important; margin-top: 1px !important;
        padding: 1px 6px !important; width: 100% !important; 
        text-align: left !important; color: #1A1A1A !important; 
        border: 1px solid rgba(0,0,0,0.15) !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
    }
    
    .stPopover button[aria-label*="📚"] { background: #ECEFF1 !important; border-left: 5px solid #455A64 !important; }
    .stPopover button[aria-label*="Eli Lilly"] { background: #FCE4EC !important; border-left: 5px solid #E91E63 !important; } 
    .stPopover button[aria-label*="Daiichi Sankyo"] { background: #E8F5E9 !important; border-left: 5px solid #4CAF50 !important; } 
    .stPopover button[aria-label*="MSD"] { background: #E3F2FD !important; border-left: 5px solid #1976D2 !important; } 
    .stPopover button[aria-label*="AstraZeneca"] { background: #F3E5F5 !important; border-left: 5px solid #8E24AA !important; } 
    .stPopover button[aria-label*="GSK"] { background: #FFF3E0 !important; border-left: 5px solid #F57C00 !important; } 
    .stPopover button[aria-label*="Gilead"] { background: #E1F5FE !important; border-left: 5px solid #03A9F4 !important; } 

    .detail-section { background: white; border-radius: 18px; padding: 25px; border: 1px solid #CFD8DC; box-shadow: 0 10px 40px rgba(0,0,0,0.05); }
    .hr-big-val { font-family: 'Roboto', sans-serif; font-size: 50px !important; font-weight: 900; color: #D84315; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 指引導航數據庫：包含 MOC 鑑別與 PSOC/PROC 分流 ---
guidelines_nested = {
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "MMRd / MSI-H / dMMR", "content": "一線標竿：Chemo + PD-1 (GY018/RUBY)。Dostarlimab 獲益顯著。"},
            {"title": "NSMP / pMMR / MSS", "content": "排除分型。視 ER/Grade 權重決策；二線考慮 Pembro+Lenva。"},
            {"title": "POLEmut / p53abn", "content": "POLE: 最佳預後可降階；p53abn: 最差預後，需積極化放療。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "IO Maintenance", "content": "一線 IO 治療後接續維持直到疾病進展 (PD)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "Recurrent EC", "content": "二線方案：標靶+免疫 (pMMR) 或 IO 單藥 (MMRd/GARNET)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "維持有效治療直到不可耐受或進展。"}]}
    ],
    "Ovarian": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "HGSC / Endometrioid", "content": "手術 (PDS/IDS) + Carboplatin/Paclitaxel ± Bevacizumab。"},
            {"title": "Mucinous (MOC) 鑑別", "content": "1. 鑑定：CK7+/SATB2- (原發)。 2. Expansile: 預後佳。 3. Infiltrative: 高復發風險，建議積極化療。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "BRCA mutated", "content": "Olaparib 單藥維持 2年。"}, {"title": "HRD positive (wt)", "content": "Olaparib+Bev (2年) 或 Niraparib 單藥 (3年)。"}]},
        {"id": "R-TX (PROC)", "header": "復發治療 (PROC)", "css": "r-tx", "subs": [{"title": "Platinum-Resistant", "content": "PFI < 6m。單藥化療 ± Bev 或標靶 ADC (MIRASOL)。"}]},
        {"id": "R-TX (PSOC)", "header": "復發治療 (PSOC)", "css": "r-tx", "subs": [{"title": "Platinum-Sensitive", "content": "PFI > 6m。含鉑雙藥化療 ± Bev。評估二次手術 (DESKTOP)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Platinum Sensitive Maint", "content": "含鉑救援緩解後續以 PARPi 維持。"}]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "CCRT (Locally Advanced)", "content": "同步化放療。高風險者同步 IO (A18) 或誘導化療 (INTERLACE)。"},
            {"title": "Early Stage (Surgery)", "content": "根治性開腹術 (LACC)。低風險者選單純切除 (SHAPE)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "Metastatic Maint", "content": "1L 轉移性 IO 方案後延續維持。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "Recurrent / Metastatic", "content": "一線 Pembro + 化療 ± Bev。二線 ADC (Tivdak) 或 IO (EMPOWER)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "維持有效治療直至進展。"}]}
    ]
}

# --- 2. 實證里程碑 (📚 Milestone Library - 深度擴充生存數據) ---
milestone_db = [
    # 子宮內膜癌
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H / dMMR"], "name": "📚 RUBY (Dostarlimab)", "drug": "Dostarlimab + CP", 
     "summary": "族群：晚期或首次復發 EC。數據：dMMR PFS HR 0.32 (死亡風險降 68%)；全人群 mOS 44.6m vs 28.2m (HR 0.69)。確立 dMMR 一線標準。"},
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H / dMMR", "NSMP / pMMR / MSS"], "name": "📚 NRG-GY018 (KEYNOTE-868)", "drug": "Pembrolizumab + CP", 
     "summary": "族群：FIGO III-IV/復發。數據：dMMR PFS HR 0.30；pMMR HR 0.54。支持一線不論 MMR 狀態之 IO 獲益。"},
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["NSMP / pMMR / MSS"], "name": "📚 DUO-E", "drug": "Durvalumab ± Olaparib", 
     "summary": "結果：Durva+Ola 三藥組 PFS HR 0.57；單藥 IO 組 HR 0.77。提示 PARPi 在 pMMR 族群具維時協同效應。"},
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H / dMMR"], "name": "📚 AtTEnd", "drug": "Atezolizumab + CP", 
     "summary": "族群：晚期/復發 (含 Carcinosarcoma)。數據：dMMR PFS HR 0.36，獲益顯著；全體 OS HR 0.82 (P=0.048)。"},
    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "name": "📚 KEYNOTE-775", "drug": "Pembro + Lenvatinib", 
     "summary": "二線標靶+免疫：pMMR OS 17.4m vs 12.0m (HR 0.68)；5年長期 OS 率 16.7% vs 7.3%。確立 MSS 標準。"},
    {"cancer": "Endometrial", "pos": "R-TX", "sub_pos": ["Recurrent EC"], "name": "📚 GARNET", "drug": "Dostarlimab 單藥", 
     "summary": "族群：dMMR/MSI-H。結果：ORR 達 45.5%，反應持久。奠定後線免疫單藥地位。"},

    # 子宮頸癌
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["CCRT (Locally Advanced)"], "name": "📚 KEYNOTE-A18", "drug": "Pembrolizumab + CCRT", 
     "summary": "族群：IB2-IVA 高風險 LACC。數據：36個月 OS 顯著提升至 82.6% (vs 74.8%, HR 0.67)。確立 LACC 標準。"},
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["CCRT (Locally Advanced)"], "name": "📚 INTERLACE", "drug": "Induction Carbo/Pacli", 
     "summary": "誘導化療：6週化療接續 CCRT。數據：5年 OS 80% vs 72% (HR 0.60)，生存獲益顯著。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["1L Recurrent"], "name": "📚 KEYNOTE-826", "drug": "Pembro + Chemo ± Bev", 
     "summary": "一線 R/M：全人群 OS HR 0.63；CPS≥1 HR 0.60。奠定 R/M 一線 IO + Chemo 標準。"},
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["2L / 3L Therapy"], "name": "📚 innovaTV 301", "drug": "Tivdak (TF-ADC)", 
     "summary": "二/三線 ADC：OS 11.5m vs 9.5m (HR 0.70)，ORR 17.8%。首個 OS 獲益 ADC 研究。"},
    {"cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Early Stage (Surgery)"], "name": "📚 LACC Trial", "drug": "Open vs MIS", 
     "summary": "早期手術：微創手術復發率與死亡率顯著較高 (HR 6.00)。重回開腹根治術為標準。"},

    # 卵巢癌
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["BRCA mutated"], "name": "📚 SOLO-1 (Olaparib)", "drug": "Olaparib 維持", 
     "summary": "一線維持：7年存活率 67% (vs 46.5%, HR 0.33)。確立 BRCAm 患者長生存治癒機會。"},
    {"cancer": "Ovarian", "pos": "P-MT", "sub_pos": ["HRD positive (wt)", "HRD negative / pHRD"], "name": "📚 PRIMA", "drug": "Niraparib 維持", 
     "summary": "一線全人群：HRD+ 獲益最大 (PFS 21.9m vs 10.4m, HR 0.43)。支持不限 BRCA 之一線維持。"},
    {"cancer": "Ovarian", "pos": "R-TX (PROC)", "sub_pos": ["Platinum-Resistant"], "name": "📚 MIRASOL (FRα ADC)", "drug": "Mirvetuximab", 
     "summary": "FRα+ PROC：OS 16.4m vs 12.7m (HR 0.67)，ORR 42.3%。PROC 歷史性 OS 突破。"},
    {"cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], "name": "📚 van Driel HIPEC", "drug": "Surgery + HIPEC", 
     "summary": "NACT 後 IDS 手術加溫熱化療。數據：RFS 改善，mOS 45.7m vs 33.9m (HR 0.67)。"},
    {"cancer": "Ovarian", "pos": "R-TX (PSOC)", "sub_pos": ["Platinum-Sensitive"], "name": "📚 DESKTOP III", "drug": "Secondary Debulking", 
     "summary": "復發手術：嚴選患者二次減積顯著延長 mOS 至 53.7m (vs 46.0m, HR 0.75)。"},
]

# --- 3. 招募中試驗 (📍 Ongoing - 完整救回並詳盡擴充) ---
ongoing_trials = [
    {"cancer": "Ovarian", "name": "FRAmework-01 (LY4170156)", "pharma": "Eli Lilly", "drug": "LY4170156 + Bevacizumab", "pos": "R-TX (PROC)", "sub_pos": ["Platinum-Resistant"], 
     "rationale": "標靶 Folate Receptor alpha (FRα) ADC。聯用 Bevacizumab 可產生血管調節與免疫重塑之協同作用 (Synergy)，提升藥物滲透深度並透過旁觀者效應殺傷低表達細胞。",
     "dosing": {"Exp Arm": "LY4170156 3 mg/kg IV + Bevacizumab 15 mg/kg IV Q3W。", "Control Arm": "醫師選擇單藥化療 (Pacli, PLD, Gem) 或 MIRV。"},
     "inclusion": ["High-grade Serous / Carcinosarcoma 之卵巢癌。", "中央實驗室確認 FRα 表達陽性。", "最後一劑鉑類後 90–180 天內惡化 (PROC)。", "先前接受過 1–3 線系統治療。"],
     "exclusion": ["先前曾用過帶有 Topoisomerase I 抑制劑 Payload 之 ADC (如 Enhertu)。", "具有臨床顯著蛋白尿 (UPCR ≥ 2.0)。", "活動性 ILD 病史。"], "ref": "NCT06536348"},
    
    {"cancer": "Ovarian", "name": "REJOICE-Ovarian01", "pharma": "Daiichi Sankyo", "drug": "R-DXd (Raludotatug Deruxtecan)", "pos": "R-TX (PROC)", "sub_pos": ["Platinum-Resistant"], 
     "rationale": "標靶 Cadherin-6 (CDH6) ADC，搭載 DXd 載荷。具備極高 DAR (8) 與強力旁觀者效應，專攻高度異質性之 PROC，挑戰二/三線生存標準。",
     "dosing": {"Exp Arm": "R-DXd 5.6mg/kg IV Q3W。", "Control Arm": "研究者選擇單藥化療。"},
     "inclusion": ["HG Serous 或 Endometrioid PROC。", "先前接受 1-4 線系統治療。", "需提供切片以進行 CDH6 分層判定。", "需曾用過 Bevacizumab。"],
     "exclusion": ["Low-grade 腫瘤。", "基線 Grade ≥2 周邊神經病變。", "LVEF < 50%。"], "ref": "JCO 2024"},
    
    {"cancer": "Ovarian", "name": "TroFuse-021", "pharma": "MSD", "drug": "Sac-TMT (MK-2870)", "pos": "P-MT", "sub_pos": ["HRD positive (wt)", "HRD negative / pHRD"], 
     "rationale": "標靶 Trop-2 ADC。結合 Beva 微環境調節與 ADC 誘導之免疫原性細胞死亡 (ICD)，旨在優化 pHRD 族群在一線含鉑化療後維持獲益。",
     "dosing": {"Arm 1": "Sac-TMT 單藥維持。", "Arm 2": "Sac-TMT + Beva 15mg/kg Q3W。", "Arm 3": "Standard Bevacizumab 維持。"},
     "inclusion": ["FIGO Stage III/IV 卵巢癌。", "HRD negative / pHRD 且 BRCA 為野生型。", "一線含鉑化療後達 CR/PR 狀態。", "可供檢測之 Trop-2 組織。"],
     "exclusion": ["先前用過針對 Trop-2 之 ADC。", "嚴重炎症性腸道疾病 (IBD) 病史。"], "ref": "ENGOT-ov85"},

    {"cancer": "Endometrial", "name": "MK2870-033", "pharma": "MSD", "drug": "Sac-TMT + Pembrolizumab", "pos": "P-MT", "sub_pos": ["IO Maintenance"], 
     "rationale": "標靶 Trop-2 ADC 協同 PD-1 抑制劑。利用免疫重塑提升 Pembrolizumab 在 pMMR 或 NSMP 族群的應答深度與持續緩解時間。",
     "inclusion": ["pMMR 子宮內膜癌 (中心檢測)。", "FIGO III/IV 一線含鉑+Pembro後達 CR/PR。", "未針對復發進行過系統性治療。"],
     "exclusion": ["子宮肉瘤 (Sarcoma)。", "先前接受過針對晚期病灶之 IO 治療。"], "ref": "ESMO 2025"},
    
    {"cancer": "Endometrial", "name": "GU-US-682-6769", "pharma": "Gilead", "drug": "SG (Trodelvy)", "pos": "R-TX", "sub_pos": ["Recurrent EC"], 
     "rationale": "標靶 Trop-2 ADC。釋放 SN-38 載荷引發 DNA 損傷，解決鉑類與免疫失敗救援，具強力 Bystander 效應對抗異質性病灶。",
     "inclusion": ["復發性 EC (不含肉瘤)。", "鉑類與 PD-1 失敗後進展。", "充分骨髓功能 (ANC ≥1500)。"],
     "exclusion": ["先前用過 Trop-2 ADC。", "活動性 CNS 轉移。"], "ref": "JCO 2024"},

    {"cancer": "Ovarian", "name": "DS8201-772 (Enhertu)", "pharma": "AstraZeneca", "drug": "T-DXd (Trastuzumab Deruxtecan)", "pos": "R-MT", "sub_pos": ["Platinum Sensitive Maint"], 
     "rationale": "標靶 HER2 ADC。救援化療穩定後之精準維持。超高 DAR (8) 優勢清除 HER2 表現殘留病灶，延緩復發。",
     "inclusion": ["HER2 IHC 1+/2+/3+ 確認。", "PSOC 救援化療達穩定 (Non-PD)。", "LVEF ≥ 50%。"],
     "exclusion": ["曾患有需類固醇治療之非感染性 ILD 肺部病史。"], "ref": "JCO 2024"},

    {"cancer": "Ovarian", "name": "DOVE", "pharma": "GSK", "drug": "Dostarlimab + Bevacizumab", "pos": "R-TX (PROC)", "sub_pos": ["Platinum-Resistant"], 
     "rationale": "針對透明細胞癌 (OCCC)。利用免疫檢查點阻斷與抗血管生成雙重打擊，改善其特有之免疫抑制環境。",
     "inclusion": ["組織學 OCCC > 50%。", "鉑類抗藥性 (PFI < 12m)。", "可測量病灶。"],
     "exclusion": ["先前用過任何免疫治療。"], "ref": "JCO 2025"},

    {"cancer": "Cervical", "name": "innovaTV 301", "pharma": "Seagen", "drug": "Tisotumab Vedotin", "pos": "R-TX", "sub_pos": ["2L / 3L Therapy"], 
     "rationale": "標靶 Tissue Factor ADC。旨在克服後線子宮頸癌化療耐藥性，改善生存期。",
     "inclusion": ["復發/轉移子宮頸癌。", "先前 1–2 線治療後進展。"],
     "exclusion": ["嚴重眼疾/角膜炎。", "活動性出血傾向。"], "ref": "NEJM 2024"}
]

# --- 4. 動態模型巡邏與 AI 模型選擇 ---
def get_gemini_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target_model = None
        for m in available_models:
            if 'gemini-1.5-flash' in m: target_model = m; break
        if not target_model:
            for m in available_models:
                if 'gemini-pro' in m or 'gemini-1.5-pro' in m: target_model = m; break
        if target_model: return genai.GenerativeModel(target_model)
    except: return None

# --- 5. 側邊欄 ---
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = ongoing_trials[0]['name']

with st.sidebar:
    st.markdown("<h3 style='color: #6A1B9A;'>🤖 AI 實證決策助理</h3>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 病歷深度數據比對", expanded=True):
        p_notes = st.text_area("輸入摘要 (含細胞型態/標記)", height=250)
        if st.button("🚀 開始分析"):
            if api_key and p_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = get_gemini_model()
                    if model:
                        prompt = f"分析：{p_notes}。參考實證：{milestone_db} 及進行中：{ongoing_trials}。提供路徑建議與理由。"
                        st.write(model.generate_content(prompt).text)
                    else: st.error("找不到 AI 模型。")
                except Exception as e: st.error(f"AI 異常: {e}")

# --- 6. 主頁面：導航地圖 ---
st.markdown("<div class='main-title'>婦癌臨床導航儀表板 (2026 實證與收案全整合)</div>", unsafe_allow_html=True)
cancer_type = st.radio("第一步：選擇癌症類型", ["Endometrial", "Ovarian", "Cervical"], horizontal=True)

# 標題與內容高度緊扣
cols = st.columns(len(guidelines_nested[cancer_type]))
stages_data = guidelines_nested[cancer_type]

for i, stage in enumerate(stages_data):
    with cols[i]:
        st.markdown(f"""<div class='big-stage-card card-{stage['css']}'><div class='big-stage-header header-{stage['css']}'>{stage['header']}</div>""", unsafe_allow_html=True)
        for sub in stage['subs']:
            st.markdown(f"""<div class='sub-block'><div class='sub-block-title'>📘 {sub['title']}</div><div class='sub-block-content'>{sub['content']}</div>""", unsafe_allow_html=True)
            
            # A. 里程碑實證 (📚)
            rel_milestones = [m for m in milestone_db if m["cancer"] == cancer_type and m["pos"] == stage["id"] and any(s in sub["title"] for s in m["sub_pos"])]
            for m in rel_milestones:
                with st.popover(f"📚 {m['name']}", use_container_width=True):
                    st.success(f"**介入:** {m['drug']}\n\n**詳細數據:** {m['summary']}")
            
            # B. 招募中試驗 (📍)
            rel_trials = [t for t in ongoing_trials if t["cancer"] == cancer_type and t["pos"] == stage["id"] and any(s in sub["title"] for s in t["sub_pos"])]
            for t in rel_trials:
                label = f"📍 {t['pharma']} | {t['name']} | {t['drug']}"
                ukey = f"btn_{t['name']}_{stage['id']}_{sub['title'].replace(' ', '')}"
                with st.popover(label, use_container_width=True):
                    if st.button("📊 開啟極量化數據報告", key=ukey):
                        st.session_state.selected_trial = t['name']
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 7. 招募中試驗極量化報告 ---
st.divider()
all_ongoing = [t["name"] for t in ongoing_trials if t["cancer"] == cancer_type]
if all_ongoing:
    try: curr_idx = all_ongoing.index(st.session_state.selected_trial)
    except: curr_idx = 0
    selected_name = st.selectbox("🎯 切換招募中計畫詳細分析：", all_ongoing, index=curr_idx)
    t = next(it for it in ongoing_trials if it["name"] == selected_name)

    st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='color:#004D40; border-bottom:3px solid #E0E0E0; padding-bottom:10px; font-weight:900;'>📋 {t['name']} 招募中深度報告</h2>", unsafe_allow_html=True)

    r1, r2 = st.columns([1.3, 1])
    with r1:
        st.markdown("<div style='background:#E3F2FD; border-left:10px solid #1976D2; padding:15px; border-radius:10px;'><b>💉 Rationale & Dosing (機轉詳解)</b></div>", unsafe_allow_html=True)
        st.write(f"**核心藥物:** {t['drug']}")
        st.success(t['rationale'])
        

    with r2:
        st.markdown("<div style='background:#E8F5E9; border-left:8px solid #2E7D32; padding:15px; border-radius:10px;'><b>✅ Inclusion Criteria (納入標準)</b></div>", unsafe_allow_html=True)
        for inc in t.get('inclusion', []): st.write(f"• **{inc}**")

    st.markdown("<div style='background:#FFEBEE; border-left:8px solid #C62828; padding:15px; border-radius:10px; margin-top:10px;'><b>❌ Exclusion Criteria (排除標準)</b></div>", unsafe_allow_html=True)
    for exc in t.get('exclusion', []): st.write(f"• **{exc}**")
    st.markdown("</div>", unsafe_allow_html=True)
