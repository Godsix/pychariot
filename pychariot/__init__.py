# -*- coding: utf-8 -*-
from .const import (RetureCode, CHR_NULL_HANDLE, CHR_BOOLEAN,
                    CHR_PROTOCOL, CHR_QOS_TEMPLATE_TYPE, CHR_VOIP_CODEC,
                    CHR_VIDEO_CODEC, CHR_DETAIL_LEVEL, CHR_THROUGHPUT_UNITS,
                    CHR_TEST_END, CHR_TEST_HOW_ENDED, CHR_TEST_REPORTING,
                    CHR_TEST_REPORTING_FIREWALL, CHR_TEST_RETRIEVING,
                    CHR_RESULTS, CHR_CFG_PARM,
                    CHR_TRACERT_RUNSTATUS_TYPE, CHR_PAIR_RUNSTATUS_TYPE,
                    CHR_MEASURE_STATS, CHR_PAIR_TYPE, CHR_LICENSE_TYPE,
                    CHR_REPORT_ITEM, CHR_GROUPING_TYPE, CHR_SORT_ORDER)
from .chariot import Chariot, CHARIOT_VERSION, Status
__version__ = '.'.join([str(x) for x in CHARIOT_VERSION])
