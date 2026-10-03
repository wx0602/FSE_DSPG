import os
from tree_sitter import Language, Parser

# 构建和加载 Tree-sitter Java 语法（第一次运行前确保已执行 build）
LIB_PATH = "build/my-languages.so"

if not os.path.exists(LIB_PATH):
    print("❌ Tree-sitter language library not found. Please run the following commands first:")
    print("""
    git clone https://github.com/tree-sitter/tree-sitter-java
    mkdir -p build
    python -m tree_sitter Language build/my-languages.so tree-sitter-java
    """)
    exit(1)

JAVA_LANGUAGE = Language(LIB_PATH, "java")
parser = Parser()
parser.set_language(JAVA_LANGUAGE)


def parse_global_stmt_from_code(code: str) -> tuple[str, str]:
    """
    提取 Java 文件中的全局变量（public static 字段）和 import 语句。
    返回 (global_vars_str, imports_str)
    """
    tree = parser.parse(bytes(code, "utf8"))
    root = tree.root_node
    source_bytes = bytes(code, "utf8")

    imports = []
    globals_ = []

    def get_text(node):
        return source_bytes[node.start_byte:node.end_byte].decode()

    def walk(node):
        for child in node.children:
            # 提取 import 语句
            if child.type == "import_declaration":
                imports.append(get_text(child))

            # 提取 public static 字段声明
            elif child.type == "field_declaration":
                # 找修饰符
                modifier_nodes = [c for c in child.children if c.type == "modifiers"]
                modifier_text = ""
                if modifier_nodes:
                    modifier_text = get_text(modifier_nodes[0])
                if "public" in modifier_text and "static" in modifier_text:
                    globals_.append(get_text(child))

            walk(child)

    walk(root)
    return "\n".join(globals_), "\n".join(imports)


def test():
    """测试解析功能"""
    sample_code = """\
package my.app;

import java.util.List;
import static java.lang.Math.PI;
import my.custom.ClassName;

public class Config {
    public static String APP_NAME = "MyApp";
    public static final int MAX_USERS = 100;
    private static int hidden = 42;
}
"""
    globals_str, imports_str = parse_global_stmt_from_code(sample_code)
    print("===== ✅ 全局变量（public static）=====")
    print(globals_str)
    print("\n===== 📥 Import 语句 =====")
    print(imports_str)


def main():
    test()


if __name__ == "__main__":
    main()
