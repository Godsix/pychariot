# -*- coding: utf-8 -*-
"""
Created on Thu Apr  1 08:51:27 2021

@author: 皓
"""
# pylint: disable=import-outside-toplevel,too-many-public-methods,too-many-instance-attributes
import sys
import os.path as osp
import logging
from glob import glob
from enum import IntEnum
from platform import architecture
from functools import lru_cache
from .const import RetureCode, CHR_DETAIL_LEVEL, CHR_NULL_HANDLE


CHARIOT_VERSION = (0, 3, 0)


def chr_api_wrapper(self, func):

    # @wraps(func)
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
                self.show_error(handle, rc, api_name)
        if out:
            if len(out) == 1:
                return out[0]
            return tuple(out)
        return None
    return wrapper


class Status(IntEnum):
    OK = 0
    INIT = 1
    API = 2
    RPC = 3


class Chariot:
    def __init__(self, address=None, status_callback=None):
        self.logger = logging.getLogger()
        self.address = address
        self.status_callback = status_callback
        self.status = Status.INIT
        self.python = None
        self.rpc_server = None
        self.pymodule = None
        self.rpc = None
        self.chrapi = None
        self.pairs = []
        if address is not None:
            self.connect(self.address)

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        if not getattr(self, '_status', None) == value:
            self._status = value
            if self.status_callback:
                self.status_callback(value)

    def connect(self, address):
        if address in ('localhost', '127.0.0.1'):
            arch, ost = architecture()
            if not ost == 'WindowsPE':
                raise OSError('The OS must be based on Windows NT.')
            if arch == '64bit':
                self.status = Status.RPC
                self.start_rpc()
                self.connect_rpcpy32(address)
                self.status = Status.API
                self.api = self.chrapi.LocalCHRAPI()
            else:
                from . import chrapi
                self.chrapi = chrapi
                self.status = Status.API
                self.api = self.chrapiLocalCHRAPI()
            self.api_dir.cache_clear()
        else:
            self.status = Status.API
            self.connect_rpc(address)
            self.api = self.chrapi.LocalCHRAPI()
        self.status = Status.OK

    def start_rpc(self):
        if self.chrapi is not None:
            return
        self.restart_rpc()

    def get_pychariot32_path(self):
        whls = glob(osp.join(osp.dirname(__file__), '*.whl'))
        if whls:
            return whls[0]
        return None

    def restart_rpc(self):
        import rpcpy32
        self.stop_rpc()
        self.python = rpcpy32
        self.rpc_server = self.python.RPC_SERVER
        rpc_pip_list = self.rpc_server.pip_list()
        if 'pychariot32' not in rpc_pip_list:
            whl = self.get_pychariot32_path()
            if whl:
                self.rpc_server.pip_install(whl)
        else:
            from .chrapi import CHR_API_VERSION
            installed = rpc_pip_list['pychariot32']
            version = '.'.join([str(x) for x in CHR_API_VERSION])
            if version > installed:
                whl = self.get_pychariot32_path()
                if whl:
                    self.rpc_server.pip_install(whl)
        self.rpc_server.start()

    def connect_rpcpy32(self, address):
        import rpyc
        self.rpc = rpyc.classic.connect(address)
        self.pymodule = self.rpc.modules.pychariot32
        self.rpc.modules.sys.stdout = sys.stdout
        self.rpc.modules.sys.stderr = sys.stderr
        self.chrapi = self.pymodule.chrapi

    def connect_rpc(self, address):
        import rpyc
        self.rpc = rpyc.classic.connect(address)
        self.pymodule = self.rpc.modules.pychariot
        self.rpc.modules.sys.stdout = sys.stdout
        self.rpc.modules.sys.stderr = sys.stderr
        self.chrapi = self.pymodule.chrapi

    def close_rpc(self):
        if hasattr(self.rpc, 'close'):
            self.rpc.close()
        self.clear_attr('rpc')

    def clear_attr(self, name):
        if not hasattr(self, name):
            return
        setattr(self, name, None)
        try:
            delattr(self, name)
        except AttributeError:
            pass

    def stop_rpc(self):
        if self.rpc is not None:
            self.close_rpc()
        rpc_server = getattr(self, 'rpc_server', None)
        if rpc_server is not None:
            rpc_server.stop()
        for item in ('chrapi', 'pymodule', 'rpc_server', 'python'):
            self.clear_attr(item)

    def __del__(self):
        self.stop_rpc()

    @lru_cache()
    def api_dir(self):
        return [x for x in dir(self.api) if x.startswith('CHR_')]

    def __dir__(self):
        return super().__dir__() + self.api_dir()

    def __getattr__(self, attr):
        classname = self.__class__.__name__
        if attr not in ('_status', 'api'):
            if hasattr(self, 'api'):
                if attr.startswith('CHR_'):
                    if hasattr(self.api, attr):
                        return getattr(self.api, attr)
                    classname = 'CHRAPI'
                else:
                    chr_name = f'CHR_{attr}'
                    if hasattr(self.api, chr_name):
                        func = getattr(self.api, chr_name)
                        wrapper = chr_api_wrapper(self, func)
                        return wrapper
        raise AttributeError(f"'{classname}' object has no attribute '{attr}'")

    def show_error(self, handle, code, where):
        '''转换错误信息'''
        rc, msg = self.CHR_api_get_return_msg(code)
        if rc != RetureCode.CHR_OK:
            # Could not get the message: show why
            self.logger.error("%s failed\n", where)
            self.logger.error(
                "Unable to get message for return code %d, rc = %d\n",
                code, rc)
        else:
            # Tell the user about the error
            self.logger.error("%s failed: rc = %d (%s)\n", where, code, msg)

        code_tuple = (RetureCode.CHR_OPERATION_FAILED,
                      RetureCode.CHR_OBJECT_INVALID,
                      RetureCode.CHR_APP_GROUP_INVALID)

        if (code in code_tuple) and handle != CHR_NULL_HANDLE:
            rc, error_info = self.CHR_common_error_get_info(
                handle, CHR_DETAIL_LEVEL.CHR_DETAIL_LEVEL_ALL)
            if rc == RetureCode.CHR_OK:
                self.logger.error("Extended error info:\n%s\n", error_info)

    def api_initialize(self):
        '''初始化IxChariot API'''
        rc, error_info = self.CHR_api_initialize(
            CHR_DETAIL_LEVEL.CHR_DETAIL_LEVEL_ALL)
        if rc != RetureCode.CHR_OK:
            self.logger.error("Initialization failed: rc = %d\n", rc)
            self.logger.error("Extended error info:\n%s\n", error_info)
        return rc

    def set_pair_addr(self, pair, addr_e1, addr_e2):
        '''设置pair的e1,e2地址'''
        self.pair_set_e1_addr(pair, str(addr_e1))
        self.pair_set_e2_addr(pair, str(addr_e2))

    def create_pair_attr(self, e1, e2, script, **kwargs):
        pair = self.pair_new()
        self.apply_pair_attr(pair, e1, e2, script, **kwargs)
        return pair

    # pylint: disable=too-many-arguments
    def apply_pair_attr(self, pair, e1, e2, script,
                        protocol=None,
                        comment=None):
        self.set_pair_addr(pair, e1, e2)
        if osp.isabs(script):
            script_path = script
        else:
            script_path = osp.join(self.path, 'Scripts', script)
        if not osp.exists(script_path):
            raise FileNotFoundError(f'Script is not fount:{script_path}')
        self.pair_use_script_filename(pair, script_path)
        if comment is not None:
            self.pair_set_comment(pair, comment)
        if protocol is not None:
            self.pair_set_protocol(pair, protocol)

    def get_pairs(self, test_handle):
        count = self.test_get_pair_count(test_handle)
        return tuple(self.test_get_pair(test_handle, x) for x in range(count))

    def get_pair_time_elapsed(self, pair):
        '''获取pair占用时间'''
        count = self.pair_get_timing_record_count(pair)
        if count <= 0:
            return 0
        handle = self.pair_get_timing_record(pair, count - 1)
        time_elapsed = self.timingrec_get_elapsed(handle)
        return time_elapsed

    def get_pair_measure_time(self, pair):
        '''获取pair占用时间'''
        measure_time = self.common_results_get_meas_time(pair)
        return measure_time

    def get_pair_bytes_all_e1(self, handle):
        '''获取pair传输总bytes数'''
        sent = self.common_results_get_bytes_sent_e1(handle)
        recv = self.common_results_get_bytes_recv_e1(handle)
        return sent + recv

    def get_pairs_bytes_sent_e1(self, pairs):
        '''获取pair传输总发送bytes数'''
        return sum(self.common_results_get_bytes_sent_e1(x) for x in pairs)

    def get_pairs_bytes_recv_e1(self, pairs):
        '''获取pair传输总接收bytes数'''
        return sum(self.common_results_get_bytes_recv_e1(x) for x in pairs)

    def get_pairs_results_average(self, pairs):
        '''获取pairs序列的总透传平均速率'''
        elapsed_max = max(self.get_pair_time_elapsed(x) for x in pairs)
        if elapsed_max == 0:
            return None
        trans_sum = sum(self.get_pair_bytes_all_e1(x) for x in pairs)
        trans_mbps = trans_sum * 8e-6
        average = trans_mbps / elapsed_max
        return average

    def get_pairs_measure_results_average(self, pairs):
        '''获取pairs序列的总透传平均速率'''
        measure_time_max = max(self.get_pair_measure_time(x) for x in pairs)
        if measure_time_max == 0:
            return None
        trans_sum = sum(self.get_pair_bytes_all_e1(x) for x in pairs)
        trans_mbps = trans_sum * 8e-6
        average = trans_mbps / measure_time_max
        return average

    def pair_swap_endpoints(self, pair):
        '''获取pairs序列的总透传平均速率'''
        if self.api.has_func('CHR_pair_swap_endpoints'):
            chr_api_wrapper(
                self, getattr(self, 'CHR_pair_swap_endpoints'))(pair)
        else:
            e1 = self.pair_get_e1_addr(pair)
            e2 = self.pair_get_e2_addr(pair)
            self.set_pair_addr(pair, e2, e1)

    def get_swap_pairs_test(self, test):
        '''获取pairs序列的总透传平均速率'''
        test_handle = self.test_new()
        src_pairs = self.get_pairs(test)
        dst_pairs = []
        for src_pair in src_pairs:
            dst_pair = self.pair_new()
            self.pair_copy(dst_pair, src_pair)
            self.pair_swap_endpoints(dst_pair)
            dst_pairs.append(dst_pair)
            self.test_add_pair(test_handle, dst_pair)
        return test_handle

    def wait_for_test(self, test_handle, time_callback=None, timeout=1):
        is_finished = False
        timer = 0
        while is_finished is False:
            rc = self.CHR_test_query_stop(test_handle, timeout)
            if time_callback is not None:
                time_callback(timer)
            if rc == RetureCode.CHR_OK:
                is_finished = True
            elif rc == RetureCode.CHR_TIMED_OUT:
                timer += timeout
                self.logger.info("Waiting for test to stop... (%d)",
                                 timer, end='\r')
            else:
                self.show_error(test_handle, rc, "test_query_stop")
                break
        if is_finished is False:
            self.show_error(test_handle, RetureCode.CHR_TIMED_OUT,
                            "wait_for_test")
            return False
        return True

    def wait_test_timeout(self, test_handle, wait_time, timeout=1):
        '''等待测试结束...'''
        is_finished = False
        timer = 0
        while is_finished is False and (timer < wait_time):
            rc = self.CHR_test_query_stop(test_handle, timeout)
            if rc == RetureCode.CHR_OK:
                is_finished = True
            elif rc == RetureCode.CHR_TIMED_OUT:
                timer += timeout
                self.logger.info("Waiting for test to stop... (%d)",
                                 timer, end='\r')
            else:
                self.show_error(test_handle, rc, "test_query_stop")
                break
        if is_finished is False:
            self.show_error(test_handle, RetureCode.CHR_TIMED_OUT,
                            "wait_for_test")
            return False
        return True
