import pytest


@pytest.fixture
def timetosecond():
        return {
            'minute': 60,
            'hour': 60 * 60,
            'day': 24 * 60 * 60
        }


@pytest.fixture
def days():
    """
    Returns number of days in seconds
    """
    def days(n):
        return n * 24 * 60 * 60
    return days
