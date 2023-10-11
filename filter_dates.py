
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class FilterDate(str):
    date: str

    def get_date_object(self):
        try:
            return datetime.strptime(self.date, '%d/%m/%Y %H:%M')
        except ValueError:
            raise SystemExit("Incorrect data format, should be DD/MM/YYYY HH:MM")

    def __post_init__(self):
        date_object = self.get_date_object()
        if date_object > datetime.now():
            raise SystemExit("Date cannot be in future")
        return date_object


@dataclass
class FilterDates:
    start: FilterDate
    end: FilterDate

    def __post_init__(self):
        if self.start.get_date_object() > self.end.get_date_object():
            raise SystemExit("End datetime cannot be before start datetime!")


def get_default_filter_dates():
    yesterday = datetime.now() - timedelta(days=1)
    filter_start_date = FilterDate(yesterday.strftime('%d/%m/%Y 00:00'))
    filter_end_date = FilterDate(datetime.now().strftime('%d/%m/%Y %H:%M'))
    return FilterDates(filter_start_date, filter_end_date)


def get_filter_dates_input():
    """Prompts user to enter a filter date from and to"""
    print("[!] Use 24 Hours format to give time.")
    filter_dates = get_default_filter_dates()

    filter_date_from = input(f"Enter starting datetime [DD/MM/YYYY HH:MM] (Default {filter_dates.start}): ")
    if filter_date_from != "":
        filter_dates.start = FilterDate(filter_date_from)

    filter_date_to = input(f"Enter ending datetime [DD/MM/YYYY HH:MM] (Default {filter_dates.end}): ")
    if filter_date_to != "":
        filter_dates.end = FilterDate(filter_date_to)

    return filter_dates

