"""The product tour: eight slides that open on a visitor's first visit and
show, with arrows on real screenshots, what each part of CyberPulse does.

The screenshots live in assets/tour/ and are made with tools/tour_shots.js.
They travel inside the page as data URIs: on Vercel, files served from
Streamlit's media endpoint can 404 (see ui.download_csv).
"""

import base64
from functools import lru_cache
from html import escape
from pathlib import Path

import streamlit as st

from core import ui

SHOTS = Path(__file__).resolve().parents[1] / "assets" / "tour"
COOKIE = "cp_tour"  # set once the tour is closed, so it opens only on the first visit

SLIDES = [
    dict(shot="1-welcome", title="Welcome to CyberPulse",
         text="CyberPulse reads a company's sign-in, email and file logs, spots warning signs, links them into one "
              "incident and explains it in plain English. This demo uses a made-up company of 8 people, so "
              "nothing you click here is real.",
         points=["The controls: play the day, or run the attack demo",
                 "The danger score, the log clock and the response buttons",
                 "The incident timeline, its story and the live feed"]),
    dict(shot="2-run-attack", title="Start here: run the attack demo",
         text="One click plays a real-looking account takeover, starting 10 minutes before the attacker signs in. "
              "Watch the danger score climb from Watch to Likely attack.",
         points=["Run attack demo: jumps to the takeover and starts playing"]),
    dict(shot="3-playback", title="Control the playback",
         text="The log plays like a video: at 1×, every second plays two minutes of company activity.",
         points=["Scenario: a quiet normal day, or the account takeover",
                 "Play or pause the log",
                 "Next event: step forward one event at a time",
                 "Reset: go back to the start of the day",
                 "Speed: play 2× or 4× faster"]),
    dict(shot="4-score", title="Read the danger score",
         text="Every incident gets a score from 0 to 100. The most dangerous one sets the score you see.",
         points=["The score, out of 100",
                 "The level: Watch below 40, Suspicious from 40, Likely attack from 75",
                 "The log clock: which minute of the day is playing"]),
    dict(shot="5-response", title="Respond in one click",
         text="Once an incident reaches Suspicious, response buttons appear for the accounts involved. In this "
              "demo they are pretend: nothing real changes.",
         points=["Lock the account",
                 "Sign the attacker out of every session",
                 "Remove the email forwarding rule the attacker added"]),
    dict(shot="6-timeline", title="See how the attack unfolded",
         text="Each dot is one warning sign, placed at the minute it happened and coloured by how serious it is. "
              "Hover a dot for the details.",
         points=["A warning sign, labelled with what happened",
                 "The severity colours: Low, Medium, High and Critical"]),
    dict(shot="7-story", title="Understand it in plain English",
         text="No security jargon: CyberPulse says what happened, why it matters and what to do now. The live "
              "feed shows every event as it arrives.",
         points=["The story: what happened, why it matters, what to do now",
                 "The live feed: tinted rows belong to an incident"]),
    dict(shot="8-pages", title="Check the evidence",
         text="Two more pages back up every claim with data, and the tour is always one click away.",
         points=["Evidence: every raw event behind an incident, with filters and a CSV download",
                 "Score card: how many attack events were caught, and how early",
                 "Product tour: open this tour again"]),
]


def should_open():
    """Open on the first visit, and whenever the visitor asks for it."""
    state = st.session_state
    if state.get("tour_open"):
        return True
    return not state.get("tour_done") and st.context.cookies.get(COOKIE) != "seen"


def close():
    st.session_state.tour_done = True
    st.session_state.tour_open = False
    st.session_state.tour_step = 0


def go(step):
    st.session_state.tour_step = max(0, min(len(SLIDES) - 1, st.session_state.tour_step + step))


@lru_cache(maxsize=None)
def shot_url(name):
    return "data:image/webp;base64," + base64.b64encode((SHOTS / f"{name}.webp").read_bytes()).decode()


@st.dialog("Quick tour", width="large", on_dismiss=close)
def show():
    step = st.session_state.setdefault("tour_step", 0)
    slide = SLIDES[step]
    last = step == len(SLIDES) - 1
    picture = (f"<img class='cp-tour-shot' src='{shot_url(slide['shot'])}' alt='Screenshot: {escape(slide['title'])}, "
               f"with numbered arrows on the parts described next to it'>")
    points = "".join(f"<li><span>{number}</span>{escape(point)}</li>" for number, point in enumerate(slide["points"], 1))
    st.html(f"""
        <div class='cp-tour'>
          {picture}
          <div>
            <div class='cp-tour-step'>Step {step + 1} of {len(SLIDES)}</div>
            <h2>{escape(slide['title'])}</h2>
            <p>{escape(slide['text'])}</p>
            <ul>{points}</ul>
          </div>
        </div>""")

    with st.container(horizontal=True, vertical_alignment="center", gap="small"):
        dots = "".join(f"<i class='{'on' if i == step else ''}'></i>" for i in range(len(SLIDES)))
        st.html(f"<div class='cp-dots' role='img' aria-label='Step {step + 1} of {len(SLIDES)}'>{dots}</div>",
                width="content")
        st.space("stretch")
        if not last and st.button("Skip tour", type="tertiary", key="tour_skip"):
            close()
            st.rerun()
        if step:
            st.button("Back", key="tour_back", on_click=go, args=(-1,))
        if not last:
            st.button("Next", type="primary", icon=":material/arrow_forward:", icon_position="right",
                      key="tour_next", on_click=go, args=(1,))
        elif st.button("Start the demo", type="primary", icon=":material/bolt:", key="tour_start"):
            close()
            ui.launch_attack()
            st.switch_page("views/monitor.py")


def remember_seen():
    """Set a cookie once the tour is closed, so a returning visitor goes
    straight to the monitor."""
    state = st.session_state
    if state.get("tour_done") and not state.get("tour_cookie_set"):
        st.html(f"<script>document.cookie = '{COOKIE}=seen; path=/; max-age=31536000; SameSite=Lax';</script>",
                unsafe_allow_javascript=True)
        state.tour_cookie_set = True
