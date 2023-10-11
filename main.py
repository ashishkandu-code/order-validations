from dataclasses import dataclass
from swap_portal import SwapDeliveryAuthenticatedPage
from datetime import datetime, timedelta
import pandas as pd

from requests import Response

import logging
from helper import dump_json_to_file, write_to_file, generate_xlsx_report
from my_logging import log_setup
from reports import (
    Report,
    ReportType,
    Filter,
)

import enlighten


log_setup()
logger = logging.getLogger(__name__)


REQUIRED_COLUMNS = ('Order_No', 'Order_Delivery_Status', 'Order_Cancellation_Status', 'Package_Type', 'Fulfillment_Mode')
RUN_FOR = ('hotlink prepaid', 'hotlink postpaid', 'maxis postpaid', 'preorder postpaid instore')
# RUN_FOR = ('preorder postpaid instore', )


@dataclass
class ReportInfo:
    report_type: ReportType
    filters: list[Filter]


REPORTS_INFO = {
    'hotlink prepaid': ReportInfo(**{
        'report_type': ReportType('PREPAID'),
        'filters': [],
    }),
    'hotlink postpaid': ReportInfo(**{
        'report_type': ReportType('POSTPAID', 'hotlink postpaid'),
        'filters': [
            Filter('Fulfillment_Mode', 'exists', ('Standard Delivery', )),
            Filter('Order_Delivery_Status', 'notExists', ('fulfilled', )),
        ],
    }),
    'maxis postpaid': ReportInfo(**{
        'report_type': ReportType('POSTPAID', 'maxis postpaid'),
        'filters': [
            Filter('Fulfillment_Mode', 'exists', ('Standard Delivery', )),
            Filter('Order_Delivery_Status', 'notExists', ('fulfilled', )),
        ],
    }),
    'preorder postpaid instore': ReportInfo(**{
        'report_type': ReportType('POSTPAID', 'maxis postpaid'),
        'filters': [
            Filter('Fulfillment_Mode', 'exists', ('In-Store Pickup', )),
            Filter('Package_Type', 'exists', ('Device + Plan', )),
            Filter('Order_Type', 'exists', ('Pre Order', )),
        ],
    }),
}

cached_reports: list[Report] = []

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


def extract_swap_eligible_orders(report: Report, filters: list[Filter]=[]) -> list[tuple[str, str]]:
    """
    It displays current report selected columns dataframe and filters order IDs.
    Also renames order IDs starting from either 'HOS' or 'MOS' based on report type.
    """
    if filters:
        for filter in filters:
            report.filter(filter)
        logger.info('Filters applied!')

    logger.info(f"{report.name} Data\n{report.get_columns_reduced_dataframe(REQUIRED_COLUMNS).count()}")
    order_ids = report.dataframe['Order_No'].values
    if report.report_type.planType == "PREPAID":
        swap_orders_ids = [(order, order) if order.startswith('MOS') else (f"HOS{order.split('A')[0]}", order) for order in order_ids]
    elif report.report_type.planType == "POSTPAID":
        swap_orders_ids = [(order, order) if order.startswith('MOS') else (f"MOS{order.split('A')[0]}", order) for order in order_ids]
    return swap_orders_ids


def swap_filtering(responses: list[Response], orders_list: list[tuple[str, str]]) -> dict[str, list[tuple[str, str]]]:
    """
    Filters the orders in responses whether flown to swap or not.
    """
    responses_from_swap = dict()

    responses_from_swap["not_found"] = []
    responses_from_swap["found"] = []

    for response, order_records in zip(responses, orders_list):
        try:
            data = response.json()
        except AttributeError as e:
            logger.error(e)
            data = response
        if data['iTotalDisplayRecords'] == 1:
            responses_from_swap["found"].append(order_records)
        else:
            responses_from_swap["not_found"].append(order_records)
    return responses_from_swap


def save_report(data, report_name):
    try:
        dump_json_to_file(data, f'{report_name}_{datetime.now().strftime("%m_%d_%Y-%H_%M_%S")}.json')
    except Exception as e:
        logger.exception(e)
        write_to_file(data, f'{report_name}_error')


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


def get_report(report_type: ReportType, filter_dates: FilterDates, save_to_disk: bool):
    for report in cached_reports:
        if report.report_type == report_type:
            logger.info('Report found in cache!')
            return report
    report = Report(report_type, filter_dates.start, filter_dates.end, save_to_disk)
    cached_reports.append(report)
    return report

def main(filter_dates: FilterDates, save_to_disk: bool):

    orders_not_flown_to_swap: list[tuple[str, str]] = []
    dataframes = dict()
    swap_delivery_page = SwapDeliveryAuthenticatedPage()

    for report_name in RUN_FOR:
        selected_report_info = REPORTS_INFO[report_name]
        report_type = selected_report_info.report_type
        report_filters = selected_report_info.filters

        report = get_report(report_type, filter_dates, save_to_disk)
        orders_to_check = extract_swap_eligible_orders(report, report_filters)

        total_orders_count = len(orders_to_check)
        if total_orders_count == 0:
            continue
        manager = enlighten.get_manager()
        pbar = manager.counter(total=total_orders_count, desc=report_name)

        responses = []
        for swap_order_id, _ in orders_to_check:
            response = swap_delivery_page.get_order(swap_order_id)
            if not response:
                responses.append({'iTotalDisplayRecords': -1})
            else:
                responses.append(response)
            pbar.update(force=True)

        swap_flown_data = swap_filtering(responses, orders_to_check)

        orders_not_found = swap_flown_data['not_found']
        if orders_not_found:
            orders_not_flown_to_swap.extend(orders_not_found)
            original_order_ids = list(map(lambda order_tuple: order_tuple[1], orders_not_found))
            filtered_dataframe = report.get_filtered_dataframe_by_orderNos(original_order_ids)
            try:
                df = dataframes[report.name]
                dataframes[report.name] = pd.concat([df, filtered_dataframe])
            except KeyError:
                dataframes[report.name] = filtered_dataframe
        # save_report(swap_flown_data, report_name)

    if orders_not_flown_to_swap:
        logger.info(f"Orders not found in swap: {', '.join(map(lambda x: x[0], orders_not_flown_to_swap))}")
        report_name_w_ext = f'Report_{datetime.now().strftime("%m_%d_%Y-%H_%M_%S")}.xlsx'
        report_path = generate_xlsx_report(dataframes, report_name_w_ext)
        if report_path.exists():
            logger.info(f"Report generated successfully! {report_path}")
    else:
        logger.info("All orders flown to swap successfully!")


if __name__ == "__main__":

    filter_dates = get_filter_dates_input()
    logger.info(f"Range selected from: {filter_dates.start} - {filter_dates.end}")

    main(filter_dates, save_to_disk=False)
