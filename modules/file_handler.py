"""
Alpha AI ECG — File Handler Module
Manages ECG file uploads: saving to disk and retrieving per patient.
"""

import os
import shutil
from datetime import datetime

# Root uploads directory (sits next to this file's parent)
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")


def _patient_dir(username: str) -> str:
    """Return (and create) the upload folder for a specific patient."""
    folder = os.path.join(UPLOAD_DIR, username)
    os.makedirs(folder, exist_ok=True)
    return folder


def save_ecg_file(uploaded_file, username: str) -> str:
    """
    Save an uploaded Streamlit file to uploads/{username}/.
    Returns the absolute file path on disk.
    """
    folder = _patient_dir(username)
    # Timestamp prefix to avoid name clashes
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{uploaded_file.name}"
    dest = os.path.join(folder, filename)

    # Reset buffer pointer before reading
    uploaded_file.seek(0)
    with open(dest, "wb") as f:
        f.write(uploaded_file.read())
    # Reset again so the caller can still read the file
    uploaded_file.seek(0)
    return dest


def get_patient_files(username: str) -> list:
    """Return a list of dicts {filename, path, size_kb, modified} for a patient."""
    folder = _patient_dir(username)
    files = []
    for fname in sorted(os.listdir(folder), reverse=True):
        fpath = os.path.join(folder, fname)
        if os.path.isfile(fpath):
            stat = os.stat(fpath)
            files.append({
                "filename": fname,
                "path": fpath,
                "size_kb": round(stat.st_size / 1024, 1),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
            })
    return files


def load_image_bytes(file_path: str) -> bytes | None:
    """Load raw bytes from a saved file path."""
    if not os.path.exists(file_path):
        return None
    with open(file_path, "rb") as f:
        return f.read()


def pdf_first_page_to_image(file_path: str):
    """
    Convert the first page of a PDF to an RGB numpy array.
    Returns None if PyMuPDF is not installed or file is not a PDF.
    """
    if not file_path.lower().endswith(".pdf"):
        return None
    try:
        import fitz  # PyMuPDF
        import numpy as np
        doc = fitz.open(file_path)
        page = doc[0]
        pix = page.get_pixmap(dpi=150)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if pix.n == 4:  # RGBA → RGB
            img = img[:, :, :3]
        return img
    except Exception:
        return None
