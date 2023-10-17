from copy import copy
import requests
from requests.exceptions import HTTPError, ConnectionError
from dataclasses import dataclass
from typing import Optional, Tuple, Literal
from collections.abc import Iterable

import pandas as pd
import io
from datetime import datetime
from filter_dates import FilterDates

from my_logging import log_setup
import logging

from helper import write_bytes_to_file

log_setup()
logger = logging.getLogger(__name__)


@dataclass
class ReportType:
    planType: Literal['PREPAID', 'POSTPAID']
    ratePlan: Optional[Literal['hotlink postpaid', 'maxis postpaid']] = ''

    def __eq__(self, other):
        return self.planType + self.ratePlan == other.planType + other.ratePlan


@dataclass
class Filter:
    columnName: str
    methodName: Literal['contains', 'exists', 'notExists']
    filter_texts: Tuple[str]


def excel_buffer_to_dataframe(buffer) -> pd.DataFrame:
    """Converts an excel buffer to a pandas dataframe."""
    with io.BytesIO(buffer) as file_handler:
        df: pd.DataFrame = pd.io.excel.read_excel(file_handler)
    return df


class ReportDownloader:
    """Helps to download the report from cms."""

    def __init__(self, filter_date_from: str, filter_date_to: str):
        self.url = 'https://api-digital2.isddc.men.maxis.com.my/ecommerce/api/v4.0/cms/order/masterreport'
        self.headers = {
            'authority': 'api-digital2.isddc.men.maxis.com.my',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'no-cache',
            'filterchannel': '',
            'pragma': 'no-cache',
            'referer': 'https://api-digital2.isddc.men.maxis.com.my/cscockpit/ui/main/export',
            'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        }
        self.headers.update({
            'filterdatefrom': filter_date_from,
            'filterdateto': filter_date_to
        })
        self.created_date = datetime.now().strftime("%m_%d_%Y-%H_%M_%S")

    def set_headers_filters(self, filterplantype, filterrateplan):
        """This will update the headers to inculde next plantype and rateplan."""
        self.headers.update({
            'filterplantype': filterplantype,
            'filterrateplan': filterrateplan,
        })


class Report(ReportDownloader):
    def __init__(self, report_type: ReportType, filter_dates: FilterDates, save_to_disk: bool) -> None:
        super().__init__(
            filter_date_from=filter_dates.start,
            filter_date_to=filter_dates.end,
        )
        self.report_type = report_type
        self.save_to_disk = save_to_disk
        self.name = self.generate_report_title()
        self.content = self.download_report()
        self.dataframe = excel_buffer_to_dataframe(self.content)


    def __enter__(self):
        return self

    def generate_report_title(self):
        if self.report_type.planType == 'PREPAID':
            return 'Hotlink Prepaid Report'
        if self.report_type.planType == 'POSTPAID':
            if self.report_type.ratePlan == 'hotlink postpaid':
                return 'Hotlink Postpaid Report'
            elif self.report_type.ratePlan == 'maxis postpaid':
                return 'Maxis Postpaid Report'
            else:
                raise SystemExit(f"Unknown ratePlan: {self.report_type.ratePlan}")
        else:
            raise SystemExit(f"Unknown plan type {self.report_type.planType}")

    def get_file_name(self):
        """Returns a file name for the report."""
        if self.report_type.planType == 'PREPAID':
            return f'prepaid_report{self.created_date}.xlsx'
        elif self.report_type.planType == 'POSTPAID':
            if self.report_type.ratePlan == 'hotlink postpaid':
                return f'hotlink_postpaid_report{self.created_date}.xlsx'
            elif self.report_type.ratePlan == 'maxis postpaid':
                return f'maxis_postpaid_report{self.created_date}.xlsx'
        return f'{self.report_type.planType}-{self.report_type.ratePlan}{self.created_date}.xlsx'

    def filter(self, filter: Filter):
        """
        Filter dataframe by given filter.
        Supports two methods "contains" and "exists".
        """
        if filter.methodName == 'contains':
            self.dataframe = self.dataframe[self.dataframe[filter.columnName].str.contains(filter.filter_texts[0])]
        elif filter.methodName == 'exists':
            self.dataframe = self.dataframe[self.dataframe[filter.columnName].isin(filter.filter_texts)]
        elif filter.methodName == 'notExists':
            self.dataframe = self.dataframe[~self.dataframe[filter.columnName].isin(filter.filter_texts)]
        else:
            logger.warning(f'Mehtod {filter.methodName} not supported.')

    def get_columns_reduced_dataframe(self, columns: Tuple[str]) -> pd.DataFrame:
        return self.dataframe.loc[:, columns]

    def get_filtered_dataframe_by_orderNos(self, orders: Iterable[str]) -> pd.DataFrame:
        return self.dataframe.loc[self.dataframe['Order_No'].isin(orders)]

    def download_report(self):
        """Pulls the report from cms and returns in bytes."""

        plantype = self.report_type.planType
        rateplan = self.report_type.ratePlan
        self.set_headers_filters(plantype, rateplan)
        report_name = self.name
        logger.info(f"[+] Fetching {report_name} ...")
        try:
            response = requests.get(
                    url=self.url,
                    headers=self.headers,
            )
            logger.info(f"{response.request.method} {response.url} [status:{response.status_code} request:{response.elapsed.total_seconds():.3f}s]")
            response.raise_for_status()
        except HTTPError as error:
            raise SystemExit(error.args[0])
        except ConnectionError as connection_error:
            raise SystemExit(connection_error.args)
        if self.save_to_disk:
            filename = self.get_file_name()
            write_bytes_to_file(response.content, filename)
        return response.content

cached_reports: list[Report] = []

def get_report(report_type: ReportType, filter_dates: FilterDates, save_to_disk: bool):
    """Return report for a given report type and also cache for future use"""
    for report in cached_reports:
        if report.report_type == report_type:
            logger.info('Report found in cache!')
            return report
    report = Report(report_type, filter_dates, save_to_disk)
    cached_reports.append(copy(report))
    return report
