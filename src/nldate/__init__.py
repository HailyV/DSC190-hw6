from __future__ import annotations

import re
from datetime import date, datetime, timedelta

_WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

_NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
    "hundred": 100,
}

_MONTH_NAMES = {
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
}


def parse(s: str, today: date | None = None) -> date:
    """Parse a natural-language date string into a datetime.date."""
    reference = today or date.today()
    return _parse_inner(s, reference, 0)


def _parse_inner(s: str, today: date, depth: int) -> date:
    if depth > 6:
        raise ValueError("Expression is too deeply nested")

    # try absolute date on the original (pre-normalize) string first
    # so that month abbreviations with capitals are preserved for strptime
    absolute_result = _parse_absolute_date(s, today.year)
    if absolute_result is not None:
        return absolute_result

    normalized = _normalize(s)
    if not normalized:
        raise ValueError("Input date string is empty")

    if normalized in {"today", "now"}:
        return today
    if normalized == "tomorrow":
        return today + timedelta(days=1)
    if normalized == "yesterday":
        return today - timedelta(days=1)

    weekday_result = _parse_weekday_expression(normalized, today)
    if weekday_result is not None:
        return weekday_result

    # try absolute date again on normalized string
    absolute_result2 = _parse_absolute_date(normalized, today.year)
    if absolute_result2 is not None:
        return absolute_result2

    in_match = re.fullmatch(r"in\s+(.+)", normalized)
    if in_match:
        return _apply_duration(today, _parse_duration(in_match.group(1)), 1)

    ago_match = re.fullmatch(r"(.+?)\s+ago", normalized)
    if ago_match:
        return _apply_duration(today, _parse_duration(ago_match.group(1)), -1)

    rel_match = re.fullmatch(r"(.+?)\s+(before|after|from)\s+(.+)", normalized)
    if rel_match:
        delta_text, relation, base_text = rel_match.groups()
        base_date = _parse_inner(base_text, today, depth + 1)
        sign = 1 if relation in {"after", "from"} else -1
        return _apply_duration(base_date, _parse_duration(delta_text), sign)

    raise ValueError(f"Unable to parse date expression: {s}")


def _normalize(s: str) -> str:
    lowered = s.strip().lower()
    lowered = re.sub(r"\s+", " ", lowered)
    lowered = re.sub(r"\bon\s+", "", lowered, count=1)
    return lowered


def _parse_weekday_expression(s: str, today: date) -> date | None:
    for prefix in ("next ", "last ", "this "):
        if s.startswith(prefix):
            weekday_name = s[len(prefix):]
            if weekday_name not in _WEEKDAYS:
                return None
            target = _WEEKDAYS[weekday_name]
            current = today.weekday()
            if prefix == "next ":
                distance = (target - current + 7) % 7
                return today + timedelta(days=distance or 7)
            if prefix == "last ":
                distance = (current - target + 7) % 7
                return today - timedelta(days=distance or 7)
            return today + timedelta(days=(target - current + 7) % 7)

    if s in _WEEKDAYS:
        target = _WEEKDAYS[s]
        return today + timedelta(days=(target - today.weekday() + 7) % 7)

    return None


def _parse_absolute_date(s: str, default_year: int) -> date | None:
    # strip ordinal suffixes (1st -> 1, 2nd -> 2, etc.)
    cleaned = _strip_ordinal_suffixes(s.strip())
    # remove periods from abbreviated month names: Dec. -> Dec, Jan. -> Jan
    cleaned = re.sub(r"\b([A-Za-z]{3})\.", r"\1", cleaned)
    # normalise whitespace
    cleaned = re.sub(r"\s+", " ", cleaned)
    without_commas = cleaned.replace(",", "").strip()

    # all formats with an explicit year
    formats_with_year = (
        "%Y-%m-%d",       # 2025-12-01
        "%Y/%m/%d",       # 2025/12/04
        "%m/%d/%Y",       # 12/01/2025
        "%m-%d-%Y",       # 12-01-2025
        "%d/%m/%Y",       # 01/12/2025  (ambiguous but included)
        "%B %d %Y",       # December 1 2025
        "%b %d %Y",       # Dec 1 2025
        "%d %B %Y",       # 1 December 2025
        "%d %b %Y",       # 1 Dec 2025
        "%B %d, %Y",      # December 1, 2025
        "%b %d, %Y",      # Dec 1, 2025
        "%d %B, %Y",      # 1 December, 2025
        "%d %b, %Y",      # 1 Dec, 2025
        "%Y %B %d",       # 2025 December 1
        "%Y %b %d",       # 2025 Dec 1
    )
    for fmt in formats_with_year:
        for candidate in (without_commas, cleaned):
            try:
                return datetime.strptime(candidate, fmt).date()
            except ValueError:
                continue

    # formats without a year — infer from default_year
    has_month_name = any(m in cleaned.lower() for m in _MONTH_NAMES)
    if has_month_name:
        formats_no_year = (
            "%B %d",   # December 1
            "%b %d",   # Dec 1
            "%d %B",   # 1 December
            "%d %b",   # 1 Dec
        )
        for fmt in formats_no_year:
            for candidate in (without_commas, cleaned):
                try:
                    parsed = datetime.strptime(candidate, fmt).date()
                    return parsed.replace(year=default_year)
                except ValueError:
                    continue

    return None


def _strip_ordinal_suffixes(s: str) -> str:
    return re.sub(r"\b(\d+)(st|nd|rd|th)\b", r"\1", s)


def _parse_duration(duration_text: str) -> dict[str, int]:
    parts = re.split(r"\s*(?:,|and)\s*", duration_text)
    totals: dict[str, int] = {"days": 0, "weeks": 0, "months": 0, "years": 0}
    pattern = re.compile(r"(.+?)\s+(day|days|week|weeks|month|months|year|years)\b")

    for raw_part in parts:
        part = raw_part.strip()
        if not part:
            continue
        match = pattern.fullmatch(part)
        if not match:
            raise ValueError(f"Invalid duration segment: {part}")
        number_text, unit = match.groups()
        amount = _parse_number(number_text)
        key = f"{unit}s" if not unit.endswith("s") else unit
        totals[key] += amount

    if all(value == 0 for value in totals.values()):
        raise ValueError(f"Invalid duration: {duration_text}")
    return totals


def _parse_number(number_text: str) -> int:
    token = number_text.strip()
    if token.isdigit():
        return int(token)

    words = token.replace("-", " ").split()
    if not words:
        raise ValueError(f"Invalid number: {number_text}")

    total = 0
    current = 0
    for word in words:
        if word not in _NUMBER_WORDS:
            raise ValueError(f"Invalid number: {number_text}")
        value = _NUMBER_WORDS[word]
        if value == 100:
            current = max(1, current) * value
        else:
            current += value
    total += current
    return total


def _apply_duration(base: date, duration: dict[str, int], sign: int) -> date:
    result = base
    year_delta = sign * duration["years"]
    month_delta = sign * duration["months"]

    if year_delta:
        result = _add_months(result, year_delta * 12)
    if month_delta:
        result = _add_months(result, month_delta)

    day_delta = sign * (duration["days"] + 7 * duration["weeks"])
    if day_delta:
        result += timedelta(days=day_delta)

    return result


def _add_months(d: date, months: int) -> date:
    zero_based_month = d.month - 1 + months
    new_year = d.year + zero_based_month // 12
    new_month = zero_based_month % 12 + 1
    max_day = _days_in_month(new_year, new_month)
    return date(new_year, new_month, min(d.day, max_day))


def _days_in_month(year: int, month: int) -> int:
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    current_month = date(year, month, 1)
    return (next_month - current_month).days
