from datetime import date
import pytest

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from week_utils import week_label_for, current_week_label


def test_w01_partial_week_uses_project_start():
    assert week_label_for(date(2026, 4, 17)) == "W01_Apr-15-19"


def test_w01_at_project_start_day():
    assert week_label_for(date(2026, 4, 15)) == "W01_Apr-15-19"


def test_w02_full_week():
    assert week_label_for(date(2026, 4, 21)) == "W02_Apr-20-26"


def test_w03_cross_month_apr_to_may():
    assert week_label_for(date(2026, 4, 29)) == "W03_Apr-27-May-3"


def test_late_year_dec_to_jan_cross_month():
    # Mon Dec 28 - Sun Jan 3, 2027
    label = week_label_for(date(2026, 12, 28))
    assert label.startswith("W")
    assert "Dec-28" in label
    assert "Jan-3" in label


def test_before_project_start_raises():
    with pytest.raises(ValueError):
        week_label_for(date(2026, 4, 12))


def test_current_week_returns_string():
    label = current_week_label()
    assert label.startswith("W")
    assert "_" in label
