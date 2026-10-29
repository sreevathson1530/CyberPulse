"""Shared screen pieces: theme, colours, page header, cached data and
playback state.

Owner: Aswin Kumaran (frontend). Every page imports this, so the colours and
the playback position are the same everywhere.
"""

import base64
from datetime import datetime, time, timedelta
from html import escape
from urllib.parse import quote

import streamlit as st
import streamlit.components.v1 as components

from core.correlation import analyze
from core.metrics import score_card as compute_score_card
from core.response import reset_response_states
from core.schema import to_frame
from core.simulator import DAY, build_scenario, employee_profiles

SCENARIOS = {"Normal day": "normal_day", "Account takeover": "account_takeover"}
DEMO_START = datetime.combine(DAY, time(13, 30))  # half the day played, just before the attack

# Ink and surface colours, shared with the charts.
INK, INK_2, INK_3 = "#16181D", "#55534E", "#8A8883"
SURFACE, BORDER, GRID = "#FFFFFF", "#E3E2DE", "#EFEEEB"
FONT = "Geist, system-ui, sans-serif"

# Status colours: (mark colour, soft tint, readable text shade). Each status
# also has an icon and a label, so colour is never the only signal.
STATUS = {
    "good": ("#0CA30C", "#E8F5E8", "#0B6B0B"),
    "warning": ("#FAB219", "#FEF5E1", "#8A5600"),
    "serious": ("#EC835A", "#FDEEE7", "#A8461F"),
    "critical": ("#D03B3B", "#FAE9E9", "#A32626"),
    "neutral": ("#8A8883", "#F1F0ED", "#55534E"),
}
LEVEL_STATUS = {"Clear": "good", "Watch": "warning", "Suspicious": "serious", "Likely attack": "critical"}
SEVERITY_STATUS = {"Low": "neutral", "Medium": "warning", "High": "serious", "Critical": "critical"}
LEVEL_COLORS = {level: STATUS[status][0] for level, status in LEVEL_STATUS.items()}
SEVERITY_COLORS = {severity: STATUS[status][0] for severity, status in SEVERITY_STATUS.items()}
SEVERITY_RANK = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}

_ICON_PATHS = {
    "good": '<circle cx="8" cy="8" r="6.25"/><path d="M5.3 8.2l1.8 1.8 3.6-3.8"/>',
    "warning": '<path d="M1.6 8S4 3.6 8 3.6 14.4 8 14.4 8 12 12.4 8 12.4 1.6 8 1.6 8z"/><circle cx="8" cy="8" r="1.9"/>',
    "serious": '<path d="M8 2.1l6.3 11.1H1.7z"/><path d="M8 6.4v3"/><path d="M8 11.3v.1"/>',
    "critical": '<path d="M5.4 1.8h5.2l3.6 3.6v5.2l-3.6 3.6H5.4l-3.6-3.6V5.4z"/><path d="M8 4.9v3.6"/><path d="M8 10.9v.1"/>',
    "neutral": '<circle cx="8" cy="8" r="6.25"/><path d="M5.5 8h5"/>',
}

LOGO_MARK = ("<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 32 32'>"
             "<rect width='32' height='32' rx='8' fill='#16181D'/>"
             "<path d='M6 17h5l2.6-6.5 4.6 12 3-8.5 1.8 3H26' fill='none' stroke='#fff' stroke-width='2.2' "
             "stroke-linecap='round' stroke-linejoin='round'/></svg>")
LOGO_WORDMARK = ("<svg xmlns='http://www.w3.org/2000/svg' width='150' height='32' viewBox='0 0 150 32'>"
                 "<rect width='32' height='32' rx='8' fill='#16181D'/>"
                 "<path d='M6 17h5l2.6-6.5 4.6 12 3-8.5 1.8 3H26' fill='none' stroke='#fff' stroke-width='2.2' "
                 "stroke-linecap='round' stroke-linejoin='round'/>"
                 "<text x='42' y='22.5' font-family='Geist, Segoe UI, system-ui, sans-serif' font-size='18' "
                 "font-weight='600' letter-spacing='-0.4' fill='#16181D'>CyberPulse</text></svg>")


def svg_url(svg):
    return "data:image/svg+xml;utf8," + quote(svg)


def _icon_rule(name, paths):
    svg = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='none' stroke='black' "
           f"stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'>{paths}</svg>")
    return f'.cp-i-{name} {{ --icon: url("{svg_url(svg)}"); }}\n'


# st.html strips inline SVG, so the status icons are CSS masks painted in the
# text colour.
ICON_CSS = "".join(_icon_rule(name, paths) for name, paths in _ICON_PATHS.items())


CSS = """
<style>
:root {
    --cp-bg: #F7F7F5; --cp-surface: #FFFFFF; --cp-sunken: #F1F0ED;
    --cp-border: #E3E2DE; --cp-border-soft: #ECEBE7;
    --cp-ink: #16181D; --cp-ink-2: #55534E; --cp-ink-3: #8A8883;
    --cp-accent: #2F5FD0;
    --cp-mono: "Geist Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    --cp-shadow: 0 1px 2px rgba(22, 24, 29, 0.04), 0 1px 3px rgba(22, 24, 29, 0.03);
}
.cp-s-good { --s: #0CA30C; --s-tint: #E8F5E8; --s-text: #0B6B0B; }
.cp-s-warning { --s: #FAB219; --s-tint: #FEF5E1; --s-text: #8A5600; }
.cp-s-serious { --s: #EC835A; --s-tint: #FDEEE7; --s-text: #A8461F; }
.cp-s-critical { --s: #D03B3B; --s-tint: #FAE9E9; --s-text: #A32626; }
.cp-s-neutral { --s: #8A8883; --s-tint: #F1F0ED; --s-text: #55534E; }

/* App chrome */
[data-testid="stHeader"] { background: rgba(255, 255, 255, 0.92); backdrop-filter: blur(8px);
                           border-bottom: 1px solid var(--cp-border); }
[data-testid="stStatusWidget"] { display: none; }
[data-testid="stMainBlockContainer"] { max-width: 1240px; padding: 5.2rem 2rem 4rem; }
[data-stale="true"] { opacity: 1 !important; }
[data-testid="stDialog"] [role="dialog"] { background: var(--cp-surface); }
button { transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease, transform 0.08s ease; }
button:active:not(:disabled) { transform: translateY(1px); }

/* Page header */
.cp-page-head h1 { font-size: 1.65rem; font-weight: 600; letter-spacing: -0.025em; line-height: 1.2;
                   margin: 0; padding: 0; color: var(--cp-ink); }
.cp-page-head p { margin: 0.35rem 0 0; color: var(--cp-ink-2); font-size: 0.93rem; max-width: 64ch;
                  text-wrap: pretty; }

/* Cards: plain HTML ones, and Streamlit containers keyed card_* */
.cp-card, [class*="st-key-card_"], .st-key-toolbar {
    background: var(--cp-surface); border: 1px solid var(--cp-border); border-radius: 12px;
    box-shadow: var(--cp-shadow); box-sizing: border-box;
}
.cp-card, [class*="st-key-card_"] { padding: 1rem 1.1rem; }
.st-key-toolbar { padding: 0.55rem 0.6rem; }
.cp-card-head { display: flex; align-items: center; justify-content: space-between; gap: 0.6rem; min-height: 1.6rem; }
.cp-card-title { font-size: 0.86rem; font-weight: 500; color: var(--cp-ink-2); margin: 0; }
.cp-card-meta { font-size: 0.8rem; color: var(--cp-ink-3); }
.cp-kpi, .st-key-card_response { min-height: 14rem; }

/* Status badge: tint, icon and label */
.cp-badge { display: inline-flex; align-items: center; gap: 0.35rem; padding: 0.2rem 0.55rem 0.2rem 0.45rem;
            border-radius: 6px; font-size: 0.8rem; font-weight: 500; line-height: 1.25; white-space: nowrap;
            background: var(--s-tint); color: var(--s-text); }
.cp-icon { display: inline-block; width: 14px; height: 14px; flex: none; background: currentColor;
           -webkit-mask: var(--icon) center / contain no-repeat; mask: var(--icon) center / contain no-repeat; }

/* Danger score */
.cp-score { display: flex; align-items: baseline; gap: 0.3rem; margin: 0.55rem 0 0.9rem; }
.cp-score b { font-size: 3.1rem; font-weight: 600; letter-spacing: -0.045em; line-height: 1; color: var(--cp-ink);
              font-variant-numeric: tabular-nums; }
.cp-score span { font-size: 1rem; color: var(--cp-ink-3); }
.cp-gauge { position: relative; height: 6px; border-radius: 3px; background: var(--cp-sunken); }
.cp-gauge i { position: absolute; inset: 0 auto 0 0; border-radius: 3px; background: var(--s); }
.cp-gauge u { position: absolute; top: -3px; width: 1.5px; height: 12px; background: #FFFFFF; }
.cp-gauge u::after { content: ""; position: absolute; inset: 3px 0; background: var(--cp-ink-3); }
.cp-scale { position: relative; height: 1rem; margin-top: 0.35rem; font-size: 0.72rem; color: var(--cp-ink-3);
            font-variant-numeric: tabular-nums; }
.cp-scale span { position: absolute; transform: translateX(-50%); }
.cp-scale span:first-child { transform: none; }
.cp-scale span:last-child { transform: translateX(-100%); }
.cp-note { margin: 0.7rem 0 0.15rem; font-size: 0.9rem; color: var(--cp-ink); text-wrap: pretty; }
.cp-meta { font-size: 0.8rem; color: var(--cp-ink-3); }

/* Log clock */
.cp-clock { font-family: var(--cp-mono); font-size: 2.6rem; font-weight: 500; letter-spacing: -0.04em; line-height: 1;
            color: var(--cp-ink); margin: 0.55rem 0 0.9rem; font-variant-numeric: tabular-nums; }
.cp-progress { height: 6px; border-radius: 3px; background: var(--cp-sunken); overflow: hidden; }
.cp-progress i { display: block; height: 100%; background: var(--cp-accent); border-radius: 3px; }
.cp-live { display: inline-flex; align-items: center; gap: 0.4rem; font-size: 0.8rem; color: var(--cp-ink-2); }
.cp-dot { width: 7px; height: 7px; border-radius: 50%; background: #B9B8B3; }
.cp-live.on .cp-dot { background: #0CA30C; animation: cp-pulse 1s ease-out infinite; }
@keyframes cp-pulse { from { box-shadow: 0 0 0 0 rgba(12, 163, 12, 0.45); } to { box-shadow: 0 0 0 6px rgba(12, 163, 12, 0); } }

/* Story */
.cp-story h3 { font-size: 1.05rem; font-weight: 600; letter-spacing: -0.01em; margin: 0.7rem 0 0; padding: 0; }
.cp-story dl { margin: 0; padding: 0; }
.cp-story dt { margin-top: 0.95rem; font-size: 0.8rem; font-weight: 500; color: var(--cp-ink-3); }
.cp-story dd { margin: 0.2rem 0 0; font-size: 0.92rem; line-height: 1.55; color: var(--cp-ink); max-width: 68ch;
               text-wrap: pretty; }

/* Live feed */
.cp-feed { height: 372px; overflow-y: auto; margin: 0.6rem -0.35rem 0; padding-right: 0.2rem;
           font-family: var(--cp-mono); font-size: 0.76rem; }
.cp-row { display: grid; grid-template-columns: 4.4rem 1fr; gap: 0.6rem; padding: 0.42rem 0.55rem;
          border-left: 3px solid transparent; border-radius: 6px; color: var(--cp-ink-2); word-break: break-word; }
.cp-row + .cp-row { margin-top: 2px; }
.cp-row time { color: var(--cp-ink-3); }
.cp-row b { color: var(--cp-ink); font-weight: 500; }
.cp-row small { display: block; margin-top: 0.1rem; font-size: 0.7rem; color: var(--cp-ink-3); }
.cp-row[class*="cp-s-"] { background: var(--s-tint); border-left-color: var(--s); }

/* Empty state */
.cp-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 0.3rem;
            padding: 2.4rem 1rem; text-align: center; font-size: 0.9rem; color: var(--cp-ink-3); }
.cp-empty strong { color: var(--cp-ink); font-weight: 500; }

/* Stat tiles */
.cp-stat-label { font-size: 0.84rem; color: var(--cp-ink-2); }
.cp-stat-value { margin: 0.35rem 0 0.35rem; font-size: 1.9rem; font-weight: 600; letter-spacing: -0.035em; line-height: 1.1;
                 color: var(--cp-ink); font-variant-numeric: tabular-nums; white-space: nowrap; }
.cp-stat-desc { font-size: 0.82rem; line-height: 1.45; color: var(--cp-ink-3); text-wrap: pretty; }
.cp-footnote { font-size: 0.8rem; color: var(--cp-ink-3); max-width: 90ch; text-wrap: pretty; }

/* Tour */
.cp-tour { display: grid; grid-template-columns: minmax(0, 1.85fr) minmax(0, 1fr); gap: 1.6rem; align-items: start; }
.cp-tour-shot { display: block; width: 100%; height: auto; aspect-ratio: 1040 / 600; border-radius: 10px;
                border: 1px solid var(--cp-border); background: var(--cp-bg); }
.cp-tour-step { margin: 0.1rem 0 0.3rem; font-size: 0.8rem; font-weight: 500; color: var(--cp-ink-3);
                font-variant-numeric: tabular-nums; }
.cp-tour h2 { margin: 0; padding: 0; font-size: 1.35rem; font-weight: 600; letter-spacing: -0.02em; line-height: 1.25; }
.cp-tour p { margin: 0.45rem 0 0; font-size: 0.95rem; line-height: 1.55; color: var(--cp-ink-2); max-width: 70ch;
             text-wrap: pretty; }
.cp-tour ul { margin: 0.6rem 0 0; padding: 0; list-style: none; display: grid; gap: 0.35rem; }
.cp-tour li { display: grid; grid-template-columns: 1.35rem 1fr; gap: 0.5rem; font-size: 0.9rem; line-height: 1.45;
              color: var(--cp-ink); }
.cp-tour li span { display: inline-grid; place-items: center; width: 1.35rem; height: 1.35rem; border-radius: 50%;
                   background: var(--cp-accent); color: #FFFFFF; font-size: 0.72rem; font-weight: 600; }
.cp-dots { display: flex; gap: 6px; align-items: center; }
.cp-dots i { width: 6px; height: 6px; border-radius: 3px; background: #D9D8D3; transition: width 0.2s ease; }
.cp-dots i.on { width: 18px; background: var(--cp-ink); }

@media (max-width: 900px) {
    .cp-tour { grid-template-columns: minmax(0, 1fr); gap: 1rem; }
}
@media (max-width: 640px) {
    [data-testid="stMainBlockContainer"] { padding: 4.6rem 1rem 3rem; }
    .cp-page-head h1 { font-size: 1.4rem; }
    .cp-score b { font-size: 2.5rem; }
    .cp-clock { font-size: 2.1rem; }
    .cp-feed { height: 300px; }
    .cp-kpi, .st-key-card_response { min-height: 0; }
}
@media (prefers-reduced-motion: reduce) {
    .cp-live.on .cp-dot { animation: none; }
    button { transition: none; }
}
</style>
"""


def apply_theme():
    st.markdown(CSS.replace("</style>", ICON_CSS + "</style>"), unsafe_allow_html=True)


def icon(status):
    return f"<i class='cp-icon cp-i-{status}' aria-hidden='true'></i>"


def badge(label, status):
    return f"<span class='cp-badge cp-s-{status}'>{icon(status)}{escape(label)}</span>"


def level_badge(level):
    return badge(level, LEVEL_STATUS[level])


def page_header(title, description):
    """Page title and one line about it, with the product tour on the right."""
    with st.container(horizontal=True, vertical_alignment="bottom", gap="medium"):
        st.html(f"<div class='cp-page-head'><h1>{escape(title)}</h1><p>{description}</p></div>")
        st.button("Product tour", icon=":material/tour:", type="tertiary", on_click=open_tour, key="open_tour")


def empty_state(title, text):
    st.html(f"<div class='cp-empty'><strong>{escape(title)}</strong><span>{escape(text)}</span></div>")


def style_figure(figure, height):
    """Light chart styling that matches the page: white surface, recessive
    grid, Geist text in ink colours."""
    figure.update_layout(
        height=height, paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
        font=dict(family=FONT, size=12, color=INK_2),
        hoverlabel=dict(bgcolor=SURFACE, bordercolor=BORDER, font=dict(family=FONT, size=12, color=INK)),
    )
    figure.update_xaxes(gridcolor=GRID, linecolor=BORDER, zeroline=False, tickfont=dict(color=INK_3))
    figure.update_yaxes(gridcolor=GRID, linecolor=BORDER, zeroline=False, tickfont=dict(color=INK_3))
    return figure


def show_chart(figure):
    st.plotly_chart(figure, width="stretch", theme=None, config={"displayModeBar": False})


def download_csv(table, file_name, label):
    """A download button for a table, with the file inside the page.

    st.download_button fetches the file from the server's memory in a second
    request. On Vercel that request can reach a different server instance,
    which answers 404, so the file travels with the page instead."""
    data = base64.b64encode(table.to_csv(index=False).encode("utf-8")).decode()
    components.html(f"""
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Geist:wght@500&display=swap">
        <style>
          body {{ margin: 0; display: flex; justify-content: flex-end; }}
          a {{ display: inline-flex; align-items: center; gap: 0.45rem; padding: 0.42rem 0.8rem; border-radius: 8px;
               text-decoration: none; border: 1px solid {BORDER}; background: {SURFACE}; color: {INK};
               font: 500 14px Geist, system-ui, sans-serif; transition: background-color 0.15s ease; }}
          a:hover {{ background: #F1F0ED; }}
          a:active {{ transform: translateY(1px); }}
          a:focus-visible {{ outline: 2px solid #2F5FD0; outline-offset: 2px; }}
          svg {{ width: 16px; height: 16px; fill: none; stroke: currentColor; stroke-width: 1.6;
                 stroke-linecap: round; stroke-linejoin: round; }}
        </style>
        <a download="{escape(file_name)}" href="data:text/csv;base64,{data}">
          <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 2.5v8M4.8 7.6L8 10.8l3.2-3.2M3 13.5h10"/></svg>
          {escape(label)}</a>""", height=42)


def short(email):
    return email.split("@")[0]


# Data

@st.cache_data(show_spinner=False)
def load_events(scenario):
    """All events of a scenario ("Normal day" or "Account takeover"), oldest first."""
    return to_frame(build_scenario(SCENARIOS[scenario]))


@st.cache_resource(show_spinner=False)
def load_profiles():
    return employee_profiles()


@st.cache_data(show_spinner=False, max_entries=600)
def incidents_upto(scenario, count):
    """Incidents found in the first `count` events, most dangerous first."""
    return analyze(load_events(scenario).iloc[:count], load_profiles())


@st.cache_data(show_spinner=False)
def score_card(scenario):
    return compute_score_card(load_events(scenario), load_profiles())


# Playback state, shared by every page

def init_state():
    if "scenario" not in st.session_state:
        set_scenario("Normal day", DEMO_START)
    st.session_state.setdefault("playing", False)
    st.session_state.setdefault("speed", "1x")


def set_scenario(scenario, clock=None):
    events = load_events(scenario)
    st.session_state.scenario = scenario
    st.session_state.clock = clock if clock is not None else events["time"].iloc[0] - timedelta(seconds=1)
    st.session_state.playing = False
    reset_response_states()


def shown_count():
    """How many events have been played so far."""
    events = load_events(st.session_state.scenario)
    return int(events["time"].searchsorted(st.session_state.clock, side="right"))


def advance(minutes):
    """Move the playback clock forward. Returns True at the end of the log."""
    last = load_events(st.session_state.scenario)["time"].iloc[-1]
    st.session_state.clock = min(st.session_state.clock + timedelta(minutes=minutes), last)
    if st.session_state.clock >= last:
        st.session_state.playing = False
        return True
    return False


# Button callbacks

def play():
    if shown_count() >= len(load_events(st.session_state.scenario)):
        set_scenario(st.session_state.scenario)  # at the end: start the day again
    st.session_state.playing = True


def pause():
    st.session_state.playing = False


def toggle_play():
    pause() if st.session_state.playing else play()


def next_event():
    st.session_state.playing = False
    events = load_events(st.session_state.scenario)
    later = events["time"][events["time"] > st.session_state.clock]
    if not later.empty:
        st.session_state.clock = later.iloc[0]


def reset():
    set_scenario(st.session_state.scenario)


def launch_attack():
    """Switch to the takeover story just before it starts, and play it."""
    events = load_events("Account takeover")
    first_attack = events.loc[events["label"] == "attack", "time"].min()
    set_scenario("Account takeover", first_attack - timedelta(minutes=10))
    st.session_state.speed = "1x"
    st.session_state.playing = True


def change_scenario():
    set_scenario(st.session_state.scenario_choice, DEMO_START)


def open_tour():
    st.session_state.tour_step = 0
    st.session_state.tour_open = True
