# 🫀 CardioLens AI v2.0
### ECG Analysis Platform — Real ECG Processing + Groq AI Chatbot

---

## ✅ Features

| Feature | Status |
|---|---|
| ECG Image Processing (OpenCV) | ✅ Real |
| Grid Removal + Lead Detection | ✅ Real |
| Signal Digitization (FFT + SavGol) | ✅ Real |
| Rhythm Classification (NSR/TACHY/BRADY/AFib/PVC) | ✅ Real |
| HR, RMSSD, RR CV Calculation | ✅ Real |
| Groq AI Chatbot (LLaMA-3.3-70B) | ✅ Real |
| PDF Report (ReportLab) | ✅ Real |
| CSV + PNG Downloads | ✅ Real |
| Hospital-Grade Dark UI | ✅ Real |
| 6-Tab Analysis Results | ✅ Real |

---

## 🔑 STEP 1 — Get Your FREE Groq API Key

1. Go to **https://console.groq.com**
2. Sign up (free, no credit card needed)
3. Click **"API Keys"** → **"Create API Key"**
4. Copy the key (starts with `gsk_`)

---

## 🔑 STEP 2 — Set Your Groq Key

### Option A — .env File (Recommended)
Create a file named `.env` in this folder:
```
GROQ_API_KEY=gsk_your_actual_key_here
```
The start scripts auto-load this file.

### Option B — Edit app.py directly
Open `app.py`, find line 42:
```python
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "gsk_YOUR_GROQ_API_KEY_HERE")
```
Replace the fallback value with your key.

### Option C — Enter in the Sidebar (no restart needed)
Run the app, open the sidebar, and paste your key in the **"Override Groq Key"** input.

---

## 🚀 How to Run Locally

### Windows (Easy Way):
```
Double-click  start.bat
```

### Windows (Manual):
```cmd
pip install -r requirements.txt
streamlit run app.py
```

### Mac / Linux:
```bash
chmod +x start.sh
./start.sh
```

Or manually:
```bash
pip install -r requirements.txt
streamlit run app.py
```

Browser opens at: **http://localhost:8501**

---

## 🌐 Deploy Online FREE — Streamlit Cloud

1. Create account at **https://streamlit.io** (free)
2. Push this folder to a **GitHub repo** (new repo)
3. Go to **https://share.streamlit.io** → New app
4. Select your GitHub repo → set main file: `app.py`
5. Click **"Advanced settings"** → **Secrets** → add:
   ```
   GROQ_API_KEY = "gsk_your_actual_key_here"
   ```
6. Click **Deploy!**

Your app will be live at `https://yourname-cardiolens-app.streamlit.app` — shareable with anyone!

---

## 🌐 Deploy Online FREE — Railway

1. Create account at **https://railway.app** (free tier available)
2. Click **"New Project"** → **"Deploy from GitHub"**
3. Connect your GitHub repo
4. Set environment variable: `GROQ_API_KEY=gsk_yourkey`
5. Add `Procfile` with: `web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
6. Deploy!

---

## 📋 Requirements

- **Python 3.10 or newer**
- Internet connection (for Groq AI chatbot)
- ECG image file (JPG or PNG, 300 DPI recommended)

Install Python from: https://python.org/downloads/
(Check "Add Python to PATH" during install on Windows)

---

## 💡 How to Use

1. **Run the app** (see above)
2. **Sidebar** → Enter patient name, age, gender, ID
3. **Tab: ECG Analysis** → Upload ECG image (JPG/PNG)
4. Wait for processing (5–15 seconds)
5. See results: preprocessing → leads → signals → rhythm
6. **Tab: AI Chatbot** → Ask questions about the results
7. **Tab: PDF Report** → Generate and download clinical report

---

## ⚙️ Processing Settings (Sidebar)

| Setting | Default | What it does |
|---|---|---|
| Expected ECG rows | 4 | Standard 12-lead has 4 rows |
| Strip crop padding | 70px | Increase if leads get cut off |
| FFT grid filter width | 6 | Higher = more grid removal |
| Classify rhythm from | Lead II | Best lead for rhythm analysis |
| R-peak sensitivity | 0.4 | Lower = detect more peaks |

---

## 🐛 Troubleshooting

**"No lead strips detected"** → Increase "Strip crop padding" to 90–110

**"Groq API Error"** → Check your API key (see STEP 2 above)

**"Module not found"** → Run: `pip install -r requirements.txt`

**"streamlit: command not found"** → Run: `pip install streamlit`

**Slow processing** → Use smaller image (resize to 2000px wide max)

---

## 📁 File Structure

```
cardiolens_merged/
├── app.py              ← Main app
├── .env                ← Your API keys (create this file)
├── .env.example        ← Template for .env
├── requirements.txt    ← Python packages
├── start.bat           ← Windows launcher
├── start.sh            ← Mac/Linux launcher
└── README.md           ← This file
```

---

## ⚕️ Medical Disclaimer
This software is for **educational and research purposes only**.
It is NOT a medical device and NOT a substitute for professional medical diagnosis.
Always consult a qualified cardiologist for ECG interpretation.

---
*CardioLens AI v2.0 · OpenCV + scipy + Groq LLaMA-3.3-70B + ReportLab*
