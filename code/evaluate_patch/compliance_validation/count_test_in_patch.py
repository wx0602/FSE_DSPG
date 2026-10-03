import os
import re
import sys

def patch_contains_test(patch_path):
    diff_git_pattern = re.compile(r"^diff --git a/(.*?) b/(.*?)$")
    plus_pattern = re.compile(r"^\+\+\+ (?:a/|b/)?(.*)$")
    minus_pattern = re.compile(r"^--- (?:a/|b/)?(.*)$")

    paths = set()

    with open(patch_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.rstrip("\n")

            m = diff_git_pattern.match(line)
            if m:
                paths.add(m.group(1))
                paths.add(m.group(2))
                continue

            m = plus_pattern.match(line)
            if m:
                path = m.group(1)
                if path != "/dev/null":
                    paths.add(path)
                continue

            m = minus_pattern.match(line)
            if m:
                path = m.group(1)
                if path != "/dev/null":
                    paths.add(path)
                continue

    return any("test" in path.lower() for path in paths)


def count_patches_with_test(folder_path):
    total_patch_files = 0
    matched_patch_files = 0

    for root, _, files in os.walk(folder_path):
        for file_name in files:
            if file_name.endswith(".patch") or file_name.endswith(".diff"):
                total_patch_files += 1
                patch_path = os.path.join(root, file_name)

                if patch_contains_test(patch_path):
                    matched_patch_files += 1
                    print(f"[HIT] {patch_path}")

    print("-" * 40)
    print(f"Total patch files: {total_patch_files}")
    print(f"Patches containing test paths: {matched_patch_files}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <patch_folder>")
        sys.exit(1)

    folder = sys.argv[1]
    count_patches_with_test(folder)

