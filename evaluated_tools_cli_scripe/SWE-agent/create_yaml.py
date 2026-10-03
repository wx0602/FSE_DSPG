#!/usr/bin/env python3
import os
import yaml

repo_root = "./VESTA_resource/resource/origin"
issue_root = "./VESTA_resource/issue/issue19"

output_file = "cases.yaml"

repos = []

# Scan all repository directories
for name in os.listdir(repo_root):
    full_path = os.path.join(repo_root, name)
    if os.path.isdir(full_path):
        repos.append(name)

# Sort alphabetically
repos.sort()

cases = []

for repo in repos:
    repo_path = os.path.join(repo_root, repo)

    problem_statement_path = os.path.join(
        issue_root,
        f"origin_{repo}.md"
    )

    cases.append({
        "repo_path": repo_path,
        "problem_statement_path": problem_statement_path
    })

data = {
    "cases": cases
}

with open(output_file, "w") as f:
    yaml.dump(data, f, sort_keys=False)

print(f"Generated {len(cases)} cases -> {output_file}")

