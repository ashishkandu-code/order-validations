from dataclasses import dataclass

from reports import (
    ReportType,
    Filter
)


REQUIRED_COLUMNS = ('Order_No', 'Order_Delivery_Status', 'Order_Cancellation_Status', 'Package_Type', 'Fulfillment_Mode')
RUN_FOR = ('hotlink prepaid', 'hotlink postpaid', 'maxis postpaid', 'preorder postpaid instore', 'wm prepaid')
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
    'wm prepaid': ReportInfo(**{
        'report_type': ReportType('PREPAID'),
        'filters': [Filter('Order_No', 'contains', ('MOS', ))],
    }),
}
