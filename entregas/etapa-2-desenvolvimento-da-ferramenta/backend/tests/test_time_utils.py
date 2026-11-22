import pytest

from app.time_utils import TimeUtils


@pytest.mark.parametrize(
    ("time_str", "minutes"),
    [
        ("00:00:00", 0.0),
        ("00:00:01", 1 / 60),
        ("08:30:45", 510.75),
        ("23:59:59", 1439 + 59 / 60),
        ("24:00:00", 1440.0),
        ("25:15:30", 1515.5),
        ("48:00:00", 2880.0),
        ("100:00:01", 6000 + 1 / 60),
    ],
)
def test_time_to_minutes_preserves_seconds_and_service_day_hours(time_str, minutes):
    assert TimeUtils.time_to_minutes(time_str) == pytest.approx(minutes)


@pytest.mark.parametrize(
    "time_str",
    [
        "", "08:30", "08:30:00:00", "8:30:00", "08:3:00", "08:30:0",
        "-01:00:00", "+08:00:00", "08:60:00", "08:00:60", "08:-1:00",
        "08:30:00.5", "aa:bb:cc", " 08:30:00", "08:30:00\n", "０８:30:00",
    ],
)
def test_time_to_minutes_rejects_invalid_times(time_str):
    with pytest.raises(ValueError):
        TimeUtils.time_to_minutes(time_str)


@pytest.mark.parametrize(
    ("minutes", "time_str"),
    [
        (0, "00:00:00"),
        (1 / 60, "00:00:01"),
        (510.75, "08:30:45"),
        (1440, "24:00:00"),
        (1515.5, "25:15:30"),
        (6000 + 1 / 60, "100:00:01"),
        (0.49 / 60, "00:00:00"),
        (0.51 / 60, "00:00:01"),
        (0.5 / 60, "00:00:00"),
        (1.5 / 60, "00:00:02"),
        (59.6 / 60, "00:01:00"),
        (59 + 59.6 / 60, "01:00:00"),
        (1439 + 59.6 / 60, "24:00:00"),
    ],
)
def test_minutes_to_time_formats_and_rounds_to_nearest_second(minutes, time_str):
    assert TimeUtils.minutes_to_time(minutes) == time_str


@pytest.mark.parametrize("minutes", [-1, -0.001, float("nan"), float("inf"), -float("inf")])
def test_minutes_to_time_rejects_negative_or_non_finite_values(minutes):
    with pytest.raises(ValueError):
        TimeUtils.minutes_to_time(minutes)


@pytest.mark.parametrize("hours", [0, 8, 23, 24, 25, 48, 100])
def test_round_trip_preserves_every_second_within_an_hour(hours):
    for minute in range(60):
        for second in range(60):
            time_str = f"{hours:02d}:{minute:02d}:{second:02d}"
            assert TimeUtils.minutes_to_time(TimeUtils.time_to_minutes(time_str)) == time_str


def test_waiting_time_across_midnight_stays_positive():
    arrival = TimeUtils.time_to_minutes("23:59:45")
    departure = TimeUtils.time_to_minutes("24:00:15")

    assert departure - arrival == pytest.approx(0.5)
