# -*- coding: utf-8 -*-
"""ASYNC-FUNC-005：asyncSetParam 设置参数成功，返回 OK，同步 getParam 可验证。

对应用例：09_异步接口.md -> ASYNC-FUNC-005
可自动化：auto（需待测设备上电在范围内）

前置条件：
  - 主机(电脑)：蓝牙已开启
  - 待测设备：OYWW1100 上电、在范围内

流程：
  1) 确认设备开机 -> 按回车
  2) scan 匹配 OYWW1100 -> requireSensor
  3) await sensor.asyncConnect() -> 到达 Ready
  4) await sensor.asyncInit(20, 1000)
  5) await sensor.asyncSetParam("NTF_EMG", "ON") -> 断言返回 "OK"
  6) 同步 getParam("NTF") 校验 -> 应包含 "EMG"
  7) await sensor.asyncSetParam("NTF_EMG", "OFF") -> 断言返回 "OK"
  8) 同步 getParam("NTF") 校验 -> EMG 应为 OFF
"""

import asyncio
import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUTOMATION_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
sys.path.insert(0, AUTOMATION_DIR)

from sensor import *
import config
from common import record, _identity_of, match_target


def _parse_pipe(s):
    """把 "KEY|VALUE|KEY|VALUE|..." 解析成 {KEY: VALUE}。"""
    out = {}
    if not s:
        return out
    parts = s.split("|")
    for i in range(0, len(parts) - 1, 2):
        out[parts[i]] = parts[i + 1]
    return out


async def main_async():
    ctrl = SensorControllerInstance

    print("=" * 60, flush=True)
    print("ASYNC-FUNC-005 asyncSetParam 设置参数成功，返回 OK，同步 getParam 可验证", flush=True)
    print("=" * 60, flush=True)
    print(f"sdk version = {ctrl.getVersion()}", flush=True)
    print(f"ble backend = {ctrl.getBLEBackendName()}", flush=True)

    print("\n[前置条件]", flush=True)
    print("  - 主机(电脑)：蓝牙已开启", flush=True)
    print("  - 待测设备：OYWW1100 上电、在范围内", flush=True)

    input("\n>>> [人工操作] 请确认待测设备 OYWW1100 已【开机】且在范围内，完成后按回车继续 ...")

    results = []

    # 环境检查
    is_enable = ctrl.isEnable
    print(f"\n[环境检查] SensorController.isEnable = {is_enable}", flush=True)
    if is_enable is not True:
        print("[跳过] 前置条件不满足：电脑蓝牙未开启。请先开启【电脑】蓝牙后重跑。", flush=True)
        ctrl.terminate()
        return

    # 扫描匹配
    print(f"\n[扫描] await ctrl.asyncScan({config.SCAN_TIMEOUT_MS}) ...", flush=True)
    try:
        devices = await ctrl.asyncScan(config.SCAN_TIMEOUT_MS)
    except Exception as e:
        devices = None
        print(f"[扫描] 抛异常 {type(e).__name__}: {e}", flush=True)
    target = match_target(devices)

    if target is None:
        print("[FAIL] 未匹配到 config 中启用的设备", flush=True)
        record(results, "scan 匹配到目标设备", False, "scan 返回含目标设备", "未匹配到目标")
        ctrl.terminate()
        return

    name = getattr(target, 'Name', '?')
    addr = getattr(target, 'Address', '?')
    print(f"[扫描] 目标设备: {name} {addr}", flush=True)
    record(results, "scan 匹配到目标设备", True, "scan 返回含目标设备", f"匹配到 {name} {addr}")

    # requireSensor
    sensor = ctrl.requireSensor(target)
    if sensor is None:
        print("[FAIL] SensorController.requireSensor 返回 None", flush=True)
        record(results, "requireSensor 返回 SensorProfile", False, "返回 SensorProfile", "返回 None")
        ctrl.terminate()
        return
    record(results, "requireSensor 返回 SensorProfile", isinstance(sensor, SensorProfile),
           "返回 SensorProfile", f"返回 {type(sensor).__name__}")

    # asyncConnect
    print("\n[异步连接] await sensor.asyncConnect() ...", flush=True)
    try:
        ok = await sensor.asyncConnect()
    except Exception as e:
        ok = False
        print(f"[异步连接] 抛异常 {type(e).__name__}: {e}", flush=True)
    if ok is not True:
        print("[FAIL] asyncConnect 失败，无法继续测试", flush=True)
        record(results, "asyncConnect 返回 True", ok is True,
               "asyncConnect() 返回 True", f"asyncConnect() -> {ok}")
        ctrl.terminate()
        return
    record(results, "asyncConnect 返回 True", ok is True,
           "asyncConnect() 返回 True", f"asyncConnect() -> {ok}")

    # 等待 Ready
    t0 = time.time()
    while time.time() - t0 < 15 and sensor.deviceState != DeviceStateEx.Ready:
        time.sleep(0.2)
    state = sensor.deviceState
    ready = (state == DeviceStateEx.Ready)
    print(f"[检查1] 连接后 deviceState = {state}", flush=True)
    record(results, "asyncConnect 后 deviceState==Ready", ready,
           "deviceState == DeviceStateEx.Ready", f"deviceState == {state}")

    if not ready:
        print("[FAIL] 未到达 Ready，无法继续", flush=True)
        try:
            await sensor.asyncDisconnect()
        except Exception:
            pass
        ctrl.terminate()
        return

    # asyncInit
    print("\n[异步初始化] await sensor.asyncInit(20, 1000) ...", flush=True)
    try:
        ok_init = await sensor.asyncInit(20, 1000)
    except Exception as e:
        ok_init = False
        print(f"[异步初始化] 抛异常 {type(e).__name__}: {e}", flush=True)
    print(f"[异步初始化] sensor.asyncInit(20, 1000) -> {ok_init}", flush=True)
    record(results, "asyncInit 返回 True", ok_init is True,
           "asyncInit(20, 1000) 返回 True", f"asyncInit() -> {ok_init}")

    # ---- asyncSetParam ON ----
    print("\n[异步设置-ON] await sensor.asyncSetParam('NTF_EMG', 'ON') ...", flush=True)
    try:
        r_on = await sensor.asyncSetParam("NTF_EMG", "ON")
    except Exception as e:
        r_on = f"抛异常 {type(e).__name__}: {e}"
        print(f"[异步设置-ON] 抛异常 {type(e).__name__}: {e}", flush=True)
    print(f"[异步设置-ON] sensor.asyncSetParam('NTF_EMG', 'ON') -> {r_on!r}", flush=True)
    record(results, "asyncSetParam('NTF_EMG', 'ON') 返回 'OK'", r_on == "OK",
           "asyncSetParam 返回 'OK'", f"asyncSetParam() -> {r_on!r}")

    # 同步 getParam 验证 ON
    print("\n[同步验证-ON] getParam('NTF') ...", flush=True)
    try:
        ntf_str_on = sensor.getParam("NTF")
    except Exception as e:
        ntf_str_on = ""
        print(f"[同步验证-ON] 抛异常 {type(e).__name__}: {e}", flush=True)
    ntf_on = _parse_pipe(ntf_str_on)
    v_on = ntf_on.get("NTF_EMG", "<缺失>")
    print(f"[同步验证-ON] getParam('NTF') 中 NTF_EMG = {v_on}", flush=True)
    record(results, "getParam('NTF') 中 NTF_EMG 为 ON", v_on == "ON",
           "NTF_EMG == 'ON'", f"NTF_EMG = {v_on!r}")

    # ---- asyncSetParam OFF ----
    print("\n[异步设置-OFF] await sensor.asyncSetParam('NTF_EMG', 'OFF') ...", flush=True)
    try:
        r_off = await sensor.asyncSetParam("NTF_EMG", "OFF")
    except Exception as e:
        r_off = f"抛异常 {type(e).__name__}: {e}"
        print(f"[异步设置-OFF] 抛异常 {type(e).__name__}: {e}", flush=True)
    print(f"[异步设置-OFF] sensor.asyncSetParam('NTF_EMG', 'OFF') -> {r_off!r}", flush=True)
    record(results, "asyncSetParam('NTF_EMG', 'OFF') 返回 'OK'", r_off == "OK",
           "asyncSetParam 返回 'OK'", f"asyncSetParam() -> {r_off!r}")

    # 同步 getParam 验证 OFF
    print("\n[同步验证-OFF] getParam('NTF') ...", flush=True)
    try:
        ntf_str_off = sensor.getParam("NTF")
    except Exception as e:
        ntf_str_off = ""
        print(f"[同步验证-OFF] 抛异常 {type(e).__name__}: {e}", flush=True)
    ntf_off = _parse_pipe(ntf_str_off)
    v_off = ntf_off.get("NTF_EMG", "<缺失>")
    print(f"[同步验证-OFF] getParam('NTF') 中 NTF_EMG = {v_off}", flush=True)
    record(results, "getParam('NTF') 中 NTF_EMG 为 OFF", v_off == "OFF",
           "NTF_EMG == 'OFF'", f"NTF_EMG = {v_off!r}")

    # 清理
    try:
        await sensor.asyncDisconnect()
    except Exception as e:
        print(f"[断开] 抛异常 {type(e).__name__}: {e}", flush=True)

    # ---- 汇总 ----
    print("\n" + "=" * 60, flush=True)
    print("测试结果汇总", flush=True)
    print("=" * 60, flush=True)
    all_pass = True
    for rname, status, expect, actual in results:
        if status == "PASS":
            print(f"  [PASS] {rname}（实际: {actual}）", flush=True)
        else:
            print(f"  [FAIL] {rname}", flush=True)
            print(f"         期待: {expect}", flush=True)
            print(f"         实际: {actual}", flush=True)
        if status != "PASS":
            all_pass = False

    print("\n结论: " + ("PASS" if all_pass else "FAIL"), flush=True)
    ctrl.terminate()


if __name__ == "__main__":
    asyncio.run(main_async())