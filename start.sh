#!/bin/bash
echo "╔══════════════════════════════════════╗"
echo "║    CardioLens AI — Starting...       ║"
echo "╚══════════════════════════════════════╝"

# Load .env file if it exists
if [ -f .env ]; then
    echo "✅ Loading API keys from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# Check if Groq key is set
if [ -z "$GROQ_API_KEY" ] || [ "$GROQ_API_KEY" = "gsk_YOUR_GROQ_API_KEY_HERE" ]; then
    echo ""
    echo "⚠️  GROQ_API_KEY not set — AI Chatbot will be disabled"
    echo "   Get a free key at: https://console.groq.com"
    echo "   Then edit .env file and add: GROQ_API_KEY=gsk_yourkey"
    echo ""
fi

# Install requirements if needed
pip install -r requirements.txt -q

echo "🚀 Opening browser at http://localhost:8501"
streamlit run app.py
