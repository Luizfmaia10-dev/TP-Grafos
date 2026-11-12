# TimeUtils contract (issue #22)

`app.time_utils.TimeUtils` converts service-day times to the minute-based values
already used by `Connection`. It has static methods, no instance state, and no
dependencies on the API, frontend, or graph libraries.

- `time_to_minutes(time_str: str) -> float`: accepts `HH:MM:SS` with at least
  two ASCII digits for hours and exactly two for minutes and seconds. Minutes
  and seconds must be in `00..59`. Hours may exceed 23; there is no daily wrap.
  Whitespace, signs, missing fields, and fractional seconds are rejected with
  `ValueError`. Input cleanup belongs to `DataLoader`.
- `minutes_to_time(minutes: float) -> str`: accepts finite, nonnegative minutes
  and rounds to the nearest whole second with Python's `round` (ties to even).
  It formats hours with at least two digits, preserving values beyond 24 hours.
  Negative, NaN, and infinite values raise `ValueError`.

The conversion is `(hours * 3600 + minutes * 60 + seconds) / 60`.
The inverse rounds `minutes * 60` once, then uses `divmod` to split the result
into hours, minutes, and seconds. Rounding once handles carries across minute,
hour, and day boundaries and avoids truncating floating-point approximations.

Examples:

```python
from app.time_utils import TimeUtils

TimeUtils.time_to_minutes("08:30:45")  # 510.75
TimeUtils.time_to_minutes("25:15:30")  # 1515.5
TimeUtils.minutes_to_time(1515.5)      # "25:15:30"

arrival = TimeUtils.time_to_minutes("23:59:45")
departure = TimeUtils.time_to_minutes("24:00:15")
waiting_time = departure - arrival   # 0.5 minutes (30 seconds)
```

Minutes are floating-point approximations, consistent with the existing domain.
The contract preserves whole seconds at transport-schedule magnitudes; it does
not promise arbitrary-precision arithmetic for unbounded hour values or retain
subsecond input when formatting. This utility does not choose service dates,
load schedules, or find routes.

## Validation

These unit tests use synthetic values and do not require the real GTFS dataset.
For integration with the real feed, download the complete TXT files using Git LFS
before loading them; see [the dataset guide](../data/gtfs/README.md).

From `backend/`, with the project dependencies installed:

```sh
python -m pytest
python -m pytest tests/test_time_utils.py --cov=app.time_utils --cov-branch --cov-report=term-missing
```

Tests cover conversion in both directions, invalid input, rounding and carries,
extended hours, waiting across midnight, and every whole second within selected
hours (including 24, 25, 48, and 100).

## Complexity and planning correction

For ordinary bounded schedule fields, conversions use constant work and space
relative to the graph size: they never traverse vertices or edges. Parsing an
input string of length L requires O(L) time; formatting also depends on the
number of hour digits. Arbitrarily large integers are not constant-cost values.

The original PLAN.md item requested integer minutes. That would discard seconds
and conflict with the UML return type and `Connection`'s floating-point minute
fields. The item is corrected to fractional minutes while preserving seconds.
