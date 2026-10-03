import os
import sys
import json
import argparse
import subprocess
from datetime import datetime


def find_repositories(root_dir):
    repos = []
    for name in sorted(os.listdir(root_dir)):
        path = os.path.join(root_dir, name)
        if os.path.isdir(path):
            repos.append(path)
    return repos


def run_test_script(test_script, repo_path, python_exec):
    cmd = [python_exec, test_script, "--repo", repo_path]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800
        )
        return {
            "repo": repo_path,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "status": "SUCCESS" if result.returncode == 0 else "FAILED",
        }
    except subprocess.TimeoutExpired as e:
        return {
            "repo": repo_path,
            "returncode": -1,
            "stdout": e.stdout or "",
            "stderr": e.stderr or "",
            "status": "TIMEOUT",
        }
    except Exception as e:
        return {
            "repo": repo_path,
            "returncode": -2,
            "stdout": "",
            "stderr": str(e),
            "status": "ERROR",
        }


def print_result(result):
    repo = result["repo"]
    status = result["status"]

    print("=" * 80)
    print(f"Repository : {repo}")
    print(f"Status     : {status}")
    print(f"ReturnCode : {result['returncode']}")

    if result["stdout"]:
        print("\n[STDOUT]")
        print(result["stdout"].rstrip())

    if result["stderr"]:
        print("\n[STDERR]")
        print(result["stderr"].rstrip())

    print()


def print_summary(results):
    total = len(results)
    success = sum(1 for r in results if r["status"] == "SUCCESS")
    failed = sum(1 for r in results if r["status"] == "FAILED")
    timeout = sum(1 for r in results if r["status"] == "TIMEOUT")
    error = sum(1 for r in results if r["status"] == "ERROR")

    print("\n" + "#" * 80)
    print("# SUMMARY")
    print("#" * 80)
    print(f"Total   : {total}")
    print(f"Success : {success}")
    print(f"Failed  : {failed}")
    print(f"Timeout : {timeout}")
    print(f"Error   : {error}")
    print()

    for r in results:
        print(f"[{r['status']:<7}] {r['repo']}")


def save_json(results, output_file):
    data = {
        "generated_at": datetime.now().isoformat(),
        "results": results,
    }
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Run single Maven test checker script against all repos under a directory."
    )
    parser.add_argument(
        "--root",
        required=True,
        help="Root directory containing multiple repositories"
    )
    parser.add_argument(
        "--script",
        required=True,
        help="Path to the previous script, e.g. run_single_maven_test.py"
    )
    parser.add_argument(
        "--output",
        default="all_repo_test_results.json",
        help="Path to save JSON result"
    )

    args = parser.parse_args()

    root_dir = os.path.abspath(args.root)
    test_script = os.path.abspath(args.script)

    if not os.path.isdir(root_dir):
        print(f"❌ Root directory not found: {root_dir}")
        sys.exit(1)

    if not os.path.isfile(test_script):
        print(f"❌ Test script not found: {test_script}")
        sys.exit(1)

    repos = find_repositories(root_dir)

    if not repos:
        print(f"❌ No repositories found under: {root_dir}")
        sys.exit(1)

    print(f"Found {len(repos)} repositories under: {root_dir}")
    print(f"Using test script: {test_script}")
    print()

    results = []
    python_exec = sys.executable

    for repo in repos:
        print(f"Running test for repo: {repo}")
        result = run_test_script(test_script, repo, python_exec)
        results.append(result)
        print_result(result)

    print_summary(results)
    save_json(results, args.output)
    print(f"\nResult JSON saved to: {os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()
