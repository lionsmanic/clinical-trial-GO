import streamlit as st
import google.generativeai as genai

# --- 🏥 婦癌臨床導航與實證圖書館 (2026 旗艦最終版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

# 初始化聯動狀態
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = "📚 RUBY"

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=Roboto:wght@400;700;900&display=swap');
    
    /* === 極致緊緻化 UI 與 高對比度文字 === */
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', 'Roboto', sans-serif;
        background-color: #F4F7F9; color: #1A1A1A;
        font-size: 19px !important; line-height: 1.1;
    }

    .main-title {
        font-size: 32px !important; font-weight: 900; color: #004D40;
        padding: 5px 0; border-bottom: 3px solid #4DB6AC; margin-bottom: 5px;
    }

    /* 圖一修復：大階段方塊配色強化，確保標題清晰 */
    .big-stage-card {
        border-radius: 10px; padding: 0px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: 2px solid transparent; background: white; 
        margin-bottom: 4px; overflow: hidden; height: auto !important;
    }
    .big-stage-header {
        font-size: 18px !important; font-weight: 900; color: white !important;
        padding: 8px; text-align: center; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }

    /* 階段配色：加深飽和度以供閱讀 */
    .card-p-tx { border-color: #1B5E20; }
    .header-p-tx { background: linear-gradient(135deg, #2E7D32, #1B5E20); } /* 深綠 */
    .card-p-mt { border-color: #0D47A1; }
    .header-p-mt { background: linear-gradient(135deg, #1565C0, #0D47A1); } /* 深藍 */
    .card-r-tx { border-color: #E65100; }
    .header-r-tx { background: linear-gradient(135deg, #EF6C00, #BF360C); } /* 深橘紅 */
    .card-r-mt { border-color: #4A148C; }
    .header-r-mt { background: linear-gradient(135deg, #6A1B9A, #4A148C); } /* 深紫 */

    .sub-block {
        margin: 2px 4px; padding: 4px; border-radius: 6px; 
        background: #F8F9FA; border-left: 5px solid #455A64;
    }
    .sub-block-title {
        font-size: 14px; font-weight: 900; color: #263238;
        margin-bottom: 1px; border-bottom: 1.1px solid #CFD8DC; padding-bottom: 1px;
    }

    /* 按鈕樣式：深黑色加粗 (#1A1A1A) */
    .stPopover button { 
        font-weight: 900 !important; font-size: 11px !important; 
        border-radius: 4px !important; margin-top: 1px !important;
        padding: 1px 6px !important; width: 100% !important; 
        text-align: left !important; color: #1A1A1A !important; 
        border: 1px solid rgba(0,0,0,0.15) !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
    }
    
    .stPopover button[aria-label*="📚"] { background: #ECEFF1 !important; border-left: 5px solid #455A64 !important; }
    .stPopover button[aria-label*="📍"] { background: #E1F5FE !important; border-left: 5px solid #0288D1 !important; } 

    .detail-section { background: white; border-radius: 18px; padding: 25px; border: 1px solid #CFD8DC; box-shadow: 0 10px 40px rgba(0,0,0,0.05); }
    .hr-big-val { font-family: 'Roboto', sans-serif; font-size: 40px !important; font-weight: 900; color: #D84315; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 指引導航：PSOC/PROC 分流與 MOC 回歸 ---
guidelines_nested = {
    "Endometrial": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "MMRd / MSI-H", "content": "首選方案：含鉑化療併用 PD-1 抑制劑 (Immuno-chemo)。"},
            {"title": "NSMP / pMMR / MSS", "content": "預後取決於 ER/Grade。二線考慮標靶免疫 (KN775)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [{"title": "IO Maintenance", "content": "延續一線使用的免疫藥物直至進展 (PD)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [{"title": "Recurrent EC", "content": "二線標準：Pembro + Lenva (pMMR) 或 IO 單藥 (MMRd)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "維持有效標靶或免疫方案直到進展。"}]}
    ],
    "Ovarian": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "HGSC / Endometrioid", "content": "手術 (PDS/IDS) + Carbo/Pacli ± Bevacizumab。"},
            {"title": "Mucinous (MOC) 鑑別", "content": "判定：CK7+/SATB2-。Expansile (預後佳) vs Infiltrative (易轉移)。"}]},
        {"id": "P-MT", "header": "一線維持 (1L Maint)", "css": "p-mt", "subs": [
            {"title": "BRCA mutated", "content": "Olaparib 維持 2年 (SOLO-1)。"}, {"title": "HRD positive (wt)", "content": "Ola+Bev (PAOLA-1) 或 Niraparib (PRIMA)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "PSOC (Sensitive Recur)", "content": "PFI > 6m。評估二次手術 (DESKTOP III) 或含鉑雙藥。"},
            {"title": "PROC (Resistant Recur)", "content": "PFI < 6m。單藥化療 ± Bev 或 FRα ADC (MIRASOL)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Platinum Sensitive Maint", "content": "救援緩解後選 PARPi 維持 (NOVA/ARIEL3/SOLO2)。"}]}
    ],
    "Cervical": [
        {"id": "P-TX", "header": "初治 (Primary Tx)", "css": "p-tx", "subs": [
            {"title": "Locally Advanced (CCRT)", "content": "CCRT ± 同步免疫 (A18) 或誘導化療 (INTERLACE)。"},
            {"title": "Early Stage (Surgery)", "content": "根治術 (LACC) 或單純切除 (SHAPE)。"}]},
        {"id": "R-TX", "header": "復發治療 (Recurr Tx)", "css": "r-tx", "subs": [
            {"title": "Recurr / Metastatic", "content": "一線 Pembro+化療±Bev (KN826)。二線 ADC (innovaTV 301)。"}]},
        {"id": "R-MT", "header": "復後維持 (PR-Maint)", "css": "r-mt", "subs": [{"title": "Continuous Therapy", "content": "維持當前有效方案直到進展。"}]}
    ]
}

# --- 2. 綜合實證資料庫 (極量化擴充) ---
all_trials = [
    # --- 📚 Published Milestones ---
    {"cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["MMRd / MSI-H"], "name": "📚 RUBY", "pharma": "GSK", "drug": "Dostarlimab + CP", 
     "popover_summary": "dMMR 族群：死亡風險顯著降低 68% (HR 0.32)，奠定一線免疫標準。",
     "rationale": "透過 PD-1 阻斷 (PD-1 blockade) 釋放免疫制動，協同化療誘導的免疫原性細胞死亡 (ICD)，針對 MMRd 族群達到極高反應與持久應答 (Durable Response)。",
     "regimen": "誘導期 (Induction): Dostarlimab 500mg Q3W + CP x6 週期 -> 維持期 (Maintenance): Dostarlimab 1000mg Q6W 最長 3年。",
     "inclusion": ["新診斷 FIGO Stage III-IV 或首次復發之子宮內膜癌 (EC)。", "包含 Carcinosarcoma / Serous 等高風險組織型態。"],
     "exclusion": ["先前接受過系統性抗癌治療。", "活動性自體免疫疾病 (Active Autoimmune Disease)。"],
     "results": "dMMR 族群 PFS HR 0.32; ITT 全人群 mOS 44.6m (vs 28.2m, HR 0.69)."},
    
    {"cancer": "Cervical", "pos": "R-TX", "sub_pos": ["Recurr / Metastatic"], "name": "📚 KEYNOTE-826", "pharma": "MSD", "drug": "Pembrolizumab + Chemo ± Bev", 
     "popover_summary": "R/M 子宮頸癌一線標準：全人群死亡風險降低 37% (OS HR 0.63)。",
     "rationale": "於含鉑化療 (Platinum-based Chemo) 基礎上加入免疫檢查點抑制劑 (ICI)，改善復發或轉移性 (R/M) 子宮頸癌長期生存率。",
     "regimen": "Pembrolizumab 200mg Q3W + Paclitaxel/Cisplatin (或 Carbo) ± Bevacizumab 15mg/kg Q3W。",
     "inclusion": ["FIGO Stage IVB 或不適合手術/放療之持續、復發性子宮頸癌。", "CPS ≥ 1 為預後分層關鍵。"],
     "exclusion": ["先前曾接受過系統性化療。", "臨床顯著的出血風險。"],
     "results": "ITT 全人群 OS HR 0.63; CPS≥1 族群 OS HR 0.60."},

    {"cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PROC (Resistant Recur)"], "name": "📚 MIRASOL", "pharma": "ImmunoGen", "drug": "Mirvetuximab Soravtansine", 
     "popover_summary": "FRα 高表達 PROC 突破：OS 延長至 16.4m，ORR 達 42.3%。",
     "rationale": "首個針對葉酸受體 alpha (FRα) 的抗體藥物複合體 (ADC)，專門克服鉑類抗藥性 (Platinum-resistant) 患者的化療耐受性。",
     "regimen": "Mirvetuximab 6.0 mg/kg (Adjusted Ideal Body Weight) IV Q3W。",
     "inclusion": ["FRα 高表達 (High expression, ≥75% 腫瘤細胞 IHC 3+)。", "1-3 線前線治療後之鉑類抗藥型 (PROC) 卵巢癌。"],
     "exclusion": ["先前曾使用過針對 FRα 之 ADC。", "嚴重的角膜病變 (Corneal Disorders)。"],
     "results": "mOS 16.4m vs 12.7m (HR 0.67); mPFS 5.6m vs 4.0m (HR 0.65)."},

    # --- 📍 Ongoing Trials ---
    {"cancer": "Ovarian", "name": "📍 FRAmework-01", "pharma": "Eli Lilly", "drug": "LY4170156 + Bevacizumab", "pos": "R-TX", "sub_pos": ["PROC (Resistant Recur)"], "type": "Ongoing",
     "popover_summary": "FRα ADC 併用血管新生抑制劑：旨在透過協同作用提升藥物於腫瘤內的滲透深度。",
     "rationale": "利用 LY4170156 (FRα ADC) 的精準標靶與 Bevacizumab (anti-VEGF) 調節腫瘤血管之特性產生協同作用 (Synergy)，增強 ADC 在基質豐富腫瘤中的殺傷效力。",
     "regimen": "LY4170156 3mg/kg IV + Bevacizumab 15mg/kg IV Q3W。",
     "inclusion": ["經中央檢測確認 FRα 表達陽性。", "High-grade Serous / Carcinosarcoma 卵巢癌。", "最後一劑鉑類後 90–180 天內進展 (PROC)。"],
     "exclusion": ["曾使用過 Topoisomerase I 抑制劑類 ADC (如 Enhertu)。", "活動性間質性肺病 (ILD)。"], "results": "Phase 3 recruitment ongoing (NCT06536348)."},
]

# --- 3. 動態模型與 AI 修復 ---
def get_gemini_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target_model = next((m for m in available_models if 'gemini-1.5-flash' in m), None)
        if not target_model:
            target_model = next((m for m in available_models if 'gemini-pro' in m), None)
        if target_model: return genai.GenerativeModel(target_model)
    except: return None

# --- 4. 側邊欄 ---
with st.sidebar:
    st.markdown("<h3 style='color: #6A1B9A;'>🤖 AI 實證媒合助理</h3>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    with st.expander("✨ 病歷分析", expanded=True):
        p_notes = st.text_area("輸入病歷摘要", height=200)
        if st.button("🚀 開始媒合"):
            if api_key and p_notes:
                try:
                    genai.configure(api_key=api_key)
                    model = get_gemini_model()
                    prompt = f"分析：{p_notes}。參考實證庫：{all_trials}。請判定患者目前 FIGO 階段，並建議適合的臨床路徑。"
                    st.write(model.generate_content(prompt).text)
                except Exception as e: st.error(f"AI 異常: {e}")

# --- 5. 主頁面：導航地圖 ---
st.markdown("<div class='main-title'>婦癌臨床導航儀表板 (2026 實證與收案全整合)</div>", unsafe_allow_html=True)
cancer_type = st.radio("第一步：選擇癌症類型", ["Endometrial", "Ovarian", "Cervical"], horizontal=True)

# 動態調整欄位數量以配合區塊顯示
cols = st.columns(len(guidelines_nested[cancer_type]))
stages_data = guidelines_nested[cancer_type]

for i, stage in enumerate(stages_data):
    with cols[i]:
        # 圖一修復：深色漸層背景
        st.markdown(f"""<div class='big-stage-card card-{stage['css']}'><div class='big-stage-header header-{stage['css']}'>{stage['header']}</div>""", unsafe_allow_html=True)
        for sub in stage['subs']:
            st.markdown(f"""<div class='sub-block'><div class='sub-block-title'>📘 {sub['title']}</div><div class='sub-block-content'>{sub['content']}</div>""", unsafe_allow_html=True)
            
            # 顯示該區塊對應的試驗
            rel_trials = [t for t in all_trials if t["cancer"] == cancer_type and t["pos"] == stage["id"] and any(s in sub["title"] for s in t["sub_pos"])]
            for t in rel_trials:
                label = t["name"]
                with st.popover(label, use_container_width=True):
                    # 圖三修復：顯示療效結論或族群
                    st.success(f"**核心結論:** {t.get('popover_summary', '詳見詳細看板。')}")
                    # 同步聯動邏輯：點擊後 rerun 並更新 session_state
                    unique_key = f"sync_{t['name']}_{stage['id']}_{sub['title'].replace(' ', '')}"
                    if st.button("📊 同步看板細節", key=unique_key):
                        st.session_state.selected_trial = t['name']
                        st.rerun() # 確保下方 selectbox 即時更新
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 6. 臨床試驗深度數據庫 (同步聯動) ---
st.divider()
st.subheader("📋 臨床研究深度數據庫 (Rationale / Dosing / Survival)")

# 根據目前選擇的癌症過濾選項
filtered_names = [t["name"] for t in all_trials if t["cancer"] == cancer_type]
if not filtered_names: filtered_names = ["無適用項目"]

# 確保 selectbox 的 index 與 session_state 同步
try: current_idx = filtered_names.index(st.session_state.selected_trial)
except: current_idx = 0

selected_name = st.selectbox("🎯 快速選擇或同步切換研究：", filtered_names, index=current_idx, key="trial_selector")
st.session_state.selected_trial = selected_name # 保持手動選擇與同步按鈕的一致性

# 抓取選中數據
t = next((it for it in all_trials if it["name"] == selected_name), all_trials[0])

st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
st.markdown(f"<h2 style='color:#004D40; border-bottom:2px solid #E0E0E0; padding-bottom:10px; font-weight:900;'>📋 {t['name']} 深度數據分析報告</h2>", unsafe_allow_html=True)

r1, r2 = st.columns([1.3, 1])
with r1:
    st.markdown("<div style='background:#E3F2FD; border-left:10px solid #1976D2; padding:15px; border-radius:10px;'><b>💉 Rationale & Regimen (機轉理據與給藥)</b></div>", unsafe_allow_html=True)
    st.write(f"**藥廠:** {t.get('pharma', 'N/A')}")
    st.write(f"**核心介入:** {t['drug']}")
    st.write(f"**詳細給藥方案 (Dosing Protocol):** {t.get('regimen', '詳見 Protocol。')}")
    st.success(f"**科學理據 (Scientific Rationale):** {t.get('rationale', '旨在挑戰現有 SoC 瓶頸。')}")
    
with r2:
    st.markdown("<div style='background:#FFF8E1; border-left:8px solid #FBC02D; padding:15px; border-radius:10px;'><b>📈 Key Outcomes (最新生存與緩解指標)</b></div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style='text-align:center; background:white; padding:15px; border:2px solid #FFE082; border-radius:12px;'>
            <div style='font-size: 14px; color: #795548; font-weight:700; margin-bottom:5px;'>Survival Metrics (PFS/OS/HR)</div>
            <div class='hr-big-val'>{t.get('results', 'Recruiting...')}</div>
        </div>
    """, unsafe_allow_html=True)
    
st.divider()
r3, r4 = st.columns(2)
with r3:
    st.markdown("<div style='background:#E8F5E9; border-left:8px solid #2E7D32; padding:15px; border-radius:10px;'><b>✅ Inclusion Criteria (關鍵納入標準)</b></div>", unsafe_allow_html=True)
    for inc in t.get('inclusion', ['詳見全文。']): st.write(f"• **{inc}**")
with r4:
    st.markdown("<div style='background:#FFEBEE; border-left:8px solid #C62828; padding:15px; border-radius:10px;'><b>❌ Exclusion Criteria (關鍵排除標準)</b></div>", unsafe_allow_html=True)
    for exc in t.get('exclusion', ['詳見全文。']): st.write(f"• **{exc}**")
st.markdown("</div>", unsafe_allow_html=True)
