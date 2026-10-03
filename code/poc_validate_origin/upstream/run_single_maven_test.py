import os
import argparse
import subprocess
import sys


def find_test_files(test_dir):
    test_files = []
    for root, dirs, files in os.walk(test_dir):
        for f in files:
            if f.endswith(".java"):
                test_files.append(os.path.join(root, f))
    return test_files


def run_test(repo_path):
    test_dir = os.path.join(repo_path, "src", "test")

    if not os.path.exists(test_dir):
        print(f"❌ src/test directory not found in: {repo_path}")
        sys.exit(1)

    test_files = find_test_files(test_dir)

    if len(test_files) == 0:
        print("❌ No Java test files found")
        sys.exit(1)

    if len(test_files) != 1:
        print("❌ Error: More than one Java test file found\n")
        print("Detected test files:")

        for f in test_files:
            print(f" - {f}")

        sys.exit(1)

    test_file = test_files[0]
    class_name = os.path.splitext(os.path.basename(test_file))[0]

    print(f"✅ Found single test file: {test_file}")
    print(f"🚀 Running test: {class_name}")

    cmd = ["mvn", "clean", "test", f"-Dtest={class_name}"]

    subprocess.run(cmd, cwd=repo_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="Path to Maven project")

    args = parser.parse_args()

    run_test(args.repo)


if __name__ == "__main__":
    main()
