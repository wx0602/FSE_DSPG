import re

import libcst as cst
import libcst.matchers as m


class CompressTransformer(cst.CSTTransformer):
    DESCRIPTION = str = "Replaces function body with ..."
    replacement_string = '"__FUNC_BODY_REPLACEMENT_STRING__"'

    def __init__(self, keep_constant=True, keep_indent=False):
        self.keep_constant = keep_constant
        self.keep_indent = keep_indent

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        new_body = [
            stmt
            for stmt in updated_node.body
            if m.matches(stmt, m.ClassDef())
            or m.matches(stmt, m.FunctionDef())
            or (
                self.keep_constant
                and m.matches(stmt, m.SimpleStatementLine())
                and m.matches(stmt.body[0], m.Assign())
            )
        ]
        return updated_node.with_changes(body=new_body)

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.ClassDef:
        # Remove docstring in the class body
        new_body = [
            stmt
            for stmt in updated_node.body.body
            if not (
                m.matches(stmt, m.SimpleStatementLine())
                and m.matches(stmt.body[0], m.Expr())
                and m.matches(stmt.body[0].value, m.SimpleString())
            )
        ]
        return updated_node.with_changes(body=cst.IndentedBlock(body=new_body))

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.CSTNode:
        if not self.keep_indent:
            # replace with unindented statement
            new_expr = cst.Expr(value=cst.SimpleString(value=self.replacement_string))
            new_body = cst.IndentedBlock((new_expr,))
            return updated_node.with_changes(body=new_body)
        else:
            # replace with indented statement
            # new_expr = [cst.Pass()]
            new_expr = [
                cst.Expr(value=cst.SimpleString(value=self.replacement_string)),
            ]
            return updated_node.with_changes(
                body=cst.IndentedBlock(body=[cst.SimpleStatementLine(body=new_expr)])
            )


class GlobalVariableVisitor(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (cst.metadata.PositionProvider,)

    def __init__(self):
        self.assigns = []

    def leave_Assign(self, original_node: cst.Module) -> list:
        stmt = original_node
        start_pos = self.get_metadata(cst.metadata.PositionProvider, stmt).start
        end_pos = self.get_metadata(cst.metadata.PositionProvider, stmt).end
        self.assigns.append([stmt, start_pos, end_pos])


code = """
\"\"\"
this is a module
...
\"\"\"
const = {1,2,3}
import os

class fooClass:
    '''this is a class'''

    def __init__(self, x):
        '''initialization.'''
        self.x = x

    def print(self):
        print(self.x)

large_var = {
    1: 2,
    2: 3,
    3: 4,
    4: 5,
    5: 6,
    6: 7,
    7: 8,
    8: 9,
    9: 10,
    10: 11,
    11: 12,
    12: 13,
    13: 14,
    14: 15,
    15: 16,
    16: 17,
    17: 18,
    18: 19,
    19: 20,
    20: 21,
}

def test():
    a = fooClass(3)
    a.print()

"""


def remove_lines(raw_code, remove_line_intervals):
    # TODO: speed up this function
    # remove_line_intervals.sort()

    # Remove lines
    new_code = ""
    for i, line in enumerate(raw_code.splitlines()):
        # intervals are one-based
        if not any(start <= i + 1 <= end for start, end in remove_line_intervals):
            new_code += line + "\n"
        if any(start == i + 1 for start, _ in remove_line_intervals):
            new_code += "...\n"
    return new_code


def compress_assign_stmts(raw_code, total_lines=30, prefix_lines=10, suffix_lines=10):
    try:
        tree = cst.parse_module(raw_code)
    except Exception as e:
        print(e.__class__.__name__, e)
        return raw_code

    wrapper = cst.metadata.MetadataWrapper(tree)
    visitor = GlobalVariableVisitor()
    wrapper.visit(visitor)

    remove_line_intervals = []
    for stmt in visitor.assigns:
        if stmt[2].line - stmt[1].line > total_lines:
            remove_line_intervals.append(
                (stmt[1].line + prefix_lines, stmt[2].line - suffix_lines)
            )
    return remove_lines(raw_code, remove_line_intervals)


def get_skeleton(
    raw_code,
    keep_constant: bool = True,
    keep_indent: bool = False,
    compress_assign: bool = False,
    total_lines=30,
    prefix_lines=10,
    suffix_lines=10,
):
    try:
        tree = cst.parse_module(raw_code)
    except:
        return raw_code

    transformer = CompressTransformer(keep_constant=keep_constant, keep_indent=True)
    modified_tree = tree.visit(transformer)
    code = modified_tree.code

    if compress_assign:
        code = compress_assign_stmts(
            code,
            total_lines=total_lines,
            prefix_lines=prefix_lines,
            suffix_lines=suffix_lines,
        )

    if keep_indent:
        code = code.replace(CompressTransformer.replacement_string + "\n", "...\n")
        code = code.replace(CompressTransformer.replacement_string, "...\n")
    else:
        pattern = f"\\n[ \\t]*{CompressTransformer.replacement_string}"
        replacement = "\n..."
        code = re.sub(pattern, replacement, code)

    return code
import os
from tree_sitter import Language, Parser

# === 需要准备好 my-languages.so，其中包含 tree-sitter-java ===
# 常见做法（按你环境的 py-tree-sitter 版本选择），这里只假设已经构建好：
LIB_PATH = "build/my-languages.so"
if not os.path.exists(LIB_PATH):
    raise FileNotFoundError(
        f"{LIB_PATH} not found. 请先把 tree-sitter-java 编进该 so，再运行本脚本。"
    )

JAVA = Language(LIB_PATH, "java")
parser = Parser()
parser.set_language(JAVA)


def _text(src: bytes, node):
    return src[node.start_byte:node.end_byte].decode()


def _child_text(src: bytes, node, field: str) -> str:
    """安全拿字段文本，不存在返回空串；兼容 'type'/'return_type' 差异。"""
    n = node.child_by_field_name(field)
    return _text(src, n) if n else ""


def get_skeleton_java(raw_code: str) -> str:
    """
    生成 Java skeleton：类/接口外壳、字段、方法(或构造器)签名（无方法体）。
    """
    tree = parser.parse(raw_code.encode("utf8"))
    root = tree.root_node
    src = raw_code.encode("utf8")

    out = []

    def walk(node, indent=0):
        pre = " " * indent

        # class
        if node.type == "class_declaration":
            name = _child_text(src, node, "name")
            out.append(f"{pre}class {name} {{")
            for ch in node.children:
                walk(ch, indent + 4)
            out.append(f"{pre}}}")
            return

        # interface
        if node.type == "interface_declaration":
            name = _child_text(src, node, "name")
            out.append(f"{pre}interface {name} {{")
            for ch in node.children:
                walk(ch, indent + 4)
            out.append(f"{pre}}}")
            return

        # enum（可选：只展示外壳）
        if node.type == "enum_declaration":
            name = _child_text(src, node, "name")
            out.append(f"{pre}enum {name} {{ ... }}")
            return

        # 字段：保留修饰符 + 声明，去重分号
        if node.type == "field_declaration":
            line = _text(src, node).strip()
            line = line.rstrip(";") + ";"  # 避免出现 ';;'
            out.append(pre + line)
            return

        # 构造器：constructor_declaration
        if node.type == "constructor_declaration":
            mods = ""
            for ch in node.children:
                if ch.type == "modifiers":
                    mods = _text(src, ch).strip()
            name = _child_text(src, node, "name")
            params = _child_text(src, node, "parameters")
            sig = " ".join(x for x in [mods, f"{name}{params}"] if x).strip()
            out.append(pre + sig + ";")
            return

        # 普通方法：method_declaration
        if node.type == "method_declaration":
            mods = ""
            for ch in node.children:
                if ch.type == "modifiers":
                    mods = _text(src, ch).strip()

            # 不同版本 grammar 这里有时叫 'type'，有时叫 'return_type'
            ret = _child_text(src, node, "type") or _child_text(src, node, "return_type")
            name = _child_text(src, node, "name")
            params = _child_text(src, node, "parameters")

            # 处理可能没有返回类型（例如接口里缺省? 或者纠正为 void）
            sig_parts = [mods]
            if ret:
                sig_parts.append(ret.strip())
            sig_parts.append(f"{name}{params}")
            sig = " ".join(p for p in sig_parts if p).strip()
            out.append(pre + sig + ";")
            return

        # 继续下钻其它结构节点（比如 class body 等）
        for ch in node.children:
            walk(ch, indent)

    walk(root)
    return "\n".join(out)


def get_text(node, code_bytes):
    return code_bytes[node.start_byte:node.end_byte].decode("utf-8")
def clean_semicolon(text: str) -> str:
    return text.rstrip(";") + ";"
def compress_assign_stmts(code: str, total_lines=30, prefix_lines=10, suffix_lines=10) -> str:
    """
    类似 Python 版本：如果代码行数超过 total_lines，就保留前 prefix_lines 和后 suffix_lines
    中间替换为 "..."
    """
    lines = code.splitlines()
    if len(lines) > total_lines:
        return "\n".join(lines[:prefix_lines] + ["..."] + lines[-suffix_lines:])
    return code



# ========== 核心：生成 Java skeleton ==========
from typing import List
def get_skeleton_java(
    raw_code: str,
    keep_constant: bool = True,   # 是否保留常量的初始化（public static final + 字面量）
    keep_indent: bool = True,     # 是否输出缩进（一般建议 True）
    compress_assign: bool = False,# 预留参数：是否进一步压缩（Java 版暂不实现）
    total_lines: int = 30,        # 预留参数
    prefix_lines: int = 10,       # 预留参数
    suffix_lines: int = 10,       # 预留参数
) -> str:
    """
    将 Java 源码压缩为结构化 skeleton。
    """
    tree = parser.parse(raw_code.encode("utf8"))
    src = raw_code.encode("utf-8")

    def text(node) -> str:
        return src[node.start_byte: node.end_byte].decode("utf-8")

    IND = "    "

    def join_lines(lines: List[str]) -> str:
        # 去掉多余空行
        out: List[str] = []
        for s in lines:
            if out and not s.strip() and not out[-1].strip():
                continue
            out.append(s)
        return "\n".join(out)

    def has_mod(node, kw: str) -> bool:
        # 判断 modifiers 里是否包含某修饰词
        for ch in node.children:
            if ch.type == "modifiers":
                if kw in text(ch):
                    return True
        return False

    def render_modifiers(node) -> str:
        for ch in node.children:
            if ch.type == "modifiers":
                return text(ch).strip()
        return ""

    def render_type(node) -> str:
        # 在 field/method 上找到类型那个 child
        # 简化处理：返回第一个类型样的命名节点
        # 更稳妥可以找 child.type in {"type_identifier","integral_type","floating_point_type","void_type","boolean_type","array_type","scoped_type_identifier","generic_type"}
        for ch in node.children:
            if ch.type.endswith("_type") or ch.type in {"type_identifier", "scoped_type_identifier", "void_type"}:
                return text(ch).strip()
        return ""

    def is_literal(node) -> bool:
        return node.type in {
            "decimal_integer_literal",
            "hex_integer_literal",
            "octal_integer_literal",
            "binary_integer_literal",
            "decimal_floating_point_literal",
            "hex_floating_point_literal",
            "true",
            "false",
            "null_literal",
            "string_literal",
            "character_literal",
        }

    def render_params(formal_params_node) -> str:
        # 直接取源码，不做花活；避免把注解/泛型漏掉
        return text(formal_params_node).strip()

    def render_variable_declarator(decl_node, keep_value: bool) -> str:
        # variable_declarator: identifier dimensions? ('=' initializer)?
        name = ""
        init_part = ""
        for ch in decl_node.children:
            if ch.type == "identifier" and not name:
                name = text(ch).strip()
            elif ch.type == "initializer":
                if keep_value:
                    init_part = " = " + text(ch.child_by_field_name("value") or ch).strip()
                else:
                    # 丢弃初始化
                    init_part = ""
        return f"{name}{init_part}"

    def render_field_lines(node, depth: int) -> List[str]:
        # field_declaration: modifiers? type variable_declarator (',' ...)* ';'
        mods = render_modifiers(node)
        typ  = render_type(node)
        is_const = has_mod(node, "final") and has_mod(node, "static")
        keep_value = keep_constant and is_const

        decls: List[str] = []
        for ch in node.children:
            if ch.type == "variable_declarator":
                decls.append(render_variable_declarator(ch, keep_value))
        if not decls:
            # 兜底：直接还原一行
            line = text(node).strip()
            if not line.endswith(";"):
                line += ";"
            return [IND * depth + line]

        out: List[str] = []
        head = (mods + " " if mods else "") + (typ + " " if typ else "")
        for d in decls:
            out.append(IND * depth + f"{head}{d};")
        return out

    def render_method_or_ctor(node, depth: int) -> str:
        # method_declaration / constructor_declaration
        mods = render_modifiers(node)
        # 名称
        name = ""
        name_field = node.child_by_field_name("name")
        if name_field:
            name = text(name_field).strip()
        else:
            # 某些 grammar 版本方法名落在 declarator 里面
            for ch in node.children:
                if ch.type == "identifier":
                    name = text(ch).strip()
                    break
        # 参数
        params = ""
        formal = node.child_by_field_name("parameters")
        if formal is None:
            # 兼容不同 grammar：去找 formal_parameters
            for ch in node.children:
                if ch.type == "formal_parameters":
                    formal = ch
                    break
        if formal is not None:
            params = render_params(formal)
        else:
            params = "()"

        # 返回类型（构造器没有）
        ret = ""
        if node.type == "method_declaration":
            typ = node.child_by_field_name("type")
            if typ is not None:
                ret = text(typ).strip()
            else:
                # 兜底尝试
                ret = render_type(node)

        header = ""
        if mods:
            header += mods + " "
        if ret:
            header += ret + " "
        header += f"{name} {params}"

        # 体 or 分号
        body = node.child_by_field_name("body")
        if body is None:
            # 抽象方法：以 ';' 结尾
            return IND * depth + header + ";"
        else:
            return IND * depth + header + " { ... }"

    def render_enum(node, depth: int, out: List[str]):
        # enum_declaration: 简化为 “enum Name { ... }”
        name_field = node.child_by_field_name("name")
        name = text(name_field).strip() if name_field else "Enum"
        mods = render_modifiers(node)
        head = ((mods + " ") if mods else "") + f"enum {name} {{"
        out.append(IND * depth + head)
        out.append(IND * (depth + 1) + "...")  # 省略常量/成员
        out.append(IND * depth + "}")

    def render_interface(node, depth: int, out: List[str]):
        name_field = node.child_by_field_name("name")
        name = text(name_field).strip() if name_field else "Interface"
        mods = render_modifiers(node)
        head = ((mods + " ") if mods else "") + f"interface {name} {{"
        out.append(IND * depth + head)
        # body
        body = None
        for ch in node.children:
            if ch.type == "interface_body":
                body = ch
                break
        if body:
            for mem in body.named_children:
                if mem.type in {"constant_declaration", "field_declaration"}:
                    out.extend(render_field_lines(mem, depth + 1))
                elif mem.type == "method_declaration":
                    out.append(render_method_or_ctor(mem, depth + 1))
                elif mem.type in {"class_declaration", "interface_declaration", "enum_declaration"}:
                    render_any(mem, depth + 1, out)
        out.append(IND * depth + "}")

    def render_class(node, depth: int, out: List[str]):
        name_field = node.child_by_field_name("name")
        name = text(name_field).strip() if name_field else "Class"
        mods = render_modifiers(node)
        head = ((mods + " ") if mods else "") + f"class {name} {{"
        out.append(IND * depth + head)
        # 找 body
        body = None
        for ch in node.children:
            if ch.type == "class_body":
                body = ch
                break
        if body:
            for mem in body.named_children:
                # class_body_declaration 里可能再包了一层 declaration
                node0 = mem
                if node0.type == "class_body_declaration":
                    # 里层第一个 named child 才是真正声明
                    if node0.named_children:
                        node0 = node0.named_children[0]
                t = node0.type
                if t == "field_declaration":
                    out.extend(render_field_lines(node0, depth + 1))
                elif t in {"method_declaration", "constructor_declaration"}:
                    out.append(render_method_or_ctor(node0, depth + 1))
                elif t in {"class_declaration", "interface_declaration", "enum_declaration"}:
                    render_any(node0, depth + 1, out)
                # 其它如 static_initializer 等可按需增加
        out.append(IND * depth + "}")

    def render_any(node, depth: int, out: List[str]):
        if node.type == "class_declaration":
            render_class(node, depth, out)
        elif node.type == "interface_declaration":
            render_interface(node, depth, out)
        elif node.type == "enum_declaration":
            render_enum(node, depth, out)
        else:
            # 不认识的声明，兜底：不报错，跳过
            pass

    lines: List[str] = []

    # 1) imports（保持源码里只有一个 ';'，不手工追加，避免 ';;'）
    root = tree.root_node
    for ch in root.named_children:
        if ch.type == "import_declaration":
            imp = text(ch).strip()
            lines.append(imp if imp.endswith(";") else (imp + ";"))

    # 2) 顶级声明：class / interface / enum
    for ch in root.named_children:
        if ch.type in {"class_declaration", "interface_declaration", "enum_declaration"}:
            render_any(ch, 0, lines)

    result = join_lines(lines)
    # keep_indent=False 时可做一个简单左对齐（这里不缩进就是保持已有缩进）
    if not keep_indent:
        # 左对齐：去掉每行前导空白
        result = "\n".join(line.lstrip() for line in result.splitlines())
    return result


# ===== 测试用例 =====
def test_get_skeleton_java():
    sample_code = """
    import java.util.List;
    import static java.lang.Math.PI;

    public class Config {
        public static final String APP_NAME = "MyApp";
        private int value;

        // 构造函数
        public Config(String name) {
            this.value = name.length();
        }

        public void run() {
            System.out.println("running");
        }

        enum Mode { AUTO, MANUAL }
    }

    interface Runner {
        void execute();
    }
    """

    print("===== Skeleton 提取结果 =====")
    print(get_skeleton_java(sample_code, keep_constant=True, keep_indent=True, compress_assign=True))












def main():
    test_get_skeleton_java()
    # test_compress()
    #test_compress_var()

if __name__ == "__main__":
    main()




