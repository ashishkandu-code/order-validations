from swap_order_validation import get_default_filter_dates, swap_order_processing
from my_logging import log_setup
import logging

log_setup()
logger = logging.getLogger(__name__)

filter_dates = get_default_filter_dates()

if __name__ == '__main__':
    logger.info(f"Range selected from: {filter_dates.start} - {filter_dates.end}")
    swap_order_processing(filter_dates=filter_dates, save_fetched_report=False)
