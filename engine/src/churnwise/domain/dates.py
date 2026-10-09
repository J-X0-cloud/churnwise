"""Calendar helpers and the date labels used on charts and tables.

Labels are built from fixed English month names rather than ``strftime`` so they never depend on the
server's locale.
"""

from __future__ import annotations

import calendar
from collections.abc import Iterator
from datetime import date, datetime

MONTH_ABBR = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
MONTH_NAMES = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


def add_months(d: date, months: int) -> date:
    """Shift by whole calendar months, clamping the day to the end of shorter months (Jan 31 + 1 = Feb 28)."""
    year, month_index = divmod(d.month - 1 + months, 12)
    year += d.year
    month = month_index + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return d.replace(year=year, month=month, day=day)


def start_of_month(d: date) -> date:
    return d.replace(day=1)


def month_key(d: date | datetime) -> date:
    """The first day of the month containing ``d``, as a plain date."""
    return date(d.year, d.month, 1)


def months_between(start: date, end: date) -> int:
    """Whole calendar months from the month of ``start`` to the month of ``end`` (can be negative)."""
    return (end.year - start.year) * 12 + end.month - start.month


def iter_months(first: date, last: date) -> Iterator[date]:
    """First day of every month from the month of ``first`` through the month of ``last``, inclusive."""
    current = month_key(first)
    stop = month_key(last)
    while current <= stop:
        yield current
        current = add_months(current, 1)


def day_of_year(d: date) -> int:
    return d.timetuple().tm_yday


def is_weekday(d: date) -> bool:
    """Monday to Friday."""
    return d.weekday() < 5


def month_label(d: date, with_year: bool = False) -> str:
    """``Oct`` or ``Jan '26``."""
    label = MONTH_ABBR[d.month - 1]
    return f"{label} '{d.year % 100:02d}" if with_year else label


def auto_month_label(d: date) -> str:
    """Month label that shows the year on January only, which is how every monthly axis is labelled."""
    return month_label(d, with_year=d.month == 1)


def day_label(d: date) -> str:
    """``Sep 24``."""
    return f"{MONTH_ABBR[d.month - 1]} {d.day}"


def month_year(d: date) -> str:
    """``Sep 2026``."""
    return f"{MONTH_ABBR[d.month - 1]} {d.year}"


def long_month_year(d: date) -> str:
    """``September 2026``."""
    return f"{MONTH_NAMES[d.month - 1]} {d.year}"


def long_date(d: date) -> str:
    """``Sep 24, 2026``."""
    return f"{MONTH_ABBR[d.month - 1]} {d.day}, {d.year}"
