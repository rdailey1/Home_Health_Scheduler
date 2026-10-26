from streamlit.testing.v1 import AppTest


def test_app_generates_schedule_and_comparison():
    at = AppTest.from_file("../app.py", default_timeout=60).run()
    assert not at.exception
    assert len(at.dataframe) == 1  # patient list only

    at.button(key="generate").click().run()
    assert not at.exception
    assert len(at.dataframe) == 7  # patients, one table per day, stages

    at.button(key="compare").click().run()
    assert not at.exception
    assert len(at.dataframe) == 7  # stages now include the random row
