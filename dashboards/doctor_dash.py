"""
Alpha AI ECG — Doctor Dashboard
Doctors view all patient ECG reports and add clinical feedback.
NO admin panel. NO chatbot.
"""

import streamlit as st
import pandas as pd
import auth as _auth


def show(user: dict):
    my_records = _auth.get_ecg_records(user["username"], role="doctor")
    all_records = _auth.get_ecg_records()          # all records for viewing
    patients    = _auth.get_all_users(role="patient")

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="cl-header">
      <h1>👨‍⚕️ <span>Doctor</span> Dashboard</h1>
      <p>Welcome, <b>{user['full_name']}</b> · {user.get('specialization','Cardiologist')} · Alpha AI ECG</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Stats ─────────────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="dash-stat"><div class="dash-stat-val" style="color:#3b82f6">{len(all_records)}</div><div class="dash-stat-lbl">Total ECG Reports</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="dash-stat"><div class="dash-stat-val" style="color:#10b981">{len(patients)}</div><div class="dash-stat-lbl">Total Patients</div></div>', unsafe_allow_html=True)
    with c3:
        feedbacks = _auth.get_all_feedback_by_doctor(user["username"])
        st.markdown(f'<div class="dash-stat"><div class="dash-stat-val" style="color:#f59e0b">{len(feedbacks)}</div><div class="dash-stat-lbl">My Feedbacks Given</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab_reports, tab_feedback, tab_patients = st.tabs([
        "📊  All ECG Reports", "💬  Add Feedback", "👥  Patients"
    ])

    # ── Tab 1: All ECG Reports ────────────────────────────────────────────────
    with tab_reports:
        st.markdown("#### Patient ECG Analysis Records")

        if not all_records:
            st.info("No ECG records in the system yet.")
        else:
            # Filter controls
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                patient_filter = st.text_input("🔍 Filter by patient username", key="doc_pt_filter", placeholder="Type to filter…")
            with col_f2:
                rhythm_opts = ["All"] + sorted(set(r["rhythm"] for r in all_records if r.get("rhythm")))
                rhythm_filter = st.selectbox("Filter by rhythm", rhythm_opts, key="doc_rhythm_filter")

            filtered = all_records
            if patient_filter:
                filtered = [r for r in filtered if patient_filter.lower() in (r.get("patient_username","") or "").lower()]
            if rhythm_filter != "All":
                filtered = [r for r in filtered if r.get("rhythm") == rhythm_filter]

            st.caption(f"Showing {len(filtered)} of {len(all_records)} records")

            for r in filtered[:30]:
                rhythm_color = {
                    "NSR": "#4ade80", "Normal Sinus Rhythm": "#4ade80",
                    "Tachycardia": "#f87171", "Bradycardia": "#93c5fd",
                    "AFib": "#fcd34d", "PVC / PAC": "#c4b5fd",
                }.get(r.get("rhythm",""), "#64748b")

                with st.expander(
                    f"📋 Patient: {r.get('patient_username','—')}  |  "
                    f"Rhythm: {r.get('rhythm','—')}  |  "
                    f"{r.get('created_at','')[:16]}"
                ):
                    ca, cb, cc = st.columns(3)
                    ca.metric("Heart Rate", f"{r['heart_rate']:.0f} bpm" if r.get('heart_rate') else "—")
                    cb.metric("Rhythm", r.get('rhythm') or "—")
                    cc.metric("RMSSD", f"{r['rmssd']:.1f} ms" if r.get('rmssd') else "—")

                    st.markdown(f"**File:** `{r.get('filename','—')}`")
                    st.markdown(f"**Date:** {r.get('created_at','')[:19]}")

                    # Show existing feedback
                    existing_fb = _auth.get_feedback(r["id"])
                    if existing_fb:
                        st.markdown("**Doctor Feedback:**")
                        for fb in existing_fb:
                            st.markdown(
                                f'<div class="feedback-card">'
                                f'<div class="feedback-meta">Dr. {fb["doctor_name"]} · {fb["created_at"][:16]}</div>'
                                f'{fb["comment"]}'
                                f'</div>',
                                unsafe_allow_html=True
                            )

    # ── Tab 2: Add Feedback ───────────────────────────────────────────────────
    with tab_feedback:
        st.markdown("#### Add Clinical Feedback to a Patient Report")

        if not all_records:
            st.info("No ECG records available to comment on.")
        else:
            # Build select options
            record_options = {
                f"#{r['id']} — {r.get('patient_username','?')} — {r.get('rhythm','?')} — {r.get('created_at','')[:10]}": r
                for r in all_records
            }
            selected_label = st.selectbox(
                "Select ECG Record",
                list(record_options.keys()),
                key="fb_record_select"
            )
            selected_record = record_options[selected_label]

            # Show record summary
            st.markdown(f"""
            <div class="info-box">
              📋 <b>Patient:</b> {selected_record.get('patient_username','—')} &nbsp;|&nbsp;
              <b>Rhythm:</b> {selected_record.get('rhythm','—')} &nbsp;|&nbsp;
              <b>HR:</b> {f"{selected_record['heart_rate']:.0f} bpm" if selected_record.get('heart_rate') else '—'}
            </div>
            """, unsafe_allow_html=True)

            # Existing feedback
            existing_fb = _auth.get_feedback(selected_record["id"])
            if existing_fb:
                st.markdown("**Existing Feedback:**")
                for fb in existing_fb:
                    st.markdown(
                        f'<div class="feedback-card">'
                        f'<div class="feedback-meta">Dr. {fb["doctor_name"]} · {fb["created_at"][:16]}</div>'
                        f'{fb["comment"]}'
                        f'</div>',
                        unsafe_allow_html=True
                    )

            # Add new feedback
            st.markdown("---")
            st.markdown("**Write Your Clinical Feedback:**")
            comment = st.text_area(
                "Feedback",
                height=140,
                key="fb_comment_input",
                label_visibility="collapsed",
                placeholder="e.g. Patient shows signs of sinus tachycardia likely due to anxiety. Recommend follow-up in 2 weeks…",
            )
            if st.button("💬 Submit Feedback", type="primary", key="submit_feedback_btn"):
                if not comment.strip():
                    st.error("Please write a comment before submitting.")
                else:
                    _auth.save_feedback(
                        ecg_record_id=selected_record["id"],
                        doctor_username=user["username"],
                        doctor_name=user["full_name"],
                        comment=comment.strip(),
                    )
                    st.success("✅ Feedback saved successfully!")
                    st.rerun()

    # ── Tab 3: Patients ───────────────────────────────────────────────────────
    with tab_patients:
        st.markdown("#### Registered Patients")
        if not patients:
            st.info("No patients registered yet.")
        else:
            for p in patients:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{p['full_name']}** (`{p['username']}`)")
                    st.caption(
                        f"Age: {p.get('age','—')} · "
                        f"Gender: {p.get('gender','—')} · "
                        f"ID: {p.get('patient_id','—')}"
                    )
                with col2:
                    # Count this patient's ECG records
                    pt_records = _auth.get_ecg_records(p["username"], role="patient")
                    st.metric("ECG Records", len(pt_records))
                st.divider()
