from dataclasses import dataclass
import os
from pathlib import Path
import re
from bs4 import BeautifulSoup
from requests import HTTPError, Session
from requests.adapters import HTTPAdapter
from requests.compat import urljoin
from dotenv import load_dotenv
from urllib3 import Retry

from loggerfactory import LoggerFactory

load_dotenv(Path().joinpath(os.path.expanduser('~'), '.env'))
logger = LoggerFactory.get_logger(__name__)


BASE_URL = 'http://10.200.50.152:8989'
LOGIN_ENDPOINT = '/user.current.start.page'
INITIALIZATION_ENDPOINT = '/opf.orderdetails'
ORDER_DETAILS = '/meta/default/maxis_opf_support___opfdetails/0000007517'


@dataclass
class WMOrder:
    order_ID: str
    interface_ID: str
    interface_log_ID: str
    event_message: str


class WM(Session):
    """WebMethods Client.

    Constructs a :obj:`requests.Session` for Web methods API requests with
    authorization, base URL, request timeouts, and request retries.

    Args:
        timeout (int, optional): :obj:`TimeoutHTTPAdapter` timeout value. Defaults to 30.
        total (int, optional): :obj:`Retry` total value. Defaults to 4.
        backoff_factor (int, optional): :obj:`Retry` backoff_factor value.
            Defaults to 30.

    Usage::

      from wm_portal import WM

      wm = WM()
    """
    def __init__(self, timeout=30, total=4, backoff_factor=30):
        """
        WM client consutructor.

        Constructs a :obj:`requests.Session` for WM API requests with
        authorization, base URL, request timeouts, and request retries.

        Args:
            timeout (int, optional): :obj:`TimeoutHTTPAdapter` timeout value. Defaults to 30.
            total (int, optional): :obj:`Retry` total value. Defaults to 4.
            backoff_factor (int, optional): :obj:`Retry` backoff_factor value.
                Defaults to 30.
        """
        super().__init__()
        self.headers = {
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Origin': BASE_URL,
            'Pragma': 'no-cache',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
        }

        adapter = TimeoutHTTPAdapter(
            timeout=timeout,
            max_retries=Retry(
                total=total,
                backoff_factor=backoff_factor,
                status_forcelist=[429, 500, 502, 503, 504],
            ),
        )
        self.mount('http://', adapter)
        self.mount('https://', adapter)

        self.login()
        self.initialize()


    def login(self):
        """Perform authentication and store cookies in session."""
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': f'{BASE_URL}/',
        }
        self.headers.update(headers)
        data = {
            'username': os.environ['secretUser'],
            'password': os.environ['wmPassword']
        }
        try:
            response = self.post(
                url=LOGIN_ENDPOINT,
                data=data
            )
            logger.info("WM login successful.")
        except ConnectionError as connection_error:
            logger.error(connection_error.args[0])

    def initialize(self):
        """Initialize the data, headers and parms to fetch order details."""
        self.data = {
            'jsfwmp7517:defaultForm': '',
            'jsfwmp7517:defaultForm:htmlInputText': '',
            'jsfwmp7517:defaultForm:asyncTable__update': '__row0,__row1,__row2,__row3,__row4,__row5',
            'jsfwmp7517:defaultForm:asyncTable__firstByID': '',
            'jsfwmp7517:defaultForm:asyncTable__first': '0',
            'jsfwmp7517:defaultForm:asyncTable__rows': '10',
            'javax.faces.ViewState': '',
            '__forms': 'jsfwmp7517:defaultForm',
            '__fc': 'jsfwmp7517:defaultForm:button',
            '__vf': 'jsfwmp7517:defaultForm',
            'wms.layout': 'tabulaRasa',
            'wms.portlet': '/meta/default/maxis_opf_support___opfdetails/0000007517',
            'wms.hiddenRequest': 'true',
            'wms.shell': 'shell.blank',
            'wms.replaceForNextUrl': 'hiddenRequest=&shell=&layout=&portlet='
        }

        logger.info("Fetching form data jsfwmp7517:defaultForm...")
        response = self.get(INITIALIZATION_ENDPOINT)
        pattern = re.compile(r'var axsrft = "(.*?)";.*?')

        soup = BeautifulSoup(response.content, 'lxml')
        scripts = soup.find_all('script', string=pattern)
        default_form_data = pattern.search(scripts[0].string).group(1)
        logger.info(f"Received: {default_form_data}")
        self.data.update({'jsfwmp7517:defaultForm': default_form_data})

        self.headers.update({
            'Accept': 'text/javascript, text/html, application/xml, text/xml, */*',
            'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Referer': urljoin(BASE_URL, INITIALIZATION_ENDPOINT),
            'X-Prototype-Version': '1.7.1',
            'X-Requested-With': 'XMLHttpRequest',
        })

        self.params = (
            ('wmp_tc', '7517'),
            ('wmp_rt', 'action'),
            ('wmp_tv', '/OpfDetails/default.view'),
            ('__ns', 'wmp7517'),
        )

    def fetch(self, id: str):
        """Fetches order details for a order by its ID."""
        self.data.update({'jsfwmp7517:defaultForm:htmlInputText': id})
        response = self.post(
            ORDER_DETAILS,
            data=self.data,
            params=self.params,
        )
        soup = BeautifulSoup(response.text, 'lxml')
        tbody = soup.find('tbody')
        last_row = tbody.find_all('tr')[-1]
        tds = last_row.find_all('td')
        order_id = tds[2].text
        interface_id = tds[4].text
        order_status = tds[5].text
        msg = tds[6].text
        return WMOrder(order_id, interface_id, order_status, msg)

    def request(self, method, path, *args, **kwargs):
        """
        Override :obj:`Session` request method to add retries.

        Args:
            method (str): Method for the new Request object.
            path (str): Path from host or BASE_URL for the new Request object.

        Returns:
            response: Response
        """
        if not isinstance(path ,str):
            path = "/".join((str(s) for s in path if s))
        path = path.rstrip("/")

        response = super().request(
            method=method,
            url=urljoin(BASE_URL, path),
            *args,
            **kwargs,
        )
        try:
            response.raise_for_status()
        except HTTPError as exception:
            logger.error(exception.args[0])
        return response


class TimeoutHTTPAdapter(HTTPAdapter):
    def __init__(self, timeout, *args, **kwargs):
        """
        TimeoutHTTPAdapter constructor.

        Args:
            timeout (int): How many seconds to wait for the server to send
            data before giving up.
        """
        self.timeout = timeout
        super().__init__(*args, **kwargs)


    def send(self, request, **kwargs):
        """Override :obj:`HTTPAdapter` send method to add a default timeout."""
        timeout = kwargs.get("timeout")
        if timeout is None:
            kwargs["timeout"] = self.timeout

        return super().send(request, **kwargs)
