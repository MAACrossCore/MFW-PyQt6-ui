"""Scan MuMu 12 instances via MuMuManager (shared by refresh / ensure / picker)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_AGENT_DIR = Path(__file__).resolve().parent
if str(_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_DIR))


def _em():
    import ensure_mumu as em

    return em


def _normalize_info(index: int, info: dict[str, Any]) -> dict[str, Any]:
    data = dict(info)
    data["index"] = int(data.get("index", index))
    return data


def list_instances(manager: Path | None = None) -> list[tuple[int, dict[str, Any]]]:
    """Return [(index, info), ...] for existing MuMu VMs.

    Prefer `MuMuManager info -v all` (one call). Fall back to scanning 0..9.
    """
    em = _em()
    if manager is None:
        _root, manager, _adb = em.find_mumu()
    if not manager or not Path(manager).is_file():
        return []

    code, output, _ = em.run([manager, "info", "-v", "all"], timeout=20)
    if code == 0 and output:
        try:
            payload = json.loads(output)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict) and payload:
            items: list[tuple[int, dict[str, Any]]] = []
            # Single-instance shape
            if payload.get("created_timestamp") or "adb_port" in payload or "name" in payload:
                if payload.get("error_code", 0) == 0:
                    idx = int(payload.get("index", 0))
                    items.append((idx, _normalize_info(idx, payload)))
                return items
            for key, emu in payload.items():
                if not isinstance(emu, dict):
                    continue
                if emu.get("error_code", 0) not in (0, None):
                    continue
                try:
                    idx = int(emu.get("index", key))
                except (TypeError, ValueError):
                    continue
                items.append((idx, _normalize_info(idx, emu)))
            items.sort(key=lambda item: item[0])
            if items:
                return items

    found: list[tuple[int, dict[str, Any]]] = []
    for index in range(10):
        info = _em().manager_info(manager, index)
        if info:
            found.append((index, _normalize_info(index, info)))
    return found


def format_label(index: int, info: dict[str, Any]) -> str:
    name = str(info.get("name") or f"实例{index}").strip() or f"实例{index}"
    if info.get("is_android_started"):
        status = "运行中"
    elif info.get("is_process_started"):
        status = "进程已起"
    else:
        status = "未启动"
    host = info.get("adb_host_ip") or "127.0.0.1"
    port = info.get("adb_port")
    adb = f"{host}:{port}" if port else "无ADB"
    return f"#{index} {name} | {status} | {adb}"


def build_option_cases(instances: list[tuple[int, dict[str, Any]]]) -> list[dict[str, str]]:
    cases = [{"name": "自动", "label": "自动（优先已启动实例）"}]
    for index, info in instances:
        cases.append({"name": str(index), "label": format_label(index, info)})
    return cases
