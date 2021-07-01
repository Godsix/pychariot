# -*- coding: utf-8 -*-
"""
Created on Thu Apr  1 08:51:27 2021

@author: 皓
"""
import os
import os.path as osp
from glob import glob
from platform import architecture
from functools import lru_cache
from winreg import (HKEY_LOCAL_MACHINE, KEY_WOW64_32KEY, KEY_READ,
                    OpenKey, QueryValueEx)
from .const import RetureCode, CHR_DETAIL_LEVEL, CHR_NULL_HANDLE, CHR_BOOLEAN


CHARIOT_VERSION = (0, 2, 1)


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
        return
    return wrapper


class PrintLogger:

    def info(self, log, *args, **kwargs):
        print(log % args, **kwargs)

    def error(self, log, *args, **kwargs):
        print(log % args, **kwargs)

    def debug(self, log, *args, **kwargs):
        print(log % args, **kwargs)


class Chariot:
    APINAME = 'ChrApi.dll'
    REG_KEYS = (r"SOFTWARE\Ixia\IxChariot",
                r"SOFTWARE\Ixia Communications\IxChariot")

    def __init__(self, path=None):
        self.rpc = None
        valid_path = self.get_chrapi_dir(path)
        if valid_path is None:
            raise FileNotFoundError(
                "Can't find Ixia ixChariot C API file ChrApi.dll")
        self.load_api(valid_path)
        # self.logger = logging.getLogger()
        self.logger = PrintLogger()
        self.pairs = []

    @classmethod
    def get_ixchariot_path(cls):
        for reg_key in cls.REG_KEYS:
            try:
                with OpenKey(HKEY_LOCAL_MACHINE, reg_key,
                             access=KEY_READ | KEY_WOW64_32KEY) as key:
                    value, *_ = QueryValueEx(key, 'Installation Directory')
                    return value
            except FileNotFoundError:
                pass
        return None

    @classmethod
    def get_chrapi_dir(cls, path=None):
        if path and osp.exists(osp.join(path, cls.APINAME)):
            return path
        for item in os.environ.get('PATH').split(';'):
            if item and osp.exists(osp.join(item, cls.APINAME)):
                return item
        else:
            ixia_path = cls.get_ixchariot_path()
            if ixia_path and osp.exists(osp.join(ixia_path, cls.APINAME)):
                return ixia_path
        return None

    @classmethod
    def get_scripts_path(cls, path=None):
        path = cls.get_chrapi_dir(path)
        if not path:
            return None
        script_path = osp.join(path, 'Scripts')
        return script_path

    def start_rpc(self):
        import rpcpy32
        import rpyc
        self.python = rpcpy32
        self.rpc_server = self.python.RPC_SERVER
        rpc_pip_list = self.rpc_server.pip_list()
        if 'pychariot32' not in rpc_pip_list:
            dir_path = osp.dirname(__file__)
            whls = glob(osp.join(dir_path, '*.whl'))
            if whls:
                self.rpc_server.pip_install(whls[0])
        self.rpc_server.start()
        self.rpc = rpyc.classic.connect("localhost")
        self.chrapi = self.rpc.modules.pychariot32

    def stop_rpc(self):
        if self.rpc is not None:
            self.chrapi = None
            self.rpc = None
            self.rpc_server.stop()
            self.rpc_server = None
            self.python = None

    def load_api(self, path):
        arch, ost = architecture()
        if not ost == 'WindowsPE':
            raise OSError('The OS must be based on Windows NT.')
        if arch == '64bit':
            self.start_rpc()
            self.api = self.chrapi.CHRAPI(path)
        else:
            from .chrapi import CHRAPI
            self.api = CHRAPI(path)
        self.path = path
        self.api_dir.cache_clear()

    def __del__(self):
        self.stop_rpc()

    @lru_cache
    def api_dir(self):
        return [x for x in dir(self.api) if x.startswith('CHR_')]

    def __dir__(self):
        return super().__dir__() + self.api_dir()

    def __getattr__(self, attr):
        classname = self.__class__.__name__
        if attr.startswith('CHR_'):
            if hasattr(self.api, attr):
                return getattr(self.api, attr)
            else:
                classname = 'CHRAPI'
        else:
            chr_name = 'CHR_{}'.format(attr)
            if hasattr(self.api, chr_name):
                func = getattr(self.api, chr_name)
                wrapper = chr_api_wrapper(self, func)
                return wrapper
        raise AttributeError(
            "'{}' object has no attribute '{}'".format(classname, attr))

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

    def apply_pair_attr(self, pair, e1, e2, script, **kwargs):
        self.set_pair_addr(pair, e1, e2)
        if osp.isabs(script):
            script_path = script
        else:
            script_path = osp.join(self.path, 'Scripts', script)
        if not osp.exists(script_path):
            raise FileNotFoundError(
                'Script is not fount:{}'.format(script_path))
        self.pair_use_script_filename(pair, script_path)
        if 'comment' in kwargs:
            self.pair_set_comment(pair, kwargs.get('comment'))
        if 'protocol' in kwargs:
            self.pair_set_protocol(pair, kwargs.get('protocol'))

    def get_pairs(self, test):
        count = self.test_get_pair_count(test)
        ret = [self.test_get_pair(test, x) for x in range(count)]
        return ret

    def get_pair_time_elapsed(self, pair):
        '''获取pair占用时间'''
        count = self.pair_get_timing_record_count(pair)
        handle = self.pair_get_timing_record(pair, count - 1)
        time_elapsed = self.timingrec_get_elapsed(handle)
        return time_elapsed

    def get_pair_bytes_all_e1(self, pair):
        '''获取pair传输总bytes数'''
        sent = self.common_results_get_bytes_sent_e1(pair)
        recv = self.common_results_get_bytes_recv_e1(pair)
        return sent + recv

    def get_pairs_bytes_sent_e1(self, pairs):
        '''获取pair传输总发送bytes数'''
        res = [self.common_results_get_bytes_sent_e1(x) for x in pairs]
        return sum(res)

    def get_pairs_bytes_recv_e1(self, pairs):
        '''获取pair传输总接收bytes数'''
        res = [self.common_results_get_bytes_recv_e1(x) for x in pairs]
        return sum(res)

    def get_pairs_results_average(self, pairs):
        '''获取pairs序列的总透传平均速率'''
        elapsed_max = max([self.get_pair_time_elapsed(x) for x in pairs])
        trans_sum = sum([self.get_pair_bytes_all_e1(x) for x in pairs])
        trans_mbps = trans_sum * 8e-6
        average = trans_mbps / elapsed_max
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

    def wait_for_test(self, test, wait_time, timeout=1):
        '''等待测试结束...'''
        is_stopped = False
        timer = 0
        while (is_stopped == CHR_BOOLEAN.CHR_FALSE) and (timer < wait_time):
            rc = self.CHR_test_query_stop(test, timeout)
            if rc == RetureCode.CHR_OK:
                is_stopped = CHR_BOOLEAN.CHR_TRUE
            elif rc == RetureCode.CHR_TIMED_OUT:
                timer += timeout
                self.logger.info("Waiting for test to stop... (%d)",
                                 timer, end='\r')
            else:
                self.show_error(test, rc, "test_query_stop")
                break
        if (is_stopped == CHR_BOOLEAN.CHR_FALSE):
            self.show_error(test, RetureCode.CHR_TIMED_OUT, "wait_for_test")
            return False
        return True
