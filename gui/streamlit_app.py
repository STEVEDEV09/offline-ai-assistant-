import streamlit as st
import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from brain.llm import ask_ai, get_available_models
from personality.identity import (
    get_identity,
    update_name,
    update_user_name,
    update_personality,
    reset_identity,
    save_identity
)
from memory.long_term import get_all_facts, save_fact, delete_fact, clear_all_facts
from memory.short_term import get_recent_chat_history, clear_chat_history
from tools.system_tools import get_system_stats, launch_application, open_url, safe_calculate
from vision.face_detection import detect_faces
from vision.mood_detection import analyze_mood
from voice.text_to_speech import speak_text, get_web_speech_html
from voice.speech_to_text import get_speech_recognition_html

# Page Configuration
st.set_page_config(
    page_title="My AI - Personal Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Dark Glassmorphism & Modern Typography)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Background and overall styling */
    .stApp {
        background: radial-gradient(circle at 15% 15%, rgba(30, 41, 59, 0.4) 0%, transparent 60%),
                    radial-gradient(circle at 85% 85%, rgba(15, 23, 42, 0.6) 0%, transparent 60%),
                    #0b0f19;
        color: #f1f5f9;
    }

    /* Glassmorphic Cards */
    .glass-card {
        background: rgba(17, 24, 39, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 20px;
        backdrop-filter: blur(12px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        margin-bottom: 20px;
    }

    /* Status Pill */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 13px;
        font-weight: 600;
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }

    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #10b981;
        box-shadow: 0 0 8px #10b981;
    }

    /* Quick action buttons */
    div.stButton > button {
        border-radius: 10px;
        font-weight: 500;
        transition: all 0.2s ease;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
        border-color: rgba(99, 102, 241, 0.6);
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(17, 24, 39, 0.5);
        padding: 6px;
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 8px 18px;
        color: #94a3b8;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(99, 102, 241, 0.2) !important;
        color: #818cf8 !important;
        font-weight: 600;
        border: 1px solid rgba(99, 102, 241, 0.4);
    }

    /* Metrics */
    div[data-testid="stMetric"] {
        background: rgba(17, 24, 39, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 14px 18px;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "auto_speak" not in st.session_state:
    st.session_state.auto_speak = False
if "selected_model" not in st.session_state:
    st.session_state.selected_model = "tinyllama:latest"

identity = get_identity()
available_models = get_available_models()

# Sidebar: Assistant Overview & Settings
with st.sidebar:
    st.markdown(f"""
    <div style="text-align: center; padding: 10px 0 15px 0;">
        <div style="font-size: 54px; filter: drop-shadow(0 0 16px rgba(99, 102, 241, 0.5));">
            {identity.get('avatar', '🤖')}
        </div>
        <h2 style="margin: 6px 0 0 0; color: #f8fafc; font-weight: 700;">{identity.get('name', 'Assistant')}</h2>
        <p style="color: #94a3b8; font-size: 13px; margin: 4px 0 12px 0;">Local Intelligence Hub</p>
        <div class="status-badge">
            <div class="status-dot"></div> Ollama Online
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown("### ⚙️ Engine Config")
    selected_model = st.selectbox(
        "Active Model",
        options=available_models,
        index=0 if st.session_state.selected_model not in available_models else available_models.index(st.session_state.selected_model),
        help="Select local Ollama model to power the assistant"
    )
    st.session_state.selected_model = selected_model

    auto_speak = st.toggle("🔊 Auto-Speak AI Replies", value=st.session_state.auto_speak)
    st.session_state.auto_speak = auto_speak

    st.divider()

    st.markdown("### ⚡ Quick Prompts")
    if st.button("⏰ What time is it?", use_container_width=True):
        st.session_state.quick_prompt = "What time is it?"
    if st.button("💻 Show PC Specs", use_container_width=True):
        st.session_state.quick_prompt = "System info"
    if st.button("🧠 Recall Memory", use_container_width=True):
        st.session_state.quick_prompt = "What do you remember about me?"
    if st.button("🚀 Open YouTube", use_container_width=True):
        st.session_state.quick_prompt = "Open youtube"

    st.divider()

    if st.button("🗑️ Clear Chat History", type="secondary", use_container_width=True):
        st.session_state.messages = []
        clear_chat_history()
        st.toast("Chat history cleared!", icon="🧹")
        st.rerun()

# Main Application Layout
st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
    <div>
        <h1 style="margin: 0; font-size: 28px; font-weight: 700; color: #f8fafc;">
            ⚡ {identity.get('name', 'Assistant')} <span style="font-size: 18px; color: #818cf8; font-weight: 400;">v2.0</span>
        </h1>
        <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 14px;">
            Companion for <b>{identity.get('user_name', 'Friend')}</b> • Powered by <code>{st.session_state.selected_model}</code>
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# Main Navigation Tabs
tab_chat, tab_memory, tab_vision, tab_tools, tab_settings = st.tabs([
    "💬 Chat",
    "🧠 Memory Vault",
    "👁️ Vision & Mood",
    "🛠️ Tools",
    "⚙️ Persona & Config"
])

# ----------------------------------------------------
# TAB 1: CHAT INTERFACE
# ----------------------------------------------------
with tab_chat:
    # Optional Speech-to-Text Widget
    with st.expander("🎙️ Voice Input (Speech-to-Text)", expanded=False):
        st.markdown(get_speech_recognition_html(), unsafe_allow_html=True)

    # Render Chat History
    chat_container = st.container()
    with chat_container:
        for idx, message in enumerate(st.session_state.messages):
            role = message["role"]
            content = message["content"]
            with st.chat_message(role, avatar="🧑‍💻" if role == "user" else identity.get("avatar", "🤖")):
                st.markdown(content)
                if role == "assistant":
                    # Option to play speech directly in browser
                    st.markdown(get_web_speech_html(content, auto_play=False), unsafe_allow_html=True)

    # Chat Input handler
    prompt = st.chat_input("Ask me anything, tell me to open apps, or say 'Remember that...'")

    # Check if a quick prompt from sidebar was clicked
    if "quick_prompt" in st.session_state and st.session_state.quick_prompt:
        prompt = st.session_state.quick_prompt
        st.session_state.quick_prompt = None

    if prompt:
        # Check for natural name change command
        lower_p = prompt.lower()
        if "your name is" in lower_p or "tumhara naam" in lower_p or "call yourself" in lower_p:
            words = prompt.strip().split()
            new_name = words[-1].strip(".,!?")
            reply = update_name(new_name)
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()

        # Display user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(prompt)

        # Assistant response with streaming
        with st.chat_message("assistant", avatar=identity.get("avatar", "🤖")):
            with st.spinner("Processing..."):
                stream_gen = ask_ai(
                    user_message=prompt,
                    chat_history=st.session_state.messages[:-1],
                    model=st.session_state.selected_model,
                    stream=True
                )
                full_response = st.write_stream(stream_gen)

            # Speak if auto_speak is enabled
            if st.session_state.auto_speak:
                speak_text(full_response, non_blocking=True)

            st.markdown(get_web_speech_html(full_response, auto_play=False), unsafe_allow_html=True)

        st.session_state.messages.append({"role": "assistant", "content": full_response})

# ----------------------------------------------------
# TAB 2: MEMORY VAULT
# ----------------------------------------------------
with tab_memory:
    st.markdown("### 🧠 Persistent Long-Term Memory")
    st.caption("Facts stored here are automatically injected into the AI's reasoning so it never forgets your preferences.")

    col_m1, col_m2 = st.columns([1, 1])

    with col_m1:
        st.markdown("#### ➕ Add New Memory")
        with st.form("add_memory_form"):
            new_fact = st.text_input("Fact to remember", placeholder="e.g. My favorite programming language is Python")
            category = st.selectbox("Category", ["personal", "preference", "work", "habit", "general"])
            submitted = st.form_submit_button("Save Memory")
            if submitted and new_fact:
                if save_fact(new_fact, category=category):
                    st.success("Memory stored successfully!")
                    st.rerun()
                else:
                    st.warning("Could not save or memory already exists.")

    with col_m2:
        st.markdown("#### 📊 Memory Stats")
        facts = get_all_facts()
        st.metric("Total Stored Facts", len(facts))
        if st.button("🧹 Clear All Stored Facts", type="secondary"):
            clear_all_facts()
            st.success("All facts cleared!")
            st.rerun()

    st.markdown("#### 📜 Recalled Memories")
    if facts:
        for f in facts:
            col_f1, col_f2 = st.columns([5, 1])
            with col_f1:
                st.markdown(f"• **[{f['category'].upper()}]** {f['fact']} *(saved {f['created_at'][:10]})*")
            with col_f2:
                if st.button("🗑️", key=f"del_{f['id']}", help="Delete this fact"):
                    delete_fact(f["id"])
                    st.rerun()
    else:
        st.info("No facts remembered yet! Say 'Remember that...' in chat or add one above.")

# ----------------------------------------------------
# TAB 3: VISION & MOOD DETECTION
# ----------------------------------------------------
with tab_vision:
    st.markdown("### 👁️ Real-Time Vision & Emotion Analysis")
    st.caption("Capture from your webcam or upload a photo to analyze faces, expressions, and mood.")

    vision_mode = st.radio("Input Source", ["📸 Webcam Snapshot", "📁 Upload Image"], horizontal=True)

    input_img = None
    if vision_mode == "📸 Webcam Snapshot":
        input_img = st.camera_input("Take a snapshot to analyze")
    else:
        input_img = st.file_uploader("Upload an image (JPG, PNG)", type=["jpg", "jpeg", "png"])

    if input_img is not None:
        col_v1, col_v2 = st.columns([1, 1])

        with st.spinner("Analyzing facial features and emotion..."):
            mood_result = analyze_mood(input_img)
            face_result = detect_faces(input_img)

        with col_v1:
            st.image(mood_result["annotated_image"], caption="Annotated Vision Output", use_container_width=True)

        with col_v2:
            st.markdown(f"""
            <div class="glass-card">
                <div style="font-size: 36px;">{mood_result['emoji']}</div>
                <h3 style="margin: 4px 0;">Mood: {mood_result['mood']}</h3>
                <p style="color: #94a3b8; font-size: 14px;">{mood_result['summary']}</p>
                <hr style="border-color: rgba(255,255,255,0.1);">
                <p><b>Faces Detected:</b> {mood_result['faces_detected']}</p>
                <p><b>Confidence:</b> {int(mood_result['confidence'] * 100)}%</p>
            </div>
            """, unsafe_allow_html=True)

            if st.button("💬 Discuss this mood with AI", use_container_width=True):
                discuss_msg = f"I just took a camera snapshot and the vision system detected that my mood is {mood_result['mood']}. Can you say something uplifting or comment on this?"
                st.session_state.quick_prompt = discuss_msg
                st.rerun()

# ----------------------------------------------------
# TAB 4: SYSTEM TOOLS & ACTIONS
# ----------------------------------------------------
with tab_tools:
    st.markdown("### 🛠️ Desktop Tools & Quick Actions")
    st.caption("Control apps, run system diagnostics, and perform calculations.")

    stats = get_system_stats()
    col_t1, col_t2, col_t3, col_t4 = st.columns(4)
    with col_t1:
        st.metric("Operating System", stats["os"])
    with col_t2:
        st.metric("Architecture", stats["architecture"])
    with col_t3:
        st.metric("Time", stats["time"])
    with col_t4:
        st.metric("Battery", stats.get("battery", "AC Powered"))

    st.markdown("#### 🚀 App Shortcuts")
    col_a1, col_a2, col_a3, col_a4 = st.columns(4)
    with col_a1:
        if st.button("📝 Open Notepad", use_container_width=True):
            st.info(launch_application("notepad"))
    with col_a2:
        if st.button("🧮 Open Calculator", use_container_width=True):
            st.info(launch_application("calc"))
    with col_a3:
        if st.button("📁 Open Explorer", use_container_width=True):
            st.info(launch_application("explorer"))
    with col_a4:
        if st.button("🌐 Open YouTube", use_container_width=True):
            st.info(open_url("https://www.youtube.com"))

    st.markdown("#### ➗ Quick Calculator")
    calc_expr = st.text_input("Enter math expression", placeholder="e.g. (150 * 4) / 2")
    if calc_expr:
        st.success(safe_calculate(calc_expr))

# ----------------------------------------------------
# TAB 5: PERSONA & CONFIGURATION
# ----------------------------------------------------
with tab_settings:
    st.markdown("### ⚙️ Personality & Identity Customizer")
    st.caption("Tune the assistant's name, user name, and behavior traits.")

    with st.form("identity_form"):
        new_ai_name = st.text_input("AI Assistant Name", value=identity.get("name", "Assistant"))
        new_user_name = st.text_input("Your Name", value=identity.get("user_name", "Friend"))
        new_avatar = st.selectbox("Avatar Emoji", ["🤖", "⚡", "🔮", "🧠", "✨", "🦾", "👾"], index=0)
        new_personality = st.text_area(
            "Personality Prompt",
            value=identity.get("personality", "I am a helpful, friendly, witty, and smart AI assistant."),
            height=120
        )
        new_instructions = st.text_area(
            "System Guidelines",
            value=identity.get("system_instructions", "Keep answers clear, helpful, and concise."),
            height=80
        )

        save_btn = st.form_submit_button("💾 Save Settings")
        if save_btn:
            identity["name"] = new_ai_name.strip()
            identity["user_name"] = new_user_name.strip()
            identity["avatar"] = new_avatar
            identity["personality"] = new_personality.strip()
            identity["system_instructions"] = new_instructions.strip()
            save_identity(identity)
            st.success("Identity settings updated successfully!")
            st.rerun()

    if st.button("🔄 Reset Identity to Defaults"):
        reset_identity()
        st.success("Reset to default settings!")
        st.rerun()