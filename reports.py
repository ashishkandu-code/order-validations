import requests
from requests.exceptions import HTTPError, ConnectionError
from dataclasses import dataclass
from typing import Optional, Tuple, Literal

import pandas as pd
import io
from datetime import datetime

from my_logging import log_setup
import logging

from helper import write_bytes_to_file

log_setup()
logger = logging.getLogger(__name__)


@dataclass
class ReportType:
    planType: Literal['PREPAID', 'POSTPAID']
    ratePlan: Optional[Literal['hotlink postpaid', 'maxis postpaid']] = ''


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

    def __init__(self, filter_date_from: str, filter_date_to: str, save_to_disk=False):
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
        self.save_to_disk = save_to_disk
        self.created_date = datetime.now().strftime("%m_%d_%Y-%H_%M_%S")

    def set_headers_filters(self, filterplantype, filterrateplan):
        """This will update the headers to inculde next plantype and rateplan."""
        self.headers.update({
            'filterplantype': filterplantype,
            'filterrateplan': filterrateplan,
        })

    def get_file_name(self, report_type: ReportType):
        """Returns a file name for the report."""
        if report_type.planType == 'PREPAID':
            return f'prepaid_report{self.created_date}.xlsx'
        elif report_type.planType == 'POSTPAID':
            if report_type.ratePlan == 'hotlink postpaid':
                return f'hotlink_postpaid_report{self.created_date}.xlsx'
            elif report_type.ratePlan == 'maxis postpaid':
                return f'maxis_postpaid_report{self.created_date}.xlsx'
        return f'{report_type.planType}-{report_type.ratePlan}{self.created_date}.xlsx'

    def get_report(self, report_type: ReportType):
        """Pulls the report from cms and returns in bytes."""

        plantype = report_type.planType
        rateplan = report_type.ratePlan
        self.set_headers_filters(plantype, rateplan)
        report_name = rateplan if rateplan else plantype
        logger.info(f"[+] Fetching {report_name} report...")
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
            filename = self.get_file_name(report_type=report_type)
            write_bytes_to_file(response.content, filename)
        return response.content


class Report:
    def __init__(self, content: bytes, report_type: ReportType) -> None:
        self.content = content
        self.dataframe = excel_buffer_to_dataframe(self.content)
        self.report_type = report_type
        self.name = self.generate_name()

    def __enter__(self):
        return self

    def generate_name(self):
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

    def get_columns_filtered_df(self, columns: Tuple[str]) -> pd.DataFrame:
        return self.dataframe.loc[:, columns]
