# -*- coding: utf-8 -*-
"""
Created on Wed Mar 13 16:46:43 2024

@author: 皓
"""
# pylint: disable=too-few-public-methods,too-many-public-methods,too-many-lines,no-else-return,R0801
from typing import get_type_hints
from functools import lru_cache, wraps
from .chrapi import CHRAPI
from .common import singleton
from .const import (RetureCode, CHR_NULL_HANDLE, CHR_PROTOCOL, CHR_VOIP_CODEC,
                    CHR_VIDEO_CODEC, CHR_DETAIL_LEVEL, CHR_THROUGHPUT_UNITS,
                    CHR_TEST_END, CHR_TEST_HOW_ENDED, CHR_TEST_REPORTING,
                    CHR_TEST_REPORTING_FIREWALL, CHR_TEST_RETRIEVING,
                    CHR_TRACERT_RUNSTATUS_TYPE, CHR_PAIR_RUNSTATUS_TYPE,
                    CHR_MEASURE_STATS, CHR_PAIR_TYPE, CHR_LICENSE_TYPE,
                    CHR_REPORT_ITEM)
from .utils import ToolKit

CHR_DETAIL_LEVEL_ALL = CHR_DETAIL_LEVEL.CHR_DETAIL_LEVEL_ALL


def chr_api_wrapper(self, func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        ret = func(*args, **kwargs)
        if isinstance(ret, (tuple, list)):
            rc, *out = ret
        else:
            rc = ret
            out = None
        if rc != RetureCode.CHR_OK:
            api_name = func.__name__[4:]
            if not api_name.startswith('api'):
                handle = args[0] if args else CHR_NULL_HANDLE
                if hasattr(self, 'show_error'):
                    self.show_error(handle, rc, api_name)
        if out:
            if len(out) == 1:
                return out[0]
            return tuple(out)
        return None
    return wrapper


@singleton
class CHRAPIWrapper:
    def __init__(self, path=None, version=None,
                 detail_level: CHR_DETAIL_LEVEL = CHR_DETAIL_LEVEL_ALL):
        if not path:
            path = ToolKit.get_chrapi_dir()
        if not version:
            version = ToolKit.get_install_version()
        if not path:
            raise FileNotFoundError("Can't find Ixia ixChariot install path")
        self.chrapi = CHRAPI(path, version)
        self.api_initialize(detail_level)

    @lru_cache()
    def dir(self):
        result = []
        chr_api = [x for x in dir(self.chrapi) if x.startswith('CHR_')]
        result.extend(x[4:] for x in chr_api)
        result.extend(chr_api)
        return result

    def __dir__(self):
        return super().__dir__() + self.dir()

    def __getattr__(self, attr: str):
        cls_name = self.__class__.__name__
        if attr.startswith('CHR_'):
            if hasattr(self.chrapi, attr):
                return getattr(self.chrapi, attr)
            else:
                cls_name = 'CHRAPI'
        else:
            chr_name = f'CHR_{attr}'
            if hasattr(self.chrapi, chr_name):
                func = getattr(self.chrapi, chr_name)
                wrapper = chr_api_wrapper(self, func)
                return wrapper
        raise AttributeError(f"'{cls_name}' object has no attribute '{attr}'")


def readonly_property(name, datatype=None):
    """Create a readonly property with getter methods."""

    def getter(self):
        """Getter method for the property."""
        func = getattr(self.api, f"{self.PREFIX}_get_{name}")
        if isinstance(self, BaseHandleCHR):
            result = func(self.handle)
        else:
            result = func()
        if datatype is None:
            return result
        else:
            return datatype(result) if result is not None else result

    return property(getter)


def property_factory(name, datatype=None):
    """Create a property with getter and setter methods."""

    def getter(self):
        """Getter method for the property."""
        func = getattr(self.api, f"{self.PREFIX}_get_{name}")
        if isinstance(self, BaseHandleCHR):
            result = func(self.handle)
        else:
            result = func()
        if datatype is None:
            return result
        else:
            return datatype(result) if result is not None else result

    def setter(self, value):
        """Setter method for the property."""
        func = getattr(self.api, f"{self.PREFIX}_set_{name}")
        if isinstance(self, BaseHandleCHR):
            param = value.handle if isinstance(value, BaseHandleCHR) else value
            return func(self.handle, param)
        else:
            return func(value)

    return property(getter, setter)


def parse_args(*args):
    return [x if not isinstance(x, BaseHandleCHR) else x.handle for x in args]


def api(func):
    func_name = func.__name__
    return_type = get_type_hints(func).get('return')

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        method = getattr(self.api, f"{self.PREFIX}_{func_name}")
        result = method(*parse_args(*args), **kwargs)
        func(self, *args, **kwargs)
        if result is not None:
            return return_type(result) if return_type is not None else result
        else:
            return result

    return wrapper


def handle_api(obj):

    def handle_api_wrapper(func):
        func_name = func.__name__
        return_type = get_type_hints(func).get('return')

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            assert self.handle is not None, 'Handle is null'
            prefix = self.PREFIX if callable(obj) else obj
            method = getattr(self.api, f"{prefix}_{func_name}")
            result = method(self.handle, *parse_args(*args), **kwargs)
            func(self, *args, **kwargs)
            if result is not None:
                return result if return_type is None else return_type(result)
            else:
                return result
        return wrapper
    return handle_api_wrapper(obj) if callable(obj) else handle_api_wrapper


class BaseCHR:
    PREFIX = ''

    def __init__(self):
        self.api = CHRAPIWrapper()


@singleton
class Api(BaseCHR):
    '''
    API Utility Functions
    ---------------------------------------------------------------------------
    The API utility functions are used to define and retrieve API information
    that is independent of specific objects (tests, pairs, etc.).
    '''
    PREFIX = 'api'

    version = readonly_property('version')
    max_pairs = readonly_property('max_pairs')
    license_type = readonly_property('license_type', CHR_LICENSE_TYPE)
    license_expiration_time = readonly_property('license_expiration_time')
    build_level = readonly_property('build_level')
    aptixia_version = readonly_property('aptixia_version')

    @api
    def initialize(self, detail_level: int):
        pass

    @api
    def initialize_with_license_details(self,
                                        detail_level: int,
                                        server_name: str,
                                        pair_count: int,
                                        days_to_borrow: int):
        pass

    @api
    def get_reporting_port(self, protocol: int) -> int:
        pass

    @api
    def get_return_msg(self, return_code: int) -> str:
        pass

    @api
    def set_reporting_port(self, protocol: int, port: int):
        pass

    @api
    def get_pair_type(self, handle: int) -> CHR_PAIR_TYPE:
        pass

    @api
    def get_port_mgmt_ip_list(self):
        pass

    @api
    def get_network_ip_list(self, port_mgmt_ip: str):
        pass

    @api
    def license_get_test_pair_count(self, test_file_name: str):
        pass

    @api
    def license_checkout_pairs(self, no_pairs: int):
        pass

    @api
    def license_checkin_pairs(self):
        pass

    @api
    def license_change_borrow_time(self, days_to_borrow: int):
        pass

    @api
    def license_change_license_server(self, server_name: str):
        pass

    @api
    def license_get_license_server(self):
        pass

    @api
    def license_get_borrow_days_remaining(self):
        pass

    #  QoS functions
    @api
    def new_qos_tos_template(self, template_type: int,
                             template_name: str,
                             tos_mask: int):
        pass

    @api
    def delete_qos_template(self, template_name: str):
        pass

    @api
    def modify_qos_tos_template(self, template_type: int,
                                template_name: str,
                                tos_mask: int):
        pass


class CommonErrorMixin:
    '''
    Common Error Functions
    ---------------------------------------------------------------------------
    Extended error information is available for some function errors after a
    test has been run. The Chariot API includes a function to get this
    information at various levels of detail. Extended error information about
    test run errors is only available for test objects, for pair objects
    contained by a test, for application group objects contained by a test,
    and for multicast pair objects in a multicast group contained by a test.
    This information is only meaningful when a test object, pair object,
    application group, or multicast group object function call returns
    CHR_OPERATION_FAILED, CHR_OBJECT_INVALID, or CHR_APP_GROUP_INVALID.
    CHR_NO_SUCH_VALUE is returned by this function if there is no extended
    error information available for the function error or test run.
    A Chariot message number is available for function errors and test run
    errors that have extended error information. The Chariot API also offers
    a common error function to get this message number for test objects,
    pair objects, multicast pair objects, and multicast group objects.
    The code CHR_NO_SUCH_VALUE is returned if there is no Chariot message
    number available for the error.
    When logging the error information reported by these functions,
    use CHR_DETAIL_LEVEL_ALL to give the maximum possible information
    about the error. Information at this level of detail is needed to
    receive assistance with error diagnosis from Ixia. You should log all
    errors, not just those with extended information, so that you can later
    debug your programs that use the IxChariot API
    '''
    @handle_api('common')
    def error_get_info(self, detail: int):
        pass

    @handle_api('common')
    def error_get_msg_num(self):
        pass


@singleton
class CommonError(BaseCHR, CommonErrorMixin):
    '''
    Common Error Functions
    ---------------------------------------------------------------------------
    Extended error information is available for some function errors after a
    test has been run. The Chariot API includes a function to get this
    information at various levels of detail. Extended error information about
    test run errors is only available for test objects, for pair objects
    contained by a test, for application group objects contained by a test,
    and for multicast pair objects in a multicast group contained by a test.
    This information is only meaningful when a test object, pair object,
    application group, or multicast group object function call returns
    CHR_OPERATION_FAILED, CHR_OBJECT_INVALID, or CHR_APP_GROUP_INVALID.
    CHR_NO_SUCH_VALUE is returned by this function if there is no extended
    error information available for the function error or test run.
    A Chariot message number is available for function errors and test run
    errors that have extended error information. The Chariot API also offers
    a common error function to get this message number for test objects,
    pair objects, multicast pair objects, and multicast group objects.
    The code CHR_NO_SUCH_VALUE is returned if there is no Chariot message
    number available for the error.
    When logging the error information reported by these functions,
    use CHR_DETAIL_LEVEL_ALL to give the maximum possible information
    about the error. Information at this level of detail is needed to
    receive assistance with error diagnosis from Ixia. You should log all
    errors, not just those with extended information, so that you can later
    debug your programs that use the IxChariot API
    '''
    @handle_api('common')
    def error_get_info(self, detail: int):
        pass

    @handle_api('common')
    def error_get_msg_num(self):
        pass


class CommonHandleMixin:
    '''
    Common Results Extraction Functions
    ---------------------------------------------------------------------------
    Common Results Extraction functions are used to obtain test results that
    are common to endpoint pairs, multicast pairs, and timing records for
    either pair type (that is, normal pair or multicast pair).
    '''

    @handle_api('common')
    def results_get_bytes_recv_e1(self):
        pass

    @handle_api('common')
    def results_get_bytes_recv_e2(self):
        pass

    @handle_api('common')
    def results_get_bytes_sent_e1(self):
        pass

    @handle_api('common')
    def results_get_dg_dup_recv_e1(self):
        pass

    @handle_api('common')
    def results_get_dg_dup_recv_e2(self):
        pass

    @handle_api('common')
    def results_get_dg_dup_sent_e1(self):
        pass

    @handle_api('common')
    def results_get_dg_dup_sent_e2(self):
        pass

    @handle_api('common')
    def results_get_dg_lost_e1_to_e2(self):
        pass

    @handle_api('common')
    def results_get_dg_out_of_order(self):
        pass

    @handle_api('common')
    def results_get_dg_recv_e1(self):
        pass

    @handle_api('common')
    def results_get_dg_recv_e2(self):
        pass

    @handle_api('common')
    def results_get_dg_sent_e1(self):
        pass

    @handle_api('common')
    def results_get_est_clock_error(self):
        pass

    @handle_api('common')
    def results_get_jitter_buffer_lost(self):
        pass

    @handle_api('common')
    def results_get_max_clock_error(self):
        pass

    @handle_api('common')
    def results_get_meas_time(self):
        pass

    @handle_api('common')
    def results_get_rtd(self):
        pass

    @handle_api('common')
    def results_get_rtd_95pct_confidence(self):
        pass

    @handle_api('common')
    def results_get_trans_count(self):
        pass

    @handle_api('common')
    def results_get_e1_syn_tx(self):
        pass

    @handle_api('common')
    def results_get_e1_syn_rx(self):
        pass

    @handle_api('common')
    def results_get_e1_syn_failed(self):
        pass

    @handle_api('common')
    def results_get_e1_conn_established(self):
        pass

    @handle_api('common')
    def results_get_e1_fin_tx(self):
        pass

    @handle_api('common')
    def results_get_e1_fin_rx(self):
        pass

    @handle_api('common')
    def results_get_e1_ack_to_fin_tx(self):
        pass

    @handle_api('common')
    def results_get_e1_ack_to_fin_rx(self):
        pass

    @handle_api('common')
    def results_get_e1_rst_tx(self):
        pass

    @handle_api('common')
    def results_get_e1_rst_rx(self):
        pass

    @handle_api('common')
    def results_get_e1_tcp_retransmissions(self):
        pass

    @handle_api('common')
    def results_get_e1_tcp_timeouts(self):
        pass


class BaseHandleCHR(BaseCHR):
    def __init__(self, handle):
        super().__init__()
        self.handle = handle

    def __repr__(self):
        return f"<{self.__class__.__name__} object [handle {self.handle}]>"


class HandleCHR(BaseHandleCHR):
    def __init__(self, handle=None):
        super(BaseHandleCHR, self).__init__()
        if handle is None:
            handle = self.new()
        self.handle = handle

    def __del__(self):
        if self.handle is not None:
            if hasattr(self, 'delete'):
                self.delete()
            self.handle = None

    def new(self):
        return 0


class IxiaNetworkMixin:
    '''
    Ixia Network Configuration Functions
    ---------------------------------------------------------------------------
    The Ixia network configuration functions are used to import Ixia network
    configurations into a test object and export Ixia network configurations
    that are part of a test object.
    '''
    ixia_network_configuration = property_factory('ixia_network_configuration')

    @handle_api
    def load_ixia_network_configuration(self, file_name: str):
        pass

    @handle_api
    def save_ixia_network_configuration(self, file_name: str):
        pass

    @handle_api
    def clear_ixia_network_configuration(self):
        pass


class DatagramOptions(BaseHandleCHR):
    '''
    Datagram Options Object Functions
    ---------------------------------------------------------------------------
    Datagram options object functions are used to define and retrieve the
    datagram options for the test that owns them. You cannot set datagram
    options for a test that has results or while a test is running.
    '''
    PREFIX = 'dgopts'
    recv_timeout = property_factory('recv_timeout')
    retrans_count = property_factory('retrans_count')
    retrans_timeout = property_factory('retrans_timeout')
    TTL = property_factory('TTL')
    window_size = property_factory('window_size')
    low_sender_jitter = property_factory('low_sender_jitter')
    limit_data_rate = property_factory('limit_data_rate')
    data_rate_limit = property_factory('data_rate_limit')
    measured_interval = property_factory('measured_interval')
    RTP_use_extended_headers = property_factory('RTP_use_extended_headers')


class RunOptions(BaseHandleCHR):
    '''
    Run Options Object Functions
    ---------------------------------------------------------------------------
    Run options object functions are used to define and retrieve the run
    options that are set for a specified test. You are not allowed to set run
    options for a test that has results or while a test is running.
    '''
    PREFIX = 'runopts'
    connect_timeout = property_factory('connect_timeout')
    CPU_util = property_factory('CPU_util')
    collect_TCP_stats = property_factory('collect_TCP_stats')
    allow_pair_reinit = property_factory('allow_pair_reinit')
    pair_reinit_max = property_factory('pair_reinit_max')
    pair_reinit_retry_interval = property_factory('pair_reinit_retry_interval')
    allow_pair_reinit_run = property_factory('allow_pair_reinit_run')
    pair_reinit_max_run = property_factory('pair_reinit_max_run')
    pair_reinit_retry_interval_run = property_factory(
        'pair_reinit_retry_interval_run')
    HW_timestamps = property_factory('HW_timestamps')
    fewer_setup_connections = property_factory('fewer_setup_connections')
    apply_dod_only = property_factory('apply_dod_only')
    deconfigure_ports = property_factory('deconfigure_ports')
    poll_endpoints = property_factory('poll_endpoints')
    poll_interval = property_factory('poll_interval')
    random_new_seed = property_factory('random_new_seed')
    reporting_type = property_factory('reporting_type', CHR_TEST_REPORTING)
    poll_retrieving_type = property_factory(
        'poll_retrieving_type', CHR_TEST_RETRIEVING)
    reporting_firewall = property_factory(
        'reporting_firewall', CHR_TEST_REPORTING_FIREWALL)
    stop_after_num_pairs_fail = property_factory('stop_after_num_pairs_fail')
    stop_on_init_failure = property_factory('stop_on_init_failure')
    test_duration = property_factory('test_duration')
    test_end = property_factory('test_end', CHR_TEST_END)
    validate_on_recv = property_factory('validate_on_recv')
    clksync_hardware_ts = property_factory('clksync_hardware_ts')
    clksync_external = property_factory('clksync_external')
    overlapped_sends_count = property_factory('overlapped_sends_count')
    management_qos_console_name = property_factory(
        'management_qos_console_name')
    management_qos_endpoint_name = property_factory(
        'management_qos_endpoint_name')

    @handle_api
    def get_num_result_ranges(self, result_type: int):
        pass

    @handle_api
    def get_result_range(self, result_type: int, index: int):
        pass

    @handle_api
    def set_num_result_ranges(self, result_type: int, number: int):
        pass

    @handle_api
    def set_result_range(self, result_type: int, index: int,
                         min_value: int, max_value: int):
        pass


class HopRecord(BaseHandleCHR):
    '''
    Hop Record Object Functions
    ---------------------------------------------------------------------------
    Hop record results extraction is part of the API's traceroute
    functionality.Hop records can be extracted from a traceroute pair.
    Hop record extraction gets a series of hop records, with a hop count.
    Individual hop records contain the hop number, the average hop latency,
    the hop address, and the resolved hop name.
    '''
    PREFIX = 'hoprec'
    hop_address = readonly_property('hop_address')
    hop_latency = readonly_property('hop_latency')
    hop_name = readonly_property('hop_name')
    hop_number = readonly_property('hop_number')


class TimingRecord(BaseHandleCHR):
    '''
    Timing Record Object Functions
    ---------------------------------------------------------------------------
    Timing record extraction functions are used to obtain test results that are
    unique to pair and multicast pair timing records. Other values typically
    stored in timing records can be obtained using common results extraction
    functions.
    '''
    PREFIX = 'timingrec'
    elapsed = readonly_property('elapsed')
    end_to_end_delay = readonly_property('end_to_end_delay')
    inactive = readonly_property('inactive')
    jitter = readonly_property('jitter')
    max_consecutive_lost = readonly_property('max_consecutive_lost')
    max_delay_variation = readonly_property('max_delay_variation')
    MOS_estimate = readonly_property('MOS_estimate')
    one_way_delay = readonly_property('one_way_delay')
    R_value = readonly_property('R_value')
    e1_rssi = readonly_property('e1_rssi')
    e2_rssi = readonly_property('e2_rssi')
    e1_bssid = readonly_property('e1_bssid')
    e2_bssid = readonly_property('e2_bssid')
    df = readonly_property('df')
    mlr = readonly_property('mlr')
    report_group_id = readonly_property('report_group_id')

    @handle_api
    def get_result_frequency(self, result_type: int, index: int):
        pass


class PairTimingRecord(TimingRecord, CommonHandleMixin):
    '''
    Timing Record Object Functions
    ---------------------------------------------------------------------------
    Timing record extraction functions are used to obtain test results that are
    unique to pair and multicast pair timing records. Other values typically
    stored in timing records can be obtained using common results extraction
    functions.
    '''
    pass


class BasePair(HandleCHR, CommonHandleMixin):
    @handle_api('pair')
    def results_get_average(self, result_type: int):
        pass

    @handle_api('pair')
    def results_get_CPU_util_e1(self):
        pass

    @handle_api('pair')
    def results_get_CPU_util_e2(self):
        pass

    @handle_api('pair')
    def results_get_maximum(self, result_type: int):
        pass

    @handle_api('pair')
    def results_get_minimum(self, result_type: int):
        pass

    @handle_api('pair')
    def results_get_rel_precision(self):
        pass

    @handle_api('pair')
    def results_get_95pct_confidence(self, result_type: int):
        pass


class MPair(BasePair):
    '''
    Multicast Pair Object Functions
    ---------------------------------------------------------------------------
    The multicast pair object functions are used to define multicast group
    members and retrieve information about a multicast pair. You cannot set
    any multicast pair information for a multicast pair that is owned by
    multicast group.
    '''
    PREFIX = 'mpair'
    timing_record_count = readonly_property('timing_record_count')
    runStatus = readonly_property('runStatus', CHR_PAIR_RUNSTATUS_TYPE)
    e2_addr = property_factory('e2_addr')
    setup_e1_e2_addr = property_factory('setup_e1_e2_addr')
    use_setup_e1_e2_values = property_factory('use_setup_e1_e2_values')

    @handle_api
    def delete(self):
        self.handle = None

    @handle_api
    def get_e2_config_value(self, parameter: int):
        pass

    @handle_api
    def get_timing_record(self, index: int) -> PairTimingRecord:
        pass

    @api
    def new(self):
        pass

    @handle_api
    def set_lock(self, lock: int):
        pass


class Pair(BasePair):
    '''
    Pair Object Functions
    ---------------------------------------------------------------------------
    Pair object functions are used to define pairs for a test and retrieve
    information about an endpoint pair. You are not allowed to set any pair
    information for a pair that is owned by a test.
    Some functions apply to VoIP pairs; seeVoIP Pair Object on page 2-16 for
    more information.
    '''
    PREFIX = 'pair'
    appl_script_name = readonly_property('appl_script_name')
    runStatus = readonly_property('runStatus', CHR_PAIR_RUNSTATUS_TYPE)
    script_filename = readonly_property('script_filename')
    timing_record_count = readonly_property('timing_record_count')
    comment = property_factory('comment')
    console_e1_addr = property_factory('console_e1_addr')
    console_e1_protocol = property_factory('console_e1_protocol')
    e1_addr = property_factory('e1_addr')
    e2_addr = property_factory('e2_addr')
    protocol = property_factory('protocol')
    qos_name = property_factory('qos_name')
    e1_qos_name = property_factory('e1_qos_name')
    e2_qos_name = property_factory('e2_qos_name')
    setup_e1_e2_addr = property_factory('setup_e1_e2_addr')
    use_console_e1_values = property_factory('use_console_e1_values')
    use_setup_e1_e2_values = property_factory('use_setup_e1_e2_values')

    @api
    def copy(self, to_pair_handle: int, from_pair_handle: int):
        pass

    @handle_api
    def delete(self):
        self.handle = None

    @handle_api
    def get_e1_config_value(self, parameter: int):
        pass

    @handle_api
    def get_e2_config_value(self, parameter: int):
        pass

    @handle_api
    def get_timing_record(self, index: int) -> PairTimingRecord:
        pass

    @handle_api
    def is_udp_RFC768_streaming(self):
        pass

    @handle_api
    def is_disabled(self):
        pass

    @api
    def new(self):
        pass

    @handle_api
    def set_lock(self, lock: int):
        pass

    @handle_api
    def set_script_variable(self, name: str, value: str):
        pass

    @handle_api
    def get_script_variable(self, name: str):
        pass

    @handle_api
    def set_script_embedded_payload(self, variable_name: str, payload: str):
        pass

    @handle_api
    def get_script_embedded_payload(self, variable_name: str):
        pass

    @handle_api
    def set_payload_file(self,
                         variable_name: str,
                         filename: str,
                         embedded: int):
        pass

    @handle_api
    def get_payload_file(self, variable_name: str):
        pass

    @handle_api
    def use_script_filename(self, filename: str):
        pass

    @handle_api
    def disable(self, disable: int):
        pass

    @handle_api
    def swap_endpoints(self):
        pass


class MGroup(HandleCHR):
    '''Multicast Group Object Functions
    ---------------------------------------------------------------------------
    The multicast group object functions are used to define and retrieve
    information about a multicast group. A separate set of functions is
    provided to define and retrieve information about multicast group members,
    called multicast pairs (mpairs). You cannot add members to or set the
    attributes of a multicast group object that is contained by a test object.
    '''
    PREFIX = 'mgroup'
    appl_script_name = readonly_property('appl_script_name')
    mpair_count = readonly_property('mpair_count')
    script_filename = readonly_property('script_filename')
    comment = property_factory('comment')
    console_e1_addr = property_factory('console_e1_addr')
    console_e1_protocol = property_factory('console_e1_protocol', CHR_PROTOCOL)
    e1_addr = property_factory('e1_addr')
    multicast_addr = property_factory('multicast_addr')
    multicast_port = property_factory('multicast_port')
    name = property_factory('name')
    protocol = property_factory('protocol', CHR_PROTOCOL)
    qos_name = property_factory('qos_name')
    use_console_e1_values = property_factory('use_console_e1_values')

    @handle_api
    def add_mpair(self, mpair_handle: int):
        pass

    @api
    def copy(self, to_mgroup_handle: int, from_mgroup_handle: int):
        pass

    @handle_api
    def delete(self):
        self.handle = None

    @handle_api
    def get_e1_config_value(self, parameter: int):
        pass

    @handle_api
    def get_mpair(self, index: int) -> MPair:
        pass

    @handle_api
    def get_script_variable(self, name: str):
        pass

    @handle_api
    def get_script_embedded_payload(self, variable_name: str):
        pass

    @handle_api
    def get_payload_file(self, variable_name: str):
        pass

    @handle_api
    def is_udp_RFC768_streaming(self):
        pass

    @handle_api
    def is_disabled(self):
        pass

    @api
    def new(self):
        pass

    @handle_api
    def remove_mpair(self, mpair_handle: int):
        pass

    @handle_api
    def set_lock(self, lock: int):
        pass

    @handle_api
    def set_script_variable(self, name: str, value: str):
        pass

    @handle_api
    def set_script_embedded_payload(self, variable_name: str, payload: str):
        pass

    @handle_api
    def set_payload_file(self,
                         variable_name: str,
                         filename: str,
                         embedded: int):
        pass

    @handle_api
    def use_script_filename(self, file_name: str):
        pass

    @handle_api
    def disable(self, disable: int):
        pass


class TracertPair(HandleCHR):
    '''
    Traceroute Pair Object Functions
    ---------------------------------------------------------------------------
    Traceroute pair object functions are used to run traceroutes on selected
    pairs of endpoints.
    You can specify the maximum hop count and maximum timeout value. You can
    also extract the runstatus while the traceroute is running.
    '''
    PREFIX = 'tracert_pair'
    runStatus = readonly_property('runStatus', CHR_TRACERT_RUNSTATUS_TYPE)
    e1_addr = property_factory('e1_addr')
    e2_addr = property_factory('e2_addr')
    max_hops = property_factory('max_hops')
    max_timeout = property_factory('max_timeout')
    resolve_hop_name = property_factory('resolve_hop_name')

    @handle_api
    def delete(self):
        self.handle = None

    @handle_api
    def get_hop_record(self, index: int) -> HopRecord:
        pass

    @api
    def new(self):
        pass

    @handle_api
    def query_stop(self, timeout: int):
        pass

    @handle_api
    def results_get_hop_count(self):
        pass

    @handle_api
    def run(self):
        pass

    @handle_api
    def stop(self):
        pass


class VoipPair(HandleCHR):
    '''
    VoIP Pair Object Functions
    ---------------------------------------------------------------------------
    VoIP pair object functions are used in voice over IP tests. A VoIP pair or
    VoIP hardware performance pair object must be contained by a test object.
    The testing parameters available for the VoIP pair object include the type
    of codec, the source and destination port numbers, whether to use silence
    suppression and its corresponding activity rate, the length of the timing
    records generated, the initial delay, and the delay between packets.
    You can also get results for a VoIP test using
    CHR_timingrec_get_MOS_estimate or one of the CHR_pair_results functions.
    '''
    PREFIX = 'voip_pair'
    codec = property_factory('codec', CHR_VOIP_CODEC)
    additional_delay = property_factory('additional_delay')
    datagram_delay = property_factory('datagram_delay')
    dest_port_num = property_factory('dest_port_num')
    initial_delay = property_factory('initial_delay')
    jitter_buffer_size = property_factory('jitter_buffer_size')
    source_port_num = property_factory('source_port_num')
    tr_duration = property_factory('tr_duration')
    no_of_timing_records = property_factory('no_of_timing_records')
    use_PLC = property_factory('use_PLC')
    use_silence_sup = property_factory('use_silence_sup')
    voice_activ_rate = property_factory('voice_activ_rate')

    @api
    def new(self):
        pass

    @handle_api
    def get_payload_file(self, filename: str):
        pass

    @handle_api
    def set_payload_file(self, filename: str, embedded: int):
        pass

    @handle_api
    def set_payload_random(self):
        pass


class VideoPair(HandleCHR):
    '''
    Video Pair Object Functions
    ---------------------------------------------------------------------------
    The video pair object functions are used to define and retrieve information
    about a video pair. A video pair object must be contained by a test object.
    The testing parameters available for the video pair object include the
    source and destination port numbers, the length of the timing records
    generated, type of codec, the bitrate of the video transmission, the frames
    per datagram, the initial delay, the RTP payload type, and the media frame
    size. You cannot add members to or set the attributes of a video pair
    object that is contained by a test object.
    A separate set of functions is provided to define and retrieve information
    about video multicast groups.
    '''
    PREFIX = 'video_pair'
    bitrate = readonly_property('bitrate')
    codec = property_factory('codec', CHR_VIDEO_CODEC)
    dest_port_num = property_factory('dest_port_num')
    initial_delay = property_factory('initial_delay')
    source_port_num = property_factory('source_port_num')
    tr_duration = property_factory('tr_duration')
    no_of_timing_records = property_factory('no_of_timing_records')
    frames_per_datagram = property_factory('frames_per_datagram')
    rtp_payload_type = property_factory('rtp_payload_type')
    media_frame_size = property_factory('media_frame_size')

    @api
    def new(self):
        pass

    @handle_api
    def set_bitrate(self, bitrate: float, rate_um: int):
        pass


class VideoMGroup(HandleCHR):
    '''
    Video Multicast Group Object Functions
    ---------------------------------------------------------------------------
    The video multicast group object functions are used to define and retrieve
    information about a video multicast group. A video multicast group object
    must be contained by a test object. The testing parameters available for
    the video multicast group object include the source port number, the length
    of the timing records generated, type of codec, the bitrate of the video
    transmission, the frames per datagram, the initial delay, the RTP payload
    type, and the media frame size. You cannot add members to or set the
    attributes of a multicast group object that is contained by a test object.
    A separate set of functions is provided to define and retrieve information
    about video pairs (unicast video).
    '''
    PREFIX = 'video_mgroup'
    bitrate = readonly_property('bitrate')
    codec = property_factory('codec', CHR_VIDEO_CODEC)
    initial_delay = property_factory('initial_delay')
    source_port_num = property_factory('source_port_num')
    tr_duration = property_factory('tr_duration')
    no_of_timing_records = property_factory('no_of_timing_records')
    frames_per_datagram = property_factory('frames_per_datagram')
    rtp_payload_type = property_factory('rtp_payload_type')
    media_frame_size = property_factory('media_frame_size')

    @api
    def new(self):
        pass

    @handle_api
    def set_bitrate(self, bitrate: float, rate_um: int):
        pass


class HardwarePair(HandleCHR):
    '''
    Hardware Performance Pair Object Functions
    ---------------------------------------------------------------------------
    Hardware Performance Pair object functions are used to define pairs for a
    test and retrieve information about a hardware performance pair, either
    VoIP or not. You are not allowed to set any pair information for a pair
    that is owned by a test. The following Pair Object Functions are used to
    get/set values in the Hardware Performance Pair Object as well

    '''
    PREFIX = 'hardware_pair'
    line_rate = property_factory('line_rate')
    override_line_rate = property_factory('override_line_rate')
    measure_statistics = property_factory('measure_statistics',
                                          CHR_MEASURE_STATS)

    @api
    def new(self):
        pass


class HardwareVoipPair(HandleCHR):
    PREFIX = 'hardware_voip_pair'
    concurrent_voice_streams = property_factory('concurrent_voice_streams')

    @api
    def new(self):
        pass


class AppGroup(HandleCHR):
    '''
    Application Group Object Functions
    ---------------------------------------------------------------------------
    The IxChariot API provides a set of functions for working with application
    groups. Application groups provide the means to synchronize the actions of
    two or more pairs during a test. This allows you to simulate the behavior
    of applications that use more than one simultaneous connection
    (such as FTP, which uses one connection for control and the other for data
     transfer).
    '''
    PREFIX = 'app_group'
    pair_count = readonly_property('pair_count')
    event_count = readonly_property('event_count')
    address_count = readonly_property('address_count')
    management_address_count = readonly_property('management_address_count')
    filename = property_factory('filename')
    name = property_factory('name')
    comment = property_factory('comment')
    lock = property_factory('lock')

    @api
    def new(self):
        pass

    @api
    def copy(self, to_app_group_handle: int, from_app_group_handle: int):
        pass

    @handle_api
    def delete(self):
        self.handle = None

    @handle_api
    def save(self):
        pass

    @handle_api
    def force_delete(self):
        pass

    @handle_api
    def add_pair(self, pair_handle: int):
        pass

    @handle_api
    def remove_pair(self, pair_handle: int):
        pass

    @handle_api
    def get_pair(self, index: int) -> Pair:
        pass

    @handle_api
    def add_event(self, event_name: str, event_comment: str):
        pass

    @handle_api
    def remove_event(self, event_name: str):
        pass

    @handle_api
    def get_event(self, index: int):
        pass

    @handle_api
    def set_pair_protocol(self, pair_index: int, protocol: int):
        pass

    @handle_api
    def get_pair_protocol(self, pair_index: int) -> CHR_PROTOCOL:
        pass

    @handle_api
    def set_pair_management_protocol(self, pair_index: int, protocol: int):
        pass

    @handle_api
    def get_pair_management_protocol(self, pair_index: int) -> CHR_PROTOCOL:
        pass

    @handle_api
    def set_pair_qos_name(self, pair_index: int, qos_name: str):
        pass

    @handle_api
    def get_pair_qos_name(self, pair_index: int):
        pass

    @handle_api
    def set_address(self, address_index: int, address: str):
        pass

    @handle_api
    def get_address(self, address_index: int):
        pass

    @handle_api
    def set_management_address(self, address_index: int, address: str):
        pass

    @handle_api
    def get_management_address(self, address_index: int):
        pass

    @handle_api
    def is_disabled(self):
        pass

    @handle_api
    def disable(self, disable: int):
        pass

    @handle_api
    def validate(self):
        pass


class Channel(HandleCHR):
    '''
    IPTV Channel Object Functions
    ---------------------------------------------------------------------------
    The IPTV channel object functions are used to define and retrieve
    information for IPTV channels. A channel object must be contained by a test
    object. The testing parameters available for a channel object include the
    channel name, test network parameters, management network parameters, and
    IPTV traffic characteristics.
    A related set of functions is provided for IPTV receiver objects and IPTV
    VPair objects.
    '''
    PREFIX = 'channel'
    bitrate = readonly_property('bitrate')
    codec = property_factory('codec', CHR_VIDEO_CODEC)
    comment = property_factory('comment')
    conn_send_buff_size = property_factory('conn_send_buff_size')
    console_e1_addr = property_factory('console_e1_addr')
    console_e1_protocol = property_factory('console_e1_protocol', CHR_PROTOCOL)
    e1_addr = property_factory('e1_addr')
    frames_per_datagram = property_factory('frames_per_datagram')
    media_frame_size = property_factory('media_frame_size')
    multicast_addr = property_factory('multicast_addr')
    multicast_port = property_factory('multicast_port')
    name = property_factory('name')
    protocol = property_factory('protocol', CHR_PROTOCOL)
    qos_name = property_factory('qos_name')
    rtp_payload_type = property_factory('rtp_payload_type')
    source_port_num = property_factory('source_port_num')
    use_console_e1_values = property_factory('use_console_e1_values')
    lock = property_factory('lock')

    @handle_api
    def delete(self):
        self.handle = None

    @api
    def new(self):
        pass

    @handle_api
    def set_bitrate(self, i_bitrate: float, i_units: int):
        pass


class Report(BaseHandleCHR):
    '''
    Report Object Functions
    --------------------------------------------------------------------------------
    Report object functions handle information reported back by the endpoint
    that does not fit into a timing record. There can be many types of reports,
    hence the ITEM_TYPE field.
    The Join Latency and Leave Latency reports are used by the IPTV functions.
    These reports are issued once per test iteration; many timing records may
    be generated during each iteration.
    The REPORT_GROUP_ID field helps associate timing records with reports.
    '''
    PREFIX = 'report'
    item_type = readonly_property('item_type', CHR_REPORT_ITEM)
    join_latency = readonly_property('join_latency')
    leave_latency = readonly_property('leave_latency')
    report_group_id = readonly_property('report_group_id')


class VPair(HandleCHR):
    '''
    IPTV Pair Object Functions
    ---------------------------------------------------------------------------
    The IPTV pair object functions are used to define IPTV pairs (vpairs) for a
    test and retrieve information about an endpoint vpair..
    A related set of commands is provided for IPTV channel objects and IPTV
    receiver objects.
    '''
    PREFIX = 'vpair'
    report_count = readonly_property('report_count')
    timing_record_count = readonly_property('timing_record_count')
    runStatus = readonly_property('runStatus')
    channel = property_factory('channel', Channel)
    no_of_timing_records = property_factory('no_of_timing_records')
    tr_duration = property_factory('tr_duration')
    lock = property_factory('lock')

    @handle_api
    def delete(self):
        self.handle = None

    @handle_api
    def get_report(self, i_report_index: int) -> Report:
        pass

    @handle_api
    def get_timing_record(self, i_record_index: int) -> TimingRecord:
        pass

    @api
    def new(self):
        pass


class Receiver(HandleCHR):
    '''
    IPTV Receiver Object Functions
    ---------------------------------------------------------------------------
    The IPTV receiver object functions are used to configure receiver group
    objects. Receiver groups are the subscribers of the IPTV channels.
    Each channel is represented by a VPair within a receiver group.
    A related set of commands is provided for IPTV channel objects and IPTV
    VPair objects.
    '''
    PREFIX = 'receiver'
    vpair_count = readonly_property('vpair_count')
    comment = property_factory('comment')
    conn_recv_buff_size = property_factory('conn_recv_buff_size')
    e2_addr = property_factory('e2_addr')
    name = property_factory('name')
    no_of_iterations = property_factory('no_of_iterations')
    setup_e1_e2_addr = property_factory('setup_e1_e2_addr')
    switch_delay = property_factory('switch_delay')
    use_e1_e2_values = property_factory('use_e1_e2_values')
    lock = property_factory('lock')

    @handle_api
    def add_vpair(self, i_pair_handle: int):
        pass

    @handle_api
    def remove_vpair(self, i_pair_handle: int):
        pass

    @handle_api
    def delete(self):
        self.handle = None

    @handle_api
    def get_vpair(self, i_pair_index: int) -> VPair:
        pass

    @handle_api
    def is_disabled(self):
        pass

    @api
    def new(self):
        pass

    @handle_api
    def disable(self, i_disable: int):
        pass


class Test(HandleCHR, IxiaNetworkMixin):
    '''
    Test Object Functions
    ---------------------------------------------------------------------------
    The test object functions are used to define and retrieve information about
    a test and to control the running of tests. You cannot add pairs or
    multicast groups to a test that has results. A test must have at least one
    pair or multicast group before it can be saved or run.
    '''
    PREFIX = 'test'
    grouping = readonly_property('grouping')
    dgopts = readonly_property('dgopts', DatagramOptions)
    how_ended = readonly_property('how_ended', CHR_TEST_HOW_ENDED)
    local_start_time = readonly_property('local_start_time')
    local_stop_time = readonly_property('local_stop_time')
    mgroup_count = readonly_property('mgroup_count')
    pair_count = readonly_property('pair_count')
    runopts = readonly_property('runopts', RunOptions)
    start_time = readonly_property('start_time')
    stop_time = readonly_property('stop_time')
    app_group_count = readonly_property('app_group_count')
    test_server_session = readonly_property('test_server_session')
    filename = property_factory('filename')
    throughput_units = property_factory('throughput_units',
                                        CHR_THROUGHPUT_UNITS)

    @handle_api
    def set_grouping_type(self, grouping_type: int):
        pass

    @handle_api
    def set_grouping_order(self, grouping_order: int):
        pass

    @handle_api
    def abandon(self):
        pass

    @handle_api
    def add_mgroup(self, mgroup_handle: int):
        pass

    @handle_api
    def add_pair(self, pair_handle: int):
        pass

    @handle_api
    def clear_results(self):
        pass

    @handle_api
    def delete(self):
        self.handle = None

    @handle_api
    def force_delete(self):
        pass

    @handle_api
    def get_mgroup(self, index: int) -> MGroup:
        pass

    @handle_api
    def get_pair(self, index: int) -> Pair:
        pass

    @handle_api
    def load(self, test_file_name: str):
        pass

    @api
    def new(self):
        pass

    @handle_api
    def query_stop(self, timeout: int):
        pass

    @handle_api
    def save(self):
        pass

    @handle_api
    def start(self):
        pass

    @handle_api
    def stop(self):
        pass

    @handle_api
    def load_app_groups(self, filename: str):
        pass

    @handle_api
    def add_app_group(self, app_group_handle: int):
        pass

    @handle_api
    def remove_app_group(self, app_group_handle: int):
        pass

    @handle_api
    def get_app_group_by_index(self, index: int) -> AppGroup:
        pass

    @handle_api
    def get_app_group_by_name(self, name: str) -> AppGroup:
        pass

    @handle_api
    def set_test_server_session(self,
                                test_server_address: str,
                                test_server_port: int,
                                session_object_id: int):
        pass


class VTest(Test):
    '''
    IPTV Test Object Functions
    '''
    channel_count = readonly_property('channel_count')
    receiver_count = readonly_property('receiver_count')

    @handle_api
    def add_channel(self, i_channel_handle: int):
        pass

    @handle_api
    def remove_channel(self, i_channel_handle: int):
        pass

    @handle_api
    def add_receiver(self, i_receiver_handle: int):
        pass

    @handle_api
    def remove_receiver(self, i_receiver_handle: int):
        pass

    @handle_api
    def get_channel(self, i_list_index: int) -> Channel:
        pass

    @handle_api
    def get_channel_by_name(self, i_channel_name: str) -> Channel:
        pass

    @handle_api
    def get_receiver(self, i_list_index: int) -> Receiver:
        pass

    @handle_api
    def get_receiver_by_name(self, i_receiver_name: str) -> Receiver:
        pass
