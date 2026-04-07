"""Shared UI helpers for consistent styling across the Streamlit app."""

from __future__ import annotations

from html import escape
from typing import Iterable, Sequence

import streamlit as st


def apply_shared_styles() -> None:
    """Inject shared CSS once per page run."""
    if st.session_state.get("_shared_ui_styles_applied"):
        return

    st.session_state["_shared_ui_styles_applied"] = True
    st.markdown(
        """
        <style>
        :root {
            --ui-primary: #22c55e;
            --ui-dark-green: #14532d;
            --ui-mint: #86efac;
            --ui-bg: #0b1410;
            --ui-card: #111c16;
            --ui-border: #1f3b2b;
            --ui-text: #e8f5ec;
            --ui-muted: #9fb7a7;
        }

        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at top right, rgba(34, 197, 94, 0.10), transparent 28%),
                linear-gradient(180deg, #0b1410 0%, #0d1712 100%);
            color: var(--ui-text);
        }

        [data-testid="stHeader"] {
            background: rgba(11, 20, 16, 0.82);
            border-bottom: 1px solid rgba(31, 59, 43, 0.92);
            backdrop-filter: blur(12px);
        }

        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 2.5rem;
            max-width: 1400px;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0e1712 0%, #0b1410 100%);
            border-right: 1px solid var(--ui-border);
        }

        [data-testid="stSidebar"] .block-container {
            padding-top: 1.1rem;
        }

        .sidebar-brand {
            padding: 0.95rem 1rem 1rem;
            margin-bottom: 0.9rem;
            background: linear-gradient(180deg, rgba(17, 28, 22, 0.98), rgba(15, 27, 20, 0.95));
            border: 1px solid rgba(31, 59, 43, 0.95);
            border-radius: 18px;
        }

        .sidebar-brand p {
            margin: 0;
            color: var(--ui-mint);
            text-transform: uppercase;
            letter-spacing: 0.12em;
            font-size: 0.7rem;
            font-weight: 700;
        }

        .sidebar-brand h2 {
            margin: 0.35rem 0 0.2rem;
            color: var(--ui-text);
            font-size: 1.02rem;
        }

        .sidebar-brand span {
            color: var(--ui-muted);
            font-size: 0.86rem;
            line-height: 1.5;
        }

        [data-testid="stSidebarNav"] a {
            border-radius: 12px;
            padding-top: 0.35rem;
            padding-bottom: 0.35rem;
            margin-bottom: 0.2rem;
            border: 1px solid transparent;
        }

        [data-testid="stSidebarNav"] a:hover {
            background: rgba(17, 28, 22, 0.98);
            border-color: rgba(31, 59, 43, 0.95);
        }

        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: rgba(34, 197, 94, 0.12);
            border-color: rgba(34, 197, 94, 0.36);
        }

        h1, h2, h3, h4 {
            color: var(--ui-text);
            letter-spacing: -0.02em;
        }

        p, li, label {
            color: var(--ui-text);
        }

        .page-header {
            padding: 1.35rem 1.45rem;
            margin-bottom: 1.15rem;
            border-radius: 24px;
            background: linear-gradient(135deg, rgba(17, 28, 22, 0.98), rgba(14, 24, 18, 0.93));
            border: 1px solid rgba(31, 59, 43, 0.95);
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.18);
        }

        .page-header.hero {
            padding: 1.7rem 1.55rem;
            background: linear-gradient(135deg, rgba(17, 28, 22, 0.98), rgba(20, 83, 45, 0.24));
        }

        .page-eyebrow {
            margin: 0 0 0.45rem;
            color: var(--ui-mint);
            text-transform: uppercase;
            letter-spacing: 0.12em;
            font-size: 0.72rem;
            font-weight: 700;
        }

        .page-title {
            margin: 0;
            color: var(--ui-text);
            font-size: clamp(1.9rem, 3vw, 2.7rem);
            line-height: 1.1;
        }

        .page-caption {
            margin: 0.7rem 0 0;
            color: var(--ui-muted);
            max-width: 860px;
            font-size: 0.98rem;
            line-height: 1.7;
        }

        .hero-chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
            margin-top: 1rem;
        }

        .hero-chip {
            padding: 0.42rem 0.75rem;
            border-radius: 999px;
            background: rgba(9, 15, 12, 0.62);
            border: 1px solid rgba(34, 197, 94, 0.18);
            color: var(--ui-text);
            font-size: 0.9rem;
        }

        .section-heading {
            margin: 1.2rem 0 0.85rem;
        }

        .section-heading h2 {
            margin: 0;
            color: var(--ui-text);
            font-size: 1.15rem;
        }

        .section-heading p {
            margin: 0.35rem 0 0;
            color: var(--ui-muted);
            font-size: 0.95rem;
            line-height: 1.6;
        }

        .feature-grid,
        .workflow-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 0.9rem;
            margin: 0.5rem 0 1.3rem;
        }

        .feature-card,
        .workflow-step,
        .session-summary {
            background: linear-gradient(180deg, rgba(17, 28, 22, 0.97), rgba(12, 21, 16, 0.98));
            border: 1px solid rgba(31, 59, 43, 0.94);
            border-radius: 18px;
            padding: 1rem 1rem 0.95rem;
        }

        .feature-card h3,
        .workflow-step h3,
        .session-summary h3 {
            margin: 0 0 0.4rem;
            color: var(--ui-text);
            font-size: 1rem;
        }

        .feature-card p,
        .workflow-step p,
        .session-summary p {
            margin: 0;
            color: var(--ui-muted);
            font-size: 0.95rem;
            line-height: 1.6;
        }

        .step-number {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 1.8rem;
            height: 1.8rem;
            margin-bottom: 0.6rem;
            border-radius: 999px;
            background: rgba(34, 197, 94, 0.12);
            border: 1px solid rgba(34, 197, 94, 0.22);
            color: var(--ui-mint);
            font-weight: 700;
            font-size: 0.88rem;
        }

        .session-summary {
            margin-bottom: 1rem;
        }

        .session-meta {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(115px, 1fr));
            gap: 0.75rem;
            margin-top: 1rem;
        }

        .session-item {
            padding: 0.75rem 0.85rem;
            border-radius: 14px;
            background: rgba(9, 15, 12, 0.76);
            border: 1px solid rgba(34, 197, 94, 0.14);
        }

        .session-item span {
            display: block;
            margin-bottom: 0.25rem;
            color: var(--ui-muted);
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-size: 0.76rem;
        }

        .session-item strong {
            color: var(--ui-text);
            font-size: 1.04rem;
        }

        div[data-testid="stMetric"] {
            background: linear-gradient(180deg, rgba(17, 28, 22, 0.98), rgba(12, 21, 16, 0.98));
            border: 1px solid rgba(31, 59, 43, 0.94);
            border-radius: 18px;
            padding: 0.9rem 0.95rem;
            min-height: 6.3rem;
        }

        div[data-testid="stMetricLabel"] {
            color: var(--ui-muted);
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-size: 0.72rem;
        }

        div[data-testid="stMetricValue"] {
            color: var(--ui-text);
        }

        .stButton > button,
        .stDownloadButton > button {
            min-height: 2.75rem;
            border-radius: 12px;
            border: 1px solid rgba(34, 197, 94, 0.18);
            background: linear-gradient(180deg, rgba(24, 37, 29, 0.98), rgba(16, 28, 21, 0.98));
            color: var(--ui-text);
            box-shadow: none;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            border-color: rgba(34, 197, 94, 0.42);
            color: #ffffff;
        }

        .stButton > button[kind="primary"],
        .stDownloadButton > button[kind="primary"] {
            background: linear-gradient(180deg, #1a7d45 0%, #166534 100%);
            border-color: rgba(134, 239, 172, 0.34);
        }

        [data-baseweb="tab-list"] {
            gap: 0.5rem;
        }

        button[data-baseweb="tab"] {
            padding: 0.62rem 0.98rem;
            border-radius: 12px 12px 0 0;
            background: rgba(17, 28, 22, 0.92);
            border: 1px solid rgba(31, 59, 43, 0.92);
            color: var(--ui-muted);
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            background: rgba(34, 197, 94, 0.12);
            border-color: rgba(34, 197, 94, 0.34);
            color: var(--ui-text);
        }

        div[data-testid="stForm"] {
            padding: 0.95rem 1rem;
            margin-bottom: 1rem;
            background: rgba(17, 28, 22, 0.88);
            border: 1px solid rgba(31, 59, 43, 0.94);
            border-radius: 16px;
        }

        div[data-testid="stExpander"] {
            background: rgba(17, 28, 22, 0.8);
            border: 1px solid rgba(31, 59, 43, 0.94);
            border-radius: 16px;
        }

        div[data-testid="stDataFrame"],
        div[data-testid="stTable"] {
            background: rgba(17, 28, 22, 0.75);
            border: 1px solid rgba(31, 59, 43, 0.94);
            border-radius: 16px;
            padding: 0.25rem;
        }

        div[data-testid="stAlertContainer"] > div {
            background: rgba(17, 28, 22, 0.94);
            border: 1px solid rgba(31, 59, 43, 0.94);
            border-radius: 16px;
        }

        label,
        .stCaption {
            color: var(--ui-muted) !important;
        }

        .stTextInput > div > div,
        .stNumberInput > div > div,
        .stDateInput > div > div,
        .stTimeInput > div > div,
        .stTextArea textarea,
        .stSelectbox > div[data-baseweb="select"],
        .stMultiSelect > div[data-baseweb="select"] {
            background: rgba(12, 21, 16, 0.94);
            border-radius: 12px;
            border-color: rgba(31, 59, 43, 0.94);
        }

        hr {
            margin: 1.4rem 0;
            border-color: rgba(31, 59, 43, 0.9);
        }

        @media (max-width: 768px) {
            .page-header.hero {
                padding: 1.25rem 1.1rem;
            }

            .page-title {
                font-size: 1.8rem;
            }

            .block-container {
                padding-top: 1.1rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_brand() -> None:
    """Render a compact project label in the sidebar."""
    st.sidebar.markdown(
        """
        <div class="sidebar-brand">
            <p>Coursework Project</p>
            <h2>Data Wrangler Studio</h2>
            <span>Clean, profile, visualize, and export tabular datasets.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(
    title: str,
    caption: str,
    eyebrow: str = "Analytics Dashboard",
    *,
    hero: bool = False,
    chips: Sequence[str] | None = None,
) -> None:
    """Render a consistent page header block."""
    chip_markup = ""
    if chips:
        chip_markup = "<div class='hero-chip-row'>" + "".join(
            f"<span class='hero-chip'>{escape(chip)}</span>" for chip in chips
        ) + "</div>"

    container_class = "page-header hero" if hero else "page-header"
    st.markdown(
        f"""
        <section class="{container_class}">
            <p class="page-eyebrow">{escape(eyebrow)}</p>
            <h1 class="page-title">{escape(title)}</h1>
            <p class="page-caption">{escape(caption)}</p>
            {chip_markup}
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(title: str, caption: str | None = None) -> None:
    """Render a compact section heading with supporting text."""
    caption_markup = f"<p>{escape(caption)}</p>" if caption else ""
    st.markdown(
        f"""
        <div class="section-heading">
            <h2>{escape(title)}</h2>
            {caption_markup}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_feature_grid(cards: Iterable[tuple[str, str]]) -> None:
    """Render a responsive grid of feature cards."""
    card_markup = "".join(
        f"""
        <article class="feature-card">
            <h3>{escape(title)}</h3>
            <p>{escape(body)}</p>
        </article>
        """
        for title, body in cards
    )
    st.markdown(f"<section class='feature-grid'>{card_markup}</section>", unsafe_allow_html=True)


def render_workflow_grid(steps: Iterable[tuple[str, str]]) -> None:
    """Render the home-page workflow steps."""
    step_markup = "".join(
        f"""
        <article class="workflow-step">
            <div class="step-number">{index}</div>
            <h3>{escape(title)}</h3>
            <p>{escape(body)}</p>
        </article>
        """
        for index, (title, body) in enumerate(steps, start=1)
    )
    st.markdown(f"<section class='workflow-grid'>{step_markup}</section>", unsafe_allow_html=True)


def render_session_summary(
    *,
    dataset_name: str,
    source: str | None,
    rows: int,
    columns: int,
    steps: int,
) -> None:
    """Render a compact current-session summary card for the home page."""
    source_text = source.replace("_", " ").title() if source else "Unknown"
    st.markdown(
        f"""
        <section class="session-summary">
            <h3>Current Session</h3>
            <p>The app is already working with <strong>{escape(dataset_name)}</strong>. You can continue cleaning,
            visualize the current data, or export the latest version at any time.</p>
            <div class="session-meta">
                <div class="session-item">
                    <span>Source</span>
                    <strong>{escape(source_text)}</strong>
                </div>
                <div class="session-item">
                    <span>Rows</span>
                    <strong>{rows:,}</strong>
                </div>
                <div class="session-item">
                    <span>Columns</span>
                    <strong>{columns}</strong>
                </div>
                <div class="session-item">
                    <span>Saved Steps</span>
                    <strong>{steps}</strong>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
