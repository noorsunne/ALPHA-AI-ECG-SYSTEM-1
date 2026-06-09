"""
╔══════════════════════════════════════════════════════════════════╗
║          CardioLens AI  —  Merged ECG Analysis Platform         ║
║  Alpha ECG real processing  +  CardioLens UI  +  Groq AI Chat  ║
║                        Version 2.0                              ║
╚══════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import cv2
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.ndimage import median_filter, gaussian_filter1d
from scipy.signal import savgol_filter, find_peaks
import io
import time
import os
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv
load_dotenv()  # Load .env file automatically
import auth as _auth

# ── PDF generation ───────────────────────────────────────────────────────────
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

# ════════════════════════════════════════════════════════════════════════════
# ██  GROQ API KEY — Change this to your key  ██
# ════════════════════════════════════════════════════════════════════════════
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "gsk_YOUR_GROQ_API_KEY_HERE")
# Get a FREE key at: https://console.groq.com
# ════════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CardioLens AI — ECG Analysis Platform",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS — CardioLens dark hospital UI
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
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
  * { margin:0; padding:0; box-sizing:border-box; }
  .stApp { background-color: #050b18; }
  [data-testid="stSidebar"] {
      background: linear-gradient(180deg, #0a1020 0%, #050b18 100%);
      border-right: 1px solid rgba(56,130,246,0.18);
  }
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
  .cl-header p  { font-size: 14px; color: #64748b; margin: 8px 0 0; }
  .cl-badge {
      display: inline-block;
      background: linear-gradient(135deg, #1e3a5f, #1e2d4f);
      color: #60a5fa; font-size: 11px; font-family: monospace;
      padding: 4px 10px; border-radius: 20px; margin-left: 10px;
      border: 1px solid rgba(96,165,250,0.3);
  }

  /* Step cards */
  .step-card {
      background: linear-gradient(90deg, rgba(59,130,246,0.08) 0%, transparent 100%);
      border: 1px solid rgba(56,130,246,0.15);
      border-left: 3px solid #3b82f6;
      border-radius: 0 10px 10px 0;
      padding: 14px 20px;
      margin: 20px 0 14px;
  }
  .step-num { font-family: monospace; font-size: 10px; color: #3b82f6; letter-spacing: 2px; margin-right: 10px; }
  .step-title { font-size: 15px; font-weight: 700; color: #e2e8f0; }

  /* Metric boxes */
  .metric-row { display: flex; gap: 12px; flex-wrap: wrap; margin: 12px 0; }
  .metric-box {
      flex: 1; min-width: 120px;
      background: linear-gradient(135deg, #0a1428 0%, #0d1a35 100%);
      border: 1px solid rgba(56,130,246,0.2);
      border-radius: 12px; padding: 16px 20px; text-align: center;
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
  }
  .metric-box .m-label { font-size: 10px; color: #475569; font-family: monospace; letter-spacing: 1.5px; margin-bottom: 6px; }
  .metric-box .m-val   { font-size: 26px; font-weight: 800; color: #e2e8f0; }
  .metric-box .m-unit  { font-size: 12px; font-weight: 400; color: #64748b; margin-left: 2px; }
  .metric-box .m-sub   { font-size: 10px; color: #334155; margin-top: 4px; }

  /* Alert boxes */
  .info-box    { background: rgba(14,30,53,0.8); border: 1px solid rgba(30,58,95,0.8); border-radius: 10px; padding: 12px 16px; font-size: 13px; color: #93c5fd; margin: 10px 0; }
  .warn-box    { background: rgba(31,24,0,0.8); border: 1px solid rgba(61,46,0,0.8); border-radius: 10px; padding: 12px 16px; font-size: 13px; color: #fcd34d; margin: 10px 0; }
  .success-box { background: rgba(7,26,15,0.8); border: 1px solid rgba(15,61,30,0.8); border-radius: 10px; padding: 12px 16px; font-size: 13px; color: #4ade80; margin: 10px 0; }
  .danger-box  { background: rgba(26,8,8,0.8); border: 1px solid rgba(61,16,16,0.8); border-radius: 10px; padding: 12px 16px; font-size: 13px; color: #f87171; margin: 10px 0; }

  /* Rhythm cards */
  .rhythm-card { border-radius: 14px; padding: 24px 28px; margin: 14px 0; border: 1px solid; }
  .rhythm-card .r-label { font-size: 10px; font-family: monospace; letter-spacing: 2px; opacity: .5; margin-bottom: 10px; }
  .rhythm-card .r-name  { font-size: 30px; font-weight: 800; margin-bottom: 4px; }
  .rhythm-card .r-abbr  { font-size: 13px; font-family: monospace; opacity: .6; margin-bottom: 12px; }
  .rhythm-card .r-desc  { font-size: 14px; line-height: 1.7; opacity: .85; }
  .rhythm-normal  { background: rgba(7,26,15,0.9); border-color: rgba(16,61,30,0.8); color: #4ade80; }
  .rhythm-tachy   { background: rgba(26,8,8,0.9); border-color: rgba(61,16,16,0.8); color: #f87171; }
  .rhythm-brady   { background: rgba(14,30,53,0.9); border-color: rgba(30,58,95,0.8); color: #93c5fd; }
  .rhythm-afib    { background: rgba(31,24,0,0.9); border-color: rgba(61,46,0,0.8); color: #fcd34d; }
  .rhythm-pvc     { background: rgba(22,10,31,0.9); border-color: rgba(46,16,64,0.8); color: #c4b5fd; }
  .rhythm-unknown { background: rgba(15,19,32,0.9); border-color: rgba(30,37,56,0.8); color: #64748b; }

  /* Feature pills */
  .feat-row  { display: flex; gap: 10px; flex-wrap: wrap; margin: 12px 0; }
  .feat-pill {
      background: linear-gradient(135deg, #0a1428 0%, #0d1a35 100%);
      border: 1px solid rgba(56,130,246,0.2);
      border-radius: 10px; padding: 10px 14px; font-size: 12px; color: #e2e8f0;
      text-align: center; flex: 1; min-width: 95px;
  }
  .feat-pill .fp-l { color: #475569; font-family: monospace; font-size: 9px; letter-spacing: 1.5px; margin-bottom: 4px; }
  .feat-pill .fp-v { font-size: 20px; font-weight: 700; }

  /* Confidence bar */
  .conf-bg { background: rgba(30,37,56,0.8); border-radius: 6px; height: 8px; margin: 4px 0; }
  .conf-fill { height: 8px; border-radius: 6px; transition: width 0.5s ease; }

  /* Chat */
  .chat-msg { padding: 12px 16px; border-radius: 12px; margin: 8px 0; font-size: 13px; line-height: 1.65; }
  .chat-user { background: rgba(14,30,53,0.8); border: 1px solid rgba(30,58,95,0.6); color: #e2e8f0; }
  .chat-ai   { background: rgba(7,26,15,0.8); border: 1px solid rgba(15,61,30,0.6); color: #d1fae5; }

  /* Sidebar */
  .sidebar-logo { font-size: 26px; font-weight: 900; color: #e2e8f0; margin-bottom: 4px; }
  .sidebar-logo span { color: #3b82f6; }
  .sidebar-section { font-size: 11px; font-weight: 700; color: #3b82f6; letter-spacing: 2px; text-transform: uppercase; margin: 16px 0 8px; }

  /* Stat cards for top dashboard */
  .stat-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 14px; margin: 16px 0; }
  .stat-card {
      background: linear-gradient(135deg, #0a1428 0%, #0d1a35 100%);
      border: 1px solid rgba(56,130,246,0.2);
      border-radius: 14px; padding: 20px 24px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
  }
  .stat-card .sc-label { font-size: 11px; color: #475569; font-family: monospace; letter-spacing: 1.5px; }
  .stat-card .sc-val   { font-size: 32px; font-weight: 800; color: #e2e8f0; margin: 6px 0 2px; }
  .stat-card .sc-sub   { font-size: 11px; color: #334155; }

  /* Tab styling */
  [data-baseweb="tab-list"] { background: transparent; border-bottom: 1px solid rgba(56,130,246,0.15); }
  [data-baseweb="tab"] { color: #64748b !important; font-weight: 600; }
  [aria-selected="true"] { color: #3b82f6 !important; border-bottom: 2px solid #3b82f6 !important; }

  /* Download buttons */
  [data-testid="stDownloadButton"] button {
      background: linear-gradient(135deg, #0a1428 0%, #0d1a35 100%) !important;
      border: 1px solid rgba(56,130,246,0.3) !important;
      color: #e2e8f0 !important; border-radius: 10px !important; width: 100%;
      font-weight: 600 !important;
  }
  [data-testid="stDownloadButton"] button:hover {
      border-color: #3b82f6 !important; color: #60a5fa !important;
      box-shadow: 0 0 15px rgba(59,130,246,0.2) !important;
  }

  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

  /* Stbutton primary */
  .stButton > button {
      background: linear-gradient(135deg, #1e3a5f 0%, #1e2d4f 100%) !important;
      border: 1px solid rgba(59,130,246,0.4) !important;
      color: #e2e8f0 !important; border-radius: 10px !important;
      font-weight: 600 !important;
  }
  .stButton > button:hover {
      background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%) !important;
      border-color: #3b82f6 !important; box-shadow: 0 0 20px rgba(59,130,246,0.3) !important;
  }
</style>
""", unsafe_allow_html=True)


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
#  ECG PROCESSING PIPELINE
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


# ═══════════════════════════════════════════════════════════════════════════════
#  GROQ AI CHATBOT
# ═══════════════════════════════════════════════════════════════════════════════

def get_groq_client():
    """Returns Groq client using hardcoded API key or user-provided key."""
    key = st.session_state.get("groq_api_key_override", "").strip()
    if not key:
        key = GROQ_API_KEY
    if not key or key == "gsk_YOUR_GROQ_API_KEY_HERE":
        return None
    try:
        return Groq(api_key=key)
    except Exception:
        return None


def build_ecg_context(rhythm_key, features, signals):
    if not rhythm_key:
        return "No ECG analysis has been performed yet."
    cls = RHYTHM_CLASSES[rhythm_key]
    ctx = f"""ECG Analysis Results:
- Rhythm: {cls['name']} ({cls['abbr']})
- Clinical Urgency: {cls['urgency']}
"""
    if features:
        ctx += f"""- Heart Rate: {features['hr_bpm']:.1f} bpm
- Mean RR Interval: {features['mean_rr_s']*1000:.0f} ms
- RR CV (variability): {features['cv_rr']:.4f}
- RMSSD: {features['rmssd']*1000:.1f} ms
- Premature Beats: {features['premature_ratio']*100:.1f}%
- R-peaks detected: {features['n_peaks']}
"""
    if signals:
        ctx += f"- Leads extracted: {', '.join(signals.keys())}\n"
    ctx += f"- Clinical note: {cls['clinical']}\n"
    return ctx


def chat_with_groq(client, user_message, chat_history, ecg_context):
    system_prompt = f"""You are CardioLens AI Assistant, an expert AI cardiologist assistant specializing in ECG interpretation.
You help doctors, students, and patients understand ECG results in a clear, professional manner.

Current ECG Analysis on File:
{ecg_context}

Guidelines:
- Be concise and clinically accurate
- Always recommend consulting a real cardiologist for medical decisions
- Explain medical terms in plain language when helpful
- Reference the actual ECG data when answering questions
- Use bullet points for clarity when appropriate
- Never diagnose — provide educational information only"""

    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history[-8:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=800,
        temperature=0.3,
    )
    return response.choices[0].message.content


# ═══════════════════════════════════════════════════════════════════════════════
#  PDF REPORT GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

def generate_pdf_report(patient_name, patient_age, patient_gender, patient_id,
                         rhythm_key, features, confidence, explanation,
                         waveform_png_bytes=None, classification_png_bytes=None):
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

    # Header
    header_data = [[
        Paragraph("<b>🫀 CardioLens AI</b>", sty("hL", fontSize=18, fontName="Helvetica-Bold",
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

    # Patient Info
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

    # Rhythm Result
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

    # Measurements
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

    # Recommendations
    story.append(Paragraph("Clinical Recommendations", h2_style))
    story.append(Paragraph(f"<b>Clinical Note:</b> {cls['clinical']}", body_style))
    story.append(Spacer(1, 3*mm))
    for i, rec in enumerate(cls["recommendations"], 1):
        story.append(Paragraph(f"  {i}. {rec}", body_style))
    story.append(Spacer(1, 8*mm))

    # Waveform images
    if waveform_png_bytes:
        story.append(Paragraph("ECG Signal Visualization", h2_style))
        story.append(RLImage(io.BytesIO(waveform_png_bytes), width=165*mm, height=60*mm))
        story.append(Spacer(1, 4*mm))

    if classification_png_bytes:
        story.append(Paragraph("R-Peak Detection & RR Tachogram", h2_style))
        story.append(RLImage(io.BytesIO(classification_png_bytes), width=165*mm, height=65*mm))
        story.append(Spacer(1, 8*mm))

    # Disclaimer
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#d1d5db")))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        "⚕️ MEDICAL DISCLAIMER: This report is generated by an AI-based algorithm for educational and research "
        "purposes only. It is NOT a substitute for professional medical advice, diagnosis, or treatment. "
        "Always consult a qualified cardiologist for clinical ECG interpretation. CardioLens AI v2.0",
        small_style
    ))

    doc.build(story)
    buf.seek(0)
    return buf.read()


# ═══════════════════════════════════════════════════════════════════════════════
#  SESSION STATE INIT
# ═══════════════════════════════════════════════════════════════════════════════
defaults = {
    "chat_history": [],
    "groq_api_key_override": "",
    "analysis_done": False,
    "ecg_context": "",
    "rhythm_key": None,
    "features": None,
    "signals": None,
    "waveform_png": None,
    "classification_png": None,
    # Auth
    "auth_token": None,
    "auth_user": None,
    "login_error": "",
    "register_mode": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ═══════════════════════════════════════════════════════════════════════════════
#  LOGIN CSS (injected once, applies everywhere)
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
.login-wrap {
    max-width:440px; margin:60px auto 0; padding:0 16px;
}
.login-card {
    background:rgba(10,20,40,0.92);
    border:1px solid rgba(59,130,246,0.25);
    border-top:3px solid #3b82f6;
    border-radius:18px;
    padding:40px 36px 32px;
    box-shadow:0 0 60px rgba(59,130,246,0.12);
}
.login-logo {
    text-align:center;
    font-size:42px;
    margin-bottom:4px;
}
.login-title {
    text-align:center;
    font-size:22px;
    font-weight:800;
    color:#e2e8f0;
    margin-bottom:4px;
}
.login-sub {
    text-align:center;
    font-size:13px;
    color:#64748b;
    margin-bottom:24px;
}
.role-grid {
    display:flex;
    gap:8px;
    margin-bottom:20px;
}
.role-btn {
    flex:1;
    text-align:center;
    padding:10px 4px;
    border-radius:10px;
    border:1px solid rgba(59,130,246,0.25);
    background:rgba(15,25,50,0.8);
    color:#94a3b8;
    font-size:12px;
    font-weight:600;
    cursor:pointer;
    transition:all 0.2s;
}
.role-btn.active {
    background:rgba(59,130,246,0.15);
    border-color:#3b82f6;
    color:#60a5fa;
}
.login-divider {
    text-align:center;
    color:#334155;
    font-size:11px;
    margin:14px 0;
    letter-spacing:2px;
}
.demo-creds {
    background:rgba(15,25,50,0.6);
    border:1px solid rgba(59,130,246,0.12);
    border-radius:10px;
    padding:12px 16px;
    margin-top:16px;
}
.demo-creds p { font-size:11px; color:#64748b; margin:2px 0; }
.demo-creds b { color:#94a3b8; }
/* Dashboard cards */
.dash-stat {
    background:rgba(10,20,40,0.85);
    border:1px solid rgba(56,130,246,0.18);
    border-radius:14px;
    padding:20px 18px;
    text-align:center;
}
.dash-stat-val { font-size:32px; font-weight:800; color:#3b82f6; }
.dash-stat-lbl { font-size:11px; color:#64748b; margin-top:4px; letter-spacing:1px; text-transform:uppercase; }
.dash-stat-sub { font-size:12px; color:#475569; margin-top:6px; }
.user-table th { background:rgba(15,25,50,0.8) !important; color:#60a5fa !important; font-size:12px; }
.role-badge-admin   { background:rgba(239,68,68,0.15);  color:#ef4444; border:1px solid rgba(239,68,68,0.3);  padding:2px 8px; border-radius:20px; font-size:11px; }
.role-badge-doctor  { background:rgba(59,130,246,0.15); color:#60a5fa; border:1px solid rgba(59,130,246,0.3); padding:2px 8px; border-radius:20px; font-size:11px; }
.role-badge-patient { background:rgba(16,185,129,0.15); color:#10b981; border:1px solid rgba(16,185,129,0.3); padding:2px 8px; border-radius:20px; font-size:11px; }
.profile-card {
    background:rgba(10,20,40,0.85);
    border:1px solid rgba(56,130,246,0.18);
    border-radius:14px;
    padding:24px;
    margin-bottom:18px;
}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  AUTH HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def do_logout():
    st.session_state.auth_token = None
    st.session_state.auth_user  = None
    st.session_state.login_error = ""
    st.rerun()

def current_user():
    if not st.session_state.auth_token:
        return None
    data = _auth.verify_token(st.session_state.auth_token)
    if not data:
        st.session_state.auth_token = None
        return None
    return st.session_state.auth_user


# ═══════════════════════════════════════════════════════════════════════════════
#  LOGIN PAGE
# ═══════════════════════════════════════════════════════════════════════════════
def show_login_page():
    st.markdown('<div class="login-wrap">', unsafe_allow_html=True)
    st.markdown("""
    <div class="login-card">
      <div class="login-logo">🫀</div>
      <div class="login-title"><span style="color:#3b82f6;">Cardio</span>Lens AI</div>
      <div class="login-sub">ECG Analysis Platform — Secure Login</div>
    </div>
    """, unsafe_allow_html=True)

    tab_login, tab_register = st.tabs(["🔐  Sign In", "📝  Register"])

    with tab_login:
        st.markdown("#### Select Your Role")
        role_col1, role_col2, role_col3 = st.columns(3)
        with role_col1:
            if st.button("🛡️ Admin", use_container_width=True):
                st.session_state["login_role_hint"] = "admin"
        with role_col2:
            if st.button("👨‍⚕️ Doctor", use_container_width=True):
                st.session_state["login_role_hint"] = "doctor"
        with role_col3:
            if st.button("🧑‍🤝‍🧑 Patient", use_container_width=True):
                st.session_state["login_role_hint"] = "patient"

        role_hint = st.session_state.get("login_role_hint", "doctor")
        demo = {"admin": ("admin","admin123"), "doctor": ("doctor1","doctor123"), "patient": ("patient1","patient123")}
        hint_u, hint_p = demo[role_hint]

        st.markdown("---")
        username = st.text_input("Username", placeholder=f"e.g. {hint_u}", key="li_user")
        password = st.text_input("Password", type="password", placeholder="Enter password", key="li_pass")

        if st.button("🔐  Sign In", use_container_width=True, type="primary"):
            if not username or not password:
                st.error("Please enter username and password")
            else:
                result = _auth.login(username.strip(), password)
                if result:
                    st.session_state.auth_token = result["token"]
                    st.session_state.auth_user  = result["user"]
                    st.session_state.login_error = ""
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")

        st.markdown(f"""
        <div class="demo-creds">
          <p><b>Demo — Admin &nbsp;&nbsp;</b> admin / admin123</p>
          <p><b>Demo — Doctor &nbsp;</b> doctor1 / doctor123</p>
          <p><b>Demo — Patient</b> patient1 / patient123</p>
        </div>
        """, unsafe_allow_html=True)

    with tab_register:
        st.markdown("#### Create New Account")
        r_role = st.selectbox("Register as", ["doctor","patient"], key="reg_role")
        r_full = st.text_input("Full Name", key="reg_name")
        r_user = st.text_input("Username", key="reg_user")
        r_email = st.text_input("Email", key="reg_email")
        r_pass = st.text_input("Password", type="password", key="reg_pass")
        r_pass2 = st.text_input("Confirm Password", type="password", key="reg_pass2")
        r_spec = ""
        r_pid = ""
        r_age = 25
        r_gender = "Male"
        if r_role == "doctor":
            r_spec = st.text_input("Specialization", placeholder="e.g. Cardiologist", key="reg_spec")
        else:
            r_pid = st.text_input("Patient ID (optional)", placeholder="e.g. PT-003", key="reg_pid")
            r_age = st.number_input("Age", 1, 120, 30, key="reg_age")
            r_gender = st.selectbox("Gender", ["Male","Female","Other"], key="reg_gender")

        if st.button("📝  Create Account", use_container_width=True, type="primary"):
            if not all([r_full, r_user, r_email, r_pass]):
                st.error("All fields required")
            elif r_pass != r_pass2:
                st.error("Passwords do not match")
            elif len(r_pass) < 6:
                st.error("Password must be at least 6 characters")
            else:
                ok, msg = _auth.create_user(
                    r_user.strip(), r_pass, r_role, r_full, r_email,
                    r_spec if r_role=="doctor" else None,
                    r_pid if r_role=="patient" else None,
                    r_age if r_role=="patient" else None,
                    r_gender if r_role=="patient" else None,
                )
                if ok:
                    st.success(f"✅ Account created! You can now sign in as **{r_user}**")
                else:
                    st.error(f"❌ {msg}")

    st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  ADMIN DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
def show_admin_dashboard(user):
    stats = _auth.get_stats()
    all_users = _auth.get_all_users()
    ecg_records = _auth.get_ecg_records()

    # Header
    st.markdown(f"""
    <div class="cl-header">
      <h1>🛡️ Admin <span>Dashboard</span></h1>
      <p>Welcome, <b>{user['full_name']}</b> · CardioLens AI Management Panel</p>
    </div>
    """, unsafe_allow_html=True)

    # Stats row
    c1,c2,c3,c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="dash-stat"><div class="dash-stat-val" style="color:#3b82f6">{stats["doctors"]}</div><div class="dash-stat-lbl">Doctors</div><div class="dash-stat-sub">Active</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="dash-stat"><div class="dash-stat-val" style="color:#10b981">{stats["patients"]}</div><div class="dash-stat-lbl">Patients</div><div class="dash-stat-sub">Registered</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="dash-stat"><div class="dash-stat-val" style="color:#f59e0b">{stats["ecg_total"]}</div><div class="dash-stat-lbl">ECG Records</div><div class="dash-stat-sub">Total</div></div>', unsafe_allow_html=True)
    with c4:
        total_users = stats["doctors"] + stats["patients"]
        st.markdown(f'<div class="dash-stat"><div class="dash-stat-val" style="color:#8b5cf6">{total_users}</div><div class="dash-stat-lbl">Total Users</div><div class="dash-stat-sub">Excl. admins</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab_users, tab_ecg, tab_add = st.tabs(["👥  All Users", "📊  ECG Records", "➕  Add User"])

    with tab_users:
        st.markdown("#### User Management")
        role_filter = st.selectbox("Filter by role", ["All","admin","doctor","patient"], key="adm_filter")
        filtered = [u for u in all_users if role_filter=="All" or u["role"]==role_filter]

        for u in filtered:
            badge_cls = f"role-badge-{u['role']}"
            col_a, col_b, col_c = st.columns([4,2,1])
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

    with tab_ecg:
        st.markdown("#### ECG Analysis Records")
        if ecg_records:
            df_ecg = pd.DataFrame(ecg_records)
            display_cols = ["created_at","patient_username","doctor_username","rhythm","heart_rate","filename"]
            display_cols = [c for c in display_cols if c in df_ecg.columns]
            st.dataframe(df_ecg[display_cols].rename(columns={
                "created_at":"Date","patient_username":"Patient","doctor_username":"Doctor",
                "rhythm":"Rhythm","heart_rate":"HR (bpm)","filename":"File"
            }), use_container_width=True)

            if stats["rhythm_counts"]:
                st.markdown("#### Rhythm Distribution")
                fig, ax = plt.subplots(figsize=(6,3), facecolor="#050b18")
                ax.set_facecolor("#080f1e")
                rhythms = list(stats["rhythm_counts"].keys())
                counts  = list(stats["rhythm_counts"].values())
                colors_list = ["#3b82f6","#10b981","#f59e0b","#ef4444","#8b5cf6","#14b8a6"]
                ax.bar(rhythms, counts, color=colors_list[:len(rhythms)], edgecolor="#1e3a5f", linewidth=0.5)
                ax.set_xlabel("Rhythm", color="#94a3b8")
                ax.set_ylabel("Count", color="#94a3b8")
                ax.tick_params(colors="#94a3b8")
                for spine in ax.spines.values(): spine.set_edgecolor("#1e3a5f")
                buf2 = io.BytesIO()
                fig.savefig(buf2, format="png", dpi=80, bbox_inches="tight", facecolor="#050b18")
                plt.close(fig)
                st.image(buf2.getvalue())
        else:
            st.info("No ECG records yet.")

    with tab_add:
        st.markdown("#### Add New User")
        na_role = st.selectbox("Role", ["doctor","patient","admin"], key="na_role")
        na_name = st.text_input("Full Name", key="na_name")
        na_user = st.text_input("Username", key="na_user")
        na_email = st.text_input("Email", key="na_email")
        na_pass = st.text_input("Password", type="password", key="na_pass")
        na_spec = na_pid = ""
        na_age, na_gender = 30, "Male"
        if na_role == "doctor":
            na_spec = st.text_input("Specialization", key="na_spec")
        elif na_role == "patient":
            na_pid  = st.text_input("Patient ID", key="na_pid")
            na_age  = st.number_input("Age", 1, 120, 30, key="na_age")
            na_gender = st.selectbox("Gender", ["Male","Female","Other"], key="na_gender")

        if st.button("➕ Create User", type="primary"):
            if not all([na_name, na_user, na_email, na_pass]):
                st.error("All fields required")
            else:
                ok, msg = _auth.create_user(na_user, na_pass, na_role, na_name, na_email,
                                             na_spec or None, na_pid or None,
                                             na_age if na_role=="patient" else None,
                                             na_gender if na_role=="patient" else None)
                if ok:
                    st.success(f"✅ {msg}")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")


# ═══════════════════════════════════════════════════════════════════════════════
#  DOCTOR DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
def show_doctor_dashboard(user):
    my_records = _auth.get_ecg_records(user["username"], role="doctor")
    patients   = _auth.get_all_users(role="patient")

    st.markdown(f"""
    <div class="cl-header">
      <h1>👨‍⚕️ <span>Doctor</span> Dashboard</h1>
      <p>Welcome, <b>{user['full_name']}</b> · {user.get('specialization','Cardiologist')} · CardioLens AI</p>
    </div>
    """, unsafe_allow_html=True)

    c1,c2,c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="dash-stat"><div class="dash-stat-val" style="color:#3b82f6">{len(my_records)}</div><div class="dash-stat-lbl">My ECG Reports</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="dash-stat"><div class="dash-stat-val" style="color:#10b981">{len(patients)}</div><div class="dash-stat-lbl">Total Patients</div></div>', unsafe_allow_html=True)
    with c3:
        unique_pts = len(set(r["patient_username"] for r in my_records)) if my_records else 0
        st.markdown(f'<div class="dash-stat"><div class="dash-stat-val" style="color:#f59e0b">{unique_pts}</div><div class="dash-stat-lbl">My Patients</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    tab_ecg_tool, tab_my_reports, tab_patients = st.tabs(["📊  ECG Analysis", "📋  My Reports", "👥  Patients"])

    with tab_ecg_tool:
        st.info("💡 Use the ECG Analysis tool below — results will be saved to your records.")
        _show_ecg_analysis_ui(user)

    with tab_my_reports:
        if my_records:
            for r in my_records[:20]:
                with st.expander(f"📋 {r['patient_username']} — {r['rhythm']} — {r['created_at'][:16]}"):
                    c_a, c_b, c_c = st.columns(3)
                    c_a.metric("Heart Rate", f"{r['heart_rate']:.0f} bpm" if r['heart_rate'] else "—")
                    c_b.metric("Rhythm", r['rhythm'] or "—")
                    c_c.metric("RMSSD", f"{r['rmssd']:.1f}" if r['rmssd'] else "—")
        else:
            st.info("No ECG reports yet. Use the ECG Analysis tab to create your first report.")

    with tab_patients:
        st.markdown("#### Registered Patients")
        for p in patients:
            col1, col2 = st.columns([3,1])
            with col1:
                st.markdown(f"**{p['full_name']}** (`{p['username']}`)")
                st.caption(f"Age: {p.get('age','—')} · Gender: {p.get('gender','—')} · ID: {p.get('patient_id','—')}")
            with col2:
                st.caption(p.get("email",""))
            st.divider()


# ═══════════════════════════════════════════════════════════════════════════════
#  PATIENT DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
def show_patient_dashboard(user):
    my_records = _auth.get_ecg_records(user["username"], role="patient")

    st.markdown(f"""
    <div class="cl-header">
      <h1>🧑‍🤝‍🧑 <span>Patient</span> Dashboard</h1>
      <p>Welcome, <b>{user['full_name']}</b> · Patient ID: {user.get('patient_id','—')} · CardioLens AI</p>
    </div>
    """, unsafe_allow_html=True)

    c1,c2,c3 = st.columns(3)
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
    tab_ecg_tool, tab_history, tab_profile = st.tabs(["📊  ECG Analysis", "📋  My History", "👤  My Profile"])

    with tab_ecg_tool:
        _show_ecg_analysis_ui(user)

    with tab_history:
        if my_records:
            for r in my_records:
                with st.expander(f"📅 {r['created_at'][:16]} — {r['rhythm']}"):
                    c_a, c_b, c_c = st.columns(3)
                    c_a.metric("Heart Rate", f"{r['heart_rate']:.0f} bpm" if r['heart_rate'] else "—")
                    c_b.metric("Rhythm", r["rhythm"] or "—")
                    c_c.metric("RMSSD", f"{r['rmssd']:.1f}" if r['rmssd'] else "—")
                    if r.get("doctor_username"):
                        st.caption(f"Analysed by: Dr. {r['doctor_username']}")
        else:
            st.info("No ECG records yet. Upload an ECG in the 'ECG Analysis' tab.")

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


# ═══════════════════════════════════════════════════════════════════════════════
#  ECG ANALYSIS UI (shared wrapper — injected into doctor & patient dashboards)
# ═══════════════════════════════════════════════════════════════════════════════
def _show_ecg_analysis_ui(user):
    """Renders the sidebar-less ECG analysis + chat + PDF inside a dashboard tab."""

    # Patient info pre-filled from user profile
    if user["role"] == "patient":
        patient_name   = user.get("full_name","")
        patient_age    = user.get("age") or 45
        patient_gender = user.get("gender","Male")
        patient_id     = user.get("patient_id","")
    else:
        # Doctor fills in patient info inline
        c1,c2,c3,c4 = st.columns(4)
        patient_name   = c1.text_input("Patient Name", key=f"pn_{user['username']}")
        patient_age    = c2.number_input("Age", 1, 120, 45, key=f"pa_{user['username']}")
        patient_gender = c3.selectbox("Gender", ["Male","Female","Other"], key=f"pg_{user['username']}")
        patient_id     = c4.text_input("Patient ID", key=f"pi_{user['username']}")

    # Processing settings in expander
    with st.expander("⚙️ Processing Settings", expanded=False):
        sc1,sc2,sc3,sc4,sc5 = st.columns(5)
        n_strips      = sc1.slider("ECG rows",2,4,4,key=f"ns_{user['username']}")
        pad           = sc2.slider("Crop padding",40,120,70,key=f"pd_{user['username']}")
        fft_band      = sc3.slider("FFT width",2,15,6,key=f"fb_{user['username']}")
        classify_lead = sc4.selectbox("Classify from",["II","I","V1","V2","aVR"],key=f"cl_{user['username']}")
        r_sensitivity = sc5.slider("R-peak sens.",0.2,0.7,0.4,0.05,key=f"rs_{user['username']}")

    uploaded = st.file_uploader(
        "Upload ECG image (JPG/PNG, 300 DPI recommended)",
        type=["png","jpg","jpeg"],
        key=f"ecg_upload_{user['username']}"
    )

    if uploaded is None:
        st.markdown('<div class="info-box">👆 Upload a JPG or PNG ECG image to begin.</div>', unsafe_allow_html=True)
        return

    # ── Reuse the existing ECG processing pipeline (same as original app) ──
    # We call the same functions that exist below in the original code
    _run_ecg_pipeline(uploaded, patient_name, patient_age, patient_gender, patient_id,
                      n_strips, pad, fft_band, classify_lead, r_sensitivity, user)



# ═══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════════════════
#  _run_ecg_pipeline — wraps the full ECG analysis + chat + PDF tabs
# ═══════════════════════════════════════════════════════════════════════════════
def _run_ecg_pipeline(uploaded, patient_name, patient_age, patient_gender, patient_id,
                      n_strips, pad, fft_band, classify_lead, r_sensitivity, current_user_obj):
    """Full ECG processing pipeline — called from Doctor/Patient dashboards."""

    # ── STEP 2+ ──────────────────────────────────────────────────────────────
    # (Original tab_analysis body, adapted)

    if uploaded.size > 20 * 1024 * 1024:
        st.markdown('<div class="warn-box">⚠ File too large (max 20 MB). Please resize or compress.</div>', unsafe_allow_html=True)
        st.stop()

    # STEP 2: Preprocessing
    st.markdown('<div class="step-card"><span class="step-num">STEP 02</span><span class="step-title">Image Preprocessing — Grayscale · Denoise · Grid Removal</span></div>', unsafe_allow_html=True)

    with st.spinner("Preprocessing ECG image…"):
        t_start = time.time()
        try:
            img_rgb, gray = load_and_grayscale(uploaded)
        except ValueError as e:
            st.error(str(e)); st.stop()
        blur, bw, cleaned, edges = preprocess(gray)

    h_img, w_img = gray.shape
    c1, c2, c3 = st.columns(3)
    with c1:
        fig = dark_fig(img_rgb, "Original ECG")
        st.pyplot(fig, use_container_width=True); plt.close(fig)
    with c2:
        fig = dark_fig(gray, "Grayscale", "gray")
        st.pyplot(fig, use_container_width=True); plt.close(fig)
    with c3:
        fig = dark_fig(cleaned, "Grid Removed (Binary)", "gray")
        st.pyplot(fig, use_container_width=True); plt.close(fig)

    st.markdown(f'<div class="info-box">📐 Image: <b>{w_img}×{h_img}px</b> · {uploaded.type} · {uploaded.size/1024:.1f} KB</div>', unsafe_allow_html=True)

    # STEP 3: Lead Detection
    st.markdown('<div class="step-card"><span class="step-num">STEP 03</span><span class="step-title">ECG Lead Strip Detection</span></div>', unsafe_allow_html=True)

    with st.spinner("Detecting lead strips via horizontal edge projection…"):
        strip_ranges, proj_smooth, peaks_found = detect_lead_strips(gray, edges, pad=pad, n_strips=n_strips)

    n_detected = len(strip_ranges)
    if n_detected == 0:
        st.markdown('<div class="warn-box">⚠ No lead strips detected. Try increasing strip padding or uploading a higher-quality image.</div>', unsafe_allow_html=True)
        st.stop()

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
    st.markdown(f'<div class="success-box">✓ {n_detected} row(s) detected → up to {n_detected*3} leads will be extracted.</div>', unsafe_allow_html=True)

    # STEP 4: Signal Extraction
    st.markdown('<div class="step-card"><span class="step-num">STEP 04</span><span class="step-title">Signal Reconstruction & Digitization — FFT · SavGol · Column Scan</span></div>', unsafe_allow_html=True)

    with st.spinner("Extracting waveforms…"):
        signals, cleaned_segs = digitize_all_leads(gray, strip_ranges)
        df_out = build_dataframe(signals)
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
    st.markdown('<div class="step-card"><span class="step-num">STEP 05</span><span class="step-title">Original vs Digitized Signal Comparison</span></div>', unsafe_allow_html=True)

    lead_names = list(signals.keys())
    selected_leads = st.multiselect(
        "Select leads to visualize",
        options=lead_names,
        default=lead_names[:4] if len(lead_names) >= 4 else lead_names,
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
        fig.suptitle("ECG Image vs Reconstructed Signal", color="#e2e8f0", fontsize=13, y=1.01)
        fig.tight_layout(pad=1.5)
        st.pyplot(fig, use_container_width=True)
        waveform_png = fig_to_bytes(fig)
        st.session_state.waveform_png = waveform_png
        plt.close(fig)

    # STEP 6: Rhythm Classification
    st.markdown('<div class="step-card"><span class="step-num">STEP 06</span><span class="step-title">Rhythm Classification — R-Peak Detection · HR · HRV</span></div>', unsafe_allow_html=True)

    clf_lead = classify_lead if classify_lead in signals else list(signals.keys())[0]
    clf_signal = signals[clf_lead]
    clf_duration = 10.0 if clf_lead == "II" else 2.5

    with st.spinner(f"Classifying rhythm from Lead {clf_lead}…"):
        samples_per_sec = len(clf_signal) / clf_duration
        min_dist = max(10, int(samples_per_sec * 0.4))
        r_peaks = detect_r_peaks(clf_signal, min_distance_samples=min_dist, min_height_factor=r_sensitivity)
        features = compute_rr_features(r_peaks, clf_duration)
        rhythm_key, confidence, explanation = classify_rhythm(features)

    # Save to session state
    st.session_state.rhythm_key = rhythm_key
    st.session_state.features = features
    st.session_state.signals = signals
    st.session_state.ecg_context = build_ecg_context(rhythm_key, features, signals)
    st.session_state.analysis_done = True

    # Save ECG record to DB
    try:
        _auth.save_ecg_record(
            patient_username=patient_name or (current_user_obj["username"] if current_user_obj["role"]=="patient" else "unknown"),
            doctor_username=current_user_obj["username"] if current_user_obj["role"]=="doctor" else None,
            filename=uploaded.name if hasattr(uploaded,"name") else "ecg.jpg",
            heart_rate=features.get("hr_bpm"),
            rhythm=RHYTHM_CLASSES[rhythm_key]["abbr"],
            rmssd=features.get("rmssd"),
            hr_cv=features.get("hr_cv"),
            analysis_json=str(features)[:500]
        )
    except Exception:
        pass  # Non-blocking

    cls = RHYTHM_CLASSES[rhythm_key]

    # Result card
    st.markdown(f"""
    <div class="rhythm-card {cls['css']}">
      <div class="r-label">RHYTHM CLASSIFICATION RESULT</div>
      <div class="r-name">{cls['emoji']} {cls['name']}</div>
      <div class="r-abbr">{cls['abbr']} · HR: {cls['hr_range']} · Urgency: <b>{cls['urgency']}</b></div>
      <div class="r-desc">{cls['desc']}</div>
    </div>
    """, unsafe_allow_html=True)

    # Feature pills
    if features:
        hr_s  = f"{features['hr_bpm']:.0f}"
        rr_s  = f"{features['mean_rr_s']*1000:.0f}ms"
        cv_s  = f"{features['cv_rr']:.3f}"
        np_s  = str(features['n_peaks'])
        pr_s  = f"{features['premature_ratio']*100:.1f}%"
        cf_s  = f"{confidence*100:.0f}%"
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
    bc = RHYTHM_BAR_COLORS[rhythm_key]
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
    classification_png = fig_to_bytes(fig)
    st.session_state.classification_png = classification_png
    plt.close(fig)

    st.markdown('<div class="warn-box">⚕️ <b>Medical Disclaimer:</b> Rule-based AI classification for educational/research purposes only. NOT a medical diagnosis. Always consult a qualified cardiologist.</div>', unsafe_allow_html=True)

    # STEP 7: Downloads
    st.markdown('<div class="step-card"><span class="step-num">STEP 07</span><span class="step-title">Download Results</span></div>', unsafe_allow_html=True)

    if features:
        df_out["rhythm"]     = cls["name"]
        df_out["hr_bpm"]     = round(features["hr_bpm"], 1)
        df_out["rr_cv"]      = round(features["cv_rr"], 4)
        df_out["confidence"] = round(confidence, 3)

    csv_bytes = df_out.to_csv(index=False).encode("utf-8")
    dc1, dc2, dc3 = st.columns(3)
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


    # ───────────────────────────────────────────────────────────────────────────────
    #  TAB 2 — AI CHATBOT
    # ───────────────────────────────────────────────────────────────────────────────


    # ═══════════════════════════════════════════════════════════════════════════════
    #  SIDEBAR (only shown when not logged in as fallback — normally hidden)
    # ═══════════════════════════════════════════════════════════════════════════════


    # ═══════════════════════════════════════════════════════════════════════════════
#  MAIN AUTH ROUTER — Entry point
# ═══════════════════════════════════════════════════════════════════════════════
user = current_user()

if user is None:
    # ── Not logged in → show login page ─────────────────────────────────────
    show_login_page()

else:
    # ── Logged in → show role-based dashboard ───────────────────────────────
    with st.sidebar:
        st.markdown('<div class="sidebar-logo">🫀 <span>Cardio</span>Lens</div>', unsafe_allow_html=True)
        role_badge_color = {"admin":"#ef4444","doctor":"#3b82f6","patient":"#10b981"}.get(user["role"],"#64748b")
        st.markdown(f'''
        <div style="margin:8px 0 16px;">
          <div style="font-size:14px;font-weight:700;color:#e2e8f0;">{user["full_name"]}</div>
          <div style="font-size:11px;color:{role_badge_color};font-weight:600;text-transform:uppercase;letter-spacing:1px;">{user["role"]}</div>
          <div style="font-size:11px;color:#475569;">{user.get("email","")}</div>
        </div>
        ''', unsafe_allow_html=True)
        st.markdown("---")

        # Groq key override
        groq_active = GROQ_API_KEY and GROQ_API_KEY != "gsk_YOUR_GROQ_API_KEY_HERE"
        st.markdown('<div class="sidebar-section">🤖 AI Chatbot</div>', unsafe_allow_html=True)
        if groq_active:
            st.markdown('<div class="success-box">✓ Groq AI Active — LLaMA-3.3-70B</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="warn-box">⚠ Set GROQ_API_KEY to enable AI</div>', unsafe_allow_html=True)
        override_key = st.text_input(
            "Override Groq Key", value=st.session_state.groq_api_key_override,
            type="password", placeholder="gsk_...", key="sidebar_groq_override"
        )
        if override_key != st.session_state.groq_api_key_override:
            st.session_state.groq_api_key_override = override_key

        st.markdown("---")
        st.caption(f"CardioLens AI v2.0\n{user['role'].title()} Portal")
        st.markdown("---")
        if st.button("🚪 Sign Out", use_container_width=True):
            do_logout()

    # Route to correct dashboard
    role = user["role"]
    if role == "admin":
        show_admin_dashboard(user)
    elif role == "doctor":
        show_doctor_dashboard(user)
    elif role == "patient":
        show_patient_dashboard(user)
    else:
        st.error("Unknown role.")

# Footer
st.markdown("---")
st.caption("CardioLens AI v2.0 · OpenCV + scipy + Groq LLaMA-3.3-70B + ReportLab · FYP Project 2025")
