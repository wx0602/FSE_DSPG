import os
from pathlib import Path
import yaml


ISSUE_ROOT = Path("./VESTA_resource/issue/63_issues_2_track")
RESOURCE_ROOT = Path("./VESTA_resource/resource")
OUTPUT_YAML = Path("output.yaml")


def build_repo_path(md_file: Path) -> str:
    """
    Generate repo_path from md filename
    Rule:
    1. Remove .md suffix
    2. Split into two parts by the FIRST underscore
    3. Use both parts as two-level directory under resource
    """
    stem = md_file.stem

    if "_" not in stem:
        raise ValueError(f"Filename has no underscore, cannot parse two-level directory: {md_file.name}")

    first_part, second_part = stem.split("_", 1)

    repo_path = RESOURCE_ROOT / first_part / second_part
    return str(repo_path)


def collect_cases(issue_root: Path):
    cases = []

    for md_file in sorted(issue_root.glob("*.md")):
        repo_path = build_repo_path(md_file)
        case = {
            "repo_path": repo_path,
            "problem_statement_path": str(md_file)
        }
        cases.append(case)

    return cases


def main():
    data = {
        "defaults": {
            "model_name": "gpt-4o",
            "deployment_image": "python:3.12"
        },
        "cases": collect_cases(ISSUE_ROOT)
    }

    with open(OUTPUT_YAML, "w", encoding="utf-8") as f:
        yaml.dump(
            data,
            f,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False
        )

    print(f"YAML generated: {OUTPUT_YAML.resolve()}")


if __name__ == "__main__":
    main()

