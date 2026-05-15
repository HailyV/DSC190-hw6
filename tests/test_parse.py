from datetime import date

import pytest

from nldate import parse


def test_today() -> None:
    assert parse("today", today=date(2025, 1, 15)) == date(2025, 1, 15)


def test_tomorrow() -> None:
    assert parse("tomorrow", today=date(2025, 1, 15)) == date(2025, 1, 16)


def test_yesterday() -> None:
    assert parse("yesterday", today=date(2025, 1, 15)) == date(2025, 1, 14)


def test_next_tuesday() -> None:
    # Wednesday -> next Tuesday is 6 days away
    assert parse("next Tuesday", today=date(2025, 1, 1)) == date(2025, 1, 7)


def test_last_monday() -> None:
    assert parse("last Monday", today=date(2025, 1, 1)) == date(2024, 12, 30)


def test_absolute_date_with_ordinal() -> None:
    assert parse("December 1st, 2025", today=date(2024, 1, 1)) == date(2025, 12, 1)


def test_absolute_date_iso() -> None:
    assert parse("2025-12-01", today=date(2024, 1, 1)) == date(2025, 12, 1)


def test_simple_before_expression() -> None:
    assert parse("5 days before December 1st, 2025", today=date(2024, 1, 1)) == date(2025, 11, 26)


def test_compound_after_expression() -> None:
    assert parse(
        "1 year and 2 months after yesterday",
        today=date(2024, 2, 29),
    ) == date(2025, 4, 28)


def test_from_expression_with_words() -> None:
    assert parse("two weeks from tomorrow", today=date(2025, 2, 10)) == date(2025, 2, 25)


def test_in_expression() -> None:
    assert parse("in 3 days", today=date(2025, 3, 10)) == date(2025, 3, 13)


def test_ago_expression() -> None:
    assert parse("3 weeks ago", today=date(2025, 3, 10)) == date(2025, 2, 17)


def test_month_rollover_clamps_day() -> None:
    assert parse("1 month after January 31st, 2025", today=date(2025, 1, 1)) == date(2025, 2, 28)


def test_invalid_expression_raises() -> None:
    with pytest.raises(ValueError):
        parse("sometime soon", today=date(2025, 1, 1))
