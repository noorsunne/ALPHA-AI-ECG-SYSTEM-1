"""
Alpha AI ECG — Patient Dashboard
Patients upload ECG, view their reports with doctor feedback, use AI chatbot.
The ECG processing pipeline is preserved exactly from the original system.
"""

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import time

import auth as _auth
from modules import ecg_processor as ecg
from modules.chatbot import render_chatbot_ui, build_ecg_context
from modules.file_handler import save_ecg_file
from modules.pdf_generator import generate_pdf_report, PDF_AVAILABLE


def show(user: dict):
    my_records = _auth.get_ecg_records(user["username"], role="patient")

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="cl-header">
      <h1>🧑 <span>Patient</span> Dashboard</h1>
      <p>Welcome, <b>{user['full_name']}</b> · Patient ID: {user.get('patient_id','—')} · Alpha AI ECG</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Stats ─────────────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="dash-stat"><div class="dash-stat-val" style="color:#3b82f6">{len(my_records)}</div><div class="dash-stat-lbl">My ECG Records</div></div>', unsafe_allow_html=True)
    with c2:
        last_hr = my_records[0]["heart_rate"] if my_records else None
        val = f"{last_hr:.0f}" if last_hr else "—"
        st.markdown(f'<div class="dash-stat"><div class="dash-stat-val" style="color:#10b981">{val}</div><div class="dash-stat-lbl">Last HR (bpm)</div></div>', unsafe_allow_html=True)
    with c3:
        last_r = my_records[0]["rhythm"] if my_records else "—"
        st.markdown(f'<div class="dash-stat"><div class="dash-stat-val" style="color:#f59e0b;font-size:20px;">{last_r or "—"}</div><div class="dash-stat-lbl">Last Rhythm</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab_ecg, tab_history, tab_chat, tab_profile = st.tabs([
        "📊  ECG Analysis", "📋  My Reports", "🤖  AI Chatbot", "👤  My Profile"
    ])

    # ── Tab 1: ECG Analysis ───────────────────────────────────────────────────
    with tab_ecg:
        _run_ecg_analysis(user)

    # ── Tab 2: My Reports ─────────────────────────────────────────────────────
    with tab_history:
        st.markdown("#### My ECG History")
        if not my_records:
            st.info("No ECG records yet. Upload an ECG in the 'ECG Analysis' tab.")
        else:
            for r in my_records:
                hr_label = (f"{r['heart_rate']:.0f} bpm") if r.get('heart_rate') else "—"
                with st.expander(
                    f"📅 {r['created_at'][:16]}  |  Rhythm: {r.get('rhythm','—')}  |  HR: {hr_label}"
                ):
                    ca, cb, cc = st.columns(3)
                    ca.metric("Heart Rate", f"{r['heart_rate']:.0f} bpm" if r.get('heart_rate') else "—")
                    cb.metric("Rhythm", r.get("rhythm") or "—")
                    cc.metric("RMSSD", f"{r['rmssd']:.1f} ms" if r.get('rmssd') else "—")

                    st.caption(f"File: {r.get('filename','—')}  |  Date: {r.get('created_at','')[:19]}")

                    # Doctor feedback for this record
                    feedbacks = _auth.get_feedback(r["id"])
                    if feedbacks:
                        st.markdown("**💬 Doctor Feedback:**")
                        for fb in feedbacks:
                            st.markdown(
                                f'<div class="feedback-card">'
                                f'<div class="feedback-meta">👨‍⚕️ Dr. {fb["doctor_name"]} · {fb["created_at"][:16]}</div>'
                                f'{fb["comment"]}'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                    else:
                        st.markdown('<div class="info-box">ℹ️ No doctor feedback yet for this record.</div>', unsafe_allow_html=True)

    # ── Tab 3: AI Chatbot ─────────────────────────────────────────────────────
    with tab_chat:
        st.markdown("#### 🤖 Alpha AI ECG Assistant")
        ecg_ctx = st.session_state.get("ecg_context", "")
        render_chatbot_ui(ecg_context=ecg_ctx, chat_key=f"patient_{user['username']}")

    # ── Tab 4: My Profile ─────────────────────────────────────────────────────
    with tab_profile:
        st.markdown('<div class="profile-card">', unsafe_allow_html=True)
        st.markdown(f"**Full Name:** {user['full_name']}")
        st.markdown(f"**Username:** {user['username']}")
        st.markdown(f"**Email:** {user.get('email','—')}")
        st.markdown(f"**Age:** {user.get('age','—')}")
        st.markdown(f"**Gender:** {user.get('gender','—')}")
        st.markdown(f"**Patient ID:** {user.get('patient_id','—')}")
        st.markdown(f"**Joined:** {user.get('created_at','—')[:10]}")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("⚕️ *If your details are incorrect, please contact your doctor or admin.*")


# ═════════════════════════════════════════════════════════════════════════════
#  ECG ANALYSIS PIPELINE (full pipeline — algorithms unchanged)
# ═════════════════════════════════════════════════════════════════════════════

def _run_ecg_analysis(user: dict):
    """Full ECG upload + analysis pipeline for the patient dashboard."""

    # Patient info (pre-filled from profile)
    patient_name   = user.get("full_name", "")
    patient_age    = user.get("age") or 45
    patient_gender = user.get("gender", "Male")
    patient_id     = user.get("patient_id", "")

    # Processing settings
    with st.expander("⚙️ Processing Settings", expanded=False):
        sc1, sc2, sc3, sc4, sc5 = st.columns(5)
        n_strips      = sc1.slider("ECG rows", 2, 4, 4, key=f"ns_{user['username']}")
        pad           = sc2.slider("Crop padding", 40, 120, 70, key=f"pd_{user['username']}")
        fft_band      = sc3.slider("FFT width", 2, 15, 6, key=f"fb_{user['username']}")
        classify_lead = sc4.selectbox("Classify from", ["II","I","V1","V2","aVR"], key=f"cl_{user['username']}")
        r_sensitivity = sc5.slider("R-peak sens.", 0.2, 0.7, 0.4, 0.05, key=f"rs_{user['username']}")

    uploaded = st.file_uploader(
        "Upload ECG image or PDF (JPG / PNG / PDF, 300 DPI recommended)",
        type=["png", "jpg", "jpeg", "pdf"],
        key=f"ecg_upload_{user['username']}"
    )

    if uploaded is None:
        st.markdown('<div class="info-box">👆 Upload a JPG, PNG, or PDF ECG file to begin analysis.</div>',
                    unsafe_allow_html=True)
        return

    if uploaded.size > 20 * 1024 * 1024:
        st.markdown('<div class="warn-box">⚠ File too large (max 20 MB). Please resize or compress.</div>',
                    unsafe_allow_html=True)
        return

    # ── Handle PDF: convert first page to image ───────────────────────────────
    if uploaded.name.lower().endswith(".pdf"):
        from modules.file_handler import pdf_first_page_to_image, save_ecg_file as _save
        saved_path = _save(uploaded, user["username"])
        img_rgb = pdf_first_page_to_image(saved_path)
        if img_rgb is None:
            st.error("❌ Could not render PDF. Please install PyMuPDF (`pip install PyMuPDF`) or upload a JPG/PNG.")
            return
        import cv2
        gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
        st.markdown('<div class="success-box">✓ PDF converted to image for analysis.</div>', unsafe_allow_html=True)
    else:
        # Save file to disk
        saved_path = save_ecg_file(uploaded, user["username"])

        # STEP 2: Preprocessing
        st.markdown('<div class="step-card"><span class="step-num">STEP 02</span><span class="step-title">Image Preprocessing — Grayscale · Denoise · Grid Removal</span></div>',
                    unsafe_allow_html=True)
        with st.spinner("Preprocessing ECG image…"):
            t_start = time.time()
            try:
                img_rgb, gray = ecg.load_and_grayscale(uploaded)
            except ValueError as e:
                st.error(str(e))
                return

    # From here — same pipeline for both image and PDF
    t_start = time.time()

    if not uploaded.name.lower().endswith(".pdf"):
        blur, bw, cleaned, edges = ecg.preprocess(gray)
        h_img, w_img = gray.shape

        c1, c2, c3 = st.columns(3)
        with c1:
            fig = ecg.dark_fig(img_rgb, "Original ECG")
            st.pyplot(fig, use_container_width=True); plt.close(fig)
        with c2:
            fig = ecg.dark_fig(gray, "Grayscale", "gray")
            st.pyplot(fig, use_container_width=True); plt.close(fig)
        with c3:
            fig = ecg.dark_fig(cleaned, "Grid Removed (Binary)", "gray")
            st.pyplot(fig, use_container_width=True); plt.close(fig)

        st.markdown(f'<div class="info-box">📐 Image: <b>{w_img}×{h_img}px</b> · {uploaded.type} · {uploaded.size/1024:.1f} KB</div>',
                    unsafe_allow_html=True)
    else:
        blur, bw, cleaned, edges = ecg.preprocess(gray)
        h_img, w_img = gray.shape

    # STEP 3: Lead Detection
    st.markdown('<div class="step-card"><span class="step-num">STEP 03</span><span class="step-title">ECG Lead Strip Detection</span></div>',
                unsafe_allow_html=True)
    with st.spinner("Detecting lead strips…"):
        strip_ranges, proj_smooth, peaks_found = ecg.detect_lead_strips(gray, edges, pad=pad, n_strips=n_strips)

    n_detected = len(strip_ranges)
    if n_detected == 0:
        st.markdown('<div class="warn-box">⚠ No lead strips detected. Try increasing strip padding or uploading a higher-quality image.</div>',
                    unsafe_allow_html=True)
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 3.5), facecolor="#050b18")
    for ax in axes:
        ax.set_facecolor("#0a1428")
        for sp in ax.spines.values(): sp.set_edgecolor("#1e2538")
        ax.tick_params(colors="#64748b")
    axes[0].plot(proj_smooth / proj_smooth.max(), color="#3b82f6", linewidth=1.5)
    for p in peaks_found:
        axes[0].axvline(p, color="#f87171", linewidth=0.8, alpha=0.7)
    axes[0].set_title("Horizontal Edge Projection", color="#e2e8f0", fontsize=10)
    axes[0].set_xlabel("Row (y)", color="#64748b"); axes[0].set_ylabel("Norm. energy", color="#64748b")
    axes[1].imshow(img_rgb)
    axes[1].set_title(f"Detected Lead Rows ({n_detected})", color="#e2e8f0", fontsize=10)
    for i, (y1, y2) in enumerate(strip_ranges):
        axes[1].axhline(y1, color="#4ade80", linewidth=1.5, linestyle="--", alpha=0.9)
        axes[1].axhline(y2, color="#f87171", linewidth=1.0, linestyle=":", alpha=0.7)
        axes[1].text(10, (y1+y2)//2, f"Row {i+1}", color="#fcd34d", fontsize=9, fontweight="bold", va="center")
    axes[1].axis("off")
    fig.tight_layout(pad=1)
    st.pyplot(fig, use_container_width=True); plt.close(fig)
    st.markdown(f'<div class="success-box">✓ {n_detected} row(s) detected → up to {n_detected*3} leads will be extracted.</div>',
                unsafe_allow_html=True)

    # STEP 4: Signal Extraction
    st.markdown('<div class="step-card"><span class="step-num">STEP 04</span><span class="step-title">Signal Reconstruction & Digitization — FFT · SavGol · Column Scan</span></div>',
                unsafe_allow_html=True)
    with st.spinner("Extracting waveforms…"):
        signals, cleaned_segs = ecg.digitize_all_leads(gray, strip_ranges)
        df_out = ecg.build_dataframe(signals)
        t_end = time.time()
        elapsed = t_end - t_start

    n_leads = len(signals)
    total_samples = len(df_out)

    st.markdown(f"""
    <div class="metric-row">
      <div class="metric-box"><div class="m-label">LEADS EXTRACTED</div><div class="m-val">{n_leads}<span class="m-unit">of 12</span></div><div class="m-sub">standard leads</div></div>
      <div class="metric-box"><div class="m-label">TOTAL SAMPLES</div><div class="m-val">{total_samples:,}</div><div class="m-sub">all leads combined</div></div>
      <div class="metric-box"><div class="m-label">PROCESS TIME</div><div class="m-val">{elapsed:.1f}<span class="m-unit">s</span></div><div class="m-sub">CPU processing</div></div>
      <div class="metric-box"><div class="m-label">OUTPUTS</div><div class="m-val">CSV</div><div class="m-sub">+ PDF + PNG</div></div>
    </div>
    """, unsafe_allow_html=True)

    if elapsed <= 15:
        st.markdown(f'<div class="success-box">✓ Completed in {elapsed:.1f}s</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="warn-box">⚠ Processing took {elapsed:.1f}s. Try a smaller image for faster results.</div>', unsafe_allow_html=True)

    with st.expander("📄 Preview CSV output (first 20 rows)"):
        st.dataframe(df_out.head(20), use_container_width=True)

    # STEP 5: Waveform Visualization
    st.markdown('<div class="step-card"><span class="step-num">STEP 05</span><span class="step-title">Original vs Digitized Signal Comparison</span></div>',
                unsafe_allow_html=True)

    lead_names = list(signals.keys())
    selected_leads = st.multiselect(
        "Select leads to visualize",
        options=lead_names,
        default=lead_names[:4] if len(lead_names) >= 4 else lead_names,
        key=f"sel_leads_{user['username']}"
    )
    waveform_png = None
    if selected_leads:
        n_plot = len(selected_leads)
        fig, axes = plt.subplots(n_plot, 2, figsize=(16, 2.8 * n_plot), facecolor="#050b18")
        if n_plot == 1:
            axes = [axes]
        for i, lead in enumerate(selected_leads):
            amp = signals[lead]
            duration = 10.0 if lead == "II" else 2.5
            t = np.linspace(0, duration, len(amp))
            axes[i][0].set_facecolor("#050b18")
            axes[i][0].imshow(cleaned_segs[lead], cmap="gray", aspect="auto")
            axes[i][0].set_title(f"Lead {lead} — FFT-cleaned", color="#e2e8f0", fontsize=10)
            axes[i][0].axis("off")
            axes[i][1].set_facecolor("#0a1428")
            for sp in axes[i][1].spines.values(): sp.set_edgecolor("#1e2538")
            axes[i][1].tick_params(colors="#64748b", labelsize=8)
            axes[i][1].plot(t, amp, color="#3b82f6", linewidth=1.3)
            axes[i][1].axhline(0, color="#1e2538", linewidth=0.8, linestyle="--")
            axes[i][1].set_title(f"Lead {lead} — Reconstructed Signal", color="#e2e8f0", fontsize=10)
            axes[i][1].set_xlabel("Time (s)", color="#64748b", fontsize=9)
            axes[i][1].set_ylabel("Amplitude (norm.)", color="#64748b", fontsize=9)
            axes[i][1].set_ylim(-1.3, 1.3)
        fig.suptitle("ECG Image vs Reconstructed Signal — Alpha AI ECG", color="#e2e8f0", fontsize=13, y=1.01)
        fig.tight_layout(pad=1.5)
        st.pyplot(fig, use_container_width=True)
        waveform_png = ecg.fig_to_bytes(fig)
        st.session_state.waveform_png = waveform_png
        plt.close(fig)

    # STEP 6: Rhythm Classification
    st.markdown('<div class="step-card"><span class="step-num">STEP 06</span><span class="step-title">Rhythm Classification — R-Peak Detection · HR · HRV</span></div>',
                unsafe_allow_html=True)

    clf_lead   = classify_lead if classify_lead in signals else list(signals.keys())[0]
    clf_signal = signals[clf_lead]
    clf_duration = 10.0 if clf_lead == "II" else 2.5

    with st.spinner(f"Classifying rhythm from Lead {clf_lead}…"):
        samples_per_sec = len(clf_signal) / clf_duration
        min_dist = max(10, int(samples_per_sec * 0.4))
        r_peaks  = ecg.detect_r_peaks(clf_signal, min_distance_samples=min_dist, min_height_factor=r_sensitivity)
        features = ecg.compute_rr_features(r_peaks, clf_duration)
        rhythm_key, confidence, explanation = ecg.classify_rhythm(features)

    # Save to session state for chatbot
    st.session_state.rhythm_key  = rhythm_key
    st.session_state.features    = features
    st.session_state.signals     = signals
    st.session_state.ecg_context = build_ecg_context(rhythm_key, features, signals, ecg.RHYTHM_CLASSES)
    st.session_state.analysis_done = True

    # Save ECG record to DB
    try:
        _auth.save_ecg_record(
            patient_username=user["username"],
            doctor_username=None,
            filename=uploaded.name,
            heart_rate=features.get("hr_bpm") if features else None,
            rhythm=ecg.RHYTHM_CLASSES[rhythm_key]["abbr"],
            rmssd=features.get("rmssd") if features else None,
            hr_cv=features.get("cv_rr") if features else None,
            analysis_json=str(features)[:500] if features else "{}",
            file_path=saved_path,
        )
    except Exception:
        pass  # Non-blocking

    cls = ecg.RHYTHM_CLASSES[rhythm_key]

    # Result card
    st.markdown(f"""
    <div class="rhythm-card {cls['css']}">
      <div class="r-label">RHYTHM CLASSIFICATION RESULT — ALPHA AI ECG</div>
      <div class="r-name">{cls['emoji']} {cls['name']}</div>
      <div class="r-abbr">{cls['abbr']} · HR: {cls['hr_range']} · Urgency: <b>{cls['urgency']}</b></div>
      <div class="r-desc">{cls['desc']}</div>
    </div>
    """, unsafe_allow_html=True)

    # Feature pills
    if features:
        hr_s    = f"{features['hr_bpm']:.0f}"
        rr_s    = f"{features['mean_rr_s']*1000:.0f}ms"
        cv_s    = f"{features['cv_rr']:.3f}"
        np_s    = str(features['n_peaks'])
        pr_s    = f"{features['premature_ratio']*100:.1f}%"
        cf_s    = f"{confidence*100:.0f}%"
        rmssd_s = f"{features['rmssd']*1000:.1f}ms"
    else:
        hr_s = rr_s = cv_s = np_s = pr_s = cf_s = rmssd_s = "N/A"

    st.markdown(f"""
    <div class="feat-row">
      <div class="feat-pill"><div class="fp-l">HEART RATE</div><div class="fp-v">{hr_s} <span style="font-size:12px;font-weight:400">bpm</span></div></div>
      <div class="feat-pill"><div class="fp-l">MEAN RR</div><div class="fp-v">{rr_s}</div></div>
      <div class="feat-pill"><div class="fp-l">RR VARIABILITY</div><div class="fp-v">{cv_s}</div></div>
      <div class="feat-pill"><div class="fp-l">RMSSD</div><div class="fp-v">{rmssd_s}</div></div>
      <div class="feat-pill"><div class="fp-l">R-PEAKS</div><div class="fp-v">{np_s}</div></div>
      <div class="feat-pill"><div class="fp-l">PREMATURE</div><div class="fp-v">{pr_s}</div></div>
      <div class="feat-pill"><div class="fp-l">CONFIDENCE</div><div class="fp-v">{cf_s}</div></div>
    </div>
    """, unsafe_allow_html=True)

    # Confidence bar
    bc     = ecg.RHYTHM_BAR_COLORS[rhythm_key]
    bw_pct = int(confidence * 100)
    st.markdown(f"""
    <div style="margin:12px 0 6px;">
      <div style="font-size:10px;color:#475569;font-family:monospace;letter-spacing:1.5px;margin-bottom:5px;">CLASSIFICATION CONFIDENCE</div>
      <div class="conf-bg"><div class="conf-fill" style="width:{bw_pct}%;background:{bc};"></div></div>
      <div style="font-size:11px;color:#64748b;margin-top:4px;">{explanation}</div>
    </div>
    """, unsafe_allow_html=True)

    # R-peak plot
    clf_t = np.linspace(0, clf_duration, len(clf_signal))
    fig, axes2 = plt.subplots(2, 1, figsize=(14, 6), facecolor="#050b18",
                               gridspec_kw={"height_ratios": [3, 1]})
    for ax in axes2:
        ax.set_facecolor("#0a1428")
        for sp in ax.spines.values(): sp.set_edgecolor("#1e2538")
        ax.tick_params(colors="#64748b", labelsize=8)

    axes2[0].plot(clf_t, clf_signal, color="#3b82f6", linewidth=1.3, label="ECG signal", zorder=2)
    axes2[0].axhline(0, color="#1e2538", linewidth=0.7, linestyle="--")
    if len(r_peaks) > 0:
        peak_t_plot = r_peaks / len(clf_signal) * clf_duration
        axes2[0].scatter(peak_t_plot, clf_signal[r_peaks], color=bc, s=60, zorder=5,
                         label=f"R-peaks ({len(r_peaks)})", marker="v")
        for i in range(len(peak_t_plot) - 1):
            if i % 2 == 0:
                axes2[0].axvspan(peak_t_plot[i], peak_t_plot[i+1], alpha=0.05, color=bc)
    axes2[0].set_title(f"Lead {clf_lead} — {cls['name']} | HR ≈ {hr_s} bpm", color="#e2e8f0", fontsize=11)
    axes2[0].set_ylabel("Amplitude (norm.)", color="#64748b", fontsize=9)
    axes2[0].set_ylim(-1.4, 1.5)
    axes2[0].legend(fontsize=9, facecolor="#0a1428", edgecolor="#1e2538", labelcolor="#e2e8f0", loc="upper right")

    if features and len(features["rr_intervals"]) > 1:
        rr_ms = features["rr_intervals"] * 1000
        axes2[1].bar(np.arange(1, len(rr_ms)+1), rr_ms, color=bc, alpha=0.75, width=0.7)
        axes2[1].axhline(np.mean(rr_ms), color="#e2e8f0", linewidth=1, linestyle="--",
                         label=f"Mean RR = {np.mean(rr_ms):.0f} ms")
        axes2[1].set_title("RR Interval Tachogram", color="#e2e8f0", fontsize=10)
        axes2[1].set_xlabel("Beat number", color="#64748b", fontsize=9)
        axes2[1].set_ylabel("RR (ms)", color="#64748b", fontsize=9)
        axes2[1].legend(fontsize=8, facecolor="#0a1428", edgecolor="#1e2538", labelcolor="#e2e8f0")
    else:
        axes2[1].text(0.5, 0.5, "Not enough R-peaks for tachogram",
                      ha="center", va="center", color="#64748b", transform=axes2[1].transAxes)
        axes2[1].set_title("RR Interval Tachogram", color="#e2e8f0", fontsize=10)

    fig.tight_layout(pad=1.5)
    st.pyplot(fig, use_container_width=True)
    classification_png = ecg.fig_to_bytes(fig)
    st.session_state.classification_png = classification_png
    plt.close(fig)

    st.markdown('<div class="warn-box">⚕️ <b>Medical Disclaimer:</b> Rule-based AI classification for educational/research purposes only. NOT a medical diagnosis. Always consult a qualified cardiologist.</div>',
                unsafe_allow_html=True)

    # STEP 7: Downloads
    st.markdown('<div class="step-card"><span class="step-num">STEP 07</span><span class="step-title">Download Results</span></div>',
                unsafe_allow_html=True)

    if features:
        df_out["rhythm"]     = cls["name"]
        df_out["hr_bpm"]     = round(features["hr_bpm"], 1)
        df_out["rr_cv"]      = round(features["cv_rr"], 4)
        df_out["confidence"] = round(confidence, 3)

    csv_bytes = df_out.to_csv(index=False).encode("utf-8")
    dc1, dc2, dc3, dc4 = st.columns(4)
    with dc1:
        st.download_button("⬇ Digitized ECG (CSV)", csv_bytes, "ecg_digitized.csv", "text/csv", use_container_width=True)
        st.caption(f"{len(df_out):,} rows · lead, time_s, amplitude, rhythm, hr_bpm")
    with dc2:
        if waveform_png:
            st.download_button("⬇ Waveform Plot (PNG)", waveform_png, "ecg_waveform.png", "image/png", use_container_width=True)
            st.caption("Original vs reconstructed signal comparison")
    with dc3:
        if classification_png:
            st.download_button("⬇ Classification Plot (PNG)", classification_png, "ecg_classification.png", "image/png", use_container_width=True)
            st.caption("R-peak detection + RR tachogram")
    with dc4:
        if PDF_AVAILABLE and features:
            pdf_bytes = generate_pdf_report(
                patient_name=patient_name,
                patient_age=patient_age,
                patient_gender=patient_gender,
                patient_id=patient_id,
                rhythm_key=rhythm_key,
                features=features,
                confidence=confidence,
                explanation=explanation,
                RHYTHM_CLASSES=ecg.RHYTHM_CLASSES,
                waveform_png_bytes=waveform_png,
                classification_png_bytes=classification_png,
            )
            if pdf_bytes:
                st.download_button("⬇ Full Report (PDF)", pdf_bytes, "alpha_ai_ecg_report.pdf", "application/pdf", use_container_width=True)
                st.caption("Professional diagnostic report")
