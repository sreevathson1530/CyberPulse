# CyberPulse

An early-warning console for small businesses. It reads a company's sign-in, file and email logs, links suspicious events into one incident, gives it a danger score and explains it in plain English.

Team QUADRAX, DEXATHON 2026.

## Run it

Needs Python 3.11 or newer.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Mac or Linux
pip install -r requirements.txt
streamlit run app.py
```

Run the tests with `pytest`.

## Who owns what

| Files | Owner | Branch |
| --- | --- | --- |
| `core/schema.py`, `core/detection.py`, `core/correlation.py` | Sreevathson | `backend` |
| `app.py`, `pages/`, `core/response.py` | Aswin Kumaran | `frontend` |
| `core/simulator.py`, `core/metrics.py`, `data/scenarios/` | Harish Karthick | `data` |
| `tests/`, `core/explain.py` | Keerthana | `testing` |

Work on your own branch and open a pull request into `main`. Only the team lead merges.
