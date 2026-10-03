import subprocess
import argparse


def main():
    parser = argparse.ArgumentParser(description='循环调用jsonl2patch.py脚本')
    parser.add_argument('--target_id', required=True, help='目标ID')
    args = parser.parse_args()
    new_target_id = args.target_id

    for i in range(1, 5):
        for j in range(10):
            jsonl_file = f"/home/user/AVR_JAVA_STUDY/agentless/Agentless/results/poc-bench-lite/repair_sample_{i}/output_{j}_processed.jsonl"
            output = f"/home/user/AVR_JAVA_STUDY/agentless/Agentless/results/poc-bench-lite/repair_patch/repair_patch_{i}/output_{j}_processed.patch"
            command = [
                "python",
                "agentless/repair/jsonl2patch.py",
                f"--target_id={new_target_id}",
                f"--jsonl_file={jsonl_file}",
                f"--output={output}"
            ]
            try:
                subprocess.run(command, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error occurred while running command: {' '.join(command)}")
                print(f"Error details: {e}")


if __name__ == "__main__":
    main()

