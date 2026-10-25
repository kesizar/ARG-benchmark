#!/bin/bash
#
# 批量计算细粒度指标
# 直接修改下面的参数，然后运行: bash run_metrics.sh
#

# ============================================================
#  路径配置
# ============================================================
PROBLEM_BASE="../题目可解性验证/narrative_generate"
EVAL_BASE="../final_eval"
OUTPUT_BASE="results_cc_包含25"

# ============================================================
#  模型与难度配置
#  格式: "模型名|难度1,难度2,..."
#  修改这里来控制计算哪些模型、哪些难度
# ============================================================
TASKS=(
    # --- 闭源模型 (4个难度) ---
    "deepseek-chat|5,10,15,20"
    "deepseek-reasoner|5,10,15,20"
    "doubao-seed-2-0-pro-260215|5,10,15,20"
    "gemini-3-flash-preview|5,10,15,20"
    "gemini-3.1-pro-preview|5,10,15,20,25"
    "gpt-5|5,10,15,20"
    "gpt-5.4|5,10,15,20,25"
    "kimi-k2-0905|5,10,15,20"
    "kimi-k2.5|5,10,15,20"
    "Minimax-M2|5,10,15,20"

    # --- Qwen 开源模型 (3个难度) ---
    "qwen3-8b|5,10,15"
    "qwen3-14b|5,10,15"
    "qwen3-32b|5,10,15"
    "qwen3-235b-a22b-instruct-2507|5,10,15"
    "qwen3-next-80b-a3b-instruct|5,10,15"
)

# ============================================================
#  以下不需要修改
# ============================================================
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

total=0
success=0
fail=0
skipped=0

# 计算总任务数
for task in "${TASKS[@]}"; do
    model="${task%%|*}"
    diffs="${task##*|}"
    IFS=',' read -ra diff_arr <<< "$diffs"
    for diff in "${diff_arr[@]}"; do
        total=$((total + 1))
    done
done

echo "============================================================"
echo "  细粒度指标批量计算"
echo "  总任务数: $total"
echo "============================================================"

current=0
start_time=$(date +%s)

for task in "${TASKS[@]}"; do
    model="${task%%|*}"
    diffs="${task##*|}"
    IFS=',' read -ra diff_arr <<< "$diffs"

    for diff in "${diff_arr[@]}"; do
        current=$((current + 1))
        problem_dir="${PROBLEM_BASE}/${diff}"
        result_dir="${EVAL_BASE}/${model}/${diff}"
        output_dir="${OUTPUT_BASE}/${model}"
        output_file="${output_dir}/metrics_output_${diff}.json"

        echo ""
        echo "[${current}/${total}] ${model} / difficulty=${diff}"

        # 检查路径是否存在
        if [ ! -d "$result_dir" ]; then
            echo "  SKIP: result dir not found: $result_dir"
            skipped=$((skipped + 1))
            continue
        fi
        if [ ! -d "$problem_dir" ]; then
            echo "  SKIP: problem dir not found: $problem_dir"
            skipped=$((skipped + 1))
            continue
        fi

        mkdir -p "$output_dir"

        python compute_fine_grained_metrics.py "$problem_dir" "$result_dir" "$output_file"

        if [ $? -eq 0 ]; then
            echo "  -> $output_file"
            success=$((success + 1))
        else
            echo "  ERROR"
            fail=$((fail + 1))
        fi
    done
done

end_time=$(date +%s)
elapsed=$((end_time - start_time))

echo ""
echo "============================================================"
echo "  完成: ${success} 成功 / ${fail} 失败 / ${skipped} 跳过"
echo "  耗时: ${elapsed}s"
echo "============================================================"
