import streamlit as st
import os
import sys
import base64
import tempfile
import time
import uuid
import hashlib
import io
import json
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv

try:
    import qrcode
except ImportError:
    qrcode = None

# Add backend to path so we can import our modules
# We add the current directory to sys.path to allow "from backend import ..."
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Load environment variables (API keys) from .env file
load_dotenv(os.path.join(current_dir, ".env"))

try:
    # AJOUTEZ analyze_document_with_ai à la fin de cette ligne 👇
    from backend.rag_engine import initialize_rag_system, get_answer, analyze_document_with_ai
    from backend.voice_processor import transcribe_audio, text_to_speech
except ImportError:
    sys.path.append(os.path.join(current_dir, "backend"))
    # ET ICI AUSSI 👇
    from rag_engine import initialize_rag_system, get_answer, analyze_document_with_ai
    from voice_processor import transcribe_audio, text_to_speech

# Page Config
st.set_page_config(
    page_title="Khadamat AI",
    page_icon=":material/account_balance:",
    layout="centered"
)

# Background image path requested by user
bg_image_path = r"C:\Users\pc\Downloads\WhatsApp Image 2026-03-12 at 15.42.42.jpeg"
bg_image_css = ""

if os.path.exists(bg_image_path):
    try:
        with open(bg_image_path, "rb") as image_file:
            image_base64 = base64.b64encode(image_file.read()).decode("utf-8")
        bg_image_css = f"""
        .stApp {{
            background-image:
                linear-gradient(rgba(0, 0, 0, 0.20), rgba(0, 0, 0, 0.20)),
                url("data:image/jpeg;base64,{image_base64}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        """
    except Exception:
        bg_image_css = ".stApp { background-color: #1b1b1b; }"
else:
    bg_image_css = ".stApp { background-color: #1b1b1b; }"

# Inject background CSS separately to avoid f-string brace parsing issues
st.markdown(f"<style>{bg_image_css}</style>", unsafe_allow_html=True)

# Custom CSS for "Senior Friendly" UI (Large fonts, clear contrast, RTL support)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel+Decorative:wght@700&display=swap');

    :root {
        --khadamat-beige: #DFA863;
        --khadamat-beige-soft: #e7ba82;
        --khadamat-beige-muted: #b9894f;
        --khadamat-light-gray: transparent;
        --khadamat-light-gray-border: rgba(223, 168, 99, 0.42);
        --kh-header-width: min(760px, calc(100vw - 3.2rem));
        --kh-cutoff-top: 12.2rem;
        --kh-cutoff-bottom: 9.8rem;
    }

    .stApp {
        position: relative;
        overflow-x: hidden;
    }

    /* Supprime la bande blanche fixe en bas (plusieurs versions Streamlit). */
    [data-testid="stBottom"],
    [data-testid="stBottom"] > div,
    [data-testid="stBottomBlockContainer"],
    [data-testid="stBottomBlockContainer"] > div,
    [data-testid="stChatFloatingInputContainer"],
    [data-testid="stChatInputContainer"] {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        z-index: 1360 !important;
    }

    /* Le wrapper principal reste transparent, seul le fond image est visible. */
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewContainer"] > .main {
        position: relative;
        z-index: 1;
        background: transparent !important;
        background-color: transparent !important;
    }

    /* Barre de saisie: force la transparence sur toutes les couches internes. */
    [data-testid="stChatInput"],
    [data-testid="stChatInput"] > div,
    [data-testid="stChatInput"] > div > div,
    [data-testid="stChatInput"] [data-baseweb="textarea"] {
        background: transparent !important;
        background-color: transparent !important;
        border: 1px solid var(--khadamat-light-gray-border) !important;
        border-radius: 12px !important;
        box-shadow: 0 8px 22px rgba(0, 0, 0, 0.22);
    }

    /* Audio: carte beige pleine (comme la bulle). */
    [data-testid="stAudioInput"],
    [data-testid="stAudioInput"] > div,
    [data-testid="stAudioInput"] > div > div,
    [data-testid="stAudioInput"] section {
        background: #DFA863 !important;
        background-color: #DFA863 !important;
        border: 1px solid rgba(106, 66, 20, 0.45) !important;
        border-radius: 18px !important;
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.22), inset 0 1px 0 rgba(255, 242, 220, 0.22) !important;
        overflow: hidden !important;
    }

    /* Blocs widgets transparents (upload + boutons secondaires). */
    [data-testid="stFileUploaderDropzone"],
    [data-testid="stFileUploader"] section,
    [data-testid="stFileUploader"] > div,
    [data-testid="stFileUploader"] button,
    [data-testid="stBaseButton-secondary"] {
        background: transparent !important;
        background-color: transparent !important;
        border: 1px solid var(--khadamat-light-gray-border) !important;
        color: var(--khadamat-beige) !important;
        box-shadow: none !important;
    }

    [data-testid="stFileUploader"] svg {
        color: var(--khadamat-beige) !important;
        fill: var(--khadamat-beige) !important;
    }

    [data-testid="stAudioInput"] section {
        padding: 0.2rem 0.25rem !important;
    }

    [data-testid="stAudioInput"] button {
        background: rgba(28, 18, 9, 0.16) !important;
        background-color: rgba(28, 18, 9, 0.16) !important;
        border: 1px solid rgba(28, 18, 9, 0.28) !important;
        border-radius: 999px !important;
    }

    [data-testid="stAudioInput"] svg,
    [data-testid="stAudioInput"] span,
    [data-testid="stAudioInput"] label,
    [data-testid="stAudioInput"] p {
        color: #1f160c !important;
        fill: #1f160c !important;
        font-weight: 600 !important;
    }

    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMarkdownContainer"],
    [data-testid="stChatMessageContent"],
    [data-testid="stChatMessageContent"] p,
    [data-testid="stChatMessageContent"] li,
    [data-testid="stChatMessageContent"] span,
    [data-testid="stFileUploader"] label,
    [data-testid="stWidgetLabel"],
    .stCaption,
    .stAlert,
    .stInfo,
    .stSuccess,
    .stWarning,
    .stError,
    p,
    li,
    label,
    span {
        color: var(--khadamat-beige-soft) !important;
    }

    /* Bulles de conversation */
    [data-testid="stChatMessageContent"] {
        background: #DFA863 !important;
        color: #1f160c !important;
        border: 1px solid rgba(113, 74, 28, 0.22) !important;
        border-radius: 16px !important;
        padding: 0.85rem 1rem !important;
        margin-left: -0.4rem !important;
        box-shadow: 0 10px 22px rgba(0, 0, 0, 0.18);
    }

    [data-testid="stChatMessageContent"] p,
    [data-testid="stChatMessageContent"] li,
    [data-testid="stChatMessageContent"] span {
        color: #1f160c !important;
    }

    /* Place l'icone du bot dans la bulle assistant. */
    [data-testid="stChatMessage"] {
        overflow: visible !important;
    }

    [data-testid="stChatMessageAvatarAssistant"] {
        position: relative;
        z-index: 3;
        margin-right: -1.45rem !important;
        margin-top: 0.55rem !important;
        background: #001f3f !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        box-shadow: 0 6px 14px rgba(10, 34, 63, 0.28);
    }

    [data-testid="stChatMessageAvatarUser"] {
        position: relative;
        z-index: 3;
        margin-right: -1.45rem !important;
        margin-top: 0.55rem !important;
        background: #001f3f !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        box-shadow: 0 6px 14px rgba(10, 34, 63, 0.28);
    }

    [data-testid="stChatMessageAvatarAssistant"] svg,
    [data-testid="stChatMessageAvatarAssistant"] path,
    [data-testid="stChatMessageAvatarAssistant"] span,
    [data-testid="stChatMessageAvatarUser"] svg,
    [data-testid="stChatMessageAvatarUser"] path,
    [data-testid="stChatMessageAvatarUser"] span {
        color: #ffffff !important;
        fill: #ffffff !important;
    }

    [data-testid="stChatMessageAvatarAssistant"] + [data-testid="stChatMessageContent"],
    [data-testid="stChatMessageAvatarUser"] + [data-testid="stChatMessageContent"] {
        margin-left: -1.5rem !important;
        padding-left: 4rem !important;
    }

    h1,
    h2,
    h3 {
        color: var(--khadamat-beige) !important;
        text-shadow: 0 2px 12px rgba(0, 0, 0, 0.65);
    }

    /* Effet lumineux animé sur le titre principal */
    @keyframes kh-title-glow {
        0%   { text-shadow: 0 0 10px #DFA863, 0 0 22px #c4893a, 0 0 40px #a8692a, 0 2px 12px rgba(0,0,0,0.55); }
        50%  { text-shadow: 0 0 18px #f5c97a, 0 0 38px #DFA863, 0 0 60px #c4893a, 0 2px 14px rgba(0,0,0,0.55); }
        100% { text-shadow: 0 0 10px #DFA863, 0 0 22px #c4893a, 0 0 40px #a8692a, 0 2px 12px rgba(0,0,0,0.55); }
    }

    @keyframes kh-icon-glow {
        0%   { filter: drop-shadow(0 0  6px #DFA863) drop-shadow(0 0 14px #c4893a); }
        50%  { filter: drop-shadow(0 0 12px #f5c97a) drop-shadow(0 0 24px #DFA863); }
        100% { filter: drop-shadow(0 0  6px #DFA863) drop-shadow(0 0 14px #c4893a); }
    }

    /* Oiseaux decoratifs en vol */
    @keyframes kh-bird-flight {
        0% {
            transform: translateX(-14vw) translateY(0) scale(0.86);
            opacity: 0;
        }
        8% {
            opacity: 0.95;
        }
        50% {
            transform: translateX(52vw) translateY(-8px) scale(0.98);
            opacity: 0.9;
        }
        92% {
            opacity: 0.9;
        }
        100% {
            transform: translateX(112vw) translateY(4px) scale(0.9);
            opacity: 0;
        }
    }

    @keyframes kh-bird-wing {
        0%, 100% { transform: scaleY(1); }
        50% { transform: scaleY(0.72); }
    }

    .kh-bird-sky {
        position: fixed;
        inset: 0;
        pointer-events: none;
        overflow: hidden;
        z-index: 1415;
    }

    .kh-bird {
        position: absolute;
        top: 6.4rem;
        left: -7rem;
        width: 50px;
        height: 26px;
        color: rgba(223, 168, 99, 0.95);
        filter: drop-shadow(0 0 7px rgba(223, 168, 99, 0.36));
        animation: kh-bird-flight 14s linear infinite;
    }

    .kh-bird svg {
        width: 100%;
        height: 100%;
        animation: kh-bird-wing 0.55s ease-in-out infinite;
        transform-origin: center;
    }

    .kh-bird.b2 {
        top: 8.1rem;
        width: 42px;
        height: 22px;
        opacity: 0.78;
        animation-duration: 16.5s;
        animation-delay: -7.2s;
    }

    .kh-page-title span {
        animation: kh-title-glow 3.2s ease-in-out infinite;
    }

    .kh-page-title .kh-icon {
        animation: kh-icon-glow 3.2s ease-in-out infinite;
    }

    .kh-heading,
    .kh-page-title,
    .kh-inline-text,
    .kh-status-row,
    .kh-center-link {
        display: flex;
        align-items: center;
        gap: 0.65rem;
    }

    .kh-page-title {
        margin: 0;
        font-size: 2.6rem;
        line-height: 1.15;
        position: sticky;
        top: 0.35rem;
        z-index: 1000;
        width: fit-content;
        padding: 0.2rem 0.45rem;
        border-radius: 10px;
        background: linear-gradient(90deg, rgba(8, 13, 24, 0.78), rgba(8, 13, 24, 0.35));
        backdrop-filter: blur(3px);
        -webkit-backdrop-filter: blur(3px);
    }

    .kh-page-title span {
        font-family: 'Cinzel Decorative', serif;
        font-weight: 700;
        letter-spacing: 0.02em;
    }

    .kh-heading {
        margin: 0;
    }

    .kh-icon {
        width: 1.15em;
        height: 1.15em;
        flex: 0 0 auto;
        color: var(--khadamat-beige);
    }

    .kh-page-title .kh-icon {
        width: 1.05em;
        height: 1.05em;
    }

    /* Entete fixe en haut: titre + sous-titre */
    .kh-fixed-header {
        position: fixed;
        top: 5rem;
        left: 50%;
        transform: translateX(-50%);
        width: var(--kh-header-width);
        z-index: 1400;
        padding: 0.45rem 0.8rem 0.65rem;
        border-radius: 14px;
        border: 1px solid rgba(223, 168, 99, 0.28);
        background: linear-gradient(90deg, rgba(5, 10, 20, 0.93), rgba(9, 17, 33, 0.76));
        box-shadow: 0 12px 26px rgba(0, 0, 0, 0.35);
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
        text-align: left;
    }

    .kh-fixed-title {
        display: flex;
        align-items: center;
        justify-content: flex-start;
        gap: 0.55rem;
    }

    .kh-fixed-title-text {
        font-family: 'Cinzel Decorative', serif;
        font-size: clamp(1.45rem, 2.3vw, 2.35rem);
        color: var(--khadamat-beige);
        line-height: 1.08;
        animation: kh-title-glow 3.2s ease-in-out infinite;
    }

    .kh-fixed-title .kh-icon {
        width: clamp(1.45rem, 2.3vw, 2.35rem);
        height: clamp(1.45rem, 2.3vw, 2.35rem);
        animation: kh-icon-glow 3.2s ease-in-out infinite;
    }

    .kh-fixed-subtitle {
        margin-top: 0.85rem;
        font-size: clamp(1rem, 1.55vw, 1.45rem);
        font-weight: 700;
        color: var(--khadamat-beige-soft) !important;
        line-height: 1.25;
        text-align: left;
    }

    /* Ligne fixe + masque: les messages disparaissent en la traversant. */
    .kh-scroll-cutoff-mask {
        position: fixed;
        top: 0;
        left: 50%;
        transform: translateX(-50%);
        width: var(--kh-header-width);
        height: var(--kh-cutoff-top);
        z-index: 1320;
        pointer-events: none;
        background: rgba(5, 10, 20, 0.98);
        border-bottom-left-radius: 18px;
        border-bottom-right-radius: 18px;
    }

    .kh-scroll-cutoff-line {
        position: fixed;
        top: var(--kh-cutoff-top);
        left: 50%;
        transform: translateX(-50%);
        width: var(--kh-header-width);
        height: 2px;
        z-index: 1340;
        pointer-events: none;
        background: linear-gradient(
            90deg,
            rgba(223, 168, 99, 0.02) 0%,
            rgba(223, 168, 99, 0.58) 14%,
            rgba(223, 168, 99, 0.9) 50%,
            rgba(223, 168, 99, 0.58) 86%,
            rgba(223, 168, 99, 0.02) 100%
        );
        box-shadow: 0 0 10px rgba(223, 168, 99, 0.32);
    }

    .kh-bottom-cutoff-mask {
        position: fixed;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: var(--kh-header-width);
        height: var(--kh-cutoff-bottom);
        z-index: 1320;
        pointer-events: none;
        background: rgba(5, 10, 20, 0.98);
        border-top-left-radius: 18px;
        border-top-right-radius: 18px;
    }

    .kh-bottom-cutoff-line {
        position: fixed;
        bottom: var(--kh-cutoff-bottom);
        left: 50%;
        transform: translateX(-50%);
        width: var(--kh-header-width);
        height: 2px;
        z-index: 1340;
        pointer-events: none;
        background: linear-gradient(
            90deg,
            rgba(223, 168, 99, 0.02) 0%,
            rgba(223, 168, 99, 0.58) 14%,
            rgba(223, 168, 99, 0.9) 50%,
            rgba(223, 168, 99, 0.58) 86%,
            rgba(223, 168, 99, 0.02) 100%
        );
        box-shadow: 0 0 10px rgba(223, 168, 99, 0.32);
    }

    .kh-status-row {
        font-size: 1.05rem;
        margin-bottom: 0.2rem;
    }

    .kh-center-link {
        margin: 0.35rem 0;
    }

    .kh-center-link a {
        color: var(--khadamat-beige-soft) !important;
        text-decoration: none;
        font-weight: 600;
    }

    .kh-center-link a:hover {
        color: var(--khadamat-beige) !important;
        text-decoration: underline;
    }

    .stChatInput textarea {
        font-size: 0.96rem !important;
        line-height: 1.3 !important;
        color: var(--khadamat-beige-soft) !important;
        caret-color: var(--khadamat-beige) !important;
        background: transparent !important;
    }

    .stChatInput textarea::placeholder {
        font-size: 0.96rem !important;
        color: var(--khadamat-beige-muted) !important;
        opacity: 1 !important;
    }

    [data-testid="stChatInput"] button,
    [data-testid="stChatInput"] button svg,
    [data-testid="stChatInputSubmitButton"],
    [data-testid="stChatInputSubmitButton"] svg {
        color: var(--khadamat-beige) !important;
        fill: var(--khadamat-beige) !important;
    }
    
    /* --- MODIFICATION ICI POUR L'ARABE (RTL) --- */
    p, li {
        font-size: 1.1rem;
        unicode-bidi: plaintext; /* Détecte la langue automatiquement */
        text-align: start;       /* Aligne selon la langue détectée */
    }
    
    .stButton button {
        background-color: #2e7d32;
        color: white;
        font-size: 1.2rem;
        height: 2.7em;
        width: 100%;
        border-radius: 10px;
    }
    .block-container {
        padding-top: 12.6rem;
        padding-bottom: calc(2rem + var(--kh-cutoff-bottom));
    }

    @media (max-width: 768px) {
        :root {
            --kh-header-width: calc(100vw - 1.8rem);
            --kh-cutoff-top: 11rem;
            --kh-cutoff-bottom: 8.5rem;
        }

        .kh-fixed-header {
            padding: 0.55rem 0.7rem 0.7rem;
            top: 4.2rem;
        }

        .block-container {
            padding-top: 11.4rem;
        }

        .kh-bird {
            top: 6rem;
            width: 42px;
            height: 22px;
        }

        .kh-bird.b2 {
            top: 7.4rem;
            width: 36px;
            height: 19px;
        }
    }
</style>
""", unsafe_allow_html=True)

ICON_BUILDING = """
<svg viewBox="0 0 24 24" class="kh-icon" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
    <path d="M3 10.5 12 4l9 6.5"/>
    <path d="M4 10h16"/>
    <path d="M6 10v8"/>
    <path d="M10 10v8"/>
    <path d="M14 10v8"/>
    <path d="M18 10v8"/>
    <path d="M3 18h18"/>
</svg>
"""

ICON_MICROPHONE = """
<svg viewBox="0 0 24 24" class="kh-icon" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
    <path d="M12 15a3 3 0 0 0 3-3V7a3 3 0 0 0-6 0v5a3 3 0 0 0 3 3Z"/>
    <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
    <path d="M12 19v3"/>
    <path d="M9 22h6"/>
</svg>
"""

ICON_DOCUMENT = """
<svg viewBox="0 0 24 24" class="kh-icon" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
    <path d="M8 3h6l5 5v13H8a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"/>
    <path d="M14 3v5h5"/>
    <path d="M10 13h6"/>
    <path d="M10 17h6"/>
</svg>
"""

ICON_LOCATION = """
<svg viewBox="0 0 24 24" class="kh-icon" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
    <path d="M12 21s-6-4.35-6-10a6 6 0 1 1 12 0c0 5.65-6 10-6 10Z"/>
    <circle cx="12" cy="11" r="2.5"/>
</svg>
"""

ICON_SHIELD = """
<svg viewBox="0 0 24 24" class="kh-icon" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
    <path d="M12 3 19 6v6c0 5-3.5 7.5-7 9-3.5-1.5-7-4-7-9V6l7-3Z"/>
    <path d="m9 12 2 2 4-4"/>
</svg>
"""

ICON_CHECK = """
<svg viewBox="0 0 24 24" class="kh-icon" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="12" cy="12" r="9"/>
    <path d="m8.5 12 2.5 2.5 4.5-5"/>
</svg>
"""

ICON_X = """
<svg viewBox="0 0 24 24" class="kh-icon" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="12" cy="12" r="9"/>
    <path d="m9 9 6 6"/>
    <path d="m15 9-6 6"/>
</svg>
"""


def render_heading(text: str, icon_svg: str, level: int = 3) -> None:
    st.markdown(
        f"<h{level} class='kh-heading'>{icon_svg}<span>{text}</span></h{level}>",
        unsafe_allow_html=True,
    )


def render_page_title(text: str, icon_svg: str) -> None:
    st.markdown(
        f"<h1 class='kh-page-title'>{icon_svg}<span>{text}</span></h1>",
        unsafe_allow_html=True,
    )


def render_fixed_header(title: str, subtitle: str, icon_svg: str) -> None:
    st.markdown(
        f"""
        <div class='kh-fixed-header'>
            <div class='kh-fixed-title'>{icon_svg}<span class='kh-fixed-title-text'>{title}</span></div>
            <div class='kh-fixed-subtitle'>{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_flying_birds() -> None:
    st.markdown(
        """
        <div class='kh-bird-sky' aria-hidden='true'>
            <div class='kh-bird'>
                <svg viewBox='0 0 48 24' fill='none' stroke='currentColor' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'>
                    <path d='M2 14 Q12 4 22 14'/>
                    <path d='M22 14 Q32 4 46 14'/>
                </svg>
            </div>
            <div class='kh-bird b2'>
                <svg viewBox='0 0 48 24' fill='none' stroke='currentColor' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'>
                    <path d='M2 14 Q12 4 22 14'/>
                    <path d='M22 14 Q32 4 46 14'/>
                </svg>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Header
render_fixed_header("Khadamat AI", "L'Assistant Administratif Intelligent / المساعد الإداري الذكي", ICON_BUILDING)
render_flying_birds()
st.markdown("<div class='kh-scroll-cutoff-mask'></div><div class='kh-scroll-cutoff-line'></div><div class='kh-bottom-cutoff-mask'></div><div class='kh-bottom-cutoff-line'></div>", unsafe_allow_html=True)
st.markdown("---")

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Salam! Je suis Khadamat AI. Je peux vous aider avec vos procédures administratives (CIN, Passeport, etc.).\n\nالسلام عليكم! أنا خدمات AI. نقدر نعاونك فالإجراءات الإدارية ديالك (لاكارط، الباسبور، ...)."}
    ]

# Initialize RAG System (Cached to run only once)
# Removed cache_resource temporarily to force reload during development/debugging
def load_backend():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_files = [
        os.path.join(base_dir, "morocco_admin_dataset.md"),
        os.path.join(base_dir, "version arabe.md"),
        os.path.join(base_dir, "version darija.md")
    ]
    with st.spinner("Chargement des connaissances... / جاري تحميل المعلومات..."):
        try:
            initialize_rag_system(data_files)
            return True
        except Exception as e:
            st.error(f"Erreur de chargement: {e}")
            return False

if "backend_loaded" not in st.session_state or not st.session_state.backend_loaded:
    st.session_state.backend_loaded = load_backend()

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Section selector
if "active_section" not in st.session_state:
    st.session_state.active_section = "voice"

render_heading("Choisissez un service / اختَر الخدمة", ICON_BUILDING)
nav_row_1 = st.columns(2)
nav_row_2 = st.columns(2)

if nav_row_1[0].button("Question vocale", key="nav_voice", use_container_width=True):
    st.session_state.active_section = "voice"
if nav_row_1[1].button("Scanner document", key="nav_scan", use_container_width=True):
    st.session_state.active_section = "scan"
if nav_row_2[0].button("Centre administratif", key="nav_location", use_container_width=True):
    st.session_state.active_section = "location"
if nav_row_2[1].button("Vérification dossier", key="nav_verification", use_container_width=True):
    st.session_state.active_section = "verification"

section_titles = {
    "voice": "Posez votre question vocalement / سول بالصوت",
    "scan": "Scanner un document / تحليل وثيقة",
    "location": "Trouver un Centre Administratif / أقرب إدارة",
    "verification": "Vérification de Dossier & QR Code",
}
current_section = st.session_state.active_section
st.caption(f"Section active: {section_titles.get(current_section, '')}")

if current_section == "voice":
    st.markdown("---")
    render_heading("Posez votre question vocalement / سول بالصوت", ICON_MICROPHONE)
    audio_value = st.audio_input("Enregistrer un message / سجل رسالة")

    if audio_value:
        if not st.session_state.get("backend_loaded", False):
            st.error("Le système n'est pas initialisé. Veuillez recharger la page.")
        else:
            try:
                # 1. Lire l'audio et créer une empreinte (hash) pour éviter les répétitions
                audio_value.seek(0)
                input_audio_bytes = audio_value.read()
                audio_hash = hashlib.md5(input_audio_bytes).hexdigest()

                # Vérifier si cet audio a déjà été traité
                if "last_audio_hash" not in st.session_state or st.session_state.last_audio_hash != audio_hash:
                    st.session_state.last_audio_hash = audio_hash

                    with st.spinner("Traitement audio... / جاري المعالجة..."):
                        # Save temporary file
                        suffix = ".wav"
                        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_audio:
                            temp_audio.write(input_audio_bytes)
                            temp_audio_path = temp_audio.name

                        # 1. Transcribe (STT)
                        transcription = transcribe_audio(temp_audio_path)

                        # Clean up input file
                        try:
                            os.remove(temp_audio_path)
                        except:
                            pass

                        if transcription:
                            # Add user message to chat
                            st.session_state.messages.append({"role": "user", "content": f"Message vocal: {transcription}"})
                            with st.chat_message("user"):
                                st.markdown(f"Message vocal: {transcription}")

                            # 2. Get Answer (RAG)
                            response_text = get_answer(transcription)

                            if response_text:
                                # 3. Text to Speech (TTS)
                                audio_response_path = f"response_{uuid.uuid4().hex}.mp3"
                                text_to_speech(response_text, audio_response_path)

                                # Display Assistant Response
                                st.session_state.messages.append({"role": "assistant", "content": response_text})
                                with st.chat_message("assistant"):
                                    st.markdown(response_text)
                                    if os.path.exists(audio_response_path) and os.path.getsize(audio_response_path) > 0:
                                        with open(audio_response_path, "rb") as f:
                                            audio_bytes = f.read()
                                        st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                                        os.remove(audio_response_path)
                            else:
                                st.error("Désolé, je n'ai pas pu trouver de réponse. / سمح ليا، ما لقيتش الجواب.")
                        else:
                            st.warning("Je n'ai pas bien entendu. Réessayez SVP. / ما سمعتش مزيان. عاود عفاك.")

            except Exception as e:
                st.error(f"Erreur audio: {e}")

elif current_section == "scan":
    st.markdown("---")
    render_heading("Scanner un document / تحليل وثيقة", ICON_DOCUMENT)
    uploaded_doc = st.file_uploader("Télécharger ou photographier (CIN, Formulaire, etc.)", type=["jpg", "jpeg", "png"])

    if uploaded_doc:
        st.image(uploaded_doc, caption="Document à analyser", use_container_width=True)

        if st.button("Lancer l'analyse / تحليل"):
            with st.spinner("Analyse en cours... / جاري التحليل..."):
                try:
                    # 1. Appel de la fonction backend
                    analysis_result = analyze_document_with_ai(uploaded_doc)

                    # 2. Affichage du texte
                    st.info("### Résultat de l'analyse :")
                    st.markdown(analysis_result)

                    # 3. Lecture vocale (TTS) finale
                    with st.spinner("Génération de l'audio... / جاري تحضير الصوت..."):
                        try:
                            audio_scan_path = f"scan_{uuid.uuid4().hex}.mp3"
                            clean_text = analysis_result.replace("*", "").replace("#", "")

                            text_to_speech(clean_text, audio_scan_path)

                            if os.path.exists(audio_scan_path) and os.path.getsize(audio_scan_path) > 0:
                                with open(audio_scan_path, "rb") as f:
                                    audio_bytes = f.read()

                                st.audio(audio_bytes, format="audio/mp3", autoplay=True)

                                # SUPPRIMEZ OU LAISSEZ CETTE LIGNE EN COMMENTAIRE (#)
                                # os.remove(audio_scan_path)
                            else:
                                st.warning("⚠️ L'audio n'a pas pu être généré (vérifiez la clé API ou le quota).")

                        except Exception as tts_error:
                            st.error(f"Erreur du système vocal : {tts_error}")

                except Exception as e:
                    if "429" in str(e):
                        st.warning("⏳ Le système est un peu surchargé. Veuillez patienter une minute avant de réessayer.")
                    else:
                        st.error(f"Erreur lors de l'analyse : {e}")

elif current_section == "location":
    st.markdown("---")
    render_heading("Trouver un Centre Administratif / أقرب إدارة", ICON_LOCATION)

    from streamlit_js_eval import get_geolocation

    # Define category mapping once
    cat_map = {
        "Commissariat (Police)": "police",
        "Moqataa / Commune": "municipality",
        "Tribunal": "court",
        "Wilaya": "wilaya",
        "Hôpital": "hospital",
        "Tout": "all",
    }
    center_type = st.selectbox("Type d'administration / نوع الإدارة", list(cat_map.keys()), index=0)

    # 1. Detect Location (Only option now)
    render_heading("Détection de votre position / تحديد موقعك", ICON_LOCATION)
    st.info("Cochez la case ci-dessous pour trouver les administrations près de chez vous. / ضع علامة لتحديد موقعك")

    if st.checkbox("Utiliser ma position actuelle / استعمال موقعي", value=False):
        geo_location = get_geolocation()
        if geo_location:
            user_lat = geo_location.get("coords", {}).get("latitude")
            user_lon = geo_location.get("coords", {}).get("longitude")

            if user_lat and user_lon:
                st.success(f"Position détectée: {user_lat:.4f}, {user_lon:.4f}")

                # Fetch results immediately
                with st.spinner("Recherche des centres proches... / جاري البحث..."):
                    try:
                        # Import inside try block to handle potential import errors gracefully
                        try:
                            from backend.location_service import LocationService
                        except ImportError as imp_err:
                            st.error(f"Erreur d'installation: Module 'geopy' manquant. (Détail: {imp_err})")
                            st.stop()

                        loc_service = LocationService()
                        category = cat_map.get(center_type, "all")
                        results = loc_service.find_nearby_centers(user_lat, user_lon, category)

                        if results:
                            st.write(f"**{len(results)} centres trouvés à proximité (5km) :**")
                            # Map
                            import pandas as pd

                            df_map = pd.DataFrame(results)
                            st.map(df_map)
                            # List
                            for r in results:
                                # Create Google Maps link
                                gmaps_link = f"https://www.google.com/maps/search/?api=1&query={r['lat']},{r['lon']}"
                                st.markdown(
                                    f"<div class='kh-center-link'>{ICON_BUILDING}<a href='{gmaps_link}' target='_blank'>{r['name']}</a></div>",
                                    unsafe_allow_html=True,
                                )
                        else:
                            st.warning("Aucun centre trouvé à proximité. / لم يتم العثور على مراكز قريبة.")

                    except Exception as e:
                        st.error(f"Erreur de recherche: {e}")
            else:
                st.warning("En attente de la position GPS... / في انتظار تحديد الموقع...")
        else:
            st.info("Veuillez autoriser la localisation dans votre navigateur. / المرجو السماح بتحديد الموقع.")

elif current_section == "verification":
    st.markdown("---")
    render_heading("Vérification de Dossier & QR Code", ICON_SHIELD)

    # Define all procedures with their required documents
    procedures_config = {
        "Renouvellement de la Carte Nationale (CNIE)": {
            "required_docs": [
                ("ancienne_carte", "1) Ancienne carte nationale"),
                ("photos_identite", "2) Photo(s) d'identité"),
            ],
            "conditional_docs": {
                "changed_address": ("address_proof", "3) Justificatif / certificat de résidence (si adresse changée)"),
            },
        },
        "Renouvellement de Passeport": {
            "required_docs": [
                ("acte_naissance", "1) Acte de naissance"),
                ("photos_identite", "2) Photo(s) d'identité (4x6 cm)"),
                ("cnie_copie", "3) Copie de la CNIE"),
            ],
            "conditional_docs": {},
        },
        "Permis de Conduire": {
            "required_docs": [
                ("cnie", "1) Carte Nationale (CNIE) originale ou copie"),
                ("photos_identite", "2) Photo(s) d'identité"),
                ("certificat_medical", "3) Certificat médical"),
            ],
            "conditional_docs": {},
        },
        "Acte de Naissance": {
            "required_docs": [
                ("cnie_parent1", "1) CNIE d'un parent"),
                ("photos_identite", "2) Photo(s) d'identité"),
                ("certificat_medical", "3) Certificat médical du nouveau-né (si applicable)"),
            ],
            "conditional_docs": {},
        },
    }

    procedure = st.selectbox(
        "Choisissez la procédure / اختر الإجراء",
        list(procedures_config.keys()),
        key="procedure_select",
    )

    if procedure in procedures_config:
        st.caption("Déposez les documents requis. Si tout est valide, un QR code 'verified' sera généré.")

        proc_config = procedures_config[procedure]
        required_docs = proc_config["required_docs"]
        conditional_docs = proc_config.get("conditional_docs", {})

        uploaded_docs = {}
        for doc_key, doc_label in required_docs:
            uploaded_docs[doc_key] = st.file_uploader(
                doc_label,
                type=["jpg", "jpeg", "png"],
                key=f"upload_{doc_key}",
            )

        # Handle conditional documents dynamically
        changed_address = False
        if "changed_address" in conditional_docs:
            changed_address = st.checkbox(
                "J'ai changé d'adresse (j'ajoute un justificatif)",
                value=False,
                key="changed_address",
            )
            if changed_address:
                upload_key, upload_label = conditional_docs["changed_address"]
                uploaded_docs[upload_key] = st.file_uploader(
                    upload_label,
                    type=["jpg", "jpeg", "png"],
                    key=f"upload_{upload_key}",
                )

        def is_doc_perfect(analysis_text: str) -> bool:
            text = (analysis_text or "").lower()
            has_correct = "correct" in text
            has_incomplete = "incomplet" in text
            has_missing = "manque" in text and "rien" not in text
            has_risk = "risque" in text and "aucun" not in text
            return has_correct and not has_incomplete and not has_missing and not has_risk

        def parse_date_from_text(text: str):
            patterns = [
                r"\b(\d{1,2})[./-](\d{1,2})[./-](\d{4})\b",
                r"\b(\d{4})[./-](\d{1,2})[./-](\d{1,2})\b",
            ]
            for pattern in patterns:
                for match in re.finditer(pattern, text or ""):
                    groups = match.groups()
                    try:
                        if pattern.startswith(r"\b(\d{1,2})"):
                            day, month, year = map(int, groups)
                        else:
                            year, month, day = map(int, groups)
                        return datetime(year, month, day).date()
                    except Exception:
                        continue
            return None

        def is_photo_ok_relaxed(analysis_text: str) -> bool:
            text = (analysis_text or "").lower()

            # Reject only hard blockers, keep this intentionally permissive.
            hard_blockers = [
                "inexploitable",
                "illisible",
                "trop flou",
                "aucun visage",
                "pas de visage",
                "visage non visible",
                "photo absente",
                "aucune photo",
            ]
            if any(token in text for token in hard_blockers):
                return False

            # Ear visibility is not blocking for this version.
            if "oreille" in text or "oreilles" in text:
                return True

            # Fall back to generic rule for other cases.
            return is_doc_perfect(analysis_text)

        def is_cnie_card_ok_with_expiry_rule(analysis_text: str) -> bool:
            text = (analysis_text or "").lower()

            # If card is unreadable, still reject.
            if any(token in text for token in ["inexploitable", "illisible", "mauvaise qualité"]):
                return False

            expiry_date = parse_date_from_text(analysis_text)
            if expiry_date is not None:
                today = datetime.utcnow().date()
                # Expired means today's date is strictly greater than card expiry date.
                return today > expiry_date

            # No explicit date found: stay permissive instead of over-rejecting.
            return is_doc_perfect(analysis_text)

        def evaluate_doc(doc_key: str, analysis_text: str) -> bool:
            if doc_key == "photos_identite":
                return is_photo_ok_relaxed(analysis_text)
            if doc_key == "ancienne_carte":
                return is_cnie_card_ok_with_expiry_rule(analysis_text)
            return is_doc_perfect(analysis_text)

        if st.button("Vérifier le dossier et générer le QR", key="verify_qr_button"):
            missing = [label for key, label in required_docs if not uploaded_docs.get(key)]
            if changed_address and not uploaded_docs.get("address_proof"):
                missing.append(conditional_docs.get("changed_address", ("", ""))[1])

            if missing:
                st.error("Dossier incomplet. Documents manquants:")
                for item in missing:
                    st.markdown(f"- {item}")
            elif not st.session_state.get("backend_loaded", False):
                st.error("Le moteur d'analyse n'est pas prêt. Veuillez recharger la page.")
            elif qrcode is None:
                st.error("Le module 'qrcode' n'est pas installé. Installez-le avec: pip install qrcode[pil]")
            else:
                with st.spinner("Analyse des documents en cours..."):
                    doc_results = []

                    for doc_key, doc_label in required_docs:
                        analysis = analyze_document_with_ai(
                            uploaded_docs[doc_key],
                            user_context=(
                                f"Procédure: {procedure}. "
                                f"Document attendu: {doc_label}. "
                                "Important: Pour les cartes et documents d'identité, mentionne clairement la date d'expiration si visible "
                                "(format JJ/MM/AAAA). Un document est expiré si la date d'aujourd'hui est strictement supérieure à sa date d'expiration. "
                                "Pour les photos d'identité, sois tolérant et ne bloque pas seulement pour les oreilles. "
                                "Référence la procédure pour des critères spécifiques."
                            ),
                        )
                        doc_results.append(
                            {
                                "name": doc_label,
                                "analysis": analysis,
                                "ok": evaluate_doc(doc_key, analysis),
                            }
                        )

                    if changed_address and "address_proof" in uploaded_docs:
                        analysis = analyze_document_with_ai(
                            uploaded_docs["address_proof"],
                            user_context=f"Procédure: {procedure}. Document attendu: Justificatif de résidence",
                        )
                        doc_results.append(
                            {
                                "name": "Justificatif / certificat de résidence",
                                "analysis": analysis,
                                "ok": is_doc_perfect(analysis),
                            }
                        )

                all_verified = all(item["ok"] for item in doc_results)
                status = "verified" if all_verified else "incomplete"

                st.markdown("#### Résultat de vérification")
                for item in doc_results:
                    badge = ICON_CHECK if item["ok"] else ICON_X
                    st.markdown(
                        f"<div class='kh-status-row'>{badge}<strong>{item['name']}</strong></div>",
                        unsafe_allow_html=True,
                    )
                    st.caption(item["analysis"])

                if all_verified:
                    payload = {
                        "status": "verified",
                        "procedure": procedure.upper().replace(" ", "_").replace("(", "").replace(")", ""),
                        "verified_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                        "verification_id": str(uuid.uuid4()),
                    }

                    qr_data = json.dumps(payload, ensure_ascii=False)
                    qr_img = qrcode.make(qr_data)
                    buf = io.BytesIO()
                    qr_img.save(buf, format="PNG")
                    qr_bytes = buf.getvalue()

                    st.success("Dossier validé. QR code VERIFIED généré.")
                    st.image(qr_bytes, caption="QR Code - VERIFIED", width=260)
                    st.download_button(
                        label="Télécharger le QR code",
                        data=qr_bytes,
                        file_name="cnie_verified_qr.png",
                        mime="image/png",
                    )
                else:
                    st.warning(f"Statut du dossier: {status}. Corrigez les documents puis réessayez.")

# --- TEXT INPUT HANDLING ---
# Assurez-vous que cette ligne est tout à gauche (sans espace avant)
user_input = st.chat_input("Écrivez votre question ici / اكتب سؤالك هنا")

if user_input:
    # Display User Message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Process
    if st.session_state.backend_loaded:
        with st.spinner("Recherche de la réponse... / كنقلب على الجواب..."):
            response = get_answer(user_input)
            
            # Display Assistant Message
            st.session_state.messages.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.markdown(response)

                # --- AUDIO RESPONSE FOR TEXT INPUT (Added) ---
                try:
                    # Clean text specifically for TTS to avoid reading markdown symbols
                    clean_response = response.replace("*", "").replace("#", "").replace("-", "")
                    
                    audio_text_path = f"response_text_{uuid.uuid4().hex}.mp3"
                    text_to_speech(clean_response, audio_text_path)
                    
                    if os.path.exists(audio_text_path) and os.path.getsize(audio_text_path) > 0:
                        with open(audio_text_path, "rb") as f:
                            audio_bytes = f.read()
                        st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                        # os.remove(audio_text_path) # Optional clean up
                except Exception as e:
                    st.warning(f"Audio non disponible: {e}")
    else:
        st.error("Le système n'est pas initialisé.")
