from pathlib import Path
import re
import argparse


def patch_contains_test_path(patch_file: Path) -> bool:
    """
    Check if a patch/diff file contains file paths with 'test' in them.
    """
    path_patterns = [
        re.compile(r"^(---|\+\+\+)\s+(.+)$"),
        re.compile(r"^diff --git\s+(.+?)\s+(.+)$"),
        re.compile(r"^rename from\s+(.+)$"),
        re.compile(r"^rename to\s+(.+)$"),
    ]

    try:
        with patch_file.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()

                for pattern in path_patterns:
                    match = pattern.match(line)
                    if not match:
                        continue

                    groups = match.groups()
                    for g in groups:
                        path_text = g.strip()

                        # Remove a/ b/ prefixes
                        if path_text.startswith("a/") or path_text.startswith("b/"):
                            path_text = path_text[2:]

                        if "test" in path_text.lower():
                            return True

        return False
    except Exception as e:
        print(f"Failed to read file: {patch_file}, error: {e}")
        return False


def count_subfolders_with_test_patches(root_dir: str):
    """
    Iterate first-level subfolders under root_dir,
    count which subfolders contain patches with test paths.
    """
    root = Path(root_dir)
    if not root.is_dir():
        raise ValueError(f"Directory does not exist or is not a folder: {root_dir}")

    matched_subfolders = []

    for subfolder in root.iterdir():
        if not subfolder.is_dir():
            continue

        has_test_patch = False

        for patch_file in subfolder.rglob("*"):
            if patch_file.is_file() and patch_file.suffix.lower() in {".patch", ".diff"}:
                if patch_contains_test_path(patch_file):
                    has_test_patch = True
                    break

        if has_test_patch:
            matched_subfolders.append(subfolder.name)

    return matched_subfolders


def main():
    parser = argparse.ArgumentParser(
        description="Count subdirectories containing patch/diff files with test file modifications"
    )
    parser.add_argument(
        "target_dir",
        help="Root directory to scan"
    )

    args = parser.parse_args()

    matched = count_subfolders_with_test_patches(args.target_dir)

    print("Matched subfolders:")
    for name in matched:
        print(f"- {name}")

    print(f"\nNumber of subfolders: {len(matched)}")


if __name__ == "__main__":
    main()

