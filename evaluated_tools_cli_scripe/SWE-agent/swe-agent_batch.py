#!/usr/bin/env python3
import os
import re
import sys
import shutil
import subprocess
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Missing PyYAML, install first: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


PATCH_PATTERN = re.compile(r"PATCH_FILE_PATH='([^']+)'")

def load_yaml(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def md_to_patch_name(md_path: str) -> str:
    md_name = Path(md_path).name
    if md_name.endswith(".md"):
        return md_name[:-3] + ".patch"
    return md_name + ".patch"

def run_one_case(model_name: str, repo_path: str, problem_statement_path: str, deployment_image: str, output_dir: Path):
    patch_name = md_to_patch_name(problem_statement_path)
    target_patch_path = output_dir / patch_name

    cmd = [
        "sweagent", "run",
        f"--agent.model.name={model_name}",
        f"--env.repo.path={repo_path}",
        f"--problem_statement.path={problem_statement_path}",
        f"--env.deployment.image={deployment_image}",
    ]

    print("=" * 80)
    print("Running command:")
    print(" ".join(cmd))
    print("=" * 80)

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )

    found_patch_path = None
    all_output = []

    assert process.stdout is not None
    for line in process.stdout:
        print(line, end="")
        all_output.append(line)

        match = PATCH_PATTERN.search(line)
        if match:
            found_patch_path = match.group(1)

    return_code = process.wait()

    if return_code != 0:
        print(f"[FAIL] sweagent exit code: {return_code}", file=sys.stderr)
        return False

    if not found_patch_path:
        print("[FAIL] PATCH_FILE_PATH not found in output", file=sys.stderr)
        return False

    src_patch = Path(found_patch_path)
    if not src_patch.exists():
        print(f"[FAIL] Patch file not found: {src_patch}", file=sys.stderr)
        return False

    output_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(src_patch, target_patch_path)

    print(f"[OK] Patch saved to: {target_patch_path}")
    return True


def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else "cases.yaml"
    config = load_yaml(config_path)

    defaults = config.get("defaults", {})
    model_name = defaults.get("model_name", "gpt-4o")
    deployment_image = defaults.get("deployment_image", "python:3.12")
    cases = config.get("cases", [])

    if not cases:
        print("No cases found in cases.yaml", file=sys.stderr)
        sys.exit(1)

    output_dir = Path.cwd() / "patch_origin"
    output_dir.mkdir(exist_ok=True)

    success = 0
    failed = 0

    for idx, case in enumerate(cases, start=1):
        print(f"\n########## Case {idx}/{len(cases)} ##########")

        repo_path = case["repo_path"]
        problem_statement_path = case["problem_statement_path"]

        ok = run_one_case(
            model_name=model_name,
            repo_path=repo_path,
            problem_statement_path=problem_statement_path,
            deployment_image=deployment_image,
            output_dir=output_dir,
        )

        if ok:
            success += 1
        else:
            failed += 1

    print("\n" + "#" * 80)
    print(f"Batch completed: Success {success}, Failed {failed}")
    print("#" * 80)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

