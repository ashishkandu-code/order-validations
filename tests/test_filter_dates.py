from unittest.mock import patch
import pytest
from datetime import datetime, timedelta
from filter_dates import DateInFutureError, FilterDate, FilterDates, get_default_filter_dates, get_filter_dates_input


class TestFilterDate:

    # Creating a FilterDate object with a valid date string should not raise any exceptions.
    def test_valid_date_string(self):
        date_string = '01/01/2022 12:00'
        expected_datetime = datetime(2022, 1, 1, 12, 0)
        try:
            filter_date = FilterDate(date_string)
        except Exception as e:
            pytest.fail(f"Unexpected exception: {e}")

        # When calling parse_date
        # Then the resulting datetime object should match the expected value
        assert filter_date.parse_date() == expected_datetime

    # Calling the parse_date method on a FilterDate object with a valid date string should return a datetime object.
    def test_parse_valid_date_string(self):
        date_string = '01/01/2022 12:00'
        filter_date = FilterDate(date_string)
        parsed_date = filter_date.parse_date()
        assert isinstance(parsed_date, datetime)

    # Creating a FilterDate object with the current date and time should not raise any exceptions.
    def test_current_date_time(self):
        current_date_time = datetime.now().strftime('%d/%m/%Y %H:%M')
        try:
            filter_date = FilterDate(current_date_time)
        except Exception as e:
            pytest.fail(f"Unexpected exception: {e}")

    # Creating a FilterDate object with an invalid date string should raise a ValueError.
    def test_invalid_date_string(self):
        date_string = '01/01/2022 25:00'
        with pytest.raises(ValueError):
            filter_date = FilterDate(date_string)

    # Creating a FilterDate object with a date string in the future should raise a DateInFutureError.
    def test_future_date_string(self):
        future_date = (datetime.now() + timedelta(days=1)).strftime('%d/%m/%Y %H:%M')
        with pytest.raises(DateInFutureError):
            filter_date = FilterDate(future_date)


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

def test_get_default_filter_dates_monday():
    """Test that default filter dates are returned with the correct types."""
    # Set the current date to a Monday
    current_date = datetime(2023, 10, 16)  # Monday
    # Mock the datetime.now() to return the Monday date
    with patch('filter_dates.datetime') as mock_datetime:
        mock_datetime.now.return_value = current_date
        # Mock the datetime.strptime() to return datetime object
        mock_datetime.strptime.return_value = current_date
        # Call the function and check the returned dates
        filter_dates = get_default_filter_dates()

        # Then the start and end dates should be strings
        assert isinstance(filter_dates.start.date, str)
        assert isinstance(filter_dates.end.date, str)

        assert filter_dates.start.date == (
            current_date - timedelta(days=3)).strftime("%d/%m/%Y 00:00")
        assert filter_dates.end.date == current_date.strftime("%d/%m/%Y 00:00")


def test_get_default_filter_dates_non_monday():
    """Test that default filter dates are returned with the correct types."""
    # Set the current date to a Tuesday
    current_date = datetime(2023, 10, 17)
    # Mock the datetime.now() to return the Tuesday date
    with patch('filter_dates.datetime') as mock_datetime:
        mock_datetime.now.return_value = current_date
        # Mock the datetime.strptime() to return datetime object
        mock_datetime.strptime.return_value = current_date
        # Call the function and check the returned dates
        filter_dates = get_default_filter_dates()

        # Then the start and end dates should be strings
        assert isinstance(filter_dates.start.date, str)
        assert isinstance(filter_dates.end.date, str)

        assert filter_dates.start.date == (
            current_date - timedelta(days=1)).strftime("%d/%m/%Y 00:00")
        assert filter_dates.end.date == current_date.strftime("%d/%m/%Y 00:00")


def test_get_filter_dates_input_defaults(monkeypatch):
    """Test that default filter dates are used when no input is given."""
    # Given no user input (default values are used)
    monkeypatch.setattr('builtins.input', lambda _: '')
    filter_dates = get_filter_dates_input()

    # When calling get_filter_dates_input
    # Then the resulting start and end dates should match the default values
    assert filter_dates.start.date == (
        datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y 00:00")
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
