# -*- coding: utf-8 -*-
"""
Created on Fri Dec 24 10:23:11 2021

@author: 皓
"""
import os.path as osp
import sys
import platform
from argparse import ArgumentParser
from subprocess import call
from rpcpy32.server import PYTHON
DIR = osp.dirname(__file__)
if DIR not in sys.path:
    sys.path.append(DIR)


PY32 = PYTHON


def argument_parse():
    parser = ArgumentParser()
    parser.add_argument("--call", '-c', action='store_true')
    return parser.parse_args()


def test_chrapi():
    from pychariot.const import CHR_DETAIL_LEVEL
    from pychariot.chrapi import LocalCHRAPI
    chrapis = LocalCHRAPI()
    # chrapis = CHRAPI(r'D:\Users\皓\Desktop\IxChariot')

    print(chrapis.CHR_api_initialize(CHR_DETAIL_LEVEL.CHR_DETAIL_LEVEL_ALL))
    print(chrapis.CHR_api_get_version())
    print(chrapis.CHR_api_get_return_msg(113))
    print(chrapis.CHR_api_get_port_mgmt_ip_list())


def test_chariot():
    from pychariot import Chariot
    chariot = Chariot()
    chariot.connect('localhost')
    print(chariot.api_initialize())
    print(chariot.api_get_version())


def test_win32():
    arch = platform.architecture()[0]
    if '64bit' == arch:
        args = argument_parse()
        if args.call:
            print('请勿循环启动')
            return
        cmd = [PY32, __file__, '-c']
        call(cmd)
    else:
        test_chrapi()


def main():
    test_chariot()


if __name__ == '__main__':
    main()
