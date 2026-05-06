"""Tema visual SMNYL aplicado a Streamlit.

Centraliza tokens de marca (colores, tipografías, spacing, sombras) y la
inyección de CSS custom para que la app cumpla con BRAND_GUIDELINES.md y
no se vea como un prototipo Streamlit default.

Fuente única de verdad: docs/BRAND_GUIDELINES.md §8.
"""

from __future__ import annotations

import streamlit as st

SMNYL_COLORS: dict[str, str] = {
    "primary": "#0079c2",  # New York Life Blue
    "primary_dark": "#0a385e",  # Dark Rain
    "bg": "#ffffff",
    "bg_soft": "#f4f5f6",  # Quartz mezclado
    "text": "#0a3c53",  # Steel
    "text_muted": "#565656",  # Iron
    "border": "#bdc1c2",  # Quartz
    "success": "#4b8b7f",  # Medium Pine
    "warning": "#ce7046",  # Medium Sunset
    "danger": "#754a62",  # Dark Rose
    "info": "#2e86af",  # Medium Rain
    "accent_soft": "#b2d4e4",  # Light Rain
}

SMNYL_FONTS: dict[str, str] = {
    "display": 'Georgia, "Times New Roman", serif',
    "body": 'Tahoma, "Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif',
}

SMNYL_SPACING: dict[str, str] = {
    "xs": "4px",
    "sm": "8px",
    "md": "16px",
    "lg": "24px",
    "xl": "40px",
    "2xl": "64px",
}

SMNYL_RADIUS: dict[str, str] = {
    "sm": "4px",
    "md": "8px",
    "lg": "12px",
}

SMNYL_SHADOW: dict[str, str] = {
    "sm": "0 1px 2px rgba(10, 60, 83, 0.06)",
    "md": "0 4px 12px rgba(10, 60, 83, 0.08)",
    "lg": "0 12px 32px rgba(10, 60, 83, 0.12)",
}


def _build_css() -> str:
    c = SMNYL_COLORS
    f = SMNYL_FONTS
    sp = SMNYL_SPACING
    r = SMNYL_RADIUS
    sh = SMNYL_SHADOW

    return f"""
    <style>
    /* Georgia y Tahoma son fuentes nativas de Windows/Mac — no requieren @import */

    :root {{
        --color-primary: {c["primary"]};
        --color-primary-dark: {c["primary_dark"]};
        --color-bg: {c["bg"]};
        --color-bg-soft: {c["bg_soft"]};
        --color-text: {c["text"]};
        --color-text-muted: {c["text_muted"]};
        --color-border: {c["border"]};
        --color-success: {c["success"]};
        --color-warning: {c["warning"]};
        --color-danger: {c["danger"]};
        --color-info: {c["info"]};
        --color-accent-soft: {c["accent_soft"]};

        --font-display: {f["display"]};
        --font-body: {f["body"]};

        --space-xs: {sp["xs"]};
        --space-sm: {sp["sm"]};
        --space-md: {sp["md"]};
        --space-lg: {sp["lg"]};
        --space-xl: {sp["xl"]};
        --space-2xl: {sp["2xl"]};

        --radius-sm: {r["sm"]};
        --radius-md: {r["md"]};
        --radius-lg: {r["lg"]};

        --shadow-sm: {sh["sm"]};
        --shadow-md: {sh["md"]};
        --shadow-lg: {sh["lg"]};
    }}

    /* Ocultar elementos default de Streamlit que no queremos */
    #MainMenu, header[data-testid="stHeader"] {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    .stDeployButton {{ display: none; }}
    [data-testid="stToolbar"] {{ display: none; }}

    /* Tipografía base */
    html, body, [class*="css"], .stApp {{
        font-family: var(--font-body);
        color: var(--color-text);
        background-color: var(--color-bg);
    }}

    h1, h2, h3, h4, h5, h6 {{
        font-family: var(--font-display);
        color: var(--color-text);
        letter-spacing: -0.01em;
        line-height: 1.2;
    }}

    h1 {{ font-size: 2.25rem; font-weight: 600; margin-bottom: var(--space-md); }}
    h2 {{ font-size: 1.75rem; font-weight: 500; margin-top: var(--space-xl); }}
    h3 {{ font-size: 1.25rem; font-weight: 500; }}

    p, li, span, label {{
        font-family: var(--font-body);
        color: var(--color-text);
        line-height: 1.6;
    }}

    /* Botones primarios */
    .stButton > button {{
        font-family: var(--font-body);
        font-weight: 500;
        border-radius: var(--radius-md);
        padding: 0.6rem 1.25rem;
        border: 1px solid transparent;
        transition: all 150ms ease;
        box-shadow: var(--shadow-sm);
    }}

    .stButton > button[kind="primary"],
    .stButton > button[data-testid="baseButton-primary"] {{
        background-color: var(--color-primary);
        color: white;
    }}

    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="baseButton-primary"]:hover {{
        background-color: var(--color-primary-dark);
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
    }}

    .stButton > button[kind="secondary"],
    .stButton > button:not([kind="primary"]):not([data-testid="baseButton-primary"]) {{
        background-color: white;
        color: var(--color-primary);
        border: 1px solid var(--color-primary);
    }}

    .stButton > button[kind="secondary"]:hover,
    .stButton > button:not([kind="primary"]):not([data-testid="baseButton-primary"]):hover {{
        background-color: var(--color-accent-soft);
    }}

    /* Inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div {{
        border-radius: var(--radius-sm);
        border: 1px solid var(--color-border);
        font-family: var(--font-body);
        color: var(--color-text);
    }}

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: var(--color-primary);
        box-shadow: 0 0 0 3px rgba(0, 121, 194, 0.12);
        outline: none;
    }}

    /* Cards (st.container con border) */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        border-radius: var(--radius-md);
        border: 1px solid var(--color-border);
        box-shadow: var(--shadow-sm);
        padding: var(--space-md);
        background-color: var(--color-bg);
    }}

    /* Métricas */
    [data-testid="stMetricValue"] {{
        font-family: var(--font-display);
        color: var(--color-text);
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: var(--color-bg-soft);
        border-right: 1px solid var(--color-border);
    }}

    /* Alertas */
    [data-testid="stAlert"] {{
        border-radius: var(--radius-md);
        border-left-width: 4px;
    }}

    /* Progress bar */
    .stProgress > div > div > div > div {{
        background-color: var(--color-primary);
    }}

    /* Links */
    a {{
        color: var(--color-primary);
        text-decoration: none;
    }}
    a:hover {{
        color: var(--color-primary-dark);
        text-decoration: underline;
    }}

    /* Reduce el padding extra default del bloque principal */
    .block-container {{
        padding-top: var(--space-xl);
        padding-bottom: var(--space-2xl);
        max-width: 1200px;
    }}
    </style>
    """


def apply_smnyl_theme() -> None:
    """Inyecta el CSS de marca SMNYL en la página de Streamlit.

    Llamar una sola vez al inicio de cada página, justo después de
    `st.set_page_config(...)`.
    """
    st.markdown(_build_css(), unsafe_allow_html=True)
