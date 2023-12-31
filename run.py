import argparse
from filter_dates import get_default_filter_dates, get_filter_dates_input

from order_validation import order_processing
from loggerfactory import LoggerFactory

logger = LoggerFactory.get_logger(__name__)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Commerce Order Validations'
    )
    parser.add_argument('--custom-dates', dest='custom_dates', required=False,
                        action='store_true', help='option to input custom dates for validations')
    args = parser.parse_args()
    custom_dates = args.custom_dates

    def check_args(custom_dates=custom_dates):
        if custom_dates:
            filter_dates = get_filter_dates_input()
        else:
            filter_dates = get_default_filter_dates()
        return filter_dates

    filter_dates = check_args()

    logger.info(f"Range selected from: {filter_dates.start} - {filter_dates.end}")
    order_processing(filter_dates=filter_dates, save_fetched_reports=False)
