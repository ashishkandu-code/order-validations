from dateutil import parser
from dataclasses import dataclass, field
from datetime import datetime, timedelta

class DateInFutureError(Exception):
    """
    Custom exception raised when the date is in the future.
    """
    pass

@dataclass
class FilterDate:
    """
    Represents a filter for a specific date.

    Attributes:
        date (str): The date in the format '%d/%m/%Y %H:%M'.

    Methods:
        parse_date:
            Parses the 'date' attribute into a datetime object.
            Returns:
                datetime: The parsed datetime object.

            Raises:
                ValueError: If the input date format is incorrect.

        validate_date:
            Validates that the date is not in the future.
            Raises:
            DateInFutureError: If the date is in the future.

        __str__:
            Returns a human-readable representation of the object.
            Returns:
                str: The formatted date string.
    """

    date: str = field(default='', metadata={'type': 'str'})

    def parse_date(self):
        """
        Return a datetime object parsed from the 'date' attribute.
        """
        return datetime.strptime(self.date, '%d/%m/%Y %H:%M')

    def validate_date(self):
        """
        Validate that the date is not in the future.
        Raises:
            DateInFutureError: If the date is in the future.
        """
        if self.parse_date() > datetime.now():
            raise DateInFutureError("Date cannot be in the future")

    def __post_init__(self):
        """
        Initialize the object and validate the date.
        """
        self.validate_date()

    def __str__(self):
        """
        Return a human-readable representation of the object.
        """
        return self.date


class EndBeforeStartError(Exception):
    """
    Custom exception raised when the end date is before the start date.
    """
    pass

@dataclass
class FilterDates:
    """
    Represents a pair of start and end dates for filtering.

    Attributes:
        start (FilterDate): The starting date for the filter.
        end (FilterDate): The ending date for the filter.

    Methods:
        __post_init__:
            Validates that the start date is before the end date.
            Raises:
                EndBeforeStartError: If the end datetime is before the start datetime.
        validate_dates:
            Validates that the start date is before the end date.
            Raises:
                EndBeforeStartError: If the end datetime is before the start datetime.
    """

    start: FilterDate
    end: FilterDate

    def __post_init__(self):
        """
        Validate that the end datetime is not before the start datetime.
        """
        self.validate_dates()

    def validate_dates(self):
        """
        Validates that the start date is before the end date.
        Raises:
            EndBeforeStartError: If the end datetime is before the start datetime.
        """
        if self.start.parse_date() > self.end.parse_date():
            raise EndBeforeStartError("End datetime cannot be before start datetime!")


def get_default_filter_dates():
    """
    Returns default filter dates for the current day or last Friday if today is Monday.

    This function provides a default start and end date for filtering. The start date is set to
    the beginning of the previous day (or the last Friday if today is Monday), and the
    end date is set to the beginning of the current day.

    Returns:
        FilterDates: The default filter dates.
    """
    today = datetime.now()
    if today.weekday() == 0:  # Monday
        last_friday = today - timedelta(days=3)
        start_date = FilterDate(last_friday.strftime('%d/%m/%Y 00:00'))
    else:
        yesterday = today - timedelta(days=1)
        start_date = FilterDate(yesterday.strftime('%d/%m/%Y 00:00'))
    end_date = FilterDate(today.strftime('%d/%m/%Y 00:00'))
    return FilterDates(start_date, end_date)


def get_month_default_dates():
    """
    To be implemented: Returns default filter dates for the current month.
    """
    raise NotImplementedError


def get_filter_dates_input():
    """
    Prompts the user to enter start and end filter dates.

    This function asks the user for the starting and ending filter dates. It provides default
    values which are the current day's beginning for the end date and the beginning of the
    previous day (or the previous Friday if today is Monday) for the start date. The user can
    either accept the defaults by pressing Enter or provide custom values.

    Returns:
        FilterDates: The filter dates based on user input.
    """
    print("[!] Use 24 Hours format to give time.")
    filter_dates = get_default_filter_dates()

    start_date_input = input(f"Enter starting datetime [DD/MM/YYYY HH:MM] (Default {filter_dates.start.date}): ")
    if start_date_input != "":
        filter_dates.start = FilterDate(start_date_input)

    end_date_input = input(f"Enter ending datetime [DD/MM/YYYY HH:MM] (Default {filter_dates.end.date}): ")
    if end_date_input != "":
        filter_dates.end = FilterDate(end_date_input)

    return filter_dates

