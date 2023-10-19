from requests import Session
from requests.exceptions import HTTPError, ConnectionError, ReadTimeout, SSLError
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
from my_logging import log_setup
import logging
import time

from dotenv import load_dotenv
from os import getenv

from helper import write_to_file, current_milli_time

log_setup()
load_dotenv()

logger = logging.getLogger(__name__)

retry_strategy = Retry(
    total=4,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
)

adapter = HTTPAdapter(max_retries=retry_strategy)

wait = 30 # seconds
timeout_seconds = 120

class Swap(Session):
    """Returns a swap authenticated session."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mount('http://', adapter)
        self.mount('https://', adapter)
        self.headers ={
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://delivery-maxis.swap-asia.com',
            'Pragma': 'no-cache',
            'Referer': 'https://delivery-maxis.swap-asia.com/User/Login',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }
        self.load_or_update_headers(self.headers)
        self.user_login_data = {
                'UserName': getenv('swapUserName'),
                'Password': getenv('Password'),
                'RememberMe': 'false'
            }
        self.login()
        self.initialize()

    def load_or_update_headers(self, headers: dict):
        self.headers.update(headers)

    def login(self):
        try:
            res = self.post('https://delivery-maxis.swap-asia.com/User/Login', data=self.user_login_data, timeout=timeout_seconds)
            logger.info(f"{res.request.method} {res.url} [status:{res.status_code} request:{res.elapsed.total_seconds():.3f}s]")
            res.raise_for_status()
            if 'Login' in res.url:
                logger.error('Could not authenticate!')
                raise SystemExit('Login failed')
        except HTTPError as http_error:
            logger.error(http_error.args[0])
        except ConnectionError as conn_error:
            logger.error(conn_error.args[0])
        except Exception as e:
            logger.exception(e)
        else:
            if not res.ok:
                write_to_file(res.text, 'login_error.html')
                logger.info('Failed response written to file')
                raise SystemExit('Could not login.')
            else:
                logger.info('Login success')

    def initialize(self):
        headers = {'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Referer': 'https://delivery-maxis.swap-asia.com/Delivery',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

        params = {
            '_': current_milli_time(),
        }
        try:
            response = self.get('https://delivery-maxis.swap-asia.com/Delivery/ShowData', params=params, headers=headers, timeout=timeout_seconds)
            logger.info(f"{response.request.method} {response.url} [status:{response.status_code} request:{response.elapsed.total_seconds():.3f}s]")
            response.raise_for_status()
        except HTTPError as http_error:
            logger.error(http_error.args[0])
        except ConnectionError as conn_error:
            logger.error(conn_error.args[0])
        except ReadTimeout as e:
            logger.exception(e)
        else:
            logger.info('Initialization is success!')


class SwapDeliveryAuthenticatedPage:
    """Prepares Swap Delivery page to check for orders."""
    def __init__(self):
        self.headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': 'https://delivery-maxis.swap-asia.com/Delivery',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'X-Requested-With': 'XMLHttpRequest',
        }
        self.params = {
            'sEcho': '2',
            'iColumns': '19',
            'sColumns': ',,,,,,,,,,,,,,,,,,',
            'iDisplayStart': '0',
            'iDisplayLength': '10',
            'mDataProp_0': '0',
            'sSearch_0': '',
            'bRegex_0': 'false',
            'bSearchable_0': 'true',
            'bSortable_0': 'false',
            'mDataProp_1': '1',
            'sSearch_1': '',
            'bRegex_1': 'false',
            'bSearchable_1': 'true',
            'bSortable_1': 'true',
            'mDataProp_2': '2',
            'sSearch_2': '',
            'bRegex_2': 'false',
            'bSearchable_2': 'true',
            'bSortable_2': 'true',
            'mDataProp_3': '3',
            'sSearch_3': '',
            'bRegex_3': 'false',
            'bSearchable_3': 'true',
            'bSortable_3': 'true',
            'mDataProp_4': '4',
            'sSearch_4': '',
            'bRegex_4': 'false',
            'bSearchable_4': 'true',
            'bSortable_4': 'true',
            'mDataProp_5': '5',
            'sSearch_5': '',
            'bRegex_5': 'false',
            'bSearchable_5': 'true',
            'bSortable_5': 'true',
            'mDataProp_6': '6',
            'sSearch_6': '',
            'bRegex_6': 'false',
            'bSearchable_6': 'true',
            'bSortable_6': 'true',
            'mDataProp_7': '7',
            'sSearch_7': '',
            'bRegex_7': 'false',
            'bSearchable_7': 'true',
            'bSortable_7': 'true',
            'mDataProp_8': '8',
            'sSearch_8': '',
            'bRegex_8': 'false',
            'bSearchable_8': 'true',
            'bSortable_8': 'true',
            'mDataProp_9': '9',
            'sSearch_9': '',
            'bRegex_9': 'false',
            'bSearchable_9': 'true',
            'bSortable_9': 'true',
            'mDataProp_10': '10',
            'sSearch_10': '',
            'bRegex_10': 'false',
            'bSearchable_10': 'true',
            'bSortable_10': 'true',
            'mDataProp_11': '11',
            'sSearch_11': '',
            'bRegex_11': 'false',
            'bSearchable_11': 'true',
            'bSortable_11': 'true',
            'mDataProp_12': '12',
            'sSearch_12': '',
            'bRegex_12': 'false',
            'bSearchable_12': 'true',
            'bSortable_12': 'false',
            'mDataProp_13': '13',
            'sSearch_13': '',
            'bRegex_13': 'false',
            'bSearchable_13': 'true',
            'bSortable_13': 'false',
            'mDataProp_14': '14',
            'sSearch_14': '',
            'bRegex_14': 'false',
            'bSearchable_14': 'true',
            'bSortable_14': 'true',
            'mDataProp_15': '15',
            'sSearch_15': '',
            'bRegex_15': 'false',
            'bSearchable_15': 'true',
            'bSortable_15': 'true',
            'mDataProp_16': '16',
            'sSearch_16': '',
            'bRegex_16': 'false',
            'bSearchable_16': 'true',
            'bSortable_16': 'true',
            'mDataProp_17': '17',
            'sSearch_17': '',
            'bRegex_17': 'false',
            'bSearchable_17': 'true',
            'bSortable_17': 'true',
            'mDataProp_18': '18',
            'sSearch_18': '',
            'bRegex_18': 'false',
            'bSearchable_18': 'true',
            'bSortable_18': 'true',
            'iSortCol_0': '0',
            'sSortDir_0': 'asc',
            'sSearch': "",
            'bRegex': 'false',
            'iSortingCols': '1',
            'Category': '1',
            'WildCard': '0',
        }

        self.swap_session = Swap()

        # Set necessary cookies and headers for fetching
        self.swap_session.load_or_update_headers(self.headers)
        self.swap_session.cookies['CLIENT_TIMEZONE'] = '-480'

    def get_order(self, order_id: str):
        """Returns the order response from swap portal."""
        self.params.update({'sSearch': order_id})
        error_msg = f'Could not get details for {order_id}'
        try:
            response = self.swap_session.get(
                'https://delivery-maxis.swap-asia.com/Delivery/AjaxHandler',
                params=self.params,
                timeout=timeout_seconds,
            )
            logger.info(f"{response.request.method} /{order_id} [status:{response.status_code} request:{response.elapsed.total_seconds():.3f}s]")
            response.raise_for_status()
            return response
        # REMOVE: for debug catching all exceptions
        except Exception as e:
            logger.exception(e)
        except HTTPError:
            logger.error(error_msg)
        except ConnectionError:
            logger.error(error_msg)
        except ReadTimeout:
            logger.error(error_msg)
        return None
