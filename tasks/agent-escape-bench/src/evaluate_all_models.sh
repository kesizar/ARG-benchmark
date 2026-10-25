#!/bin/bash

# 多模型批量评测脚本
# 用途：自动对多个模型进行批量评测
# 使用方法：
#   chmod +x evaluate_all_models.sh
#   ./evaluate_all_models.sh

echo "================================================================================"
echo "                    多模型批量评测脚本"
echo "================================================================================"
echo ""

# 定义要评测的模型配置文件列表
models=(
  "config/kimi-k2-yuju.json"
  "config/gpt-4o.json"
  "config/deepseek-chat.json"
  "config/gemini-3-pro-preview.json"
  # 可以添加更多模型配置
  # "config/qwen3-32b.json"
  # "config/doubao-seed-2.0-pro.json"
)

# 配置参数
PARALLEL=4           # 并行线程数
DIFFICULTIES="5 10 15"  # 评测的难度级别

echo "配置信息："
echo "  - 模型数量: ${#models[@]}"
echo "  - 并行线程: $PARALLEL"
echo "  - 评测难度: $DIFFICULTIES"
echo ""
echo "================================================================================"
echo ""

# 记录开始时间
START_TIME=$(date +%s)

# 遍历每个模型配置
for i in "${!models[@]}"; do
  config="${models[$i]}"
  model_num=$((i + 1))
  total_models=${#models[@]}
  
  echo ""
  echo "================================================================================"
  echo "[$model_num/$total_models] 评测模型: $config"
  echo "================================================================================"
  echo ""
  
  # 检查配置文件是否存在
  if [ ! -f "$config" ]; then
    echo "❌ 错误: 配置文件不存在: $config"
    echo "跳过此模型..."
    continue
  fi
  
  # 运行批量评测
  python batch_evaluate.py \
    --config "$config" \
    --difficulties $DIFFICULTIES \
    --parallel $PARALLEL
  
  EXIT_CODE=$?
  
  if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ [$model_num/$total_models] 完成: $config"
  else
    echo ""
    echo "❌ [$model_num/$total_models] 失败: $config (退出码: $EXIT_CODE)"
  fi
  
  echo ""
  echo "================================================================================"
  echo ""
  
  # 可选：在模型之间添加延迟以避免API限流
  if [ $model_num -lt $total_models ]; then
    echo "等待 5 秒后继续下一个模型..."
    sleep 5
  fi
done

# 计算总耗时
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
HOURS=$((DURATION / 3600))
MINUTES=$(((DURATION % 3600) / 60))
SECONDS=$((DURATION % 60))

echo ""
echo "================================================================================"
echo "                        所有模型评测完成！"
echo "================================================================================"
echo ""
echo "总耗时: ${HOURS}小时 ${MINUTES}分钟 ${SECONDS}秒"
echo ""
echo "结果文件位置："
for config in "${models[@]}"; do
  if [ -f "$config" ]; then
    output_dir=$(python -c "import json; f=open('$config'); c=json.load(f); print(c.get('output_dir', 'evaluation_results'))")
    echo "  - $output_dir/"
  fi
done
echo ""
echo "================================================================================"