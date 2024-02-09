import pytest
from datetime import datetime, timedelta
from filter_dates import FilterDate, FilterDates, get_default_filter_dates, get_filter_dates_input

def test_get_date_object_success():
    """Test that a FilterDate object returns the correct datetime object."""
    # Given a valid date string
    filter_date = FilterDate('01/04/2023 12:00')
    expected_date = datetime(2023, 4, 1, 12, 0)

    # When calling get_date_object
    # Then the resulting datetime object should match the expected value
    assert filter_date.get_date_object() == expected_date

def test_get_date_object_fail():
    """Test that an invalid date string raises a SystemExit exception."""
    # Given an invalid date string
    # When calling get_date_object
    # Then a SystemExit exception should be raised with the correct error message
    with pytest.raises(SystemExit) as e:
        FilterDate('32/04/2023 12:00').get_date_object()
    assert str(e.value) == "Incorrect data format, should be DD/MM/YYYY HH:MM"

def test_post_init_not_future():
    """Test that a FilterDate object is not initialized with a future date."""
    # Given a date string that is not in the future
    filter_date = FilterDate('01/04/2023 12:00')

    # When calling __post_init__
    # Then the returned datetime object should not be in the future
    assert filter_date.__post_init__() <= datetime.now()

def test_post_init_future_date():
    """Test that initializing a FilterDate object with a future date raises SystemExit."""
    # Given a date string that is in the future
    future_date = (datetime.now() + timedelta(days=1)).strftime('%d/%m/%Y %H:%M')

    # When calling __post_init__
    # Then a SystemExit exception should be raised with the correct error message
    with pytest.raises(SystemExit) as e:
        FilterDate(future_date).__post_init__()
    assert str(e.value) == "Date cannot be in future"

def test_filter_dates():
    """Test that a FilterDates object is initialized with the correct start and end dates."""
    # Given valid start and end date strings
    start_date = FilterDate('01/01/2022 00:00')
    end_date = FilterDate('01/01/2023 00:00')
    filter_dates = FilterDates(start_date, end_date)

    # When initializing a FilterDates object
    # Then the start and end attributes should match the provided FilterDate objects
    assert filter_dates.start == start_date
    assert filter_dates.end == end_date

def test_filter_dates_invalid():
    """Test that initializing FilterDates with an end date before the start date raises SystemExit."""
    # Given start and end date strings where the end date is before the start date
    end_date = FilterDate('01/01/2022 00:00')
    start_date = FilterDate('01/01/2023 00:00')

    # When initializing a FilterDates object
    # Then a SystemExit exception should be raised with the correct error message
    with pytest.raises(SystemExit) as e:
        FilterDates(start_date, end_date).__post_init__()
    assert str(e.value) == "End datetime cannot be before start datetime!"

def test_get_default_filter_dates():
    """Test that default filter dates are returned with the correct types."""
    # When calling get_default_filter_dates
    default_filter_dates = get_default_filter_dates()

    # Then the start and end dates should be strings
    assert isinstance(default_filter_dates.start.date, str)
    assert isinstance(default_filter_dates.end.date, str)

def test_get_filter_dates_input_defaults(monkeypatch):
    """Test that default filter dates are used when no input is given."""
    # Given no user input (default values are used)
    monkeypatch.setattr('builtins.input', lambda _: '')
    filter_dates = get_filter_dates_input()

    # When calling get_filter_dates_input
    # Then the resulting start and end dates should match the default values
    assert filter_dates.start.date == (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y 00:00")
    assert filter_dates.end.date == datetime.now().strftime("%d/%m/%Y 00:00")

def test_get_filter_dates_input_custom_values(monkeypatch):
    """Test that custom filter dates are used when input is given."""
    # Given user input for custom start and end dates
    monkeypatch.setattr('builtins.input', lambda _: '01/01/2023 08:00')
    filter_dates = get_filter_dates_input()

    # When calling get_filter_dates_input
    # Then the resulting start and end dates should match the custom values provided
    assert filter_dates.start.date == '01/01/2023 08:00'
    assert filter_dates.end.date == '01/01/2023 08:00'

