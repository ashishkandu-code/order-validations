from swap_portal import SwapOrder
from datetime import datetime, timedelta

from typing import List
from requests import Response

import logging
from helper import dump_json_to_file, write_to_file
from my_logging import log_setup
from reports import (
    Report,
    ReportDownloader,
    ReportType,
    Filter,
)

import enlighten


log_setup()
logger = logging.getLogger(__name__)


REQUIRED_COLUMNS = ('Order_No', 'Order_Delivery_Status', 'Order_Cancellation_Status', 'Package_Type', 'Fulfillment_Mode')
RUN_FOR = ('hotlink prepaid', 'hotlink postpaid', 'maxis postpaid')
RUN_FOR = ('preorder postpaid instore', )


def validate_date(date_text):
    try:
        date_obj = datetime.strptime(date_text, '%d/%m/%Y %H:%M')
    except ValueError:
        raise SystemExit("Incorrect data format, should be DD/MM/YYYY HH:MM")
    else:
        if date_obj > datetime.now():
            raise SystemExit("Date cannot be in future")
        return date_obj


def extract_swap_eligible_orders(report: Report, filters: List[Filter]=[]):
    """
    It displays current report selected columns dataframe and filters order IDs.
    Also renames order IDs starting from either 'HOS' or 'MOS' based on report type.
    """
    if filters:
        for filter in filters:
            report.filter(filter)
        logger.info('Filters applied!')

    logger.info(f"{report.name} Data\n{report.get_columns_filtered_df(REQUIRED_COLUMNS).count()}")
    order_ids = report.dataframe['Order_No'].values
    if report.report_type.planType == "PREPAID":
        swap_orders_ids = [order if order.startswith('MOS') else f"HOS{order.split('A')[0]}" for order in order_ids]
    elif report.report_type.planType == "POSTPAID":
        swap_orders_ids = [order if order.startswith('MOS') else f"MOS{order.split('A')[0]}" for order in order_ids]
    return swap_orders_ids


def swap_filtering(responses: List[Response], orders_list: List[str]):
    """
    Filters the orders in responses whether flown to swap or not.
    """
    responses_from_swap = dict()

    responses_from_swap["not_found"] = []
    responses_from_swap["found"] = []

    for response, order in zip(responses, orders_list):
        try:
            data = response.json()
        except AttributeError as e:
            logger.error(e)
            data = response
        if data['iTotalDisplayRecords'] == 1:
            responses_from_swap["found"].append(order)
        else:
            responses_from_swap["not_found"].append((order, data))
    return responses_from_swap


def save_report(data, report_name):
    try:
        dump_json_to_file(data, f'{report_name}_{datetime.now().strftime("%m_%d_%Y-%H_%M_%S")}.json')
    except Exception as e:
        logger.exception(e)
        write_to_file(data, f'{report_name}_error')


def main(reports_info:dict, downloader: ReportDownloader, swap_delivery: SwapOrder):

    orders_not_flown_to_swap = []
    for report_name in RUN_FOR:
        selected_report: dict = reports_info[report_name]
        report_type = selected_report.get('report_type')
        report_filter = selected_report.get('filters')

        raw_content = downloader.get_report(report_type)
        report = Report(raw_content, report_type)
        orders_to_check = extract_swap_eligible_orders(report, report_filter)

        total_orders_count = len(orders_to_check)
        if total_orders_count == 0:
            continue
        manager = enlighten.get_manager()
        pbar = manager.counter(total=total_orders_count, desc=report_name)

        responses = []
        for order_id in orders_to_check:
            response = swap_delivery.get_order(order_id)
            if not response:
                responses.append({'iTotalDisplayRecords': -1})
            else:
                responses.append(response)
            pbar.update(force=True)

        swap_flown_data = swap_filtering(responses, orders_to_check)

        orders_not_found = swap_flown_data['not_found']
        if orders_not_found:
            orders_not_flown_to_swap.extend(list(map(lambda order_tuple: order_tuple[0], orders_not_found)))
        save_report(swap_flown_data, report_name)
    if orders_not_flown_to_swap:
        print('\n\nOrders not found in swap:', orders_not_flown_to_swap)


if __name__ == "__main__":

    reports_info = {
        'hotlink prepaid': {
            'report_type': ReportType('PREPAID'),
            'filters': [],
        },
        'hotlink postpaid': {
            'report_type': ReportType('POSTPAID', 'hotlink postpaid'),
            'filters': [
                Filter('Fulfillment_Mode', 'exists', ('Standard Delivery', )),
                Filter('Order_Delivery_Status', 'notExists', ('fulfilled', )),
            ],
        },
        'maxis postpaid': {
            'report_type': ReportType('POSTPAID', 'maxis postpaid'),
            'filters': [
                Filter('Fulfillment_Mode', 'exists', ('Standard Delivery', )),
                Filter('Order_Delivery_Status', 'notExists', ('fulfilled', )),
            ],
        },
        'preorder postpaid instore': {
            'report_type': ReportType('POSTPAID', 'maxis postpaid'),
            'filters': [
                Filter('Fulfillment_Mode', 'exists', ('In-Store Pickup', )),
                Filter('Package_Type', 'exists', ('Device + Plan', )),
                Filter('Order_Type', 'exists', ('Pre Order', )),
            ],
        },
    }

    print("[!] Use 24 Hours format to give time.")
    filter_date_from = input("Enter starting datetime [DD/MM/YYYY HH:MM] (Default Yesterday): ")
    if filter_date_from == "":
        filter_date_from = datetime.now() - timedelta(days=1)
        filter_date_from = filter_date_from.strftime('%d/%m/%Y 00:00')
        from_date_comp_obj = datetime.strptime(filter_date_from, '%d/%m/%Y %H:%M')
    else:
        from_date_comp_obj = validate_date(filter_date_from)

    filter_date_to = input("Enter ending datetime [DD/MM/YYYY HH:MM] (Default to now): ")
    if filter_date_to == "":
        filter_date_to = datetime.now().strftime('%d/%m/%Y %H:%M')
        to_date_comp_obj = datetime.strptime(filter_date_to, '%d/%m/%Y %H:%M')
    else:
        to_date_comp_obj = validate_date(filter_date_to)
    logger.info(f"Range selected from: {filter_date_from} - {filter_date_to}")


    if from_date_comp_obj > to_date_comp_obj:
        raise SystemExit("End datetime cannot be before start datetime!")

    downloader = ReportDownloader(filter_date_from, filter_date_to, True)
    swap_delivery = SwapOrder()

    main(reports_info, downloader, swap_delivery)
