"""
Alpha AI ECG — Admin Dashboard
Admin-only panel: user management, role changes, system records view.
NO ECG analysis. NO chatbot.
"""

import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import auth as _auth


def show(user: dict):
    stats = _auth.get_stats()
    all_users = _auth.get_all_users()
    ecg_records = _auth.get_ecg_records()

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="cl-header">
      <h1>🛡️ Admin <span>Panel</span></h1>
      <p>Welcome, <b>{user['full_name']}</b> · Alpha AI ECG — System Management</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Stats row ─────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="dash-stat"><div class="dash-stat-val" style="color:#3b82f6">{stats["doctors"]}</div><div class="dash-stat-lbl">Doctors</div><div class="dash-stat-sub">Active</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="dash-stat"><div class="dash-stat-val" style="color:#10b981">{stats["patients"]}</div><div class="dash-stat-lbl">Patients</div><div class="dash-stat-sub">Registered</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="dash-stat"><div class="dash-stat-val" style="color:#f59e0b">{stats["ecg_total"]}</div><div class="dash-stat-lbl">ECG Records</div><div class="dash-stat-sub">Total</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="dash-stat"><div class="dash-stat-val" style="color:#8b5cf6">{stats.get("feedback_total",0)}</div><div class="dash-stat-lbl">Feedbacks</div><div class="dash-stat-sub">By Doctors</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab_users, tab_roles, tab_ecg, tab_add = st.tabs([
        "👥  All Users", "🔄  Manage Roles", "📊  System Records", "➕  Add User"
    ])

    # ── Tab 1: All Users ──────────────────────────────────────────────────────
    with tab_users:
        st.markdown("#### User Management")
        role_filter = st.selectbox("Filter by role", ["All", "admin", "doctor", "patient"], key="adm_filter")
        filtered = [u for u in all_users if role_filter == "All" or u["role"] == role_filter]

        for u in filtered:
            badge_cls = f"role-badge-{u['role']}"
            col_a, col_b, col_c = st.columns([4, 2, 1])
            with col_a:
                status = "🟢" if u["is_active"] else "🔴"
                st.markdown(f"{status} **{u['full_name']}** (`{u['username']}`)")
                st.caption(f"{u.get('email','')} · {u.get('specialization') or u.get('patient_id','')}")
            with col_b:
                st.markdown(f'<span class="{badge_cls}">{u["role"].upper()}</span>', unsafe_allow_html=True)
                st.caption(f"Joined: {u['created_at'][:10]}")
            with col_c:
                if u["username"] != user["username"] and u["is_active"]:
                    if st.button("🗑️", key=f"del_{u['username']}", help="Deactivate user"):
                        _auth.delete_user(u["username"])
                        st.success(f"User {u['username']} deactivated")
                        st.rerun()
            st.divider()

    # ── Tab 2: Manage Roles ───────────────────────────────────────────────────
    with tab_roles:
        st.markdown("#### Change User Roles")
        st.info("💡 You can change a patient to doctor or vice versa. Admin accounts are protected.")

        non_admin = [u for u in all_users if u["role"] != "admin" and u["is_active"]]
        if non_admin:
            for u in non_admin:
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.markdown(f"**{u['full_name']}** (`{u['username']}`)")
                    badge_cls = f"role-badge-{u['role']}"
                    st.markdown(f'<span class="{badge_cls}">{u["role"].upper()}</span>', unsafe_allow_html=True)
                with col2:
                    new_role = st.selectbox(
                        "New role",
                        ["patient", "doctor"],
                        index=0 if u["role"] == "patient" else 1,
                        key=f"role_sel_{u['username']}",
                        label_visibility="collapsed",
                    )
                with col3:
                    if st.button("Update", key=f"role_upd_{u['username']}"):
                        if new_role != u["role"]:
                            ok = _auth.update_user_role(u["username"], new_role)
                            if ok:
                                st.success(f"✅ {u['username']} → {new_role}")
                                st.rerun()
                        else:
                            st.info("No change.")
                st.divider()
        else:
            st.info("No non-admin users found.")

    # ── Tab 3: System Records ─────────────────────────────────────────────────
    with tab_ecg:
        st.markdown("#### ECG Analysis Records — Read Only")
        if ecg_records:
            df_ecg = pd.DataFrame(ecg_records)
            display_cols = ["created_at", "patient_username", "doctor_username", "rhythm", "heart_rate", "filename"]
            display_cols = [c for c in display_cols if c in df_ecg.columns]
            st.dataframe(df_ecg[display_cols].rename(columns={
                "created_at": "Date", "patient_username": "Patient",
                "doctor_username": "Doctor", "rhythm": "Rhythm",
                "heart_rate": "HR (bpm)", "filename": "File"
            }), use_container_width=True)

            if stats.get("rhythm_counts"):
                st.markdown("#### Rhythm Distribution")
                fig, ax = plt.subplots(figsize=(6, 3), facecolor="#050b18")
                ax.set_facecolor("#080f1e")
                rhythms = list(stats["rhythm_counts"].keys())
                counts = list(stats["rhythm_counts"].values())
                colors_list = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#14b8a6"]
                ax.bar(rhythms, counts, color=colors_list[:len(rhythms)],
                       edgecolor="#1e3a5f", linewidth=0.5)
                ax.set_xlabel("Rhythm", color="#94a3b8")
                ax.set_ylabel("Count", color="#94a3b8")
                ax.tick_params(colors="#94a3b8")
                for spine in ax.spines.values():
                    spine.set_edgecolor("#1e3a5f")
                buf2 = io.BytesIO()
                fig.savefig(buf2, format="png", dpi=80, bbox_inches="tight", facecolor="#050b18")
                plt.close(fig)
                st.image(buf2.getvalue())
        else:
            st.info("No ECG records in the system yet.")

    # ── Tab 4: Add User ───────────────────────────────────────────────────────
    with tab_add:
        st.markdown("#### Create New User Account")
        na_role = st.selectbox("Role", ["doctor", "patient", "admin"], key="na_role")
        na_name = st.text_input("Full Name", key="na_name")
        na_user = st.text_input("Username", key="na_user")
        na_email = st.text_input("Email", key="na_email")
        na_pass = st.text_input("Password", type="password", key="na_pass")
        na_spec = na_pid = ""
        na_age, na_gender = 30, "Male"
        if na_role == "doctor":
            na_spec = st.text_input("Specialization", key="na_spec")
        elif na_role == "patient":
            na_pid = st.text_input("Patient ID", key="na_pid")
            na_age = st.number_input("Age", 1, 120, 30, key="na_age")
            na_gender = st.selectbox("Gender", ["Male", "Female", "Other"], key="na_gender")

        if st.button("➕ Create User", type="primary", key="create_user_btn"):
            if not all([na_name, na_user, na_email, na_pass]):
                st.error("All fields are required")
            else:
                ok, msg = _auth.create_user(
                    na_user, na_pass, na_role, na_name, na_email,
                    na_spec or None, na_pid or None,
                    na_age if na_role == "patient" else None,
                    na_gender if na_role == "patient" else None,
                )
                if ok:
                    st.success(f"✅ {msg}")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
