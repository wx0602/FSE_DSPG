#!/usr/bin/env python3
import subprocess
import time
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Missing dependency PyYAML, please install first: pip install pyyaml")
    sys.exit(1)


def load_cases(yaml_path: Path):
    if not yaml_path.exists():
        raise FileNotFoundError(f"File not found: {yaml_path}")

    with yaml_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict) or "cases" not in data:
        raise ValueError("Invalid YAML format: missing 'cases' field")

    cases = data["cases"]
    if not isinstance(cases, list):
        raise ValueError("Invalid YAML format: 'cases' must be a list")

    target_ids = []
    for i, item in enumerate(cases, start=1):
        if not isinstance(item, dict):
            print(f"Case {i} has invalid format, skipped: {item}")
            continue

        target_id = item.get("target_id")
        if not target_id:
            print(f"Case {i} is missing 'target_id', skipped")
            continue

        target_ids.append(str(target_id))

    return target_ids


def run_patch_workflow(target_id: str):
    cmd = [
        "./agentless/agentless_java/patch_workflow.sh",
        f"--target_id={target_id}",
    ]

    print(f"\nStarting execution: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    print(f"Return code: {result.returncode}")
    if result.stdout:
        print("stdout:")
        print(result.stdout.strip())
    if result.stderr:
        print("stderr:")
        print(result.stderr.strip())

    return result.returncode == 0


def main():
    yaml_path = Path("cases.yaml")

    try:
        target_ids = load_cases(yaml_path)
    except Exception as e:
        print(f"Failed to read YAML: {e}")
        sys.exit(1)

    if not target_ids:
        print("No executable target_id found")
        sys.exit(1)

    success_count = 0
    fail_count = 0

    for idx, target_id in enumerate(target_ids, start=1):
        print(f"\n========== [{idx}/{len(target_ids)}] target_id={target_id} ==========")

        ok = run_patch_workflow(target_id)
        if ok:
            success_count += 1
            print(f"target_id={target_id} executed successfully")
        else:
            fail_count += 1
            print(f"target_id={target_id} execution failed")

        if idx < len(target_ids):
            print("Sleeping for 5 seconds...")
            time.sleep(5)

    print("\n========== Execution Summary ==========")
    print(f"Total: {len(target_ids)}")
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")


if __name__ == "__main__":
    main()

