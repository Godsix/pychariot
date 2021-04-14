# -*- coding: utf-8 -*-
"""
Created on Wed Feb 10 11:31:50 2021

@author: haoyue
"""
import os.path as osp
from ctypes import (CDLL, create_string_buffer, create_unicode_buffer, byref,
                    c_int, c_ulong, c_long,
                    c_ushort, c_char, c_ubyte, c_double, c_longlong)
from functools import wraps
import logging
from .chrapi_constant import (CHR_MAX_FILENAME, CHR_MAX_FILE_PATH,
                              CHR_MAX_EMBEDDED_PAYLOAD_SIZE,
                              CHR_MAX_ERROR_INFO, CHR_MAX_PAIR_COMMENT,
                              CHR_MAX_ADDR, CHR_MAX_MULTICAST_ADDR,
                              CHR_MAX_QOS_NAME, CHR_MAX_APPL_SCRIPT_NAME,
                              CHR_MAX_GROUP_NAME, CHR_MAX_VERSION,
                              CHR_MAX_RETURN_MSG,
                              CHR_MAX_SCRIPT_VARIABLE_VALUE,
                              CHR_MAX_CFG_PARM, CHR_MAX_ADDR_STRING,
                              CHR_BSSID_SIZE, CHR_MAX_APP_GROUP_NAME,
                              CHR_MAX_APP_GROUP_COMMENT,
                              CHR_MAX_APP_GROUP_EVENT_NAME,
                              CHR_MAX_APP_GROUP_EVENT_COMMENT,
                              CHR_MAX_CHANNEL_NAME, CHR_MAX_RECEIVER_NAME,
                              CHR_MAX_CHANNEL_COMMENT,
                              CHR_MAX_RECEIVER_COMMENT)


CHR_API_VERSION = (7, 10, 0)


class BaseParam:
    ENCODE = 'gbk'

    def __init__(self, datatype):
        self.datatype = datatype

    @classmethod
    def encode_data(cls, data, datatype):
        if isinstance(data, datatype):
            return data
        if datatype == bytes and isinstance(data, str):
            return data.encode(cls.ENCODE)
        if datatype == str and isinstance(data, bytes):
            return data.decode(cls.ENCODE)


class ParamIn(BaseParam):

    def __call__(self, value):
        if self.datatype in (bytes, str):
            valid_value = self.encode_data(value, self.datatype)
            return valid_value, len(valid_value)
        return tuple([self.datatype(value)])


class ParamOut(BaseParam):

    def __init__(self, datatype, max_len=None):
        super().__init__(datatype)
        self.maxlength = CHR_MAX_RETURN_MSG if max_len is None else max_len
        self.data = None
        self.data_len = 0

    def __call__(self):
        if self.datatype in (bytes, str):
            if self.datatype == bytes:
                self.data = create_string_buffer(b"\0", self.maxlength)
            else:
                self.data = create_unicode_buffer("\0", self.maxlength)
            self.data_len = c_ulong()
            return self.data, c_ulong(self.maxlength), byref(self.data_len)
        if self.datatype in (c_int, c_ulong, c_long, c_ushort, c_char,
                             c_ubyte, c_double, c_longlong):
            self.data = self.datatype()
            return tuple([byref(self.data)])

    def get_result(self):
        if self.datatype in (bytes, str):
            value = self.encode_data(self.data.value, str)
            return value
        if self.datatype in (c_int, c_ulong, c_long, c_ushort, c_char,
                             c_ubyte, c_double, c_longlong):
            return self.data.value


def ctypes_param(*param_args):
    def decorator(func):
        func_name = func.__name__

        @wraps(func)
        def wrapper(*args, **kwargs):
            self, *param = args
            dll = getattr(self, 'dll')
            chrapi_func = getattr(dll, func_name)
            param_iter = iter(param)
            valid_args = []
            out_params = []
            param_iter = iter(param)
            for item in param_args:
                if isinstance(item, ParamIn):
                    valid_args.extend(item(next(param_iter)))
                elif isinstance(item, ParamOut):
                    out_params.append(item)
                    valid_args.extend(item())
                elif item in (str, bytes):
                    param_item = ParamIn.encode_data(next(param_iter), item)
                    valid_args.append(param_item)
                else:
                    valid_args.append(item(next(param_iter)))
            ret = chrapi_func(*valid_args, **kwargs)
            if out_params:
                out_values = [x.get_result() for x in out_params]
                return ret, *out_values
            return ret
        return wrapper
    return decorator


class CHRAPI:

    def __init__(self, path=None):
        self.path = path
        self.logger = logging.getLogger()

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        self._path = osp.realpath(value if value else osp.dirname(__file__))
        # import API dll
        self.dll = CDLL(osp.join(self._path, 'ChrApi.dll'))

    def __getattr__(self, attr):
        if attr.startswith('CHR'):
            if hasattr(self.api, attr):
                return getattr(self.dll, attr)
        raise AttributeError(
            "'{}' object has no attribute '{}'".format(self.__class__.__name__,
                                                       attr))

    def has_func(self, attr):
        return hasattr(self.dll, attr)

    #  API Utility Functions

    @ctypes_param(ParamOut(c_ulong))
    def CHR_api_get_max_pairs(self):
        '''
        The CHR_api_get_max_pairs function gets the maximum number of pairs
        and multicast pairs allowed in a test for this installation of
        IxChariot.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        max_pairs : int
            The maximum number of pairs.

        '''
        pass

    @ctypes_param(ParamOut(c_char))
    def CHR_api_get_license_type(self):
        '''
        The CHR_api_get_license_type function returns the value of the current
        Ixia license type.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        license_type : int
            A pointer to the variable where the license type value
            (CHR_LICENSE_TYPE) will be returned.
        '''
        pass

    @ctypes_param(ParamOut(c_long))
    def CHR_api_get_license_expiration_time(self):
        '''
        The CHR_api_get_license_expiration_time function returns the
        expiration time for borrowed licenses
        (CHR_LICENSE_TYPE_FLOATING_BORROW).
        It returns 0 for NODE-LOCKED and FLOATING licenses.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        expiration_time : int
            A pointer to the variable where the license expiration time value
            will be returned.
        '''
        pass

    @ctypes_param(c_char, ParamOut(c_ushort))
    def CHR_api_get_reporting_port(self, protocol: int):
        '''
        The CHR_api_get_reporting_port function gets the port number used to
        report results to the IxChariot Console for the given network
        protocol type.

        Parameters
        ----------
        protocol : int
            The protocol type CHR_PROTOCOL_TCP or CHR_PROTOCOL_SPX.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        port : int
            A pointer to the variable where the port number should be returned.
            A value of zero indicates that IxChariot automatically selects the
            port when a test is run using the protocol for Console to Endpoint
            1 communications.
        '''
        pass

    @ctypes_param(c_int, ParamOut(bytes))
    def CHR_api_get_return_msg(self, return_code: int):
        '''
        The CHR_api_get_return_msg function gets the text message
        corresponding to the given IxChariot API return code.

        Parameters
        ----------
        return_code : int
            A code returned by an IxChariot API function.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        msg : str
            A pointer to the buffer where the text message should be returned.

        '''
        pass

    @ctypes_param(ParamOut(bytes, CHR_MAX_VERSION))
    def CHR_api_get_version(self):
        '''
        The CHR_api_get_version function gets the version of the IxChariot API.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        version : str
            A pointer to the buffer where the version should be returned.
        '''
        pass

    @ctypes_param(ParamOut(bytes, CHR_MAX_VERSION))
    def CHR_api_get_build_level(self):
        '''
        CHR_api_get_build_level

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        build_level : str
            A pointer to the buffer where the build_level should be returned.
        '''
        pass

    @ctypes_param(ParamOut(bytes, CHR_MAX_VERSION))
    def CHR_api_get_aptixia_version(self):
        '''
        CHR_api_get_aptixia_version

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        version : str
            A pointer to the buffer where the version should be returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_ERROR_INFO))
    def CHR_api_initialize(self, detail: int):
        '''
        The CHR_api_initialize function initializes the IxChariot API.
        This function must be called before any other IxChariot API function.

        Parameters
        ----------
        detail : int
            The detail level for extended error information.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        error_info : str
            A pointer to the buffer where the extended error information
            should be returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_ERROR_INFO), bytes, c_ulong,
                  c_ulong)
    def CHR_api_initialize_with_license_details(self,
                                                detail_level: int,
                                                server_name: str,
                                                pair_count: int,
                                                days_to_borrow: int
                                                ):
        '''
        The CHR_api_initialize function initializes the IxChariot API.
        This function must be called before any other IxChariot API function.

        Parameters
        ----------
        detail_level : int
            The detail level for extended error information.
        server_name : str
            The name of the license server to try checking out pairs from.
        pair_count : int
            The number of pairs to check out from the server.
        days_to_borrow : int
            The number of days to borrow the license for. If set to zero,
            the pairs will be checked out as release on exit.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        error_info : str
            A pointer to the buffer where the extended error information
            should be returned.
        '''
        pass

    @ctypes_param(c_char, c_ushort)
    def CHR_api_set_reporting_port(self, protocol: int, port: int):
        '''
        The CHR_api_set_reporting_port function sets or changes the port
        number used to report results to the Console.
        The port number can only be changed if the current process has not
        run a test. After the current process runs a test, the reporting port
        is allocated by the API and attempts to change it will result in
        a CHR_OBJECT_IN_USE return code.

        Parameters
        ----------
        protocol : str
            The protocol for which the port number is specified.
            This must be either int_TCP or int_SPX.
        port : int
            The port number in the range of 1 - 65535. Specifying a zero
            causes IxChariot to automatically select the port when a test is
            run using the given protocol for Console to
            Endpoint 1 communications.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_api_get_pair_type(self, handle: int):
        '''
        The CHR_api_get_pair_type function gets the pair type for a pair
        defined in a test. This enables you to identify the specific
        parameters available for that pair. For example,
        if the IxChariot test uses only regular pairs, then you can check for
        Average Throughput, Timing Records completed, and so forth.
        If the test uses VoIP pairs, you can check for Average MOS,
        Jitter delay variation, and so forth.

        Parameters
        ----------
        handle : int
            A handle returned by CHR_test_new() or CHR_mpair_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        type : str
            A pointer to the variable where the pair type identifier
            (CHR_PAIR_TYPE) is returned.
        '''
        pass

    #  Ixia
    @ctypes_param(bytes, c_ulong, ParamOut(bytes, CHR_MAX_ADDR_STRING))
    def CHR_api_get_port_mgmt_ip_list(self, port_mgmt_ip: str,
                                      ip_addr_count: int):
        '''
        The CHR_api_get_port_mgmt_ip_list function retrieves the list of
        available hardware performance pair port management IP addresses.
        These are the addresses that are used for the console to know how to
        reach E1 and for E1 to know how to reach E2 for hardware performance
        pairs and endpoints that reside on Ixia port CPUs.

        Parameters
        ----------
        port_mgmt_ip : CHR_CHAR
            The port management address as returned in a previous call to
            CHR_api_get_port_mgmt_ip_list.
            This identifies the port to which the network IP addresses are
            associated.
        ip_addr_count : int
            The count of strings the user is providing space for in ip_list.
            Zero when the user wants to know the total count of strings
            available from the system.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        ip_list : CHR_ADDR_STRING_P
            An array of address strings.
            Each index receives a single IP address from the internal port
            management IP list.
            The user must preallocate with the number of strings passed to the
            call in ip_addr_count.
            This may be CHR_NULL_HANDLE when ip_addr_count is 0 when the user
            is checking for the number of available addresses.
        ip_addr_read : int
            The pointer to the count of strings actually read when CHR_OK
            is returned.
            When CHR_BUFFER_TOO_SMALL is returned, this is the total count of
            addresses available from the system, regardless of what was passed
            in ip_addr_count.
        '''
        pass

    @ctypes_param(bytes, c_ulong, ParamOut(bytes, CHR_MAX_ADDR_STRING))
    def CHR_api_get_network_ip_list(self, port_mgmt_ip: str,
                                    ip_addr_count: int):
        '''
        The CHR_api_get_network_ip_list function retrieves the list of
        available hardware performance pair network IP addresses that are
        configured for the given port management IP address.
        These are the addresses that are used for the console as E1 and E2 for
        hardware performance pairs and endpoints running on the Ixia port CPU.

        Parameters
        ----------
        port_mgmt_ip : str
            The port management address as returned in a previous call to
            CHR_api_get_port_mgmt_ip_list.
            This identifies the port to which the network IP addresses are
            associated.
        ip_addr_count : int
            The count of strings the user is providing space for in ip_list.
            Zero when the user wants to know the total count of strings
            available from the system.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        ip_list : CHR_ADDR_STRING_P
            An array of address strings.
            Each index receives a single IP address from the internal network
            IP list based on the given port management address.
            The user must preallocate with the number of strings passed to
            the call in ip_addr_count. This may be CHR_NULL_HANDLE when ip
            _addr_count is 0 when the user is checking for the number of
            available addresses.
        ip_addr_read : int
            The pointer to the count of strings actually read when CHR_OK is
            returned.
            When CHR_BUFFER_TOO_SMALL is returned, this is the total count of
            addresses available from the system, regardless of what was passed
            in ip_addr_count.
        '''
        pass

    #  Licensing Control Functions

    @ctypes_param(ParamIn(bytes), ParamOut(c_ulong))
    def CHR_api_license_get_test_pair_count(self, test_file_name: str):
        '''
        The CHR_api_license_get_test_pair_count function returns a count of the
        number of pairs configured for the specified IxChariot test.
        This function can be called even if there is no license for the pairs.

        Parameters
        ----------
        test_file_name : str
            A handle returned by CHR_test_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        pair_count : int
            A pointer to the variable where the pair count is returned.
        '''
        pass

    @ctypes_param(c_ulong)
    def CHR_api_license_checkout_pairs(self, no_pairs: int):
        '''
        The CHR_api_license_checkout_pairs function checks out the specified
        number of pairs from the license server.
        This function is applicable only if the current license is either
        FLOATING or FLOATING_BORROW.

        Parameters
        ----------
        no_pairs : int
            The number of pairs to check out. The number of pairs specified
            must be positive.
            In addition, the actual number of pairs that will be checked-out
            from the server will be rounded to the next highest multiple of 10.
            For example, if you specify 14 as the value for noPairs, 20 pairs
            will be checked out.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        '''
        pass

    @ctypes_param()
    def CHR_api_license_checkin_pairs(self):
        '''
        The CHR_api_license_checkin_pairs function checks in to the license
        server any pairs that are presently checked out.
        This function will fail if the license type is neither FLOATING nor
        FLOATING_BORROW.
        It does nothing if there are no pairs checked-out.

        Parameters
        ----------

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        '''
        pass

    @ctypes_param(c_ulong)
    def CHR_api_license_change_borrow_time(self, days_to_borrow: int):
        '''
        The CHR_api_license_change_borrow_time function changes the expiration
        time for all the current licenses (console, VoIP, video.
        pairs, and so forth).
        It will fail if the current license type is neither FLOATING nor
        FLOATING_BORROW.
        Calling this function while IxChariot console is open will result in
        an error code being returned (CHR_FLOATING_LICENSE_IN_USE).

        Parameters
        ----------
        days_to_borrow : int
            The number of days for which the license is borrowed.
            If daysToBorrow is zero, floating licenses will be used.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        '''
        pass

    @ctypes_param(bytes)
    def CHR_api_license_change_license_server(self, server_name: str):
        '''
        The CHR_api_license_change_license_server function  changes the license
        server used to check out a floating license.
        It will check in any previously checked out licenses and try a check
        out with the same license parameters (pair count and borrow days) from
        the new server.

        Parameters
        ----------
        server_name : str
            The name of the new server to attempt the new license check out
            from.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        '''
        pass

    @ctypes_param(ParamOut(bytes))
    def CHR_api_license_get_license_server(self):
        '''
        The CHR_api_license_get_license_server function gets the name of the
        license server currently in use for license check out.

        Parameters
        ----------

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        server_name : str
            A pointer to the buffer where the server name should be returned.
        '''
        pass

    @ctypes_param(ParamOut(c_ulong))
    def CHR_api_license_get_borrow_days_remaining(self):
        '''
        The CHR_api_license_get_borrow_days_remaining function returns the
        number of borrow days remaining for the current license check out.
        This function returns:

        Parameters
        ----------

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        days_remaining : int
            A pointer to the variable where the number of remaining
            borrow-days is returned.
        '''
        pass

    #  QoS functions
    @ctypes_param(c_char, ParamIn(bytes), c_ubyte)
    def CHR_api_new_qos_tos_template(self, template_type: int,
                                     template_name: str,
                                     tos_mask: int):
        '''
        The CHR_api_new_qos_tos_template function creates a new TOS template in
        the IxChariot QoS template library.

        Parameters
        ----------
        template_type : int
            The type of template that will be created. This must be
            CHR_QOS_TEMPLATE_TOS_BIT_MASK, CHR_QOS_TEMPLATE_DIFFSERV,
            or CHR_QOS_TEMPLATE_L2_PRIORITY.
        template_name : str
            A string containing the QoS template name..
        tos_mask : int
            The TOS mask value to be used by the template, given as a decimal
            number.
            For example, if the desired TOS mask is 0110 0000, you would enter
            96 as the mask value.
            For Layer 2, must be in the 0-7 interval.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        '''
        pass

    @ctypes_param(ParamIn(bytes))
    def CHR_api_delete_qos_template(self, template_name: str):
        '''
        The CHR_api_delete_qos_template function deletes the specified QoS
        template from the IxChariot library of QoS templates.
        The template must be present in the servqual.
        dat file; otherwise the delete operation will fail.

        Parameters
        ----------
        template_name : str
            A string containing the QoS template name.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        '''
        pass

    @ctypes_param(c_char, ParamIn(bytes), c_ubyte)
    def CHR_api_modify_qos_tos_template(self, template_type: int,
                                        template_name: str,
                                        tos_mask: int):
        '''
        The CHR_api_modify_qos_tos_template function modifies the specified TOS
        template.
        The template must be present in the servqual.
        dat file; otherwise the modify operation will fail.

        Parameters
        ----------
        template_type : int
            The type of template that will be created. This must be
            CHR_QOS_TEMPLATE_TOS_BIT_MASK, CHR_QOS_TEMPLATE_DIFFSERV,
            or CHR_QOS_TEMPLATE_L2_PRIORITY.
        template_name : str
            A string containing the QoS template name..
        tos_mask : int
            The TOS mask value to be used by the template, given as a decimal
            number.
            For example, if the desired TOS mask is 0110 0000, you would enter
            96 as the mask value.
            For Layer 2, must be in the 0-7 interval.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        '''
        pass

    #  Common Error Functions
    #  (CHR_TEST_HANDLE/CHR_PAIR_HANDLE/CHR_MGROUP_HANDLE/CHR_MPAIR_HANDLE)

    @ctypes_param(c_ulong, c_ulong, ParamOut(bytes, CHR_MAX_ERROR_INFO))
    def CHR_common_error_get_info(self, handle: int, detail: int):
        '''
        The CHR_common_error_get_info function retrieves the extended error
        information for function calls and test run errors.

        Parameters
        ----------
        handle : int
            For a test, the handle returned by CHR_test_new.
            For an endpoint pair, the handle returned by CHR_pair_new() or
            CHR_test_get_pair().
            For a multicast group, the handle returned by CHR_mgroup_new() or
            CHR_test_get_mgroup().
            For a multicast pair, the handle returned by CHR_mpair_new() or
            CHR_mgroup_get_mpair().
        detail : int
            The detail level for extended error information.
            Refer to Error Detail Levels on page 3-3 for available levels.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        error_info : str
            A pointer to the buffer where the extended error information
            should be returned.
            If the buffer is valid but not large enough, truncated extended
            error information is returned..
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_int))
    def CHR_common_error_get_msg_num(self, handle: int):
        '''
        The CHR_common_error_get_msg_num function gets the IxChariot error
        message that applies to the extended error information for a function
        or test run error.

        Parameters
        ----------
        handle : int
            For a test, the handle returned by CHR_test_new.
            For an endpoint pair, the handle returned by CHR_pair_new() or
            CHR_test_get_pair().
            For a multicast group, the handle returned by CHR_mgroup_new() or
            CHR_test_get_mgroup().
            For a multicast pair, the handle returned by CHR_mpair_new() or
            CHR_mgroup_get_mpair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        msg_number : int
            A pointer to the variable where the message number should be
            returned.
            See the Message Reference for more information on messages.
        '''
        pass

    #  Common Results Extraction Functions
    #  (CHR_PAIR_HANDLE/CHR_MPAIR_HANDLE/CHR_TIMINGREC_HANDLE)

    @ctypes_param(c_ulong, ParamOut(c_double))
    def CHR_common_results_get_bytes_recv_e1(self, handle: int):
        '''
        The CHR_common_results_get_bytes_recv_e1 function gets the number of
        bytes received by Endpoint 1 from the test results in the given
        endpoint pair or timing record.
        This value does not apply for pairs defined with a streaming script.

        Parameters
        ----------
        handle : int
            For an endpoint pair, the handle returned by CHR_pair_new() or
            CHR_test_get_pair().
            For a timing record, the handle returned by
            CHR_pair_get_timing_record().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        bytes : float
            A pointer to the variable where the number of bytes received should
            be returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_double))
    def CHR_common_results_get_bytes_recv_e2(self, handle: int):
        '''
        The CHR_common_results_get_bytes_recv_e2 function gets the number of
        bytes received by Endpoint 2 from the test results in the given
        endpoint pair, multicast pair, or timing record.
        This value only applies to pairs defined with a streaming script since
        the received value may not be the same as the bytes_sent_e1 value.

        Parameters
        ----------
        handle : int
            For an endpoint pair, the handle returned by CHR_pair_new() or
            CHR_test_get_pair().
            For a multicast pair, the handle returned by CHR_mpair_new() or
            CHR_mgroup_get_mpair().
            For a timing record, the handle returned by
            CHR_pair_get_timing_record() or CHR_mpair_get_timing_record().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        bytes : float
            A pointer to the variable where the number of bytes received should
            be returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_double))
    def CHR_common_results_get_bytes_sent_e1(self, handle: int):
        '''
        The CHR_common_results_get_bytes_sent_e1 function gets the number of
        bytes sent by Endpoint 1 from the test results in the given endpoint
        pair, multicast pair, or timing record.

        Parameters
        ----------
        handle : int
            For an endpoint pair, the handle returned by CHR_pair_new() or
            CHR_test_get_pair().
            For a multicast pair, the handle returned by CHR_mpair_new() or
            CHR_mgroup_get_mpair().
            For a timing record, the handle returned by
            CHR_pair_get_timing_record() or CHR_mpair_get_timing_record().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        bytes : float
            A pointer to the variable where the number of bytes sent should be
            returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_double))
    def CHR_common_results_get_dg_dup_recv_e1(self, handle: int):
        '''
        The CHR_common_results_get_dg_dup_recv_e1 function gets the number of
        duplicate datagrams received by Endpoint 1 from the test results in the
        given endpoint pair or timing record.
        This value does not apply for pairs defined with a streaming script.

        Parameters
        ----------
        handle : int
            For an endpoint pair, the handle returned by CHR_pair_new() or
            CHR_test_get_pair().
            For a timing record, the handle returned by
            CHR_pair_get_timing_record().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        dg : float
            A pointer to the variable where the number of duplicate datagrams
            received by Endpoint 1 should be returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_double))
    def CHR_common_results_get_dg_dup_recv_e2(self, handle: int):
        '''
        The CHR_common_results_get_dg_dup_recv_e2 function gets the number of
        duplicate datagrams received by Endpoint 2 from the test results in the
        given endpoint pair, multicast pair, or timing record.

        Parameters
        ----------
        handle : int
            For an endpoint pair, the handle returned by CHR_pair_new() or
            CHR_test_get_pair().
            For a multicast pair, the handle returned by CHR_mpair_new() or
            CHR_mgroup_get_mpair().
            For a timing record, the handle returned by
            CHR_pair_get_timing_record() or CHR_mpair_get_timing_record().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        dg : float
            A pointer to the variable where the number of duplicate datagrams
            received should be returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_double))
    def CHR_common_results_get_dg_dup_sent_e1(self, handle: int):
        '''
        The CHR_common_results_get_dg_dup_sent_e1 function gets the total
        number of duplicate datagrams sent by Endpoint 1 from the test results
        in the given endpoint pair or timing record.
        This value does not apply for pairs defined with a streaming script.

        Parameters
        ----------
        handle : int
            For an endpoint pair, the handle returned by CHR_pair_new() or
            CHR_test_get_pair().
            For a timing record, the handle returned by
            CHR_pair_get_timing_record().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        dg : float
            A pointer to the variable where the number of duplicate datagrams
            sent should be returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_double))
    def CHR_common_results_get_dg_dup_sent_e2(self, handle: int):
        '''
        The CHR_common_results_get_dg_dup_sent_e2 function gets the number of
        duplicate datagrams sent by Endpoint 2 from the test results in the
        given endpoint pair or timing record.
        This value does not apply for pairs defined with a streaming script.

        Parameters
        ----------
        handle : int
            For an endpoint pair, the handle returned by CHR_pair_new() or
            CHR_test_get_pair().
            For a timing record, the handle returned by
            CHR_pair_get_timing_record().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        dg : float
            A pointer to the variable where the number of duplicate datagrams
            should be returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_double))
    def CHR_common_results_get_dg_lost_e1_to_e2(self, handle: int):
        '''
        The CHR_common_results_get_dg_lost e1_to_e2 function gets the total
        number of datagrams lost between Endpoint 1 and Endpoint 2 from the
        test results in the given endpoint pair, multicast pair, or timing
        record.

        Parameters
        ----------
        handle : int
            For an endpoint pair, the handle returned by CHR_pair_new() or
            CHR_test_get_pair().
            For a multicast pair, the handle returned by CHR_mpair_new() or
            CHR_mgroup_get_mpair().
            For a timing record, the handle returned by
            CHR_pair_get_timing_record() or CHR_mpair_get_timing_record().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        dg : float
            A pointer to the variable where the number of datagrams lost should
            be returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_double))
    def CHR_common_results_get_dg_out_of_order(self, handle: int):
        '''
        The CHR_common_results_get_dg_out_of_order function gets the number of
        datagrams received out of order by Endpoint 2 from the test results in
        the given endpoint pair, multicast pair, or timing record.
        This value only applies to pairs defined with a streaming script.

        Parameters
        ----------
        handle : int
            For an endpoint pair, the handle returned by CHR_pair_new() or
            CHR_test_get_pair().
            For a multicast pair, the handle returned by CHR_mpair_new() or
            CHR_mgroup_get_mpair().
            For a timing record, the handle returned by
            CHR_pair_get_timing_record() or CHR_mpair_get_timing_record().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        dg : float
            A pointer to the variable where the number of datagrams received
            out of order is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_double))
    def CHR_common_results_get_dg_recv_e1(self, handle: int):
        '''
        The CHR_common_results_get_dg_recv_e1 function gets the number of
        datagrams received by Endpoint 1 from the test results in the given
        endpoint pair or timing record.
        This value does not include duplicate datagrams.

        Parameters
        ----------
        handle : int
            For an endpoint pair, the handle returned by CHR_pair_new() or
            CHR_test_get_pair().
            For a timing record, the handle returned by
            CHR_pair_get_timing_record().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        dg : float
            A pointer to the variable where the number of datagrams sent is
            returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_double))
    def CHR_common_results_get_dg_recv_e2(self, handle: int):
        '''
        The CHR_common_results_get_dg_recv_e2 function gets the number of
        datagrams received by Endpoint 2 from the test results in the given
        endpoint pair, multicast pair, or timing record.
        This value does not include duplicate datagrams.

        Parameters
        ----------
        handle : int
            For an endpoint pair, the handle returned by CHR_pair_new() or
            CHR_test_get_pair().
            For a multicast pair, the handle returned by CHR_mpair_new() or
            CHR_mgroup_get_mpair().
            For a timing record, the handle returned by
            CHR_pair_get_timing_record() or CHR_mpair_get_timing_record().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        dg : float
            A pointer to the variable where the number of datagrams received by
            Endpoint 2 is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_double))
    def CHR_common_results_get_dg_sent_e1(self, handle: int):
        '''
        The CHR_common_results_get_dg_sent_e1 function gets the number of
        datagrams sent by Endpoint 1 from the test results in the given
        endpoint pair, multicast pair, or timing record.
        This value does not include retransmitted datagrams.

        Parameters
        ----------
        handle : int
            For an endpoint pair, the handle returned by CHR_pair_new() or
            CHR_test_get_pair().
            For a multicast pair, the handle returned by CHR_mpair_new() or
            CHR_mgroup_get_mpair().
            For a timing record, the handle returned by
            CHR_pair_get_timing_record() or CHR_mpair_get_timing_record().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        dg : float
            A pointer to the variable where the number of datagrams sent.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_double))
    def CHR_common_results_get_est_clock_error(self, handle: int):
        '''
        The CHR_common_results_get_est_clock_error function gets the maximum
        error in clock synchronization between the endpoints.

        Parameters
        ----------
        handle : int
            For an endpoint pair, the handle returned by CHR_pair_new() or
            CHR_test_get_pair().
            For a multicast pair, the handle returned by CHR_mpair_new() or
            CHR_mgroup_get_mpair().
            For a timing record, the handle returned by
            CHR_pair_get_timing_record() or CHR_mpair_get_timing_record().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        est_clock_error : float
            A pointer to the variable where the estimated clock error is
            returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_common_results_get_jitter_buffer_lost(self, handle: int):
        '''
        The CHR_common_results_get_jitter_buffer_lost function gets the number
        of datagrams that were lost due to the jitter buffer.
        This value is only available for VoIP pairs and timing records
        associated with a VoIP pair.

        Parameters
        ----------
        handle : int
            For an endpoint pair, the handle returned by CHR_voip_pair_new() or
            CHR_test_get_pair().
            For a timing record, the handle returned by
            CHR_pair_get_timing_record().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        result : int
            A pointer to the variable where the number of jitter buffer lost
            datagrams is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_double))
    def CHR_common_results_get_max_clock_error(self, handle: int):
        '''
        The CHR_common_results_get_max_clock_error function gets the maximum
        error in clock synchronization between the endpoints.

        Parameters
        ----------
        handle : int
            For an endpoint pair, the handle returned by CHR_pair_new() or
            CHR_test_get_pair().
            For a multicast pair, the handle returned by CHR_mpair_new() or
            CHR_mgroup_get_mpair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        max_clock_error : float
            A pointer to the variable where the maximum clock error is
            returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_double))
    def CHR_common_results_get_meas_time(self, handle: int):
        '''
        The CHR_common_results_get_meas_time function gets the measured time in
        seconds from the test results in the given endpoint pair, multicast
        pair, or timing record.

        Parameters
        ----------
        handle : int
            For an endpoint pair, the handle returned by CHR_pair_new() or
            CHR_test_get_pair().
            For a multicast pair, the handle returned by CHR_mpair_new() or
            CHR_mgroup_get_mpair().
            For a timing record, the handle returned by
            CHR_pair_get_timing_record() or CHR_mpair_get_timing_record().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        meastime : float
            A pointer to the variable where the measured time is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_double))
    def CHR_common_results_get_rtd(self, handle: int):
        '''
        The CHR_common_results_get_rtd function gets the round-trip delay for a
        voice over IP (VoIP) pair.

        Parameters
        ----------
        handle : int
            For an endpoint pair, the handle returned by CHR_pair_new() or
            CHR_test_get_pair().
            For a multicast pair, the handle returned by CHR_mpair_new() or
            CHR_mgroup_get_mpair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        rtd : float
            A pointer to the variable where the round-trip delay time is
            returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_double))
    def CHR_common_results_get_rtd_95pct_confidence(self, handle: int):
        '''
        The CHR_common_results_get_rtd_95pct_confidence function gets the 95%
        confidence interval for the round-trip delay time.

        Parameters
        ----------
        handle : int
            For an endpoint pair, the handle returned by CHR_pair_new() or
            CHR_test_get_pair().
            For a multicast pair, the handle returned by CHR_mpair_new() or
            CHR_mgroup_get_mpair().
            For a timing record, the handle returned by
            CHR_pair_get_timing_record() or CHR_mpair_get_timing_record().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        confidence : float
            A pointer to the variable where the 95% confidence interval is
            returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_double))
    def CHR_common_results_get_trans_count(self, handle: int):
        '''
        The CHR_common_results_get_trans_count function gets the transaction
        count from the test results in the given endpoint pair, multicast pair,
        or timing record.

        Parameters
        ----------
        handle : int
            For an endpoint pair, the handle returned by CHR_pair_new() or
            CHR_test_get_pair().
            For a multicast pair, the handle returned by CHR_mpair_new() or
            CHR_mgroup_get_mpair().
            For a timing record, the handle returned by
            CHR_pair_get_timing_record() or CHR_mpair_get_timing_record().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        count : float
            A pointer to the variable where the transaction count is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_common_results_get_e1_syn_tx(self, handle: int):
        '''
        The CHR_common_results_get_e1_syn_tx function retrieves from the test
        results in the given endpoint pair or timing record the number of TCP
        SYN packets transmitted by Endpoint 1.

        Parameters
        ----------
        handle : int
            One of the following:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        syn_tx : int
            A pointer to the variable to which the function returns the number
            of SYNs transmitted by Endpoint 1.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_common_results_get_e1_syn_rx(self, handle: int):
        '''
        The CHR_common_results_get_e1_syn_rx function retrieves from the test
        results in the given endpoint pair or timing record the number of TCP
        SYN packets received by Endpoint 1.

        Parameters
        ----------
        handle : int
            One of the following:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        syn_rx : int
            A pointer to the variable to which the function returns the number
            of SYNs received by Endpoint 1.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_common_results_get_e1_syn_failed(self, handle: int):
        '''
        The CHR_common_results_get_e1_syn_failed function retrieves from the
        test results in the given endpoint pair or timing record a count of the
        number of TCP connection attempts for which Endpoint 1 reset the
        connection before synchronization was established.

        Parameters
        ----------
        handle : int
            One of the following:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        syn_failed : int
            A pointer to the variable to which the function returns the count
            of TCP connection attempts for which Endpoint 1 reset the
            connection before synchronization was established.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_common_results_get_e1_conn_established(self, handle: int):
        '''
        The CHR_common_results_get_e1_conn_established function retrieves from
        the test results in the given endpoint pair or timing record a count of
        the number of TCP connections successfully established by Endpoint 1.

        Parameters
        ----------
        handle : int
            One of the following:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        conn_established : int
            A pointer to the variable to which the function returns the count
            of TCP connections successfully established by Endpoint 1.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_common_results_get_e1_fin_tx(self, handle: int):
        '''
        The CHR_common_results_get_e1_fin_tx function retrieves from the test
        results in the given endpoint pair or timing record the number of TCP
        FIN packets transmitted by Endpoint 1.

        Parameters
        ----------
        handle : int
            One of the following:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        fin_tx : int
            A pointer to the variable to which the function returns the number
            of FINs transmitted by Endpoint 1.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_common_results_get_e1_fin_rx(self, handle: int):
        '''
        The CHR_common_results_get_e1_fin_rx function retrieves from the test
        results in the given endpoint pair or timing record the number of TCP
        FIN packets received by Endpoint 1.

        Parameters
        ----------
        handle : int
            One of the following:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        fin_rx : int
            A pointer to the variable to which the function returns the number
            of FINs received by Endpoint 1.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_common_results_get_e1_ack_to_fin_tx(self, handle: int):
        '''
        The CHR_common_results_get_e1_ack_to_fin_tx function retrieves from the
        test results in the given endpoint pair or timing record the number of
        TCP ACK packets transmitted by Endpoint 1 in response to a FIN sent by
        Endpoint 2.

        Parameters
        ----------
        handle : int
            One of the following:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        fin_ack_tx : int
            A pointer to the variable to which the function returns the number
            of ACK packets transmitted by Endpoint 1 in response to a FIN sent
            by Endpoint 2.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_common_results_get_e1_ack_to_fin_rx(self, handle: int):
        '''
        The CHR_common_results_get_e1_ack_to_fin_rx function retrieves from the
        test results in the given endpoint pair or timing record the number of
        TCP ACK packets received by Endpoint 1 from Endpoint 2 in response to a
        FIN packet sent by Endpoint 1.

        Parameters
        ----------
        handle : int
            One of the following:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        fin_ack_rx : int
            A pointer to the variable to which the function returns the number
            of ACK packets received by Endpoint 1 from Endpoint 2 in response
            to a FIN packet sent by Endpoint 1.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_common_results_get_e1_rst_tx(self, handle: int):
        '''
        The CHR_common_results_get_e1_rst_tx function retrieves from the test
        results in the given endpoint pair or timing record the number of TCP
        RST (Reset) packets transmitted by Endpoint 1.

        Parameters
        ----------
        handle : int
            One of the following:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        rst_tx : int
            A pointer to the variable to which the function returns the number
            of TCP RST (Reset) packets transmitted by Endpoint 1.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_common_results_get_e1_rst_rx(self, handle: int):
        '''
        The CHR_common_results_get_e1_rst_rx function retrieves from the test
        results in the given endpoint pair or timing record the number of TCP
        RST (Reset) packets received by Endpoint 1.

        Parameters
        ----------
        handle : int
            One of the following:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        rst_rx : int
            A pointer to the variable to which the function returns the number
            of TCP RST (Reset) packets received by Endpoint 1.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_common_results_get_e1_tcp_retransmissions(self, handle: int):
        '''
        The CHR_common_results_get_e1_tcp_retransmissions function retrieves
        from the test results in the given endpoint pair or timing record a
        count of the number of packets retransmitted by Endpoint 1.

        Parameters
        ----------
        handle : int
            One of the following:
                For an endpoint pair, the handle returned by CHR_pair_new()
                or CHR_test_get_pair().
                For a timing record, the handle returned by
                CHR_pair_get_timing_record().
        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        tcp_retransmissions : int
            A pointer to the variable to which the function returns the count
            of packets retransmitted by Endpoint 1.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_common_results_get_e1_tcp_timeouts(self, handle: int):
        '''
        The CHR_common_results_get_e1_tcp_timeouts function retrieves from the
        test results in the given endpoint pair or timing record a count of the
        number of TCP connection timeouts that occurred on Endpoint 1.

        Parameters
        ----------
        handle : int
            One of the following:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        tcp_timeouts : int
            A pointer to the variable to which the function returns the count
            of the number of TCP timeouts that occurred on Endpoint 1
        '''
        pass

    #  Datagram Options Object Functions
    #  (CHR_DGOPTS_HANDLE)

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_dgopts_get_recv_timeout(self, datagram_options_handle: int):
        '''
        The CHR_dgopts_get_recv_timeout function gets the multicast datagram
        receive timeout in milliseconds.

        Parameters
        ----------
        datagram_options_handle : int
            The handle returned by CHR_test_get_dgopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        recv_timeout : int
            A pointer to the variable where the datagram receive timeout is
            returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_dgopts_get_retrans_count(self, datagram_options_handle: int):
        '''
        The CHR_dgopts_get_retrans_count function gets the datagram
        retransmission count.

        Parameters
        ----------
        datagram_options_handle : int
            The handle returned by CHR_test_get_dgopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        retrans_count : int
            A pointer to the variable where the datagram retransmission count
            is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_dgopts_get_retrans_timeout(self, datagram_options_handle: int):
        '''
        The CHR_dgopts_get_retrans_timeout function gets the datagram
        retransmission timeout in milliseconds.

        Parameters
        ----------
        datagram_options_handle : int
            The handle returned by CHR_test_get_dgopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        retrans_timeout : int
            A pointer to the variable where the datagram retransmission timeout
            is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_dgopts_get_TTL(self, datagram_options_handle: int):
        '''
        The CHR_dgopts_get_TTL function gets the multicast datagram time to
        live hop count.

        Parameters
        ----------
        datagram_options_handle : int
            The handle returned by CHR_test_get_dgopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        ttl : int
            A pointer to the variable where the time to live is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_dgopts_get_window_size(self, datagram_options_handle: int):
        '''
        The CHR_dgopts_get_window_size function gets the datagram window size
        in bytes.

        Parameters
        ----------
        datagram_options_handle : int
            The handle returned by CHR_test_get_dgopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        window_size : int
            A pointer to the variable where the datagram window size is
            returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_dgopts_get_low_sender_jitter(self, datagram_options_handle: int):
        '''
        The CHR_dgopts_get_low_sender_jitter function gets the value of the
        datagram low sender jitter flag that has been set for all the streaming
        pairs in the test.
        This flag is used to enable very precise timers to reduce the jitter
        on the sender.
        When the flag is enabled, datagrams are sent at more precise intervals.

        Parameters
        ----------
        datagram_options_handle : int
            The handle returned by CHR_test_get_dgopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        flag : int
            A pointer to the variable where the value of the datagram low
            sender jitter flag is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_dgopts_get_limit_data_rate(self, datagram_options_handle: int):
        '''
        The CHR_dgopts_get_limit_data_rate function gets the value of the
        datagram data rate limit flag that has been set for all the streaming
        pairs in the test.
        This flag is used to enable a data rate (throughput) limit measured on
        intervals much smaller than a timing record interval.

        Parameters
        ----------
        datagram_options_handle : int
            The handle returned by CHR_test_get_dgopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        flag : int
            A pointer to the variable where the value of the datagram data rate
            limit flag is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_dgopts_get_data_rate_limit(self, datagram_options_handle: int):
        '''
        The CHR_dgopts_get_data_rate_limit function gets the datagram data rate
        limit that has been set for all the streaming pairs in the test.
        The data rate limit is expressed as a percent of the required data
        rate defined in the script.
        For example, a value of 100 means that the limit is equal to 100% of
        the required data rate.

        Parameters
        ----------
        datagram_options_handle : int
            The handle returned by CHR_test_get_dgopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        data_rate_limit : int
            A pointer to the variable where the datagram data rate limit is
            returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_dgopts_get_measured_interval(self, datagram_options_handle: int):
        '''
        The CHR_dgopts_get_measured_interval function gets the datagram
        measured interval that has been set for all the streaming pairs in the
        test.
        The measured interval is the interval (in milliseconds) over which
        IxChariot enforces the data rate limit.

        Parameters
        ----------
        datagram_options_handle : int
            The handle returned by CHR_test_get_dgopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        measured_interval : int
            A pointer to the variable where the datagram measured interval is
            returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_dgopts_get_RTP_use_extended_headers(self,
                                                datagram_options_handle: int):
        '''
        The CHR_dgopts_get_RTP_use_extended_headers function gets the
        use extension header setting defined for RTP traffic.

        Parameters
        ----------
        datagram_options_handle : int
            The handle returned by CHR_test_get_dgopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        flag : int
            A pointer to the variable where the use extension header Boolean
            value is returned.
            The variable can take either of the following values:
                CHR_TRUE – The RTP datagram includes an extension header.
                In this case, the RTP timestamp field contains a monotonous
                timestamp value, while the header extension contains a time
                value derived from the system clock.
                CHR_FALSE – The RTP datagram does not include an extension
                header.
                In this case, the RTP timestamp field contains a time value
                derived from the system clock.
        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_dgopts_set_recv_timeout(self,
                                    datagram_options_handle: int,
                                    recv_timeout: int):
        '''
        The CHR_dgopts_set_recv_timeout function sets or changes the multicast
        datagram receive timeout in milliseconds.

        Parameters
        ----------
        datagram_options_handle : int
            The handle returned by CHR_test_get_dgopts().
        recv_timeout : int
            The time in milliseconds. The range of valid values is 1 to
            999,999.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_dgopts_set_retrans_count(self, datagram_options_handle: int,
                                     retrans_count: int):
        '''
        The CHR_dgopts_set_retrans_count function sets or changes the datagram
        retransmission count.

        Parameters
        ----------
        datagram_options_handle : int
            The handle returned by CHR_test_get_dgopts().
        retrans_count : int
            The number of retransmissions before aborting.
            The range of valid values is 1 to 999.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_dgopts_set_retrans_timeout(self, datagram_options_handle: int,
                                       retrans_timeout: int):
        '''
        The CHR_dgopts_set_retrans_timeout function sets or changes datagram
        retransmission timeout in milliseconds.

        Parameters
        ----------
        datagram_options_handle : int
            The handle returned by CHR_test_get_dgopts().
        retrans_timeout : int
            Retransmission timeout in milliseconds.
            The range of valid values is 1 to 99999.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_dgopts_set_TTL(self, datagram_options_handle: int, ttl: int):
        '''
        The CHR_dgopts_set_TTL function sets or changes the multicast datagram
        time to live hop count.

        Parameters
        ----------
        datagram_options_handle : int
            The handle returned by CHR_test_get_dgopts().
        ttl : int
            The time to live hop count. The range of valid values is 0 to 255.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_dgopts_set_window_size(self, datagram_options_handle: int,
                                   window_size: int):
        '''
        The CHR_dgopts_set_window_size function sets or changes the datagram
        window size in bytes.

        Parameters
        ----------
        datagram_options_handle : int
            The handle returned by CHR_test_get_dgopts().
        window_size : int
            The datagram window size in bytes.
            The range of valid values is 1 to 9999999.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_dgopts_set_low_sender_jitter(self, datagram_options_handle: int,
                                         flag: int):
        '''
        The CHR_dgopts_set_low_sender_jitter function sets the datagram low
        sender jitter flag for all the streaming pairs in the test.
        This flag is used to enable very precise timers to reduce the jitter
        on the sender.
        When the flag is enabled, datagrams are sent at more precise intervals.

        Parameters
        ----------
        datagram_options_handle : int
            The handle returned by CHR_test_get_dgopts().
        flag : int
            The value of the datagram low sender jitter flag:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_dgopts_set_limit_data_rate(self, datagram_options_handle: int,
                                       flag: int):
        '''
        The CHR_dgopts_set_limit_data_rate function sets the datagram data rate
        limit flag for all the streaming pairs in the test.
        This flag is used to enable a data rate (throughput) limit measured on
        intervals much smaller than a timing record interval.

        Parameters
        ----------
        datagram_options_handle : int
            The handle returned by CHR_test_get_dgopts().
        flag : int
            The value of the datagram data rate limit flag:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_dgopts_set_data_rate_limit(self, datagram_options_handle: int,
                                       data_rate_limit: int):
        '''
        The CHR_dgopts_set_data_rate_limit function sets the datagram data rate
        limit for all the streaming pairs in the test.

        Parameters
        ----------
        datagram_options_handle : int
            The handle returned by CHR_test_get_dgopts().
        data_rate_limit : int
            The datagram data rate limit.
            The data rate limit is expressed as a percent of the required data
            rate defined in the script.
            For example, a value of 100 means that the limit is equal to 100%
            of the required data rate.
            The valid range of values is from 100 through 200.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_dgopts_set_measured_interval(self, datagram_options_handle: int,
                                         measured_interval: int):
        '''
        The CHR_dgopts_set_measured_interval function sets the datagram
        measured interval for all the streaming pairs in the test.

        Parameters
        ----------
        datagram_options_handle : int
            The handle returned by CHR_test_get_dgopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        measured_interval : int
            The datagram measured interval.
            This is the interval (in milliseconds) over which IxChariot
            enforces the data rate limit.
            The valid range of values is from 1 through 999,999.
            You will typically set this value to match the interval over which
            network devices check for throughput spikes.
        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_dgopts_set_RTP_use_extended_headers(self,
                                                datagram_options_handle: int,
                                                flag: int):
        '''
        The CHR_dgopts_set_RTP_use_extended_headers function sets the
        use extension header option for RTP traffic.

        Parameters
        ----------
        datagram_options_handle : int
            The handle returned by CHR_test_get_dgopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        flag : int
            A Boolean variable that sets the use extension header option.
            The variable can take either of the following values:
        '''
        pass

    #  Traceroute Hop Record Object Functions
    #  (CHR_HOPREC_HANDLE)

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_ADDR))
    def CHR_hoprec_get_hop_address(self, hoprec_handle: int):
        '''
        The CHR_hoprec_get_hop_address function gets the address of a
        particular hop from a traceroute.

        Parameters
        ----------
        hoprec_handle : int
            A handle returned by CHR_tracert_pair_get_hop_record.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        hop_address : str
            A pointer to the buffer where the address is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_hoprec_get_hop_latency(self, hoprec_handle: int):
        '''
        The CHR_hoprec_get_hop_latency function gets the number of milliseconds
        it took to reach the hop from the Endpoint 1 in a traceroute.

        Parameters
        ----------
        hoprec_handle : int
            A handle returned by CHR_tracert_pair_get_hop_record.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        hop_latency : int
            A pointer to the buffer where the latency value is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes))
    def CHR_hoprec_get_hop_name(self, hoprec_handle: int):
        '''
        The CHR_hoprec_get_hop_name function gets the resolved name of a hop in
        a traceroute.

        Parameters
        ----------
        hoprec_handle : int
            A handle returned by CHR_tracert_pair_get_hop_record.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        hop_name : str
            A pointer to the buffer where the hop name is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_hoprec_get_hop_number(self, hoprec_handle: int):
        '''
        The CHR_hoprec_get_hop_number function gets the number of hops before a
        traceroute was completed.
        An index of 0 gets the first hop record, while an index of 1 gets the
        second hop record, and so on.

        Parameters
        ----------
        hoprec_handle : int
            A handle returned by CHR_tracert_pair_get_hop_record.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        hop_number : int
            A pointer to the buffer where the hop number is returned.
        '''
        pass

    #  Multicast Group Object Functions
    #  (CHR_MGROUP_HANDLE)

    @ctypes_param(c_ulong, c_ulong)
    def CHR_mgroup_add_mpair(self, mgroup_handle: int, mpair_handle: int):
        '''
        The CHR_mgroup_add_mpair function adds the given multicast pair to the
        given multicast group.
        A multicast pair handle can only be added to one multicast group and
        can only be added once to that group.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().
        mpair_handle : int
            A handle returned by CHR_mpair_new().
            The multicast pair handle is checked to ensure that it refers to a
            properly defined multicast pair before the mpair is added to the
            multicast group.
            If not properly defined, CHR_OBJECT_INVALID is returned.
            This mpair must not be owned by any other mgroup.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_mgroup_copy(self, to_mgroup_handle: int, from_mgroup_handle: int):
        '''
        The CHR_mgroup_copy function copies the attributes of the source
        multicast group to the destination multicast group.
        This does not include any results information.

        Parameters
        ----------
        to_mgroup_handle : int
            A handle for the destination, returned by CHR_mgroup_new() or
            CHR_test_get_mgroup().
        from_mgroup_handle : int
            A handle for the source, returned by CHR_mgroup_new() or
            CHR_test_get_mgroup().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        '''
        pass

    @ctypes_param(c_ulong)
    def CHR_mgroup_delete(self, mgroup_handle: int):
        '''
        The CHR_mgroup_delete function frees all memory associated with the
        given multicast group.
        <META NAME="Keywords" CONTENT="Multicast Group Object
        Functions:CHR_mgroup_delete, Return Codes">

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().
            After verifying that the handle refers to a valid multicast group
            object, it is checked to ensure that it is not referenced by a test
            object known by the API.
            The multicast group object is not deleted if it is contained by a
            test object.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_APPL_SCRIPT_NAME))
    def CHR_mgroup_get_appl_script_name(self, mgroup_handle: int):
        '''
        The CHR_mgroup_get_appl_script_name function gets the application
        script name for the given multicast group.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        script_name : str
            A pointer to the buffer where the script name is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_APP_GROUP_COMMENT))
    def CHR_mgroup_get_comment(self, mgroup_handle: int):
        '''
        The CHR_mgroup_get_comment function gets the comment for the given
        multicast group.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        comment : str
            A pointer to the buffer where the comment is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_ADDR))
    def CHR_mgroup_get_console_e1_addr(self, mgroup_handle: int):
        '''
        The CHR_mgroup_get_console_e1_addr function gets the address by which
        the Console knows Endpoint 1 for the given multicast group.
        This attribute applies only when the
        CHR_mgroup_set_use_console_e1_values function sets the "use" attribute
        to CHR_TRUE.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        console_e1_name : str
            A pointer to the buffer where the address is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_mgroup_get_console_e1_protocol(self, mgroup_handle: int):
        '''
        The CHR_mgroup_get_console_e1_protocol function gets the Console to
        Endpoint 1 network protocol for the given multicast group.
        This attribute applies only when the
        CHR_mgroup_set_use_console_e1_values function sets the "use" attribute
        to CHR_TRUE.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        protocol : int
            A pointer to the variable where the protocol is returned. See the
            CHR_mgroup_set_console_e1_protocol on page 4-256 function for
            applicable protocols.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_ADDR))
    def CHR_mgroup_get_e1_addr(self, mgroup_handle: int):
        '''
        The CHR_mgroup_get_e1_addr function gets the Endpoint 1 address for the
        given multicast group.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        e1_name : str
            A pointer to the buffer where the Endpoint 1 address is returned.
        '''
        pass

    @ctypes_param(c_ulong, c_char, ParamOut(bytes, CHR_MAX_CFG_PARM))
    def CHR_mgroup_get_e1_config_value(self,
                                       mgroup_handle: int,
                                       parameter: int):
        '''
        The CHR_mgroup_get_e1_config_value function gets an Endpoint 1
        configuration value from the multicast group.
        The configuration information is returned from the endpoint during
        test execution.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().
        parameter : int
            One of the CHR_CFG_PARM values.
            See "Typedefs and Enumerations" for CHR_CFG_PARM values.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        value : str
            One of the CHR_CFG_PARM values.
            See "Typedefs and Enumerations" for CHR_CFG_PARM values.
        '''
        pass

    @ctypes_param(c_ulong, c_ulong, ParamOut(c_ulong))
    def CHR_mgroup_get_mpair(self, mgroup_handle: int, index: int):
        '''
        The CHR_mgroup_get_mpair function gets the handle for the multicast
        pair that corresponds to the given index number in the given multicast
        group.
        The handle returned by this function is needed for other function
        calls to operate on this object.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().
        index : int
            An index into the array of multicast pairs.
            The index parameter is determined by the order in which mpairs were
            added to this multicast group.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        mpair_handle : int
            A pointer to the variable where the multicast pair handle is
            returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_mgroup_get_mpair_count(self, mgroup_handle: int):
        '''
        The CHR_mgroup_get_mpair_count function gets the number of multicast
        pairs owned by the given multicast group.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        mpair_count : int
            A pointer to the variable where the number of multicast pairs is
            returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_MULTICAST_ADDR))
    def CHR_mgroup_get_multicast_addr(self, mgroup_handle: int):
        '''
        The CHR_mgroup_get_multicast_addr function gets the multicast IP
        address for the given multicast group.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        addr : str
            A pointer to the buffer where the multicast IP address is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ushort))
    def CHR_mgroup_get_multicast_port(self, mgroup_handle: int):
        '''
        The CHR_mgroup_get_multicast_port function gets the multicast port
        number for the given multicast group.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        port : int
            A pointer to the variable where the multicast port number is
            returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_APP_GROUP_NAME))
    def CHR_mgroup_get_name(self, mgroup_handle: int):
        '''
        The CHR_mgroup_get_name function gets the name for the given multicast
        group.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        name : str
            A pointer to the buffer where the multicast group name is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_mgroup_get_protocol(self, mgroup_handle: int):
        '''
        The CHR_mgroup_get_protocol function gets the Endpoint 1 to Endpoint 2
        protocol for the given multicast group.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        protocol : int
            A pointer to the variable where the protocol is returned.
            See the CHR_mgroup_set_protocol on page 4-269 function for
            applicable protocols.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_QOS_NAME))
    def CHR_mgroup_get_qos_name(self, mgroup_handle: int):
        '''
        The CHR_mgroup_get_qos_name function gets the quality of service name
        for the given multicast group.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        qos_name : str
            A pointer to the buffer where the quality of service name is
            returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_FILE_PATH))
    def CHR_mgroup_get_script_filename(self, mgroup_handle: int):
        '''
        The CHR_mgroup_get_script_filename function gets the script filename
        for the given multicast group.
        The script filename is returned without path information.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        file_name : str
            A pointer to the buffer where the script filename is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_mgroup_get_use_console_e1_values(self, mgroup_handle: int):
        '''
        The CHR_mgroup_get_use_console_e1_values function gets whether the
        Console-to-Endpoint 1 values are to be used.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        use_values : int
            A pointer to the variable where the boolean value is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes),
                  ParamOut(bytes, CHR_MAX_SCRIPT_VARIABLE_VALUE))
    def CHR_mgroup_get_script_variable(self, mgroup_handle: int, name: str):
        '''
        The CHR_mgroup_get_script_variable function gets the value of a
        specified variable from the script defined for use by the given
        multicast group.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().
        name : str
            A string containing the name of the script variable.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        value : str
            The buffer to which the value of the script variable is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes),
                  ParamOut(bytes, CHR_MAX_EMBEDDED_PAYLOAD_SIZE))
    def CHR_mgroup_get_script_embedded_payload(self,
                                               mgroup_handle: int,
                                               variable_name: str):
        '''
        The CHR_mgroup_get_script_embedded_payload function gets the value of
        the embedded payload data from the script used by this multicast group.
        This function requires that the variable is of type send_datatype.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().
        variable_name : str
            A string containing the name of the send_datatype script variable
            that is used by the given multicast group.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        payload : str
            The buffer to which the embedded script payload is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes), ParamOut(bytes, CHR_MAX_FILENAME),
                  ParamOut(c_char))
    def CHR_mgroup_get_payload_file(self,
                                    mgroup_handle: int,
                                    variable_name: str):
        '''
        The CHR_mgroup_get_payload_file function gets the name of the payload
        file that is defined for the script used by the given multicast group,
        as well as the embedded flag (indicating whether the payload is
        embedded or referenced).
        This function requires that the variable is of type send_datatype, and
        that send_datatype is set to "Payload file", rather than "Embedded
        payload".

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().
        variable_name : str
            A string containing the name of the send_datatype script variable
            that is used by the given multicast group.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        filename : str
            The buffer where the name of the payload file will be returned.
        embedded : int
            A pointer to the variable where the embedded payload flag is
            returned. The values for the flag are:
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_mgroup_is_udp_RFC768_streaming(self, mgroup_handle: int):
        '''
        The CHR_ mgroup_is_udp_RFC768_streaming function determines whether or
        not the RFC 768 option is enabled in the script for the specified
        multicast group.
        If the option is present in the script, and it is enabled, the
        function returns TRUE.
        In all other cases, it returns FALSE.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mpair_new() or CHR_mgroup_get_mpair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        used : int
            A pointer to the variable where the boolean value is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_mgroup_is_disabled(self, mgroup_handle: int):
        '''
        The CHR_mgroup_is_disabled function determines whether or not the pairs
        in the specified multicast group or video multicast group are disabled.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by any of the following functions:
            CHR_mgroup_new(), CHR_video_mgroup_new(), or CHR_test_get_mgroup().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        disabled : int
            A pointer to the variable where the Boolean value is returned.
            The returned values can be:
                CHR_TRUE: All the pairs in the specified multicast group or
                video multicast group are disabled.
                CHR_FALSE: All the pairs in the specified multicast group or
                video multicast group are enabled.
        '''
        pass

    @ctypes_param(ParamOut(c_ulong))
    def CHR_mgroup_new(self):
        '''
        The CHR_mgroup_new function creates a new multicast group object and
        initializes it to object default values.
        Note that the object default values do not use the default values
        specified in the Chariot Options Menu.
        See Multicast Group Object Default Values on page 2-11 for the object
        default values.

        Parameters
        ----------

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        mgroup_handle : int
            A pointer to the variable where the handle for the new multicast
            group is returned.
            The handle returned by this function is needed for other function
            calls to operate on this object.
        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_mgroup_remove_mpair(self, mgroup_handle: int, mpair_handle: int):
        '''
        The function CHR_mgroup_remove_mpair removes a multicast pair from a
        multicast group.
        The multicast group must be unowned or locked.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().
        mpair_handle : int
            A handle returned by CHR_mpair_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_mgroup_set_comment(self, mgroup_handle: int, comment: str):
        '''
        The CHR_mgroup_set_comment function sets or changes the comment for the
        given multicast group.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().
        comment : str
            A string containing the multicast group comment.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_mgroup_set_console_e1_addr(self,
                                       mgroup_handle: int,
                                       console_e1_name: str):
        '''
        The CHR_mgroup_set_console_e1_addr function sets or changes the address
        by which the Console knows Endpoint 1 for the given multicast group.
        This attribute applies only when the
        CHR_mgroup_set_use_console_e1_values function sets the "use" attribute
        to CHR_TRUE.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().
        console_e1_name : str
            A string containing the endpoint address.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_mgroup_set_console_e1_protocol(self,
                                           mgroup_handle: int,
                                           protocol: int):
        '''
        The CHR_mgroup_set_console_e1_protocol function sets or changes the
        Console to Endpoint 1 network protocol for the given multicast group.
        This attribute applies only when the
        CHR_mgroup_set_use_console_e1_values function sets the "use" attribute
        to CHR_TRUE.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().
        protocol : int
            A protocol type: CHR_PROTOCOL_TCP, CHR_PROTOCOL_TCP6, or
            CHR_PROTOCOL_SPX.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_mgroup_set_e1_addr(self, mgroup_handle: int, e1_name: str):
        '''
        The CHR_mgroup_set_e1_addr function sets or changes the Endpoint 1
        address for the given multicast group.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().
        e1_name : str
            A string containing the Endpoint 1 address (IPv4 or IPv6).

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_mgroup_set_lock(self, mgroup_handle: int, lock: int):
        '''
        The function CHR_mgroup_set_lock locks an unlocked multicast group
        object if lock is CHR_TRUE, or unlocks a locked multicast group object
        if lock is CHR_FALSE.
        An owned object must be locked--disabled for validationbefore any of
        its attributes can be modified (using the set subcommand).
        To enable validation, all objects owned by a test (including multicast
        pairs owned by the test's multicast groups) must be unlocked before the
        test can be run or saved.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_pair_mgroup() or CHR_test_get_mgroup.
        lock : int
            A CHR_BOOLEAN, where CHR_TRUE locks the (unlocked) multicast group
            object, and CHR_FALSE unlocks the (locked) object.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_mgroup_set_multicast_addr(self, mgroup_handle: int, addr: str):
        '''
        The CHR_mgroup_set_multicast_addr function sets or changes the
        multicast IP address for the given multicast group.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().
        addr : str
            A string containing the multicast IP address.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_ushort)
    def CHR_mgroup_set_multicast_port(self, mgroup_handle: int, port: int):
        '''
        The CHR_mgroup_set_multicast_port function sets or changes the
        multicast port number for the given multicast group.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().
        port : int
            A multicast port number.
            The range of valid port numbers is 1 to 65535.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_mgroup_set_name(self, mgroup_handle: int, name: str):
        '''
        The CHR_mgroup_set_name function sets or changes the name of the given
        multicast group.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().
        name : str
            A string containing the name for the multicast group.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_mgroup_set_protocol(self, mgroup_handle: int, protocol: int):
        '''
        The CHR_mgroup_set_protocol function sets or changes the Endpoint 1 to
        Endpoint 2 protocol for the given multicast group.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().
        protocol : int
            A protocol type: CHR_PROTOCOL_UDP,CHR_PROTOCOL_UDP6,
            CHR_PROTOCOL_RTP, or CHR_PROTOCOL_RTP6.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_mgroup_set_qos_name(self, mgroup_handle: int, qos_name: str):
        '''
        The CHR_mgroup_set_qos_name function sets or changes the quality of
        service name for the given multicast group.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().
        qos_name : str
            A string containing quality of service name.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes), ParamIn(bytes))
    def CHR_mgroup_set_script_variable(self,
                                       mgroup_handle: int,
                                       name: str,
                                       value: str):
        '''
        The CHR_mgroup_set_script_variable function modifies the value of a
        variable in the script defined for use by the given multicast group.
        The script variable name is checked to ensure that it exists in the
        defined script.
        CHR_NO_SUCH_OBJECT is returned if the variable does not exist in the
        script.
        The variable value is checked to ensure that it is valid for that
        variable in that script.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().
        name : str
            A string containing the name of the script variable.
        value : str
            A string containing the value for the script variable.
            Use the following table to determine the valid string entries:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes), ParamIn(bytes))
    def CHR_mgroup_set_script_embedded_payload(self,
                                               mgroup_handle: int,
                                               variable_name: str,
                                               payload: str):
        '''
        The CHR_mgroup_set_script_embedded_payload function modifies the value
        of a send_datatype variable in the script defined for use by the given
        multicast group.
        The type of the variable is automatically set to "Embedded payload".

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().
        variable_name : str
            A string containing the name of the script variable.
        payload : str
            A pointer to the buffer that holds the payload.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes), ParamIn(bytes), c_char)
    def CHR_mgroup_set_payload_file(self, mgroup_handle: int,
                                    variable_name: str,
                                    filename: str,
                                    embedded: int):
        '''
        The CHR_mgroup_set_payload_file function modifies the value of a
        send_datatype variable in the script defined for use by the given
        multicast group.
        It allows a user to specify a file whose content will be used as
        payload when running the script.
        This function sets the variable type to "Embedded payload" as well.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().
        variable_name : str
            A string containing the name of a send_datatype script variable.
        filename : str
            The name of the file containing the payload data.
        embedded : int
            If set to CHR_TRUE, the payload file will be embedded within the
            script. If set to CHR_FALSE, the script will contain a reference to
            the external file. The recommended option is CHR_TRUE.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_mgroup_set_use_console_e1_values(self,
                                             mgroup_handle: int,
                                             use_values: int):
        '''
        The CHR_mgroup_set_use_console_e1_values function sets or changes
        whether the Console-to-Endpoint 1 values are to be used.
        If the value is set to CHR_TRUE, the Console to Endpoint 1 address and
        Console to Endpoint 1 Quality Of Service name must be properly defined
        before the test is run.
        The Console to Endpoint 1 protocol defaults to TCP and may be changed
        if needed.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().
        use_values : int
            Specifies CHR_TRUE or CHR_FALSE to indicate whether the
            Console-to-Endpoint 1 values are to be used.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_mgroup_use_script_filename(self,
                                       mgroup_handle: int,
                                       file_name: str):
        '''
        The CHR_mgroup_use_script_filename function sets or changes the script
        file to be used by the given multicast group.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_mgroup_new() or CHR_test_get_mgroup().
        file_name : str
            A string containing the new script filename. The script filename
            may be specified with a full or relative pathname.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_mgroup_disable(self, mgroup_handle: int, disable: int):
        '''
        The CHR_mgroup_disable function disables or enables all of the pairs
        assigned to the specified multicast group or video multicast group.
        IxChariot ignores any disabled pairs when running a test.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by any of the following functions:
            CHR_mgroup_new(), CHR_video_mgroup_new(), or CHR_test_get_mgroup().
        disable : int
            Specifies the action to perform:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Multicast Pair Object Functions
    #  (CHR_MPAIR_HANDLE)

    @ctypes_param(c_ulong)
    def CHR_mpair_delete(self, mpair_handle: int):
        '''
        The CHR_mpair_delete function frees all memory associated with the
        given multicast pair.

        Parameters
        ----------
        mpair_handle : int
            A handle returned by CHR_mpair_new() or CHR_mgroup_get_mpair().
            After verifying that the handle refers to a multicast pair object,
            it is checked to ensure that it is not referenced by a multicast
            object known by the API. The multicast pair object cannot be
            deleted if it is referenced.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_ADDR))
    def CHR_mpair_get_e2_addr(self, mpair_handle: int):
        '''
        The CHR_mpair_get_e2_addr function gets the Endpoint 2 address for the
        given multicast pair.

        Parameters
        ----------
        mpair_handle : int
            A handle returned by CHR_mpair_new() or CHR_mgroup_get_mpair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        e2_name : str
            A pointer to the buffer where the Endpoint 2 address is returned.
        '''
        pass

    @ctypes_param(c_ulong, c_char, ParamOut(bytes, CHR_MAX_CFG_PARM))
    def CHR_mpair_get_e2_config_value(self, pair_handle: int, parameter: int):
        '''
        The CHR_mpair_get_e2_config_value function gets an Endpoint 2
        configuration value from the multicast pair.
        The configuration information is returned from the endpoint during
        test execution.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_mpair_new() or CHR_mgroup_get_mpair().
        parameter : int
            One of the CHR_CFG_PARM values. See Typedefs and Enumerations on
            page 4-612 for CHR_CFG_PARM values.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        value : str
            One of the CHR_CFG_PARM values.
            See Typedefs and Enumerations on page 4-612 for CHR_CFG_PARM
            values.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_ADDR))
    def CHR_mpair_get_setup_e1_e2_addr(self, mpair_handle: int):
        '''
        The CHR_mpair_get_setup_e1_e2_addr function gets the address by which
        Endpoint 1 knows Endpoint 2 for purposes of test setup.
        This attribute applies only when the
        CHR_mpair_set_use_setup_e1_e2_values function sets the "use" attribute
        to CHR_TRUE.

        Parameters
        ----------
        mpair_handle : int
            A handle returned by CHR_mpair_new() or CHR_mgroup_get_mpair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        e2_name : str
            A pointer to the buffer where the address is returned.
        '''
        pass

    @ctypes_param(c_ulong, c_ulong, ParamOut(c_ulong))
    def CHR_mpair_get_timing_record(self, mpair_handle: int, index: int):
        '''
        The CHR_mpair_get_timing_record function gets the handle for the
        specified timing record from the results for the given multicast pair.
        The handle returned by this function is needed for other function
        calls to operate on this object.

        Parameters
        ----------
        mpair_handle : int
            A handle returned by CHR_mpair_new() or CHR_mgroup_get_mpair().
        index : int
            The number indicating a specific timing record. The number is
            determined by the order in which timing records were received from
            the endpoints.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        timing_record_handle : int
            A pointer to the variable where the handle of the timing record
            is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_mpair_get_timing_record_count(self, mpair_handle: int):
        '''
        The CHR_mpair_get_timing_record_count function gets the number of
        timing records in the results for the given multicast pair.

        Parameters
        ----------
        mpair_handle : int
            A handle returned by CHR_mpair_new() or CHR_mgroup_get_mpair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        count : int
            A pointer to the variable where the number of timing records is
            returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_mpair_get_use_setup_e1_e2_values(self, mpair_handle: int):
        '''
        The CHR_mpair_get_use_setup_e1_e2_values function gets whether to use
        the values by which Endpoint 1 knows Endpoint 2 for purposes of test
        setup.

        Parameters
        ----------
        mpair_handle : int
            A handle returned by CHR_mpair_new() or CHR_mgroup_get_mpair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        use : int
            A pointer to the variable where the boolean value is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_mpair_get_runStatus(self, mpair_handle: int):
        '''
        The CHR_mpair_get_runStatus function returns the run status for this
        multicast pair.

        Parameters
        ----------
        mpair_handle : int
            A multicast pair object handle returned by CHR_mpair_new() or
            CHR_mgroup_get_mpair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        run_status : int
            A pointer to the variable where the run status value is returned.
            The following status types are applicable:
            CHR_PAIR_RUNSTATUS_UNINITIALIZED
            CHR_PAIR_RUNSTATUS_INITIALIZING_1
            CHR_PAIR_RUNSTATUS_INITIALIZING_2
            CHR_PAIR_RUNSTATUS_INITIALIZING_3
            CHR_PAIR_RUNSTATUS_INITIALIZED
            CHR_PAIR_RUNSTATUS_RUNNING
            CHR_PAIR_RUNSTATUS_STOPPING
            CHR_PAIR_RUNSTATUS_REQUESTED_STOP
            CHR_PAIR_RUNSTATUS_ERROR
            CHR_PAIR_RUNSTATUS_RESOLVING_NAMES
            CHR_PAIR_RUNSTATUS_POLLING
            CHR_PAIR_RUNSTATUS_FINISHED
            CHR_PAIR_RUNSTATUS_REQUESTING_STOP
            CHR_PAIR_RUNSTATUS_FINISHED_WARNINGS
            CHR_PAIR_RUNSTATUS_TRANSFERRING_PAYLOAD
            CHR_PAIR_RUNSTATUS_APPLYING_IXIA_CONFIG
            CHR_PAIR_RUNSTATUS_WAITING_FOR_REINIT
            CHR_PAIR_RUNSTATUS_ABANDONED
        '''
        pass

    @ctypes_param(ParamOut(c_ulong))
    def CHR_mpair_new(self):
        '''
        The CHR_mpair_new function creates a multicast pair.
        See the Multicast Pair Object Functions on page 4-276for more
        information.

        Parameters
        ----------

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        mpair_handle : int
            A pointer to the variable where the handle for the new pair is
            returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_mpair_set_e2_addr(self, mpair_handle: int, e2_name: str):
        '''
        The CHR_mpair_set_e2_addr function sets or changes the address for
        Endpoint 2 in the given multicast pair.

        Parameters
        ----------
        mpair_handle : int
            A handle returned by CHR_mpair_new() or CHR_mgroup_get_mpair().
        e2_name : str
            A string containing the address for Endpoint 2.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_mpair_set_lock(self, mpair_handle: int, lock: int):
        '''
        The function CHR_mpair_set_lock locks an unlocked multicast pair object
        if lock is CHR_TRUE, or unlocks a locked multicast pair object if lock
        is CHR_FALSE.
        An owned object must be locked--disabled for validation--before any of
        its attributes can be modified (using the set subcommand).
        To enable validation, all objects owned by a test (including multicast
        pairs owned by the test's multicast groups) must be unlocked before the
        test can be run or saved.

        Parameters
        ----------
        mpair_handle : int
            A handle returned by CHR_mpair_new() or CHR_mgroup_get_mpair.
        lock : int
            A CHR_BOOLEAN, where CHR_TRUE locks the (unlocked) multicast pair
            object, and CHR_FALSE unlocks the (locked) object.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_mpair_set_setup_e1_e2_addr(self, mpair_handle: int, e2_name: str):
        '''
        The CHR_mpair_set_setup_e1_e2_addr function sets the address by which
        Endpoint 1 knows Endpoint 2 for purposes of test setup.
        This attribute applies only when the
        CHR_mpair_set_use_setup_e1_e2_values function sets the "use" attribute
        to CHR_TRUE.

        Parameters
        ----------
        mpair_handle : int
            A handle returned by CHR_mpair_new() or CHR_mgroup_get_mpair().
        e2_name : str
            A string containing the address.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_mpair_set_use_setup_e1_e2_values(self,
                                             mpair_handle: int,
                                             use: int):
        '''
        The CHR_mpair_set_use_setup_e1_e2_values function sets or changes
        whether the values by which Endpoint 1 knows Endpoint 2 for purposes of
        test setup should be used.
        If this value is set to CHR_TRUE, the Pair Setup Endpoint 1 to
        Endpoint 2 address must be properly defined before the test is run.
        The Pair Setup Endpoint 1 to Endpoint 2 protocol is automatically set
        to TCP and cannot be changed.

        Parameters
        ----------
        mpair_handle : int
            A handle returned by CHR_mpair_new() or CHR_mgroup_get_mpair().
        use : int
            Specifies CHR_TRUE or CHR_FALSE to indicate whether to use the
            Endpoint 1 to Endpoint 2 test setup values.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Pair Object Functions
    #  (CHR_PAIR_HANDLE)

    @ctypes_param(c_ulong, c_ulong)
    def CHR_pair_copy(self, to_pair_handle: int, from_pair_handle: int):
        '''
        The CHR_pair_copy function copies the attributes of the source endpoint
        pair or hardware performance pair to the destination endpoint pair.
        The destination endpoint pair must not yet be owned by a test.
        Only the attributes of the endpoint pair are copied from the source to
        the destination.
        This does not include any results information.

        Parameters
        ----------
        to_pair_handle : int
            A handle of the destination pair object, returned by
            CHR_pair_new().
        from_pair_handle : int
            A handle of the source pair object, returned by CHR_pair_new() or
            CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong)
    def CHR_pair_delete(self, pair_handle: int):
        '''
        The CHR_pair_delete function frees all memory associated with the given
        endpoint pair or hardware performance pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair().
            After verifying that the handle refers to an endpoint pair object,
            it is checked to ensure that it is not referenced by a test object
            known by the API.
            The endpoint pair object cannot be deleted if it is contained by a
            test object.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_APPL_SCRIPT_NAME))
    def CHR_pair_get_appl_script_name(self, pair_handle: int):
        '''
        The CHR_pair_get_appl_script_name function gets the application script
        name for the given endpoint pair.
        This function is not available for a voice over IP (VoIP) pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        script_name : str
            A pointer to the buffer where the script name is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_PAIR_COMMENT))
    def CHR_pair_get_comment(self, pair_handle: int):
        '''
        The CHR_pair_get_comment function gets the comment for the given
        endpoint pair or hardware performance pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        comment : str
            A pointer to the buffer where the comment is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_ADDR))
    def CHR_pair_get_console_e1_addr(self, pair_handle: int):
        '''
        The CHR_pair_get_console_e1_addr function gets the address by which the
        Console knows Endpoint 1 for the given endpoint pair or hardware
        performance pair.
        This attribute applies only when the
        CHR_pair_set_use_console_e1_values function sets the "use" attribute to
        CHR_TRUE.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        console_e1_name : str
            A pointer to the buffer where the address is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_pair_get_console_e1_protocol(self, pair_handle: int):
        '''
        The CHR_pair_get_console_e1_protocol function gets the Console to
        Endpoint 1 network protocol for the given endpoint pair.
        This attribute applies only when the
        CHR_pair_set_use_console_e1_values function sets the "use" attribute to
        CHR_TRUE.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        protocol : int
            A pointer to the variable where the protocol is returned.
            See CHR_mgroup_set_console_e1_protocol on page 4-256 for
            information on applicable protocols.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_ADDR))
    def CHR_pair_get_e1_addr(self, pair_handle: int):
        '''
        The CHR_pair_get_e1_addr function gets the Endpoint 1 address for the
        given endpoint pair or hardware performance pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        e1_name : str
            A pointer to the buffer where the Endpoint 1 address is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_ADDR))
    def CHR_pair_get_e2_addr(self, pair_handle: int):
        '''
        The CHR_pair_get_e2_addr function gets the Endpoint 2 address for the
        given endpoint pair or hardware performance pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        e2_name : str
            A pointer to the buffer where the Endpoint 2 address is returned.
        '''
        pass

    @ctypes_param(c_ulong, c_char, ParamOut(bytes, CHR_MAX_CFG_PARM))
    def CHR_pair_get_e1_config_value(self, pair_handle: int, parameter: int):
        '''
        The CHR_pair_get_e1_config_value function gets an Endpoint 1
        configuration value from the pair.
        The configuration information is returned from the endpoint during
        test execution.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair().
        parameter : int
            One of the CHR_CFG_PARM values. See Typedefs and Enumerations on
            page 4-612 or CHR_CFG_PARM values.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        value : str
            One of the CHR_CFG_PARM values. See Typedefs and Enumerations on
            page 4-612 or CHR_CFG_PARM values.
        '''
        pass

    @ctypes_param(c_ulong, c_char, ParamOut(bytes, CHR_MAX_CFG_PARM))
    def CHR_pair_get_e2_config_value(self, pair_handle: int, parameter: int):
        '''
        The CHR_pair_get_e2_config_value function gets an Endpoint 2
        configuration value from the pair.
        The configuration information is returned from the endpoint during
        test execution.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair().
        parameter : int
            One of the CHR_CFG_PARM values. See Typedefs and Enumerations on
            page 4-612 for CHR_CFG_PARM values.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        value : str
            One of the CHR_CFG_PARM values.
            See Typedefs and Enumerations on page 4-612 for CHR_CFG_PARM
            values.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_pair_get_protocol(self, pair_handle: int):
        '''
        The CHR_pair_get_protocol function gets the Endpoint 1 to Endpoint 2
        network protocol for the given endpoint pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        protocol : int
            A pointer to the variable where the protocol is returned.
            See the CHR_pair_set_protocol on page 4-337 function for applicable
            protocols.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_QOS_NAME))
    def CHR_pair_get_qos_name(self, pair_handle: int):
        '''
        The CHR_pair_get_qos_name function returns the endpoint 1 service
        quality template.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        qos_name : str
            A pointer to the buffer where the service quality name is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_QOS_NAME))
    def CHR_pair_get_e1_qos_name(self, pair_handle: int):
        '''
        The CHR_pair_get_e1_qos_name function gets the service quality name for
        Endpoint 1 in the pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        qos_name : str
            A pointer to the buffer where the service quality of name is
            returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_QOS_NAME))
    def CHR_pair_get_e2_qos_name(self, pair_handle: int):
        '''
        The CHR_pair_get_e2_qos_name function gets the service quality name for
        Endpoint 2 in the pair, where it exists.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        qos_name : str
            A pointer to the buffer where the service quality of name is
            returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_pair_get_runStatus(self, pair_handle: int):
        '''
        The CHR_pair_get_runStatus function gets the status of an endpoint pair
        or hardware performance pair during a test run.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        run_status : int
            A pointer to the variable where the run status is returned.
            The following status types are applicable:
            CHR_PAIR_RUNSTATUS_UNINITIALIZED
            CHR_PAIR_RUNSTATUS_INITIALIZING_1
            CHR_PAIR_RUNSTATUS_INITIALIZING_2
            CHR_PAIR_RUNSTATUS_INITIALIZING_3
            CHR_PAIR_RUNSTATUS_INITIALIZED
            CHR_PAIR_RUNSTATUS_RUNNING
            CHR_PAIR_RUNSTATUS_STOPPING
            CHR_PAIR_RUNSTATUS_REQUESTED_STOP
            CHR_PAIR_RUNSTATUS_ERROR
            CHR_PAIR_RUNSTATUS_RESOLVING_NAMES
            CHR_PAIR_RUNSTATUS_POLLING
            CHR_PAIR_RUNSTATUS_FINISHED
            CHR_PAIR_RUNSTATUS_REQUESTING_STOP
            CHR_PAIR_RUNSTATUS_FINISHED_WARNINGS
            CHR_PAIR_RUNSTATUS_TRANSFERRING_PAYLOAD
            CHR_PAIR_RUNSTATUS_APPLYING_IXIA_CONFIG
            CHR_PAIR_RUNSTATUS_WAITING_FOR_REINIT
            CHR_PAIR_RUNSTATUS_ABANDONED
            See also typedef char CHR_PAIR_RUNSTATUS_TYPE, listed in Typedefs
            and Enumerations on page 4-612.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_FILE_PATH))
    def CHR_pair_get_script_filename(self, pair_handle: int):
        '''
        The CHR_pair_get_script_filename function gets the script filename for
        the given endpoint pair or hardware performance pair.
        The script filename is returned without path information.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        file_name : str
            A pointer to the buffer where the script filename is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_ADDR))
    def CHR_pair_get_setup_e1_e2_addr(self, pair_handle: int):
        '''
        The CHR_pair_get_setup_e1_e2_addr function gets the address at which
        Endpoint 1 knows Endpoint 2 for purposes of test setup for the given
        endpoint pair or hardware performance pair.
        This attribute applies only when the
        CHR_pair_set_use_setup_e1_e2_values function sets the "use" attribute
        to CHR_TRUE.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        e1_e2_name : str
            A pointer to the buffer where the address is returned.
        '''
        pass

    @ctypes_param(c_ulong, c_ulong, ParamOut(c_ulong))
    def CHR_pair_get_timing_record(self, pair_handle: int, index: int):
        '''
        The CHR_pair_get_timing_record function gets the specified timing
        record from the given endpoint pair or hardware performance pair.
        The handle returned by this function is needed for other function
        calls to operate on this object.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair().
        index : int
            The number indicating which timing record. The number is determined
            by the order in which timing records were received.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        timing_record_handle : int
            A pointer to the variable where the handle of the timing record is
            returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_pair_get_timing_record_count(self, pair_handle: int):
        '''
        The CHR_pair_get_timing_record_count function gets the number of timing
        records in the results for the given endpoint pair or hardware
        performance pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        count : int
            A pointer to the variable where the number of timing records is
            returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_pair_get_use_console_e1_values(self, pair_handle: int):
        '''
        The CHR_pair_get_use_console_e1_values function gets whether to use the
        Console-to-Endpoint 1 values.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new or CHR_test_get_pair.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        use_values : int
            A pointer to the variable where the boolean value is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_pair_get_use_setup_e1_e2_values(self, pair_handle: int):
        '''
        The CHR_pair_get_use_setup_e1_e2_values function gets whether to use
        the values by which Endpoint 1 knows Endpoint 2 for purposes of test
        setup.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        use_values : int
            A pointer to the variable where the boolean value is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_pair_is_udp_RFC768_streaming(self, pair_handle: int):
        '''
        The CHR_ pair_is_udp_RFC768_streaming function determines whether or
        not the RFC 768 option is enabled in the script for the specified pair.
        If the option is present in the script, and it is enabled, the
        function returns TRUE.
        In all other cases, it returns FALSE.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        used : int
            A pointer to the variable where the boolean value is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_pair_is_disabled(self, pair_handle: int):
        '''
        The CHR_pair_is_disabled function determines whether or not the
        specified pair is disabled in the test.
        You can use this function for any of the following pair types: regular
        pairs, Hardware Performance Pairs, VoIP pairs, VoIP Hardware
        Performance Pairs, and video pairs.
        However, this function is not valid for pairs within application
        groups.

        Parameters
        ----------
        pair_handle : int
            A handle returned by any of the following functions:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        disabled : int
            A pointer to the variable where the Boolean value is returned. The
            returned values can be:
        '''
        pass

    @ctypes_param(ParamOut(c_ulong))
    def CHR_pair_new(self):
        '''
        The CHR_pair_new function creates an endpoint pair object
        and initializes it to object default values.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        pair_handle : int
            A pointer to the variable where the handle for the new endpoint
            pair is returned.

        '''

        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_pair_set_comment(self, pair_handle: int, comment: str):
        '''
        The CHR_pair_set_comment function sets or changes the comment for the
        given endpoint pair or hardware performance pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair().
        comment : str
            The string containing the new comment.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_pair_set_console_e1_addr(self,
                                     pair_handle: int,
                                     console_e1_name: str):
        '''
        The CHR_pair_set_console_e1_addr function sets or changes the address
        by which the Console knows Endpoint 1 for the given endpoint pair or
        hardware performance pair.
        This attribute applies only when the
        CHR_pair_set_use_console_e1_values function sets the "use" attribute to
        CHR_TRUE.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair().
        console_e1_name : str
            A string containing the address.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_pair_set_console_e1_protocol(self,
                                         pair_handle: int,
                                         protocol: int):
        '''
        The CHR_pair_set_console_e1_protocol function sets or changes the
        Console to Endpoint 1 network protocol for the given endpoint pair.
        This attribute applies only when the
        CHR_pair_set_use_console_e1_values function sets the "use" attribute to
        CHR_TRUE.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair().
        protocol : int
            The protocol type: CHR_PROTOCOL_TCP, CHR_PROTOCOL_TCP6, or
            CHR_PROTOCOL_SPX.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_pair_set_e1_addr(self, pair_handle: int, e1_name: str):
        '''
        The CHR_pair_set_e1_addr function sets or changes the address for
        Endpoint 1 in the given endpoint pair or hardware performance pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair().
        e1_name : str
            A string containing the address for Endpoint 1 (IPv4 or IPv6).

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_pair_set_e2_addr(self, pair_handle: int, e2_name: str):
        '''
        The CHR_pair_set_e2_addr function adds or changes the address for
        Endpoint 2 in the given endpoint pair or hardware performance pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair().
        e2_name : str
            A string containing the address for Endpoint 2.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_pair_set_lock(self, pair_handle: int, lock: int):
        '''
        The function CHR_pair_set_lock locks an unlocked pair object if lock is
        CHR_TRUE, or unlocks a locked pair object if lock is CHR_FALSE.
        An owned object must be locked--disabled for validation--before any of
        its attributes can be modified (using the set subcommand).
        To enable validation, all objects owned by a test must be unlocked
        before the test can be run or saved.
        <META NAME="Keywords" CONTENT="Pair Object Functions:CHR_pair_set_lock,
        LOCK">

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair.
        lock : int
            A CHR_BOOLEAN, where CHR_TRUE locks the (unlocked) pair object, and
            CHR_FALSE unlocks the (locked) object.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_pair_set_protocol(self, pair_handle: int, protocol: int):
        '''
        The CHR_pair_set_protocol function sets or changes the Endpoint 1 to
        Endpoint 2 network protocol for the given endpoint or VoIP pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair.
        protocol : int
            Provides the following protocol types: CHR_PROTOCOL_UDP,
            CHR_PROTOCOL_RTP, CHR_PROTCOL_TCP, CHR_PROTOCOL_IPX, and
            CHR_PROTOCOL_SPX.
            With the separately licensed IPv6 Test Module, also provides
            CHR_PROTCOL_TCP6, CHR_PROTOCOL_UDP6, and CHR_PROTOCOL_RTP6.
            With the VoIP Test Module, also provides CHR_PROTOCOL_RTP.
            With both the IPv6 Test Module and the VoIP Test Module, also
            provides CHR_PROTOCOL_RTP or CHR_PROTOCOL_RTP6.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_pair_set_qos_name(self, pair_handle: int, qos_name: str):
        '''
        The CHR_pair_set_qos_name function sets or changes the service quality
        template for both endpoint 1 and endpoint 2.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new().
        qos_name : str
            A string containing quality of service name.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_pair_set_e1_qos_name(self, pair_handle: int, qos_name: str):
        '''
        The CHR_pair_set_e1_qos_name function sets or changes the service
        quality name for endpoint 1 in the given pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new().
        qos_name : str
            A string containing quality of service name.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_pair_set_e2_qos_name(self, pair_handle: int, qos_name: str):
        '''
        The CHR_pair_set_e2_qos_name function sets or changes the service
        quality name for endpoint 2 in the given pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new().
        qos_name : str
            A string containing quality of service name.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes), ParamIn(bytes))
    def CHR_pair_set_script_variable(self, pair_handle: int,
                                     name: str, value: str):
        '''
        The CHR_pair_set_script_variable function modifies the value of a
        variable in the script defined for use by the given endpoint pair.
        There must be a script defined for use by the given endpoint pair.
        The script variable name is checked to ensure that it exists in the
        defined script.
        CHR_NO_SUCH_OBJECT is returned if the variable does not exist in the
        script.
        Note that the options related to Nagle, UDP checksum and MSS must have
        previously been created using the IxChariot editor before being set
        with this command.
        The variable value is checked to ensure that it is valid for that
        variable in that script.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new().
        name : str
            A string containing the name of the script variable.
        value : str
            A string containing the value for the script variable.
            Use the following table to determine the valid string values.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes),
                  ParamOut(bytes, CHR_MAX_SCRIPT_VARIABLE_VALUE))
    def CHR_pair_get_script_variable(self, pair_handle: int, name: str):
        '''
        The CHR_pair_get_script_variable function gets the value of a specified
        variable from the script used by this endpoint pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair().
        name : str
            A string containing the name of the script variable.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        value : str
            The name of the buffer to which the value of the script variable is
            returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes), ParamIn(bytes))
    def CHR_pair_set_script_embedded_payload(self,
                                             pair_handle: int,
                                             variable_name: str,
                                             payload: str):
        '''
        The CHR_pair_set_script_embedded_payload function modifies the value
        of an embedded payload within a script. The send_datatype for the
        variable will automatically be set to "Embedded payload". There must
        be a script defined for use by the given endpoint pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new().
        variable_name : str
            A string containing the name of the script variable.
        payload : str
            A pointer to a buffer that contains the payload.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes),
                  ParamOut(bytes, CHR_MAX_EMBEDDED_PAYLOAD_SIZE))
    def CHR_pair_get_script_embedded_payload(self, pair_handle: int,
                                             variable_name: str):
        '''
        The CHR_pair_get_script_embedded_payload function gets the value of the
        embedded payload data from the script used by this endpoint pair.
        This function requires that the variable is of type send_datatype.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair().
        variable_name : str
            A string containing the name of the script variable.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        payload : str
            The buffer to which the embedded script payload is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes), ParamIn(bytes), c_char)
    def CHR_pair_set_payload_file(self, pair_handle: int,
                                  variable_name: str, filename: str,
                                  embedded: int):
        '''
        The CHR_pair_set_payload_file function specifies the payload of a
        particular SEND command.
        It allows the user to specify a file whose content will be used as
        payload when running the script.
        In addition to specifying the payload, this function will also set the
        send_datatype to "Payload File".

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new().
        variable_name : str
            A string containing the name of a send_datatype script variable.
        filename : str
            The name of the file containing the payload data.
        embedded : int
            If set to CHR_TRUE, the payload file will be embedded within the
            script. If set to CHR_FALSE, the script will contain a reference to
            the external file. The recommended option is CHR_TRUE.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes), ParamOut(bytes, CHR_MAX_FILENAME),
                  ParamOut(c_char))
    def CHR_pair_get_payload_file(self, pair_handle: int, variable_name: str):
        '''
        The CHR_pair_get_payload_file function gets the name of the payload
        file that is defined for the script used by the given endpoint pair, as
        well as the embedded flag (indicating whether the payload is embedded
        or referenced).
        This function requires that the variable is of type send_datatype, and
        that send_datatype is set to "Payload file", rather than "Embedded
        payload".

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair().
        variable_name : CHR_STRING
            A string containing the name of the send_datatype script variable
            that is used by the given endpoint pair.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        filename : CHR_STRING
            The buffer containing the name of the payload file.
        embedded : int
            A pointer to the variable where the embedded payload flag is
            returned. The values for the flag are:
            CHR_TRUE: The payload file is embedded within the script.
            CHR_FALSE: The script contains a reference to the external
            file.
        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_pair_set_setup_e1_e2_addr(self, pair_handle: int, e1_e2_name: str):
        '''
        The CHR_pair_set_setup_e1_e2_addr function sets the address by which
        Endpoint 1 knows Endpoint 2 for purposes of test setup for the given
        endpoint pair or hardware performance pair.
        This attribute applies only when the
        CHR_pair_set_use_setup_e1_e2_values function sets the "use" attribute
        to CHR_TRUE.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair().
        e1_e2_name : str
            A string containing the address.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_pair_set_use_console_e1_values(self, pair_handle: int,
                                           use_values: int):
        '''
        The CHR_pair_set_use_console_e1_values function sets or changes whether
        the Console-to-Endpoint 1 values are to be used.
        If the value is set to CHR_TRUE, the Console to Endpoint 1 address and
        Console to Endpoint 1 QOS name must be properly defined before the test
        is run.
        The Console to Endpoint 1 protocol defaults to TCP and may be changed
        if needed.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new().
        use_values : int
            Specifies CHR_TRUE or CHR_FALSE to indicate whether to use the
            Console to Endpoint 1 values.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_pair_set_use_setup_e1_e2_values(self, pair_handle: int,
                                            use_values: int):
        '''
        The CHR_pair_set_use_setup_e1_e2_values function sets or changes
        whether the values by which Endpoint 1 knows Endpoint 2 for purposes of
        test setup should be used.
        If this value is set to CHR_TRUE, the Pair Setup Endpoint 1 to
        Endpoint 2 address must be properly defined before the test is run.
        The Pair Setup Endpoint 1 to Endpoint 2 protocol is automatically set
        to TCP and cannot be changed.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair().
        use_values : int
            Specifies CHR_TRUE or CHR_FALSE to indicate whether to use the
            Endpoint 1 to Endpoint 2 test setup values.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_pair_use_script_filename(self, pair_handle: int, filename: str):
        '''
        The CHR_pair_use_script_filename function defines or changes the
        script file to be used by the given endpoint pair or hardware
        performance pair. The script filename may be specified by relative or
        absolute path.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_pair_new().
        file_name : str
            A string containing the script filename.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_pair_disable(self, pair_handle: int, disable: int):
        '''
        The CHR_pair_disable function disables or enables the specified pair
        for the test.
        IxChariot ignores any disabled pairs when running a test.
        You can use this function for any of the following pair types: regular
        pairs, Hardware Performance Pairs, VoIP pairs, VoIP Hardware
        Performance Pairs, and video pairs.
        However, this function is not valid for pairs within application
        groups.

        Parameters
        ----------
        pair_handle : int
            A handle returned by any of the following functions:
        disable : int
            Specifies the action to perform:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong)
    def CHR_pair_swap_endpoints(self, pair_handle: int):
        '''
        The CHR_pair_swap_endpoints function swaps (exchanges) endpoints (test
        and management addresses between E1 and E2).
        It is supported for regular pairs, VoIP, unicast video, HPP, and vHPP.

        Parameters
        ----------
        pair_handle : int
            A handle returned by many functions, since CHR_pair_swap_endpoint
            is supported for regular pairs, VoIP, unicast video, HPP, and vHPP
            (e.g., CHR_pair_new, CHR_voip_pair_new, etc.).

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Pair/Multicast Group Pair Results Extraction Functions
    #  (CHR_PAIR_HANDLE/CHR_MPAIR_HANDLE)

    @ctypes_param(c_ulong, c_char, ParamOut(c_double))
    def CHR_pair_results_get_average(self, handle: int, result_type: int):
        '''
        The CHR_pair_results_get_average function gets the average for the
        given type from the test results in the given endpoint pair or
        multicast pair.

        Parameters
        ----------
        handle : int
            For an endpoint pair, the handle returned by CHR_pair_new() or
            CHR_test_get_pair().
            For a multicast pair, the handle returned by CHR_mpair_new() or
            CHR_mgroup_get_mpair().
        result_type : int
            Provides one of the CHR_RESULTS values. See Typedefs and
            Enumerations on page 4-612 for CHR_RESULTS values.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        avg : float
            A pointer to the variable where the average value is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_double))
    def CHR_pair_results_get_CPU_util_e1(self, handle: int):
        '''
        The CHR_pair_results_get_CPU_util_e1 function gets the CPU utilization
        for Endpoint 1 from the test results in the given endpoint pair or
        multicast pair.

        Parameters
        ----------
        handle : int
            For an endpoint pair, the handle returned by CHR_pair_new() or
            CHR_test_get_pair().
            For a multicast pair, the handle returned by CHR_mpair_new() or
            CHR_mgroup_get_mpair().
        cpu_util : float
            A pointer to the variable where the CPU utilization is returned.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_double))
    def CHR_pair_results_get_CPU_util_e2(self, handle: int):
        '''
        The CHR_pair_results_get_CPU_util_e2 function gets the CPU utilization
        for Endpoint 2 from the test results in the given endpoint pair or
        multicast pair.

        Parameters
        ----------
        handle : int
            For an endpoint pair, the handle returned by CHR_pair_new() or
            CHR_test_get_pair().
            For a multicast pair, the handle returned by CHR_mpair_new() or
            CHR_mgroup_get_mpair().
        cpu_util : float
            A pointer to the variable where the CPU utilization is returned.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char, ParamOut(c_double))
    def CHR_pair_results_get_maximum(self, handle: int, result_type: int):
        '''
        The CHR_pair_results_get_maximum function gets the maximum for the
        given type from the test results in the given endpoint pair or
        multicast pair.

        Parameters
        ----------
        handle : int
            For an endpoint pair, the handle returned by CHR_pair_new() or
            CHR_test_get_pair().
            For a multicast pair, the handle returned by CHR_mpair_new() or
            CHR_mgroup_get_mpair().
        result_type : int
            Provides one of the CHR_RESULTS values. See Typedefs and
            Enumerations on page 4-612 for CHR_RESULTS values.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        max : float
            A pointer to the variable where the maximum value is returned.
        '''
        pass

    @ctypes_param(c_ulong, c_char, ParamOut(c_double))
    def CHR_pair_results_get_minimum(self,
                                     handle: int,
                                     result_type: int):
        '''
        The CHR_pair_results_get_minimum function gets the minimum for the
        given type from the test results in the given endpoint pair or
        multicast pair.

        Parameters
        ----------
        handle : int
            For an endpoint pair, the handle returned by CHR_pair_new() or
            CHR_test_get_pair().
            For a multicast pair, the handle returned by CHR_mpair_new() or
            CHR_mgroup_get_mpair().
        result_type : int
            Provides one of the CHR_RESULTS values. See Typedefs and
            Enumerations on page 4-612 for CHR_RESULTS values.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        min : float
            A pointer to the variable where the minimum value is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_double))
    def CHR_pair_results_get_rel_precision(self, handle: int):
        '''
        The CHR_pair_results_get_rel_precision function gets the relative
        precision from the test results in the given endpoint pair or multicast
        pair.

        Parameters
        ----------
        handle : int
            For an endpoint pair, the handle returned by CHR_pair_new() or
            CHR_test_get_pair().
            For a multicast pair, the handle returned by CHR_mpair_new() or
            CHR_mgroup_get_mpair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        precision : float
            A pointer to the variable where the relative precision value is
            returned.
        '''
        pass

    @ctypes_param(c_ulong, c_char, ParamOut(c_double))
    def CHR_pair_results_get_95pct_confidence(self, handle: int,
                                              result_type: int):
        '''
        The CHR_pair_results_get_95pct_confidence function gets the 95 percent
        confidence interval for the given endpoint pair or multicast pair.

        Parameters
        ----------
        handle : int
            For an endpoint pair, the handle returned by CHR_pair_new() or
            CHR_test_get_pair().
            For a multicast pair, the handle returned by CHR_mpair_new() or
            CHR_mgroup_get_mpair().
        result_type : int
            Provides one of the following CHR_RESULTS values:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        result : float
            A pointer to the variable where the confidence interval value is
            returned.
        '''
        pass

    #  Run Options Object Functions
    #  (CHR_RUNOPTS_HANDLE)

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_runopts_get_connect_timeout(self,
                                        run_options_handle: int):
        '''
        The CHR_runopts_get_connect_timeout function gets the time in minutes
        for which connection attempts are retried.
        A value of zero minutes means no retries are attempted.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        connect_timeout : int
            A pointer to the variable where the connection timeout is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_runopts_get_CPU_util(self, run_options_handle: int):
        '''
        The CHR_runopts_get_CPU_util function gets the option value indicating
        that endpoints are collecting CPU utilization (CHR_TRUE) or not
        collecting (CHR_FALSE).

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        cpu_util : int
            A pointer to the true or false variable that tells whether CPU
            utilization can be collected.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_runopts_get_collect_TCP_stats(self, run_options_handle: int):
        '''
        CHR_runopts_get_collect_TCP_stats

        Parameters
        ----------
        run_options_handle : int
            DESCRIPTION.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        collect_TCP_stats : int
            DESCRIPTION.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_runopts_get_allow_pair_reinit(self, run_options_handle: int):
        '''
        The CHR_runopts_get_allow_pair_reinit function returns a pointer that
        indicates whether pair reinitialization is allowed as part of the
        IxChariot test.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        allow_pair_reinit : int
            A pointer to the variable to which the function returns one of the
            following:
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_runopts_get_pair_reinit_max(self, run_options_handle: int):
        '''
        The CHR_runopts_get_pair_reinit_max function returns a pointer to the
        variable that specifies the maximum number of reinitialization attempts
        that IxChariot will make for a pair that fails during test
        initialization.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        pair_reinit_max : int
            A pointer to the variable that specifies the maximum number of
            reinitialization attempts that IxChariot will make for a pair that
            fails during test initialization.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_runopts_get_pair_reinit_retry_interval(self,
                                                   run_options_handle: int):
        '''
        The CHR_runopts_get_pair_reinit_retry_interval function returns a
        pointer to the variable that specifies the time interval between the
        reinitialization attempts that IxChariot will make for a pair that
        fails during test initialization.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        pair_reinit_retry_interval : int
            A pointer to the variable that specifies the time interval between
            the reinitialization attempts that IxChariot will make for a pair
            that fails during test initialization. The interval is specified in
            seconds.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_runopts_get_allow_pair_reinit_run(self, run_options_handle: int):
        '''
        The CHR_runopts_get_allow_pair_reinit_run function returns a pointer
        that indicates whether pair reinitialization is allowed once the
        IxChariot test has commenced running.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        allow_pair_reinit : int
            A pointer to the variable to which the function returns one of the
            following:
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_runopts_get_pair_reinit_max_run(self, run_options_handle: int):
        '''
        The CHR_runopts_get_pair_reinit_max_run function returns a pointer to
        the variable that specifies the maximum number of reinitialization
        attempts that IxChariot will make for a pair that fails while the test
        is running.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        pair_reinit_max : int
            A pointer to the variable that specifies the maximum number of
            reinitialization attempts that IxChariot will make for a pair that
            fails while the test is running.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_runopts_get_pair_reinit_retry_interval_run(
            self,
            run_options_handle: int):
        '''
        The CHR_runopts_get_pair_reinit_retry_interval_run function returns a
        pointer to the variable that specifies the time interval between the
        reinitialization attempts that IxChariot will make for a pair that
        fails while the test is running.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        pair_reinit_retry_interval : int
            A pointer to the variable that specifies the time interval between
            the reinitialization attempts that IxChariot will make for a pair
            that fails while the test is running. The interval is specified in
            seconds.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_runopts_get_HW_timestamps(self, run_options_handle: int):
        '''
        The CHR_runopts_get_HW_timestamps function gets a variable that
        specifies whether the option to use hardware timestamps during test
        initialization is set.
        Hardware timestamps are used to determine the video test source jitter
        and account for it in video test DF calculations.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        hw_timestamps : int
            A pointer to the true or false variable that tells whether the
            option to use hardware timestamps during test setup is set.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_runopts_get_fewer_setup_connections(self, run_options_handle: int):
        '''
        The CHR_runopts_get_fewer_setup_connections function gets whether the
        option to use fewer setup connections during test initialization is
        set.
        If a test has more than 500 pairs, this option defaults to true.
        For tests with more than 1250 pairs, this option is set to "true" and
        cannot be disabled.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        fewer_connections : int
            A pointer to the true or false variable that tells whether the
            option to use fewer connections during test setup is set.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_runopts_get_apply_dod_only(self, run_options_handle: int):
        '''
        The CHR_runopts_get_apply_dod_only function returns a pointer that
        indicates whether the "Apply only Endpoint DoD package" run option is
        set.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        iep_dod_only : int
            A pointer to the variable to which the function returns one of the
            following:
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_runopts_get_deconfigure_ports(self, run_options_handle: int):
        '''
        The CHR_runopts_get_deconfigure_ports function gets the option value
        indicating that  the Ixia ports are deconfigured (CHR_TRUE) or not
        (CHR_FALSE).

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        flag : int
            A pointer to the true or false variable that tells whether to
            deconfigure the Ixia ports.
        '''
        pass

    @ctypes_param(c_ulong, c_char, ParamOut(c_ulong))
    def CHR_runopts_get_num_result_ranges(self, handle: int, result_type: int):
        '''
        The CHR_runopts_get_num_result_ranges function gets the number of
        configurable ranges for different statistics.

        Parameters
        ----------
        handle : int
            A handle returned by CHR_test_get_runopts().
        result_type : int
            The desired result type. One of the following:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        number : int
            The number of configurable ranges.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_runopts_get_poll_endpoints(self, run_options_handle: int):
        '''
        The CHR_runopts_get_poll_endpoints function gets whether the endpoints
        will be polled during a test.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        poll_endpoints : int
            A pointer to the true or false variable that determines whether to
            poll the endpoints.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_runopts_get_poll_interval(self, run_options_handle: int):
        '''
        The CHR_runopts_get_poll_interval function gets the interval in minutes
        used when endpoints are to be polled.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        poll_interval : int
            A pointer to the variable where the polling interval is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_runopts_get_random_new_seed(self, run_options_handle: int):
        '''
        The CHR_runopts_get_random_new_seed function gets whether to reseed the
        random number generator.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        random_new_seed : int
            A pointer to the true or false variable that tells whether to
            reseed the random number generator.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_runopts_get_reporting_type(self, run_options_handle: int):
        '''
        The CHR_runopts_get_reporting_type function gets how to report the
        timing records.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        reporting_type : CHR_TEST_REPORTING_P
            A pointer to variable where the reporting type value is returned.
            See the "CHR_runopts_set_reporting_type" function for
            CHR_TEST_REPORTING values..
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_runopts_get_poll_retrieving_type(self, run_options_handle: int):
        '''
        The CHR_runopts_get_poll_retrieving_type function gets the value of the
        reporting type that is in effect for polling.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        test_retrieving : CHR_TEST_RETRIEVING_P
            A pointer to the variable where the retrieving type value is
            returned.
            The retrieving type is one of the following:

            CHR_TEST_RETRIEVE_NUMBER (Polling retrieves a count of the timing
            records).
            CHR_TEST_RETRIEVE_TIMING_RECORD (Polling retrieves the actual
            timing records).
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_runopts_get_reporting_firewall(self, run_options_handle: int):
        '''
        The CHR_runopts_get_reporting_firewall function gets the value that
        indicates whether or not there is a firewall between the IxChariot
        Console and endpoint 1.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        test_reporting_firewall : int
            A pointer to the variable where the value is returned. The
            reporting_firewall variable takes one of the following values:
        '''
        pass

    @ctypes_param(c_ulong, c_char, c_ulong, ParamOut(c_ulong),
                  ParamOut(c_ulong))
    def CHR_runopts_get_result_range(self,
                                     run_options_handle: int,
                                     result_type: int,
                                     index: int):
        '''
        The CHR_runopts_get_result_range function gets the values for a
        specified statistics bucket ranges.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().
        result_type : int
            The desired statistic type. One of the following:
        index : int
            The index of the range value to set. The index value can be a value
            from 0 to the number of configured ranges  1, for a specified
            result type.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        min_value : int
            The minimum value for this particular range.
        max_value : int
            The maximum value for this particular range.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_runopts_get_stop_after_num_pairs_fail(self,
                                                  run_options_handle: int):
        '''
        The CHR_runopts_get_stop_after_num_pairs_fail function gets the number
        of pairs that must fail to force the test to stop with an error.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        num_pairs : int
            A pointer to the variable where the number of pair failures
            necessary to force stoppage is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_runopts_get_stop_on_init_failure(self, run_options_handle: int):
        '''
        The CHR_runopts_get_stop_on_init_failure function gets whether the test
        is to stop on initialization errors.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        stop_on_init_failure : int
            A pointer to the true or false variable that tells whether to stop
            on initialization errors.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_runopts_get_test_duration(self, run_options_handle: int):
        '''
        The CHR_runopts_get_test_duration function gets the time in seconds the
        test is to run.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        test_duration : int
            A pointer to the variable where the test duration is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_runopts_get_test_end(self, run_options_handle: int):
        '''
        The CHR_runopts_get_test_end function gets the option indicating when
        the test is to end.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        test_end : CHR_TEST_END_P
            A pointer to the variable where the test end value is returned. See
            the CHR_runopts_set_test_end on page 4-444 function for
            CHR_TEST_END values.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_runopts_get_validate_on_recv(self, run_options_handle: int):
        '''
        The CHR_runopts_get_validate_on_recv function gets whether to validate
        the data when it is received.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        validate_on_recv : int
            A pointer to the true or false variable that tells whether to
            validate the data when it is received.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_runopts_get_clksync_hardware_ts(self, run_options_handle: int):
        '''
        The CHR_runopts_get_clksync_hardware_ts function returns a pointer that
        indicates whether the endpoints in the test will attempt to use
        hardware timestamps as the timing source on the Ixia ports.
        Where this option is not supported, the endpoint internal clock is
        used.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        clksync_hardware_ts : int
            Sets the variable to one of the following:
                CHR_TRUE – the endpoints in the test will attempt to use
                hardware time-stamps as the timing source on the Ixia ports.
                CHR_FALSE – the endpoints in the test will not use hardware
                timestamps as the timing source on the Ixia ports.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_runopts_get_clksync_external(self, run_options_handle: int):
        '''
        The CHR_runopts_get_clksync_external function returns a pointer that
        indicates whether the endpoints in the test are using an external
        clocking source (such as NTP servers synchronized to the Global
        Positioning System).

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        clksync_external : int
            A pointer to the variable to which the function returns one of the
            following:
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_runopts_get_overlapped_sends_count(self, run_options_handle: int):
        '''
        The CHR_runopts_get_overlapped_sends_count function gets the number of
        multiple buffers sent in parallel.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        value : int
            The number of multiple buffers to send.
        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_runopts_set_connect_timeout(self, run_options_handle: int,
                                        connect_timeout: int):
        '''
        The CHR_runopts_set_connect_timeout function sets or changes the time
        in minutes waited for a connection before it is considered an error.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().
        connect_timeout : int
            The time in minutes. The valid range is 1 to 999.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_runopts_set_CPU_util(self, run_options_handle: int, cpu_util: int):
        '''
        The CHR_runopts_set_CPU_util function sets or changes the option that
        determines whether endpoints collect CPU utilization data.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().
        cpu_util : int
            Specifies CHR_TRUE or CHR_FALSE to indicate whether to collect CPU
            utilization.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_runopts_set_collect_TCP_stats(self, run_options_handle: int,
                                          collect_TCP_stats: int):
        '''
        CHR_runopts_set_collect_TCP_stats

        Parameters
        ----------
        run_options_handle : int
            DESCRIPTION.
        collect_TCP_stats : int
            DESCRIPTION.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_runopts_set_allow_pair_reinit(self, run_options_handle: int,
                                          allow_pair_reinit: int):
        '''
        The CHR_runopts_set_allow_pair_reinit function sets or changes the
        option that determines whether or not pair reinitialization is allowed
        as part of the IxChariot test.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().
        allow_pair_reinit : int
            Sets one of the following to specify whether or not pair
            reinitialization is allowed as part of the IxChariot test:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_runopts_set_pair_reinit_max(self, run_options_handle: int,
                                        pair_reinit_max: int):
        '''
        The CHR_runopts_set_pair_reinit_max function sets or changes the
        maximum number of reinitialization attempts that IxChariot will make
        for a pair that fails during test initialization.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().
        pair_reinit_max : int
            The maximum number of reinitialization attempts that IxChariot will
            make for a pair that fails during test initialization. Accepted
            values are in the 1-99999 range.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_runopts_set_pair_reinit_retry_interval(
            self, run_options_handle: int,
            pair_reinit_retry_interval: int):
        '''
        The CHR_runopts_set_pair_reinit_retry_interval function sets or changes
        the time interval between the reinitialization attempts that IxChariot
        will make for a pair that fails during test initialization.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().
        pair_reinit_retry_interval : int
            The time interval between the reinitialization attempts that
            IxChariot will make for a pair that fails during test
            initialization. The interval is specified in seconds. The accepted
            values are in the 1-99999 range.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_runopts_set_allow_pair_reinit_run(self, run_options_handle: int,
                                              allow_pair_reinit: int):
        '''
        The CHR_runopts_set_allow_pair_reinit_run function sets or changes the
        option that determines whether or not pair reinitialization is allowed
        once the IxChariot test starts running.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().
        allow_pair_reinit : int
            Sets one of the following to specify whether or not pair
            reinitialization is allowed as part of the IxChariot test:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_runopts_set_pair_reinit_max_run(self, run_options_handle: int,
                                            pair_reinit_max: int):
        '''
        The CHR_runopts_set_pair_reinit_max_run function sets or changes the
        maximum number of reinitialization attempts that IxChariot will make
        for a pair that fails while the test is running.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().
        pair_reinit_max : int
            The maximum number of reinitialization attempts that IxChariot will
            make for a pair that fails while the test is running. Accepted
            values are in the 1-99999 range.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_runopts_set_pair_reinit_retry_interval_run(
            self, run_options_handle: int,
            pair_reinit_retry_interval: int):
        '''
        The CHR_runopts_set_pair_reinit_retry_interval_run function sets or
        changes the time interval between the reinitialization attempts that
        IxChariot will make for a pair that fails while the test is running.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().
        pair_reinit_retry_interval : int
            The time interval between the reinitialization attempts that
            IxChariot will make for a pair that fails while the test is
            running. The interval is specified in seconds. Accepted values are
            in the 1-99999 range.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_runopts_set_HW_timestamps(self, run_options_handle: int,
                                      hw_timestamps: int):
        '''
        The CHR_runopts_set_HW_timestamps function specifies whether or not
        hardware timestamps will be used during video testing.
        Hardware timestamps are used to determine the video test source jitter
        and account for it in video test DF calculations.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_set_runopts().
        hw_timestamps : int
            Specifies CHR_TRUE or CHR_FALSE to indicate whether to use hardware
            time-stamps.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_runopts_set_fewer_setup_connections(self, run_options_handle: int,
                                                fewer_connections: int):
        '''
        The CHR_runopts_set_fewer_setup_connections function sets whether to
        use fewer setup connections during test initialization.
        If a test contains more than 500 pairs, this option is automatically
        set to true, but it can still be changed to false.
        For tests with more than 1250 pairs, this option is set to "true" and
        cannot be disabled.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().
        fewer_connections : int
            Specifies CHR_TRUE or CHR_FALSE to indicate whether to use fewer
            connections during test setup.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_runopts_set_apply_dod_only(self, run_options_handle: int,
                                       ep_dod_only: int):
        '''
        The CHR_runopts_set_apply_dod_only function enables or disables the
        "Apply only Endpoint DoD package" run option.
        This option applies the endpoint DoD package only, without applying
        the configuration.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().
        ep_dod_only : int
            Sets the "Apply only Endpoint DoD package" run option to one of the
            following values:
            CHR_TRUE – enables the "Apply only Endpoint DoD package" run
            option.
            CHR_FALSE – disables the "Apply only Endpoint DoD package" run
            option.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_runopts_set_deconfigure_ports(self, run_options_handle: int,
                                          flag: int):
        '''
        The CHR_runopts_set_deconfigure_ports function  sets or changes the
        option that determines whether to deconfigure Ixia ports as soon as the
        test ends.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().
        flag : int
            Specifies CHR_TRUE or CHR_FALSE to indicate whether to deconfigure
            Ixia ports when test ends.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char, c_ulong)
    def CHR_runopts_set_num_result_ranges(self, run_options_handle: int,
                                          result_type: int,
                                          number: int):
        '''
        The CHR_runopts_set_num_result_ranges function sets the number of
        ranges into which different statistics are placed in VoIP test results.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().
        result_type : int
            The desired result type. One of the following:
        number : int
            The number of configurable ranges. The maximum number of
            configurable ranges is 5 for CHR_RESULTS_DELAY_VARIATION and
            CHR_RESULTS_CONSECUTIVE_LOST. Ranges must be contiguous. If a
            number of ranges is set that interferes with the contiguity of
            configured ranges, ranges are adjusted to be contiguous.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_runopts_set_poll_endpoints(self, run_options_handle: int,
                                       poll_endpoints: int):
        '''
        The CHR_runopts_set_poll_endpoints function sets or changes whether to
        poll the endpoints.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().
        poll_endpoints : int
            Specifies CHR_TRUE or CHR_FALSE to indicate whether to poll the
            endpoints.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_runopts_set_poll_interval(self, run_options_handle: int,
                                      poll_interval: int):
        '''
        The CHR_runopts_set_poll_interval function sets or changes the interval
        in minutes used when endpoints are to be polled.
        This attribute applies only when the poll endpoints option is set to
        CHR_TRUE.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().
        poll_interval : int
            The polling interval in minutes. The valid range is 1 to 9999.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_runopts_set_random_new_seed(self, run_options_handle: int,
                                        random_new_seed: int):
        '''
        The CHR_runopts_set_random_new_seed function sets or changes whether to
        reseed the random number generator.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().
        random_new_seed : int
            Specifies CHR_TRUE or CHR_FALSE to indicate whether to reseed the
            random number generator.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_runopts_set_reporting_type(self, run_options_handle: int,
                                       reporting_type: int):
        '''
        The CHR_runopts_set_reporting_type function sets how to report the
        timing records.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().
        reporting_type : CHR_TEST_REPORTING
            One of the CHR_REPORTING values:
            CHR_TEST_REPORTING_BATCH or
            CHR_TEST_REPORTING_REALTIME.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_runopts_set_poll_retrieving_type(self, run_options_handle: int,
                                             poll_retrieving_type: int):
        '''
        The CHR_runopts_set_poll_retrieving_type function sets the value of the
        reporting type that IxChariot will use when polling the endpoints
        during a test.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().
        poll_retrieving_type : CHR_TEST_RETRIEVING
            One of the CHR_POLL_RETRIEVING values:
            CHR_TEST_RETRIEVE_NUMBER (Polling retrieves a count of the timing
            records).
            CHR_TEST_RETRIEVE_TIMING_RECORD (Polling retrieves the actual
            timing records).

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_runopts_set_reporting_firewall(self, run_options_handle: int,
                                           test_reporting_firewall: int):
        '''
        The CHR_runopts_set_reporting_firewall function sets the value that
        indicates whether or not there is a firewall between the IxChariot
        Console and endpoint 1.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().
        test_reporting_firewall : CHR_TEST_REPORTING_FIREWALL
            The reporting_firewall variable takes one of the following values:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char, c_ulong, c_ulong, c_ulong)
    def CHR_runopts_set_result_range(self, run_options_handle: int,
                                     result_type: int,
                                     index: int,
                                     min_value: int,
                                     max_value: int):
        '''
        The CHR_runopts_set_result_range function sets the range of values for
        a given statistic.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().
        result_type : int
            The desired statistic type. One of the following:
        index : int
            The index of the range value to set. The index value can be a value
            from 0 to the number of configured ranges  1, for a specified
            result type.
        min_value : int
            The minimum value for this particular range. All ranges must be
            increasing and contiguous. This value is currently ignored and is
            set to the previous range's maximum value + 1.
        max_value : int
            The maximum value for this particular range. Ranges must be
            contiguous. If a change is made to the maximum range that ends the
            contiguity of the lower ranges, the lower ranges are adjusted to be
            contiguous.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_runopts_set_stop_after_num_pairs_fail(self,
                                                  run_options_handle: int,
                                                  num_pairs: int):
        '''
        The CHR_runopts_set_stop_after_num_pairs_fail function sets or changes
        the number of pairs that must fail to force the test to stop with an
        error.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().
        num_pairs : int
            The number of pair failures necessary to force a stop. The valid
            range is 1 to 9999.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_runopts_set_stop_on_init_failure(self, run_options_handle: int,
                                             stop_on_init_failure: int):
        '''
        The CHR_runopts_set_stop_on_init_failure function sets or changes
        whether the test is to stop on initialization errors.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().
        stop_on_init_failure : int
            Provides a CHR_TRUE or CHR_FALSE.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_runopts_set_test_duration(self, run_options_handle: int,
                                      test_duration: int):
        '''
        The CHR_runopts_set_test_duration function sets or changes the test
        duration in seconds.
        This attribute applies only when the CHR_RUNOPTS_SET_TEST_END is set
        to CHR_END_AFTER_FIXED_DURATION.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().
        test_duration : int
            The time in seconds to run the test. The valid range is 1 to
            359,999.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_runopts_set_test_end(self, run_options_handle: int,
                                 test_end: int):
        '''
        The CHR_runopts_set_test_end function sets or changes how the test is
        to end.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().
        test_end : CHR_TEST_END
            Provides one of the CHR_TEST_END values:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_runopts_set_validate_on_recv(self, run_options_handle: int,
                                         validate_on_recv: int):
        '''
        The CHR_runopts_set_validate_on_recv function sets or changes whether
        data is to be validated at the endpoint as it is received.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().
        validate_on_recv : int
            Specifies CHR_TRUE or CHR_FALSE.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_runopts_set_clksync_hardware_ts(self, run_options_handle: int,
                                            clksync_hardware_ts: int):
        '''
        The CHR_runopts_set_clksync_hardware_ts function sets an option that
        specifies whether the endpoints in the test will attempt to use
        hardware timestamps as the timing source on the Ixia ports.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().
        clksync_hardware_ts : int
            Sets the variable to one of the following:
                CHR_TRUE – the endpoints in the test will attempt to use
                hardware time-stamps as the timing source on the Ixia ports.
                CHR_FALSE – the endpoints in the test will not use hardware
                timestamps as the timing source on the Ixia ports.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_runopts_set_clksync_external(self, run_options_handle: int,
                                         clksync_external: int):
        '''
        The CHR_runopts_set_clksync_external function sets an option that
        specifies whether the endpoints in the test will use external clocking
        as the timing source on the Ixia ports.
        Note that IxChariot validates neither the presence nor the reliability
        of the external timing source.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().
        clksync_external : int
            Sets the variable to one of the following:
            CHR_TRUE – the endpoints in the test will use external clocking as
            the timing source on the Ixia ports.
            CHR_FALSE – the endpoints in the test will not use external
            clocking as the timing source on the Ixia ports.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_QOS_NAME))
    def CHR_runopts_get_management_qos_console_name(self,
                                                    run_options_handle: int):
        '''
        The CHR_runopts_get_management_qos_console_name function returns the
        quality of service template name that the IxChariot test uses for
        management traffic sent from the console to Endpoint 1.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        qos_name : str
            A pointer to the buffer where the service quality name is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_QOS_NAME))
    def CHR_runopts_get_management_qos_endpoint_name(self,
                                                     run_options_handle: int):
        '''
        The CHR_runopts_get_management_qos_endpoint_name function returns the
        quality of service template name that the IxChariot test uses for (1)
        management traffic sent from Endpoint 1 to the console, and (2)
        management traffic exchanged by Endpoint 1 and Endpoint 2.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        qos_name : str
            A pointer to the buffer where the service quality name is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_runopts_set_management_qos_console_name(self,
                                                    run_options_handle: int,
                                                    qos_name: str):
        '''
        The CHR_runopts_set_management_qos_console_name function specifies the
        quality of service template name that the IxChariot test will use for
        the management traffic sent from the console to Endpoint 1.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().
        qos_name : CHR_STRING
            A string containing the quality of service template name.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_runopts_set_management_qos_endpoint_name(self,
                                                     run_options_handle: int,
                                                     qos_name: str):
        '''
        The CHR_runopts_set_management_qos_endpoint_name function specifies the
        quality of service template name that the IxChariot test will use for
        (1) management traffic sent from Endpoint 1 to the console, and (2)
        management traffic exchanged by Endpoint 1 and Endpoint 2.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().
        qos_name : str
            A string containing the quality of service template name.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_runopts_set_overlapped_sends_count(self, run_options_handle: int,
                                               value: int):
        '''
        The CHR_runopts_set_overlapped_sends_count function sets the number of
        multiple buffers sent in parallel.

        Parameters
        ----------
        run_options_handle : int
            A handle returned by CHR_test_get_runopts().
        value : int
            The number of multiple buffers to send. Valid values are in the
            2-999999 range.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Test Object Functions
    #  (CHR_TEST_HANDLE)
    @ctypes_param(c_ulong, ParamOut(c_ubyte), ParamOut(c_ubyte))
    def CHR_test_get_grouping(self, test_handle: int):
        '''
        The CHR_test_get_grouping function gets the grouping order and grouping
        type, for grouping endpoints in the test.
        See also CHR_test_set_grouping_order on page 4-493 and
        CHR_test_set_grouping_type on page 4-494.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        grouping_type : CHR_GROUPING_TYPE_P
            See values listed under CHR_test_set_grouping_type on page 4-494
        grouping_order : CHR_SORT_ORDER_P
            sortOrder can have one of the following values:
        '''
        pass

    @ctypes_param(c_ulong, c_ubyte)
    def CHR_test_set_grouping_type(self, test_handle: int, grouping_type: int):
        '''
        The CHR_test_set_grouping_type function sets the grouping type, for
        grouping endpoints in the test.
        See also CHR_test_set_grouping_order on page 4-493.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().
        grouping_type : CHR_GROUPING_TYPE
            groupingType can have one of the following values:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_ubyte)
    def CHR_test_set_grouping_order(self, test_handle: int,
                                    grouping_order: int):
        '''
        The CHR_test_set_grouping_order function sets the grouping order, for
        grouping endpoints in the test.
        See also CHR_test_set_grouping_type on page 4-494.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().
        grouping_order : CHR_SORT_ORDER
            sortOrder can have one of the following values:
            CHR_SORT_ORDER_ASCENDING
            CHR_SORT_ORDER_DESCENDING

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong)
    def CHR_test_abandon(self, test_handle: int):
        '''
        The CHR_test_abandon function abandons running the given test.
        This call returns immediately, perhaps before the test has stopped.
        Use CHR_test_query_stop() to determine when the test has stopped.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_test_add_mgroup(self, test_handle: int, mgroup_handle: int):
        '''
        The CHR_test_add_mgroup function adds the given multicast group to the
        given test.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().
        mgroup_handle : int
            A handle returned by CHR_mgroup_new(). The multicast group handle
            is checked to ensure that it refers to a properly defined multicast
            group before the group is added to the test, including a valid
            multicast address and port, and a valid script filename. A
            multicast group handle can only be added to one test, and can only
            be added once to that test.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_test_add_pair(self, test_handle: int, pair_handle: int):
        '''
        The CHR_test_add_pair function adds the given pair to the given test.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().
        pair_handle : int
            A handle returned by CHR_pair_new(). The endpoint pair handle is
            checked to ensure that it refers to a properly defined endpoint
            pair before the pair is added to the test, including defined
            endpoint addresses and a valid script filename. A pair handle can
            only be added to one test, and can only be added once to that test.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong)
    def CHR_test_clear_results(self, test_handle: int):
        '''
        The CHR_test_clear_results function clears all the results from the
        test, the multicast pairs in its multicast groups, and its pairs.
        If the test contains results, a test object cannot be deleted, pairs
        and multicast groups cannot be added to the test, and the associated
        run options and datagram options cannot be changed.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong)
    def CHR_test_delete(self, test_handle: int):
        '''
        The CHR_test_delete function frees all memory associated with the given
        test.
        This includes all objects associated with the test including endpoint
        pairs and multicast groups.
        If the test has not been saved since it was defined, modified or was
        run, it cannot be deleted.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong)
    def CHR_test_force_delete(self, test_handle: int):
        '''
        The CHR_test_force_delete function frees all memory associated with the
        given test.
        This includes all objects associated with this test including endpoint
        pairs and multicast groups.
        This function will delete the test object whether or not it has been
        saved.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_test_get_dgopts(self, test_handle: int):
        '''
        The CHR_test_get_dgopts function gets the handle to the datagram
        options for the given test.
        The handle returned by this function is needed for other function
        calls to operate on this object.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        dgopts_handle : int
            A pointer to the variable where the handle to the datagram options
            is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_FILE_PATH))
    def CHR_test_get_filename(self, test_handle: int):
        '''
        The CHR_test_get_filename function gets the name of the file from which
        this test was loaded or to which it is to be saved.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        save_file_name : str
            A pointer to the buffer where the filename is returned.
            The returned filename includes any specified path information.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_test_get_how_ended(self, test_handle: int):
        '''
        The CHR_test_get_how_ended function gets the value indicating how the
        test ended.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        how_ended : CHR_TEST_HOW_ENDED_P
            A pointer to the variable where the test ended value is returned.
            See Typedefs and Enumerations on page 4-612 for CHR_TEST_HOW_ENDED
            values.
        '''
        pass

    @ctypes_param(c_ulong)
    def CHR_test_get_local_start_time(self, test_handle: int):
        '''
        The CHR_test_get_local_start_time function gets the time the test
        started.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong)
    def CHR_test_get_local_stop_time(self, test_handle: int):
        '''
        The CHR_test_get_local_stop_time function gets the time the test
        stopped.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong, ParamOut(c_ulong))
    def CHR_test_get_mgroup(self, test_handle: int, index: int):
        '''
        The CHR_test_get_mgroup function gets the handle to a specific
        multicast group in the given test.
        The handle returned by this function is needed for other function
        calls to operate on this object.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().
        index : int
            An index into the array of multicast groups. The index is
            determined by the order in which mgroups were added to this test.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        mgroup_handle : int
            A pointer to the variable where the handle for the multicast group
            is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_test_get_mgroup_count(self, test_handle: int):
        '''
        The CHR_test_get_mgroup_count function gets the number of multicast
        groups owned by the given test.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        mgroup_count : int
            A pointer to the variable where the number of multicast groups is
            returned.
        '''
        pass

    @ctypes_param(c_ulong, c_ulong, ParamOut(c_ulong))
    def CHR_test_get_pair(self, test_handle: int, index: int):
        '''
        The CHR_test_get_pair function gets the handle to a specific endpoint
        pair in the given test.
        The handle returned by this function is needed for other function
        calls to operate on this object.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().
        index : int
            An index into the endpoint pairs list. The index is determined by
            the order in which pairs were added to this test.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        pair_handle : int
            A pointer to the variable where the handle for the endpoint pair is
            returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_test_get_pair_count(self, test_handle: int):
        '''
        The CHR_test_get_pair_count function gets the number of endpoint pairs
        owned by the given test.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        pair_count : int
            A pointer to the variable where the number of pairs is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_test_get_runopts(self, test_handle: int):
        '''
        The CHR_test_get_runopts function gets the handle to the run options
        for the given test.
        The handle returned by this function is needed for other function
        calls to operate on this object.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        runopts_handle : int
            A pointer to get the handle to the run options for the given
            test.
        '''
        pass

    @ctypes_param(c_ulong)
    def CHR_test_get_start_time(self, test_handle: int):
        '''
        The CHR_test_get_start_time function gets the time the test started.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong)
    def CHR_test_get_stop_time(self, test_handle: int):
        '''
        The CHR_test_get_stop_time function gets the time the test stopped.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_test_get_throughput_units(self, test_handle: int):
        '''
        The function CHR_test_get_throughput_units gets the throughput units
        defined for the given test.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        throughput_units : CHR_THROUGHPUT_UNITS_P
            A pointer to the variable where the throughput unit value is
            returned. See the "CHR_test_set_throughput_units" function for
            information on valid throughput unit values.
        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_test_load(self, test_handle: int, test_file_name: str):
        '''
        The CHR_test_load function loads a test from the given file.
        This function uses the run options that have been defined for the test.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new(). A test cannot be loaded using
            an existing test handle unless the test to which the handle refers
            has been saved or has not been modified since it was loaded.
        test_file_name : str
            A handle returned by CHR_test_new(). A test cannot be loaded using
            an existing test handle unless the test to which the handle refers
            has been saved or has not been modified since it was loaded.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(ParamOut(c_ulong))
    def CHR_test_new(self):
        '''
        The CHR_test_new function creates a test object and its associated
        run options and datagram options objects, and initializes them to
        object default values

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        test_handle : int
            A pointer to the variable where the handle for the new test is
            returned.
            This handle is needed for other function calls to operate on
            this object.
        '''

        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_test_query_stop(self, test_handle: int, timeout: int):
        '''
        The CHR_test_query_stop function waits the given time for the test
        to stop.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().
        timeout : int
            The time in seconds to wait for the test to stop or CHR_INFINITE.
            This call blocks until the test stops or the timeout is reached.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong)
    def CHR_test_save(self, test_handle: int):
        '''
        The CHR_test_save function saves the given test to the currently
        defined filename.
        Before it can be saved, the test must not be running and it must have
        at least one pair, multicast group, or application group.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_test_set_filename(self, test_handle: int, save_file_name: str):
        '''
        The CHR_test_set_filename function sets or changes the name of the file
        to which the given test is saved.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().
        save_file_name : CHR_STRING
            A string containing the filename. The filename may be specified
            using a relative or an absolute pathname.
            Note that once you've set the filename, you can't change it back
            to the loaded filename.
            To reset the filename to the name of the loaded test, use a null
            filename parameter and a "0" filename length..

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_test_set_throughput_units(self, test_handle: int,
                                      throughput_units: int):
        '''
        The CHR_test_set_throughput_units function sets or changes the
        throughput units value for the given test.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().
        throughput_units : int
            Provides one of the CHR_THROUGHPUT_UNITS values:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong)
    def CHR_test_start(self, test_handle: int):
        '''
        The CHR_test_start function starts running the given test.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        '''
        pass

    @ctypes_param(c_ulong)
    def CHR_test_stop(self, test_handle: int):
        '''
        The CHR_test_stop function requests that the given running test be
        stopped.
        This call can and usually does return before the test has stopped.
        Use the CHR_test_query_stop function to determine when the test has
        actually stopped.
        If the test doesn't stop within a reasonable amount of time, use
        CHR_test_abandon function to stop the test.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_test_load_app_groups(self, test_handle: int, filename: str):
        '''
        The CHR_test_load_app_groups function loads a test from the given file.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new(). A test cannot be loaded using
            an existing test handle unless the test to which the handle refers
            has been saved or has not been modified since it was loaded.
        filename : str
            A string containing the name of the file from which to load the
            test.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_test_add_app_group(self, test_handle: int, app_group_handle: int):
        '''
        The CHR_test_add_app_group function adds the given application group to
        the given test.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().
        app_group_handle : int
            A handle returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_test_remove_app_group(self, test_handle: int,
                                  app_group_handle: int):
        '''
        The CHR_test_remove_app_group function removes the specified
        application group from the specified test.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().
        app_group_handle : int
            A handle returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong, ParamOut(c_ulong))
    def CHR_test_get_app_group_by_index(self, test_handle: int, index: int):
        '''
        The CHR_test_get_app_group_by_index function gets the handle to a
        specific application group in the given test.
        The handle returned by this function is needed for other function
        calls to operate on this object.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().
        index : int
            An index into the application group list. The index is determined
            by the order in which application groups were added to this test.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        app_group_handle : int
            A pointer to the variable where the handle for the application
            group is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes), ParamOut(c_ulong))
    def CHR_test_get_app_group_by_name(self, test_handle: int, name: str):
        '''
        The CHR_test_get_app_group_by_name function gets the handle to a
        specific application group in the given test.
        The handle returned by this function is needed for other function
        calls to operate on this object.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().
        name : str
            A string containing the name of the application group.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        app_group_handle : int
            A pointer to the variable where the handle for the application
            group is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_test_get_app_group_count(self, test_handle: int):
        '''
        The CHR_test_get_app_group_count function gets the number of endpoint
        pairs owned by the given test.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        app_group_count : int
            A pointer to the variable where the number of pairs is returned.
        '''
        pass

    #  These are Ixia hardware specfic functions to
    #  manipulate the stack manager configuration in the
    #  file.
    @ctypes_param(c_ulong, bytes, c_ulong, c_ulong, c_longlong)
    def CHR_test_set_test_server_session(self,
                                         test_handle: int,
                                         test_server_address: str,
                                         test_server_size: int,
                                         test_server_port: int,
                                         session_object_id: int):
        '''
        The CHR_test_set_test_server_session function associates the test with
        an active Aptixia session.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().
        test_server_address : str
            The IP address of the TestServer.
        test_server_size : int
            The size of the testServerAddress buffer.
        test_server_port : int
            The TCP port of the TestServer. (Note that 0 indicates the default
            of 5568.)
        session_object_id : int
            The 64-bit Object ID associated with the session to connect to.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes), ParamOut(c_ulong),
                  ParamOut(c_longlong))
    def CHR_test_get_test_server_session(self, test_handle: int):
        '''
        The CHR_test_get_test_server_session function gets the TestServer
        address, port, and Object ID for the Aptixia session that is currently
        active in the test.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        test_server_address : str
            The returned test server address.
        test_server_port : int
            The returned TCP port.
        session_object_id : int
            The returned 64-bit Object ID of the session.
        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_test_set_ixia_network_configuration(self, test_handle: int,
                                                data_ptr: str):
        '''
        The CHR_test_set_ixia_network_configuration function applies the Ixia
        port configuration to the test identified by testHandle.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().
        data_ptr : CHR_BYTE_P
            A pointer to the buffer containing the Ixia port configuration.
        data_size : CHR_LENGTH
            The size of the configuration buffer pointed to by dataPtr.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes))
    def CHR_test_get_ixia_network_configuration(self, test_handle: int):
        '''
        The CHR_test_get_ixia_network_configuration function gets the Ixia port
        configuration that is presently associated with the test identified by
        testHandle.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        data_ptr : CHR_BYTE_P
            A pointer to the variable where the Ixia network configuration is
            returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_test_load_ixia_network_configuration(self, test_handle: int,
                                                 file_name: str):
        '''
        The CHR_test_load_ixia_network_configuration function loads the Ixia
        port configuration into the test object identified by testHandle.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().
        file_name : str
            The filename associated with the Ixia network configuration.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_test_save_ixia_network_configuration(self, test_handle: int,
                                                 file_name: str):
        '''
        The CHR_test_save_ixia_network_configuration function saves the Ixia
        port configuration from the test object identified by testHandle to the
        file identified by fileName.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().
        file_name : str
            The filename associated with the Ixia network configuration.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong)
    def CHR_test_clear_ixia_network_configuration(self, test_handle: int):
        '''
        The CHR_test_clear_ixia_network_configuration function clears the Ixia
        port configuration that is presently associated with test identified by
        testHandle.

        Parameters
        ----------
        test_handle : int
            A handle returned by CHR_test_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Timing Record Obect Functions
    #  (CHR_TIMINGREC_HANDLE)

    @ctypes_param(c_ulong, ParamOut(c_double))
    def CHR_timingrec_get_elapsed(self, timingrec_handle: int):
        '''
        The CHR_timingrec_get_elapsed function gets the elapsed time in seconds
        from the given timing record.

        Parameters
        ----------
        timingrec_handle : int
            A handle returned by CHR_pair_get_timing_record() or
            CHR_mpair_get_timing_record().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        elapsed : float
            A pointer to the variable where the elapsed time is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_double))
    def CHR_timingrec_get_end_to_end_delay(self, timingrec_handle: int):
        '''
        The CHR_timingrec_get_end_to_end_delay function gets the end-to-end
        delay in milliseconds from the given timing record.

        Parameters
        ----------
        timingrec_handle : int
            A handle returned by CHR_pair_get_timing_record() or
            CHR_mpair_get_timing_record().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        delay : float
            A pointer to the variable where the end-to-end delay is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_double))
    def CHR_timingrec_get_inactive(self, timingrec_handle: int):
        '''
        The CHR_timingrec_get_inactive function gets the inactive time in
        seconds from the given timing record.

        Parameters
        ----------
        timingrec_handle : int
            A handle returned by CHR_pair_get_timing_record() or
            CHR_mpair_get_timing_record().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        inactive : float
            A pointer to the variable where the inactive time is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_double))
    def CHR_timingrec_get_jitter(self, timingrec_handle: int):
        '''
        The CHR_timingrec_get_jitter function gets the jitter time in seconds
        from the given timing record.

        Parameters
        ----------
        timingrec_handle : int
            A handle returned by CHR_pair_get_timing_record() or
            CHR_mpair_get_timing_record().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        jitter : float
            A pointer to the variable where the jitter time is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_timingrec_get_max_consecutive_lost(self,
                                               timingrec_handle: int):
        '''
        The CHR_timingrec_get_max_consecutive_lost function gets the maximum
        consecutive lost datagrams from the given timing record.
        VoIP Test Module only.

        Parameters
        ----------
        timingrec_handle : int
            A handle returned by CHR_pair_get_timing_record() or
            CHR_mpair_get_timing_record().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        lost : int
            A pointer to the variable where the maximum consecutive lost
            datagrams is returned.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_timingrec_get_max_delay_variation(self, timingrec_handle: int):
        '''
        The CHR_timingrec_get_max_delay_variation function gets the jitter
        (delay variation) maximum in milliseconds from the given timing record.

        Parameters
        ----------
        timingrec_handle : int
            A handle returned by CHR_pair_get_timing_record() or
            CHR_mpair_get_timing_record().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        variation : int
            A pointer to the variable where the jitter (delay variation)
            maximum is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_double))
    def CHR_timingrec_get_MOS_estimate(self, timingrec_handle: int):
        '''
        The CHR_timingrec_get_MOS_estimate function gets the Mean Opinion Score
        (MOS) estimate from the given timing record.

        Parameters
        ----------
        timingrec_handle : int
            A handle returned by CHR_pair_get_timing_record().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        estimate : float
            A pointer to the variable where the MOS estimate is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_timingrec_get_one_way_delay(self, timingrec_handle: int):
        '''
        The CHR_timingrec_get_one_way_delay function gets the one-way delay in
        milliseconds from the given timing record.

        Parameters
        ----------
        timingrec_handle : int
            A handle returned by CHR_pair_get_timing_record() or
            CHR_mpair_get_timing_record().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        delay : int
            A pointer to the variable where the one-way delay is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_double))
    def CHR_timingrec_get_R_value(self, timingrec_handle: int):
        '''
        The CHR_timingrec_get_R_value function gets the R-value calculated for
        the given timing record.

        Parameters
        ----------
        timingrec_handle : int
            A handle returned by CHR_pair_get_timingrecord().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        rvalue : float
            A pointer to the variable where the R-value is returned.
        '''
        pass

    @ctypes_param(c_ulong, c_char, c_ulong, ParamOut(c_ulong))
    def CHR_timingrec_get_result_frequency(self,
                                           timingrec_handle: int,
                                           result_type: int,
                                           index: int):
        '''
        The CHR_timingrec_get_result_frequency function gets the number of
        occurrences in a specified range for the specified result from the
        given timing record.

        Parameters
        ----------
        timingrec_handle : int
            A handle returned by CHR_pair_get_timing_record() or
            CHR_mpair_get_timing_record().
        result_type : int
            A result type to query. One of the following:
        index : int
            The index of the range where the frequency will be retrieved. Range
            indices run from 0 to the number of configured ranges - 1.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        frequency : int
            A pointer to the variable where the frequency is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_long))
    def CHR_timingrec_get_e1_rssi(self, timingrec_handle: int):
        '''
        The CHR_timingrec_get_e1_RSSI function gets the Receive Signal Strength
        Indicator for Endpoint 1.
        This may only be used for non-streaming scripts.

        Parameters
        ----------
        timingrec_handle : int
            A handle returned by CHR_pair_get_timing_record() or
            CHR_mpair_get_timing_record().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        rssi : CHR_LONG_P
            A pointer to the variable where the receive signal strength
            indicator is returned. A range of -10 (strong) to -100 (weak) is
            used.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_long))
    def CHR_timingrec_get_e2_rssi(self, timingrec_handle: int):
        '''
        The CHR_timingrec_get_e1_RSSI function gets the Receive Signal Strength
        Indicator for endpoint 1.
        This may only be used for streaming scripts.

        Parameters
        ----------
        timingrec_handle : int
            A handle returned by CHR_pair_get_timing_record() or
            CHR_mpair_get_timing_record().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        rssi : int
            A pointer to the variable where the receive signal strength
            indicator is returned. A range of -10 (strong) to -100 (weak) is
            used.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_BSSID_SIZE))
    def CHR_timingrec_get_e1_bssid(self, timingrec_handle: int):
        '''
        The CHR_timingrec_get_e1_BSSID function gets the Base Service Station
        ID for Endpoint 1.
        This is only valid when using non-streaming scripts.

        Parameters
        ----------
        timingrec_handle : int
            A handle returned by CHR_pair_get_timing_record() or
            CHR_mpair_get_timing_record().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        bssid : str
            A pointer to the variable where the base station ID is returned.
            The result is in the form of a standard MAC address:
            "01:02:03:04:05:06".
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_BSSID_SIZE))
    def CHR_timingrec_get_e2_bssid(self, timingrec_handle: int):
        '''
        The CHR_timingrec_get_e1_BSSID function gets the Base Service Station
        ID for Endpoint 2.
        This is only valid for streaming scripts.

        Parameters
        ----------
        timingrec_handle : int
            A handle returned by CHR_pair_get_timing_record() or
            CHR_mpair_get_timing_record().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        bssid : str
            A pointer to the variable where the base station ID is returned.
            The result is in the form of a standard MAC address:
            "01:02:03:04:05:06".
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_timingrec_get_df(self, timingrec_handle: int):
        '''
        The CHR_timingrec_get_df function gets the DF (delay factor) value
        generated from a video pair or video multicast group test.

        Parameters
        ----------
        timingrec_handle : int
            A handle returned by CHR_pair_get_timing_record() or
            CHR_mpair_get_timing_record().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        df : int
            A pointer to the variable where the DF (delay factor) value is
            returned.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_double))
    def CHR_timingrec_get_mlr(self, timingrec_handle: int):
        '''
        The CHR_timingrec_get_mlr function gets the MLR (media loss rate) value
        generated from a video pair or video multicast group test.
        MLR is the number of media packets lost per second.

        Parameters
        ----------
        timingrec_handle : int
            A handle returned by CHR_pair_get_timing_record() or
            CHR_mpair_get_timing_record().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        mlr : float
            A pointer to the variable where the MLR value is returned.
        '''
        pass

    #  Returns the Report Group Identifier field from the timing record.
    #
    #  @param i_recordHandle    Timing record handle.
    #  @param o_reportGroupId   Report group identifier.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_timingrec_get_report_group_id(self, i_record_handle: int):
        '''
        The CHR_timingrec_get_report_group_id function returns the report group
        identifier field from the specified timing record.

        Parameters
        ----------
        i_record_handle : int
            A timing record handle returned by CHR_vpair_get_timing_record(),
            CHR_pair_get_timing_record(), or CHR_mpair_get_timing_record().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_report_group_id : int
            A pointer to the variable where the report group identifier is
            returned.
        '''
        pass

    #  Traceroute Object Functions
    #  (CHR_TRACERT_PAIR_HANDLE)

    @ctypes_param(c_ulong)
    def CHR_tracert_pair_delete(self, pair_handle: int):
        '''
        The CHR_tracert_pair_delete function deletes a traceroute pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_tracert_pair_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_ADDR))
    def CHR_tracert_pair_get_e1_addr(self, pair_handle: int):
        '''
        The CHR_tracert_pair_get_e1_addr function gets the address for Endpoint
        1 in a given traceroute.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_tracert_pair_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        e1_name : str
            A pointer to the buffer where the Endpoint 1 address is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_ADDR))
    def CHR_tracert_pair_get_e2_addr(self, pair_handle: int):
        '''
        The CHR_tracert_pair_get_e2_addr function gets the address for Endpoint
        2 in a given traceroute.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_tracert_pair_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        e1_name : str
            A pointer to the buffer where the Endpoint 2 address is returned.
        '''
        pass

    @ctypes_param(c_ulong, c_ulong, ParamOut(c_ulong))
    def CHR_tracert_pair_get_hop_record(self, trpair_handle: int, index: int):
        '''
        The CHR_tracert_pair_get_hop_record function gets the record number for
        a particular hop of a traceroute.

        Parameters
        ----------
        trpair_handle : int
            A handle returned by CHR_tracert_pair_new().
        index : int
            The number indicating which hop. The number is determined by the
            order in which traceroute data reached the hop.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        hop_record_handle : int
            A handle returned by CHR_tracert_pair_get_hop_record.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_tracert_pair_get_max_hops(self, pair_handle: int):
        '''
        The CHR_tracert_pair_get_max_hops function gets the maximum hop count
        before a traceroute is abandoned.

        Parameters
        ----------
        pair_handle : int
            A pointer to the variable where the maximum number of hops for a
            traceroute is returned.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        max_hops : int
            A pointer to the variable where the maximum number of hops for
            a traceroute is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_tracert_pair_get_max_timeout(self, pair_handle: int):
        '''
        The CHR_tracert_pair_get_max_timeout function gets the maximum timeout
        value before a traceroute is abandoned.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_tracert_pair_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        max_timeout : int
            A pointer to the variable where the maximum time to wait for a
            reply from a particular hop is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_tracert_pair_get_resolve_hop_name(self, pair_handle: int):
        '''
        The CHR_tracert_pair_get_resolve_hop_name function determines whether
        hop names for a particular hop in a traceroute will be resolved.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_tracert_pair_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        resolve_name : int
            Specifies CHR_TRUE or CHR_FALSE to indicate whether hop names will
            be resolved.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_tracert_pair_get_runStatus(self, pair_handle: int):
        '''
        The CHR_tracert_pair_get_runStatus function gets the status of a
        traceroute.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_tracert_pair_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        status : CHR_TRACERT_RUNSTATUS_TYPE_P
            A pointer to the variable where the runstatus is returned. The
            following status types are applicable:
        '''
        pass

    @ctypes_param(ParamOut(c_ulong))
    def CHR_tracert_pair_new(self):
        '''
        The CHR_tracert_pair_new function selects an endpoint pair on which a
        traceroute will be run.

        Parameters
        ----------

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        pair_handle : int
            A pointer to the variable where the handle for the new traceroute
            pair is returned.
        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_tracert_pair_query_stop(self, pair_handle: int, timeout: int):
        '''
        The CHR_tracert_pair_query_stop function waits the given time for the
        test to stop.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_tracert_pair_new().
        timeout : int
            The time in seconds to wait for the test to stop or CHR_INFINITE.
            This call blocks until the test stops or the timeout is reached.
            This should be the same value as the maximum number of hops in the
            traceroute.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_tracert_pair_results_get_hop_count(self, pair_handle: int):
        '''
        The CHR_tracert_pair_results_get_hop_count function gets the number of
        hops in a traceroute.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_tracert_pair_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        count : int
            A pointer to the variable where the number of hops in a traceroute
            is returned.
        '''
        pass

    @ctypes_param(c_ulong)
    def CHR_tracert_pair_run(self, pair_handle: int):
        '''
        The CHR_tracert_pair_run starts a traceroute.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_tracert_pair_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_tracert_pair_set_e1_addr(self, pair_handle: int, e1_name: str):
        '''
        The CHR_tracert_pair_set_e1_addr function sets or changes the address
        for Endpoint 1 in a given traceroute.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_tracert_pair_new().
        e1_name : str
            A pointer to the buffer where the Endpoint 1 address is stored.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_tracert_pair_set_e2_addr(self, pair_handle: int, e2_name: str):
        '''
        The CHR_tracert_pair_set_e2_addr function sets or changes the address
        for Endpoint 2 in a given traceroute.
        <META NAME="Keywords" CONTENT="Traceroute Pair Object
        Functions:CHR_tracert_pair_set_e2_addr">

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_tracert_pair_new().
        e2_name : str
            A pointer to the buffer where the Endpoint 2 address is stored.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_tracert_pair_set_max_hops(self, pair_handle: int, max_hops: int):
        '''
        The CHR_tracert_pair_set_max_hops function sets or changes the maximum
        hop count before a traceroute is abandoned.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_tracert_pair_new().
        max_hops : int
            The value that specifies the maximum number of hops for a
            traceroute before it is abandoned. This value must be between 2 and
            40.The default value for maximum hops is 30.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_tracert_pair_set_max_timeout(self,
                                         pair_handle: int,
                                         max_timeout: int):
        '''
        The CHR_tracert_pair_set_max_timeout function sets or changes the
        maximum timeout value before a traceroute is abandoned.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_tracert_pair_new().
        max_timeout : int
            The maximum time to wait for the traceroute to complete (in
            milliseconds). This value must be between 1 and 10,000.The default
            value for maximum timeout is 3000 milliseconds.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_tracert_pair_set_resolve_hop_name(self,
                                              pair_handle: int,
                                              resolve_name: int):
        '''
        The CHR_tracert_pair_set_resolve_hop_name function sets or changes the
        resolution of hop addresses in a traceroute to hop names.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_tracert_pair_new().
        resolve_name : int
            Specifies CHR_TRUE or CHR_FALSE to indicate whether to use resolved
            hop names.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong)
    def CHR_tracert_pair_stop(self, pair_handle: int):
        '''
        The CHR_tracert_pair_stop function stops a running traceroute.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_tracert_pair_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  ----------------------------------------------------------------------
    #                    VoIP Pair functions
    #                    (CHR_VOIP_PAIR_HANDLE)
    #  ----------------------------------------------------------------------

    @ctypes_param(ParamOut(c_ulong))
    def CHR_voip_pair_new(self):
        '''
        The CHR_voip_pair_new function creates an endpoint pair object for
        voice over IP testing and initializes it to object default values.
        See VoIP Pair Object on page 2-16 for information on the object
        default values.

        Parameters
        ----------

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        pair_handle : int
            A pointer to the variable where the handle for the new endpoint
            pair is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_voip_pair_get_codec(self, pair_handle: int):
        '''
        The CHR_voip_pair_get_codec function gets the codec type for the given
        endpoint pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_voip_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        codec : int
            A pointer to the variable where the codec is returned. See
            CHR_voip_pair_set_codec on page 4-597 for applicable codecs.
        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_voip_pair_set_codec(self, pair_handle: int, codec: int):
        '''
        The CHR_voip_pair_set_codec function sets or changes the codec for the
        given endpoint pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_voip_pair_new() or CHR_test_get_pair().
        codec : int
            Provides one of the following codecs:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_voip_pair_get_additional_delay(self, pair_handle: int):
        '''
        The CHR_voip_pair_get_additional_delay function gets the delay value
        for the given endpoint pair.
        See also CHR_voip_pair_set_additional_delay on page 4-596.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_voip_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        size : int
            Specifies the size, in milliseconds, for the additional delay.
            Valid values are in the following ranges:

        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_voip_pair_set_additional_delay(self, pair_handle: int, delay: int):
        '''
        The CHR_voip_pair_set_additional_delay function allows the user to set
        a delay value to account for known delays (such as device delays) that
        are not otherwise measured by a Chariot voice over IP test.
        This delay is included when calculating the MOS estimate and R-value.

        Parameters
        ----------
        pair_handle : int
            Specifies the delay in milliseconds (ms) that the user wishes to
            account for. Range is 0 to 300 ms.
        delay : int
            Specifies the delay in milliseconds (ms) that the user wishes to
            account for. Range is 0 to 300 ms.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_voip_pair_get_datagram_delay(self, pair_handle: int):
        '''
        The CHR_voip_pair_get_datagram_delay function gets the delay between
        voice datagrams for one voice over IP pair.
        See also CHR_voip_pair_set_datagram_delay on page 4-599.

        Parameters
        ----------
        pair_handle : int
            Specifies the delay in milliseconds (ms) that the user wishes to
            account for.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        delay : int
            Specifies the delay in milliseconds (ms) that the user wishes to
            account for.
        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_voip_pair_set_datagram_delay(self, pair_handle: int, delay: int):
        '''
        The CHR_voip_pair_set_datagram_delay function sets or changes the delay
        between voice datagrams for one voice over IP pair.
        By default, the delay is set to 20 ms (G711u, G711a, G729, G.
        726) or 30 ms (G723.
        1A, G723.
        1M).
        The delay between datagrams is equivalent to the datagram size.
        The timing record duration may be adjusted slightly so that only full
        buffers are sent.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_voip_pair_new() or CHR_test_get_pair().
        delay : int
            Specifies the delay between voice datagrams in milliseconds (ms).
            Valid values are in the range of 20 ms  200 ms inclusive.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ushort))
    def CHR_voip_pair_get_dest_port_num(self, pair_handle: int):
        '''
        The CHR_voip_pair_get_dest_port_num  function gets the destination port
        number for a single voice over IP pair.
        See also CHR_voip_pair_set_dest_port_num on page 4-600.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_voip_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        port : int
            Specifies the port number to be used. The value 0 (or the macro
            CHR_PORT_AUTO) instructs Chariot to automatically select the port.
        '''
        pass

    @ctypes_param(c_ulong, c_ushort)
    def CHR_voip_pair_set_dest_port_num(self, pair_handle: int, port: int):
        '''
        The CHR_voip_pair_set_dest_port_num function sets or changes the
        destination port number for a single voice over IP pair.
        By default, the port number is set to CHR_PORT_AUTO.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_voip_pair_new() or CHR_test_get_pair().
        port : int
            Specifies the port number to be used. Valid values are in the range
            0  65535 inclusive, where 0 (or the macro CHR_PORT_AUTO) instructs
            Chariot to automatically select the port.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes))
    def CHR_voip_pair_get_initial_delay(self, pair_handle: int):
        '''
        The CHR_voip_pair_get_initial_delay function gets the delay before the
        first voice data traffic is transmitted in the voice over IP test.
        See also CHR_voip_pair_set_initial_delay on page 4-601.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_voip_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        delay : str
            A pointer to a string that will contain the initial delay in the
            same format as the one used for set.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes))
    def CHR_voip_pair_set_initial_delay(self, pair_handle: int):
        '''
        The CHR_voip_pair_set_initial_delay function sets or changes the delay
        before the first voice data traffic is transmitted in the voice over IP
        test.
        By default, the initial delay is set to 0.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_voip_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        delay : str
            Specifies the initial delay distribution. Valid values are in the
            form of "d[x,y]", where:
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_voip_pair_get_jitter_buffer_size(self, pair_handle: int):
        '''
        The CHR_voip_pair_get_jitter_buffer_size  function gets the size of the
        jitter buffer.
        See also CHR_voip_pair_set_jitter_buffer_size on page 4-602.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_voip_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        size : int
            Specifies the size, in milliseconds, for the jitter buffer.
        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_voip_pair_set_jitter_buffer_size(self,
                                             pair_handle: int,
                                             size: int):
        '''
        The CHR_voip_pair_set_jitter_buffer_size function sets or changes the
        size of the jitter buffer.
        You can set the size of the jitter buffer to zero if you do not want
        IxChariot to emulate jitter buffering in your test.
        By default, the jitter buffer is two times the delay between packets.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_voip_pair_new() or CHR_test_get_pair().
        size : int
            Specifies the size, in milliseconds, for the jitter buffer. Valid
            values are in the following ranges:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ushort))
    def CHR_voip_pair_get_source_port_num(self, pair_handle: int):
        '''
        The CHR_voip_pair_get_source_port_num  function gets the source port
        number for a voice over IP pair.
        See also CHR_voip_pair_set_source_port_num on page 4-607.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_voip_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        port : int
            Specifies the port number to be used. The value 0 (or the macro
            CHR_PORT_AUTO) instructs Chariot to automatically select the port.
        '''
        pass

    @ctypes_param(c_ulong, c_ushort)
    def CHR_voip_pair_set_source_port_num(self, pair_handle: int, port: int):
        '''
        The CHR_voip_pair_set_source_port_num function sets or changes the
        source port number for a voice over IP pair.
        By default, the port number is set to CHR_PORT_AUTO.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_voip_pair_new() or CHR_test_get_pair().
        port : int
            Specifies the port number to be used. Valid values are in the range
            0  65535 inclusive, where 0 (or the macro CHR_PORT_AUTO) instructs
            Chariot to automatically select the port.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_voip_pair_get_tr_duration(self, pair_handle: int):
        '''
        The CHR_voip_pair_get_tr_duration  function gets the duration of a
        single timing record generated by a single voice over IP pair.
        See also CHR_voip_pair_set_tr_duration on page 4-608.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_voip_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        seconds : int
            Specifies the approximate time, in seconds, for one timing record
            to complete.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_voip_pair_set_tr_duration(self, pair_handle: int, seconds: int):
        '''
        The CHR_voip_pair_set_tr_duration function sets or changes the duration
        of a single timing record generated by a single voice over IP pair.
        By default, the duration is set to 3 seconds.
        The duration may be adjusted slightly so that only full buffers are
        sent.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_voip_pair_new() or CHR_test_get_pair().
        seconds : int
            Specifies the approximate time, in seconds, for one timing record
            to complete. Valid values are in the range of 1  3600 inclusive.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_voip_pair_get_no_of_timing_records(self, pair_handle: int):
        '''
        The CHR_voip_pair_get_no_of_timing_records  function gets the number of
        timing records for a VoIP pair.
        See also CHR_voip_pair_set_no_of_timing_records on page 4-603.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_voip_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        no_of_tr : int
            Specifies the number of timing records that the endpoint will
            create during the execution of a test.
        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_voip_pair_set_no_of_timing_records(self,
                                               pair_handle: int,
                                               no_of_tr: int):
        '''
        The CHR_voip_pair_set_no_of_timing_records function allows you to set
        the number of timing records for a VoIP pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_voip_pair_new() or CHR_test_get_pair().
        no_of_tr : int
            Specifies the number of timing records that the endpoint will
            create during the execution of a test. The valid range is from 1 to
            2147483647, inclusive. The default value is 50.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_voip_pair_get_use_PLC(self, pair_handle: int):
        '''
        The CHR_voip_pair_get_use_PLC  function gets the value of the use_PLC
        setting.
        See also CHR_voip_pair_set_use_PLC on page 4-609.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_voip_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        use : int
            Specifies CHR_TRUE or CHR_FALSE to indicate whether to use PLC.
        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_voip_pair_set_use_PLC(self, pair_handle: int, use: int):
        '''
        The CHR_voip_pair_set_use_PLC function allows you to emulate packet
        loss concealment (PLC).
        PLC is supported by the G.
        711 codecs only.
        The default setting is not to use PLC (CHR_FALSE).

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_voip_pair_new() or CHR_test_get_pair().
        use : int
            Specifies CHR_TRUE or CHR_FALSE to indicate whether to use PLC.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_voip_pair_get_use_silence_sup(self, pair_handle: int):
        '''
        The CHR_voip_pair_get_use_silence_sup  function gets the value of the
        silence suppression setting.
        See also CHR_voip_pair_set_use_silence_sup on page 4-610.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_voip_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        use : int
            Specifies CHR_TRUE or CHR_FALSE to indicate whether to use silence
            suppression.
        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_voip_pair_set_use_silence_sup(self, pair_handle: int, use: int):
        '''
        The CHR_voip_pair_set_use_silence_sup function sets or changes whether
        silence suppression is enabled.
        If the value is set to CHR_TRUE, silence suppression is enabled.
        The voice activity rate (set by CHR_voip_pair_set_voice_activ_rate) is
        ignored when this value is set to CHR_FALSE.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_voip_pair_new() or CHR_test_get_pair().
        use : int
            Specifies CHR_TRUE or CHR_FALSE to indicate whether to use silence
            suppression.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_voip_pair_get_voice_activ_rate(self, pair_handle: int):
        '''
        The CHR_voip_pair_get_voice_activ_rate  function gets the voice
        activity rate for a voice over IP pair.
        See also CHR_voip_pair_set_voice_activ_rate on page 4-611.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_voip_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        rate : int
            Specifies a voice activity rate percentage.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_voip_pair_set_voice_activ_rate(self, pair_handle: int, rate: int):
        '''
        The CHR_voip_pair_set_voice_activ_rate function sets or changes the
        voice activity rate for silence suppression in the voice over IP test.
        This value is ignored unless silence suppression has been enabled (see
        CHR_voip_pair_set_use_silence_sup).
        By default, the activity rate is set to 50 percent.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_voip_pair_new() or CHR_test_get_pair().
        rate : int
            Specifies a voice activity rate percentage (1-100).

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes), ParamOut(c_ulong), ParamOut(c_char))
    def CHR_voip_pair_get_payload_file(self,
                                       pair_handle: int,
                                       filename: str):
        '''
        The CHR_voip_pair_get_payload_file  function gets a file whose content
        will be used as payload when running the VoIP pair.
        See also CHR_voip_pair_set_payload_file on page 4-604.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_voip_pair_new() or CHR_test_get_pair().
        filename : str
            The buffer that will hold the filename (as returned by this
            function).

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        rtnlen : int
            rtnlen = 0 means random payload is selected, while rtnlen > 0 means
            payload file is selected (and the file was set to "filename"
            buffer).
        embedded : int
            Specifies whether the payload file will be embedded within the
            script or referenced as an external file.
        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes), c_char)
    def CHR_voip_pair_set_payload_file(self,
                                       pair_handle: int,
                                       filename: str,
                                       embedded: int):
        '''
        The CHR_voip_pair_set_payload_file function allows a user to specify a
        file whose content will be used as payload when running the VoIP pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_voip_pair_new().
        filename : str
            The name of the file containing the payload data.
        embedded : int
            Specifies whether the payload file will be embedded within the
            script or referenced as an external file:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong)
    def CHR_voip_pair_set_payload_random(self, pair_handle: int):
        '''
        The CHR_voip_pair_set_payload_random function sets the payload for a
        VoIP test to random data.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_voip_pair_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  ----------------------------------------------------------------------
    #                    Video Unicast Pair functions
    #                      (CHR_VIDEO_PAIR_HANDLE)
    #  ----------------------------------------------------------------------

    @ctypes_param(ParamOut(c_ulong))
    def CHR_video_pair_new(self):
        '''
        The CHR_video_pair_new function creates a new video pair object for
        unicast video testing, and initializes it to object default values.
        See Video Pair Object Default Values on page 2-18 for information on
        the object default values.

        Parameters
        ----------

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        pair_handle : int
            A pointer to the variable where the handle for the new video pair
            is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_video_pair_get_codec(self, pair_handle: int):
        '''
        The CHR_video_pair_get_codec function gets the codec defined for the
        given video pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_video_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        codec : CHR_VIDEO_CODEC_P
            A pointer to the variable where the codec is returned. See
            CHR_video_pair_set_codec on page 4-571 for applicable codecs.
        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_video_pair_set_codec(self, pair_handle: int, codec: int):
        '''
        The CHR_video_pair_set_codec function sets or changes the codec for the
        given video pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_video_pair_new() or CHR_test_get_pair().
        codec : int
            Provides one of the following codecs:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ushort))
    def CHR_video_pair_get_dest_port_num(self, pair_handle: int):
        '''
        The CHR_video_pair_get_dest_port_num function gets the UDP destination
        port number defined for the given video pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_video_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        port : int
            A pointer to the variable where the UDP destination port number is
            returned.
        '''
        pass

    @ctypes_param(c_ulong, c_ushort)
    def CHR_video_pair_set_dest_port_num(self, pair_handle: int, port: int):
        '''
        The CHR_video_pair_set_dest_port_num function sets or changes the UDP
        destination port number defined for the given video pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_video_pair_new() or CHR_test_get_pair().
        port : int
            The UDP destination port number for the test traffic.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes))
    def CHR_video_pair_get_initial_delay(self, pair_handle: int):
        '''
        The CHR_video_pair_get_initial_delay function gets the value of the
        delay that occurs before the first video data traffic is transmitted in
        the unicast video test.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_video_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        delay : str
            A pointer to a string that will contain the initial delay in the
            same format as the one used for set.
        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_video_pair_set_initial_delay(self, pair_handle: int, delay: str):
        '''
        The CHR_video_pair_set_initial_delay function sets or changes the delay
        before the first video data traffic is transmitted in the unicast video
        test.
        By default, the initial delay is set to 0.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_video_pair_new() or CHR_test_get_pair().
        delay : str
            Specifies the initial delay distribution. Valid values are in the
            form of "d[x,y]", where:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ushort))
    def CHR_video_pair_get_source_port_num(self, pair_handle: int):
        '''
        The CHR_video_pair_get_source_port_num function gets the UDP source
        port number for the given video pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_video_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        port : int
            A pointer to the variable where the UDP source port number is
            returned.
        '''
        pass

    @ctypes_param(c_ulong, c_ushort)
    def CHR_video_pair_set_source_port_num(self, pair_handle: int, port: int):
        '''
        The CHR_video_pair_set_source_port_num function sets or changes the UDP
        source unicast port number for the given video pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_video_pair_new() or CHR_test_get_pair().
        port : int
            Sets the UDP source port number for the test traffic.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_video_pair_get_tr_duration(self, pair_handle: int):
        '''
        The CHR_video_pair_get_tr_duration function gets the timing record
        duration defined for the given video pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_video_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        seconds : int
            A pointer to the variable where the timing record duration value is
            returned.
        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_video_pair_set_tr_duration(self, pair_handle: int, seconds: int):
        '''
        The CHR_video_pair_set_tr_duration function sets or changes the timing
        record duration for the given video pair.
        This function returns CHR_VALUE_INVALID if the value set is less than
        1 or greater than 3600.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_video_pair_new() or CHR_test_get_pair().
        seconds : int
            Sets the timing record duration, in seconds. The valid range of
            values is from 1 to 3600 (inclusive).

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_video_pair_get_no_of_timing_records(self, pair_handle: int):
        '''
        The CHR_video_pair_get_no_of_timing_records function gets the number of
        timing records that were created for the given video pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_video_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        no_of_tr : int
            A pointer to the variable where the count of timing records is
            returned.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_video_pair_set_no_of_timing_records(self, pair_handle: int,
                                                no_of_tr: int):
        '''
        The CHR_video_pair_set_no_of_timing_record function allows you to set
        the number of timing records for a video pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_video_pair_new() or CHR_test_get_pair().
        no_of_tr : int
            Specifies the number of timing records that the endpoint will
            create during the execution of a test. The valid range is from 1 to
            2147483647, inclusive. The default value is 50.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_video_pair_get_frames_per_datagram(self, pair_handle: int):
        '''
        The CHR_video_pair_get_frames_per_datagram function gets the number of
        media frames per datagram defined for the given video pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_video_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        frames : int
            A pointer to the variable where the frames-per-datagram value is
            returned.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_video_pair_set_frames_per_datagram(self, pair_handle: int,
                                               frames: int):
        '''
        The CHR_video_pair_set_frames_per_datagram function sets or changes the
        number of media frames per datagram for the given video pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_video_pair_new() or CHR_test_get_pair().
        frames : int
            Sets the number of media frames that will be contained in a
            datagram. For Ethernet, there are typically seven frames per
            datagram. All integer values greater than zero are valid.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_double), ParamOut(c_char))
    def CHR_video_pair_get_bitrate(self, pair_handle: int):
        '''
        The CHR_video_pair_get_bitrate function gets the bitrate value and unit
        measurement defined for the given video pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_video_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        bitrate : float
            A pointer to the variable where the bitrate value is returned.
        rate_um : int
            A pointer to the variable where the throughput units measurement
            setting is returned.
            See CHR_video_pair_set_bitrate on page 4-570 for applicable values.
        '''
        pass

    @ctypes_param(c_ulong, c_double, c_char)
    def CHR_video_pair_set_bitrate(self, pair_handle: int, bitrate: float,
                                   rate_um: int):
        '''
        The CHR_video_pair_set_bitrate function sets the bitrate value and unit
        measurement for the given video pair.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_video_pair_new() or CHR_test_get_pair().
        bitrate : CHR_FLOAT
            The media data rate of the video stream. Typical values for MPEG2
            are between 3 and 15 megabits. The default is 3.75 megabits.
        rate_um : CHR_THROUGHPUT_UNITS
            The unit measurement setting for the media data rate. The unit
            measurement can be any of the following:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ubyte))
    def CHR_video_pair_get_rtp_payload_type(self, pair_handle: int):
        '''
        The CHR_video_pair_get_rtp_payload_type function gets the RTP payload
        type defined for the given video pair.
        This function will only be successful if codec is set to "custom" and
        protocol is set to RTP or RTP6.
        Otherwise, the function returns CHR_NO_SUCH_VALUE.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_video_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        rtp_payload_type : int
            A pointer to the variable where the RTP payload type value is
            returned. Any value from 0 to 127 is valid.
        '''
        pass

    @ctypes_param(c_ulong, c_ubyte)
    def CHR_video_pair_set_rtp_payload_type(self, pair_handle: int,
                                            rtp_payload_type: int):
        '''
        The CHR_video_pair_set_rtp_payload_type function sets or changes the
        RTP payload type for the given video pair.
        This function will only be successful if codec is set to "custom" and
        protocol is set to RTP or RTP6.
        Otherwise, the function returns CHR_ VALUE_INVALID.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_video_pair_new() or CHR_test_get_pair().
        rtp_payload_type : int
            Sets the RTP payload type. Any value from 0 to 127 is valid.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_video_pair_get_media_frame_size(self, pair_handle: int):
        '''
        The CHR_video_pair_get_media_frame_size function gets the media frame
        size used in the unicast video test.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_video_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        media_frame_size : int
            A pointer to the variable where the frame size value is returned.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_video_pair_set_media_frame_size(self, pair_handle: int,
                                            media_frame_size: int):
        '''
        The CHR_video_pair_set_media_frame_size function sets or changes the
        media frame size used in the unicast video test.

        Parameters
        ----------
        pair_handle : int
            A handle returned by CHR_video_pair_new() or CHR_test_get_pair().
        media_frame_size : int
            RETURN CODES

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  ----------------------------------------------------------------------
    #                    Video Multicast Group functions
    #                       (CHR_VIDEO_MGROUP_HANDLE)
    #  ----------------------------------------------------------------------

    @ctypes_param(ParamOut(c_ulong))
    def CHR_video_mgroup_new(self):
        '''


        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        mgroup_handle : int
            A pointer to the variable where the handle for the new video
            multicast group is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_video_mgroup_get_codec(self, mgroup_handle: int):
        '''
        The CHR_video_mgroup_get_codec function gets the codec defined for the
        given video multicast group.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_video_mgroup_new() or
            CHR_test_get_mgroup().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        codec : CHR_VIDEO_CODEC_P
            A pointer to the variable where the codec is returned. See
            CHR_video_mgroup_set_codec on page 4-550 for applicable codecs.
        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_video_mgroup_set_codec(self, mgroup_handle: int, codec: int):
        '''
        The CHR_video_mgroup_set_codec function sets or changes the codec for
        the given video multicast group.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_video_mgroup_new() or
            CHR_test_get_mgroup().
        codec : int
            Provides one of the following codecs:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes))
    def CHR_video_mgroup_get_initial_delay(self, mgroup_handle: int):
        '''
        CHR_video_mgroup_get_initial_delay

        Parameters
        ----------
        mgroup_handle : int
            DESCRIPTION.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        delay : str
            DESCRIPTION.
        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_video_mgroup_set_initial_delay(self, mgroup_handle: int,
                                           delay: str):
        '''
        CHR_video_mgroup_set_initial_delay

        Parameters
        ----------
        mgroup_handle : int
            DESCRIPTION.
        delay : str
            DESCRIPTION.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ushort))
    def CHR_video_mgroup_get_source_port_num(self, mgroup_handle: int):
        '''
        The CHR_video_mgroup_get_source_port_num function gets the UDP source
        port number for the given video multicast group.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_video_mgroup_new() or
            CHR_test_get_mgroup().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        port : int
            A pointer to the variable where the UDP source port number is
            returned.
        '''
        pass

    @ctypes_param(c_ulong, c_ushort)
    def CHR_video_mgroup_set_source_port_num(self, mgroup_handle: int,
                                             port: int):
        '''
        The CHR_video_mgroup_set_source_port_num function sets or changes the
        UDP source multicast port number for the given video multicast group.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_video_mgroup_new() or
            CHR_test_get_mgroup().
        port : int
            Sets the UDP source multicast port number for the test traffic.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_video_mgroup_get_tr_duration(self, mgroup_handle: int):
        '''
        The CHR_video_mgroup_get_tr_duration function gets the timing record
        duration defined for the given video multicast group.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_video_mgroup_new() or
            CHR_test_get_mgroup().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        seconds : int
            A pointer to the variable where the timing record duration value is
            returned.
        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_video_mgroup_set_tr_duration(self, mgroup_handle: int,
                                         seconds: int):
        '''
        The CHR_video_mgroup_set_tr_duration function sets or changes the
        timing record duration for the given video multicast group.
        This function returns CHR_VALUE_INVALID if the value set is less than
        1 or greater than 3600.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_video_mgroup_new() or
            CHR_test_get_mgroup().
        seconds : int
            Sets the timing record duration, in seconds. The valid range of
            values is from 1 to 3600 (inclusive).

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_video_mgroup_get_no_of_timing_records(self, mgroup_handle: int):
        '''
        The CHR_video_mgroup_get_no_of_timing_records function gets the number
        of timing records that were created for the given video multicast
        group.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_video_mgroup_new() or
            CHR_test_get_mgroup().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        no_of_tr : int
            A pointer to the variable where the count of timing records is
            returned.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_video_mgroup_set_no_of_timing_records(self, mgroup_handle: int,
                                                  no_of_tr: int):
        '''
        The CHR_video_mgroup_set_no_of_timing_record function allows you to set
        the number of timing records for a video multicast group.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_video_mgroup_new() or
            CHR_test_get_mgroup().
        no_of_tr : int
            Specifies the number of timing records that the endpoint will
            create during the execution of a test. The valid range is from 1 to
            2147483647, inclusive. The default value is 50.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_video_mgroup_get_frames_per_datagram(self, mgroup_handle: int):
        '''
        The CHR_video_mgroup_get_frames_per_datagram function gets the number
        of media frames per datagram defined for the given video multicast
        group.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_video_mgroup_new() or
            CHR_test_get_mgroup().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        frames : int
            A pointer to the variable where the frames-per-datagram value is
            returned.
        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_video_mgroup_set_frames_per_datagram(self, mgroup_handle: int,
                                                 frames: int):
        '''
        The CHR_video_mgroup_set_frames_per_datagram function sets or changes
        the number of media frames per datagram for the given video multicast
        group.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_video_mgroup_new() or
            CHR_test_get_mgroup().
        frames : int
            Sets the number of media frames that will be contained in a
            datagram. For Ethernet, there are typically seven frames per
            datagram. All integer values greater than zero are valid.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_double), ParamOut(c_char))
    def CHR_video_mgroup_get_bitrate(self, mgroup_handle: int):
        '''
        The CHR_video_mgroup_get_bitrate function gets the bitrate value and
        unit measurement defined for the given video multicast group.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_video_mgroup_new() or
            CHR_test_get_mgroup().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        bitrate : float
            A pointer to the variable where the bitrate value is returned.
        rate_um : CHR_THROUGHPUT_UNITS_P
            A pointer to the variable where the throughput units measurement
            setting is returned. See CHR_video_mgroup_set_bitrate on page 4-548
            for applicable values.
        '''
        pass

    @ctypes_param(c_ulong, c_double, c_char)
    def CHR_video_mgroup_set_bitrate(self, mgroup_handle: int,
                                     bitrate: float, rate_um: int):
        '''
        The CHR_video_mgroup_set_bitrate function sets the bitrate value and
        unit measurement for the given video multicast group.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_video_mgroup_new() or
            CHR_test_get_mgroup().
        bitrate : float
            The media data rate of the video stream. Typical values for MPEG2
            are between 3 and 15 megabits. The default is 3.75 megabits.
        rate_um : int
            The unit measurement setting for the media data rate. The unit
            measurement can be any of the following:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ubyte))
    def CHR_video_mgroup_get_rtp_payload_type(self, mgroup_handle: int):
        '''
        The CHR_video_mgroup_get_rtp_payload_type function gets the RTP payload
        type defined for the given video multicast group.
        This function will only be successful if codec is set to "custom" and
        protocol is set to RTP or RTP6.
        Otherwise, the function returns CHR_NO_SUCH_VALUE.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_video_mgroup_new() or
            CHR_test_get_mgroup().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        rtp_payload_type : int
            A pointer to the variable where the RTP payload type value is
            returned.
        '''
        pass

    @ctypes_param(c_ulong, c_ubyte)
    def CHR_video_mgroup_set_rtp_payload_type(self, mgroup_handle: int,
                                              rtp_payload_type: int):
        '''
        The CHR_video_mgroup_set_rtp_payload_type function sets or changes the
        RTP payload type for the given video multicast group.
        This function will only be successful if codec is set to "custom" and
        protocol is set to RTP or RTP6.
        Otherwise, the function returns CHR_ VALUE_INVALID.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_video_mgroup_new() or
            CHR_test_get_mgroup().
        rtp_payload_type : int
            Sets the RTP payload type. Any value from 0 to 127 is valid.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_video_mgroup_get_media_frame_size(self, mgroup_handle: int):
        '''
        The CHR_video_mgroup_get_media_frame_size function gets the media frame
        size used in the multicast video test.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_video_mgroup_new() or
            CHR_test_get_mgroup().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        media_frame_size : int
            A pointer to the variable where the frame size value is returned.
        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_video_mgroup_set_media_frame_size(self, mgroup_handle: int,
                                              media_frame_size: int):
        '''
        The CHR_video_mgroup_set_media_frame_size function sets or changes the
        media frame size used in the multicast video test.

        Parameters
        ----------
        mgroup_handle : int
            A handle returned by CHR_video_mgroup_new() or
            CHR_test_get_mgroup().
        media_frame_size : int
            Specifies the media frame size. For Video over IP packets, the
            Ethernet frame size is typically 1362 bytes (assuming 1316 bytes of
            MPEG2 TS payload).

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  ----------------------------------------------------------------------
    #                    Hardware Performance Pair functions
    #                        (CHR_HARDWARE_PAIR_HANDLE)
    #  ----------------------------------------------------------------------

    @ctypes_param(ParamOut(c_ulong))
    def CHR_hardware_pair_new(self):
        '''
        The CHR_hardware_pair_new function creates a hardware pair object and
        initializes it to object default values.
        Note that the object default values do not use the default values
        specified in the Chariot Options Menu.
        See Hardware Performance Pair Object Default Values on page 2-10 for
        information on the object default values.

        Parameters
        ----------

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        pair_handle : int
            A pointer to the variable where the handle for the new hardware
            pair is returned.
        '''
        pass

    @ctypes_param(c_ulong, c_double)
    def CHR_hardware_pair_set_line_rate(self, pair_handle: int,
                                        line_rate: float):
        '''
        The CHR_hardware_pair_set_line_rate function sets or changes the line
        rate percentage for the given hardware pair.

        Parameters
        ----------
        pair_handle : int
            A handled returned by CHR_hardware_pair_new () or CHR_test_get_pair
            ().
        line_rate : float
            The line rate to send traffic for this pair. Applicable values are
            greater than 0 and less than or equal 100.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_hardware_pair_get_override_line_rate(self, pair_handle: int):
        '''
        The CHR_hardware_pair_get_override_line_rate function gets the setting
        for the override line rate flag for the given hardware pair.

        Parameters
        ----------
        pair_handle : int
            A handled returned by CHR_hardware_pair_new () or CHR_test_get_pair
            ().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        override_line_rate : int
            A pointer to the variable where the override line rate condition is
            returned. See the CHR_hardware_pair_set_override_line_rate on page
            4-357 function for applicable override line rate values.
        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_hardware_pair_set_override_line_rate(self, pair_handle: int,
                                                 override_line_rate: int):
        '''
        The CHR_hardware_pair_set_override_line_rate function sets or changes
        the line rate override condition for the given hardware pair.

        Parameters
        ----------
        pair_handle : int
            A handled returned by CHR_hardware_pair_new () or CHR_test_get_pair
            ().
        override_line_rate : int
            Indicates whether to override the line rate programmed in the
            stream associated with the hardware performance pair or not.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_double))
    def CHR_hardware_pair_get_line_rate(self, pair_handle: int):
        '''
        The CHR_hardware_pair_get_line_rate function gets the line rate for the
        given hardware pair.

        Parameters
        ----------
        pair_handle : int
            A handled returned by CHR_hardware_pair_new () or CHR_test_get_pair
            ().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        line_rate : float
            A pointer to the variable where the line rate is returned. See the
            CHR_hardware_pair_set_line_rate on page 4-356 function for
            applicable line rate values.
        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_hardware_pair_set_measure_statistics(self, pair_handle: int,
                                                 measure_statistics: int):
        '''
        The CHR_Hardware_pair_set_measure_statistics function sets a flag to
        tell the hardware pair whether or not to collect background statistics.

        Parameters
        ----------
        pair_handle : int
            A handled returned by CHR_hardware_pair_new () or CHR_test_get_pair
            ().
        measure_statistics : int
            A flag to indicate whether or not to collect background statistics.
            If this value is set to CHR_TRUE then the applicable statistics
            will be collected for this hardware pair.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_hardware_pair_get_measure_statistics(self, pair_handle: int):
        '''
        The CHR_hardware_pair_get_measure_statistics function gets the flag
        that indicates whether background statistics should be  collected for
        the given hardware pair.

        Parameters
        ----------
        pair_handle : int
            A handled returned by CHR_hardware_pair_new () or CHR_test_get_pair
            ().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        measure_statistics : int
            A pointer to the variable where the collect statistics flag is
            returned. See the CHR_hardware_pair_set_measure_statistics on page
            4-358.
        '''
        pass

    #  ----------------------------------------------------------------------
    #                    VoIP Hardware Performance Pair functions
    #                          (CHR_HARDWARE_PAIR_HANDLE)
    #  ----------------------------------------------------------------------

    @ctypes_param(ParamOut(c_ulong))
    def CHR_hardware_voip_pair_new(self):
        '''
        The CHR_hardware_voip_pair_new function creates a new hardware pair
        object specialized for Voice over IP testing and initializes it to
        object default values.
        Note that the object default values do not use the default values
        specified in the Chariot Options Menu.
        See VoIP Hardware Performance Pair Object Default Values on page 2-10
        for information on the object default values.

        Parameters
        ----------

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        pair_handle : int
            A pointer to the variable where the handle for the new hardware
            pair is returned.
        '''
        pass

    @ctypes_param(c_ulong)
    def CHR_hardware_voip_pair_set_concurrent_voice_streams(self,
                                                            pair_handle: int):
        '''
        CHR_hardware_voip_pair_set_concurrent_voice_streams

        Parameters
        ----------
        pair_handle : int
            DESCRIPTION.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong)
    def CHR_hardware_voip_pair_get_concurrent_voice_streams(self,
                                                            pair_handle: int):
        '''
        CHR_hardware_voip_pair_get_concurrent_voice_streams

        Parameters
        ----------
        pair_handle : int
            DESCRIPTION.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  ----------------------------------------------------------------------
    #                    Application Group functions
    #                      (CHR_APP_GROUP_HANDLE)
    #  ----------------------------------------------------------------------

    @ctypes_param(ParamOut(c_ulong))
    def CHR_app_group_new(self):
        '''
        The CHR_app_group_new function creates an application group object and
        initializes it to object default values.
        See Application Group Object Default Values on page 2-12 for
        information on the object default values.

        Parameters
        ----------

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        app_group_handle : int
            A handle returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().
        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_app_group_set_filename(self, app_group_handle: int, filename: str):
        '''
        The CHR_app_group_set_filename function sets or changes the name of the
        file to which the given test is saved.

        Parameters
        ----------
        app_group_handle : int
            A handle returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().
        filename : str
            A string containing the filename. The filename may be specified
            using a relative or an absolute pathname. Note that once you've set
            the filename, you cannot change it back to the loaded filename. To
            reset the filename to the name of the loaded test, use a null
            filename parameter and a "0" filename length.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_FILE_PATH))
    def CHR_app_group_get_filename(self, app_group_handle: int):
        '''
        The CHR_app_group_get_filename function gets the name of the file from
        which this application group was loaded or to which it will be saved.

        Parameters
        ----------
        app_group_handle : int
            A handle returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        buffer : str
            A pointer to the buffer where the filename is returned. The
            returned filename includes any specified path information.
        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_app_group_copy(self,
                           to_app_group_handle: int,
                           from_app_group_handle: int):
        '''
        The CHR_app_group_copy function copies the attributes of the source
        application group to the destination application group.
        This does not include any results information.

        Parameters
        ----------
        to_app_group_handle : int
            A handle for the destination object, returned by
            CHR_app_group_new(), CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().
        from_app_group_handle : int
            A handle for the source object, returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong)
    def CHR_app_group_delete(self, app_group_handle: int):
        '''
        The CHR_app_group_delete function frees all memory associated with the
        given application group.

        Parameters
        ----------
        app_group_handle : int
            A handle returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong)
    def CHR_app_group_save(self, app_group_handle: int):
        '''
        The CHR_app_group_save function saves the given application group to
        the currently defined filename.

        Parameters
        ----------
        app_group_handle : int
            A handle returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong)
    def CHR_app_group_force_delete(self, app_group_handle: int):
        '''
        The CHR_app_group_force_delete function frees all memory associated
        with the given application group.

        Parameters
        ----------
        app_group_handle : int
            A handle returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_app_group_set_name(self, app_group_handle: int, name: str):
        '''
        The CHR_app_group_set_name function sets or changes the name of the
        given application group.

        Parameters
        ----------
        app_group_handle : int
            A handle returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().
        name : str
            A string containing the name for the application group.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_GROUP_NAME))
    def CHR_app_group_get_name(self, app_group_handle: int):
        '''
        The CHR_app_group_get_name function gets the name of the given
        application group.

        Parameters
        ----------
        app_group_handle : int
            A handle returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        name : str
            The length of the buffer.
        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_app_group_set_comment(self, app_group_handle: int, comment: str):
        '''
        The CHR_app_group_set_comment function sets or changes the comment for
        the given application group.

        Parameters
        ----------
        app_group_handle : int
            A handle returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().
        comment : CHR_STRING
            The string containing the new comment.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_APP_GROUP_COMMENT))
    def CHR_app_group_get_comment(self, app_group_handle: int):
        '''
        The CHR_app_group_get_comment function gets the comment for the given
        application group.

        Parameters
        ----------
        app_group_handle : int
            A handle returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        comment : str
            A pointer to the buffer where the comment is returned.
        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_app_group_add_pair(self, app_group_handle: int, pair_handle: int):
        '''
        The CHR_app_group_add_pair function adds an endpoint pair to the
        designated application group.

        Parameters
        ----------
        app_group_handle : int
            A handle for the target application group object, returned by
            CHR_app_group_new(), CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong)
    def CHR_app_group_remove_pair(self, app_group_handle: int,
                                  pair_handle: int):
        '''
        The CHR_app_group_remove_pair function removes an endpoint pair from
        the designated application group.

        Parameters
        ----------
        app_group_handle : int
            A handle for the target application group object, returned by
            CHR_app_group_new(), CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().
        pair_handle : int
            A handle returned by CHR_pair_new() or CHR_test_get_pair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_app_group_get_pair_count(self, app_group_handle: int):
        '''
        The CHR_app_group_get_pair_count function gets the number of endpoint
        pairs owned by the given application group.

        Parameters
        ----------
        app_group_handle : int
            A handle returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        pair_count : int
            A pointer to the variable where the number of pairs is returned.
        '''
        pass

    @ctypes_param(c_ulong, c_ulong, ParamOut(c_ulong))
    def CHR_app_group_get_pair(self, app_group_handle: int, index: int):
        '''
        The CHR_app_group_get_pair function gets the handle of a specified pair
        from the designated application group.

        Parameters
        ----------
        app_group_handle : int
            A handle returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().
        index : int
            A zero-based index that can take values between 0 and
            CHR_app_group_get_pair_count()  1. The index  identifies a
            specific pair within the application group. For example, if there
            are four pairs in an application group, their index numbers are 0,
            1, 2, and 3.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        pair_handle : int
            A pointer to the variable where the pair handle is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes), ParamIn(bytes))
    def CHR_app_group_add_event(self, app_group_handle: int, event_name: str,
                                event_comment: str):
        '''
        The CHR_app_group_add_event function adds an event to the designated
        application group.
        Events are objects defined within application groups and passed as
        parameters to the WAIT_EVENT and SIGNAL_EVENT script commands.
        An event is simply a unique name (a character string) defined within
        an application group.
        An event does not specify any actions.
        Rather, it acts as a token to trigger the scripts to pause or resume
        execution at specific points in the scripts.

        Parameters
        ----------
        app_group_handle : int
            A handle for the target application group object, returned by
            CHR_app_group_new(), CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().
        event_name : CHR_STRING
            A name for the event. Note that:
        event_comment : CHR_STRING
            An optional comment for this event.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_app_group_remove_event(self,
                                   app_group_handle: int,
                                   event_name: str):
        '''
        The CHR_app_group_remove_event function removes an event from the
        designated application group.

        Parameters
        ----------
        app_group_handle : int
            A handle for the target application group object, returned by
            CHR_app_group_new(), CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().
        event_name : str
            The name of the event to remove.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_app_group_get_event_count(self, app_group_handle: int):
        '''
        The CHR_app_group_get_event_count function gets the number of events
        defined in the given application group.

        Parameters
        ----------
        app_group_handle : int
            A handle returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        event_count : int
            A pointer to the variable where the number of events is returned.
        '''
        pass

    @ctypes_param(c_ulong, c_ulong,
                  ParamOut(bytes, CHR_MAX_APP_GROUP_EVENT_NAME),
                  ParamOut(bytes, CHR_MAX_APP_GROUP_EVENT_COMMENT))
    def CHR_app_group_get_event(self, app_group_handle: int, index: int):
        '''
        The CHR_app_group_get_event function gets information about a specific
        event defined in the given application group.

        Parameters
        ----------
        app_group_handle : int
            A handle returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().
        index : int
            A zero-based index that can take values between 0 and
            CHR_app_group_get_event_count()  1. The index identifies a
            specific (and unique) event within the application group. For
            example, if there are four events defined in an application group,
            their index numbers are 0, 1, 2, and 3.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        event_name : str
            The name of the buffer to which the event name is returned.
        event_comment : str
            The name of the buffer to which the event comment is returned.
        '''
        pass

    @ctypes_param(c_ulong, c_ulong, c_char)
    def CHR_app_group_set_pair_protocol(self, app_group_handle: int,
                                        pair_index: int, protocol: int):
        '''
        The CHR_app_group_set_pair_protocol function sets or changes the
        Endpoint 1 to Endpoint 2 network protocol for the given endpoint in the
        application group.

        Parameters
        ----------
        app_group_handle : int
            A handle returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().
        pair_index : int
            A handle returned by CHR_app_group_get_pair_count(). The index
            identifies the specific pair within the application group.
        protocol : int
            Specifies the protocol type: CHR_PROTOCOL_UDP, CHR_PROTOCOL_RTP,
            CHR_PROTCOL_TCP, CHR_PROTOCOL_IPX, or CHR_PROTOCOL_SPX.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong, ParamOut(c_char))
    def CHR_app_group_get_pair_protocol(self, app_group_handle: int,
                                        pair_index: int):
        '''
        The CHR_app_group_get_pair_protocol function gets the Endpoint 1 to
        Endpoint 2 network protocol for the given endpoint pair within the
        application group.

        Parameters
        ----------
        app_group_handle : int
            A handle returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().
        pair_index : int
            An address index returned by CHR_app_group_get_pair_count(). The
            index identifies the specific pair within the application group.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        protocol : int
            A pointer to the variable where the protocol is returned. See the
            CHR_pair_set_protocol on page 4-337 function for applicable
            protocols.
        '''
        pass

    @ctypes_param(c_ulong, c_ulong, c_char)
    def CHR_app_group_set_pair_management_protocol(self,
                                                   app_group_handle: int,
                                                   pair_index: int,
                                                   protocol: int):
        '''
        The CHR_app_group_set_pair_management_protocol function sets or changes
        the management protocol for the given pair within the application
        group.

        Parameters
        ----------
        app_group_handle : int
            A handle returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().
        pair_index : int
            A handle returned by CHR_app_group_get_pair_count(). The index
            identifies the specific pair within the application group.
        protocol : int
            Specifies the protocol type: CHR_PROTOCOL_UDP, CHR_PROTOCOL_RTP,
            CHR_PROTCOL_TCP, CHR_PROTOCOL_IPX, or CHR_PROTOCOL_SPX.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong, ParamOut(c_char))
    def CHR_app_group_get_pair_management_protocol(self,
                                                   app_group_handle: int,
                                                   pair_index: int):
        '''
        The CHR_app_group_get_pair_management_protocol function gets the
        Endpoint 1 to Endpoint 2 management protocol for the given pair within
        the application group.

        Parameters
        ----------
        app_group_handle : int
            A handle returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().
        pair_index : int
            An address index returned by CHR_app_group_get_pair_count(). The
            index identifies the specific pair within the application group.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        protocol : int
            A pointer to the variable where the protocol is returned. See the
            CHR_pair_set_protocol on page 4-337 function for applicable
            protocols.
        '''
        pass

    @ctypes_param(c_ulong, c_ulong, ParamIn(bytes))
    def CHR_app_group_set_pair_qos_name(self,
                                        app_group_handle: int,
                                        pair_index: int,
                                        qos_name: str):
        '''
        The CHR_app_group_set_pair_qos_name function sets or changes the
        service quality name for the given endpoint pair within the application
        group.

        Parameters
        ----------
        app_group_handle : int
            A handle returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().
        pair_index : int
            A handle returned by CHR_app_group_get_pair_count(). The index
            identifies the specific pair within the application group.
        qos_name : str
            A string containing quality of service name.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong, ParamOut(bytes, CHR_MAX_QOS_NAME))
    def CHR_app_group_get_pair_qos_name(self,
                                        app_group_handle: int,
                                        pair_index: int):
        '''
        The CHR_app_group_get_pair_qos_name function gets the service quality
        name for the given endpoint pair.

        Parameters
        ----------
        app_group_handle : int
            A handle returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().
        pair_index : int
            An address index returned by CHR_app_group_get_pair_count(). The
            index identifies the specific pair within the application group.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        qos_name : str
            A pointer to the buffer where the service quality name is returned.
        max_length : CHR_LENGTH
            The length of the provided buffer.
        length : CHR_LENGTH_P
            A pointer to the variable where the number of bytes in the buffer
            is returned, excluding the null terminator--like strlen().
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_app_group_get_address_count(self,
                                        app_group_handle: int):
        '''
        The CHR_app_group_get_address_count function gets the number of unique
        network addresses used in the given application group.

        Parameters
        ----------
        app_group_handle : int
            A handle returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        address_count : int
            A pointer to the variable where the number of application group
            pairs is returned.
        '''
        pass

    @ctypes_param(c_ulong, c_ulong, ParamIn(bytes))
    def CHR_app_group_set_address(self,
                                  app_group_handle: int,
                                  address_index: int,
                                  address: str):
        '''
        The CHR_app_group_set_address function sets or changes a network
        address within the application group.

        Parameters
        ----------
        app_group_handle : int
            A handle returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().
        address_index : int
            An address index returned by CHR_app_group_get_address_count(). The
            index identifies a specific (and unique) network address within the
            application group.
        address : str
            A string containing the address for Endpoint 1 (IPv4 or IPv6).

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong, ParamOut(bytes, CHR_MAX_ADDR))
    def CHR_app_group_get_address(self,
                                  app_group_handle: int,
                                  address_index: int):
        '''
        The CHR_app_group_get_address function returns the IP address of the
        given pair within the application group.

        Parameters
        ----------
        app_group_handle : int
            A handle returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().
        address_index : int
            An address index returned by CHR_app_group_get_address_count(). The
            index identifies a specific (and unique) network address within the
            application group.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        address : str
            A pointer to the buffer where the management address is returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_app_group_get_management_address_count(self,
                                                   app_group_handle: int):
        '''
        The CHR_app_group_get_management_address_count function gets the number
        of unique management addresses owned by the given application group.
        If the management address is not user-defined (that is,
        USE_CONSOLE_E1_ADDR and USE_SETUP_E1_E2_ADDR are false), the address is
        not counted.

        Parameters
        ----------
        app_group_handle : int
            A handle returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        address_count : int
            A pointer to the variable where the number of management addresses
            is returned.
        '''
        pass

    @ctypes_param(c_ulong, c_ulong, ParamIn(bytes))
    def CHR_app_group_set_management_address(self,
                                             app_group_handle: int,
                                             address_index: int,
                                             address: str):
        '''
        The CHR_app_group_set_management_address function sets or changes a
        management address in the application group.

        Parameters
        ----------
        app_group_handle : int
            A handle returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().
        address_index : int
            A handle returned by CHR_app_group_get_management_address_count().
            The index identifies a specific (and unique) management address
            within the application group.
        address : str
            A string containing the management address (IPv4 or IPv6).

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_ulong, ParamOut(bytes, CHR_MAX_ADDR))
    def CHR_app_group_get_management_address(self,
                                             app_group_handle: int,
                                             address_index: int):
        '''
        The CHR_app_group_get_management_address function gets the management
        address for the given endpoint pair in the application group.

        Parameters
        ----------
        app_group_handle : int
            A handle returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().
        address_index : int
            An address index returned by
            CHR_app_group_get_management_address_count(). The index identifies
            a specific (and unique) management address within the application
            group.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        address : str
            A pointer to the buffer where the management address is returned.
        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_app_group_set_lock(self, app_group_handle: int, lock: int):
        '''
        The CHR_app_group_set_lock  function takes one of the following
        actions:

        Parameters
        ----------
        app_group_handle : int
            A handle returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().
        lock : int
            A CHR_BOOLEAN, where CHR_TRUE locks the (unlocked) application
            group object, and CHR_FALSE unlocks the (locked) object.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_app_group_get_lock(self, app_group_handle: int):
        '''
        The function CHR_app_group_get_lock returns a Boolean value that
        indicates whether the application group is locked (CHR_TRUE) or
        unlocked (CHR_FALSE).
        An application group object that is contained by a test object must be
        locked before any of its attributes (such as its endpoint address) can
        be set.

        Parameters
        ----------
        app_group_handle : int
            A handle returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        lock : int
            A pointer to the variable where the Boolean "lock" value is
            returned.
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_app_group_is_disabled(self, app_group_handle: int):
        '''
        The CHR_app_group_is_disabled function determines whether or not the
        pairs in the specified application group are disabled.

        Parameters
        ----------
        app_group_handle : int
            A handle returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        disabled : int
            A pointer to the variable where the Boolean value is returned. The
            returned values can be:

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_app_group_disable(self, app_group_handle: int, disable: int):
        '''
        The CHR_app_group_disable function disables or enables all of the pairs
        assigned to the specified application group.
        IxChariot ignores any disabled pairs when running a test.

        Parameters
        ----------
        app_group_handle : int
            A handle returned by CHR_app_group_new(),
            CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().
        disable : int
            Specifies the action to perform:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong)
    def CHR_app_group_validate(self, app_group_handle: int):
        '''
        The CHR_app_group_validate function verifies the validity of the
        designated application group.

        Parameters
        ----------
        app_group_handle : int
            A handle for the target application group object, returned by
            CHR_app_group_new(), CHR_test_get_app_group_by_name(), or
            CHR_test_get_app_group_by_index().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  ----------------------------------------------------------------------
    #                    IPTV Channel Object functions
    #                        (CHR_CHANNEL_HANDLE)
    #  ----------------------------------------------------------------------

    #  Deletes the specified IPTV channel object.
    #
    #  @param i_channelHandle   Channel Object handle.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_HANDLE_INVALID
    #  - CHR_OBJECT_IN_USE
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong)
    def CHR_channel_delete(self, i_channel_handle: int):
        '''
        The CHR_channel_delete function deletes the specified IPTV channel
        object.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Gets the bit rate value and unit of measurement defined for the given
    #  channel.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param o_bitrate         Transmission bit rate.
    #  @param o_units           Unit of measurement in which the
    #                           transmission rate is expressed.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_HANDLE_INVALID
    #  - CHR_POINTER_INVALID
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(c_double), ParamOut(c_char))
    def CHR_channel_get_bitrate(self, i_channel_handle: int):
        '''
        The CHR_channel_get_bitrate function gets the bit rate value and unit
        of measurement defined for the given IPTV channel object.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_bitrate : float
            A pointer to the variable where the transmission bit rate value is
            returned.
        o_units : CHR_THROUGHPUT_UNITS_P
            A pointer to the variable where the unit of measurement is
            returned.
            (This is the unit of measurement in which the transmission rate is
             expressed.)
        '''
        pass

    #  Returns the codec type defined for the specified IPTV channel.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param o_videoCodec      Video codec type (MPEG2 or CUSTOM).
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_HANDLE_INVALID
    #  - CHR_POINTER_INVALID
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_channel_get_codec(self, i_channel_handle: int):
        '''
        The CHR_channel_get_codec function returns the codec type defined for
        the specified IPTV channel object.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_video_codec : CHR_VIDEO_CODEC_P
            A pointer to the variable where the video codec type (MPEG2 or
            CUSTOM) is returned.
        '''
        pass

    #  Returns the comment string for the specified channel object.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param o_comment         Character buffer to receive the comment.
    #  @param i_maxLength       Size of the return buffer.
    #  @param o_length          Actual number of bytes returned.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_BUFFER_TOO_SMALL
    #  - CHR_HANDLE_INVALID
    #  - CHR_POINTER_INVALID
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_CHANNEL_COMMENT))
    def CHR_channel_get_comment(self, i_channel_handle: int):
        '''
        The CHR_channel_get_comment function returns the comment string for the
        specified IPTV channel object.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_comment : str
            Character buffer to receive the comment. The symbol
            CHR_MAX_CHANNEL_COMMENT may be used to define a character buffer
            large enough to hold the largest comment string supported.
        '''
        pass

    #  Returns the send buffer size to be specified in the CONNECT.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param o_bufferSize      Send buffer size.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_HANDLE_INVALID
    #  - CHR_POINTER_INVALID
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_channel_get_conn_send_buff_size(self, i_channel_handle: int):
        '''
        The CHR_channel_get_conn_send_buff_size function returns the size of
        the socket connection buffer that this channel uses for send
        operations.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_buffer_size : int
            The buffer size that this channel connection uses for send
            operations.
        '''
        pass

    #  Returns the IP address of Endpoint 1 on the management network.
    #  This is the address the console will use to perform pair setup.
    #
    #  This parameter will only be used if the use_e1_e2_values attribute is
    #  false.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param o_mgmtAddr        Character buffer to receive the address.
    #  @param i_maxLength       Size of the IP address buffer.
    #  @param o_length          Actual number of bytes returned.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_BUFFER_TOO_SMALL
    #  - CHR_HANDLE_INVALID
    #  - CHR_POINTER_INVALID
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_ADDR))
    def CHR_channel_get_console_e1_addr(self, i_channel_handle: int):
        '''
        The CHR_channel_get_console_e1_addr function returns the IP address of
        Endpoint 1 on the management network.
        This is the address the console will use to perform IPTV pair setup.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_mgmt_addr : str
            Character buffer to receive the address.
        '''
        pass

    #  Returns the network protocol the console will use when connecting to
    #  Endpoint 1 to perform pair setup.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param o_protocol        Management network protocol.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_HANDLE_INVALID
    #  - CHR_POINTER_INVALID
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_channel_get_console_e1_protocol(self, i_channel_handle: int):
        '''
        The CHR_channel_get_console_e1_protocol function returns the network
        protocol that the console will use when connecting to Endpoint 1 to
        perform IPTV pair setup.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_protocol : int
            A pointer to the variable where the protocol designation
            (CHR_PROTOCOL_TCP or CHR_PROTOCOL_TCP6) is returned.
        '''
        pass

    #  Returns the IP address of Endpoint 1 on the test network.
    #  The channel will use this as the source IP address of the multicast.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param o_address         Buffer to receive IP address.
    #  @param i_maxLength       Size of the return buffer.
    #  @param o_length          Actual number of bytes returned.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_BUFFER_TOO_SMALL
    #  - CHR_HANDLE_INVALID
    #  - CHR_POINTER_INVALID
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_ADDR))
    def CHR_channel_get_e1_addr(self, i_channel_handle: int):
        '''
        The CHR_channel_get_e1_addr function returns the IP address of
        Endpoint 1 on the test network.
        The channel will use this as the source IP address of the multicast.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_address : str
            Character buffer to receive the IP address.
        '''
        pass

    #  Returns the number of media frames per datagram defined for the
    #  specified IPTV channel.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param o_frames          Number of media frames per datagram.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_HANDLE_INVALID
    #  - CHR_POINTER_INVALID
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_channel_get_frames_per_datagram(self, i_channel_handle: int):
        '''
        The CHR_channel_get_frames_per_datagram function returns the number of
        media frames per datagram defined for the specified IPTV channel.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_frames : int
            A pointer to the variable where the number of media frames per
            datagram is returned.
        '''
        pass

    #  Gets the media frame size defined for the given IPTV channel.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param o_frameSize       The media frame size.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_HANDLE_INVALID
    #  - CHR_POINTER_INVALID
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_channel_get_media_frame_size(self, i_channel_handle: int):
        '''
        The CHR_channel_get_media_frame_size function returns the media frame
        size defined for the given IPTV channel.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_frame_size : int
            A pointer to the variable where the media frame size value is
            returned.
        '''
        pass

    #  Returns the multicast IP address of the IPTV channel.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param o_multicastAddr   Buffer to receive the multicast address.
    #  @param i_maxLength       Size of the result buffer.
    #  @param o_length          Number of bytes stored in result buffer.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_BUFFER_TOO_SMALL
    #  - CHR_HANDLE_INVALID
    #  - CHR_POINTER_INVALID
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_MULTICAST_ADDR))
    def CHR_channel_get_multicast_addr(self, i_channel_handle: int):
        '''
        The CHR_channel_get_multicast_addr function returns the multicast IP
        address of the given IPTV channel.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_multicast_addr : str
            Character buffer to receive the multicast IP address.
        '''
        pass

    #  Returns the multicast port number of the IPTV channel.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param o_multicastPort   Multicast port number.
    #
    #  - CHR_OK
    #  - CHR_HANDLE_INVALID
    #  - CHR_POINTER_INVALID
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(c_ushort))
    def CHR_channel_get_multicast_port(self, i_channel_handle: int):
        '''
        The CHR_channel_get_multicast_port function returns the multicast port
        number of the given IPTV channel.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_multicast_port : int
            A pointer to the variable where the multicast port number is
            returned.
        '''
        pass

    #  Returns the name assigned to the specified IPTV channel.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param o_name            Buffer to receive the channel name.
    #  @param i_maxLength       Size of the result buffer.
    #  @param o_length          Number of bytes stored in result buffer.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_BUFFER_TOO_SMALL
    #  - CHR_HANDLE_INVALID
    #  - CHR_POINTER_INVALID
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_CHANNEL_NAME))
    def CHR_channel_get_name(self, i_channel_handle: int):
        '''
        The CHR_channel_get_name function returns the name assigned to the
        specified IPTV channel.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_name : str
            Character buffer to receive the channel name.
        '''
        pass

    #  Returns the test protocol of the IPTV channel.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param o_protocol        Protocol type.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_HANDLE_INVALID
    #  - CHR_POINTER_INVALID
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_channel_get_protocol(self, i_channel_handle: int):
        '''
        The CHR_channel_get_protocol function returns the test protocol of the
        specified IPTV channel.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_protocol : int
            A pointer to the variable where the test protocol designation is
            returned. Refer to Typedefs and Enumerations on page 4-612 for the
            list of valid CHR_PROTOCOL values.
        '''
        pass

    #  Returns the quality-of-service template name for the channel.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param o_qosName         Buffer to receive the qos name.
    #  @param i_maxLength       Size of the result buffer.
    #  @param o_length          Number of bytes stored in result buffer.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_BUFFER_TOO_SMALL
    #  - CHR_HANDLE_INVALID
    #  - CHR_POINTER_INVALID
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_QOS_NAME))
    def CHR_channel_get_qos_name(self, i_channel_handle: int):
        '''
        The CHR_channel_get_qos_name function returns the quality-of-service
        template name for the specified IPTV channel.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_qos_name : CHR_STRING
            Character buffer to receive the QoS template name.
        '''
        pass

    #  Returns the RTP payload type defined for the given IPTV channel. This
    #  function will only be successful if the code type is set to CUSTOM
    #  and the protocol is set to RTP or RTP6. Otherwise, the function
    #  returns CHR_NO_SUCH_VALUE.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param o_payloadType     RTP payload type.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_HANDLE_INVALID
    #  - CHR_POINTER_INVALID
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong)
    def CHR_channel_get_rtp_payload_type(self, i_channel_handle: int):
        '''
        The CHR_channel_get_rtp_payload_type function returns the RTP payload
        type defined for the given IPTV channel.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_payload_type : int
            A pointer to the variable where the RTP payload type designation is
            returned.
        '''
        pass

    #  Gets the UDP source port number for the specified IPTV channel.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param o_sourcePort      UDP source port number.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_HANDLE_INVALID
    #  - CHR_POINTER_INVALID
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(c_ushort))
    def CHR_channel_get_source_port_num(self, i_channel_handle: int):
        '''
        The CHR_channel_get_source_port_num function returns the UDP source
        port number for the specified IPTV channel.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_source_port : int
            A pointer to the variable where the UDP source port number is
            returned.
        '''
        pass

    #  Indicates whether the console will use the management network or the
    #  test network to perform pair setup.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param o_useValues       CHR_TRUE if the console will use
    #                           the management network; CHR_FALSE if it
    #                           will use the test network.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_HANDLE_INVALID
    #  - CHR_POINTER_INVALID
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_channel_get_use_console_e1_values(self, i_channel_handle: int):
        '''
        The CHR_channel_get_use_console_e1_values function indicates whether
        the console will use the management network or the test network to
        perform pair setup.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_use_values : int
            A pointer to the variable where the Boolean value is returned. The
            values are:
        '''
        pass

    #  Creates a new IPTV channel object and initializes it to the default
    #  values.
    #
    #  The handle returned by this function is needed for other function
    #  calls to operate on the channel object.
    #
    #  @param o_channelHandle   Channel Object handle.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_LICENSE_HAS_EXPIRED
    #  - CHR_NO_MEMORY
    #  - CHR_NOT_LICENSED
    #  - CHR_POINTER_INVALID
    #
    #  @since IxChariot 6.50
    @ctypes_param(ParamOut(c_ulong))
    def CHR_channel_new(self):
        '''
        The CHR_channel_new function creates a new IPTV channel object and
        initializes it to the default values.

        Parameters
        ----------

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_channel_handle : int
            A handle to the new channel object.
        '''
        pass

    #  Specifies the bit rate value and unit of measurement for the given
    #  IPTV channel.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param i_bitrate         Transmission rate of channel.
    #  @param i_units           Units in which transmission rate is
    #                           specified.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_HANDLE_INVALID
    #  - CHR_NOT_SUPPORTED
    #  - CHR_OBJECT_IN_USE
    #  - CHR_PGM_INTERNAL_ERROR
    #  - CHR_RESULTS_NOT_CLEARED
    #  - CHR_TEST_RUNNING
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, c_double, c_char)
    def CHR_channel_set_bitrate(self, i_channel_handle: int,
                                i_bitrate: float,
                                i_units: int):
        '''
        The CHR_channel_set_bitrate function specifies the bit rate value and
        unit of measurement defined for the given IPTV channel object.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().
        i_bitrate : float
            The transmission bit rate for the given IPTV channel object.
        i_units : int
            The unit of measurement in which transmission rate is specified.
            Refer to Typedefs and Enumerations on page 4-612 for the list of
            valid CHR_THROUGHPUT_UNITS values.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Specifies the type of codec for the IPTV channel object.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param i_videoCodec      Codec type.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_HANDLE_INVALID
    #  - CHR_NOT_SUPPORTED
    #  - CHR_OBJECT_IN_USE
    #  - CHR_RESULTS_NOT_CLEARED
    #  - CHR_TEST_RUNNING
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, c_char)
    def CHR_channel_set_codec(self, i_channel_handle: int, i_video_codec: int):
        '''
        The CHR_channel_set_codec function specifies the type of codec for the
        IPTV channel object.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().
        i_video_codec : CHR_VIDEO_CODEC
            The video codec type that the IPTV channel object will use. Refer
            to Typedefs and Enumerations on page 4-612 for the list of valid
            CHR_VIDEO_CODEC values.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Specifies the comment string for the channel object.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param i_comment         Comment string to be assigned to channel.
    #  @param i_length          Length of comment string.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_HANDLE_INVALID
    #  - CHR_NOT_SUPPORTED
    #  - CHR_OBJECT_IN_USE
    #  - CHR_POINTER_INVALID
    #  - CHR_RESULTS_NOT_CLEARED
    #  - CHR_TEST_RUNNING
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_channel_set_comment(self, i_channel_handle: int, i_comment: str):
        '''
        The CHR_channel_set_comment function specifies the comment string for
        the given IPTV channel object.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().
        i_comment : CHR_CONST_STRING
            Comment string to be assigned to the IPTV channel object.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Specifies the send buffer size to be specified in the CONNECT.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param i_bufferSize      Send buffer size.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_HANDLE_INVALID
    #  - CHR_NOT_SUPPORTED
    #  - CHR_OBJECT_IN_USE
    #  - CHR_RESULTS_NOT_CLEARED
    #  - CHR_TEST_RUNNING
    @ctypes_param(c_ulong, c_ulong)
    def CHR_channel_set_conn_send_buff_size(self, i_channel_handle: int,
                                            i_buffer_size: int):
        '''
        The CHR_channel_set_conn_send_buff_size function specifies the  desired
        size of the socket connection buffer that this channel should use for
        sending IPTV data streams.
        Note that the maximum value is determined by the operating system on
        which the Performance Endpoint is running

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().
        i_buffer_size : int
            The desired buffer size that this channel should use for send
            operations. You can specify a buffer size in the 0  2,147,483,646
            bytes range or as CHR_SOCKET_BUFFER_DEFAULT.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Specifies the IP address on the management network that the console
    #  uses to connect to Endpoint 1 during test setup.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param i_mgmtAddr        Management address of Endpoint 1.
    #  @param i_length          Length of management address.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_HANDLE_INVALID
    #  - CHR_NOT_SUPPORTED
    #  - CHR_OBJECT_IN_USE
    #  - CHR_POINTER_INVALID
    #  - CHR_RESULTS_NOT_CLEARED
    #  - CHR_TEST_RUNNING
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_channel_set_console_e1_addr(self, i_channel_handle: int,
                                        i_mgmt_addr: str):
        '''
        The CHR_channel_set_console_e1_addr function specifies the IP address
        on the management network that the console uses to connect to
        Endpoint 1 during test setup.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().
        i_mgmt_addr : CHR_CONST_STRING
            Management address of Endpoint 1.
        i_length : CHR_LENGTH
            Length of the management address.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Specifies the network protocol the console will use when connecting
    #  to Endpoint 1 to perform pair setup.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param i_protocol        Management network protocol.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_HANDLE_INVALID
    #  - CHR_NOT_SUPPORTED
    #  - CHR_OBJECT_IN_USE
    #  - CHR_RESULTS_NOT_CLEARED
    #  - CHR_TEST_RUNNING
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, c_char)
    def CHR_channel_set_console_e1_protocol(self, i_channel_handle: int,
                                            i_protocol: int):
        '''
        The CHR_channel_set_console_e1_protocol function specifies the network
        protocol the console will use when connecting to Endpoint 1 to perform
        pair setup.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().
        i_protocol : int
            The management network protocol. Refer to Typedefs and Enumerations
            on page 4-612 for the list of valid CHR_PROTOCOL values.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Specifies the IP address of Endpoint 1 on the test network. Will be
    #  used as the source IP address for the multicast.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param i_address         Source IP address of channel.
    #  @param i_length          Length of IP address.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_HANDLE_INVALID
    #  - CHR_NOT_SUPPORTED
    #  - CHR_OBJECT_IN_USE
    #  - CHR_POINTER_INVALID
    #  - CHR_RESULTS_NOT_CLEARED
    #  - CHR_TEST_RUNNING
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_channel_set_e1_addr(self, i_channel_handle: int, i_address: str):
        '''
        The CHR_channel_set_e1_addr function specifies the IP address of
        Endpoint 1 on the test network.
        The channel will use this as the source IP address for the multicast.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().
        i_address : str
            Source IP address of channel.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Specifies the number of media frames per datagram for the channel.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param i_frames          Media frames per datagram.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_HANDLE_INVALID
    #  - CHR_NOT_SUPPORTED
    #  - CHR_OBJECT_IN_USE
    #  - CHR_RESULTS_NOT_CLEARED
    #  - CHR_TEST_RUNNING
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, c_ulong)
    def CHR_channel_set_frames_per_datagram(self, i_channel_handle: int,
                                            i_frames: int):
        '''
        The CHR_channel_set_frames_per_datagram function specifies the number
        of media frames per datagram for the specified IPTV channel.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().
        i_frames : int
            The number of media frames per datagram.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Specifies the media frame size used for the channel.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param i_frameSize       Media frame size.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_HANDLE_INVALID
    #  - CHR_NOT_SUPPORTED
    #  - CHR_OBJECT_IN_USE
    #  - CHR_RESULTS_NOT_CLEARED
    #  - CHR_TEST_RUNNING
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, c_ulong)
    def CHR_channel_set_media_frame_size(self, i_channel_handle: int,
                                         i_frame_size: int):
        '''
        The CHR_channel_set_media_frame_size function specifies the media frame
        size used for the IPTV channel.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().
        i_frame_size : int
            The media frame size to use for the IPTV channel.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Specifies the multicast IP address on which traffic will be
    #  transmitted.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param i_multicastAddr   Multicast address.
    #  @param i_length          Length of multicast address.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_HANDLE_INVALID
    #  - CHR_NOT_SUPPORTED
    #  - CHR_OBJECT_IN_USE
    #  - CHR_POINTER_INVALID
    #  - CHR_RESULTS_NOT_CLEARED
    #  - CHR_TEST_RUNNING
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_channel_set_multicast_addr(self, i_channel_handle: int,
                                       i_multicast_addr: str):
        '''
        The CHR_channel_set_multicast_addr function specifies the multicast IP
        address on which traffic will be transmitted for the given IPTV
        channel.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().
        i_multicast_addr : CHR_CONST_STRING
            The multicast IP address on which traffic will be transmitted.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Specifies the source port number on which multicast traffic will be
    #  transmitted.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param i_multicastPort   Multicast port number.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_HANDLE_INVALID
    #  - CHR_NOT_SUPPORTED
    #  - CHR_OBJECT_IN_USE
    #  - CHR_RESULTS_NOT_CLEARED
    #  - CHR_TEST_RUNNING
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, c_ushort)
    def CHR_channel_set_multicast_port(self, i_channel_handle: int,
                                       i_multicast_port: int):
        '''
        The CHR_channel_set_multicast_port function specifies the source port
        number on which multicast traffic will be transmitted.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().
        i_multicast_port : int
            The source port number on which multicast traffic will be
            transmitted.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Specifies the name of the channel.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param i_name            Name to be assigned to channel object.
    #  @param i_length          Length of channel name.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_HANDLE_INVALID
    #  - CHR_NOT_SUPPORTED
    #  - CHR_OBJECT_IN_USE
    #  - CHR_POINTER_INVALID
    #  - CHR_RESULTS_NOT_CLEARED
    #  - CHR_TEST_RUNNING
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_channel_set_name(self, i_channel_handle: int, i_name: str):
        '''
        The CHR_channel_set_name function specifies a name of the IPTV channel.
        The name is a characters string, such as "BBC".

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().
        i_name : CHR_CONST_STRING
            The name to be assigned to IPTV channel object.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Specifies the test protocol of the IPTV channel.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param i_protocol        Protocol type.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_HANDLE_INVALID
    #  - CHR_NOT_SUPPORTED
    #  - CHR_OBJECT_IN_USE
    #  - CHR_RESULTS_NOT_CLEARED
    #  - CHR_TEST_RUNNING
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, c_char)
    def CHR_channel_set_protocol(self, i_channel_handle: int, i_protocol: int):
        '''
        The CHR_channel_set_protocol function specifies the test protocol of
        the IPTV channel.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().
        i_protocol : int
            The test protocol of the IPTV channel. Refer to Typedefs and
            Enumerations on page 4-612 for the list of valid CHR_PROTOCOL
            values.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Specifies the quality-of-service template for the channel.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param i_qosName         QoS template name.
    #  @param i_length          Length of QoS template name.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_HANDLE_INVALID
    #  - CHR_NOT_SUPPORTED
    #  - CHR_OBJECT_IN_USE
    #  - CHR_POINTER_INVALID
    #  - CHR_RESULTS_NOT_CLEARED
    #  - CHR_TEST_RUNNING
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_channel_set_qos_name(self, i_channel_handle: int, i_qos_name: str):
        '''
        The CHR_channel_set_qos_name function specifies the quality-of-service
        template name for the IPTV channel.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().
        i_qos_name : CHR_CONST_STRING
            The QoS template name.
        i_length : CHR_LENGTH
            The length of the QoS template name.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Specifies the RTP payload type for the given channel. This function
    #  will only succeed if the codec type is set to CUSTOM and the protocol
    #  is set to RTP or RTP6. Otherwise, the function returns
    #  CHR_VALUE_INVALID.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param i_payloadType     RTP payload type.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_HANDLE_INVALID
    #  - CHR_NOT_SUPPORTED
    #  - CHR_OBJECT_IN_USE
    #  - CHR_RESULTS_NOT_CLEARED
    #  - CHR_TEST_RUNNING
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, c_ubyte)
    def CHR_channel_set_rtp_payload_type(self, i_channel_handle: int,
                                         i_payload_type: int):
        '''
        The CHR_channel_set_rtp_payload_type function specifies the RTP payload
        type for the given IPTV channel.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().
        i_payload_type : CHR_BYTE
            The RTP payload type.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Specifies the UDP source port for the IPTV channel.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param i_sourcePort      UDP source port number.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_HANDLE_INVALID
    #  - CHR_NOT_SUPPORTED
    #  - CHR_OBJECT_IN_USE
    #  - CHR_RESULTS_NOT_CLEARED
    #  - CHR_TEST_RUNNING
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, c_ushort)
    def CHR_channel_set_source_port_num(self, i_channel_handle: int,
                                        i_source_port: int):
        '''
        The CHR_channel_set_source_port_num function specifies the UDP source
        port number for the IPTV channel.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().
        i_source_port : int
            The UDP source port number.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Specifies whether to use the management network (true) or the
    #  test network (false) for pair setup.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param i_useValues       CHR_TRUE to use the management network;
    #                           CHR_FALSE to use the test network.
    #
    #  @return Chariot API return code.
    #  - CHR_OK
    #  - CHR_HANDLE_INVALID
    #  - CHR_NOT_SUPPORTED
    #  - CHR_OBJECT_IN_USE
    #  - CHR_RESULTS_NOT_CLEARED
    #  - CHR_TEST_RUNNING
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, c_char)
    def CHR_channel_set_use_console_e1_values(self, i_channel_handle: int,
                                              i_use_values: int):
        '''
        The CHR_channel_set_use_console_e1_values function specifies whether
        the console will use the management network or the test network to
        perform IPTV pair setup.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().
        i_use_values : int
            Specifies whether the console will use the test network or the
            management network to perform IPTV pair setup:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Specifies whether the channel object is locked.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param o_useValues       CHR_TRUE for locked; CHR_FALSE for
    #                           unlocked.
    #
    #  @since IxChariot 6.70
    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_channel_get_lock(self, i_channel_handle: int):
        '''
        The CHR_channel_get_lock function returns a Boolean value that
        specifies whether or not the channel object is locked.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_use_values : int
            A pointer to the variable where the Boolean value is returned. The
            returned values are:
        '''
        pass

    #  Specifies whether to lock or not the channel object. Locking
    #  allows editing a channel owned by a test.
    #
    #  @param i_channelHandle   Channel Object handle.
    #  @param i_useValues       CHR_TRUE to lock; CHR_FALSE to
    #                           unlock.
    #
    #  @since IxChariot 6.70
    @ctypes_param(c_ulong, c_char)
    def CHR_channel_set_lock(self, i_channel_handle: int, i_use_values: int):
        '''
        The CHR_channel_set_lock function locks or unlocks the channel object.
        Locking allows a channel that is owned by a test to be edited.

        Parameters
        ----------
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().
        i_use_values : int
            Indicates the action to take on the channel object:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  ----------------------------------------------------------------------
    #                    IPTV Receiver Object functions
    #                        (CHR_RECEIVER_HANDLE)
    #  ----------------------------------------------------------------------

    #  Adds an IPTV pair to the list for this receiver.
    #
    #  @param i_receiverHandle  Handle of receiver object.
    #  @param i_pairHandle      IPTV pair to be added to receiver.
    #
    #  @return Chariot API return code.
    @ctypes_param(c_ulong, c_ulong)
    def CHR_receiver_add_vpair(self, i_receiver_handle: int,
                               i_pair_handle: int):
        '''
        The CHR_receiver_add_vpair function adds an IPTV pair to the list for
        the designated receiver.

        Parameters
        ----------
        i_receiver_handle : int
            A receiver object handle returned by CHR_receiver_new(),
            CHR_test_get_receiver(), or CHR_test_get_receiver_by_name().
        i_pair_handle : int
            The handle of the IPTV pair to be added to the receiver list. The
            vpair object handle is returned by CHR_vpair_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Removes an IPTV pair from the list for this receiver.
    #
    #  @param i_receiverHandle  Handle of receiver object.
    #  @param i_pairHandle      IPTV pair to be removed.
    #
    #  @return Chariot API return code.
    @ctypes_param(c_ulong, c_ulong)
    def CHR_receiver_remove_vpair(self, i_receiver_handle: int,
                                  i_pair_handle: int):
        '''
        The CHR_receiver_remove_vpair function removes an IPTV pair from the
        list for this receiver.

        Parameters
        ----------
        i_receiver_handle : int
            A receiver object handle returned by CHR_receiver_new(),
            CHR_test_get_receiver(), or CHR_test_get_receiver_by_name().
        i_pair_handle : int
            An IPTV pair object handle returned by CHR_vpair_new() or
            CHR_receiver_get_vpair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Deletes the specified IPTV receiver object.
    #
    #  @param i_receiverHandle  Handle of receiver object to be deleted.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong)
    def CHR_receiver_delete(self, i_receiver_handle: int):
        '''
        The CHR_receiver_delete function deletes the specified IPTV receiver
        object.

        Parameters
        ----------
        i_receiver_handle : int
            A receiver object handle returned by CHR_receiver_new(),
            CHR_test_get_receiver(), or CHR_test_get_receiver_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Returns the comment string for the specified receiver object.
    #
    #  @param i_receiverHandle  Handle of receiver object.
    #  @param o_comment         Buffer to receive the comment string.
    #  @param i_maxLength       Size of the return buffer.
    #  @param o_length          Actual number of bytes returned.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_RECEIVER_COMMENT))
    def CHR_receiver_get_comment(self, i_receiver_handle: int):
        '''
        The CHR_receiver_get_comment function returns the comment string for
        the specified IPTV receiver object.

        Parameters
        ----------
        i_receiver_handle : int
            A receiver object handle returned by CHR_receiver_new(),
            CHR_test_get_receiver(), or CHR_test_get_receiver_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_comment : str
            Character buffer to receive the comment.
        '''
        pass

    #  Returns the receive buffer size to be specified in the CONNECT.
    #
    #  @param i_receiverHandle  Handle of receiver object.
    #  @param o_bufferSize      Receiver buffer size.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_receiver_get_conn_recv_buff_size(self, i_receiver_handle: int):
        '''
        The CHR_receiver_get_conn_recv_buff_size function returns the size of
        the socket connection buffer that this receiver uses for receiving IPTV
        data streams.

        Parameters
        ----------
        i_receiver_handle : int
            A receiver object handle returned by CHR_receiver_new(),
            CHR_test_get_receiver(), or CHR_test_get_receiver_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_buffer_size : int
            The buffer size that this receiver uses for receiving IPTV data
            streams.
        '''
        pass

    #  Returns the IP address of the receiver on the test network.
    #
    #  @param i_receiverHandle  Handle of receiver object.
    #  @param o_address         Buffer to receive the IP address.
    #  @param i_maxLength       Size of the return buffer.
    #  @param o_length          Actual number of bytes returned.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_ADDR))
    def CHR_receiver_get_e2_addr(self, i_receiver_handle: int):
        '''
        The CHR_receiver_get_e2_addr function returns the IP address of an
        Endpoint 2 receiver on the test network.

        Parameters
        ----------
        i_receiver_handle : int
            A receiver object handle returned by CHR_receiver_new(),
            CHR_test_get_receiver(), or CHR_test_get_receiver_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_address : str
            Character buffer to receive the IP address.
        '''
        pass

    #  Returns the name assigned to the receiver object.
    #
    #  @param i_receiverHandle  Handle of receiver object.
    #  @param o_name            Buffer to receive the receiver name.
    #  @param i_maxLength       Size of the return buffer.
    #  @param o_length          Actual number of bytes returned.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_RECEIVER_NAME))
    def CHR_receiver_get_name(self, i_receiver_handle: int):
        '''
        The CHR_receiver_get_name function returns the name assigned to the
        specified IPTV receiver.

        Parameters
        ----------
        i_receiver_handle : int
            A receiver object handle returned by CHR_receiver_new(),
            CHR_test_get_receiver(), or CHR_test_get_receiver_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_name : str
            Character buffer to receive the receiver name.
        '''
        pass

    #  Returns the number of times the JOIN/LEAVE loop will be repeated.
    #
    #  @param i_receiverHandle  Handle of receiver object.
    #  @param o_iterations      JOIN/LEAVE repeat count.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_receiver_get_no_of_iterations(self, i_receiver_handle: int):
        '''
        The CHR_receiver_get_no_of_iterations function returns the number of
        times the JOIN/LEAVE loop will be repeated in the test.

        Parameters
        ----------
        i_receiver_handle : int
            A receiver object handle returned by CHR_receiver_new(),
            CHR_test_get_receiver(), or CHR_test_get_receiver_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_iterations : int
            A pointer to the variable where the JOIN/LEAVE repeat count is
            returned.
        '''
        pass

    #  Returns the specified IPTV pair object from the list of pairs
    #  assigned to this receiver.
    #
    #  @param i_receiverHandle  Handle of receiver object.
    #  @param i_pairIndex       Index of the desired entry in the pair list,
    #                           in the range 0..pair_count-1.
    #  @param o_pairHandle      Handle of the IPTV pair object.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, c_ulong, ParamOut(c_ulong))
    def CHR_receiver_get_vpair(self, i_receiver_handle: int,
                               i_pair_index: int):
        '''
        The CHR_receiver_get_vpair function returns the IPTV pair object with
        the specified index from the list of pairs assigned to this receiver.

        Parameters
        ----------
        i_receiver_handle : int
            A receiver object handle returned by CHR_receiver_new(),
            CHR_test_get_receiver(), or CHR_test_get_receiver_by_name().
        i_pair_index : int
            Zero-based index of the desired entry in the pair list. Must be
            less than the value returned by CHR_receiver_get_pair_count().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_pair_handle : int
            A pointer to the variable where the handle of the IPTV pair object
            is returned. Refer to IPTV Pair Object Functions on page 4-178 for
            a description of the IPTV pair object APIs.
        '''
        pass

    #  Returns the number of pairs that have been assigned to this receiver.
    #
    #  @param i_receiverHandle  Handle of receiver object.
    #  @param o_pairCount       Number of entries in the pair list.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_receiver_get_vpair_count(self, i_receiver_handle: int):
        '''
        The CHR_receiver_get_vpair_count function returns the number of pairs
        that have been assigned to this receiver.

        Parameters
        ----------
        i_receiver_handle : int
            A receiver object handle returned by CHR_receiver_new(),
            CHR_test_get_receiver(), or CHR_test_get_receiver_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_pair_count : int
            A pointer to the variable where the number of entries in the pair
            list is returned.
        '''
        pass

    #  Returns the management IP address of the receiver.
    #
    #  @param i_receiverHandle  Handle of receiver object.
    #  @param o_address         Buffer to receive the IP address.
    #  @param i_maxLength       Size of the return buffer.
    #  @param o_length          Actual number of bytes returned.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(bytes, CHR_MAX_ADDR))
    def CHR_receiver_get_setup_e1_e2_addr(self, i_receiver_handle: int):
        '''
        The CHR_receiver_get_setup_e1_e2_addr function returns the management
        IP address of the receiver.

        Parameters
        ----------
        i_receiver_handle : int
            A receiver object handle returned by CHR_receiver_new(),
            CHR_test_get_receiver(), or CHR_test_get_receiver_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_address : str
            Character buffer to receive the IP address.
        '''
        pass

    #  Returns the channel switch delay (the interval between a LEAVE and
    #  the next JOIN).
    #
    #  @param i_receiverHandle  Handle of receiver object.
    #  @param o_switchDelay     Channel switch delay, in milliseconds.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_receiver_get_switch_delay(self, i_receiver_handle: int):
        '''
        The CHR_receiver_get_switch_delay function returns the channel switch
        delay (measured as the interval between a LEAVE and the next JOIN).

        Parameters
        ----------
        i_receiver_handle : int
            A receiver object handle returned by CHR_receiver_new(),
            CHR_test_get_receiver(), or CHR_test_get_receiver_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_switch_delay : int
            A pointer to the variable where the switch delay value is returned.
        '''
        pass

    #  Indicates whether IxChariot will use the management network or the
    #  test network when setting up the test.
    #
    #  @param i_receiverHandle  Handle of receiver object.
    #  @param o_useValues       CHR_TRUE if IxChariot will use the
    #                           management network; CHR_FALSE if it will
    #                           perform pair setup over the test
    #                           network.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_receiver_get_use_e1_e2_values(self, i_receiver_handle: int):
        '''
        The CHR_receiver_get_use_e1_e2_values function indicates whether
        IxChariot will use the management network or the test network when
        setting up the test.

        Parameters
        ----------
        i_receiver_handle : int
            A receiver object handle returned by CHR_receiver_new(),
            CHR_test_get_receiver(), or CHR_test_get_receiver_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_use_values : int
            A pointer to the variable where the Boolean value is returned. The
            values are:
        '''
        pass

    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_receiver_is_disabled(self, i_receiver_handle: int):
        '''
        The CHR_receiver_is_disabled function determines whether or not the
        pairs in the specified IPTV receiver group are disabled.

        Parameters
        ----------
        i_receiver_handle : int
            A receiver object handle returned by CHR_receiver_new(),
            CHR_test_get_receiver(), or CHR_test_get_receiver_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_disabled : int
            A pointer to the variable where the Boolean value is returned. The
            returned values can be:
        '''
        pass

    #  Creates a new IPTV receiver object and initializes it to the default
    #  values.
    #
    #  The handle returned by this function is needed for other function
    #  calls to operate on the receiver object.
    #
    #  @param o_receiverHandle  Handle of receiver object.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(ParamOut(c_ulong))
    def CHR_receiver_new(self):
        '''
        The CHR_receiver_new function creates a new IPTV receiver object and
        initializes it to the default values.

        Parameters
        ----------

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_receiver_handle : int
            A handle to the new receiver object.
        '''
        pass

    #  Specifies the comment string for the receiver object.
    #
    #  @param i_receiverHandle  Handle of receiver object.
    #  @param i_comment         Comment string to be assigned to receiver.
    #  @param i_length          Length of comment string.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_receiver_set_comment(self, i_receiver_handle: int, i_comment: str):
        '''
        The CHR_receiver_set_comment function specifies a comment string for
        the specified IPTV receiver object.

        Parameters
        ----------
        i_receiver_handle : int
            A receiver object handle returned by CHR_receiver_new(),
            CHR_test_get_receiver(), or CHR_test_get_receiver_by_name().
        i_comment : CHR_CONST_STRING
            The comment string to be assigned to the receiver.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Specifies the receive buffer size to be used in the CONNECT.
    #
    #  @param i_receiverHandle  Handle of receiver object.
    #  @param i_bufferSize      Receiver buffer size.
    #
    #  @return Chaript API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, c_ulong)
    def CHR_receiver_set_conn_recv_buff_size(self, i_receiver_handle: int,
                                             i_buffer_size: int):
        '''
        The CHR_receiver_set_conn_recv_buff_size function specifies the desired
        size of the socket connection buffer that this receiver should use for
        receiving IPTV data streams.
        Note that the maximum value is determined by the operating system on
        which the Performance Endpoint is running.

        Parameters
        ----------
        i_receiver_handle : int
            A receiver object handle returned by CHR_receiver_new(),
            CHR_test_get_receiver(), or CHR_test_get_receiver_by_name().
        i_buffer_size : int
            The desired buffer size that this receiver should use for receiving
            IPTV data streams. You can specify a buffer size in the 0 
            2147483646 bytes range or as CHR_SOCKET_BUFFER_DEFAULT.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Specifies the IP address of the receiver on the test network.
    #
    #  @param i_receiverHandle  Handle of receiver object.
    #  @param i_address         IP address to be assigned to receiver.
    #  @param i_length          Length of IP address.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_receiver_set_e2_addr(self, i_receiver_handle: int, i_address: str):
        '''
        The CHR_receiver_set_e2_addr function specifies the IP address of an
        Endpoint 2 receiver on the test network.

        Parameters
        ----------
        i_receiver_handle : int
            A receiver object handle returned by CHR_receiver_new(),
            CHR_test_get_receiver(), or CHR_test_get_receiver_by_name().
        i_address : CHR_CONST_STRING
            IP address to be assigned to the receiver.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Specifies the name of the receiver object.
    #
    #  @param i_receiverHandle  Handle of receiver object.
    #  @param i_name            Name to be assigned to receiver.
    #  @param i_length          Length of name string.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_receiver_set_name(self, i_receiver_handle: int, i_name: str):
        '''
        The CHR_receiver_set_name function specifies the name of the IPTV
        receiver object.

        Parameters
        ----------
        i_receiver_handle : int
            A receiver object handle returned by CHR_receiver_new(),
            CHR_test_get_receiver(), or CHR_test_get_receiver_by_name().
        i_name : CHR_CONST_STRING
            The name to assign to the receiver object.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Specifies the number of times the JOIN/LEAVE loop is to be repeated.
    #
    #  @param i_receiverHandle  Handle of receiver object.
    #  @param i_iterations      Number of JOINs/LEAVEs to perform.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, c_ulong)
    def CHR_receiver_set_no_of_iterations(self, i_receiver_handle: int,
                                          i_iterations: int):
        '''
        The CHR_receiver_set_no_of_iterations function specifies the number of
        times the JOIN/LEAVE loop is to be repeated in the test.

        Parameters
        ----------
        i_receiver_handle : int
            A receiver object handle returned by CHR_receiver_new(),
            CHR_test_get_receiver(), or CHR_test_get_receiver_by_name().
        i_iterations : int
            The number of times the JOIN/LEAVE loop is to be repeated.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Specifies the IP address of the receiver on the management network.
    #
    #  @param i_receiverHandle  Handle of receiver object.
    #  @param i_address         Management IP address.
    #  @param i_length          Length of management IP address.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamIn(bytes))
    def CHR_receiver_set_setup_e1_e2_addr(self, i_receiver_handle: int,
                                          i_address: str):
        '''
        The CHR_receiver_set_setup_e1_e2_addr function specifies the IP address
        of the receiver on the management network.

        Parameters
        ----------
        i_receiver_handle : int
            A receiver object handle returned by CHR_receiver_new(),
            CHR_test_get_receiver(), or CHR_test_get_receiver_by_name().
        i_address : CHR_CONST_STRING
            The management IP address.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Specifies the channel switch delay (the interval between a LEAVE and
    #  the next JOIN).
    #
    #  @param i_receiverHandle  Handle of receiver object.
    #  @param i_switchDelay     Channel switch delay, in milliseconds.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, c_ulong)
    def CHR_receiver_set_switch_delay(self, i_receiver_handle: int,
                                      i_switch_delay: int):
        '''
        The CHR_receiver_set_switch_delay function specifies the channel switch
        delay (the interval between a LEAVE and the next JOIN).

        Parameters
        ----------
        i_receiver_handle : int
            A receiver object handle returned by CHR_receiver_new(),
            CHR_test_get_receiver(), or CHR_test_get_receiver_by_name().
        i_switch_delay : int
            The channel switch delay, in milliseconds.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Specifies whether IxChariot should use the management network
    #  (true) or the test network (false) for pair setup.
    #
    #  @param i_receiverHandle  Handle of receiver object.
    #  @param i_useValues       CHR_TRUE to use the management network;
    #                           CHR_FALSE to use the test network.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, c_char)
    def CHR_receiver_set_use_e1_e2_values(self, i_receiver_handle: int,
                                          i_use_values: int):
        '''
        The CHR_receiver_set_use_e1_e2_values function specifies whether
        IxChariot will use the management network or the test network when
        setting up the test.

        Parameters
        ----------
        i_receiver_handle : int
            A receiver object handle returned by CHR_receiver_new(),
            CHR_test_get_receiver(), or CHR_test_get_receiver_by_name().
        i_use_values : int
            Specifies whether the receiver will use the test network or the
            management network when setting up the test:
            CHR_TRUE: IxChariot will perform pair setup over the management
            network.
            CHR_FALSE: IxChariot will perform pair setup over the test network.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    @ctypes_param(c_ulong, c_char)
    def CHR_receiver_disable(self, i_receiver_handle: int, i_disable: int):
        '''
        The CHR_receiver_disable function disables or enables all of the pairs
        assigned to the specified IPTV receiver.
        IxChariot ignores any disabled pairs when running a test.

        Parameters
        ----------
        i_receiver_handle : int
            A receiver object handle returned by CHR_receiver_new(),
            CHR_test_get_receiver(), or CHR_test_get_receiver_by_name().
        i_disable : int
            Specifies the action to perform:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  ----------------------------------------------------------------------
    #                        Report Object functions
    #                          (CHR_REPORT_HANDLE)
    #  ----------------------------------------------------------------------

    #  Returns the type of the specified report item.
    #
    #  @param i_reportHandle    Report handle.
    #  @param o_reportItem      Report item type.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_report_get_item_type(self, i_report_handle: int):
        '''
        The CHR_report_get_item_type function returns the type of the specified
        report item.

        Parameters
        ----------
        i_report_handle : int
            A handle returned by CHR_vpair_get_report().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_report_item : CHR_REPORT_ITEM_P
            DESCRIPTION.
        '''
        pass

    #  Returns the join latency field from the specified report.
    #
    #  @param i_reportHandle    Report handle.
    #  @param o_joinLatency     Join latency, in milliseconds.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(c_double))
    def CHR_report_get_join_latency(self, i_report_handle: int):
        '''
        The CHR_report_get_join_latency function returns the join latency field
        from the specified report.

        Parameters
        ----------
        i_report_handle : int
            A handle returned by CHR_vpair_get_report().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_join_latency : float
            A pointer to the variable to which the function returns the join
            latency value, in milliseconds.
        '''
        pass

    #  Returns the leave latency field from the specified report.
    #
    #  @param i_reportHandle    Report handle.
    #  @param o_leaveLatency    Leave latency, in milliseconds.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(c_double))
    def CHR_report_get_leave_latency(self, i_report_handle: int):
        '''
        The CHR_report_get_item_type function returns the leave latency field
        from the specified report.

        Parameters
        ----------
        i_report_handle : int
            A handle returned by CHR_vpair_get_report().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_leave_latency : float
            A pointer to the variable to which the function returns the leave
            latency value, in milliseconds.
        '''
        pass

    #  Returns the report group identifier from the specified report.
    #
    #  @param i_reportHandle    Report handle.
    #  @param o_reportGroupId   Report group identifier.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_report_get_report_group_id(self, i_report_handle: int):
        '''
        The CHR_report_get_report_group_id function returns the report group
        identifier from the specified report.
        The group identifier helps associate timing records with reports.

        Parameters
        ----------
        i_report_handle : int
            A handle returned by CHR_vpair_get_report().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_report_group_id : int
            A pointer to the variable to which the function returns the report
            group identifier.
        '''
        pass

    #  Specifies whether the receiver object is locked.
    #
    #  @param i_receiverHandle  Receiver Object handle.
    #  @param o_useValues       CHR_TRUE for locked; CHR_FALSE for
    #                           unlocked.
    #
    #  @since IxChariot 6.70
    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_receiver_get_lock(self, i_receiver_handle: int):
        '''
        The CHR_receiver_get_lock function returns a Boolean value that
        specifies whether or not the receiver object is locked.

        Parameters
        ----------
        i_receiver_handle : int
            A receiver object handle returned by CHR_receiver_new(),
            CHR_test_get_receiver(), or CHR_test_get_receiver_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_use_values : int
            A pointer to the variable where the Boolean value is returned.
            The returned values are:
            CHR_TRUE: The receiver object is locked.
            CHR_FALSE: The receiver object is unlocked.
        '''
        pass

    #  Specifies whether to lock or not the receiver object. Locking
    #  allows editing a receiver owned by a test.
    #
    #  @param i_receiverHandle  Receiver Object handle.
    #  @param i_useValues       CHR_TRUE to lock; CHR_FALSE to
    #                           unlock.
    #
    #  @since IxChariot 6.70
    @ctypes_param(c_ulong, c_char)
    def CHR_receiver_set_lock(self, i_receiver_handle: int, i_use_values: int):
        '''
        The CHR_receiver_set_lock function locks or unlocks the receiver
        object.
        Locking allows a receiver that is owned by a test to be edited.

        Parameters
        ----------
        i_receiver_handle : int
            A receiver object handle returned by CHR_receiver_new(),
            CHR_test_get_receiver(), or CHR_test_get_receiver_by_name().
        i_use_values : int
            Indicates the action to take on the receiver object:

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  ----------------------------------------------------------------------
    #                    IPTV Test Object functions
    #                        (int)
    #  ----------------------------------------------------------------------

    #  Adds a channel object to the test.
    #
    #  @param i_testHandle      Test Object handle.
    #  @param i_channelHandle   Handle of the Channel Object to be added to
    #                           the configuration.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, c_ulong)
    def CHR_test_add_channel(self, i_test_handle: int,
                             i_channel_handle: int):
        '''
        The CHR_test_add_channel function adds an IPTV channel object to the
        specified test.

        Parameters
        ----------
        i_test_handle : int
            A handle returned by CHR_test_new().
        i_channel_handle : int
            A handle returned by CHR_channel_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Removes a channel object from the test.
    #
    #  @param i_testHandle      Test Object handle.
    #  @param i_channelHandle   Handle of the Channel Object to be
    #                           removed.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.70
    @ctypes_param(c_ulong, c_ulong)
    def CHR_test_remove_channel(self, i_test_handle: int,
                                i_channel_handle: int):
        '''
        The CHR_test_remove_channel function removes a channel object from the
        specified test.

        Parameters
        ----------
        i_test_handle : int
            A handle returned by CHR_test_new().
        i_channel_handle : int
            A channel object handle returned by CHR_channel_new(),
            CHR_vpair_get_channel(), CHR_test_get_channel(), or
            CHR_test_get_channel_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Adds a receiver object to the test.
    #
    #  @param i_testHandle      Test Object handle.
    #  @param i_receiverHandle  Handle of the Receiver object to be added to
    #                           the configuration.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, c_ulong)
    def CHR_test_add_receiver(self, i_test_handle: int,
                              i_receiver_handle: int):
        '''
        The CHR_test_add_receiver function adds an IPTV receiver object to the
        specified test.

        Parameters
        ----------
        i_test_handle : int
            A handle returned by CHR_test_new().
        i_receiver_handle : int
            A handle returned by CHR_receiver_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Removes a receiver object from the test.
    #
    #  @param i_testHandle      Test Object handle.
    #  @param i_receiverHandle  Handle of the Receiver object to be
    #                           removed
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.70
    @ctypes_param(c_ulong, c_ulong)
    def CHR_test_remove_receiver(self, i_test_handle: int,
                                 i_receiver_handle: int):
        '''
        The CHR_test_remove_receiver function removes a receiver object from
        the specified test.

        Parameters
        ----------
        i_test_handle : int
            A handle returned by CHR_test_new().
        i_receiver_handle : int
            A receiver object handle returned by CHR_receiver_new(),
            CHR_test_get_receiver(), or CHR_test_get_receiver_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Gets the specified channel object from the test.
    #
    #  @param i_testHandle      Test Object handle.
    #  @param i_listIndex       Index of the item in the list of channel
    #                           objects, in the range 0..channel_count-1.
    #  @param o_channelHandle   Handle of the requested channel object.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, c_ulong, ParamOut(c_ulong))
    def CHR_test_get_channel(self, i_test_handle: int, i_list_index: int):
        '''
        The CHR_test_get_channel function gets the specified IPTV channel
        object from the test.
        The handle returned by this function is needed for other function
        calls to operate on this object.

        Parameters
        ----------
        i_test_handle : int
            A handle returned by CHR_test_new().
        i_list_index : int
            Index of the item in the list of channel objects, in the following
            range: 0..channel_count-1.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_channel_handle : int
            A pointer to the variable where the handle of the requested channel
            object is returned.
        '''
        pass

    #  Returns the channel object with the specified name.
    #
    #  @param i_testHandle      Test Object handle.
    #  @param i_channelName     String specifying the name of the channel.
    #  @param i_nameLength      Length of the channel name string.
    #  @param o_channelHandle   Handle of the requested channel object.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamIn(bytes), ParamOut(c_ulong))
    def CHR_test_get_channel_by_name(self, i_test_handle: int,
                                     i_channel_name: str):
        '''
        The CHR_test_get_channel_by_name function gets the IPTV channel object
        with the specified name from the test.
        The handle returned by this function is needed for other function
        calls to operate on this object.

        Parameters
        ----------
        i_test_handle : int
            A handle returned by CHR_test_new().
        i_channel_name : CHR_CONST_STRING
            String specifying the name of the channel.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_channel_handle : int
            A pointer to the variable where the handle of the requested channel
            object is returned.
        '''
        pass

    #  Returns the number of channel objects in the test.
    #
    #  @param i_testHandle      Test Object handle.
    #  @param o_channelCount    The channel object count.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_test_get_channel_count(self, i_test_handle: int):
        '''
        The CHR_test_get_channel_count function returns a count of the IPTV
        channel objects in the specified test.

        Parameters
        ----------
        i_test_handle : int
            A handle returned by CHR_test_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_channel_count : int
            A pointer to the variable where the count of the channel objects is
            returned.
        '''
        pass

    #  Gets the specified receiver object from the test.
    #
    #  @param i_testHandle      Test Object handle.
    #  @param i_listIndex       Index of the object in the receive list, in
    #                           the range 0..receiver_count-1.
    #  @param o_receiverHandle  Handle of the requested receiver object.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, c_ulong, ParamOut(c_ulong))
    def CHR_test_get_receiver(self, i_test_handle: int, i_list_index: int):
        '''
        The CHR_test_get_receiver function returns the specified IPTV receiver
        from the specified test.

        Parameters
        ----------
        i_test_handle : int
            A handle returned by CHR_test_new().
        i_list_index : int
            Index of the item in the list of receiver objects, in the following
            range: 0..receiver_count-1.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_receiver_handle : int
            A pointer to the variable where the handle of the requested
            receiver object is returned.
        '''
        pass

    #  Returns the receiver object with the specified name.
    #
    #  @param i_testHandle      Test Object handle.
    #  @param i_receiverName    String specifying the name of the receiver.
    #  @param i_nameLength      Length of the receiver name string.
    #  @param o_receiverHandle  Handle of the requested receiver object.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamIn(bytes), ParamOut(c_ulong))
    def CHR_test_get_receiver_by_name(self,
                                      i_test_handle: int,
                                      i_receiver_name: str):
        '''
        The CHR_test_get_receiver_by_name function returns the IPTV receiver
        object with the specified name from the specified test.

        Parameters
        ----------
        i_test_handle : int
            A handle returned by CHR_test_new().
        i_receiver_name : str
            String specifying the name of the receiver.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_receiver_handle : int
            A pointer to the variable where the handle of the requested
            receiver object is returned.
        '''
        pass

    #  Returns the number of receiver objects in the test.
    #
    #  @param i_testHandle      Test Object handle.
    #  @param o_receiverCount   The receiver object count.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_test_get_receiver_count(self, i_test_handle: int):
        '''
        The CHR_test_get_receiver_count function returns a count of the IPTV
        receiver objects in the specified test.

        Parameters
        ----------
        i_test_handle : int
            A handle returned by CHR_test_new().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_receiver_count : int
            A pointer to the variable where the count of the receiver objects
            is returned.
        '''
        pass

    #  ----------------------------------------------------------------------
    #                    IPTV Pair object functions
    #                        (int)
    #  ----------------------------------------------------------------------

    #  Deletes the specified IPTV pair object.
    #
    #  @param i_pairHandle      Pair handle.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong)
    def CHR_vpair_delete(self, i_pair_handle: int):
        '''
        The CHR_vpair_delete function deletes the specified IPTV pair object.

        Parameters
        ----------
        i_pair_handle : int
            An IPTV pair object handle returned by CHR_vpair_new() or
            CHR_receiver_get_vpair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Returns the channel with which this pair is associated.
    #
    #  @param i_pairHandle      Pair handle.
    #  @param o_channelHandle   Channel handle.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_vpair_get_channel(self, i_pair_handle: int):
        '''
        The CHR_vpair_get_channel function returns the IPTV channel with which
        this IPTV pair is associated.

        Parameters
        ----------
        i_pair_handle : int
            An IPTV pair object handle returned by CHR_vpair_new() or
            CHR_receiver_get_vpair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_channel_handle : int
            A pointer to the variable to which the function returns the IPTV
            channel handle.
        '''
        pass

    #  Returns the number of timing records the pair should generate.
    #
    #  @param i_pairHandle      Pair handle.
    #  @param o_count           Number of timing records.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_vpair_get_no_of_timing_records(self, i_pair_handle: int):
        '''
        The CHR_vpair_get_no_of_timing_records function returns the number of
        timing records that the pair has been configured to create during the
        execution of a test.

        Parameters
        ----------
        i_pair_handle : int
            An IPTV pair object handle returned by CHR_vpair_new() or
            CHR_receiver_get_vpair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_count : int
            A pointer to the variable to which the function returns the number
            of timing records that the IPTV pair has been configured to
            generate.
        '''
        pass

    #  Returns the specified report for this pair.
    #
    #  @param i_pairHandle      Pair handle.
    #  @param i_reportIndex     Index of the requested report (zero-based).
    #  @param o_reportHandle    Report handle.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, c_ulong, ParamOut(c_ulong))
    def CHR_vpair_get_report(self, i_pair_handle: int, i_report_index: int):
        '''
        The CHR_vpair_get_report function returns the specified report for this
        IPTV pair.

        Parameters
        ----------
        i_pair_handle : int
            An IPTV pair object handle returned by CHR_vpair_new() or
            CHR_receiver_get_vpair().
        i_report_index : int
            Zero-based index of the requested report. Must be less than the
            value returned by CHR_vpair_get_report_count().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_report_handle : int
            A pointer to the variable where the handle of the requested report
            is returned. Refer to Report Object Functions on page 4-377 for a
            description of the report object APIs.
        '''
        pass

    #  Returns the number of reports collected for this pair.
    #
    #  @param i_pairHandle      Pair handle.
    #  @param o_reportCount     Number of reports collected.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_vpair_get_report_count(self, i_pair_handle: int):
        '''
        The CHR_vpair_get_report_count function returns the number of reports
        collected for this IPTV pair.

        Parameters
        ----------
        i_pair_handle : int
            An IPTV pair object handle returned by CHR_vpair_new() or
            CHR_receiver_get_vpair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_report_count : int
            A pointer to the variable where the report count is returned.
        '''
        pass

    #  Returns the specified timing record for this pair.
    #
    #  @param i_pairHandle      Pair handle.
    #  @param i_recordIndex     Index of the requested timing record.
    #  @param o_recordHandle    Timing record handle.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, c_ulong, ParamOut(c_ulong))
    def CHR_vpair_get_timing_record(self, i_pair_handle: int,
                                    i_record_index: int):
        '''
        The CHR_vpair_get_timing_record function returns the specified timing
        record for this IPTV pair.

        Parameters
        ----------
        i_pair_handle : int
            An IPTV pair object handle returned by CHR_vpair_new() or
            CHR_receiver_get_vpair().
        i_record_index : int
            Zero-based index of the requested timing record. Must be less than
            the value returned by CHR_vpair_get_timing_record_count().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_record_handle : int
            A pointer to the variable where the timing record handle is
            returned. Refer to Timing Record Object Functions on page 4-500 for
            a description of the timing record object APIs.
        '''
        pass

    #  Returns the number of timing records collected for this pair.
    #
    #  @param i_pairHandle      Pair handle.
    #  @param o_recordCount     Number of timing records collected.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_vpair_get_timing_record_count(self, i_pair_handle: int):
        '''
        The CHR_vpair_get_timing_record_count function returns the number of
        timing records collected for this IPTV pair.

        Parameters
        ----------
        i_pair_handle : int
            An IPTV pair object handle returned by CHR_vpair_new() or
            CHR_receiver_get_vpair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_record_count : int
            A pointer to the variable where the timing record count is
            returned.
        '''
        pass

    #  Returns the timing record duration, in seconds.
    #
    #  @param i_pairHandle      Pair handle.
    #  @param o_duration        Timing record duration, in seconds.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, ParamOut(c_ulong))
    def CHR_vpair_get_tr_duration(self, i_pair_handle: int):
        '''
        The CHR_vpair_get_tr_duration function returns the timing record
        duration, in seconds.

        Parameters
        ----------
        i_pair_handle : int
            An IPTV pair object handle returned by CHR_vpair_new() or
            CHR_receiver_get_vpair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_duration : int
            A pointer to the variable where the timing record duration is
            returned.
            (The timing record duration is measured in seconds.)
        '''
        pass

    #  Creates a new IPTV pair object.
    #
    #  @param o_pairHandle      Pair handle.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(ParamOut(c_ulong))
    def CHR_vpair_new(self):
        '''
        The CHR_vpair_new function creates a new IPTV pair object.

        Parameters
        ----------

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_pair_handle : int
            The handle for the new IPTV pair object.
        '''
        pass

    #  Specifies the number of timing records the pair should generate.
    #
    #  @param i_pairHandle      Pair handle.
    #  @param i_count           Timing record count.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, c_ulong)
    def CHR_vpair_set_no_of_timing_records(self, i_pair_handle: int,
                                           i_count: int):
        '''
        The CHR_vpair_set_no_of_timing_records function specifies the number of
        timing records the IPTV pair should generate.

        Parameters
        ----------
        i_pair_handle : int
            An IPTV pair object handle returned by CHR_vpair_new() or
            CHR_receiver_get_vpair().
        i_count : int
            The number of timing records the IPTV pair should generate.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.

        '''
        pass

    #  Specifies the channel with which this pair is associated.
    #
    #  @param i_pairHandle      Pair handle.
    #  @param i_channelHandle   Channel handle.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, c_ulong)
    def CHR_vpair_set_channel(self, i_pair_handle: int, i_channel_handle: int):
        '''
        The CHR_vpair_set_channel function specifies the channel with which
        this IPTV pair is associated.

        Parameters
        ----------
        i_pair_handle : int
            An IPTV pair object handle returned by CHR_vpair_new() or
            CHR_receiver_get_vpair().
        i_channel_handle : int
            The channel handle returned by CHR_channel_new(),
            CHR_test_get_channel(), or CHR_test_get_channel_by_name().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        '''
        pass

    #  Specifies the timing record duration, in seconds.
    #
    #  @param i_pairHandle      Pair handle.
    #  @param i_duration        Timing record duration, in seconds.
    #
    #  @return Chariot API return code.
    #
    #  @since IxChariot 6.50
    @ctypes_param(c_ulong, c_ulong)
    def CHR_vpair_set_tr_duration(self, i_pair_handle: int, i_duration: int):
        '''
        The CHR_vpair_set_tr_duration function specifies the timing record
        duration, in seconds.

        Parameters
        ----------
        i_pair_handle : int
            An IPTV pair object handle returned by CHR_vpair_new() or
            CHR_receiver_get_vpair().
        i_duration : int
            The timing record duration, in seconds.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        '''
        pass

    #  Returns the runstatus of the specified pair
    #
    #  @param i_pairHandle      Pair handle.
    #  @param runStatus         Runstatus to be filled in.
    #
    #  @return Chariot API return code.
    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_vpair_get_runStatus(self, i_pair_handle: int):
        '''
        The CHR_vpair_get_runStatus function returns the run status for this
        IPTV pair.

        Parameters
        ----------
        i_pair_handle : int
            An IPTV pair object handle returned by CHR_vpair_new() or
            CHR_receiver_get_vpair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        run_status : int
            A pointer to the variable where the run status value is returned.
            The following status types are applicable:
            CHR_PAIR_RUNSTATUS_UNINITIALIZED
            CHR_PAIR_RUNSTATUS_INITIALIZING_1
            CHR_PAIR_RUNSTATUS_INITIALIZING_2
            CHR_PAIR_RUNSTATUS_INITIALIZING_3
            CHR_PAIR_RUNSTATUS_INITIALIZED
            CHR_PAIR_RUNSTATUS_RUNNING
            CHR_PAIR_RUNSTATUS_STOPPING
            CHR_PAIR_RUNSTATUS_REQUESTED_STOP
            CHR_PAIR_RUNSTATUS_ERROR
            CHR_PAIR_RUNSTATUS_RESOLVING_NAMES
            CHR_PAIR_RUNSTATUS_POLLING
            CHR_PAIR_RUNSTATUS_FINISHED
            CHR_PAIR_RUNSTATUS_REQUESTING_STOP
            CHR_PAIR_RUNSTATUS_FINISHED_WARNINGS
            CHR_PAIR_RUNSTATUS_TRANSFERRING_PAYLOAD
            CHR_PAIR_RUNSTATUS_APPLYING_IXIA_CONFIG
            CHR_PAIR_RUNSTATUS_WAITING_FOR_REINIT
            CHR_PAIR_RUNSTATUS_ABANDONED
        '''
        pass

    #  Specifies whether the pair object is locked.
    #
    #  @param i_pairHandle      Pair Object handle.
    #  @param o_useValues       CHR_TRUE for locked; CHR_FALSE for
    #                           unlocked.
    #
    #  @since IxChariot 6.70
    @ctypes_param(c_ulong, ParamOut(c_char))
    def CHR_vpair_get_lock(self, i_pair_handle: int):
        '''
        The CHR_vpair_get_lock function returns a Boolean value that specifies
        whether or not the IPTV pair object is locked.

        Parameters
        ----------
        i_pair_handle : int
            An IPTV pair object handle returned by CHR_vpair_new() or
            CHR_receiver_get_vpair().

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        o_use_values : bool
            A pointer to the variable where the Boolean value is returned.
        '''
        pass

    #  Specifies whether to lock or not the pair object. Locking
    #  allows editing a pair owned by a test.
    #
    #  @param i_pairHandle      Pair Object handle.
    #  @param i_useValues       CHR_TRUE to lock; CHR_FALSE to
    #                           unlock.
    #
    #  @since IxChariot 6.70
    @ctypes_param(c_ulong, c_char)
    def CHR_vpair_set_lock(self, i_pair_handle: int, i_use_values: int):
        '''
        The CHR_vpair_set_lock function locks or unlocks the IPTV pair
        object.
        Locking allows a pair that is owned by a receiver to be edited.

        Parameters
        ----------
        i_pair_handle : int
            An IPTV pair object handle returned by CHR_vpair_new() or
            CHR_receiver_get_vpair().
        i_use_values : int
            Indicates the action to take on the IPTV pair object:
                CHR_TRUE: Lock the IPTV pair object.
                CHR_FALSE: Unlock the IPTV pair object.
                When you unlock the object, it is automatically validated.

        Returns
        -------
        rc : int
            The following return code indicates that the function call was
            successful: CHR_OK.
        '''
        pass
