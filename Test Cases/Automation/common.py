# -*- coding: utf-8 -*-
"""Automation test common utilities — shared across all device scripts.

Import this module in test scripts under OYWW1100/ (or future device directories):
    import common
    from common import record, _identity_of, match_target

The module reads config.TARGET_IDENTITY and config.DEVICES from the shared
config.py in the parent Automation/ directory.
"""

import re
import sys
import os

# Ensure the Automation directory is on sys.path so we can import config
AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
if AUTOMATION_DIR not in sys.path:
    sys.path.insert(0, AUTOMATION_DIR)

import config


def _parse_target_identities():
    """Parse config.TARGET_IDENTITY (comma-separated) into a list of uppercase identities.
    
    Validates that every identity exists in config.DEVICES. Raises SystemExit if not.
    """
    raw = (config.TARGET_IDENTITY or "").strip()
    if not raw:
        return []
    ids = [s.strip().upper() for s in raw.split(",") if s.strip()]
    
    # 校验：所有目标 identity 必须在 DEVICES 中有定义
    defined = {c.get("identity", "").strip().upper() for c in config.DEVICES}
    undefined = [i for i in ids if i not in defined]
    if undefined:
        print(f"[common] 错误：TARGET_IDENTITY 中的设备未在 DEVICES 中定义: {undefined}", flush=True)
        print(f"[common] DEVICES 中已定义的 identity: {sorted(defined)}", flush=True)
        raise SystemExit(1)
    
    return ids


# 模块加载时解析并校验
TARGET_IDENTITIES = _parse_target_identities()


def record(results, name, ok, expect, actual):
    """Record a test result.
    
    ok: True=PASS, False=FAIL, None=SKIP/informational
    """
    status = "PASS" if ok is True else ("FAIL" if ok is False else "SKIP")
    results.append((name, status, expect, actual))


def _identity_of(name):
    """Extract 4-hex identity from broadcast name like 'OYWW1100(80F3)' -> '80F3'."""
    m = re.search(r"\(([0-9A-Fa-f]{4})\)", name or "")
    return m.group(1).upper() if m else None


def _find_config(identity):
    """Find the config.DEVICES entry for a given identity."""
    for c in config.DEVICES:
        if (c.get("identity") or "").strip().upper() == identity:
            return c
    return None


def match_target(devices, target_identity=None):
    """Match the first target device from scan results.
    
    Uses config.TARGET_IDENTITIES (parsed from comma-separated config.TARGET_IDENTITY)
    by default. Pass an explicit target_identity to override.
    
    Returns the first matching BLEDevice, or None if no match.
    """
    if target_identity is not None:
        targets = [target_identity.strip().upper()]
    else:
        targets = TARGET_IDENTITIES if isinstance(TARGET_IDENTITIES, list) else [TARGET_IDENTITIES]
    
    for tid in targets:
        cfg = _find_config(tid)
        if cfg is None:
            continue
        mac = (cfg.get("mac") or "").strip().upper()
        for d in (devices or []):
            addr = (getattr(d, 'Address', '') or '').upper()
            name = getattr(d, 'Name', '') or ''
            if mac and addr == mac:
                return d
            if _identity_of(name) == tid:
                return d
    return None