"""Conversions between service-day timestamps and fractional minutes."""

from math import isfinite
from re import fullmatch


class TimeUtils:
    """Stateless time conversions; hours are not wrapped at midnight."""

    __slots__ = ()

    @staticmethod
    def time_to_minutes(time_str: str) -> float:
        """Parse HH:MM:SS, preserving seconds and allowing hours above 23.

        Hours require at least two ASCII digits. Minutes and seconds require
        exactly two digits in 00..59. Invalid strings raise ValueError.
        """
        if fullmatch(r"[0-9]{2,}:[0-5][0-9]:[0-5][0-9]", time_str) is None:
            raise ValueError("Expected HH:MM:SS with minutes and seconds in 00..59")

        hours, minutes, seconds = map(int, time_str.split(":"))
        return (hours * 3600 + minutes * 60 + seconds) / 60

    @staticmethod
    def minutes_to_time(minutes: float) -> str:
        """Format finite, nonnegative minutes as HH:MM:SS without daily wrap.

        Round to the nearest second, using ties to even as in Python's round.
        Invalid numeric values raise ValueError.
        """
        if not isfinite(minutes) or minutes < 0:
            raise ValueError("Minutes must be finite and nonnegative")

        total_seconds = round(minutes * 60)
        hours, remaining_seconds = divmod(total_seconds, 3600)
        whole_minutes, seconds = divmod(remaining_seconds, 60)
        return f"{hours:02d}:{whole_minutes:02d}:{seconds:02d}"
