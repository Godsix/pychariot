# -*- coding: utf-8 -*-

from .const import (RetureCode, CHR_PROTOCOL, CHR_TEST_END, CHR_TEST_HOW_ENDED,
                    CHR_RESULTS)
from .chariot import Chariot, CHARIOT_VERSION
__version__ = '.'.join([str(x) for x in CHARIOT_VERSION])