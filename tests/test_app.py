"""The screens run without errors, and the demo's buttons do what they say."""

from datetime import timedelta
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


@pytest.fixture
def app():
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    assert not at.exception
    return at


def button(at, text):
    return next(b for b in at.button if text in b.label)


def test_dashboard_opens_on_the_normal_day(app):
    assert app.session_state["scenario"] == "Normal day"
    assert "Danger meter" in "".join(m.value for m in app.markdown)


def test_launch_attack_plays_the_takeover(app):
    button(app, "Launch attack").click().run()
    assert app.session_state["scenario"] == "Account takeover"
    assert app.session_state["playing"]


def test_response_buttons_appear_once_the_attack_is_red(app):
    button(app, "Launch attack").click().run()
    app.session_state["clock"] = app.session_state["clock"] + timedelta(minutes=45)
    button(app, "Pause").click().run()
    assert not app.exception
    button(app, "Lock account").click().run()
    assert any("Account locked" in b.label for b in app.button)


def test_next_event_and_reset(app):
    start = app.session_state["clock"]
    button(app, "Next event").click().run()
    assert app.session_state["clock"] > start
    button(app, "Reset").click().run()
    assert app.session_state["clock"] < start


@pytest.mark.parametrize("page", ["pages/1_Incident_Details.py", "pages/2_Scorecard.py"])
def test_other_pages_open(app, page):
    app.switch_page(page).run()
    assert not app.exception

