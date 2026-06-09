"""
Alpha AI ECG — UI Styles Module
All CSS for the dark hospital UI. Call inject_styles() once at app startup.
FONT UPDATE: Added Inter font + brightened all dim text colors for readability.
"""

import streamlit as st


def inject_styles():
    """Inject all Alpha AI ECG CSS into the Streamlit app."""
    st.markdown("""
<style>
  /* ── Google Font: Inter (clean, highly readable) ── */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

  :root {
    --bg-deep: #050b18;
    --bg-dark: #080f1e;
    --bg-card: rgba(10,20,40,0.85);
    --border: rgba(56,130,246,0.18);
    --blue: #3b82f6;
    --blue-bright: #60a5fa;
    --teal: #14b8a6;
    --green: #10b981;
    --amber: #f59e0b;
    --red: #ef4444;
    --purple: #8b5cf6;
    --text: #e2e8f0;
    --text-dim: #94a3b8;
    --glow: 0 0 40px rgba(59,130,246,0.15);
  }

  /* Apply Inter font globally for readability */
  *, html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    margin:0; padding:0; box-sizing:border-box;
  }
  .stApp { background-color: #050b18; }
  [data-testid="stSidebar"] {
      background: linear-gradient(180deg, #0a1020 0%, #050b18 100%);
      border-right: 1px solid rgba(56,130,246,0.18);
  }

  /* ── Header ── */
  .cl-header {
      background: linear-gradient(135deg, #0a1428 0%, #0d1a35 50%, #0a1428 100%);
      border: 1px solid rgba(56,130,246,0.25);
      border-top: 3px solid #3b82f6;
      border-radius: 16px;
      padding: 28px 36px;
      margin-bottom: 24px;
      box-shadow: 0 0 40px rgba(59,130,246,0.1);
  }
  .cl-header h1 { font-size: 32px; font-weight: 800; color: #e2e8f0; margin: 0; letter-spacing: -0.5px; }
  .cl-header h1 span { color: #3b82f6; }
  /* FONT FIX: was #64748b — now brighter for readability */
  .cl-header p  { font-size: 15px; color: #b0bec5; margin: 8px 0 0; font-weight: 500; }
  .cl-badge {
      display: inline-block;
      background: linear-gradient(135deg, #1e3a5f, #1e2d4f);
      color: #60a5fa; font-size: 11px; font-family: 'Inter', monospace;
      padding: 4px 10px; border-radius: 20px; margin-left: 10px;
      border: 1px solid rgba(96,165,250,0.3);
  }

  /* ── Step cards ── */
  .step-card {
      background: linear-gradient(90deg, rgba(59,130,246,0.08) 0%, transparent 100%);
      border: 1px solid rgba(56,130,246,0.15);
      border-left: 3px solid #3b82f6;
      border-radius: 0 10px 10px 0;
      padding: 14px 20px;
      margin: 20px 0 14px;
  }
  /* FONT FIX: was font-size 10px — now 12px and brighter */
  .step-num { font-size: 12px; font-weight: 700; color: #60a5fa; letter-spacing: 2px; margin-right: 10px; }
  .step-title { font-size: 15px; font-weight: 700; color: #e2e8f0; }

  /* ── Metric boxes ── */
  .metric-row { display: flex; gap: 12px; flex-wrap: wrap; margin: 12px 0; }
  .metric-box {
      flex: 1; min-width: 120px;
      background: linear-gradient(135deg, #0a1428 0%, #0d1a35 100%);
      border: 1px solid rgba(56,130,246,0.2);
      border-radius: 12px; padding: 16px 20px; text-align: center;
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
  }
  /* FONT FIX: was #475569 (too dark) — now #94a3b8 (readable) */
  .metric-box .m-label { font-size: 11px; color: #94a3b8; font-weight: 600; letter-spacing: 1.5px; margin-bottom: 6px; text-transform: uppercase; }
  .metric-box .m-val   { font-size: 26px; font-weight: 800; color: #e2e8f0; }
  /* FONT FIX: was #64748b — now #94a3b8 */
  .metric-box .m-unit  { font-size: 13px; font-weight: 500; color: #94a3b8; margin-left: 2px; }
  /* FONT FIX: was #334155 (nearly invisible) — now #7c90a8 */
  .metric-box .m-sub   { font-size: 11px; color: #7c90a8; margin-top: 4px; }

  /* ── Alert boxes ── */
  .info-box    { background: rgba(14,30,53,0.8); border: 1px solid rgba(30,58,95,0.8); border-radius: 10px; padding: 12px 16px; font-size: 14px; color: #93c5fd; margin: 10px 0; line-height: 1.6; }
  .warn-box    { background: rgba(31,24,0,0.8); border: 1px solid rgba(61,46,0,0.8); border-radius: 10px; padding: 12px 16px; font-size: 14px; color: #fcd34d; margin: 10px 0; line-height: 1.6; }
  .success-box { background: rgba(7,26,15,0.8); border: 1px solid rgba(15,61,30,0.8); border-radius: 10px; padding: 12px 16px; font-size: 14px; color: #4ade80; margin: 10px 0; line-height: 1.6; }
  .danger-box  { background: rgba(26,8,8,0.8); border: 1px solid rgba(61,16,16,0.8); border-radius: 10px; padding: 12px 16px; font-size: 14px; color: #f87171; margin: 10px 0; line-height: 1.6; }

  /* ── Rhythm cards ── */
  .rhythm-card { border-radius: 14px; padding: 24px 28px; margin: 14px 0; border: 1px solid; }
  /* FONT FIX: was opacity .5 (hard to read) — now .85 and 12px */
  .rhythm-card .r-label { font-size: 12px; font-weight: 600; letter-spacing: 2px; opacity: .85; margin-bottom: 10px; text-transform: uppercase; }
  .rhythm-card .r-name  { font-size: 30px; font-weight: 800; margin-bottom: 4px; }
  /* FONT FIX: was opacity .6 — now .9 and 14px */
  .rhythm-card .r-abbr  { font-size: 14px; font-weight: 600; opacity: .9; margin-bottom: 12px; }
  .rhythm-card .r-desc  { font-size: 15px; line-height: 1.75; opacity: .95; }
  .rhythm-normal  { background: rgba(7,26,15,0.9); border-color: rgba(16,61,30,0.8); color: #4ade80; }
  .rhythm-tachy   { background: rgba(26,8,8,0.9); border-color: rgba(61,16,16,0.8); color: #f87171; }
  .rhythm-brady   { background: rgba(14,30,53,0.9); border-color: rgba(30,58,95,0.8); color: #93c5fd; }
  .rhythm-afib    { background: rgba(31,24,0,0.9); border-color: rgba(61,46,0,0.8); color: #fcd34d; }
  .rhythm-pvc     { background: rgba(22,10,31,0.9); border-color: rgba(46,16,64,0.8); color: #c4b5fd; }
  .rhythm-unknown { background: rgba(15,19,32,0.9); border-color: rgba(30,37,56,0.8); color: #94a3b8; }

  /* ── Feature pills ── */
  .feat-row  { display: flex; gap: 10px; flex-wrap: wrap; margin: 12px 0; }
  .feat-pill {
      background: linear-gradient(135deg, #0a1428 0%, #0d1a35 100%);
      border: 1px solid rgba(56,130,246,0.2);
      border-radius: 10px; padding: 10px 14px; font-size: 13px; color: #e2e8f0;
      text-align: center; flex: 1; min-width: 95px;
  }
  /* FONT FIX: was #475569 9px (nearly invisible) — now #94a3b8 11px */
  .feat-pill .fp-l { color: #94a3b8; font-size: 11px; font-weight: 600; letter-spacing: 1.5px; margin-bottom: 4px; text-transform: uppercase; }
  .feat-pill .fp-v { font-size: 20px; font-weight: 700; }

  /* ── Confidence bar ── */
  .conf-bg { background: rgba(30,37,56,0.8); border-radius: 6px; height: 8px; margin: 4px 0; }
  .conf-fill { height: 8px; border-radius: 6px; transition: width 0.5s ease; }

  /* ── Chat ── */
  /* FONT FIX: was 13px — now 14px and better line-height */
  .chat-msg { padding: 14px 18px; border-radius: 12px; margin: 8px 0; font-size: 14px; line-height: 1.75; }
  .chat-user { background: rgba(14,30,53,0.8); border: 1px solid rgba(30,58,95,0.6); color: #e2e8f0; }
  .chat-ai   { background: rgba(7,26,15,0.8); border: 1px solid rgba(15,61,30,0.6); color: #d1fae5; }

  /* ── Sidebar ── */
  .sidebar-logo { font-size: 26px; font-weight: 900; color: #e2e8f0; margin-bottom: 4px; }
  .sidebar-logo span { color: #3b82f6; }
  /* FONT FIX: was 11px — now 12px */
  .sidebar-section { font-size: 12px; font-weight: 700; color: #60a5fa; letter-spacing: 2px; text-transform: uppercase; margin: 16px 0 8px; }

  /* ── Stat / dash cards ── */
  .stat-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 14px; margin: 16px 0; }
  .stat-card {
      background: linear-gradient(135deg, #0a1428 0%, #0d1a35 100%);
      border: 1px solid rgba(56,130,246,0.2);
      border-radius: 14px; padding: 20px 24px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
  }
  /* FONT FIX: was #475569 11px — now #94a3b8 12px */
  .stat-card .sc-label { font-size: 12px; color: #94a3b8; font-weight: 600; letter-spacing: 1.5px; text-transform: uppercase; }
  .stat-card .sc-val   { font-size: 32px; font-weight: 800; color: #e2e8f0; margin: 6px 0 2px; }
  /* FONT FIX: was #334155 (nearly invisible) — now #7c90a8 */
  .stat-card .sc-sub   { font-size: 12px; color: #7c90a8; }
  .dash-stat {
      background: rgba(10,20,40,0.85);
      border: 1px solid rgba(56,130,246,0.18);
      border-radius: 14px;
      padding: 20px 18px;
      text-align: center;
  }
  .dash-stat-val { font-size: 32px; font-weight: 800; color: #3b82f6; }
  /* FONT FIX: was #64748b 11px — now #94a3b8 12px */
  .dash-stat-lbl { font-size: 12px; color: #94a3b8; margin-top: 4px; letter-spacing: 1px; text-transform: uppercase; font-weight: 600; }
  /* FONT FIX: was #475569 — now #7c90a8 */
  .dash-stat-sub { font-size: 12px; color: #7c90a8; margin-top: 6px; }

  /* ── Role badges ── */
  /* FONT FIX: was 11px — now 12px for readability */
  .role-badge-admin   { background:rgba(239,68,68,0.15);  color:#ef4444; border:1px solid rgba(239,68,68,0.3);  padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
  .role-badge-doctor  { background:rgba(59,130,246,0.15); color:#60a5fa; border:1px solid rgba(59,130,246,0.3); padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
  .role-badge-patient { background:rgba(16,185,129,0.15); color:#10b981; border:1px solid rgba(16,185,129,0.3); padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }

  /* ── Tab styling ── */
  [data-baseweb="tab-list"] { background: transparent; border-bottom: 1px solid rgba(56,130,246,0.15); }
  /* FONT FIX: was #64748b — now #94a3b8 */
  [data-baseweb="tab"] { color: #94a3b8 !important; font-weight: 600; font-size: 14px !important; }
  [aria-selected="true"] { color: #3b82f6 !important; border-bottom: 2px solid #3b82f6 !important; }

  /* ── Download buttons ── */
  [data-testid="stDownloadButton"] button {
      background: linear-gradient(135deg, #0a1428 0%, #0d1a35 100%) !important;
      border: 1px solid rgba(56,130,246,0.3) !important;
      color: #e2e8f0 !important; border-radius: 10px !important; width: 100%;
      font-weight: 600 !important; font-size: 14px !important;
  }
  [data-testid="stDownloadButton"] button:hover {
      border-color: #3b82f6 !important; color: #60a5fa !important;
      box-shadow: 0 0 15px rgba(59,130,246,0.2) !important;
  }

  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

  /* ── Buttons ── */
  .stButton > button {
      background: linear-gradient(135deg, #1e3a5f 0%, #1e2d4f 100%) !important;
      border: 1px solid rgba(59,130,246,0.4) !important;
      color: #e2e8f0 !important; border-radius: 10px !important;
      font-weight: 600 !important; font-size: 14px !important;
  }
  .stButton > button:hover {
      background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%) !important;
      border-color: #3b82f6 !important; box-shadow: 0 0 20px rgba(59,130,246,0.3) !important;
  }

  /* ── Login ── */
  .login-wrap { max-width:460px; margin:60px auto 0; padding:0 16px; }
  .login-card {
      background:rgba(10,20,40,0.92);
      border:1px solid rgba(59,130,246,0.25);
      border-top:3px solid #3b82f6;
      border-radius:18px; padding:40px 36px 32px;
      box-shadow:0 0 60px rgba(59,130,246,0.12);
  }
  .login-logo { text-align:center; font-size:48px; margin-bottom:6px; }
  .login-title { text-align:center; font-size:24px; font-weight:800; color:#e2e8f0; margin-bottom:4px; }
  /* FONT FIX: was #64748b — now #94a3b8 */
  .login-sub { text-align:center; font-size:14px; color:#94a3b8; margin-bottom:24px; font-weight:500; }
  .demo-creds {
      background:rgba(15,25,50,0.6); border:1px solid rgba(59,130,246,0.12);
      border-radius:10px; padding:12px 16px; margin-top:16px;
  }
  /* FONT FIX: was #64748b 11px — now #94a3b8 13px */
  .demo-creds p { font-size:13px; color:#94a3b8; margin:4px 0; }
  /* FONT FIX: was #94a3b8 — now #cbd5e1 (brighter) */
  .demo-creds b { color:#cbd5e1; font-weight:700; }

  /* ── Profile card ── */
  .profile-card {
      background:rgba(10,20,40,0.85); border:1px solid rgba(56,130,246,0.18);
      border-radius:14px; padding:24px; margin-bottom:18px;
      font-size:15px; color:#e2e8f0; line-height:2;
  }

  /* ── Feedback card ── */
  .feedback-card {
      background:rgba(7,26,15,0.5); border:1px solid rgba(16,185,129,0.2);
      border-radius:10px; padding:14px 18px; margin-top:8px;
      font-size:14px; color:#d1fae5; line-height:1.7;
  }
  /* FONT FIX: was #475569 10px (nearly invisible) — now #94a3b8 12px */
  .feedback-meta { font-size:12px; color:#94a3b8; margin-bottom:6px; font-weight:600; }
</style>
""", unsafe_allow_html=True)
