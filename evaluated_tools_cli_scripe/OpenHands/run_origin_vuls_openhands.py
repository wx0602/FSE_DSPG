#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path

try:
    import yaml
except ImportError:
    print("[ERROR] Missing dependency: pyyaml")
    print("Install with: pip install pyyaml")
    sys.exit(1)


def collect_target_ids(obj):
    target_ids = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "target_id":
                target_ids.append(v)
            else:
                target_ids.extend(collect_target_ids(v))
    elif isinstance(obj, list):
        for item in obj:
            target_ids.extend(collect_target_ids(item))
    return target_ids


def main():
    cases_file = Path(sys.argv[1] if len(sys.argv) > 1 else "cases.yaml")
    
    script_path = Path("./run_openhands_patch.sh")
    logs_dir = Path("logs")

    if not cases_file.exists():
        print(f"[ERROR] cases file not found: {cases_file}")
        sys.exit(1)

    if not script_path.exists():
        print(f"[ERROR] script not found: {script_path}")
        sys.exit(1)

    if not script_path.is_file():
        print(f"[ERROR] not a file: {script_path}")
        sys.exit(1)

    logs_dir.mkdir(parents=True, exist_ok=True)

    with cases_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    target_ids = collect_target_ids(data)

    target_ids = [str(tid) for tid in target_ids if tid is not None]

    if not target_ids:
        print("[WARN] No target_id found in cases.yaml")
        sys.exit(0)

    print(f"[INFO] Found {len(target_ids)} target_id(s)")

    success_ids = []
    failed_ids = []
    failed_detail = []

    for idx, target_id in enumerate(target_ids, 1):
        print("=" * 80)
        print(f"[INFO] ({idx}/{len(target_ids)}) Running target_id={target_id}")

        log_file = logs_dir / f"{target_id}.log"

        with log_file.open("w", encoding="utf-8") as lf:
            result = subprocess.run(
                [str(script_path), f"--target_id={target_id}"],
                stdout=lf,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )

        if result.returncode == 0:
            print(f"[OK] target_id={target_id} succeeded")
            print(f"[INFO] log saved to {log_file}")
            success_ids.append(target_id)
        else:
            print(f"[ERROR] target_id={target_id} failed, exit_code={result.returncode}")
            print(f"[INFO] log saved to {log_file}")
            failed_ids.append(target_id)
            failed_detail.append((target_id, result.returncode))

    print("\n" + "=" * 80)
    print("[SUMMARY]")
    print(f"Total   : {len(target_ids)}")
    print(f"Success : {len(success_ids)}")
    print(f"Failed  : {len(failed_ids)}")

    print("\n[SUCCESS target_id]")
    if success_ids:
        for tid in success_ids:
            print(f"  - {tid}")
    else:
        print("  (none)")

    print("\n[FAILED target_id]")
    if failed_detail:
        for tid, code in failed_detail:
            print(f"  - {tid} (exit_code={code})")
    else:
        print("  (none)")


if __name__ == "__main__":
    main()
