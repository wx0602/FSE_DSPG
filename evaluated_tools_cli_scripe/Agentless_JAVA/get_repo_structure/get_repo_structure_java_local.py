import os
import re
import shutil
import subprocess
import tempfile
import json
from typing import Dict, Any, List


# ---------------------------
# Heuristic Java parser
#这个脚本是用来一次性加载本地的大量仓库，而非git于网络的仓库。
# ---------------------------

def parse_java_file(file_path: str, java_language=None) -> Dict[str, Any]:
    """
    Parse a Java file heuristically to extract classes, fields, and methods.
    Returns dict with classes, functions, and file text.
    """
    result = {"classes": [], "functions": [], "text": []}
    try:
        if file_path and os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                orig_lines = f.read().splitlines()
        elif isinstance(java_language,str):
            print("输入命中")
            orig_lines = java_language.splitlines()
        else:
            print("parse_java_file 的输入不正确")
    except Exception:
        print("parse_java_file 的输入不正确")
        return 
    result["text"] = orig_lines

    # -------- helpers --------
    def remove_comments_and_literals(code: str) -> str:
        out = []
        i, n = 0, len(code)
        in_block = in_line = in_str = in_char = False
        while i < n:
            ch, nxt = code[i], code[i+1] if i+1 < n else ""
            if in_block:
                if ch == "*" and nxt == "/":
                    in_block = False
                    out.append("  ")
                    i += 2
                    continue
                out.append("\n" if ch == "\n" else " ")
                i += 1
                continue
            if in_line:
                if ch == "\n":
                    in_line = False
                    out.append("\n")
                else:
                    out.append(" ")
                i += 1
                continue
            if in_str:
                if ch == "\\":
                    out.append("  ")
                    i += 2
                    continue
                if ch == "\"":
                    in_str = False
                out.append(" ")
                i += 1
                continue
            if in_char:
                if ch == "\\":
                    out.append("  ")
                    i += 2
                    continue
                if ch == "'":
                    in_char = False
                out.append(" ")
                i += 1
                continue
            if ch == "/" and nxt == "*":
                in_block = True
                out.append("  ")
                i += 2
                continue
            if ch == "/" and nxt == "/":
                in_line = True
                out.append("  ")
                i += 2
                continue
            if ch == "\"":
                in_str = True
                out.append(" ")
                i += 1
                continue
            if ch == "'":
                in_char = True
                out.append(" ")
                i += 1
                continue
            out.append(ch)
            i += 1
        return "".join(out)

    def remove_generics(text: str) -> str:
        result_chars, depth = [], 0
        for ch in text:
            if ch == "<":
                depth += 1
            elif ch == ">":
                if depth > 0:
                    depth -= 1
            elif depth == 0:
                result_chars.append(ch)
        return "".join(result_chars)

    def extract_variable_names(orig_line: str, pre_line: str) -> List[str]:
        if ";" not in pre_line or "(" in pre_line or ")" in pre_line:
            return []
        pre_line = remove_generics(pre_line)
        segment = pre_line.split(";")[0].strip()
        if not segment:
            return []
        tokens = segment.split()
        if len(tokens) >= 2:
            var_part = tokens[-1].rstrip("=,")
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", var_part):
                return [var_part]
        return []

    pre_lines = remove_comments_and_literals("\n".join(orig_lines)).splitlines()
    class_stack, method_stack, classes = [], [], []
    brace_depth = 0

    for line_no, (pre_line, orig_line) in enumerate(zip(pre_lines, orig_lines), start=1):
        m = re.search(r"\b(class|interface|enum)\s+([A-Za-z_][A-Za-z0-9_]*)", pre_line)
        if m:
            class_stack.append({
                "name": m.group(2),
                "start_line": line_no,
                "variables": [], "functions": [], "_brace_depth": brace_depth,
            })
        if class_stack and not method_stack:
            m = re.search(r"(?:[A-Za-z0-9_<>\[\]]+\s+)+([A-Za-z_][A-Za-z0-9_]*)\s*\(", pre_line)
            if m:
                method_stack.append({
                    "name": m.group(1),
                    "start_line": line_no,
                    "_brace_depth": brace_depth,
                })
        if class_stack and not method_stack:
            var_names = extract_variable_names(orig_line, pre_line)
            if var_names:
                class_stack[-1]["variables"].extend(var_names)

        opens, closes = pre_line.count("{"), pre_line.count("}")
        brace_depth += opens - closes

        if method_stack and brace_depth < method_stack[-1]["_brace_depth"] + 1:
            meth = method_stack.pop()
            meth["end_line"] = line_no
            meth["text"] = orig_lines[meth["start_line"]-1 : meth["end_line"]]
            class_stack[-1]["functions"].append(meth)

        if class_stack and brace_depth < class_stack[-1]["_brace_depth"] + 1:
            cls = class_stack.pop()
            cls["end_line"] = line_no
            cls["text"] = orig_lines[cls["start_line"]-1 : cls["end_line"]]
            classes.append(cls)

    classes.sort(key=lambda c: c.get("start_line", 0))
    result["classes"] = classes
    return result


# ---------------------------
# Repo-level parsing
# ---------------------------

def parse_repo_at_local(local_path) -> Dict[str, Any]:
    """
    Clone a GitHub repo at a specific ref (commit, tag, or branch) and parse Java files.
    If keep_clone=True, the cloned repo will not be deleted (useful for debugging).
    """
    temp_dir = local_path
    project_structure = {}
    for root, dirs, files in os.walk(temp_dir):
        dirs[:] = [d for d in dirs if d != ".git"]
        rel_path = os.path.relpath(root, temp_dir)
        current = project_structure
        if rel_path != ".":
            for part in rel_path.split(os.sep):
                if part not in current:
                    current[part] = {}
                current = current[part]
        for file_name in files:
            if file_name.endswith(".java"):
                file_path = os.path.join(root, file_name)
                current[file_name] = parse_java_file(file_path, None)

    return project_structure




# ---------------------------
# Wrapper function
# ---------------------------


def get_project_structure_from_local(
    path_local,output_file_path
):
    """
instance_id使用的是二级目录
    """
    # 确保 playground 目录存在
    #os.makedirs(repo_playground, exist_ok=True)

    # 输出文件路径：存放 JSON 结果
    #output_file = os.path.join(repo_playground, f"{instance_id}.json")

    # 调用新版函数
    structure = parse_repo_at_local(
        path_local
    )

    # 保持与旧函数一致的返回格式
    d = {
        "repo": os.path.basename(path_local),
        "base_commit": "",
        "structure": structure,
        "instance_id": os.path.basename(os.path.dirname(path_local))+"_"+os.path.basename(path_local),
    }
    with open(output_file_path,"w",encoding="utf-8") as f:
        json.dump(d, f ,indent=2)
    return d
    
import javalang
from typing import List, Dict, Any, Tuple


import os

def main():
    root_dir = "/home/user/AVR_JAVA_STUDY/VESTA_resource/resource"
    # 你想把所有 json 放到哪个目录里：
    output_base_dir = "/home/user/AVR_JAVA_STUDY/VESTA_resource/json_output"

    os.makedirs(output_base_dir, exist_ok=True)

    # 第一层循环：CVE 目录
    for first_level_name in os.listdir(root_dir):
        first_level_path = os.path.join(root_dir, first_level_name)
        if not os.path.isdir(first_level_path):
            continue  # 不是文件夹就跳过

        # 第二层循环：对应 CVE 下面的项目目录
        for second_level_name in os.listdir(first_level_path):
            second_level_path = os.path.join(first_level_path, second_level_name)
            if not os.path.isdir(second_level_path):
                continue  # 也只处理文件夹

            # 构造输出文件名：第一层_第二层.json
            output_file_name = f"{first_level_name}_{second_level_name}.json"
            output_file_path = os.path.join(output_base_dir, output_file_name)

            print(f"Processing: {second_level_path}")
            print(f"Output to : {output_file_path}")

            # 这里调用你已有的函数
            get_project_structure_from_local(
                path_local=second_level_path,
                output_file_path=output_file_path,
            )

if __name__ == "__main__":
    main()


