# CyberPulse

**Early warning for small businesses.** CyberPulse reads a company's sign-in, file and email logs, spots
suspicious events, links the ones that belong to the same attack into one incident, scores how dangerous it
is, and explains it in plain English with what to do next.

DEXATHON 2026 · Team QUADRAX

## What you see

- **Product tour** (`core/tour.py`): eight slides that open on a visitor's first visit. Each one is a
  screenshot of the real app with numbered arrows on the buttons it explains. It can be reopened from
  **Product tour** at the top right of every page.
- **Live monitor** (`views/monitor.py`): plays a day of logs event by event. Pick *Normal day* or press
  **Run attack demo** to watch an account takeover unfold. The danger score climbs from Watch to
  Suspicious to Likely attack, the warning signs appear on a timeline, the story explains what happened,
  and the response buttons (pretend) appear once it is worth acting.
- **Evidence** (`views/evidence.py`): the raw events behind each incident, filtered by person,
  IP address or device, with a CSV download.
- **Score card** (`views/scorecard.py`): measured live against the answer key in the simulated data.

`app.py` is the entry point: it sets up the theme, the top navigation and the tour, then runs the page.

| Measured on the simulated company | Result |
|---|---|
| Attack events caught | 163 / 163 |
| Warning before the mass download starts | 15 min (meter red 4.8 min before) |
| False alarms (normal day and takeover day) | 0 |

These come from simulated data, so treat them as a demonstration, not a guarantee.

## Run it

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt      # macOS/Linux: .venv/bin/pip
.venv\Scripts\streamlit run app.py
```

Or double-click `run.bat` on Windows. Then open http://localhost:8501.

Run the tests (86 of them: every rule, linking and scoring, the whole demo story, the explanations, the
screens and the tour):

```bash
.venv\Scripts\python -m pytest
```

## How it works

```
core/simulator.py ──► core/schema.py ──► core/detection.py ──► core/correlation.py ──► core/explain.py
 a made-up company     the agreed log      10 rules raise        link signs into         plain-English
 and its log           format, checked     warning signs         incidents, score them   story
                                                                        │
                                              core/metrics.py ◄─────────┤
                                              score card vs answer key  ▼
                                                     app.py and views/ (core/ui.py, core/tour.py, core/response.py)
```

1. **Detection** reads events in time order, as they would arrive. Ten rules:

   | Rule | Fires when | MITRE ATT&CK |
   |---|---|---|
   | Password guessing | 5 wrong passwords on one account in 10 min | T1110.001 |
   | One IP trying many accounts | one IP fails on 4+ accounts in 30 min | T1110.003 |
   | Login after failed attempts | a successful sign-in straight after those failures | T1078 |
   | Login from new device or country | a device or country the person has never used | T1078 |
   | Made admin | admin rights granted; Critical if self-granted, by a non-admin or out of hours | T1098 |
   | Mass file access | far more files in 30 min than the person's usual pace | T1213 |
   | Login at an odd hour | outside the person's working hours, with an hour's grace | T1078 |
   | Mail forwarded outside | a forwarding rule to an address outside the company | T1114.003 |
   | Big upload | 500 MB+ uploaded in an hour | T1567 |
   | Mass file renaming | 100+ files renamed in 5 min, the mark of ransomware | T1486 |

2. **Linking** joins warning signs that share a person, IP address or device within 3 hours. The office's
   shared IP is ignored, since everyone in the office uses it.
3. **Scoring**: the most severe sign gives the base (Low 5, Medium 15, High 25, Critical 40), plus 10 for
   each other kind of sign, capped at 100. 1–39 is *Watch*, 40–74 *Suspicious*, 75+ *Likely attack*.
4. **Explaining**: each kind of incident (account takeover, ransomware, email forwarding and so on) gets
   what happened, why it matters and what to do now.

## Who owns what

| Person | Part | Files |
|---|---|---|
| Sreevathson (lead) | Backend: log format, rules, linking, scoring | `core/schema.py`, `core/detection.py`, `core/correlation.py` |
| Harish | Simulated company and score card numbers | `core/simulator.py`, `core/metrics.py`, `data/` |
| Aswin | Screens and product tour | `app.py`, `views/`, `core/ui.py`, `core/tour.py`, `core/response.py`, `assets/`, `.streamlit/` |
| Keerthana | Explanations, tests and presentation | `core/explain.py`, `tests/` |

## Safe data only

Everything is made up: IP addresses come only from the 203.0.113.x documentation range and emails end in
`.example`. The response buttons change nothing real.

## Design

Light theme with one accent: ink text and buttons, Geist and Geist Mono fonts (`.streamlit/config.toml`).
Status colours are kept for status only (green Clear, amber Watch, orange Suspicious, red Likely attack),
and each status always comes with an icon and a label. The shared styles live in `core/ui.py`.

The tour screenshots in `assets/tour/` are made from the running app. After a screen changes, remake them:
run the app on port 8601, run `tools/tour_shots.js` with Playwright (the script says how), then
`.venv\Scripts\python tools/tour_webp.py`.

## Hosting

`asgi.py` wraps the Streamlit app as an ASGI app (`st.App`), which is how it runs on Vercel
(`pyproject.toml` points Vercel at it). Locally, keep using `streamlit run app.py`.
