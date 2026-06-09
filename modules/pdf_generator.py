"""
Alpha AI ECG — PDF Report Generator
Generates professional PDF diagnostic reports. Renamed from CardioLens to Alpha AI ECG.
"""

import io
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        Image as RLImage, HRFlowable
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


def generate_pdf_report(patient_name, patient_age, patient_gender, patient_id,
                         rhythm_key, features, confidence, explanation,
                         RHYTHM_CLASSES,
                         waveform_png_bytes=None, classification_png_bytes=None):
    """Generate a professional PDF ECG report. Returns bytes or None."""
    if not PDF_AVAILABLE:
        return None

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             rightMargin=20*mm, leftMargin=20*mm,
                             topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    story = []
    cls = RHYTHM_CLASSES[rhythm_key]
    now = datetime.now()

    def sty(name, **kw):
        return ParagraphStyle(name, **kw)

    title_style = sty("Title2", fontSize=22, fontName="Helvetica-Bold",
                       textColor=colors.HexColor("#1e3a5f"), spaceAfter=2)
    h2_style    = sty("H2",    fontSize=13, fontName="Helvetica-Bold",
                       textColor=colors.HexColor("#1e3a5f"), spaceBefore=12, spaceAfter=6)
    body_style  = sty("Body2", fontSize=10, fontName="Helvetica",
                       textColor=colors.HexColor("#374151"), leading=16)
    small_style = sty("Small", fontSize=8,  fontName="Helvetica",
                       textColor=colors.HexColor("#9ca3af"))

    urgency_color_map = {
        "Normal":   colors.HexColor("#065f46"),
        "Moderate": colors.HexColor("#92400e"),
        "Monitor":  colors.HexColor("#78350f"),
        "HIGH":     colors.HexColor("#7f1d1d"),
        "Recheck":  colors.HexColor("#374151"),
    }

    # ── Header ────────────────────────────────────────────────────────────────
    header_data = [[
        Paragraph("<b>🫀 Alpha AI ECG</b>", sty("hL", fontSize=18, fontName="Helvetica-Bold",
                                                  textColor=colors.HexColor("#1e3a5f"))),
        Paragraph(f"<b>ECG Diagnostic Report</b><br/><font size='9' color='#6b7280'>Generated: {now.strftime('%B %d, %Y  %H:%M')}</font>",
                  sty("hR", fontSize=12, fontName="Helvetica-Bold",
                      textColor=colors.HexColor("#1e3a5f"), alignment=TA_RIGHT))
    ]]
    header_table = Table(header_data, colWidths=["55%", "45%"])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#eff6ff")),
        ("BOX", (0,0), (-1,-1), 1.5, colors.HexColor("#1e3a5f")),
        ("LINEBELOW", (0,0), (-1,0), 2, colors.HexColor("#2563eb")),
        ("LEFTPADDING", (0,0), (-1,-1), 12),
        ("RIGHTPADDING", (0,0), (-1,-1), 12),
        ("TOPPADDING", (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10*mm))

    # ── Patient Info ──────────────────────────────────────────────────────────
    story.append(Paragraph("Patient Information", h2_style))
    pdata = [
        ["Patient Name:", patient_name or "N/A",   "Patient ID:", patient_id or "N/A"],
        ["Age:",          str(patient_age) if patient_age else "N/A", "Gender:", patient_gender or "N/A"],
        ["Date of Test:", now.strftime("%B %d, %Y"), "Time:", now.strftime("%H:%M:%S")],
        ["Report Type:", "AI-Assisted ECG Analysis", "Status:", "PRELIMINARY"],
    ]
    pt = Table(pdata, colWidths=["28%", "22%", "28%", "22%"])
    pt.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#eff6ff")),
        ("BACKGROUND", (2,0), (2,-1), colors.HexColor("#eff6ff")),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME", (2,0), (2,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("TEXTCOLOR", (0,0), (0,-1), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR", (2,0), (2,-1), colors.HexColor("#1e3a5f")),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#d1d5db")),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(pt)
    story.append(Spacer(1, 8*mm))

    # ── Rhythm Result ─────────────────────────────────────────────────────────
    story.append(Paragraph("Rhythm Classification Result", h2_style))
    urgency_c = urgency_color_map.get(cls["urgency"], colors.HexColor("#374151"))
    result_data = [[
        Paragraph(f"<b>{cls['emoji']} {cls['name']}</b>",
                  sty("rn", fontSize=16, fontName="Helvetica-Bold", textColor=urgency_c)),
        Paragraph(f"<b>HR Range:</b> {cls['hr_range']}<br/><b>Clinical Urgency:</b> {cls['urgency']}",
                  sty("rs", fontSize=10, fontName="Helvetica", textColor=colors.HexColor("#374151"))),
        Paragraph(f"<b>Confidence</b><br/>{confidence*100:.0f}%",
                  sty("rc", fontSize=14, fontName="Helvetica-Bold", textColor=urgency_c, alignment=TA_CENTER)),
    ]]
    rt = Table(result_data, colWidths=["42%", "38%", "20%"])
    rt.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#f0f9ff")),
        ("BOX", (0,0), (-1,-1), 2, urgency_c),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING", (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(rt)
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(cls["desc"], body_style))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(f"<b>Algorithm Explanation:</b> {explanation}", body_style))
    story.append(Spacer(1, 8*mm))

    # ── Measurements ──────────────────────────────────────────────────────────
    if features:
        story.append(Paragraph("Quantitative ECG Measurements", h2_style))
        mdata = [
            ["Parameter", "Value", "Reference Range", "Status"],
            ["Heart Rate", f"{features['hr_bpm']:.1f} bpm", "60–100 bpm",
             "Normal" if 60 <= features['hr_bpm'] <= 100 else "Abnormal"],
            ["Mean RR Interval", f"{features['mean_rr_s']*1000:.0f} ms", "600–1000 ms",
             "Normal" if 600 <= features['mean_rr_s']*1000 <= 1000 else "Abnormal"],
            ["RR Std Deviation", f"{features['std_rr_s']*1000:.1f} ms", "< 50 ms", ""],
            ["RMSSD", f"{features['rmssd']*1000:.1f} ms", "20–50 ms (resting)", ""],
            ["RR Coefficient of Variation", f"{features['cv_rr']:.4f}", "< 0.10 (regular)", ""],
            ["Premature Beat Ratio", f"{features['premature_ratio']*100:.1f}%", "< 5%",
             "Normal" if features['premature_ratio'] < 0.05 else "Elevated"],
            ["R-peaks Detected", str(features['n_peaks']), "≥ 3", ""],
        ]
        mt = Table(mdata, colWidths=["35%", "20%", "30%", "15%"])
        mt.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1e3a5f")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#f9fafb"), colors.white]),
            ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#d1d5db")),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("RIGHTPADDING", (0,0), (-1,-1), 8),
            ("TOPPADDING", (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("ALIGN", (1,0), (-1,-1), "CENTER"),
        ]))
        story.append(mt)
        story.append(Spacer(1, 8*mm))

    # ── Recommendations ───────────────────────────────────────────────────────
    story.append(Paragraph("Clinical Recommendations", h2_style))
    story.append(Paragraph(f"<b>Clinical Note:</b> {cls['clinical']}", body_style))
    story.append(Spacer(1, 3*mm))
    for i, rec in enumerate(cls["recommendations"], 1):
        story.append(Paragraph(f"  {i}. {rec}", body_style))
    story.append(Spacer(1, 8*mm))

    # ── Waveform images ───────────────────────────────────────────────────────
    if waveform_png_bytes:
        story.append(Paragraph("ECG Signal Visualization", h2_style))
        story.append(RLImage(io.BytesIO(waveform_png_bytes), width=165*mm, height=60*mm))
        story.append(Spacer(1, 4*mm))

    if classification_png_bytes:
        story.append(Paragraph("R-Peak Detection & RR Tachogram", h2_style))
        story.append(RLImage(io.BytesIO(classification_png_bytes), width=165*mm, height=65*mm))
        story.append(Spacer(1, 8*mm))

    # ── Disclaimer ────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#d1d5db")))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        "⚕️ MEDICAL DISCLAIMER: This report is generated by Alpha AI ECG, an AI-based algorithm "
        "for educational and research purposes only. It is NOT a substitute for professional medical "
        "advice, diagnosis, or treatment. Always consult a qualified cardiologist for clinical ECG "
        "interpretation. Alpha AI ECG v2.0",
        small_style
    ))

    doc.build(story)
    buf.seek(0)
    return buf.read()
