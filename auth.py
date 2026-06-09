"""
Alpha AI ECG — Authentication Module
JWT + SQLite — Admin / Doctor / Patient roles
New in v2: doctor_feedback table, file_path in ecg_records, update_user_role()
"""

import sqlite3
import hashlib
import hmac
import os
import json
import base64
import time
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "cardiolens.db")
SECRET_KEY = os.environ.get("SECRET_KEY", "cardiolens-secret-2025-change-in-prod")

# ─── DB INIT ──────────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin','doctor','patient')),
            full_name TEXT,
            email TEXT,
            specialization TEXT,
            patient_id TEXT,
            age INTEGER,
            gender TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            is_active INTEGER DEFAULT 1
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS ecg_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_username TEXT,
            doctor_username TEXT,
            filename TEXT,
            file_path TEXT,
            heart_rate REAL,
            rhythm TEXT,
            rmssd REAL,
            hr_cv REAL,
            analysis_json TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    # Add file_path column if upgrading from old DB (migration-safe)
    try:
        c.execute("ALTER TABLE ecg_records ADD COLUMN file_path TEXT")
        conn.commit()
    except Exception:
        pass  # Column already exists

    c.execute("""
        CREATE TABLE IF NOT EXISTS doctor_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ecg_record_id INTEGER NOT NULL,
            doctor_username TEXT NOT NULL,
            doctor_name TEXT,
            comment TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (ecg_record_id) REFERENCES ecg_records(id)
        )
    """)

    # Seed default users if empty
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        seed_users = [
            ("admin",   hash_password("admin123"),   "admin",   "System Admin",      "admin@alphaaiecg.ai",   None,          None,        None, None),
            ("doctor1", hash_password("doctor123"),  "doctor",  "Dr. Ali Hassan",    "ali@alphaaiecg.ai",     "Cardiologist",None,        None, None),
            ("doctor2", hash_password("doctor123"),  "doctor",  "Dr. Sara Ahmed",    "sara@alphaaiecg.ai",    "Cardiologist",None,        None, None),
            ("patient1",hash_password("patient123"), "patient", "Ahmed Khan",        "ahmed@gmail.com",       None,          "PT-001",    45,   "Male"),
            ("patient2",hash_password("patient123"), "patient", "Fatima Malik",      "fatima@gmail.com",      None,          "PT-002",    32,   "Female"),
        ]
        c.executemany("""
            INSERT INTO users (username,password_hash,role,full_name,email,specialization,patient_id,age,gender)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, seed_users)
    conn.commit()
    conn.close()

# ─── PASSWORD ─────────────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    salt = "cardiolens2025"
    return hashlib.sha256((password + salt).encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hmac.compare_digest(hash_password(password), hashed)

# ─── SIMPLE JWT (no external lib needed) ─────────────────────────────────────
def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def _unb64(s: str) -> bytes:
    pad = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * pad)

def create_token(username: str, role: str) -> str:
    header  = _b64(json.dumps({"alg":"HS256","typ":"JWT"}).encode())
    payload = _b64(json.dumps({"sub":username,"role":role,"iat":int(time.time()),"exp":int(time.time())+86400*7}).encode())
    sig     = _b64(hmac.new(SECRET_KEY.encode(), f"{header}.{payload}".encode(), "sha256").digest())
    return f"{header}.{payload}.{sig}"

def verify_token(token: str):
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header, payload, sig = parts
        expected_sig = _b64(hmac.new(SECRET_KEY.encode(), f"{header}.{payload}".encode(), "sha256").digest())
        if not hmac.compare_digest(sig, expected_sig):
            return None
        data = json.loads(_unb64(payload))
        if data["exp"] < int(time.time()):
            return None
        return data
    except Exception:
        return None

# ─── USER CRUD ────────────────────────────────────────────────────────────────
def login(username: str, password: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND is_active=1", (username,))
    user = c.fetchone()
    conn.close()
    if user and verify_password(password, user["password_hash"]):
        token = create_token(username, user["role"])
        return {"token": token, "user": dict(user)}
    return None

def get_user(username: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_users(role=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    if role:
        c.execute("SELECT * FROM users WHERE role=? ORDER BY created_at DESC", (role,))
    else:
        c.execute("SELECT * FROM users ORDER BY role, created_at DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_user(username, password, role, full_name, email,
                specialization=None, patient_id=None, age=None, gender=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO users (username,password_hash,role,full_name,email,specialization,patient_id,age,gender)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (username, hash_password(password), role, full_name, email,
              specialization, patient_id, age, gender))
        conn.commit()
        return True, "User created successfully"
    except sqlite3.IntegrityError:
        return False, "Username already exists"
    finally:
        conn.close()

def delete_user(username: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET is_active=0 WHERE username=?", (username,))
    conn.commit()
    conn.close()

def update_user_role(username: str, new_role: str) -> bool:
    """Change a user's role (patient ↔ doctor). Admin role cannot be set from here."""
    if new_role not in ("patient", "doctor"):
        return False
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET role=? WHERE username=? AND role != 'admin'", (new_role, username))
    changed = c.rowcount > 0
    conn.commit()
    conn.close()
    return changed

# ─── ECG RECORDS ─────────────────────────────────────────────────────────────
def save_ecg_record(patient_username, doctor_username, filename, heart_rate,
                    rhythm, rmssd, hr_cv, analysis_json, file_path=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO ecg_records
          (patient_username,doctor_username,filename,file_path,heart_rate,rhythm,rmssd,hr_cv,analysis_json)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (patient_username, doctor_username, filename, file_path,
          heart_rate, rhythm, rmssd, hr_cv, analysis_json))
    conn.commit()
    conn.close()

def get_ecg_records(username=None, role=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    if role == "patient":
        c.execute("SELECT * FROM ecg_records WHERE patient_username=? ORDER BY created_at DESC", (username,))
    elif role == "doctor":
        c.execute("SELECT * FROM ecg_records WHERE doctor_username=? ORDER BY created_at DESC", (username,))
    else:
        c.execute("SELECT * FROM ecg_records ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ─── DOCTOR FEEDBACK ─────────────────────────────────────────────────────────
def save_feedback(ecg_record_id: int, doctor_username: str, doctor_name: str, comment: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO doctor_feedback (ecg_record_id, doctor_username, doctor_name, comment)
        VALUES (?,?,?,?)
    """, (ecg_record_id, doctor_username, doctor_name, comment))
    conn.commit()
    conn.close()

def get_feedback(ecg_record_id: int) -> list:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM doctor_feedback WHERE ecg_record_id=? ORDER BY created_at DESC",
              (ecg_record_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_feedback_by_doctor(doctor_username: str) -> list:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM doctor_feedback WHERE doctor_username=? ORDER BY created_at DESC",
              (doctor_username,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ─── STATS ───────────────────────────────────────────────────────────────────
def get_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    stats = {}
    c.execute("SELECT COUNT(*) FROM users WHERE role='doctor' AND is_active=1")
    stats["doctors"] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE role='patient' AND is_active=1")
    stats["patients"] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM ecg_records")
    stats["ecg_total"] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM doctor_feedback")
    stats["feedback_total"] = c.fetchone()[0]
    c.execute("SELECT rhythm, COUNT(*) as cnt FROM ecg_records GROUP BY rhythm")
    stats["rhythm_counts"] = dict(c.fetchall())
    conn.close()
    return stats

# Init on import
init_db()
