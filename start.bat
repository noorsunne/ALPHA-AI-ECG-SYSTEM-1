@echo off
echo ╔══════════════════════════════════════╗
echo ║    CardioLens AI — Starting...       ║
echo ╚══════════════════════════════════════╝

REM Load .env file if it exists
if exist .env (
    echo ✅ Loading API keys from .env file...
    for /f "tokens=1,2 delims==" %%A in (.env) do (
        if not "%%A"=="" if not "%%A:~0,1%"=="#" set %%A=%%B
    )
)

pip install -r requirements.txt -q
echo 🚀 Opening browser at http://localhost:8501
streamlit run app.py
pause
