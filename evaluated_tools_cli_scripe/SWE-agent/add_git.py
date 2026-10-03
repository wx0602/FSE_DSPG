import os
import shutil
import subprocess

def reinit_git_for_second_level_dirs(root_path):
    root_path = os.path.abspath(root_path)

    for first_level in os.listdir(root_path):
        first_level_path = os.path.join(root_path, first_level)

        if not os.path.isdir(first_level_path):
            continue

        for second_level in os.listdir(first_level_path):
            second_level_path = os.path.join(first_level_path, second_level)

            if not os.path.isdir(second_level_path):
                continue

            

            git_dir = os.path.join(second_level_path, ".git")

          
            if os.path.exists(git_dir):
                
                shutil.rmtree(git_dir)

            # git init
            subprocess.run(["git", "init"], cwd=second_level_path, check=True)

            # git add .
            subprocess.run(["git", "add", "."], cwd=second_level_path, check=True)

            # git commit
            subprocess.run(
                ["git", "commit", "-m", "init"],
                cwd=second_level_path,
                check=True
            )

if __name__ == "__main__":
    reinit_git_for_second_level_dirs("/home/user/AVR_JAVA_STUDY/VESTA_resource/resource")
