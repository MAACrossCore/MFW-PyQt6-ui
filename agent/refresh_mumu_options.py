"""Refresh interface.json「MuMu实例」dropdown labels from live MuMu scan.

MFW loads interface.json at startup. After running this script, restart MFW
(or reopen it) so the PreTask / 启动游戏 options show the new labels.
"""

from __future__ import annotations

import sys
from pathlib import Path

_AGENT_DIR = Path(__file__).resolve().parent
if str(_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_DIR))

import ensure_mumu as em
import mumu_scan


INTERFACE_PATH = em.PROJECT_ROOT / "interface.json"


def main() -> int:
    em._configure_stdio_utf8()
    root, manager, adb = em.find_mumu()
    if not manager:
        print("未找到 MuMu 12（可设置 MUMU_HOME 后重试）")
        return 1

    instances = mumu_scan.list_instances(manager)
    if not instances:
        print(f"已找到 MuMu：{root}，但没有可用实例")
        return 1

    print(f"MuMu 安装目录：{root}")
    print(f"扫到 {len(instances)} 个实例：")
    for index, info in instances:
        print(f"  - {mumu_scan.format_label(index, info)}")

    data = em.load_json(INTERFACE_PATH)
    option = (data.get("option") or {}).get("MuMu实例")
    if not isinstance(option, dict):
        print("interface.json 缺少 option.MuMu实例")
        return 1

    option["cases"] = mumu_scan.build_option_cases(instances)
    option["default_case"] = option.get("default_case") or "自动"
    em.save_json(INTERFACE_PATH, data)

    em.save_json(
        em.CACHE_FILE,
        {
            **em.load_json(em.CACHE_FILE),
            "root": str(root),
            "adb_path": str(adb) if adb else "",
            "scanned": [
                {
                    "index": index,
                    "name": info.get("name"),
                    "label": mumu_scan.format_label(index, info),
                    "adb_port": info.get("adb_port"),
                    "is_android_started": bool(info.get("is_android_started")),
                    "is_process_started": bool(info.get("is_process_started")),
                }
                for index, info in instances
            ],
        },
    )

    print()
    print(f"已写入：{INTERFACE_PATH}")
    print("请关闭并重新打开 MFW，然后在「PreTask」或「启动游戏」里选 MuMu 实例。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
