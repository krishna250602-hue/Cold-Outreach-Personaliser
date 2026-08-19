import os
import io
import time
import pandas as pd
import streamlit as st

from utils import (
    clean_text,
    validate_csv,
    build_profile,
    safe_filename,
    validate_sender_info,
)

from generator import (
    generate_single_prospect,
    generate_batch,
    get_groq_client,
)

st.set_page_config(
    page_title="Cold Outreach Personaliser",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# DESIGN SYSTEM
# ============================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

:root {
    --bg: #f7f8fa;
    --surface: #ffffff;
    --surface-2: #fbfbfc;
    --text: #111318;
    --muted: #6b7280;
    --subtle: #9aa0aa;
    --border: #e7e9ed;
    --border-strong: #d9dce2;
    --accent: #111318;
    --accent-hover: #2a2d33;
    --success: #16805c;
    --danger: #c83a3a;
    --radius-sm: 10px;
    --radius-md: 14px;
    --radius-lg: 20px;
    --shadow-sm: 0 1px 2px rgba(16,24,40,.04);
    --shadow-md: 0 8px 30px rgba(16,24,40,.06);
}

html, body, [class*="css"] {
    font-family: "DM Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    color: var(--text);
}

.stApp {
    background: var(--bg);
}

.block-container {
    max-width: 1240px;
    padding-top: 1rem;
    padding-bottom: 4rem;
}

header[data-testid="stHeader"] {
    background: transparent;
}

section[data-testid="stSidebar"] {
    display: none;
}

/* ---------- Navbar ---------- */

.navbar {
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 2px;
    margin-bottom: 54px;
}

.brand {
    display: flex;
    align-items: center;
    gap: 11px;
    font-family: "Space Grotesk", sans-serif;
    font-weight: 700;
    font-size: 16px;
    letter-spacing: -.02em;
}

.brand-mark {
    width: 31px;
    height: 31px;
    display: grid;
    place-items: center;
    border-radius: 9px;
    background: #111318;
    color: white;
    font-size: 15px;
    box-shadow: 0 3px 12px rgba(17,19,24,.14);
}

.nav-right {
    display: flex;
    align-items: center;
    gap: 9px;
}

.nav-pill {
    border: 1px solid var(--border);
    background: rgba(255,255,255,.8);
    color: var(--muted);
    padding: 7px 12px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
}

/* ---------- Hero ---------- */

.hero {
    max-width: 850px;
    margin: 0 auto 46px;
    text-align: center;
}

.eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 7px 11px;
    border: 1px solid var(--border);
    background: #fff;
    border-radius: 999px;
    color: var(--muted);
    font-size: 12px;
    font-weight: 600;
    margin-bottom: 18px;
    box-shadow: var(--shadow-sm);
}

.eyebrow-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #22a06b;
    box-shadow: 0 0 0 4px rgba(34,160,107,.09);
}

.hero h1 {
    font-family: "Space Grotesk", sans-serif;
    font-size: clamp(38px, 5vw, 64px);
    line-height: 1.02;
    letter-spacing: -.055em;
    margin: 0 0 18px;
    color: #0f1115;
}

.hero h1 span {
    color: #777d87;
}

.hero p {
    max-width: 680px;
    margin: 0 auto;
    color: var(--muted);
    font-size: 16px;
    line-height: 1.7;
}

/* ---------- Cards ---------- */

.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    padding: 24px;
    transition: border-color .2s ease, box-shadow .2s ease, transform .2s ease;
}

.card:hover {
    border-color: var(--border-strong);
    box-shadow: var(--shadow-md);
}

.card-title-row {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 20px;
}

.card-title {
    font-family: "Space Grotesk", sans-serif;
    font-size: 17px;
    font-weight: 600;
    letter-spacing: -.025em;
}

.card-subtitle {
    margin-top: 4px;
    color: var(--muted);
    font-size: 12px;
    line-height: 1.5;
}

.step {
    min-width: 29px;
    height: 29px;
    display: grid;
    place-items: center;
    border: 1px solid var(--border);
    border-radius: 9px;
    color: var(--muted);
    background: var(--surface-2);
    font-size: 11px;
    font-weight: 700;
}

/* ---------- Streamlit inputs ---------- */

div[data-testid="stTextArea"] label,
div[data-testid="stTextInput"] label,
div[data-testid="stSelectbox"] label,
div[data-testid="stFileUploader"] label {
    font-size: 12px !important;
    color: #444952 !important;
    font-weight: 600 !important;
    margin-bottom: 7px !important;
}

div[data-testid="stTextArea"] textarea,
div[data-testid="stTextInput"] input {
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    background: #fff !important;
    color: var(--text) !important;
    box-shadow: none !important;
    transition: border-color .18s ease, box-shadow .18s ease !important;
}

div[data-testid="stTextArea"] textarea:focus,
div[data-testid="stTextInput"] input:focus {
    border-color: #b9bdc5 !important;
    box-shadow: 0 0 0 3px rgba(17,19,24,.055) !important;
}

div[data-testid="stTextArea"] textarea {
    line-height: 1.65 !important;
}

div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    min-height: 42px;
}

/* ---------- Buttons ---------- */

.stButton > button,
.stDownloadButton > button {
    border-radius: 11px !important;
    min-height: 43px !important;
    font-family: "DM Sans", sans-serif !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    transition: transform .15s ease, box-shadow .15s ease, background .15s ease !important;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    transform: translateY(-1px);
}

button[kind="primary"] {
    background: #111318 !important;
    border: 1px solid #111318 !important;
    color: white !important;
    box-shadow: 0 5px 14px rgba(17,19,24,.13) !important;
}

button[kind="primary"]:hover {
    background: #292c32 !important;
    box-shadow: 0 8px 20px rgba(17,19,24,.17) !important;
}

button[kind="secondary"] {
    background: white !important;
    color: #30343b !important;
    border: 1px solid var(--border) !important;
}

/* ---------- Tone / goal chips ---------- */

.selector-label {
    color: #444952;
    font-size: 12px;
    font-weight: 600;
    margin: 4px 0 9px;
}

/* Radio group */
div[data-testid="stRadio"] > div {
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 8px !important;
}

/* Individual selector */
div[data-testid="stRadio"] label {
    position: relative !important;
    display: flex !important;
    align-items: center !important;
    width: auto !important;
    min-height: 38px !important;
    padding: 8px 14px !important;

    background: #ffffff !important;
    border: 1px solid #e3e5e8 !important;
    border-radius: 10px !important;

    color: #3f434b !important;
    cursor: pointer !important;

    transition:
        background-color .18s ease,
        border-color .18s ease,
        color .18s ease,
        transform .18s ease,
        box-shadow .18s ease !important;
}

/* Hide native radio */
div[data-testid="stRadio"] label input {
    position: absolute !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

/* Option text */
div[data-testid="stRadio"] label p {
    margin: 0 !important;
    padding: 0 !important;
    color: #3f434b !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    line-height: 1.2 !important;
}

/* Hover */
div[data-testid="stRadio"] label:hover {
    background: #f5f6f8 !important;
    border-color: #cfd2d7 !important;
    color: #111318 !important;
    transform: translateY(-1px) !important;
}

/* Selected */
div[data-testid="stRadio"] label:has(input:checked) {
    background: #111318 !important;
    border-color: #111318 !important;
    color: #ffffff !important;
    box-shadow: 0 4px 12px rgba(17, 19, 24, .16) !important;
    transform: translateY(-1px) !important;
}

/* Selected text */
div[data-testid="stRadio"] label:has(input:checked) p {
    color: #ffffff !important;
}

/* Selected hover */
div[data-testid="stRadio"] label:has(input:checked):hover {
    background: #292c32 !important;
    border-color: #292c32 !important;
    color: #ffffff !important;
}

div[data-testid="stRadio"] label:has(input:checked):hover p {
    color: #ffffff !important;
}

/* ---------- Result ---------- */

.result-shell {
    background: #111318;
    color: white;
    border-radius: var(--radius-lg);
    padding: 24px;
    box-shadow: 0 12px 35px rgba(17,19,24,.13);
    margin-bottom: 16px;
}

.result-kicker {
    color: #aeb3bd;
    text-transform: uppercase;
    letter-spacing: .1em;
    font-size: 10px;
    font-weight: 700;
    margin-bottom: 8px;
}

.result-title {
    font-family: "Space Grotesk", sans-serif;
    font-size: 22px;
    letter-spacing: -.035em;
    font-weight: 600;
}

.result-meta {
    color: #9da3ad;
    font-size: 12px;
    margin-top: 6px;
}

.email-card {
    background: #fff;
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    overflow: hidden;
    box-shadow: var(--shadow-md);
}

.email-section {
    padding: 21px 23px;
    border-bottom: 1px solid var(--border);
}

.email-section:last-child {
    border-bottom: 0;
}

.email-label {
    color: #858b95;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: .1em;
    font-weight: 700;
    margin-bottom: 9px;
}

.email-subject {
    color: #15171b;
    font-size: 15px;
    font-weight: 700;
    line-height: 1.5;
}

.email-body {
    color: #353942;
    font-size: 14px;
    line-height: 1.8;
    white-space: pre-wrap;
}

.followup {
    background: #fafbfc;
}

.copy-box {
    border: 1px dashed #d9dce2;
    border-radius: 12px;
    background: #fbfbfc;
    padding: 14px;
    color: #555b65;
    font-size: 12px;
    line-height: 1.65;
    white-space: pre-wrap;
}

/* ---------- Empty state ---------- */

.empty-state {
    min-height: 455px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    border: 1px dashed #dfe2e7;
    border-radius: var(--radius-lg);
    background: rgba(255,255,255,.55);
    padding: 40px;
}

.empty-icon {
    width: 52px;
    height: 52px;
    border-radius: 15px;
    display: grid;
    place-items: center;
    background: white;
    border: 1px solid var(--border);
    box-shadow: var(--shadow-sm);
    margin-bottom: 17px;
    font-size: 21px;
}

.empty-title {
    font-family: "Space Grotesk", sans-serif;
    font-size: 17px;
    font-weight: 600;
    margin-bottom: 7px;
}

.empty-text {
    max-width: 330px;
    color: var(--muted);
    font-size: 12px;
    line-height: 1.65;
}

/* ---------- Utility ---------- */

.divider {
    height: 1px;
    background: var(--border);
    margin: 28px 0;
}

.caption {
    color: var(--subtle);
    font-size: 11px;
    line-height: 1.6;
}

.success-note {
    border: 1px solid #d8eee5;
    background: #f4fbf8;
    color: var(--success);
    border-radius: 10px;
    padding: 10px 12px;
    font-size: 12px;
    font-weight: 600;
}

.error-note {
    border: 1px solid #f1d5d5;
    background: #fff7f7;
    color: var(--danger);
    border-radius: 10px;
    padding: 10px 12px;
    font-size: 12px;
    font-weight: 600;
}

div[data-testid="stExpander"] {
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    background: white !important;
}

div[data-testid="stProgressBar"] {
    margin-top: 8px;
}

/* ---------- Mobile ---------- */

@media (max-width: 800px) {
    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .navbar {
        margin-bottom: 35px;
    }

    .nav-pill {
        display: none;
    }

    .hero {
        margin-bottom: 30px;
    }

    .hero h1 {
        font-size: 42px;
    }

    .card {
        padding: 18px;
    }

    .result-shell {
        padding: 19px;
    }
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# STATE
# ============================================================

def init_state():
    defaults = {
        "single_subject": "",
        "single_email": "",
        "single_follow_up": "",
        "single_raw": "",
        "generated": False,
        "last_error": "",
        "batch_results": None,
        "mode": "Single Prospect",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()

tones = [
    "Professional",
    "Friendly",
    "Casual",
    "Confident",
    "Concise",
    "Consultative",
]

goals = [
    "Book a meeting",
    "Introduce a product",
    "Offer a service",
    "Start a conversation",
    "Request feedback",
    "Partnership",
    "Networking",
]

api_key = os.getenv("GROQ_API_KEY")
api_key_missing = not api_key


# ============================================================
# NAVBAR + HERO
# ============================================================

st.markdown("""
<div class="navbar">
    <div class="brand">
        <div class="brand-mark">✦</div>
        Cold Outreach Personaliser
    </div>
    <div class="nav-right">
        <div class="nav-pill">AI-powered outreach</div>
        <div class="nav-pill">Groq</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <div class="eyebrow">
        <span class="eyebrow-dot"></span>
        Personalised outreach, without the robotic copy
    </div>
    <h1>Turn a prospect profile into<br><span>an email worth replying to.</span></h1>
    <p>
        Give us the context. Choose how you want to sound.
        Get concise, human-sounding outreach tailored to the person you're contacting.
    </p>
</div>
""", unsafe_allow_html=True)


# ============================================================
# MODE SWITCH
# ============================================================

mode_col1, mode_col2, _ = st.columns([1.2, 1.2, 2.6])

with mode_col1:
    if st.button(
        "Single Prospect",
        use_container_width=True,
        type="primary" if st.session_state.mode == "Single Prospect" else "secondary",
    ):
        st.session_state.mode = "Single Prospect"
        st.rerun()

with mode_col2:
    if st.button(
        "Batch CSV",
        use_container_width=True,
        type="primary" if st.session_state.mode == "Batch CSV" else "secondary",
    ):
        st.session_state.mode = "Batch CSV"
        st.rerun()

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)


# ============================================================
# API WARNING
# ============================================================

if api_key_missing:
    st.markdown(
        '<div class="error-note">Groq API key is not configured. Add '
        '<code>GROQ_API_KEY</code> to your environment before generating outreach.</div>',
        unsafe_allow_html=True,
    )
    st.write("")


# ============================================================
# SINGLE PROSPECT
# ============================================================

if st.session_state.mode == "Single Prospect":

    left, right = st.columns([1, 1], gap="large")

    with left:
        st.markdown("""
        <div class="card">
            <div class="card-title-row">
                <div>
                    <div class="card-title">Build your outreach</div>
                    <div class="card-subtitle">Start with the prospect's context. More signal means better personalisation.</div>
                </div>
                <div class="step">01</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        profile_input = st.text_area(
            "Prospect profile",
            placeholder=(
                "Sarah is the Head of Marketing at Acme Technologies.\n\n"
                "She has 8 years of experience in B2B SaaS marketing and recently "
                "shared a post about improving outbound conversion rates.\n\n"
                "Acme is expanding its sales team across India."
            ),
            height=230,
            key="profile_input",
        )

        st.markdown('<div class="selector-label">Choose your tone</div>', unsafe_allow_html=True)
        tone = st.radio(
            "Tone",
            tones,
            horizontal=True,
            label_visibility="collapsed",
            key="single_tone",
        )

        st.markdown('<div class="selector-label">Choose your outreach goal</div>', unsafe_allow_html=True)
        goal = st.radio(
            "Outreach goal",
            goals,
            horizontal=True,
            label_visibility="collapsed",
            key="single_goal",
        )

        with st.expander("Add sender details (optional)"):
            sender_name = st.text_input("Your name", placeholder="Krish")
            sender_company = st.text_input("Your company", placeholder="Acme AI")
            sender_role = st.text_input("Your role", placeholder="Founder")
            sender_product = st.text_input(
                "Product / service",
                placeholder="Sales Automation Platform",
            )
            sender_website = st.text_input(
                "Website",
                placeholder="https://acme.ai",
            )

        st.write("")
        generate_btn = st.button(
            "✦  Generate personalised outreach",
            type="primary",
            use_container_width=True,
            disabled=api_key_missing,
        )

        if generate_btn:
            cleaned_profile = clean_text(profile_input)

            if not cleaned_profile:
                st.session_state.last_error = "Please enter a prospect profile first."
                st.session_state.generated = False
                st.rerun()

            try:
                formatted_sender = validate_sender_info(
                    sender_name,
                    sender_company,
                    sender_role,
                    sender_product,
                    sender_website,
                )

                with st.spinner("Finding the right angle and writing your outreach..."):
                    outreach = generate_single_prospect(
                        profile=cleaned_profile,
                        tone=tone,
                        goal=goal,
                        sender_info=formatted_sender,
                    )

                st.session_state.single_subject = outreach.get("subject", "")
                st.session_state.single_email = outreach.get("email", "")
                st.session_state.single_follow_up = outreach.get("follow_up", "")
                st.session_state.single_raw = outreach.get("raw_response", "")
                st.session_state.generated = True
                st.session_state.last_error = ""

                st.rerun()

            except Exception as e:
                st.session_state.last_error = f"Generation failed: {str(e)}"
                st.session_state.generated = False
                st.rerun()

        if st.session_state.last_error:
            st.markdown(
                f'<div class="error-note">{st.session_state.last_error}</div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            '<div class="caption" style="margin-top:12px;">Tip: include role, company, '
            'recent activity, priorities, or anything specific to the prospect.</div>',
            unsafe_allow_html=True,
        )

    with right:
        if st.session_state.generated and st.session_state.single_email:

            st.markdown("""
            <div class="result-shell">
                <div class="result-kicker">Generated outreach</div>
                <div class="result-title">Ready to send</div>
                <div class="result-meta">Personalised from your prospect context and selected intent.</div>
            </div>
            """, unsafe_allow_html=True)

            subject = st.session_state.single_subject
            email = st.session_state.single_email
            follow_up = st.session_state.single_follow_up

            st.markdown(f"""
            <div class="email-card">
                <div class="email-section">
                    <div class="email-label">Subject</div>
                    <div class="email-subject">{subject}</div>
                </div>
                <div class="email-section">
                    <div class="email-label">Email</div>
                    <div class="email-body">{email}</div>
                </div>
                <div class="email-section followup">
                    <div class="email-label">Follow-up message</div>
                    <div class="email-body">{follow_up}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.write("")

            combined_text = (
                f"Subject: {subject}\n\n"
                f"{email}\n\n"
                f"---\n\n"
                f"Follow-up:\n\n"
                f"{follow_up}"
            )

            action1, action2, action3 = st.columns([1, 1, 1])

            with action1:
                if st.button("↻ Regenerate", use_container_width=True):
                    # Reuse current inputs by triggering generation through a normal
                    # button-style rerun. Streamlit will preserve the entered state.
                    st.session_state.generated = False
                    st.rerun()

            with action2:
                st.download_button(
                    "↓ Export .txt",
                    data=combined_text,
                    file_name=safe_filename("cold_outreach", "txt"),
                    mime="text/plain",
                    use_container_width=True,
                )

            with action3:
                st.download_button(
                    "↓ Export .csv",
                    data=pd.DataFrame([{
                        "subject": subject,
                        "email": email,
                        "follow_up": follow_up,
                    }]).to_csv(index=False).encode("utf-8"),
                    file_name=safe_filename("cold_outreach", "csv"),
                    mime="text/csv",
                    use_container_width=True,
                )

            st.write("")

            with st.expander("Copy-ready version"):
                st.code(combined_text, language="text")

            with st.expander("View raw AI response"):
                st.code(st.session_state.single_raw or "No raw response available.", language="markdown")

        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-icon">✦</div>
                <div class="empty-title">Your outreach will appear here</div>
                <div class="empty-text">
                    Add a prospect profile, choose a tone and goal, then generate.
                    Your subject line, email and follow-up will be presented here.
                </div>
            </div>
            """, unsafe_allow_html=True)


# ============================================================
# BATCH MODE
# ============================================================

else:
    st.markdown("""
    <div class="card">
        <div class="card-title-row">
            <div>
                <div class="card-title">Batch outreach</div>
                <div class="card-subtitle">
                    Upload a CSV of prospects and generate personalised outreach for every row.
                </div>
            </div>
            <div class="step">01</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Prospect CSV",
        type=["csv"],
        help="Upload a CSV containing prospect information.",
    )

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)

            st.markdown("#### Preview")
            st.dataframe(
                df.head(5),
                use_container_width=True,
                hide_index=True,
            )

            is_valid, err_msg = validate_csv(df)

            if not is_valid:
                st.markdown(
                    f'<div class="error-note">{err_msg}</div>',
                    unsafe_allow_html=True,
                )
            else:
                col1, col2 = st.columns(2, gap="large")

                with col1:
                    st.markdown("#### Outreach settings")
                    batch_tone = st.radio(
                        "Tone",
                        tones,
                        horizontal=True,
                        key="batch_tone",
                    )
                    batch_goal = st.radio(
                        "Goal",
                        goals,
                        horizontal=True,
                        key="batch_goal",
                    )

                with col2:
                    st.markdown("#### Sender details")
                    with st.expander("Optional sender information", expanded=True):
                        b_sender_name = st.text_input("Your name", key="b_name")
                        b_sender_company = st.text_input("Your company", key="b_company")
                        b_sender_role = st.text_input("Your role", key="b_role")
                        b_sender_product = st.text_input("Product / service", key="b_product")
                        b_sender_website = st.text_input("Website", key="b_web")

                st.write("")

                generate_batch_btn = st.button(
                    "✦  Generate outreach for all prospects",
                    type="primary",
                    use_container_width=True,
                    disabled=api_key_missing,
                )

                if generate_batch_btn:
                    try:
                        formatted_sender = validate_sender_info(
                            b_sender_name,
                            b_sender_company,
                            b_sender_role,
                            b_sender_product,
                            b_sender_website,
                        )

                        records = df.to_dict(orient="records")
                        for record in records:
                            record["built_profile"] = build_profile(record)

                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        def update_progress(current, total, name):
                            pct = current / total if total else 0
                            progress_bar.progress(pct)
                            status_text.markdown(
                                f"**Generating {current} / {total}** — {name}"
                            )

                        with st.spinner("Processing batch outreach..."):
                            results = generate_batch(
                                prospects=records,
                                tone=batch_tone,
                                goal=batch_goal,
                                sender_info=formatted_sender,
                                progress_callback=update_progress,
                            )

                        status_text.success(
                            f"Successfully processed {len(records)} prospects."
                        )

                        res_df = pd.DataFrame(results)

                        if "built_profile" in res_df.columns:
                            res_df = res_df.drop(columns=["built_profile"])

                        st.session_state.batch_results = res_df

                    except Exception as e:
                        st.markdown(
                            f'<div class="error-note">Batch generation failed: {str(e)}</div>',
                            unsafe_allow_html=True,
                        )

        except Exception as e:
            st.markdown(
                f'<div class="error-note">Could not read CSV: {str(e)}</div>',
                unsafe_allow_html=True,
            )

    if st.session_state.batch_results is not None:
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="result-shell">
            <div class="result-kicker">Batch complete</div>
            <div class="result-title">Your personalised outreach set</div>
            <div class="result-meta">Review the generated messages below or export the full dataset.</div>
        </div>
        """, unsafe_allow_html=True)

        st.dataframe(
            st.session_state.batch_results,
            use_container_width=True,
            hide_index=True,
        )

        csv_data = st.session_state.batch_results.to_csv(index=False).encode("utf-8")

        st.download_button(
            "↓  Download completed CSV",
            data=csv_data,
            file_name=safe_filename("personalised_outreach", "csv"),
            mime="text/csv",
            use_container_width=True,
        )


# ============================================================
# FOOTER
# ============================================================

st.markdown("""
<div style="text-align:center; margin-top:65px; color:#9aa0aa; font-size:11px;">
    Cold Outreach Personaliser · Built for thoughtful outbound
</div>
""", unsafe_allow_html=True)
