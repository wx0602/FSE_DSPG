#!/usr/bin/env python3
import os
import argparse
import hashlib
import shutil
import sys


def file_hash(path):
    """计算文件内容 SHA256"""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def is_empty_patch(path):
    """判断patch文件是否为空（去除空白字符后无有效内容）"""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            # 读取内容并去除所有空白字符（空格、换行、制表符等）
            content = f.read().strip()
            # 去除空白后长度为0则视为空patch
            return len(content) == 0
    except Exception as e:
        print(f"[WARN] 检查文件是否为空失败: {path} ({e})")
        # 读取失败时暂不视为空，交给后续hash步骤处理
        return False


def dedup_patches(input_root, output_dir):
    if not os.path.isdir(input_root):
        print(f"[ERROR] input 不是目录: {input_root}")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    seen = {}
    total = 0          # 总扫描patch数
    empty_count = 0    # 空patch数
    kept = 0           # 最终保留的patch数

    for root, _, files in os.walk(input_root):
        for name in files:
            if not name.endswith(".patch"):
                continue

            total += 1
            src = os.path.join(root, name)

            # 第一步：检测是否为空patch，统计并跳过
            if is_empty_patch(src):
                empty_count += 1
                print(f"[EMPTY] {src}")
                continue

            # 第二步：非空patch才计算hash并去重
            try:
                h = file_hash(src)
            except Exception as e:
                print(f"[ERROR] 读取失败: {src} ({e})")
                continue

            if h in seen:
                print(f"[DUP]  {src}")
                continue

            # 处理重名
            dst_name = name
            base, ext = os.path.splitext(name)
            idx = 1
            while os.path.exists(os.path.join(output_dir, dst_name)):
                dst_name = f"{base}_{idx}{ext}"
                idx += 1

            dst = os.path.join(output_dir, dst_name)
            shutil.copy2(src, dst)

            seen[h] = dst
            kept += 1
            print(f"[OK ] {src} -> {dst}")

    print("\n===== 完成 =====")
    print(f"扫描 patch 数: {total}")
    print(f"空 patch 数: {empty_count}")
    print(f"有效 patch 数: {total - empty_count}")
    print(f"保留 patch 数: {kept}")
    print(f"去重 patch 数: {(total - empty_count) - kept}")


def main():
    parser = argparse.ArgumentParser(
        description="递归收集 patch 并基于内容去重（先过滤空patch），输出到指定目录"
    )
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="输入根目录（包含多个子目录）"
    )
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="去重后的 patch 输出目录"
    )

    args = parser.parse_args()
    dedup_patches(args.input, args.output)


if __name__ == "__main__":
    main()

