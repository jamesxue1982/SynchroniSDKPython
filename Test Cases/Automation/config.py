# -*- coding: utf-8 -*-
"""Smoke test 设备配置（支持多台设备）。

DEVICES 为设备列表，每台字段：
    name_prefix : 广播名前缀，从扫描结果按前缀匹配（如 "OB"、"OY"）
    mac         : 精确 MAC 地址（大写、含冒号）；非空时优先按 MAC 精确匹配
    identity    : 蓝牙地址后四位（如 "6C6B"，对应广播名 "OB6000C(6C6B)" 括号内部分）；
                  非空时按广播名后四位精确匹配，用于区分同前缀下的多台设备
    enabled     : True 参与本轮 smoke test，False 跳过

匹配优先级：mac > identity > name_prefix。
"""

# ---- 通用参数 ----
SCAN_TIMEOUT_MS = 5000              # 扫描时长（毫秒）
COLLECT_SECONDS = 5                 # 起流后采集时长（秒）
PACKAGE_SAMPLE_COUNT = 20           # init(packageSampleCount, ...)
POWER_REFRESH_INTERVAL_MS = 1000    # init(..., powerRefreshInterval)
MIN_SAMPLES = 1                     # 判定"收到数据"的最小样本数

# ---- 设备列表（支持多台）----
# 注意：如需暂时停用某台设备，请用 # 注释掉整段，或把 enabled 设为 False（不要用 ''' ''' 包裹）。
DEVICES = [
    {
        "name_prefix": "OB",
        "mac": "",
        "identity": "6C6B",
        "enabled": False,
    },

    {
         "name_prefix": "OYWW",
         "mac": "",
         "identity": "80F3",
         "enabled": True,
     }
]
