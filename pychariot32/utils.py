# -*- coding: utf-8 -*-
"""
Created on Tue Sep 20 09:39:55 2022

@author: 皓
"""
import os
import os.path as osp
from winreg import (HKEY_LOCAL_MACHINE, KEY_WOW64_32KEY, KEY_READ,
                    OpenKey, QueryValueEx)


class WinTools:
    APINAME = 'ChrApi.dll'
    REG_KEYS = (r"SOFTWARE\Ixia\IxChariot",
                r"SOFTWARE\Ixia Communications\IxChariot")

    @classmethod
    def get_install_path(cls):
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
    def get_install_version(cls):
        for reg_key in cls.REG_KEYS:
            try:
                with OpenKey(HKEY_LOCAL_MACHINE, reg_key,
                             access=KEY_READ | KEY_WOW64_32KEY) as key:
                    value, *_ = QueryValueEx(key, 'Version/Release')
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
            ixia_path = cls.get_install_path()
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


def test():
    print(WinTools.get_install_path())
    print(WinTools.get_install_version())


if __name__ == '__main__':
    test()
