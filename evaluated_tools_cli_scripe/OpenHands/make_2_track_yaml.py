from pathlib import Path
import yaml

# Directory to scan
input_dir = Path("./VESTA_resource/issue/63_issues_2_track")

# Output YAML file
output_file = Path("output.yaml")

cases = []

for file_path in input_dir.iterdir():
    if file_path.is_file():
        cases.append({"target_id": file_path.stem})

data = {"cases": cases}

with output_file.open("w", encoding="utf-8") as f:
    yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)

print(f"YAML file generated: {output_file}")

