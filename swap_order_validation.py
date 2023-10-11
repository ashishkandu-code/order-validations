from filter_dates import FilterDates
from swap_portal import SwapDeliveryAuthenticatedPage
from datetime import datetime
import pandas as pd

from requests import Response

import logging
from helper import generate_xlsx_report
from my_logging import log_setup
from reports import (
    Report,
    Filter,
    get_report,
)

import enlighten

from swap_validation_config import REPORTS_INFO, REQUIRED_COLUMNS, RUN_FOR


log_setup()
logger = logging.getLogger(__name__)


def extract_swap_eligible_orders(report: Report, filters: list[Filter]=[]) -> list[tuple[str, str]]:
    """
    It applies filters if filters is not empty and returns list of tuples as following:

    (modified_order_id, original_order_id)

    where 'modified_order_id' is obtained by renaming 'original_order_id' to start from 'HOS' or
    'MOS' based on report type and remove suffix 'A'.
    It also logs the current dataframe with selected columns
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


def orders_flow_filtering(responses: list[Response], orders_list: list[tuple[str, str]]) -> dict[str, list[tuple[str, str]]]:
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


def swap_order_processing(filter_dates: FilterDates, save_fetched_reports: bool):

    orders_not_flown_to_swap: list[tuple[str, str]] = []
    dataframes: dict[str, pd.DataFrame] = {}
    swap_delivery_page = SwapDeliveryAuthenticatedPage()

    for report_name in RUN_FOR:
        selected_report_info = REPORTS_INFO[report_name]
        report_type = selected_report_info.report_type
        report_filters = selected_report_info.filters

        report = get_report(report_type, filter_dates, save_fetched_reports)
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

        swap_flown_data = orders_flow_filtering(responses, orders_to_check)

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
        # save_json_data(swap_flown_data, report_name)

    if orders_not_flown_to_swap:
        logger.info(f"Orders not found in swap: {', '.join(map(lambda x: x[0], orders_not_flown_to_swap))}")
        report_name_w_ext = f'Report_{datetime.now().strftime("%m_%d_%Y-%H_%M_%S")}.xlsx'
        report_path = generate_xlsx_report(dataframes, report_name_w_ext)
        if report_path.exists():
            logger.info(f"Report generated successfully! {report_path}")
    else:
        logger.info("All orders flown to swap successfully!")
