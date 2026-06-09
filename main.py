"""
╔══════════════════════════════════════════════════════════════════╗
║                      Alpha AI ECG                                ║
║   Role-Based ECG Analysis Platform — Patient · Doctor · Admin    ║
║              Powered by OpenCV + scipy + Groq AI                 ║
║                       Version 2.0                                ║
╚══════════════════════════════════════════════════════════════════╝

Run with:
    streamlit run main.py
"""

import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import auth as _auth
from ui.styles import inject_styles
from dashboards import patient_dash, doctor_dash, admin_dash

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Alpha AI ECG — ECG Analysis Platform",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# INJECT STYLES
# ─────────────────────────────────────────────────────────────────────────────
inject_styles()

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE DEFAULTS
# ─────────────────────────────────────────────────────────────────────────────
_defaults = {
    "auth_token":           None,
    "auth_user":            None,
    "login_error":          "",
    "groq_api_key_override":"",
    # ECG analysis state (shared between analysis + chatbot)
    "analysis_done":        False,
    "ecg_context":          "",
    "rhythm_key":           None,
    "features":             None,
    "signals":              None,
    "waveform_png":         None,
    "classification_png":   None,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─────────────────────────────────────────────────────────────────────────────
# AUTH HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def current_user():
    if not st.session_state.auth_token:
        return None
    data = _auth.verify_token(st.session_state.auth_token)
    if not data:
        st.session_state.auth_token = None
        return None
    return st.session_state.auth_user


def do_logout():
    for key in ["auth_token", "auth_user", "analysis_done", "ecg_context",
                "rhythm_key", "features", "signals", "waveform_png", "classification_png"]:
        st.session_state[key] = None if "token" in key or "user" in key else (False if key == "analysis_done" else "")
    st.session_state.auth_token = None
    st.session_state.auth_user  = None
    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN PAGE
# ─────────────────────────────────────────────────────────────────────────────
def show_login_page():
    st.markdown('<div class="login-wrap">', unsafe_allow_html=True)
    st.markdown("""
    <div class="login-card">
      <div class="login-logo">🫀</div>
      <div class="login-title"><span style="color:#3b82f6;">Alpha AI</span> ECG</div>
      <div class="login-sub">ECG Analysis Platform — Secure Login</div>
    </div>
    """, unsafe_allow_html=True)

    tab_login, tab_register = st.tabs(["🔐  Sign In", "📝  Register"])

    # ── Sign In ───────────────────────────────────────────────────────────────
    with tab_login:
        st.markdown("#### Select Your Role")
        role_col1, role_col2, role_col3 = st.columns(3)
        with role_col1:
            if st.button("🛡️ Admin", use_container_width=True, key="role_admin"):
                st.session_state["login_role_hint"] = "admin"
        with role_col2:
            if st.button("👨‍⚕️ Doctor", use_container_width=True, key="role_doctor"):
                st.session_state["login_role_hint"] = "doctor"
        with role_col3:
            if st.button("🧑 Patient", use_container_width=True, key="role_patient"):
                st.session_state["login_role_hint"] = "patient"

        role_hint = st.session_state.get("login_role_hint", "doctor")
        demo = {
            "admin":   ("admin",   "admin123"),
            "doctor":  ("doctor1", "doctor123"),
            "patient": ("patient1","patient123"),
        }
        hint_u, _ = demo[role_hint]

        st.markdown("---")
        username = st.text_input("Username", placeholder=f"e.g. {hint_u}", key="li_user")
        password = st.text_input("Password", type="password", placeholder="Enter password", key="li_pass")

        if st.button("🔐  Sign In", use_container_width=True, type="primary", key="signin_btn"):
            if not username or not password:
                st.error("Please enter username and password")
            else:
                result = _auth.login(username.strip(), password)
                if result:
                    st.session_state.auth_token = result["token"]
                    st.session_state.auth_user  = result["user"]
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")

        st.markdown("""
        <div class="demo-creds">
          <p><b>Demo — Admin &nbsp;&nbsp;</b> admin / admin123</p>
          <p><b>Demo — Doctor &nbsp;</b> doctor1 / doctor123</p>
          <p><b>Demo — Patient</b> patient1 / patient123</p>
        </div>
        """, unsafe_allow_html=True)

    # ── Register ──────────────────────────────────────────────────────────────
    with tab_register:
        st.markdown("#### Create New Account")
        st.info("ℹ️ Patients and Doctors can self-register. Admin accounts are created by the administrator.")
        r_role   = st.selectbox("Register as", ["patient", "doctor"], key="reg_role")
        r_full   = st.text_input("Full Name", key="reg_name")
        r_user   = st.text_input("Username", key="reg_user")
        r_email  = st.text_input("Email", key="reg_email")
        r_pass   = st.text_input("Password (min 6 chars)", type="password", key="reg_pass")
        r_pass2  = st.text_input("Confirm Password", type="password", key="reg_pass2")
        r_spec   = r_pid = ""
        r_age    = 25
        r_gender = "Male"
        if r_role == "doctor":
            r_spec = st.text_input("Specialization", placeholder="e.g. Cardiologist", key="reg_spec")
        else:
            r_pid    = st.text_input("Patient ID (optional)", placeholder="e.g. PT-003", key="reg_pid")
            r_age    = st.number_input("Age", 1, 120, 30, key="reg_age")
            r_gender = st.selectbox("Gender", ["Male", "Female", "Other"], key="reg_gender")

        if st.button("📝  Create Account", use_container_width=True, type="primary", key="register_btn"):
            if not all([r_full, r_user, r_email, r_pass]):
                st.error("All fields are required")
            elif r_pass != r_pass2:
                st.error("Passwords do not match")
            elif len(r_pass) < 6:
                st.error("Password must be at least 6 characters")
            else:
                ok, msg = _auth.create_user(
                    r_user.strip(), r_pass, r_role, r_full, r_email,
                    r_spec if r_role == "doctor" else None,
                    r_pid  if r_role == "patient" else None,
                    r_age  if r_role == "patient" else None,
                    r_gender if r_role == "patient" else None,
                )
                if ok:
                    st.success(f"✅ Account created! You can now sign in as **{r_user}**")
                else:
                    st.error(f"❌ {msg}")

    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR (shown when logged in)
# ─────────────────────────────────────────────────────────────────────────────
def render_sidebar(user: dict):
    with st.sidebar:
        st.markdown(
            '<div class="sidebar-logo">🫀 <span>Alpha</span> AI ECG</div>',
            unsafe_allow_html=True
        )
        role_badge_color = {
            "admin":   "#ef4444",
            "doctor":  "#3b82f6",
            "patient": "#10b981",
        }.get(user["role"], "#64748b")

        st.markdown(f"""
        <div style="margin:8px 0 16px;">
          <div style="font-size:14px;font-weight:700;color:#e2e8f0;">{user["full_name"]}</div>
          <div style="font-size:11px;color:{role_badge_color};font-weight:600;text-transform:uppercase;letter-spacing:1px;">{user["role"]}</div>
          <div style="font-size:11px;color:#475569;">{user.get("email","")}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        # Groq status
        groq_key = os.environ.get("GROQ_API_KEY", "")
        groq_active = groq_key and groq_key not in ("gsk_YOUR_GROQ_API_KEY_HERE", "")
        st.markdown('<div class="sidebar-section">🤖 AI Assistant</div>', unsafe_allow_html=True)
        if groq_active:
            st.markdown('<div class="success-box">✓ Groq AI Active — LLaMA-3.3-70B</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="warn-box">⚠ Set GROQ_API_KEY to enable AI chat</div>', unsafe_allow_html=True)

        # Allow key override
        override = st.text_input(
            "Override Groq Key",
            value=st.session_state.groq_api_key_override,
            type="password",
            placeholder="gsk_...",
            key="sidebar_groq_override",
        )
        if override != st.session_state.groq_api_key_override:
            st.session_state.groq_api_key_override = override

        st.markdown("---")
        st.caption(f"Alpha AI ECG v2.0\n{user['role'].title()} Portal")
        st.markdown("---")
        if st.button("🚪 Sign Out", use_container_width=True, key="logout_btn"):
            do_logout()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN AUTH ROUTER
# ─────────────────────────────────────────────────────────────────────────────
user = current_user()

if user is None:
    show_login_page()
else:
    render_sidebar(user)
    role = user["role"]
    if role == "patient":
        patient_dash.show(user)
    elif role == "doctor":
        doctor_dash.show(user)
    elif role == "admin":
        admin_dash.show(user)
    else:
        st.error("Unknown role. Please contact the administrator.")

# Footer
st.markdown("---")
st.caption("Alpha AI ECG v2.0 · OpenCV + scipy + Groq LLaMA-3.3-70B + ReportLab · Healthcare AI Project 2025")
