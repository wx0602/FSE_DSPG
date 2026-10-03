#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import argparse
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("[ERROR] PyYAML is missing, please install first: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


def load_yaml(yaml_path: Path):
    """Load YAML configuration."""
    try:
        with yaml_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to read YAML: {e}")

    if not isinstance(data, dict):
        raise ValueError("YAML top-level must be a dictionary, e.g., containing 'targets' field")

    targets = data.get("targets")
    if not isinstance(targets, list):
        raise ValueError("YAML must contain a 'targets' list")

    normalized = []
    for i, item in enumerate(targets, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Item {i} in 'targets' must be a dictionary")

        target_id = item.get("target_id")
        poc_string = item.get("poc_string")
        poc_cmd = item.get("poc_cmd")

        if not target_id or not isinstance(target_id, str):
            raise ValueError(f"Item {i} in 'targets' is missing a valid 'target_id'")
        if not poc_string or not isinstance(poc_string, str):
            raise ValueError(f"Item {i} in 'targets' is missing a valid 'poc_string'")

        if poc_cmd is not None and not isinstance(poc_cmd, str):
            raise ValueError(f"'poc_cmd' for item {i} in 'targets' must be a string")

        normalized.append({
            "target_id": target_id,
            "poc_string": poc_string,
            "poc_cmd": poc_cmd,
        })

    return normalized


def find_repo_by_target_id(root_dir: Path, target_id: str):
    """
    Find repositories whose directory names contain the target_id under the root directory.
    Only searches the first-level subdirectories by default.
    """
    matches = []
    for p in root_dir.iterdir():
        if p.is_dir() and target_id in p.name:
            matches.append(p)

    return matches


def run_single(script_path: Path, repo_path: Path, poc_string: str, poc_cmd: str = None):
    """Invoke a single statistics script."""
    cmd = [
        sys.executable,
        str(script_path),
        "--repo",
        str(repo_path),
        "--poc_string",
        poc_string,
    ]

    if poc_cmd:
        cmd.extend(["--poc_cmd", poc_cmd])

    print(f"\n[INFO] Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    return result.returncode


def main():
    parser = argparse.ArgumentParser(
        description="Batch invoke Maven test statistics scripts based on YAML configuration"
    )
    parser.add_argument(
        "--dir",
        required=True,
        help="Root directory containing all Java repositories"
    )
    parser.add_argument(
        "--yaml",
        required=True,
        help="Input YAML configuration file"
    )
    parser.add_argument(
        "--script",
        default="count_poc.py",
        help="Path to the statistics script to be invoked, default: count_poc.py"
    )

    args = parser.parse_args()

    root_dir = Path(args.dir).resolve()
    yaml_path = Path(args.yaml).resolve()
    script_path = Path(args.script).resolve()

    if not root_dir.exists() or not root_dir.is_dir():
        print(f"[ERROR] --dir is not a valid directory: {root_dir}", file=sys.stderr)
        sys.exit(1)

    if not yaml_path.exists() or not yaml_path.is_file():
        print(f"[ERROR] --yaml file does not exist: {yaml_path}", file=sys.stderr)
        sys.exit(1)

    if not script_path.exists() or not script_path.is_file():
        print(f"[ERROR] --script file does not exist: {script_path}", file=sys.stderr)
        sys.exit(1)

    try:
        targets = load_yaml(yaml_path)
    except Exception as e:
        print(f"[ERROR] YAML parsing failed: {e}", file=sys.stderr)
        sys.exit(1)

    success_count = 0
    fail_count = 0
    skip_count = 0

    print(f"[INFO] Root directory: {root_dir}")
    print(f"[INFO] YAML file: {yaml_path}")
    print(f"[INFO] Statistics script: {script_path}")
    print(f"[INFO] Total tasks loaded: {len(targets)}")

    for idx, item in enumerate(targets, start=1):
        target_id = item["target_id"]
        poc_string = item["poc_string"]
        poc_cmd = item.get("poc_cmd")

        print(f"\n{'=' * 80}")
        print(f"[INFO] Task {idx}")
        print(f"[INFO] target_id  = {target_id}")
        print(f"[INFO] poc_string = {poc_string}")
        print(f"[INFO] poc_cmd    = {poc_cmd if poc_cmd else '<default>'}")

        matches = find_repo_by_target_id(root_dir, target_id)

        if not matches:
            print(f"[WARN] No repo matched target_id='{target_id}', skipping")
            skip_count += 1
            continue

        if len(matches) > 1:
            print(f"[WARN] Multiple matching repos found, will execute one by one:")
            for m in matches:
                print(f"       - {m}")

        for repo_path in matches:
            ret = run_single(
                script_path=script_path,
                repo_path=repo_path,
                poc_string=poc_string,
                poc_cmd=poc_cmd,
            )

            if ret == 0:
                success_count += 1
            else:
                fail_count += 1
                print(f"[ERROR] Execution failed, repo={repo_path.name}, return code={ret}")

    print(f"\n{'=' * 80}")
    print("[INFO] Batch execution completed")
    print(f"[INFO] Success count: {success_count}")
    print(f"[INFO] Failure count: {fail_count}")
    print(f"[INFO] Skip count: {skip_count}")


if __name__ == "__main__":
    main()


#python3 batch_run.py --dir /data/repos --yaml targets.yaml --script count_poc.py
