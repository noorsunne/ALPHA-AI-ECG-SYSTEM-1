"""
Alpha AI ECG — Groq AI Chatbot Module
Handles all Groq API interactions for ECG explanation and heart health Q&A.
"""

import os
import streamlit as st
from groq import Groq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

SYSTEM_PROMPT = (
    "You are a medical assistant for Alpha AI ECG platform. "
    "You explain ECG reports in simple educational terms to patients and doctors. "
    "You answer general heart health questions clearly and kindly. "
    "Do NOT give medical diagnosis. Always recommend consulting a qualified cardiologist for clinical decisions. "
    "When ECG data is provided, reference actual values in your explanation. "
    "Use bullet points for clarity when listing information."
)


def get_groq_client():
    """Return Groq client using env key or session override."""
    key = st.session_state.get("groq_api_key_override", "").strip()
    if not key:
        key = GROQ_API_KEY
    if not key or key in ("gsk_YOUR_GROQ_API_KEY_HERE", ""):
        return None
    try:
        return Groq(api_key=key)
    except Exception:
        return None


def build_ecg_context(rhythm_key, features, signals, RHYTHM_CLASSES):
    """Build a text context string from ECG analysis results for the chatbot."""
    if not rhythm_key:
        return "No ECG analysis has been performed yet in this session."
    cls = RHYTHM_CLASSES.get(rhythm_key, {})
    ctx = f"""ECG Analysis Results (Alpha AI ECG):
- Rhythm: {cls.get('name', rhythm_key)} ({cls.get('abbr', '')})
- Clinical Urgency: {cls.get('urgency', 'Unknown')}
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
    ctx += f"- Clinical note: {cls.get('clinical', '')}\n"
    return ctx


def chat_with_groq(client, user_message, chat_history, ecg_context):
    """Send message to Groq LLaMA and return response string."""
    system_with_context = SYSTEM_PROMPT
    if ecg_context and "No ECG" not in ecg_context:
        system_with_context += f"\n\nCurrent Patient ECG Data on File:\n{ecg_context}"

    messages = [{"role": "system", "content": system_with_context}]
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


def render_chatbot_ui(ecg_context: str, chat_key: str = "main"):
    """
    Full chatbot UI widget — renders chat history, input box, and handles Groq call.
    Call this inside any Streamlit page.
    """
    history_key = f"chat_history_{chat_key}"
    if history_key not in st.session_state:
        st.session_state[history_key] = []

    st.markdown("""
    <div style="background:rgba(10,20,40,0.6);border:1px solid rgba(59,130,246,0.2);
         border-radius:14px;padding:18px 20px;margin-bottom:16px;">
      <div style="font-size:13px;color:#64748b;line-height:1.6;">
        🤖 <b style="color:#60a5fa;">Alpha AI ECG Assistant</b> — Powered by Groq LLaMA-3.3-70B<br>
        Ask me about your ECG results, heart health, or any cardiac questions.
        <span style="color:#f59e0b;font-size:11px;">⚕️ Not a substitute for professional medical advice.</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    client = get_groq_client()
    if client is None:
        st.warning("⚠️ Groq API key not configured. Set GROQ_API_KEY in your .env file or use the sidebar override.")
        return

    # Display chat history
    for msg in st.session_state[history_key]:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="chat-msg chat-user">👤 <b>You:</b> {msg["content"]}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="chat-msg chat-ai">🤖 <b>Alpha AI:</b> {msg["content"]}</div>',
                unsafe_allow_html=True,
            )

    # Input
    with st.form(key=f"chat_form_{chat_key}", clear_on_submit=True):
        col_inp, col_btn = st.columns([5, 1])
        user_input = col_inp.text_input(
            "Ask about your ECG or heart health…",
            placeholder="e.g. What does Atrial Fibrillation mean?",
            label_visibility="collapsed",
        )
        submitted = col_btn.form_submit_button("Send ➤", use_container_width=True)

    if submitted and user_input.strip():
        with st.spinner("Alpha AI is thinking…"):
            try:
                reply = chat_with_groq(client, user_input.strip(),
                                       st.session_state[history_key], ecg_context)
                st.session_state[history_key].append({"role": "user", "content": user_input.strip()})
                st.session_state[history_key].append({"role": "assistant", "content": reply})
                st.rerun()
            except Exception as e:
                st.error(f"❌ Groq error: {e}")

    if st.session_state[history_key]:
        if st.button("🗑️ Clear Chat", key=f"clear_chat_{chat_key}"):
            st.session_state[history_key] = []
            st.rerun()
