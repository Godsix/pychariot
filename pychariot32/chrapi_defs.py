# -*- coding: utf-8 -*-
"""
Created on Fri Feb 26 14:42:01 2021

This file contains the constants, typedefs and function prototypes for
Ixia's Chariot application programming interface.

/***************************************************************
 *
 *  Ixia IxChariot API                       File: chrapi.h
 *
 *  For more information, contact:
 *
 *  Ixia
 *  26601 W. Agoura Rd.
 *  Calabasas, CA 91302 USA
 *  Web:   http://www.ixiacom.com
 *  Phone: 818-871-1800
 *  Fax:   818-871-1805
 *
 *  General Information:
 *    e-mail: info@ixiacom.com
 *
 *  Technical Support:
 *    e-mail: support@ixiacom.com
 *
 *  Copyright (C) Ixia, 2003-2007.
 *  Copyright (C) NetIQ Corporation, 1995-2000.
 *  All rights reserved.
 *
 ***************************************************************/
@author: haoyue
"""
# pylint: disable=too-few-public-methods
from datetime import datetime
from ctypes import Structure, POINTER, c_ssize_t, c_int, c_char, c_ubyte
from .voip_defs import (
    IX_VOIP_CODEC_NONE, IX_VOIP_CODEC_G711u, IX_VOIP_CODEC_G723_1A,
    IX_VOIP_CODEC_G723_1M, IX_VOIP_CODEC_G729, IX_VOIP_CODEC_G711a,
    IX_VOIP_CODEC_G726, IX_VOIP_CODEC_AMR_NB_4_75, IX_VOIP_CODEC_AMR_NB_5_15,
    IX_VOIP_CODEC_AMR_NB_5_9, IX_VOIP_CODEC_AMR_NB_6_7,
    IX_VOIP_CODEC_AMR_NB_7_4, IX_VOIP_CODEC_AMR_NB_7_95,
    IX_VOIP_CODEC_AMR_NB_10_2, IX_VOIP_CODEC_AMR_NB_12_2,
    IX_VOIP_CODEC_AMR_WB_6_6, IX_VOIP_CODEC_AMR_WB_8_85,
    IX_VOIP_CODEC_AMR_WB_12_65, IX_VOIP_CODEC_AMR_WB_14_25,
    IX_VOIP_CODEC_AMR_WB_15_85, IX_VOIP_CODEC_AMR_WB_18_25,
    IX_VOIP_CODEC_AMR_WB_19_85, IX_VOIP_CODEC_AMR_WB_23_05,
    IX_VOIP_CODEC_AMR_WB_23_85)

### Chariot API return codes
CHR_RC_BASE                                                 = 100
CHR_OK                                                      = 0
CHR_HANDLE_INVALID                                          = CHR_RC_BASE + 1
CHR_STRING_TOO_LONG                                         = CHR_RC_BASE + 2
CHR_POINTER_INVALID                                         = CHR_RC_BASE + 3
CHR_NO_SUCH_OBJECT                                          = CHR_RC_BASE + 4
CHR_TEST_NOT_RUN                                            = CHR_RC_BASE + 5
CHR_TEST_RUNNING                                            = CHR_RC_BASE + 6
CHR_OBJECT_IN_USE                                           = CHR_RC_BASE + 7
CHR_OPERATION_FAILED                                        = CHR_RC_BASE + 8
CHR_NO_TEST_FILE                                            = CHR_RC_BASE + 9
CHR_RESULTS_NOT_CLEARED                                     = CHR_RC_BASE + 10
CHR_PAIR_LIMIT_EXCEEDED                                     = CHR_RC_BASE + 11
CHR_OBJECT_INVALID                                          = CHR_RC_BASE + 12
CHR_API_NOT_INITIALIZED                                     = CHR_RC_BASE + 13
CHR_NO_RESULTS                                              = CHR_RC_BASE + 14
CHR_VALUE_INVALID                                           = CHR_RC_BASE + 15
CHR_NO_SUCH_VALUE                                           = CHR_RC_BASE + 16
CHR_NO_SCRIPT_IN_USE                                        = CHR_RC_BASE + 17
CHR_TIMED_OUT                                               = CHR_RC_BASE + 18
CHR_BUFFER_TOO_SMALL                                        = CHR_RC_BASE + 19
CHR_NO_MEMORY                                               = CHR_RC_BASE + 20
CHR_PGM_INTERNAL_ERROR                                      = CHR_RC_BASE + 21
CHR_TRACERT_NOT_RUN                                         = CHR_RC_BASE + 22
CHR_TRACERT_RUNNING                                         = CHR_RC_BASE + 23
CHR_NOT_SUPPORTED                                           = CHR_RC_BASE + 24
CHR_NO_CODEC_IN_USE                                         = CHR_RC_BASE + 25
CHR_NOT_LICENSED                                            = CHR_RC_BASE + 26
CHR_SCRIPT_TOO_LARGE                                        = CHR_RC_BASE + 27
CHR_LICENSE_HAS_EXPIRED                                     = CHR_RC_BASE + 28
CHR_NO_NETWORK_CONFIGURATION                                = CHR_RC_BASE + 29
CHR_INVALID_NETWORK_CONFIGURATION                           = CHR_RC_BASE + 30
CHR_ERROR_ACCESSING_TESTSERVER_SESSION                      = CHR_RC_BASE + 31
CHR_FUNCTION_NOT_SUPPORTED                                  = CHR_RC_BASE + 32
CHR_TEST_NOT_SAVED                                          = CHR_RC_BASE + 33
CHR_LICENSE_WILL_EXPIRE                                     = CHR_RC_BASE + 34
CHR_APP_GROUP_NOT_VALIDATED                                 = CHR_RC_BASE + 35
CHR_APP_GROUP_INVALID                                       = CHR_RC_BASE + 36
CHR_APP_GROUP_DUPLICATE_NAME                                = CHR_RC_BASE + 37
CHR_PAYLOAD_FILE_TOO_LARGE                                  = CHR_RC_BASE + 38
CHR_NO_APPLIFIER_CONFIGURATION                              = CHR_RC_BASE + 39
CHR_CHANNEL_DUPLICATE_NAME                                  = CHR_RC_BASE + 40
CHR_RECEIVER_DUPLICATE_NAME                                 = CHR_RC_BASE + 41
CHR_IPTV_INVALID                                            = CHR_RC_BASE + 42
CHR_DUPLICATE_NAME                                          = CHR_RC_BASE + 43
CHR_LICENSE_ALREADY_BORROWED                                = CHR_RC_BASE + 44
CHR_FLOATING_LICENSE_IN_USE                                 = CHR_RC_BASE + 45
CHR_NO_MULTISESSION_LICENSE                                 = CHR_RC_BASE + 46
CHR_RAVE_SINGLE_RUNNING                                     = CHR_RC_BASE + 47
CHR_RAVE_MULTI_RUNNING                                      = CHR_RC_BASE + 48

### String buffer maximum sizes (including a terminating '\0')
CHR_MAX_DIR_PATH                                            = 301
CHR_MAX_FILENAME                                            = 301
CHR_MAX_FILE_PATH                                           = CHR_MAX_DIR_PATH + CHR_MAX_FILENAME
CHR_MAX_EMBEDDED_PAYLOAD_SIZE                               = 27904
CHR_MAX_ERROR_INFO                                          = 4096
CHR_MAX_PAIR_COMMENT                                        = 65
CHR_MAX_ADDR                                                = 65
CHR_MAX_MULTICAST_ADDR                                      = 16
CHR_MAX_QOS_NAME                                            = 65
CHR_MAX_APPL_SCRIPT_NAME                                    = 65
CHR_MAX_GROUP_NAME                                          = 65
CHR_MAX_VERSION                                             = 32
CHR_MAX_RETURN_MSG                                          = 256
CHR_MAX_SCRIPT_VARIABLE_NAME                                = 25
CHR_MAX_SCRIPT_VARIABLE_VALUE                               = 65
CHR_MAX_CFG_PARM                                            = 512
CHR_MAX_ADDR_STRING                                         = CHR_MAX_ADDR
CHR_BSSID_SIZE                                              = 18
CHR_MAX_APP_GROUP_NAME                                      = 25
CHR_MAX_APP_GROUP_COMMENT                                   = 129
CHR_MAX_APP_GROUP_EVENT_NAME                                = 25
CHR_MAX_APP_GROUP_EVENT_COMMENT                             = 129
CHR_MAX_CHANNEL_NAME                                        = 33
CHR_MAX_RECEIVER_NAME                                       = 33
CHR_MAX_CHANNEL_COMMENT                                     = 65
CHR_MAX_RECEIVER_COMMENT                                    = 65
CHR_SOCKET_BUFFER_DEFAULT                                   = 2147483647


CHR_ADDR_STRING = c_char * CHR_MAX_ADDR_STRING


###
CHR_NULL_HANDLE                                             = 0

### CHR_BOOLEAN
CHR_TRUE                                                    = 1
CHR_FALSE                                                   = 0

###
CHR_INFINITE                                                = 0xffffffff

### Protocol
# CHR_PROTOCOL
CHR_PROTOCOL_APPC_NOT_SUPPORTED                             = 1 # APPC is no longer supported
CHR_PROTOCOL_TCP                                            = 2
CHR_PROTOCOL_IPX                                            = 3
CHR_PROTOCOL_SPX                                            = 4
CHR_PROTOCOL_UDP                                            = 5
CHR_PROTOCOL_RTP                                            = 6
CHR_PROTOCOL_TCP6                                           = 7
CHR_PROTOCOL_UDP6                                           = 8
CHR_PROTOCOL_RTP6                                           = 9

### QoS template types
# CHR_QOS_TEMPLATE_TYPE
CHR_QOS_TEMPLATE_TOS_BIT_MASK                               = 1
CHR_QOS_TEMPLATE_DIFFSERV                                   = 2
CHR_QOS_TEMPLATE_L2_PRIORITY                                = 3

### VoIP Codecs -- map to CHR defs
# IX_VOIP_CODEC
CHR_VOIP_CODEC_NONE                                         = IX_VOIP_CODEC_NONE
CHR_VOIP_CODEC_G711u                                        = IX_VOIP_CODEC_G711u
CHR_VOIP_CODEC_G723_1A                                      = IX_VOIP_CODEC_G723_1A
CHR_VOIP_CODEC_G723_1M                                      = IX_VOIP_CODEC_G723_1M
CHR_VOIP_CODEC_G729                                         = IX_VOIP_CODEC_G729
CHR_VOIP_CODEC_G711a                                        = IX_VOIP_CODEC_G711a
CHR_VOIP_CODEC_G726                                         = IX_VOIP_CODEC_G726
CHR_VOIP_CODEC_AMR_NB_4_75                                  = IX_VOIP_CODEC_AMR_NB_4_75
CHR_VOIP_CODEC_AMR_NB_5_15                                  = IX_VOIP_CODEC_AMR_NB_5_15
CHR_VOIP_CODEC_AMR_NB_5_9                                   = IX_VOIP_CODEC_AMR_NB_5_9
CHR_VOIP_CODEC_AMR_NB_6_7                                   = IX_VOIP_CODEC_AMR_NB_6_7
CHR_VOIP_CODEC_AMR_NB_7_4                                   = IX_VOIP_CODEC_AMR_NB_7_4
CHR_VOIP_CODEC_AMR_NB_7_95                                  = IX_VOIP_CODEC_AMR_NB_7_95
CHR_VOIP_CODEC_AMR_NB_10_2                                  = IX_VOIP_CODEC_AMR_NB_10_2
CHR_VOIP_CODEC_AMR_NB_12_2                                  = IX_VOIP_CODEC_AMR_NB_12_2
CHR_VOIP_CODEC_AMR_WB_6_6                                   = IX_VOIP_CODEC_AMR_WB_6_6
CHR_VOIP_CODEC_AMR_WB_8_85                                  = IX_VOIP_CODEC_AMR_WB_8_85
CHR_VOIP_CODEC_AMR_WB_12_65                                 = IX_VOIP_CODEC_AMR_WB_12_65
CHR_VOIP_CODEC_AMR_WB_14_25                                 = IX_VOIP_CODEC_AMR_WB_14_25
CHR_VOIP_CODEC_AMR_WB_15_85                                 = IX_VOIP_CODEC_AMR_WB_15_85
CHR_VOIP_CODEC_AMR_WB_18_25                                 = IX_VOIP_CODEC_AMR_WB_18_25
CHR_VOIP_CODEC_AMR_WB_19_85                                 = IX_VOIP_CODEC_AMR_WB_19_85
CHR_VOIP_CODEC_AMR_WB_23_05                                 = IX_VOIP_CODEC_AMR_WB_23_05
CHR_VOIP_CODEC_AMR_WB_23_85                                 = IX_VOIP_CODEC_AMR_WB_23_85

### Video Codecs
# CHR_VIDEO_CODEC
CHR_VIDEO_CODEC_NONE                                        = 1
CHR_VIDEO_CODEC_MPEG2                                       = 2
CHR_VIDEO_CODEC_CUSTOM                                      = 3

### Port Number
CHR_PORT_AUTO                                               = 0

### Error Information Detail Level
# CHR_DETAIL_LEVEL
CHR_DETAIL_LEVEL_NONE                                       = 0x0000
CHR_DETAIL_LEVEL_PRIMARY                                    = 0x00a3
CHR_DETAIL_LEVEL_ADVANCED                                   = 0x0014 | CHR_DETAIL_LEVEL_PRIMARY
CHR_DETAIL_LEVEL_ALL                                        = 0x0148 | CHR_DETAIL_LEVEL_ADVANCED

### Throughput Units
# CHR_THROUGHPUT_UNITS
CHR_THROUGHPUT_UNITS_KB                                     = 1
CHR_THROUGHPUT_UNITS_kB                                     = 2
CHR_THROUGHPUT_UNITS_Kb                                     = 3
CHR_THROUGHPUT_UNITS_kb                                     = 4
CHR_THROUGHPUT_UNITS_Mb                                     = 5
CHR_THROUGHPUT_UNITS_Gb                                     = 6

### When To End Test
# CHR_TEST_END
CHR_TEST_END_WHEN_FIRST_COMPLETES                           = 1
CHR_TEST_END_WHEN_ALL_COMPLETE                              = 2
CHR_TEST_END_AFTER_FIXED_DURATION                           = 3

### How Test Ended
# CHR_TEST_HOW_ENDED
CHR_TEST_HOW_ENDED_USER_STOPPED                             = 1
CHR_TEST_HOW_ENDED_ERROR                                    = 2
CHR_TEST_HOW_ENDED_NORMAL                                   = 3

### Test Reporting
# CHR_TEST_REPORTING
CHR_TEST_REPORTING_REALTIME                                 = 1
CHR_TEST_REPORTING_BATCH                                    = 2

### Test Reporting Firewall
# CHR_TEST_REPORTING_FIREWALL
CHR_TEST_REPORTING_NO_FIREWALL                              = 11
CHR_TEST_REPORTING_USE_FIREWALL                             = 12

### Test Poll Retrieving
# CHR_TEST_RETRIEVING
CHR_TEST_RETRIEVE_NUMBER                                    = 1
CHR_TEST_RETRIEVE_TIMING_RECORD                             = 2

### Test Results
# CHR_RESULTS
CHR_RESULTS_THROUGHPUT                                      = 1
CHR_RESULTS_TRANSACTION_RATE                                = 2
CHR_RESULTS_RESPONSE_TIME                                   = 3
CHR_RESULTS_JITTER                                          = 4     # RFC 1889 jitter calculation
CHR_RESULTS_DELAY_VARIATION                                 = 5     # typically called jitter
CHR_RESULTS_CONSECUTIVE_LOST                                = 6
CHR_RESULTS_MOS_ESTIMATE                                    = 7
CHR_RESULTS_ROUND_TRIP_DELAY                                = 8
CHR_RESULTS_ONE_WAY_DELAY                                   = 9
CHR_RESULTS_R_VALUE                                         = 10
CHR_RESULTS_END_TO_END_DELAY                                = 11
CHR_RESULTS_RSSI_E1                                         = 12
CHR_RESULTS_RSSI_E2                                         = 13
CHR_RESULTS_DF                                              = 14
CHR_RESULTS_MLR                                             = 15
CHR_RESULTS_JOIN_LATENCY                                    = 16
CHR_RESULTS_LEAVE_LATENCY                                   = 17

### Endpoint Config parameters
# CHR_CFG_PARM
CHR_CFG_PARM_ENDPOINT_VERSION                               = 1
CHR_CFG_PARM_ENDPOINT_BUILD_LEVEL                           = 2
CHR_CFG_PARM_ENDPOINT_PRODUCT_TYPE                          = 3
CHR_CFG_PARM_ENDPOINT_OS                                    = 4
CHR_CFG_PARM_ENDPOINT_CPU_UTIL_SUPPORT                      = 5
CHR_CFG_PARM_ENDPOINT_OS_MAJOR_VER                          = 6
CHR_CFG_PARM_ENDPOINT_OS_MINOR_VER                          = 7
CHR_CFG_PARM_ENDPOINT_OS_BUILD_NUM                          = 8
CHR_CFG_PARM_ENDPOINT_CSD_VERSION                           = 9
CHR_CFG_PARM_ENDPOINT_MEMORY                                = 10
CHR_CFG_PARM_ENDPOINT_APPC_DEFAULT_SEND_NOT_SUPPORTED       = 11 # APPC is no longer supported
CHR_CFG_PARM_ENDPOINT_IPX_DEFAULT_SEND                      = 12
CHR_CFG_PARM_ENDPOINT_SPX_DEFAULT_SEND                      = 13
CHR_CFG_PARM_ENDPOINT_TCP_DEFAULT_SEND                      = 14
CHR_CFG_PARM_ENDPOINT_UDP_DEFAULT_SEND                      = 15
CHR_CFG_PARM_ENDPOINT_RTP_DEFAULT_SEND                      = 16
CHR_CFG_PARM_ENDPOINT_APPC_STACK_NOT_SUPPORTED              = 17 # APPC is no longer supported
CHR_CFG_PARM_ENDPOINT_APPC_API_VERSION_NOT_SUPPORTED        = 18 # APPC is no longer supported
CHR_CFG_PARM_ENDPOINT_WINSOCK_API                           = 19
CHR_CFG_PARM_ENDPOINT_WINSOCK_STACK_VER                     = 20
CHR_CFG_PARM_ENDPOINT_WINSOCK_API_VER                       = 21
CHR_CFG_PARM_ENDPOINT_MEMORY_LIMIT_PAYLOAD_FILES            = 22
CHR_CFG_PARM_ENDPOINT_MAX_MEMORY_USAGE_PAYLOAD_FILES        = 23
CHR_CFG_PARM_ENDPOINT_MAX_DISK_USAGE_PAYLOAD_FILES          = 24
CHR_CFG_PARM_ENDPOINT_USE_ENCRYPTED_FLOWS                   = 25
CHR_CFG_PARM_ENDPOINT_MANAGEMENT_PORT                       = 26

CHR_CFG_PARM_ENDPOINT_LAST                                  = CHR_CFG_PARM_ENDPOINT_MANAGEMENT_PORT

### Traceroute run status
# CHR_TRACERT_RUNSTATUS_TYPE
CHR_TRACERT_RUNSTATUS_UNINITIALIZED                         = 0
CHR_TRACERT_RUNSTATUS_INITIALIZING                          = 1
CHR_TRACERT_RUNSTATUS_RUNNING                               = 2
CHR_TRACERT_RUNSTATUS_STOPPING                              = 3
CHR_TRACERT_RUNSTATUS_ERROR                                 = 4
CHR_TRACERT_RUNSTATUS_FINISHED                              = 5
CHR_TRACERT_RUNSTATUS_USER_STOPPED                          = 6

### Pair run status
# CHR_PAIR_RUNSTATUS_TYPE
CHR_PAIR_RUNSTATUS_UNINITIALIZED                            = 0
CHR_PAIR_RUNSTATUS_INITIALIZING_1                           = 1
CHR_PAIR_RUNSTATUS_INITIALIZING_2                           = 2
CHR_PAIR_RUNSTATUS_INITIALIZING_3                           = 3
CHR_PAIR_RUNSTATUS_INITIALIZED                              = 4
CHR_PAIR_RUNSTATUS_RUNNING                                  = 5
CHR_PAIR_RUNSTATUS_STOPPING                                 = 6
CHR_PAIR_RUNSTATUS_REQUESTED_STOP                           = 7
CHR_PAIR_RUNSTATUS_ERROR                                    = 8
CHR_PAIR_RUNSTATUS_RESOLVING_NAMES                          = 9
CHR_PAIR_RUNSTATUS_POLLING                                  = 10
CHR_PAIR_RUNSTATUS_FINISHED                                 = 11
CHR_PAIR_RUNSTATUS_REQUESTING_STOP                          = 12
CHR_PAIR_RUNSTATUS_FINISHED_WARNINGS                        = 13
CHR_PAIR_RUNSTATUS_TRANSFERRING_PAYLOAD                     = 14
CHR_PAIR_RUNSTATUS_APPLYING_IXIA_CONFIG                     = 15
CHR_PAIR_RUNSTATUS_WAITING_FOR_REINIT                       = 16
CHR_PAIR_RUNSTATUS_ABANDONED                                = 17

### HPP measure/stats option.
# CHR_MEASURE_STATS
CHR_MEASURE_STATS_NO_STATS_FILTERS                          = 0
CHR_MEASURE_STATS_STATS_FILTERS                             = 1
CHR_MEASURE_STATS_FILTERS                                   = 2

### Pair type
# CHR_PAIR_TYPE
CHR_PAIR_TYPE_REGULAR                                       = 1 # Pairs with non-streaming scripts
CHR_PAIR_TYPE_STREAMING                                     = 2
CHR_PAIR_TYPE_VOIP                                          = 3
CHR_PAIR_TYPE_VIDEO                                         = 4
CHR_PAIR_TYPE_HARDWARE                                      = 5
CHR_PAIR_TYPE_HARDWARE_VOIP                                 = 6

### License type
# CHR_LICENSE_TYPE
CHR_LICENSE_TYPE_NONE                                       = 1
CHR_LICENSE_TYPE_NODE_LOCKED                                = 2
CHR_LICENSE_TYPE_FLOATING                                   = 3
CHR_LICENSE_TYPE_FLOATING_BORROW                            = 4

### Report item.
# CHR_REPORT_ITEM
CHR_REPORT_ITEM_JOIN_LEAVE                                  = 1 # Join/leave latencies.

# ----------------------------------------------------------------------
#                   CHR_GROUPING_TYPE
# ----------------------------------------------------------------------
# CHR_GROUPING_TYPE
CHR_GROUPING_TYPE_NO_GROUPING                               = 1
CHR_GROUPING_TYPE_ENDPOINT1                                 = 2
CHR_GROUPING_TYPE_ENDPOINT2                                 = 3
CHR_GROUPING_TYPE_PROTOCOL                                  = 4
CHR_GROUPING_TYPE_SCRIPT                                    = 5
CHR_GROUPING_TYPE_SERVICE_QUALITY                           = 6
CHR_GROUPING_TYPE_USER_GROUP                                = 7
CHR_GROUPING_TYPE_PAIR_COMMENT                              = 8
CHR_GROUPING_TYPE_CONSOLE_E1_ADDR                           = 9
CHR_GROUPING_TYPE_E1_E2_ADDR                                = 10
CHR_GROUPING_TYPE_RUN_STATUS                                = 11
CHR_GROUPING_TYPE_DYNAMIC_E1_MGMT                           = 12
CHR_GROUPING_TYPE_DYNAMIC_E2_MGMT                           = 13
CHR_GROUPING_TYPE_E1_SERVICE_QUALITY                        = CHR_GROUPING_TYPE_SERVICE_QUALITY
CHR_GROUPING_TYPE_E2_SERVICE_QUALITY                        = 14

# CHR_SORT_ORDER
CHR_SORT_ORDER_ASCENDING                                    = 1
CHR_SORT_ORDER_DESCENDING                                   = 2



class tm(Structure):
    _fields_ = [
        # seconds after the minute - [0, 60] including leap second
        ("tm_sec", c_int),
        ("tm_min", c_int),   # minutes after the hour - [0, 59]
        ("tm_hour", c_int),   # hours since midnight - [0, 23]
        ("tm_mday", c_int),   # day of the month - [1, 31]
        ("tm_mon", c_int),   # months since January - [0, 11]
        ("tm_year", c_int),   # years since 1900
        ("tm_wday", c_int),   # days since Sunday - [0, 6]
        ("tm_yday", c_int),   # days since January 1 - [0, 365]
        ("tm_isdst", c_int)  # daylight savings time flag
    ]

    @property
    def value(self):
        return datetime(self.tm_year + 1900, self.tm_mon + 1,
                        max(1, self.tm_mday), self.tm_hour,
                        self.tm_min, self.tm_sec)


c_time_t = c_ssize_t
c_ubyte_p = POINTER(c_ubyte)
