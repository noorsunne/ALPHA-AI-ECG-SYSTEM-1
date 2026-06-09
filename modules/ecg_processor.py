"""
Alpha AI ECG — ECG Processing Engine
Pure computation module — zero UI code. All algorithms preserved exactly.
"""

import cv2
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.ndimage import median_filter, gaussian_filter1d
from scipy.signal import savgol_filter, find_peaks
import io


# ─────────────────────────────────────────────────────────────────────────────
# RHYTHM METADATA
# ─────────────────────────────────────────────────────────────────────────────
RHYTHM_CLASSES = {
    "NSR": {
        "name": "Normal Sinus Rhythm", "abbr": "NSR", "css": "rhythm-normal", "emoji": "✅",
        "hr_range": "60–100 bpm", "urgency": "Normal",
        "clinical": "Regular rhythm from sinoatrial node. RR intervals consistent. No intervention needed.",
        "recommendations": [
            "Routine annual ECG recommended",
            "Maintain healthy lifestyle and regular exercise",
            "Blood pressure monitoring every 6 months",
            "Continue current medication if prescribed",
        ],
        "desc": "The heart is beating in a normal, regular pattern from the SA node. All intervals are within normal range.",
    },
    "TACHY": {
        "name": "Sinus Tachycardia", "abbr": "Tachycardia", "css": "rhythm-tachy", "emoji": "⚡",
        "hr_range": "> 100 bpm", "urgency": "Moderate",
        "clinical": "Elevated HR >100 bpm. Regular rhythm. Rule out fever, anemia, thyroid disease, anxiety.",
        "recommendations": [
            "Identify and treat underlying cause",
            "Avoid caffeine, alcohol, and stimulants",
            "Consider 24-hour Holter monitor",
            "Follow up with cardiologist within 2 weeks",
        ],
        "desc": "Heart rate elevated above 100 bpm. Rhythm is regular. May be physiological or pathological.",
    },
    "BRADY": {
        "name": "Sinus Bradycardia", "abbr": "Bradycardia", "css": "rhythm-brady", "emoji": "🐢",
        "hr_range": "< 60 bpm", "urgency": "Monitor",
        "clinical": "HR below 60 bpm. May be normal in athletes. Rule out hypothyroidism, AV block, medications.",
        "recommendations": [
            "Check current medications (beta-blockers, digoxin, amiodarone)",
            "Thyroid function test (TSH, T3, T4)",
            "If symptomatic (dizziness, syncope), refer to electrophysiology",
            "Exercise tolerance test if clinically indicated",
        ],
        "desc": "Heart rate below 60 bpm. Regular rhythm. Commonly benign in trained athletes.",
    },
    "AFIB": {
        "name": "Atrial Fibrillation", "abbr": "AFib", "css": "rhythm-afib", "emoji": "〰️",
        "hr_range": "Variable", "urgency": "HIGH",
        "clinical": "Irregular irregular rhythm. High stroke risk. Anticoagulation may be indicated. Refer urgently.",
        "recommendations": [
            "URGENT cardiology referral",
            "Stroke risk assessment (CHA₂DS₂-VASc score)",
            "Consider anticoagulation therapy (DOAC or warfarin)",
            "Rate or rhythm control strategy discussion",
            "Echocardiogram to assess cardiac structure",
        ],
        "desc": "Highly irregular RR intervals. Most common sustained arrhythmia. Significant stroke risk without treatment.",
    },
    "PVC": {
        "name": "Premature Ventricular Contractions", "abbr": "PVC / PAC", "css": "rhythm-pvc", "emoji": "💥",
        "hr_range": "Variable", "urgency": "Monitor",
        "clinical": "Ectopic beats causing irregular rhythm. If >10% burden, consider further evaluation.",
        "recommendations": [
            "24-hour Holter monitoring to quantify PVC burden",
            "Echocardiogram to assess structural heart disease",
            "Reduce caffeine, alcohol, and stress",
            "Electrolyte panel (K+, Mg++, Ca++)",
        ],
        "desc": "Regular rhythm with occasional premature beats. Short RR followed by compensatory pause.",
    },
    "UNKNOWN": {
        "name": "Indeterminate Rhythm", "abbr": "Unknown", "css": "rhythm-unknown", "emoji": "❓",
        "hr_range": "N/A", "urgency": "Recheck",
        "clinical": "Insufficient signal quality for reliable classification. Repeat with better image.",
        "recommendations": [
            "Upload a higher quality ECG image (≥300 DPI recommended)",
            "Ensure good contrast and minimal noise",
            "Try adjusting strip padding in Settings",
            "Ensure standard 12-lead layout is used",
        ],
        "desc": "Could not reliably detect enough R-peaks for classification. Image quality may be insufficient.",
    },
}

URGENCY_COLORS = {
    "Normal":   "#4ade80",
    "Moderate": "#fb923c",
    "Monitor":  "#fcd34d",
    "HIGH":     "#f87171",
    "Recheck":  "#64748b",
}

RHYTHM_BAR_COLORS = {
    "NSR": "#4ade80", "TACHY": "#f87171", "BRADY": "#60a5fa",
    "AFIB": "#fcd34d", "PVC": "#c4b5fd", "UNKNOWN": "#64748b",
}


# ═══════════════════════════════════════════════════════════════════════════════
#  ECG PROCESSING PIPELINE  (exact copy — no changes)
# ═══════════════════════════════════════════════════════════════════════════════

def load_and_grayscale(uploaded_file):
    file_bytes = np.frombuffer(uploaded_file.read(), np.uint8)
    img_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if img_bgr is None:
        raise ValueError("Could not decode image. Please upload a valid JPG or PNG.")
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    return img_rgb, gray


def preprocess(gray):
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, bw = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
    kernel_vert = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
    vertical_lines = cv2.morphologyEx(bw, cv2.MORPH_OPEN, kernel_vert)
    kernel_horz = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
    horizontal_lines = cv2.morphologyEx(bw, cv2.MORPH_OPEN, kernel_horz)
    combined = cv2.add(vertical_lines, horizontal_lines)
    grid_removed = cv2.subtract(bw, combined)
    kernel_vert2 = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 120))
    vertical_strong = cv2.morphologyEx(bw, cv2.MORPH_OPEN, kernel_vert2)
    cleaned = cv2.subtract(grid_removed, vertical_strong)
    edges = cv2.Canny(blur, 30, 150)
    return blur, bw, cleaned, edges


def detect_lead_strips(gray, edges, pad=70, n_strips=4):
    h, w = gray.shape
    proj = edges.sum(axis=1).astype(float)
    proj_smooth = gaussian_filter1d(proj, sigma=6)
    peaks, _ = find_peaks(proj_smooth, distance=80, height=np.max(proj_smooth) * 0.08)
    all_strips = [(i, max(0, int(y - pad)), min(h, int(y + pad))) for i, y in enumerate(peaks)]
    scores = []
    for idx, y1, y2 in all_strips:
        s = gray[y1:y2, :]
        edge_s = cv2.Canny(cv2.GaussianBlur(s, (5, 5), 0), 20, 120)
        energy = edge_s.sum() / (s.shape[0] * s.shape[1] + 1e-9)
        scores.append((idx, y1, y2, energy))
    scores_sorted = sorted(scores, key=lambda x: x[3], reverse=True)
    top_strips = sorted(scores_sorted[:n_strips], key=lambda x: x[1])
    return [(y1, y2) for (_, y1, y2, _) in top_strips], proj_smooth, peaks


def extract_signal_from_segment(seg_gray, fft_band=6):
    seg = seg_gray.astype(np.float32)
    seg = (seg - seg.min()) / (seg.max() - seg.min() + 1e-9)
    seg_inv = 1.0 - seg
    F = np.fft.fft2(seg_inv)
    Fshift = np.fft.fftshift(F)
    rows, cols = seg_inv.shape
    ccol = cols // 2
    mask = np.ones((rows, cols), np.uint8)
    mask[:, ccol - fft_band: ccol + fft_band] = 0
    Ff = Fshift * mask
    img_back = np.abs(np.fft.ifft2(np.fft.ifftshift(Ff)))
    img_back = (img_back - img_back.min()) / (img_back.max() - img_back.min() + 1e-9)
    col_idx = np.argmax(img_back, axis=0)
    col_med = median_filter(col_idx, size=9)
    win = 51 if cols > 101 else (33 if cols > 65 else 11)
    if win >= cols:
        win = cols - 1 if (cols - 1) % 2 == 1 else cols - 2
    if win < 3:
        win = 3
    col_smooth = savgol_filter(col_med.astype(float), window_length=win, polyorder=2)
    amp = -(col_smooth - np.mean(col_smooth))
    rng = amp.max() - amp.min()
    if rng > 1e-9:
        amp = (amp - amp.min()) / rng
        amp = (amp - 0.5) * 2.0
    else:
        amp = np.zeros_like(amp)
    return amp, img_back


def digitize_all_leads(gray, strip_ranges):
    row_to_leads = [["I","II","III"], ["aVR","aVL","aVF"], ["V1","V2","V3"], ["V4","V5","V6"]]
    h, w = gray.shape
    results, cleaned_segs = {}, {}
    for row_idx in range(min(len(strip_ranges), 4)):
        y1, y2 = strip_ranges[row_idx]
        strip = gray[y1:y2, :]
        col_w = w // 3
        for col in range(3):
            x1 = col * col_w
            x2 = w if col == 2 else (col + 1) * col_w
            seg = strip[:, x1:x2]
            lead_name = row_to_leads[row_idx][col]
            amp, img_back = extract_signal_from_segment(seg)
            results[lead_name] = amp
            cleaned_segs[lead_name] = img_back
    return results, cleaned_segs


def build_dataframe(signals):
    rows = []
    for lead, amp in signals.items():
        duration = 10.0 if lead == "II" else 2.5
        t = np.linspace(0, duration, len(amp))
        for ti, ai in zip(t, amp):
            rows.append({"lead": lead, "time_s": round(ti, 5), "amplitude_norm": round(float(ai), 6)})
    return pd.DataFrame(rows)


def detect_r_peaks(signal, min_distance_samples=30, min_height_factor=0.4):
    if len(signal) < 10:
        return np.array([])
    median_val = np.median(signal)
    sig_range = signal.max() - signal.min()
    height_thresh = median_val + min_height_factor * sig_range
    peaks, _ = find_peaks(signal, height=height_thresh, distance=min_distance_samples, prominence=0.15 * sig_range)
    return peaks


def compute_rr_features(peaks, duration_s):
    if len(peaks) < 3:
        return None
    total_len_est = int(peaks[-1] * (1 + 1.0 / max(len(peaks), 1))) + 1
    peak_times = peaks / total_len_est * duration_s
    rr_intervals = np.diff(peak_times)
    if len(rr_intervals) < 2:
        return None
    mean_rr   = float(np.mean(rr_intervals))
    std_rr    = float(np.std(rr_intervals))
    rmssd     = float(np.sqrt(np.mean(np.diff(rr_intervals) ** 2)))
    cv_rr     = std_rr / (mean_rr + 1e-9)
    hr_bpm    = 60.0 / (mean_rr + 1e-9)
    short_rr  = rr_intervals < 0.75 * mean_rr
    premature_ratio = float(short_rr.sum()) / len(rr_intervals)
    return {
        "hr_bpm": hr_bpm, "mean_rr_s": mean_rr, "std_rr_s": std_rr,
        "rmssd": rmssd, "cv_rr": cv_rr, "premature_ratio": premature_ratio,
        "n_peaks": len(peaks), "rr_intervals": rr_intervals,
    }


def classify_rhythm(features):
    if features is None:
        return "UNKNOWN", 0.0, "Fewer than 3 R-peaks detected."
    hr = features["hr_bpm"]
    cv = features["cv_rr"]
    pr = features["premature_ratio"]
    rmssd = features["rmssd"]
    if cv > 0.18:
        conf = min(1.0, (cv - 0.18) / 0.12 + 0.6)
        return "AFIB", conf, f"RR CV={cv:.3f} (>0.18). RMSSD={rmssd*1000:.1f}ms — highly irregular."
    if pr > 0.10 and cv < 0.18:
        conf = min(1.0, pr * 3 + 0.5)
        return "PVC", conf, f"{pr*100:.0f}% premature beats. CV={cv:.3f}."
    if hr > 100:
        conf = min(1.0, (hr - 100) / 50 + 0.7)
        return "TACHY", conf, f"HR={hr:.0f}bpm (>100). Regular rhythm."
    if hr < 60:
        conf = min(1.0, (60 - hr) / 30 + 0.7)
        return "BRADY", conf, f"HR={hr:.0f}bpm (<60). Regular rhythm."
    conf = min(1.0, 0.6 + (1 - cv) * 0.4)
    return "NSR", conf, f"HR={hr:.0f}bpm. CV={cv:.3f}. Regular, normal rate."


def fig_to_bytes(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="#050b18", edgecolor="none")
    buf.seek(0)
    return buf.read()


def dark_fig(img, title, cmap=None):
    fig, ax = plt.subplots(figsize=(5, 3), facecolor="#050b18")
    ax.set_facecolor("#0a1428")
    if cmap:
        ax.imshow(img, cmap=cmap)
    else:
        ax.imshow(img)
    ax.set_title(title, color="#e2e8f0", fontsize=10, pad=8)
    ax.axis("off")
    fig.tight_layout(pad=0.5)
    return fig
