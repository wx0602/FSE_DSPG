import os
import re
import shutil
import subprocess
import tempfile
import json
from typing import Dict, Any, List


# ---------------------------
# Heuristic Java parser
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

def parse_repo_at_ref(repo_url: str, ref: str, keep_clone: bool = False) -> Dict[str, Any]:
    """
    Clone a GitHub repo at a specific ref (commit, tag, or branch) and parse Java files.
    If keep_clone=True, the cloned repo will not be deleted (useful for debugging).
    """
    temp_dir = tempfile.mkdtemp()
    try:
        subprocess.run(["git", "clone", repo_url, temp_dir], check=True)
        subprocess.run(["git", "-C", temp_dir, "checkout", ref], check=True)
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise e

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

    if not keep_clone:
        shutil.rmtree(temp_dir, ignore_errors=True)
    return project_structure


# ---------------------------
# Wrapper function
# ---------------------------

def get_project_structure(repo_url: str, ref: str, output_file: str, keep_clone: bool = False) -> None:
    """
    High-level wrapper: parse repo and dump JSON structure.
    """
    structure = parse_repo_at_ref(repo_url, ref, keep_clone=keep_clone)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(structure, f, indent=2)
    return structure
def get_project_structure_from_scratch(
    repo_name: str,
    commit_id: str,
    instance_id: str,
    repo_playground: str
):
    """
    Wrapper for compatibility:
    - 保持原有的函数签名 (repo_name, commit_id, instance_id, repo_playground)
    - 内部调用新版 get_project_structure(repo_url, ref, output_file)
    - 返回新版函数的返回值 (解析后的结构)
    """
    # 拼接仓库 URL
    repo_url = f"https://github.com/{repo_name}.git"

    # 确保 playground 目录存在
    os.makedirs(repo_playground, exist_ok=True)

    # 输出文件路径：存放 JSON 结果
    output_file = os.path.join(repo_playground, f"{instance_id}.json")

    # 调用新版函数
    structure = get_project_structure(
        repo_url=repo_url,
        ref=commit_id,
        output_file=output_file,
        keep_clone=False
    )

    # 保持与旧函数一致的返回格式
    d = {
        "repo": repo_name,
        "base_commit": commit_id,
        "structure": structure,
        "instance_id": instance_id,
    }
    return d
    
import javalang
from typing import List, Dict, Any, Tuple

def parse_Java_file(file_path: str, file_content: str = None) -> Tuple[List[Dict], List[Dict], List[str]]:
    """
    
    Warning： this function is not used, so I just set Exception at where it is called 
    
    Parse a Java file to extract class and function definitions with their line numbers.
    输入:
        file_path: Java 文件路径
        file_content: (可选) Java 源码字符串
    输出:
        class_info: 类信息 (包含类名、起止行、方法列表)
        function_names: 顶层函数信息 (Java 一般没有顶层函数, 通常为空)
        file_lines: 文件的所有行
    """
    # 读取源码
    if file_content is None:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return [], [], []
    
    file_lines = file_content.splitlines()

    try:
        tree = javalang.parse.parse(file_content)
    except Exception as e:
        print(f"Error parsing Java file {file_path}: {e}")
        return [], [], file_lines

    class_info = []
    function_names = []  # Java 一般没有独立函数，但保留接口一致性

    # 遍历 AST 节点
    for path, node in tree:
        if isinstance(node, javalang.tree.ClassDeclaration) or isinstance(node, javalang.tree.InterfaceDeclaration):
            methods = []
            for m in node.methods:
                methods.append({
                    "name": m.name,
                    "start_line": m.position.line if m.position else None,
                    "end_line": None,  # javalang 不提供 end_line, 可以补充用正则/启发式计算
                    "text": file_lines[m.position.line - 1:] if m.position else []
                })
            class_info.append({
                "name": node.name,
                "start_line": node.position.line if node.position else None,
                "end_line": None,  # 同上，需要进一步计算
                "text": file_lines[node.position.line - 1:] if node.position else [],
                "methods": methods
            })

    return class_info, function_names, file_lines
    
    
    
def main():
    # 示例输入
    repo_name = "netty/netty"
    commit_id = "e22ef712667864b33e29038f66b0d17c9d25ae8f"  # netty-3.9.7.Final 的 tag 对应 commit
    instance_id = "CVE-2015-2156"
    repo_playground = "/tmp/playground"

    output_file="/home/user/AVR_JAVA_STUDY/agentless/Agentless/get_repo_structure/OSS_JSON/"+instance_id+".json"
    
    # 调用封装函数
    result = get_project_structure_from_scratch(
        repo_name=repo_name,
        commit_id=commit_id,
        instance_id=instance_id,
        repo_playground=repo_playground
    )

    # 打印结果的关键信息
    print("Repo:", result["repo"])
    print("Commit:", result["base_commit"])
    print("Instance ID:", result["instance_id"])
    print("Top-level keys in structure:", list(result["structure"].keys()))

    # 如果想看具体输出的 JSON 文件路径
    json_path = os.path.join(repo_playground, f"{instance_id}.json")
    print(f"结构已写入: {json_path}")
    print("*"*10)
    with open(output_file,"w",encoding="utf-8") as f:
        json.dump(result, f ,indent=2)
    print("JSON结构文件结果被保存在{output_file}，需要手动迁移它到PROJECT_FILE_LOC所在文件夹")


if __name__ == "__main__":
    main()
