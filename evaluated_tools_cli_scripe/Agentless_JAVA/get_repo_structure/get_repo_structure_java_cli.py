import os
import re
import shutil
import subprocess
import tempfile
import json
from typing import Dict, Any, List

# -------------------------------------------------
# Heuristic Java parser (fallback if no tree-sitter)
# -------------------------------------------------

def parse_java_file(file_path: str, java_language=None) -> Dict[str, Any]:
    """
    Parse a Java file heuristically to extract classes, fields, and methods.
    Returns dict with classes, functions (always []), and file text.
    """
    result = {"classes": [], "functions": [], "text": []}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            orig_lines = f.read().splitlines()
    except Exception:
        return result

    result["text"] = orig_lines

    # --- helpers ---
    def remove_comments_and_literals(code: str) -> str:
        """Remove comments and literals but preserve newlines."""
        out = []
        i = 0
        n = len(code)
        in_block = False
        in_line = False
        in_str = False
        in_char = False
        while i < n:
            ch = code[i]
            nxt = code[i+1] if i+1 < n else ""

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
        """Remove <...> generic declarations."""
        result_chars = []
        depth = 0
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
        """Extract variable names from a candidate field declaration line."""
        if ";" not in pre_line:
            return []
        if "(" in pre_line or ")" in pre_line:
            return []
        pre_line = remove_generics(pre_line)
        segment = pre_line.split(";")[0].strip()
        if not segment:
            return []
        tokens = segment.split()
        if not tokens:
            return []
        if len(tokens) >= 2:
            var_part = tokens[-1]
            var_part = var_part.rstrip("=,")
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", var_part):
                return [var_part]
        return []

    pre_lines = remove_comments_and_literals("\n".join(orig_lines)).splitlines()

    class_stack = []
    method_stack = []
    classes: List[Dict[str, Any]] = []

    brace_depth = 0

    for line_no, (pre_line, orig_line) in enumerate(zip(pre_lines, orig_lines), start=1):
        # class/interface/enum detection
        m = re.search(r"\b(class|interface|enum)\s+([A-Za-z_][A-Za-z0-9_]*)", pre_line)
        if m:
            class_name = m.group(2)
            class_stack.append({
                "name": class_name,
                "start_line": line_no,
                "variables": [],
                "functions": [],
                "_brace_depth": brace_depth,
            })

        # method detection (only when inside class, not already in method)
        if class_stack and not method_stack:
            m = re.search(r"(?:[A-Za-z0-9_<>\[\]]+\s+)+([A-Za-z_][A-Za-z0-9_]*)\s*\(", pre_line)
            if m:
                method_name = m.group(1)
                method_stack.append({
                    "name": method_name,
                    "start_line": line_no,
                    "_brace_depth": brace_depth,
                })

        # variable detection
        if class_stack and not method_stack:
            var_names = extract_variable_names(orig_line, pre_line)
            if var_names:
                class_stack[-1]["variables"].extend(var_names)

        # update brace depth
        opens = pre_line.count("{")
        closes = pre_line.count("}")
        brace_depth += opens - closes

        # method end detection
        if method_stack:
            if brace_depth < method_stack[-1]["_brace_depth"] + 1:
                meth = method_stack.pop()
                meth["end_line"] = line_no
                meth["text"] = orig_lines[meth["start_line"]-1 : meth["end_line"]]
                class_stack[-1]["functions"].append(meth)

        # class end detection
        if class_stack:
            if brace_depth < class_stack[-1]["_brace_depth"] + 1:
                cls = class_stack.pop()
                cls["end_line"] = line_no
                cls["text"] = orig_lines[cls["start_line"]-1 : cls["end_line"]]
                classes.append(cls)

    classes.sort(key=lambda c: c.get("start_line", 0))
    result["classes"] = classes
    return result


# -------------------------------------------------
# Repo-level parsing
# -------------------------------------------------

def parse_repo_at_ref(repo_url: str, ref: str) -> Dict[str, Any]:
    """
    Clone a GitHub repo at a specific ref (commit, tag, or branch) and parse Java files.
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

    shutil.rmtree(temp_dir, ignore_errors=True)
    return project_structure


# -------------------------------------------------
# CLI entry
# -------------------------------------------------
'''
python get_repo_structure_java.py \
    --repo https://github.com/netty/netty.git \
    --ref netty-3.9.7.Final \
    --output netty_3.9.7.json
'''
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Parse Java project structure from a GitHub repo at a given ref (commit, tag, or branch)."
    )
    parser.add_argument("--repo", required=True, help="GitHub repository URL")
    parser.add_argument("--ref", required=True, help="Git ref: commit hash, tag, or branch")
    parser.add_argument("--output", required=True, help="Output JSON file")
    args = parser.parse_args()

    structure = parse_repo_at_ref(args.repo, args.ref)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(structure, f, indent=2)
