# -*- coding: utf-8 -*-
"""
Created on Fri Apr  2 11:10:47 2021

@author: 皓
"""
import pywifi
from pywifi import const  # 引入一个常量
import time


def get_wifi_signal(ssid):
    wifi = pywifi.PyWiFi()
    # 起始获得的是列表，列表中存放的是无线网卡对象,
    # 可能一台电脑有多个网卡，请注意选择
    ifaces = wifi.interfaces()
    if len(ifaces) == 0:
        print('无线网卡数量为0，请检查环境。')
        return
    iface_index = 0
    if len(ifaces) > 1:
        print('无线网卡数量为 {}，请选择无线网卡：'.format(len(ifaces)))
        indexs = []
        for index, item in enumerate(ifaces):
            print('{}.{};'.foramt(index, item.name))
            indexs.append(index)
        while True:
            ret = input('请选择序号：')
            if not ret.isdigit():
                print('请输入数字。')
                continue
            ifaces_index = int(ret)
            if ifaces_index not in indexs:
                print('请输入正确序号。')
                continue
            break
    # 如果网卡选择错了，程序会卡住，不出结果
    iface = ifaces[iface_index]
    iface.scan()
    results = iface.scan_results()
    for item in results:
        if item.ssid == ssid:
            print(item.signal)
            break
    else:
        print('没有搜索到信号，SSID：{}'.format(ssid))
        for item in results:
            print(item.ssid, item.signal)
        return


def wifi_connect(ssid, password=None):
    wifi = pywifi.PyWiFi()
    iface = wifi.interfaces()[0]
    if iface.status() == const.IFACE_CONNECTED:
        connection = iface.current_connection()
        if connection.ssid == ssid:
            print('已连接')
            return
    iface.scan()
    results = iface.scan_results()
    for item in results:
        if item.ssid == ssid:
            break
    else:
        print('没有搜索到信号，SSID：{}'.format(ssid))
        return
    iface.disconnect()
    retry = 10
    while not iface.status() == const.IFACE_DISCONNECTED and retry > 0:
        time.sleep(0.1)
        retry -= 1
    profiles = iface.network_profiles()
    for profile in profiles:
        if profile.ssid == ssid:
            target_profile = profile
            break
    else:
        if not password:
            print('WiFi密码为空.')
            return
        profile = pywifi.Profile()  # 创建WiFi连接文件
        profile.ssid = ssid  # WiFi的ssid，即wifi的名称
        profile.key = password  # WiFi密码
        # WiFi的加密类型，现在一般的wifi都是wpa2psk
        profile.akm.append(const.AKM_TYPE_WPA2PSK)
        profile.auth = const.AUTH_ALG_OPEN  # 开放网卡
        profile.cipher = const.CIPHER_TYPE_CCMP  # 加密单元
        target_profile = iface.add_network_profile(profile)  # 设定新的连接文件
    iface.connect(target_profile)  # 连接WiFi
    retry = 3
    while not iface.status() == const.IFACE_CONNECTED and retry > 0:
        time.sleep(0.5)
        retry -= 1
    if iface.status() == const.IFACE_CONNECTED:
        print('连接成功')
        return True
    else:
        print('连接失败')
        return False


if __name__ == '__main__':
    get_wifi_signal('haoyue88')
