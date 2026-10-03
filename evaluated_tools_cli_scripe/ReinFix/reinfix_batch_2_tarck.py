#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Missing dependency PyYAML, install first: pip install pyyaml")
    sys.exit(1)


REINFIX_DIR = Path("./Reinfix/reinfix")
CASES_FILE = REINFIX_DIR / "cases.yaml"
STATE_FILE = REINFIX_DIR / "batch_run_state.json"


def load_cases(yaml_file: Path):
    if not yaml_file.exists():
        raise FileNotFoundError(f"Cases file not found: {yaml_file}")

    with open(yaml_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    raw_cases = data.get("cases", [])
    if not isinstance(raw_cases, list):
        raise ValueError("Invalid cases.yaml format: 'cases' must be a list")

    cases = []
    for idx, item in enumerate(raw_cases):
        if not isinstance(item, dict):
            raise ValueError(f"Case {idx + 1} is not a dictionary: {item}")

        target_id = item.get("target_id")
        buggy = item.get("buggy", item.get("bubby"))

        if not target_id or not buggy:
            raise ValueError(
                f"Case {idx + 1} missing target_id or buggy/bubby: {item}"
            )

        cases.append({
            "index": idx,
            "target_id": str(target_id).strip(),
            "buggy": str(buggy).strip(),
        })

    return cases


def load_state():
    if not STATE_FILE.exists():
        return {
            "last_run_cases_file": str(CASES_FILE),
            "completed_indexes": [],
            "failed_index": None,
            "failed_command": None,
            "last_status": None,
            "updated_at": None,
        }

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def build_command(case):
    return [
        "./reinfix_workflow.sh",
        f"--target_id={case['target_id']}",
        f"--buggy={case['buggy']}",
    ]


def case_name(case):
    return f"[{case['index']}] target_id={case['target_id']}, buggy={case['buggy']}"


def print_summary(cases, state):
    completed = set(state.get("completed_indexes", []))
    failed_index = state.get("failed_index")

    print("\n========== PROGRESS SUMMARY ==========")
    print(f"State file: {STATE_FILE}")

    print("\nCompleted cases:")
    any_completed = False
    for c in cases:
        if c["index"] in completed:
            print(f"  {case_name(c)}")
            any_completed = True
    if not any_completed:
        print("  (none)")

    print("\nFailed case:")
    if failed_index is not None:
        failed_case = next((c for c in cases if c["index"] == failed_index), None)
        if failed_case:
            print(f"  {case_name(failed_case)}")
            print(f"  Failed command: {state.get('failed_command')}")
        else:
            print(f"  index={failed_index} (not found in current cases.yaml)")
    else:
        print("  (none)")

    print("\nPending cases:")
    any_pending = False
    for c in cases:
        if c["index"] not in completed and c["index"] != failed_index:
            print(f"  {case_name(c)}")
            any_pending = True
    if not any_pending:
        print("  (none)")
    print("======================================\n")


def resolve_start_index(cases, args, state):
    index_set = {c["index"] for c in cases}
    target_id_map = {c["target_id"]: c["index"] for c in cases}

    if args.case_index is not None:
        if args.case_index not in index_set:
            raise ValueError(f"--case-index={args.case_index} does not exist")
        return args.case_index

    if args.target_id is not None:
        if args.target_id not in target_id_map:
            raise ValueError(f"--target-id={args.target_id} not found in cases.yaml")
        return target_id_map[args.target_id]

    if args.resume:
        failed_index = state.get("failed_index")
        if failed_index is not None:
            if failed_index not in index_set:
                raise ValueError(
                    f"Failed index {failed_index} in state not in current cases.yaml"
                )
            return failed_index

        completed = set(state.get("completed_indexes", []))
        for c in cases:
            if c["index"] not in completed:
                return c["index"]

        raise ValueError("No cases to resume, all appear completed")

    return 0


def reset_state_if_requested(args, state):
    if args.reset:
        state = {
            "last_run_cases_file": str(CASES_FILE),
            "completed_indexes": [],
            "failed_index": None,
            "failed_command": None,
            "last_status": None,
            "updated_at": None,
        }
        save_state(state)
    return state


def run_one_case(case, dry_run=False):
    cmd = build_command(case)
    cmd_str = " ".join(cmd)

    print(f"[RUN ] {case_name(case)}")
    print(f"[CMD ] {cmd_str}")

    if dry_run:
        print("[DRY ] Skip actual execution")
        return 0, cmd_str

    result = subprocess.run(
        cmd,
        cwd=REINFIX_DIR,
    )
    return result.returncode, cmd_str


def main():
    parser = argparse.ArgumentParser(description="Batch run reinfix_workflow.sh")
    parser.add_argument("--resume", action="store_true", help="Resume from last failure")
    parser.add_argument("--case-index", type=int, help="Start from specified case index")
    parser.add_argument("--target-id", type=str, help="Start from specified target_id")
    parser.add_argument("--only-one", action="store_true", help="Run only the starting case")
    parser.add_argument("--reset", action="store_true", help="Clear all progress state")
    parser.add_argument("--status", action="store_true", help="Show progress only, no execution")
    parser.add_argument("--dry-run", action="store_true", help="Print commands only")
    args = parser.parse_args()

    try:
        cases = load_cases(CASES_FILE)
        state = load_state()
        state = reset_state_if_requested(args, state)

        if args.status:
            print_summary(cases, state)
            return

        start_index = resolve_start_index(cases, args, state)

        print(f"[INFO] Total cases: {len(cases)}")
        print(f"[INFO] Start index: {start_index}")

        started = False
        for case in cases:
            idx = case["index"]

            if idx < start_index:
                continue

            started = True
            return_code, cmd_str = run_one_case(case, dry_run=args.dry_run)

            state["last_run_cases_file"] = str(CASES_FILE)
            state["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

            if return_code == 0:
                completed = set(state.get("completed_indexes", []))
                completed.add(idx)
                state["completed_indexes"] = sorted(completed)
                state["failed_index"] = None
                state["failed_command"] = None
                state["last_status"] = "success"
                save_state(state)

                print(f"[ OK ] {case_name(case)}")

                if args.only_one:
                    print("[INFO] --only-one specified, exit after this case")
                    break
            else:
                state["failed_index"] = idx
                state["failed_command"] = cmd_str
                state["last_status"] = "failed"
                save_state(state)

                print(f"[FAIL] Failed case: {case_name(case)}")
                print(f"[FAIL] Failed command:\n{cmd_str}")
                print(f"[FAIL] Return code: {return_code}")
                print("\n[INFO] Failure saved, use --resume to continue later")
                break

        if not started:
            print("[INFO] No matching cases to execute")
            return

        print_summary(cases, state)

    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

