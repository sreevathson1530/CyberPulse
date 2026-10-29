"""The screens run without errors, the demo's buttons do what they say, and
the product tour opens on a first visit and steps through its slides."""

from datetime import timedelta
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from core.tour import SHOTS, SLIDES

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def open_app(tour_seen=True):
    at = AppTest.from_file(APP, default_timeout=30)
    if tour_seen:
        at.session_state["tour_done"] = True
    at.run()
    assert not at.exception
    return at


@pytest.fixture
def app():
    return open_app()


def button(at, text):
    return next(b for b in at.button if b.label == text)


def labels(at):
    return [b.label for b in at.button]


def test_monitor_opens_on_the_normal_day(app):
    assert app.session_state["scenario"] == "Normal day"
    assert "Skip tour" not in labels(app)
    assert {"Play", "Next event", "Reset", "Run attack demo"} <= set(labels(app))


def test_run_attack_demo_plays_the_takeover(app):
    button(app, "Run attack demo").click().run()
    assert app.session_state["scenario"] == "Account takeover"
    assert app.session_state["playing"]
    assert "Pause" in labels(app)


def test_response_buttons_appear_once_the_attack_is_red(app):
    button(app, "Run attack demo").click().run()
    app.session_state["clock"] = app.session_state["clock"] + timedelta(minutes=45)
    button(app, "Pause").click().run()
    assert not app.exception
    button(app, "Lock account").click().run()
    assert "Account locked" in labels(app)


def test_next_event_and_reset(app):
    start = app.session_state["clock"]
    button(app, "Next event").click().run()
    assert app.session_state["clock"] > start
    button(app, "Reset").click().run()
    assert app.session_state["clock"] < start


@pytest.mark.parametrize("page", ["views/evidence.py", "views/scorecard.py"])
def test_other_pages_open(app, page):
    app.switch_page(page).run()
    assert not app.exception
    assert "Product tour" in labels(app)


def test_tour_opens_on_the_first_visit():
    at = open_app(tour_seen=False)
    assert {"Skip tour", "Next"} <= set(labels(at))
    assert "Back" not in labels(at)


def test_tour_steps_forward_and_back_then_skips():
    at = open_app(tour_seen=False)
    button(at, "Next").click().run()
    assert at.session_state["tour_step"] == 1
    button(at, "Back").click().run()
    assert at.session_state["tour_step"] == 0
    button(at, "Skip tour").click().run()
    assert at.session_state["tour_done"]
    assert "Skip tour" not in labels(at)


def test_tour_ends_by_starting_the_demo():
    at = open_app(tour_seen=False)
    at.session_state["tour_step"] = len(SLIDES) - 1
    at.run()
    assert "Next" not in labels(at)
    button(at, "Start the demo").click().run()
    assert not at.exception
    assert at.session_state["tour_done"]
    assert at.session_state["scenario"] == "Account takeover"
    assert at.session_state["playing"]


def test_product_tour_button_reopens_the_tour(app):
    button(app, "Product tour").click().run()
    assert "Skip tour" in labels(app)


def test_every_slide_has_a_screenshot():
    for slide in SLIDES:
        assert (SHOTS / f"{slide['shot']}.webp").exists(), slide["shot"]
    assert 5 <= len(SLIDES) <= 10
