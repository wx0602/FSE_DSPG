#!/bin/bash

# 定义脚本名称，用于错误提示
SCRIPT_NAME="combined_pipeline.sh"

# 初始化 target_id 变量
TARGET_ID=""

# 解析命令行参数
for arg in "$@"; do
  case $arg in
    --target_id=*)
      # 提取 --target_id= 后面的值
      TARGET_ID="${arg#*=}"
      # 移除参数，避免后续传递混乱
      shift
      ;;
    *)
      # 未知参数提示
      echo "错误：未知参数 '$arg'"
      echo "使用方法：$SCRIPT_NAME --target_id=<目标ID>"
      exit 1
      ;;
  esac
done

# 检查 target_id 是否为空
if [ -z "$TARGET_ID" ]; then
  echo "错误：必须指定 --target_id 参数"
  echo "使用方法：$SCRIPT_NAME --target_id=<目标ID>"
  exit 1
fi

# 定义要调用的两个脚本路径
SCRIPT1="./localization_all.sh"
SCRIPT2="./repair_validate_pipeline.sh"

# 检查脚本是否存在且可执行
check_script() {
  local script_path=$1
  if [ ! -f "$script_path" ]; then
    echo "错误：脚本 $script_path 不存在！"
    exit 1
  fi
  if [ ! -x "$script_path" ]; then
    echo "警告：脚本 $script_path 没有执行权限，尝试添加..."
    chmod +x "$script_path"
    # 再次检查是否添加成功
    if [ ! -x "$script_path" ]; then
      echo "错误：无法为 $script_path 添加执行权限，请手动执行 chmod +x $script_path"
      exit 1
    fi
  fi
}

# 检查两个脚本的可用性
check_script "$SCRIPT1"
check_script "$SCRIPT2"

# 执行第一个脚本
echo "========================================"
echo "开始执行 $SCRIPT1 --target_id=$TARGET_ID"
echo "========================================"
"$SCRIPT1" --target_id="$TARGET_ID"

# 检查第一个脚本执行状态
if [ $? -ne 0 ]; then
  echo "错误：$SCRIPT1 执行失败，终止流程！"
  exit 1
fi

# 执行第二个脚本
echo "========================================"
echo "开始执行 $SCRIPT2 --target_id=$TARGET_ID"
echo "========================================"
"$SCRIPT2" --target_id="$TARGET_ID"

# 检查第二个脚本执行状态
if [ $? -ne 0 ]; then
  echo "错误：$SCRIPT2 执行失败！"
  exit 1
fi

# 所有步骤执行完成
echo "========================================"
echo "所有脚本执行完成！目标ID：$TARGET_ID"
echo "========================================"
exit 0

