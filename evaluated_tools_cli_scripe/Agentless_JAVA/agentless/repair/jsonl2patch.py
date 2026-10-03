import json
import argparse
import sys
import os
def extract_patch_from_jsonl(jsonl_file, target_id, output_patch_file):
    """
    从JSONL文件中匹配指定target_id的行，提取model_patch生成patch文件
    :param jsonl_file: 输入的JSONL文件路径
    :param target_id: 要匹配的target_id值
    :param output_patch_file: 输出的patch文件路径
    """
    # 核心修改：自动创建输出文件的父目录（如果不存在）
    output_dir = os.path.dirname(output_patch_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)  # exist_ok=True 避免目录已存在时报错

    
    matched = False
    # 逐行读取JSONL文件
    with open(jsonl_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:  # 跳过空行
                continue
            try:
                # 解析单行JSON
                data = json.loads(line)
                # 匹配target_id（核心修改：instance_id → target_id）
                print(data.get("instance_id") )
                if data.get("instance_id") == target_id:
                    # 提取model_patch内容
                    patch_content = data.get("model_patch", "")
                    # 写入patch文件
                    with open(output_patch_file, "w", encoding="utf-8") as patch_f:
                        patch_f.write(patch_content)
                    matched = True
                    print(f"✅ 成功匹配target_id={target_id}（第{line_num}行）")
                    print(f"✅ Patch文件已生成：{output_patch_file}")
                    return  # 找到后直接退出，避免多匹配
            except json.JSONDecodeError as e:
                print(f"⚠️  第{line_num}行JSON解析失败：{e}", file=sys.stderr)
                continue
    
    if not matched:
        print(f"❌ 未找到target_id={target_id}的行", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    # 解析命令行参数（核心修改：instance_id → target_id）
    parser = argparse.ArgumentParser(description="从JSONL文件中提取指定target_id的model_patch生成patch文件")
    parser.add_argument("--target_id", required=True, help="要匹配的target_id值（必填）")
    parser.add_argument("--jsonl_file", required=True, help="输入的JSONL文件路径（必填）")
    parser.add_argument("--output", default="output.patch", help="输出的patch文件路径（默认：output.patch）")
    
    args = parser.parse_args()
    
    # 执行提取逻辑
    extract_patch_from_jsonl(args.jsonl_file, args.target_id, args.output)

