# -*- coding: utf-8 -*-
"""
Created on Fri Apr  2 15:33:19 2021

@author: 皓
"""
from pychariot import Chariot, RetureCode


def main():

    api = Chariot()
    ret = api.api_initialize()
    if not ret == RetureCode.CHR_OK:
        raise RuntimeError('Chariot api initialize error.')
    ret = api.api_get_version()
    print(ret)


if __name__ == '__main__':
    main()
