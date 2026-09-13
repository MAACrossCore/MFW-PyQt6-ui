"""Console picker: choose a MuMu instance and lock it into MFW config.

Does not require restarting MFW for ensure_mumu to obey the choice
(writes mumu_runtime.json user_selected + current config MuMu实例).
Dropdown labels still need refresh_mumu_options + MFW restart.
"""

from __future__ import annotations

import sys
from pathlib import Path

_AGENT_DIR = Path(__file__).resolve().parent
if str(_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_DIR))

import ensure_mumu as em
import mumu_scan


def main() -> int:
    em._configure_stdio_utf8()
    root, manager, adb = em.find_mumu()
    if not manager or not adb:
        print("未找到 MuMu 12 / adb")
        return 1

    instances = mumu_scan.list_instances(manager)
    if not instances:
        print("没有可用的 MuMu 实例")
        return 1

    print("可用 MuMu 实例：")
    print("  0) 自动（优先已启动）")
    for i, (index, info) in enumerate(instances, start=1):
        print(f"  {i}) {mumu_scan.format_label(index, info)}")

    raw = input("请输入序号并回车：").strip()
    if raw == "0":
        em.save_json(
            em.CACHE_FILE,
            {
                **em.load_json(em.CACHE_FILE),
                "root": str(root),
                "user_selected": False,
                "vm_index": None,
            },
        )
        em.update_mfw_mumu_option("自动")
        print("已设为自动")
        return 0

    try:
        choice = int(raw)
    except ValueError:
        print("无效输入")
        return 1
    if choice < 1 or choice > len(instances):
        print("超出范围")
        return 1

    index, info = instances[choice - 1]
    host = info.get("adb_host_ip") or "127.0.0.1"
    port = info.get("adb_port")
    serial = f"{host}:{port}" if port else ""

    em.save_json(
        em.CACHE_FILE,
        {
            "root": str(root),
            "vm_index": index,
            "adb_serial": serial,
            "user_selected": True,
            "display": mumu_scan.format_label(index, info),
        },
    )
    em.update_mfw_mumu_option(str(index))
    em.update_mfw_controller(
        adb=adb,
        serial=serial or f"127.0.0.1:{16384 + int(index) * 32}",
        root=root,
        index=index,
        name=str(info.get("name") or f"实例{index}"),
    )

    print(f"已选择：{mumu_scan.format_label(index, info)}")
    print("下次点开始时，ensure_mumu 会优先使用该实例。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
