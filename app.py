import streamlit as st
import google.generativeai as genai
import pandas as pd

# --- 🏥 婦癌臨床導航與實證圖書館 (2026 極量化專業版) ---
st.set_page_config(page_title="婦癌臨床試驗導航系統", layout="wide")

# 初始化 session_state
if 'selected_trial' not in st.session_state:
    st.session_state.selected_trial = "📚 RUBY (ENGOT-EN6)"

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=Roboto:wght@400;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', 'Roboto', sans-serif;
        background-color: #F4F7F9; color: #1A1A1A;
        font-size: 18px !important;
    }

    .main-title {
        font-size: 38px !important; font-weight: 900; color: #004D40;
        padding: 15px 0; border-bottom: 5px solid #004D40; margin-bottom: 15px;
    }

    /* 強化專屬標籤：DUO 系列與旗艦試驗 */
    .flagship-badge {
        background: #D32F2F; color: white; padding: 2px 8px; border-radius: 4px;
        font-size: 12px; font-weight: 900; margin-right: 5px; vertical-align: middle;
    }

    .big-stage-card {
        border-radius: 12px; margin-bottom: 10px; overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1); background: white;
    }
    .big-stage-header {
        font-size: 22px !important; font-weight: 900; color: white !important;
        padding: 15px; text-align: center;
    }

    /* 階段配色 */
    .card-p-tx { border: 2px solid #2E7D32; } .header-p-tx { background: #2E7D32; }
    .card-p-mt { border: 2px solid #1565C0; } .header-p-mt { background: #1565C0; }
    .card-r-tx { border: 2px solid #C62828; } .header-r-tx { background: #C62828; }
    .card-r-mt { border: 2px solid #6A1B9A; } .header-r-mt { background: #6A1B9A; }

    .sub-block {
        margin: 10px; padding: 12px; border-radius: 8px; background: #F8F9FA;
        border-left: 5px solid #455A64;
    }
    .sub-block-title { font-weight: 900; color: #263238; font-size: 18px; margin-bottom: 5px; }

    /* 按鈕強化 */
    .stPopover button { 
        font-weight: 900 !important; color: #1A1A1A !important;
        border: 2px solid #BDBDBD !important; transition: 0.3s;
    }
    .stPopover button:hover { border-color: #004D40 !important; background: #E0F2F1 !important; }

    /* 深度看板區 */
    .detail-section { background: white; border-radius: 15px; padding: 30px; border: 1px solid #CFD8DC; box-shadow: 0 10px 30px rgba(0,0,0,0.05); }
    .regimen-box { 
        background: #E8F5E9; border-left: 8px solid #2E7D32; padding: 20px; 
        border-radius: 10px; font-size: 17px; line-height: 1.6; font-family: 'Roboto Mono', monospace;
    }
    .hr-big-val { font-size: 32px !important; font-weight: 900; color: #D84315; }
    </style>
    """, unsafe_allow_html=True)

# --- 數據庫：納入 DUO-O 並標記 Flagship ---
all_trials_db = [
    # === Endometrial ===
    {
        "cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["dMMR / MSI-H / MMRd"], 
        "name": "📚 RUBY (ENGOT-EN6)", "pharma": "GSK", "drug": "Dostarlimab + Carbo/Pacli", 
        "flagship": False,
        "regimen": """<b>1. 誘導期 (Induction):</b> Dostarlimab 500 mg IV Q3W + Carboplatin (AUC 5) + Paclitaxel (175 mg/m²) 共 6 個週期。<br>
                      <b>2. 維持期 (Maintenance):</b> Dostarlimab 1000 mg IV Q6W，持續給藥直到 3 年或疾病進展。""",
        "outcomes": "dMMR PFS HR 0.28 (0.16-0.50); mOS 未達到 vs 18.3m (HR 0.32)",
        "inclusion": ["Stage III/IV 或首次復發 EC", "可測量病灶 (RECIST 1.1)", "ECOG 0-1"],
        "exclusion": ["曾用過全身性化療 (除外新輔助)", "活動性自體免疫疾病", "需要類固醇治療的間質性肺病"]
    },
    {
        "cancer": "Endometrial", "pos": "P-TX", "sub_pos": ["pMMR / NSMP / MSS"], 
        "name": "🔥 DUO-E (ENGOT-EN9)", "pharma": "AstraZeneca", "drug": "Durvalumab + CP ± Olaparib", 
        "flagship": True,
        "regimen": """<b>1. 誘導期 (Induction):</b> Durvalumab 1120 mg IV Q3W + Carboplatin (AUC 5-6) + Paclitaxel (175 mg/m²) 共 6 週期。<br>
                      <b>2. 維持期 (Maintenance):</b> <br>
                      - Arm 2: Durvalumab 1500 mg IV Q4W 直到疾病進展。<br>
                      - Arm 3: Durvalumab 1500 mg IV Q4W + Olaparib 300 mg BID (口服) 直到疾病進展。""",
        "outcomes": "pMMR (Durva+Ola): PFS HR 0.57 (0.42-0.79); dMMR (Durva): PFS HR 0.42",
        "inclusion": ["新診斷 Stage III/IV 或復發性 EC", "所有組織學分型 (含肉瘤)", "MMR 狀態已知"],
        "exclusion": ["先前接受過 IO 治療", "腦轉移未受控者", "CTCAE Grade >2 的剩餘毒性"]
    },
    # === Ovarian ===
    {
        "cancer": "Ovarian", "pos": "P-TX", "sub_pos": ["HGSC / Endometrioid"], 
        "name": "🔥 DUO-O (ENGOT-ov60)", "pharma": "AstraZeneca", "drug": "Durvalumab + CP + Bev ± Olaparib", 
        "flagship": True,
        "regimen": """<b>1. 誘導期 (Induction):</b> Durvalumab 1120 mg IV Q3W + Carboplatin (AUC 5/6) + Paclitaxel (175 mg/m²) + Bevacizumab 15 mg/kg Q3W (共 6 週期)。<br>
                      <b>2. 維持期 (Maintenance):</b> <br>
                      - Durvalumab 1500 mg IV Q4W (持續 24 個月) + Bevacizumab 15 mg/kg Q3W (持續 15 個月) + Olaparib 300 mg BID (持續 24 個月)。""",
        "outcomes": "Non-tBRCAm HRD(+): PFS HR 0.49 (0.34-0.69); ITT PFS HR 0.63",
        "inclusion": ["新診斷 FIGO Stage III-IV 高級別上皮性卵巢癌", "接受過 PDS 或計畫 IDS", "無 BRCA 突變者特別關注"],
        "exclusion": ["非上皮性腫瘤", "先前有腸梗阻病史", "活動性發炎性腸道疾病"]
    },
    {
        "cancer": "Ovarian", "pos": "R-TX", "sub_pos": ["PROC (Resistant Recur)"], 
        "name": "📚 MIRASOL (GOG-3045)", "pharma": "ImmunoGen", "drug": "Mirvetuximab Soravtansine", 
        "flagship": False,
        "regimen": """<b>1. 治療方案:</b> Mirvetuximab 6.0 mg/kg (基於調整後體重 AIBW) IV Q3W (每 21 天一次)。<br>
                      <b>2. 劑量調整:</b> 若發生角膜病變 (Keratopathy)，應暫停並降階至 5.0 mg/kg 或 4.0 mg/kg。""",
        "outcomes": "mOS: 16.4m vs 12.7m (HR 0.67); ORR: 42.3% vs 15.9%",
        "inclusion": ["FRα 高表達 (IHC PS2+ ≥ 75%)", "1-3 前線治療方案", "鉑類耐藥 (PFI < 6m)"],
        "exclusion": ["活動性角膜疾病或需長期配戴隱形眼鏡者", "未治療的 CNS 轉移"]
    },
    # === Cervical ===
    {
        "cancer": "Cervical", "pos": "P-TX", "sub_pos": ["Locally Advanced (CCRT)"], 
        "name": "📚 KEYNOTE-A18", "pharma": "MSD", "drug": "Pembrolizumab + CCRT", 
        "flagship": False,
        "regimen": """<b>1. 同步期:</b> Pembrolizumab 200 mg IV Q3W (共 5 劑) + Cisplatin 40 mg/m² (每週一次) + 體外放射線 (EBRT) 與近接放射 (Brachytherapy)。<br>
                      <b>2. 維持期:</b> Pembrolizumab 400 mg IV Q6W (共 15 劑)。""",
        "outcomes": "36m OS: 82.6% vs 74.8% (HR 0.67); PFS HR 0.70",
        "inclusion": ["新診斷 Stage IB2-IIB LN(+) 或 Stage III-IVA", "ECOG 0-1", "肝腎功能正常"],
        "exclusion": ["曾接受過盆腔放療", "活動性全身免疫疾病"]
    }
]

# --- UI 邏輯 ---
st.markdown("<div class='main-title'>婦癌臨床導航儀表板 (2026 極量化數據版)</div>", unsafe_allow_html=True)

cancer_type = st.radio("第一步：選擇癌症類型", ["Endometrial", "Ovarian", "Cervical"], horizontal=True)

# 渲染導航卡片
import guidelines_data # 假設您將 guidelines_nested 移至此或保持在原處
# (為了縮短代碼長度，此處 guidelines_nested 延用您原本的 dictionary 結構)
from trial_guidelines import guidelines_nested # 示意

cols = st.columns(4)
for i, stage in enumerate(guidelines_nested[cancer_type]):
    with cols[i]:
        st.markdown(f"""<div class='big-stage-card card-{stage['css']}'><div class='big-stage-header header-{stage['css']}'>{stage['header']}</div>""", unsafe_allow_html=True)
        for sub in stage['subs']:
            st.markdown(f"""<div class='sub-block'><div class='sub-block-title'>📘 {sub['title']}</div>""", unsafe_allow_html=True)
            
            # 過濾對應試驗並檢查旗艦標記
            rel_trials = [t for t in all_trials_db if t["cancer"] == cancer_type and t["pos"] == stage["id"] and any(s in sub["title"] for s in t["sub_pos"])]
            for t in rel_trials:
                badge = "<span class='flagship-badge'>🔥 FLAGSHIP</span>" if t.get("flagship") else ""
                label = f"{t['name']}"
                with st.popover(f"{badge} {label}", use_container_width=True):
                    st.write(f"**核心藥物:** {t['drug']}")
                    if st.button("📊 同步看板細節", key=f"btn_{t['name']}"):
                        st.session_state.selected_trial = t['name']
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 深度看板 (這部分我特別強化了給藥方案的顯示) ---
st.divider()
selected_trial = next((t for t in all_trials_db if t["name"] == st.session_state.selected_trial), all_trials_db[0])

st.markdown(f"<div class='detail-section'>", unsafe_allow_html=True)
st.markdown(f"<h2 style='color:#004D40; font-weight:900;'>📋 {selected_trial['name']} 深度分析 (2026 最新更新)</h2>", unsafe_allow_html=True)

r1, r2 = st.columns([1.5, 1])
with r1:
    st.markdown("### 💉 臨床給藥方案 (Precise Regimen Protocol)")
    st.markdown(f"<div class='regimen-box'>{selected_trial['regimen']}</div>", unsafe_allow_html=True)
    
    st.markdown("### ✅ 關鍵納入標準 (Inclusion)")
    for inc in selected_trial['inclusion']: st.write(f"• {inc}")

with r2:
    st.markdown("### 📈 生存數據摘要 (Primary Outcomes)")
    st.markdown(f"""
        <div style='background:#FFF8E1; padding:20px; border:2px solid #FFE082; border-radius:15px; text-align:center;'>
            <div style='color:#795548; font-weight:bold;'>Survival Metrics & HR</div>
            <div class='hr-big-val'>{selected_trial['outcomes']}</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### ❌ 關鍵排除標準 (Exclusion)")
    for exc in selected_trial['exclusion']: st.write(f"• {exc}")

st.markdown("</div>", unsafe_allow_html=True)
