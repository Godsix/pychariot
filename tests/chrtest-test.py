# -*- coding: utf-8 -*-
"""
Created on Wed Feb 10 11:31:50 2021

@author: haoyue
"""
import os
import os.path as osp
import sys
from platform import architecture
import logging
import subprocess
from functools import lru_cache
from winreg import (HKEY_LOCAL_MACHINE, KEY_WOW64_32KEY, KEY_READ,
                    OpenKey, QueryValueEx)
from argparse import ArgumentParser
from chrapi_constant import (CHR_DETAIL_LEVEL_ALL, CHR_OK, CHR_NULL_HANDLE,
                             CHR_OPERATION_FAILED, CHR_OBJECT_INVALID,
                             CHR_APP_GROUP_INVALID, CHR_FALSE, CHR_TRUE,
                             CHR_TIMED_OUT, CHR_PROTOCOL_TCP,
                             CHR_TEST_END_AFTER_FIXED_DURATION,
                             CHR_RESULTS_THROUGHPUT)
import Spec_CHR


__version__ = (0, 1, 1)


class CHRTest:
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
        self.logger = logging.getLogger()
        self.pairs = []

    def get_ixchariot_path(self):
        for reg_key in self.REG_KEYS:
            try:
                with OpenKey(HKEY_LOCAL_MACHINE, reg_key,
                             access=KEY_READ | KEY_WOW64_32KEY) as key:
                    value, *_ = QueryValueEx(key, 'Installation Directory')
                    return value
            except FileNotFoundError:
                pass
        return None

    def get_chrapi_dir(self, path=None):
        if path and osp.exists(osp.join(path, self.APINAME)):
            return path
        for item in os.environ.get('PATH').split(';'):
            if item and osp.exists(osp.join(item, self.APINAME)):
                return item
        else:
            ixia_path = self.get_ixchariot_path()
            if ixia_path and osp.exists(osp.join(ixia_path, self.APINAME)):
                return ixia_path
        return None

    def start_rpc(self):
        import rpcpy32
        import rpyc
        self.python = rpcpy32
        self.rpc_server = self.python.RPC_SERVER
        # self.rpc_server.pip_upgrade()
        self.rpc_server.start()
        self.rpc = rpyc.classic.connect("localhost")
        self.chrapi = self.rpc.modules.pyixchariot32

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
            import chrapi as chrapi32
            self.chrapi = chrapi32
            self.api = self.chrapi.CHRAPI(path)
        self.path = path
        self.api_dir.cache_clear()

    def __del__(self):
        self.stop_rpc()

    @lru_cache
    def api_dir(self):
        return [x for x in dir(self.api) if x.startswith('CHR_')]

    def __dir__(self):
        return super().__dir__() + self.api_dir()

    def show_error(self, handle, code, where):
        '''转换错误信息'''
        rc, msg = self.CHR_api_get_return_msg(code)
        if rc != CHR_OK:
            # Could not get the message: show why
            self.logger.error("%s failed\n", where)
            self.logger.error(
                "Unable to get message for return code %d, rc = %d\n",
                code, rc)
        else:
            # Tell the user about the error
            self.logger.error("%s failed: rc = %d (%s)\n", where, code, msg)

        code_tuple = (CHR_OPERATION_FAILED, CHR_OBJECT_INVALID,
                      CHR_APP_GROUP_INVALID)

        if (code in code_tuple) and handle != CHR_NULL_HANDLE:
            rc, error_info = self.api.CHR_common_error_get_info(
                handle, CHR_DETAIL_LEVEL_ALL)
            if rc == CHR_OK:
                self.logger.error("Extended error info:\n%s\n", error_info)

    def get_version(self):
        rc, version = self.CHR_api_get_version()
        return version

    def initialize(self):
        '''初始化IxChariot API'''
        rc, error_info = self.CHR_api_initialize(CHR_DETAIL_LEVEL_ALL)
        if rc != CHR_OK:
            self.logger.error("Initialization failed: rc = %d\n", rc)
            self.logger.error("Extended error info:\n%s\n", error_info)
        return rc

    def create_test_new(self):
        '''创建测试'''
        self.logger.info('Create the test...')
        rc, test_handle = self.CHR_test_new()
        if rc != CHR_OK:
            self.show_error(CHR_NULL_HANDLE, rc, "test_new")
        return test_handle

    def create_pair_new(self):
        '''创建Pair'''
        self.logger.info('Create the pair....')
        rc, pair_handle = self.CHR_pair_new()
        if rc != CHR_OK:
            self.show_error(CHR_NULL_HANDLE, rc, "pair_new")
        return pair_handle

    def set_pair_addr(self, pair, addr_e1, addr_e2):
        '''设置pair的e1,e2地址'''
        addr_e1 = str(addr_e1)
        addr_e2 = str(addr_e2)
        rc = self.CHR_pair_set_e1_addr(pair, addr_e1)
        if rc != CHR_OK:
            self.show_error(pair, rc, "pair_set_e1_addr")
            return rc

        rc = self.CHR_pair_set_e2_addr(pair, addr_e2)
        if rc != CHR_OK:
            self.show_error(pair, rc, "pair_set_e2_addr")
            return rc
        return rc

    def set_pair_comment(self, pair, comment):
        '''设置Pair的注释'''
        self.logger.info('Set the required pair comment...')
        rc = self.CHR_pair_set_comment(pair, comment)
        if rc != CHR_OK:
            self.show_error(pair, rc, "pair_set_comment")

    def set_pair_protocol(self, pair, protocol):
        '''设置Pair的协议'''
        self.logger.info('Set the required pair protocol...')
        rc = self.CHR_pair_set_protocol(pair, protocol)
        if rc != CHR_OK:
            self.show_error(pair, rc, "pair_set_protocol")

    def set_pair_script(self, pair, script):
        '''设置Pair的脚本'''
        self.logger.info('Use a script...')
        rc = self.CHR_pair_use_script_filename(pair, script)
        if rc != CHR_OK:
            self.show_error(pair, rc, "pair_use_script_filename")

    def create_pair_attr(self, e1, e2, script, **kwargs):
        pair_handle = self.create_pair_new()
        self.apply_pair_attr(pair_handle, e1, e2, script, **kwargs)
        return pair_handle

    def apply_pair_attr(self, pair, e1, e2, script, **kwargs):
        self.set_pair_addr(pair, e1, e2)
        if osp.isabs(script):
            script_path = script
        else:
            script_path = osp.join(self.path, 'Scripts', script)
        if not osp.exists(script_path):
            raise FileNotFoundError(
                'Script is not fount:{}'.format(script_path))
        self.set_pair_script(pair, script_path)
        if 'comment' in kwargs:
            self.set_pair_comment(pair, kwargs.get('comment'))

    def set_saving_file(self, test, test_file):
        '''设置保存文件名'''
        self.logger.info('Set the test filename for saving...')
        rc = self.CHR_test_set_filename(test, test_file)
        if rc != CHR_OK:
            self.show_error(test, rc, "test_set_filename")

    def set_pair_script_embedded_payload(self, pair, variable_name):
        '''设置Pair的脚本嵌入Payload'''
        self.logger.info('Set the Script Embedded Payload...')
        payload = 'This is a sample\0embedded payload'
        rc = self.CHR_pair_set_script_embedded_payload(pair,
                                                       variable_name,
                                                       payload)
        if (rc != CHR_OK):
            self.show_error(pair, rc, "pair_set_script_embedded_payload")

    def set_connect_timeout(self, runopts, timeout):
        '''设置连接超时时间'''
        self.logger.info('Set the connect timeout...')
        rc = self.CHR_runopts_set_connect_timeout(runopts, timeout)
        if (rc != CHR_OK):
            self.show_error(runopts, rc, "runopts_set_connect_timeout")

    def set_dgopts_recv_timeout(self, dgopts, timeout):
        '''设置数据包接收超时时间（单位：ms）'''
        self.logger.info('Set the datagram receive timeout...')
        rc = self.CHR_dgopts_set_recv_timeout(dgopts, timeout)
        if rc != CHR_OK:
            self.show_error(dgopts, rc, "dgopts_set_recv_timeout")

    def set_dgopts_retrans_timeout(self, dgopts, timeout):
        '''设置数据包接收超时时间（单位：ms）'''
        self.logger.info('Set the datagram receive timeout...')

        rc = self.CHR_dgopts_set_retrans_timeout(dgopts, timeout)
        if rc != CHR_OK:
            self.show_error(dgopts, rc, "dgopts_set_retrans_timeout")

    def set_test_duration(self, runopts, duration):
        '''设置脚本运行时间（单位：s）'''
        rc = self.CHR_runopts_set_test_duration(runopts, duration)
        if rc != CHR_OK:
            self.show_error(runopts, rc, "runopts_set_test_duration")

    def set_test_end(self, runopts, testend):
        '''设置脚本运结束方式'''
        rc = self.CHR_runopts_set_test_end(runopts, testend)
        if (rc != CHR_OK):
            self.show_error(runopts, rc, "runopts_set_test_end")

    def add_pair_to_test(self, test, pair):
        '''添加Pair到测试'''
        self.logger.info('Add the pair to the test...')
        rc = self.CHR_test_add_pair(test, pair)
        if rc != CHR_OK:
            self.show_error(test, rc, "test_add_pair")

    # def set_pairs_attribute(self, test):
    #     '''设置Pairs属性'''
    #     self.logger.info('Add the pair attribute...')
    #     pair_index = 0
    #     #
    #     card_no = 0
    #     part = Spec_CHR.num_pairs/Spec_CHR.num_cards
    #     semi = part/2
    #     for index in range(Spec_CHR.num_cards):
    #         card_no += 1
    #         for i in range(part):
    #             # 创建pair
    #             pair = self.create_pair_new()
    #             # 添加pair注释
    #             pair_index += 1
    #             comment = "[Card %d] Pair %d" % (card_no, pair_index)
    #             self.set_pair_comment(pair, comment)
    #             # 设置endpoint地址
    #             if Spec_CHR.test_type == 'RX':
    #                 if Spec_CHR.network_type == 'WAN':
    #                     self.set_pair_addr(pair, Spec_CHR.e1_ip[index],
    #                                        Spec_CHR.e2_ip)
    #                 else:
    #                     self.set_pair_addr(pair, Spec_CHR.e2_ip,
    #                                        Spec_CHR.e1_ip[index])
    #                 # 设置脚本
    #                 self.set_pair_script(pair, Spec_CHR.script_file)
    #             elif Spec_CHR.test_type == 'TX':
    #                 self.set_pair_addr(pair, Spec_CHR.e1_ip[index],
    #                                    Spec_CHR.e2_ip)
    #                 # 设置脚本
    #                 self.set_pair_script(pair, Spec_CHR.script_file)
    #             else:
    #                 if i >= semi:
    #                     self.set_pair_addr(pair, Spec_CHR.e1_ip[index],
    #                                        Spec_CHR.e2_ip)
    #                     # 设置脚本
    #                     if Spec_CHR.network_type == 'WAN':
    #                         ll = Spec_CHR.script_file.split('_')
    #                         # 修改脚本名称
    #                         i = 0
    #                         for elem in ll:
    #                             i += 1
    #                             if 'Throughput' in elem:
    #                                 break
    #                         ll.insert(i, 'TX')
    #                         script_file = '_'.join(ll)
    #                         self.set_pair_script(pair, script_file)
    #                     else:
    #                         self.set_pair_script(pair, Spec_CHR.script_file)
    #                 else:
    #                     if Spec_CHR.network_type == 'WAN':
    #                         self.set_pair_addr(pair, Spec_CHR.e1_ip[index],
    #                                            Spec_CHR.e2_ip)
    #                         # 设置脚本
    #                         ll = Spec_CHR.script_file.split('_')
    #                         # 修改脚本名称
    #                         i = 0
    #                         for elem in ll:
    #                             i += 1
    #                             if 'Throughput' in elem:
    #                                 break
    #                         ll.insert(i, 'RX')
    #                         script_file = '_'.join(ll)
    #                         self.set_pair_script(pair, script_file)
    #                     else:
    #                         self.set_pair_addr(pair, Spec_CHR.e2_ip,
    #                                            Spec_CHR.e1_ip[index])
    #                         # 设置脚本
    #                         self.set_pair_script(pair, Spec_CHR.script_file)
    #             # 设置协议
    #             self.set_pair_protocol(pair, CHR_PROTOCOL_TCP)
    #             # 设置脚本
    #             # self.set_pair_script(pair, Spec_CHR.script_file)
    #             # 设置嵌入Payload
    #             # self.set_pair_script_embedded_payload(
    #             #     pair, Spec_CHR.send_data_type_name)
    #             # pair添加到list中
    #             self.pairs.append(pair)
    #             # pair添加到test中
    #             self.add_pair_to_test(test, pair)

    def start_test(self, test):
        '''开始测试'''
        self.logger.info('Run the test...')

        rc = self.CHR_test_start(test)
        if rc != CHR_OK:
            self.show_error(test, rc, "start_test")

    def wait_for_test(self, test):
        '''等待测试结束...'''
        self.logger.info('Wait for the test to stop...')

        #
        is_stopped = CHR_FALSE
        timer = 0
        while (is_stopped == CHR_FALSE) and (timer < Spec_CHR.max_wait):
            rc = self.CHR_test_query_stop(test, Spec_CHR.timeout)
            if rc == CHR_OK:
                is_stopped = CHR_TRUE
            elif rc == CHR_TIMED_OUT:
                timer += Spec_CHR.timeout
                self.logger.info("Waiting for test to stop... (%d)", timer)
            else:
                self.show_error(test, rc, "test_query_stop")

        if (is_stopped == CHR_FALSE):
            self.show_error(test, CHR_TIMED_OUT, "test_query_stop")

    def save_test(self, test):
        '''保存测试结果'''
        self.logger.info('Save the test...')

        rc = self.CHR_test_save(test)
        if (rc != CHR_OK):
            self.show_error(test, rc, "test_save")

    def get_run_opts(self, test):
        '''获取运行参数句柄'''
        self.logger.info('Get the handle of run options...')
        rc, runopts = self.CHR_test_get_runopts(test)
        if (rc != CHR_OK):
            self.show_error(test, rc, "test_get_runopts")
        return runopts

    def get_dg_opts(self, test):
        '''获取Datagram参数句柄'''
        self.logger.info('Get the handle of datagram options...')

        rc, dgopts = self.CHR_test_get_dgopts(test)
        if (rc != CHR_OK):
            self.show_error(test, rc, "test_get_dgopts")
        #
        return dgopts

    def get_connect_timeout(self, runopts):
        '''获取连接超时时间'''
        self.logger.info('Get the handle of run options...')
        rc, timeout = self.CHR_runopts_get_connect_timeout(runopts)
        if (rc != CHR_OK):
            self.show_error(runopts, rc, "runopts_get_connect_timeout")
        return timeout

    def get_pair_count(self, test):
        '''获取测试Pair数量'''
        self.logger.info('Get the number of pairs...')

        rc, pair_count = self.CHR_test_get_pair_count(test)
        if (rc != CHR_OK):
            self.show_error(test, rc, "get_pair_count")
        self.logger.info("Number of pairs = %d", pair_count)
        return pair_count

    def get_pair(self, test, index):
        '''获取测试Pair数量'''
        self.logger.info('Get pairs by index...')

        rc, pair = self.CHR_test_get_pair(test, index)
        if (rc != CHR_OK):
            self.show_error(test, rc, "get_pair")
        return pair

    def get_pair_addr_e1(self, pair):
        '''获取endpoint1的地址'''
        self.logger.info('Get the address of endpoint1...')
        rc, addr = self.CHR_pair_get_e1_addr(pair)
        if (rc != CHR_OK):
            self.show_error(pair, rc, "pair_get_e1_addr")
        return addr

    def get_pair_addr_e2(self, pair):
        '''获取endpoint2的地址'''
        self.logger.info('Get the address of endpoint2...')
        rc, addr = self.CHR_pair_get_e2_addr(pair)
        if (rc != CHR_OK):
            self.show_error(pair, rc, "pair_get_e2_addr")
        return addr

    def get_pair_protocol(self, pair):
        '''获取Pair的协议'''
        self.logger.info('Get the required pair protocol...')
        rc, protocol = self.CHR_pair_get_protocol(pair)
        if (rc != CHR_OK):
            self.show_error(pair, rc, "pair_get_protocol")
        return ord(protocol)

    def get_pair_script(self, pair):
        '''获取Pair的脚本'''
        self.logger.info('Get the required pair script filename...')
        rc, script_name = self.CHR_pair_get_script_filename(pair)
        if (rc != CHR_OK):
            self.show_error(pair, rc, "pair_get_script_filename")
        return script_name

    def get_pair_appl_script(self, pair):
        '''获取Pair的应用程序脚本'''
        self.logger.info('Get the required pair application script name...')

        rc, appl_script_name = self.CHR_pair_get_appl_script_name(pair)
        if (rc != CHR_OK):
            self.show_error(pair, rc, "pair_get_appl_script_name")
        return appl_script_name

    def get_pair_comment(self, pair):
        '''获取Pair的注释'''
        self.logger.info('Set the required pair comment...')

        rc, buf = self.CHR_pair_get_comment(pair)
        if rc != CHR_OK:
            self.show_error(pair, rc, "pair_get_comment")
        return buf

    def get_pair_time_record_count(self, pair):
        '''获取Pair的时间记录序列'''
        self.logger.info('Get the required pair number of timing records...')
        rc, timing_rec_count = self.CHR_pair_get_timing_record_count(pair)
        if (rc != CHR_OK):
            self.show_error(pair, rc, "pair_get_timing_record_count")
        return timing_rec_count

    def get_pair_time_record(self, pair, num):
        '''获取Pair的时间记录数'''
        self.logger.info('Get the required pair number of timing records...')

        rc, timing_rec_handle = self.CHR_pair_get_timing_record(pair, num)
        if (rc != CHR_OK):
            self.show_error(pair, rc, "pair_get_timing_record")
        return timing_rec_handle

    def get_pair_time_elapsed(self, handle):
        '''获取Pair的时间记录数elapsed'''
        self.logger.info('Get the required pair number of timing records...')

        rc, time_elapsed = self.CHR_timingrec_get_elapsed(handle)
        if (rc != CHR_OK):
            self.show_error(handle, rc, "timingrec_get_elapsed")
        #
        return time_elapsed

    def get_pair_bytes_recv_e1(self, pair):
        '''获取Pair的endpoit1接收的字节数'''
        self.logger.info('Get the number of bytes received' +
                         ' by Endpoint 1 from the test results...')

        rc, recv_bytes = self.CHR_common_results_get_bytes_recv_e1(pair)
        if (rc != CHR_OK):
            self.show_error(pair, rc, "common_results_get_bytes_recv_e1")
        return recv_bytes

    def get_pair_bytes_sent_e1(self, pair):
        '''获取Pair的endpoit1发送的字节数'''
        self.logger.info('Get the number of bytes sent' +
                         ' by Endpoint 1 from the test results...')

        rc, sent_bytes = self.CHR_common_results_get_bytes_sent_e1(pair)
        if (rc != CHR_OK):
            self.show_error(pair, rc, "common_results_get_bytes_sent_e1")
        #
        return sent_bytes

    def get_pair_bytes_recv_e2(self, pair):
        '''获取Pair的endpoit2接收的字节数'''
        self.logger.info('Get the number of bytes received' +
                         ' by Endpoint 2 from the test results...')

        rc, recv_bytes = self.CHR_common_results_get_bytes_recv_e2(pair)
        if (rc != CHR_OK):
            self.show_error(pair, rc, "common_results_get_bytes_recv_e2")
        return recv_bytes

    def get_pair_res_avg(self, pair, res_type):
        '''获取Pair平均结果'''
        self.logger.info('Get the average results...')

        rc, res_avg = self.CHR_pair_results_get_average(pair, res_type)
        if (rc != CHR_OK):
            self.show_error(pair, rc, "pair_results_get_average")
        return res_avg

    def get_pair_res_min(self, pair, res_type):
        '''获取Pair最小结果'''
        self.logger.info('Get the minimum results...')

        rc, res_min = self.CHR_pair_results_get_minimum(pair, res_type)
        if (rc != CHR_OK):
            self.show_error(pair, rc, "pair_results_get_minimum")
        return res_min

    def get_pair_res_max(self, pair, res_type):
        '''获取Pair最大结果'''
        self.logger.info('Get the maximum results...')

        rc, res_max = self.CHR_pair_results_get_maximum(pair, res_type,)
        if (rc != CHR_OK):
            self.show_error(pair, rc, "pair_results_get_maximum")
        return res_max

    def del_pair(self, pair):
        '''删除Pair'''
        self.logger.info('Delete the special pair...')

        if pair != CHR_NULL_HANDLE:
            self.CHR_pair_delete(pair)

    def del_test(self, test):
        '''删除Test'''
        self.logger.info('Delete the special test...')

        if test != CHR_NULL_HANDLE:
            self.CHR_test_delete(test)

    def exit_test(self, rc):
        '''退出Test'''
        self.logger.info('Exit the test...')
        sys.exit(rc)

    def reset_test(self, rc):
        '''重置Test'''
        self.logger.info('Reset the test...')
        self.pairs.clear()

    def get_pairs(self):
        '''获取Pairs'''
        self.logger.info('Get the pairs...')
        return self.pairs

    def check_error(self):
        '''检查是否存在timeout测试'''
        self.logger.info('Check the error log')
        with open('error.log') as f:
            lines = f.readlines()
            for line in lines:
                if 'attempt timed out' in line:
                    self.logger.error('The test timed out')
                    break


def parse_args():
    args_parser = ArgumentParser(
        description='Run ixia Chariot by call C API.')

    common_args_parser = args_parser.add_argument_group('Common options')
    common_args_parser.add_argument("--version", '-v', action='store_true')
    common_args_parser.add_argument("--test-type",
                                    help="RX/TX/TX_RX.")
    common_args_parser.add_argument("--net-check", action='store_true',
                                    help="Check the network.")
    common_args_parser.add_argument("--e1-ip",
                                    help="The ip list of endpoint1.")
    common_args_parser.add_argument("--e2-ip",
                                    help="The ip of endpoint2.")
    common_args_parser.add_argument("---max-wait", type=int,
                                    help="The max wait time,or force to stop.")
    common_args_parser.add_argument("--run-time", type=int,
                                    help="The run time of the script.")
    common_args_parser.add_argument("--num-cards", type=int,
                                    help="The cards number of the endpoint1.")
    common_args_parser.add_argument("--num-pairs", type=int,
                                    help="The pairs number.")
    common_args_parser.add_argument("--script-file",
                                    help="The script filepath.")
    common_args_parser.add_argument("--res-file",
                                    help="The result filename.")

    raw_args = args_parser.parse_args()
    return raw_args


def main():
    api = CHRTest()
    _ = api.initialize()
    args = parse_args()
    # print(args)
    if args.version:
        print('Python API wrapper version:',
              '.'.join([str(x) for x in __version__]))
        print('ixia Chariot Version:', api.get_version())
        return

    if args.e1_ip:
        Spec_CHR.e1_ip = args.e1_ip.split('/')
    if args.e2_ip:
        Spec_CHR.e2_ip = args.e2_ip
    if args.err_check:
        api.check_error()
        return
    if args.net_check:
        api.check_network(Spec_CHR.num_cards)
        return
    if args.test_type:
        Spec_CHR.test_type = args.test_type
    if args.network_type:
        Spec_CHR.network_type = args.network_type
    if args.max_wait:
        Spec_CHR.max_wait = args.max_wait
    if args.run_time:
        Spec_CHR.run_time = args.run_time
        Spec_CHR.max_wait = Spec_CHR.run_time + 30
    if args.num_cards:
        Spec_CHR.num_cards = args.num_cards
    if args.num_pairs:
        Spec_CHR.num_pairs = args.num_pairs
    if args.script_file:
        Spec_CHR.script_file = args.script_file
    if args.res_file:
        Spec_CHR.res_file = args.res_file

    print('Running...')
    #
    # api.SetConf_CHR_Mod(Spec_CHR.test_type,'info')
    #

    _ = api.initialize()

    test = api.create_test_new()
    #
    api.set_pairs_attribute(test)
    #
    # dgopts = api.GetDGOpts(test)
    # api.SetDgoptsRecvTimeout(dgopts, 2000)
    # api.SetDgoptsRetransTimeout(dgopts, 2000)
    #
    runopts = api.get_run_opts(test)
    # api.SetConnectTimeout(runopts, 1)
    # timeout = api.GetConnectTimeout(runopts)
    api.set_test_end(runopts, CHR_TEST_END_AFTER_FIXED_DURATION)
    api.set_test_duration(runopts, Spec_CHR.run_time)

    #
    api.start_test(test)
    api.wait_for_test(test)
    # api.get_pair_count(test)
    # api.get_pair_addr_e1(pair)
    # api.get_pair_addr_e2(pair)
    # api.get_pair_protocol(pair)
    # api.get_pair_script(pair)
    # api.get_pair_appl_script(pair)
    # api.get_pair_time_record_count(pair)
    #
    thr_all = 0.0
    thr_e1 = 0.0
    thr_e2 = 0.0
    thr_e1_tx = 0.0
    pairs = api.get_pairs()
    bytes_sent_e1_tx = []
    bytes_recv_e1_tx = []
    bytes_sent_e1_rx = []
    bytes_recv_e1_rx = []
    time_elapsed_max = 1.0
    pair_header_len = 14
    # card_header_len = 6
    for pair in pairs:
        #
        num = api.get_pair_time_record_count(pair)
        handle = api.get_pair_time_record(pair, num - 1)
        time_elapsed = api.get_pair_time_elapsed(handle)
        if time_elapsed > time_elapsed_max:
            time_elapsed_max = time_elapsed
        #
        cur_ip = api.get_pair_addr_e1(pair)
        comment = api.get_pair_comment(pair)
        pair_no = int(str(comment[pair_header_len:]))
        # card_no = int(str(comment[card_header_len]))
        #
        single_thr_no = Spec_CHR.num_pairs / Spec_CHR.num_cards / 2
        # thr_avg = api.get_pair_res_avg(pair, CHR_RESULTS_THROUGHPUT)
        sent_tmp = api.get_pair_bytes_sent_e1(pair)
        recv_tmp = api.get_pair_bytes_recv_e1(pair)
        if Spec_CHR.network_type == 'LAN':
            if cur_ip in Spec_CHR.e1_ip:
                # thr_e1 += string.atof(thr_avg)
                bytes_sent_e1_tx.append(sent_tmp)
                bytes_recv_e1_tx.append(recv_tmp)
            #
            else:
                # thr_e2 += string.atof(thr_avg)
                bytes_sent_e1_rx.append(sent_tmp)
                bytes_recv_e1_rx.append(recv_tmp)
        elif Spec_CHR.network_type == 'WAN':
            if cur_ip in Spec_CHR.e1_ip:
                # thr_e1 += string.atof(thr_avg)
                if Spec_CHR.test_type == 'TX':
                    bytes_sent_e1_tx.append(sent_tmp)
                    bytes_recv_e1_tx.append(recv_tmp)
                elif Spec_CHR.test_type == 'RX':
                    bytes_sent_e1_rx.append(sent_tmp)
                    bytes_recv_e1_rx.append(recv_tmp)
                else:
                    # TX
                    if ((pair_no-1)/single_thr_no) % 2 == 0:
                        bytes_sent_e1_tx.append(sent_tmp)
                        bytes_recv_e1_tx.append(recv_tmp)
                    # RX
                    else:
                        bytes_sent_e1_rx.append(sent_tmp)
                        bytes_recv_e1_rx.append(recv_tmp)
            else:
                pass
    #
    for card in range(Spec_CHR.num_cards):
        #
        if cur_ip in Spec_CHR.e1_ip:
            #
            for pair_no in range(len(bytes_sent_e1_tx)):
                thr_e1 += (float(str(bytes_sent_e1_tx[pair_no]))
                           + float(str(bytes_recv_e1_tx[pair_no])))
            #
            thr_e1_tx = thr_e1*8/1000000/time_elapsed_max
            #
            for pair_no in range(len(bytes_sent_e1_rx)):
                thr_e1 += (float(bytes_sent_e1_rx[pair_no])
                           + float(bytes_recv_e1_rx[pair_no]))
            #
            thr_e1 = thr_e1*8/1000000/time_elapsed_max
        else:
            #
            for pair_no in range(len(bytes_sent_e1_tx)):
                thr_e2 += (float(str(bytes_sent_e1_tx[pair_no]))
                           + float(str(bytes_recv_e1_tx[pair_no])))
            #
            for pair_no in range(len(bytes_sent_e1_rx)):
                thr_e2 += (float(bytes_sent_e1_rx[pair_no])
                           + float(bytes_recv_e1_rx[pair_no]))
            #
            thr_e2 = thr_e2*8/1000000/time_elapsed_max
    #
    thr_all = thr_e1 + thr_e2
    ret_list = [
        'AVG_All = {:.3f}Mbps'.format(thr_all),
        'AVG_E1 = {:.3f}Mbps'.format(thr_e1),
        'AVG_E2 = {:.3f}Mbps'.format(thr_e2),
        'AVG_E1_TX = {:.3f}Mbps'.format(thr_e1_tx)
    ]
    str_ret = ', '.join(ret_list)

    # 写入tmp文件
    f = open('tmp.txt', 'w')
    f.write(str_ret)
    f.close()

    # thr_avg = api.get_pair_res_avg(pair, CHR_RESULTS_THROUGHPUT)
    # thr_min = api.get_pair_res_min(pair, CHR_RESULTS_THROUGHPUT)
    # thr_max = api.get_pair_res_max(pair, CHR_RESULTS_THROUGHPUT)
    # api.get_pair_res_max(pair, CHR_RESULTS_RSSI_E1)
    api.set_saving_file(test, Spec_CHR.res_file)
    api.save_test(test)
    for pair in pairs:
        api.del_pair(pair)
    # 耗费时间
    api.del_test(test)
    # api.exit_test(-1)
    subprocess.call('taskkill /t /f /im python.exe')

    # test = api.create_test_new()
    # print('test', test)
    # pair = api.create_pair_new()
    # print('pair', pair)
    # print(api.version())
    # rc = api.set_pair_addr(pair, '192.168.100.1', '192.168.100.10')
    # print(rc)


def test1():
    api = CHRTest()
    rc = api.initialize()
    rc
    api.get_version()
    test_handle = api.create_test_new()

    api.CHR_test_load(test_handle, r'D:\Users\皓\Desktop\Tests\test1.tst')
    api.CHR_test_get_filename(test_handle)
    api.CHR_test_get_pair_count(test_handle)
    # ret = api.get_pair_protocol(pair_handle)

    api.wait_for_test(test_handle)
    for item in range(10):
        ret = api.CHR_test_query_stop(test_handle, 10)
        print(item, ret)



if __name__ == '__main__':
    test1()
