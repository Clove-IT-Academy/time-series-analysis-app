from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_full_example_and_invalidation():
    app = AppTest.from_file(str(Path(__file__).parents[1] / "app.py"), default_timeout=40).run()
    assert not app.exception
    app.checkbox(key="confirm").check().run()
    assert not app.exception
    next(b for b in app.button if b.label == "Compare and forecast").click().run(timeout=60)
    assert not app.exception
    response = app.session_state["response"]
    assert response.forecast_rows, response.message
    assert app.dataframe
    target = next(x for x in app.selectbox if x.label == "Business target")
    target.select("purchases").run()
    assert not app.exception
    assert "response" not in app.session_state
    assert not app.checkbox(key="confirm").value


def test_short_history_is_explained():
    app = AppTest.from_file(str(Path(__file__).parents[1] / "app.py"), default_timeout=30).run()
    next(x for x in app.selectbox if x.label == "Example").select("Short history").run()
    app.checkbox(key="confirm").check().run()
    next(b for b in app.button if b.label == "Compare and forecast").click().run()
    assert app.session_state["response"].status == "insufficient_history"
    assert not app.exception
