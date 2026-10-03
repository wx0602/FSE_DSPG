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
    cases_file = Path(sys.argv[1] if len(sys.argv) > 1 else "cases_track_2.yaml")
    
    script_path = Path("./run_openhands_patch_track_2.sh")
    logs_dir = Path("logs")

    if not cases_file.exists():
        print(f"[ERROR] Cases file not found: {cases_file}")
        sys.exit(1)

    if not script_path.exists():
        print(f"[ERROR] Script not found: {script_path}")
        sys.exit(1)

    if not script_path.is_file():
        print(f"[ERROR] Not a file: {script_path}")
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

        # Core modification: Real-time output and write to log
        with log_file.open("w", encoding="utf-8") as lf:
            # Start subprocess, read stdout/stderr pipe in real time
            process = subprocess.Popen(
                [str(script_path), f"--target_id={target_id}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Redirect stderr to stdout for unified processing
                text=True,
                bufsize=1,  # Line buffering, real-time output
                universal_newlines=True
            )

            # Read output in real time and write to both log and console
            for line in iter(process.stdout.readline, ''):
                # Print to console
                print(line, end='')
                # Write to log file
                lf.write(line)
                lf.flush()  # Flush buffer immediately to ensure real-time logging

            # Wait for process to finish and get return code
            process.wait()
            result = process

        if result.returncode == 0:
            print(f"\n[OK] target_id={target_id} succeeded")
            print(f"[INFO] Log saved to {log_file}")
            success_ids.append(target_id)
        else:
            print(f"\n[ERROR] target_id={target_id} failed, exit_code={result.returncode}")
            print(f"[INFO] Log saved to {log_file}")
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

