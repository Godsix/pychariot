# -*- coding: utf-8 -*-
from pychariot.chrapi_constant import (CHR_DETAIL_LEVEL_ALL, CHR_OK,
                                       CHR_NULL_HANDLE,
                                       CHR_OPERATION_FAILED,
                                       CHR_OBJECT_INVALID,
                                       CHR_APP_GROUP_INVALID,
                                       CHR_FALSE, CHR_TRUE,
                                       CHR_TIMED_OUT, CHR_PROTOCOL_TCP,
                                       CHR_TEST_END_AFTER_FIXED_DURATION,
                                       CHR_RESULTS_THROUGHPUT)


# 测试类型
test_type = 'TX'
rotating_platform = '192.168.1.136'
rotation_angle = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]
# pair设置

e1 = '172.28.100.80'

e2 = '172.28.100.93'

script = 'High_Performance_Throughput.scr'

pairs_conf = [
    (e1, e2, script),
    (e1, e2, script),
    (e1, e2, script),
    (e1, e2, script),
    (e1, e2, script),
    (e1, e2, script),
    (e1, e2, script),
    (e1, e2, script),
    (e1, e2, script),
    (e1, e2, script),
    (e1, e2, script),
    (e1, e2, script),
    (e1, e2, script),
    (e1, e2, script),
    (e1, e2, script),
    (e1, e2, script),
    (e1, e2, script),
    (e1, e2, script),
    (e1, e2, script),
    (e1, e2, script),
]
# Run 设置
runopts_conf = {
    'test_end': CHR_TEST_END_AFTER_FIXED_DURATION,
    'test_duration': 20,
}
# 超时时间（单位：s）
timeout = 1
# 最大超时时间（单位：s）
max_wait_time = 60
# 结果文件名称
# result_file = './Results/perf_test08012.tst'
result_file = 'result.xlsx'
