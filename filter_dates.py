from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class FilterDate:
    """
    Represents a filter for a specific date.

    Attributes:
        date (str): The date in the format '%d/%m/%Y %H:%M'.

    Methods:
        get_date_object:
            Parses the 'date' attribute into a datetime object.
            Returns:
                datetime: The parsed datetime object.

            Raises:
                SystemExit: If the input date format is incorrect.

        __post_init__:
            Validates that the date is not in the future immediately after object initialization.
            Returns:
                datetime: The validated datetime object.
    """

    date: str

    def get_date_object(self):
        """
        Return a datetime object parsed from the 'date' attribute.
        """
        try:
            return datetime.strptime(self.date, '%d/%m/%Y %H:%M')
        except ValueError:
            raise SystemExit("Incorrect data format, should be DD/MM/YYYY HH:MM")

    def __post_init__(self):
        """
        Validate that the date is not in the future.
        """
        date_object = self.get_date_object()
        if date_object > datetime.now():
            raise SystemExit("Date cannot be in future")
        return date_object


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
                SystemExit: If the end datetime is before the start datetime.
    """

    start: FilterDate
    end: FilterDate

    def __post_init__(self):
        """
        Validate that the end datetime is not before the start datetime.
        """
        if self.start.get_date_object() > self.end.get_date_object():
            raise SystemExit("End datetime cannot be before start datetime!")


def get_default_filter_dates():
    """
    Returns default filter dates for the current day or last Friday if today is Monday.

    This function provides a default start and end date for filtering. The start date is set to
    the beginning of the previous day (or the previous Friday if today is Monday), and the
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

    filter_date_from = input(f"Enter starting datetime [DD/MM/YYYY HH:MM] (Default {filter_dates.start.date}): ")
    if filter_date_from != "":
        filter_dates.start = FilterDate(filter_date_from)

    filter_date_to = input(f"Enter ending datetime [DD/MM/YYYY HH:MM] (Default {filter_dates.end.date}): ")
    if filter_date_to != "":
        filter_dates.end = FilterDate(filter_date_to)

    return filter_dates

