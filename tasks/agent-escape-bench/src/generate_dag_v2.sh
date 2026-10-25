#!/bin/bash

# DAG 数据生成完整流程脚本 V2
# 前4步与 generate_dag_complete.sh 相同（skeleton→sources→inits→full）
# 第5步使用 narrative_generator2.py + 随机叙事风格（8种）
# 用法: ./generate_dag_v2.sh [--count COUNT] [--difficulty DIFFICULTY] [--parallel N] [--droppable-ratio RATIO] [--config CONFIG]

export PROMPT_LANGUAGE=en

# 默认参数
COUNT=1
DIFFICULTY=5
PARALLEL=1
DROPPABLE_RATIO=0.3
CONFIG_FILE="config/narrative_yuju_v2.json"
API_KEY=""
CLIENT_TYPE=""

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --count)
            COUNT="$2"
            shift 2
            ;;
        --difficulty)
            DIFFICULTY="$2"
            shift 2
            ;;
        --parallel)
            PARALLEL="$2"
            shift 2
            ;;
        --droppable-ratio)
            DROPPABLE_RATIO="$2"
            shift 2
            ;;
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --api-key)
            API_KEY="$2"
            shift 2
            ;;
        --client-type)
            CLIENT_TYPE="$2"
            shift 2
            ;;
        *)
            echo "未知参数: $1"
            echo "用法: $0 [--count COUNT] [--difficulty DIFFICULTY] [--parallel N] [--droppable-ratio RATIO] [--config CONFIG] [--api-key KEY] [--client-type TYPE]"
            exit 1
            ;;
    esac
done

echo "========================================="
echo "DAG 数据生成完整流程 V2（随机叙事风格）"
echo "========================================="
echo "Count: $COUNT"
echo "Difficulty: $DIFFICULTY"
echo "并行数: $PARALLEL"
echo "可掉落工具比例: $DROPPABLE_RATIO"
echo "Language: $PROMPT_LANGUAGE"
echo "Config: $CONFIG_FILE"
echo "Client: $CLIENT_TYPE"
echo "叙事风格: 随机（cyberpunk / detective / sci_fi / fantasy /"
echo "          steampunk / post_apocalyptic / mystery / techno_thriller）"
echo "========================================="

# 验证配置文件
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Error: 配置文件不存在: $CONFIG_FILE"
    exit 1
fi

# 清理 Python 缓存
echo "清理 Python 缓存以确保语言设置生效..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo "✓ Python 缓存已清理"
echo ""

# 确保输出目录存在
mkdir -p ./data_en2/${DIFFICULTY}/dag
mkdir -p ./data_en2/${DIFFICULTY}/sources
mkdir -p ./data_en2/${DIFFICULTY}/inits
mkdir -p ./data_en2/${DIFFICULTY}/full
mkdir -p ./data_en2/${DIFFICULTY}/narrative
mkdir -p ./data_en2/${DIFFICULTY}/wrongs

# 创建日志目录
LOG_DIR="./narrative_generation_logs_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"
echo "Narrative 生成日志将保存到: $LOG_DIR"
echo ""

# =========================================
# 文件名冲突检测：收集已存在的 skeleton 文件名
# =========================================
echo "检查已存在的文件..."
EXISTING_FILES_SET=""
for dir in dag sources inits full narrative wrongs; do
    if [ -d "./data_en2/${DIFFICULTY}/$dir" ]; then
        for file in ./data_en2/${DIFFICULTY}/$dir/skeleton_*.json; do
            if [ -f "$file" ]; then
                basename=$(basename "$file" .json)
                basename=${basename%_dag}
                basename=${basename%_sources}
                basename=${basename%_inits}
                basename=${basename%_full}
                basename=${basename%_narrative}
                EXISTING_FILES_SET="$EXISTING_FILES_SET $basename"
            fi
        done
    fi
done

EXISTING_FILES_SET=$(echo "$EXISTING_FILES_SET" | tr ' ' '\n' | sort -u | tr '\n' ' ')
EXISTING_COUNT=$(echo "$EXISTING_FILES_SET" | wc -w | tr -d ' ')
if [ "$EXISTING_COUNT" -gt 0 ]; then
    echo "✓ 发现 $EXISTING_COUNT 个已存在的 skeleton 文件（将避免覆盖）"
else
    echo "✓ 未发现已存在的文件"
fi

# 创建临时Python脚本用于检查value完整性
cat > /tmp/check_value_completeness.py << 'PYTHON_SCRIPT'
#!/usr/bin/env python3
import json
import sys
from collections import defaultdict

def check_completeness(file_path):
    """检查DAG文件的value完整性，返回True表示完整"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            dag = json.load(f)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        return False

    edges_by_source = defaultdict(dict)
    edges_by_target = defaultdict(dict)

    for edge in dag.get('edges', []):
        source_id = edge['source_id']
        source_port = edge['source_port']
        target_id = edge['target_id']
        target_port = edge['target_port']

        if source_port not in edges_by_source[source_id]:
            edges_by_source[source_id][source_port] = []
        edges_by_source[source_id][source_port].append(edge)

        if target_port not in edges_by_target[target_id]:
            edges_by_target[target_id][target_port] = []
        edges_by_target[target_id][target_port].append(edge)

    for node in dag.get('nodes', []):
        node_id = node['id']

        for port in node.get('inputs', []):
            port_name = port['name']
            port_type = port['type']
            if port_type in ['Item', 'Hidden_Item']:
                continue
            has_edge = port_name in edges_by_target.get(node_id, {})
            has_init_value = 'init_value' in port
            if (has_edge or has_init_value) and 'value' not in port:
                return False

        for port in node.get('outputs', []):
            port_name = port['name']
            port_type = port['type']
            if port_type in ['Item', 'Hidden_Item']:
                has_edge = port_name in edges_by_source.get(node_id, {})
                if not has_edge:
                    if 'value' not in port and 'init_value' not in port:
                        return False
                continue
            if 'value' not in port and 'init_value' not in port:
                return False

    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: check_value_completeness.py <dag_file>", file=sys.stderr)
        sys.exit(1)
    is_complete = check_completeness(sys.argv[1])
    sys.exit(0 if is_complete else 1)
PYTHON_SCRIPT

chmod +x /tmp/check_value_completeness.py

# =========================================
# 单个 DAG 的处理函数（步骤2-6）
# =========================================
process_single_dag() {
    local SKELETON_FILE=$1
    local INDEX=$2
    local TOTAL=$3

    SKELETON_BASENAME=$(basename "$SKELETON_FILE" .json)

    echo ""
    echo "========================================="
    echo "[$INDEX/$TOTAL] 处理: $SKELETON_BASENAME"
    echo "========================================="

    # 第 2 步：标注 DAG sources
    echo "[$INDEX/$TOTAL] [2/6] 标注 DAG sources..."
    if ! python annotate_DAG_sources.py \
        --input "./data_en2/${DIFFICULTY}/dag/${SKELETON_BASENAME}.json" \
        --output "./data_en2/${DIFFICULTY}/sources/${SKELETON_BASENAME}.json" 2>&1; then
        echo "[$INDEX/$TOTAL] ❌ 标注失败"
        return 1
    fi

    # 第 3 步：填充参数
    echo "[$INDEX/$TOTAL] [3/6] 填充参数..."
    if ! PROMPT_LANGUAGE="$PROMPT_LANGUAGE" python dag_parameter_filler.py \
        --skeleton "./data_en2/${DIFFICULTY}/sources/${SKELETON_BASENAME}.json" \
        -o "./data_en2/${DIFFICULTY}/inits/${SKELETON_BASENAME}.json" \
        --client-type "$CLIENT_TYPE" \
        --api-key "$API_KEY" 2>&1; then
        echo "[$INDEX/$TOTAL] ❌ 参数填充失败"
        return 1
    fi

    # 第 4 步：执行 DAG
    echo "[$INDEX/$TOTAL] [4/6] 执行 DAG..."
    if ! python run_dag_executor.py \
        "./data_en2/${DIFFICULTY}/sources/${SKELETON_BASENAME}.json" \
        "./data_en2/${DIFFICULTY}/inits/${SKELETON_BASENAME}.json" \
        "./data_en2/${DIFFICULTY}/full/${SKELETON_BASENAME}.json" 2>&1 | grep -E "(成功|失败|错误|Error)"; then
        echo "[$INDEX/$TOTAL] ❌ DAG 执行失败"
        return 1
    fi

    # 第 4.5 步：检查 value 完整性
    echo "[$INDEX/$TOTAL] [4.5/6] 检查 value 完整性..."
    if ! python /tmp/check_value_completeness.py "./data_en2/${DIFFICULTY}/full/${SKELETON_BASENAME}.json"; then
        echo "[$INDEX/$TOTAL] ⚠️  value 不完整，跳过后续步骤"
        mv "./data_en2/${DIFFICULTY}/dag/${SKELETON_BASENAME}.json"     "./data_en2/${DIFFICULTY}/wrongs/${SKELETON_BASENAME}_dag.json"     2>/dev/null || true
        mv "./data_en2/${DIFFICULTY}/sources/${SKELETON_BASENAME}.json" "./data_en2/${DIFFICULTY}/wrongs/${SKELETON_BASENAME}_sources.json" 2>/dev/null || true
        mv "./data_en2/${DIFFICULTY}/inits/${SKELETON_BASENAME}.json"   "./data_en2/${DIFFICULTY}/wrongs/${SKELETON_BASENAME}_inits.json"   2>/dev/null || true
        mv "./data_en2/${DIFFICULTY}/full/${SKELETON_BASENAME}.json"    "./data_en2/${DIFFICULTY}/wrongs/${SKELETON_BASENAME}_full.json"    2>/dev/null || true
        return 1
    fi
    echo "[$INDEX/$TOTAL] ✅ value 完整，继续后续步骤"

    # 第 5 步：生成 narrative（随机风格）
    echo "[$INDEX/$TOTAL] [5/6] 生成 narrative（随机叙事风格）..."

    local styles=("cyberpunk" "detective" "sci_fi" "fantasy" "steampunk" "post_apocalyptic" "mystery" "techno_thriller")
    local random_index=$((RANDOM % ${#styles[@]}))
    local selected_style="${styles[$random_index]}"
    local log_file="${LOG_DIR}/${SKELETON_BASENAME}.log"
    local output_file="./data_en2/${DIFFICULTY}/narrative/${SKELETON_BASENAME}_narrative.json"

    echo "[$INDEX/$TOTAL]   → 风格: $selected_style"

    if ! python narrative_generator2.py \
        --config "$CONFIG_FILE" \
        --input "./data_en2/${DIFFICULTY}/full/${SKELETON_BASENAME}.json" \
        --output "$output_file" \
        --style "$selected_style" \
        >> "$log_file" 2>&1; then
        echo "[$INDEX/$TOTAL] ❌ Narrative 生成失败（详见 $log_file）"
        return 1
    fi

    # 第 6 步：验证生成的数据
    echo "[$INDEX/$TOTAL] [6/6] 验证生成的数据..."
    if python validate_dag.py "$output_file" 2>&1; then
        echo "[$INDEX/$TOTAL] ✅ 完成: $SKELETON_BASENAME（风格: $selected_style）"
        return 0
    else
        echo "[$INDEX/$TOTAL] ⚠️  验证失败: $SKELETON_BASENAME"
        # validate_dag.py 已自动将 narrative 文件移到 wrongs/
        mv "./data_en2/${DIFFICULTY}/dag/${SKELETON_BASENAME}.json"     "./data_en2/${DIFFICULTY}/wrongs/${SKELETON_BASENAME}_dag.json"     2>/dev/null || true
        mv "./data_en2/${DIFFICULTY}/sources/${SKELETON_BASENAME}.json" "./data_en2/${DIFFICULTY}/wrongs/${SKELETON_BASENAME}_sources.json" 2>/dev/null || true
        mv "./data_en2/${DIFFICULTY}/inits/${SKELETON_BASENAME}.json"   "./data_en2/${DIFFICULTY}/wrongs/${SKELETON_BASENAME}_inits.json"   2>/dev/null || true
        mv "./data_en2/${DIFFICULTY}/full/${SKELETON_BASENAME}.json"    "./data_en2/${DIFFICULTY}/wrongs/${SKELETON_BASENAME}_full.json"    2>/dev/null || true
        return 1
    fi
}

export -f process_single_dag
export PROMPT_LANGUAGE
export CONFIG_FILE
export LOG_DIR
export API_KEY
export CLIENT_TYPE
export DIFFICULTY

# =========================================
# 第 1 步：生成所有 DAG skeleton（启用同构检查）
# =========================================
echo ""
echo "[步骤 1/6] 生成 $COUNT 个 DAG skeleton（启用同构去重）..."

TEMP_BACKUP_DIR=$(mktemp -d)
echo "  → 临时备份已存在文件到: $TEMP_BACKUP_DIR"

BEFORE_FILES=()
if [ -d "./data_en2/${DIFFICULTY}/dag" ]; then
    for file in ./data_en2/${DIFFICULTY}/dag/skeleton_*.json; do
        if [ -f "$file" ]; then
            BEFORE_FILES+=("$file")
            mv "$file" "$TEMP_BACKUP_DIR/"
        fi
    done
fi

BEFORE_COUNT=${#BEFORE_FILES[@]}
if [ $BEFORE_COUNT -gt 0 ]; then
    echo "  → 已备份 $BEFORE_COUNT 个已存在的文件"
fi

python dag_skeleton_generator.py \
    --count "$COUNT" \
    --difficulty "$DIFFICULTY" \
    --droppable-ratio "$DROPPABLE_RATIO" \
    --output ./data_en2/${DIFFICULTY}/dag \
    --check-isomorphism

# 恢复备份的文件
if [ $BEFORE_COUNT -gt 0 ]; then
    echo "  → 恢复备份文件..."
    NAME_COLLISION_COUNT=0
    for backup_file in "$TEMP_BACKUP_DIR"/skeleton_*.json; do
        if [ -f "$backup_file" ]; then
            backup_basename=$(basename "$backup_file")
            target_file="./data_en2/${DIFFICULTY}/dag/$backup_basename"

            if [ -f "$target_file" ]; then
                echo "    ⚠️  文件名冲突: $backup_basename（新旧文件重名）"
                if python3 check_dag_isomorphism.py "$target_file" "$TEMP_BACKUP_DIR" > /dev/null 2>&1; then
                    timestamp=$(date +%Y%m%d_%H%M%S)_$$_$RANDOM
                    new_name="${backup_basename%.json}_new_${timestamp}.json"
                    echo "        → 新旧文件不同构，重命名新文件为: $new_name"
                    mv "$target_file" "./data_en2/${DIFFICULTY}/dag/$new_name"
                    mv "$backup_file" "$target_file"
                    NAME_COLLISION_COUNT=$((NAME_COLLISION_COUNT + 1))
                else
                    echo "        → 新旧文件同构，删除新生成的文件，保留原文件"
                    rm "$target_file"
                    mv "$backup_file" "$target_file"
                fi
            else
                mv "$backup_file" "$target_file"
            fi
        fi
    done

    if [ $NAME_COLLISION_COUNT -gt 0 ]; then
        echo "  → 处理了 $NAME_COLLISION_COUNT 个文件名冲突（极罕见）"
    fi
fi

rmdir "$TEMP_BACKUP_DIR" 2>/dev/null || true

# 新旧同构检查
echo "  → 检查新生成文件与已存在文件的同构..."
NEW_FILES_TEMP=($(ls -t ./data_en2/${DIFFICULTY}/dag/skeleton_*.json 2>/dev/null))
ISOMORPHIC_REMOVED=0

for new_file in "${NEW_FILES_TEMP[@]}"; do
    new_basename=$(basename "$new_file")
    is_old=false
    for old_file in "${BEFORE_FILES[@]}"; do
        if [ "$(basename "$old_file")" = "$new_basename" ]; then
            is_old=true
            break
        fi
    done
    if [ "$is_old" = true ]; then
        continue
    fi

    for old_file in "${BEFORE_FILES[@]}"; do
        if python3 check_dag_isomorphism.py "$new_file" "$(dirname "$old_file")" > /dev/null 2>&1; then
            continue
        else
            exit_code=$?
            if [ $exit_code -eq 1 ]; then
                echo "    ⚠️  删除同构文件: $(basename "$new_file") 与 $(basename "$old_file") 同构"
                rm "$new_file"
                ISOMORPHIC_REMOVED=$((ISOMORPHIC_REMOVED + 1))
                break
            fi
        fi
    done
done

if [ $ISOMORPHIC_REMOVED -gt 0 ]; then
    echo "  → 已删除 $ISOMORPHIC_REMOVED 个与已存在文件同构的新文件"
fi

# 获取最终新文件列表
ALL_NEW_FILES=()
AFTER_FILES=($(ls ./data_en2/${DIFFICULTY}/dag/skeleton_*.json 2>/dev/null | sort))
for file in "${AFTER_FILES[@]}"; do
    is_old=false
    for old_file in "${BEFORE_FILES[@]}"; do
        if [ "$file" = "$old_file" ]; then
            is_old=true
            break
        fi
    done
    if [ "$is_old" = false ]; then
        ALL_NEW_FILES+=("$file")
    fi
done

NEW_FILES_COUNT=${#ALL_NEW_FILES[@]}
echo "✓ 本次新生成 $NEW_FILES_COUNT 个 DAG 文件（已去除同构）"
echo ""
echo "✓ 跳过与历史失败 DAG 的同构检查（允许重试）"

SKELETON_FILES=($(ls -t ./data_en2/${DIFFICULTY}/dag/skeleton_*.json 2>/dev/null | head -n "$COUNT"))
ACTUAL_COUNT=${#SKELETON_FILES[@]}

if [ $ACTUAL_COUNT -eq 0 ]; then
    echo "错误: 没有找到生成的 skeleton 文件"
    exit 1
fi

echo "实际生成了 $ACTUAL_COUNT 个非同构 DAG 文件"

# =========================================
# 并行处理步骤 2~6
# =========================================
echo ""
echo "========================================="
echo "开始并行处理（并行数: $PARALLEL）"
echo "========================================="

if command -v parallel &> /dev/null; then
    export -f process_single_dag
    printf "%s\n" "${SKELETON_FILES[@]}" | \
    parallel -j "$PARALLEL" --line-buffer --tagstring "[{#}]" \
        process_single_dag {} {#} $ACTUAL_COUNT
else
    export -f process_single_dag
    printf "%s\n" "${SKELETON_FILES[@]}" | \
    xargs -P "$PARALLEL" -I {} bash -c \
        'export PROMPT_LANGUAGE='"$PROMPT_LANGUAGE"'; export CONFIG_FILE='"$CONFIG_FILE"'; export LOG_DIR='"$LOG_DIR"'; process_single_dag "$@"' _ {} 1 $ACTUAL_COUNT
fi

# =========================================
# 统计结果
# =========================================
echo ""
echo "========================================="
echo "处理完成"
echo "========================================="

SUCCESS_COUNT=0
FAIL_COUNT=0
INCOMPLETE_COUNT=0

for SKELETON_FILE in "${SKELETON_FILES[@]}"; do
    SKELETON_BASENAME=$(basename "$SKELETON_FILE" .json)

    if [ -f "./data_en2/${DIFFICULTY}/wrongs/${SKELETON_BASENAME}_full.json" ]; then
        INCOMPLETE_COUNT=$((INCOMPLETE_COUNT + 1))
        continue
    fi

    NARRATIVE_FILE="./data_en2/${DIFFICULTY}/narrative/${SKELETON_BASENAME}_narrative.json"
    if [ -f "$NARRATIVE_FILE" ]; then
        if python validate_dag.py "$NARRATIVE_FILE" &> /dev/null; then
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        else
            FAIL_COUNT=$((FAIL_COUNT + 1))
        fi
    else
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
done

echo "总计处理: $ACTUAL_COUNT 个"
echo "✅ 成功: $SUCCESS_COUNT 个"
echo "❌ 失败: $FAIL_COUNT 个"
echo "⚠️  value不完整: $INCOMPLETE_COUNT 个"
echo ""
echo "输出目录:"
echo "  - 成功的数据: ./data_en2/${DIFFICULTY}/narrative/"
  echo "  - 不完整/失败的: ./data_en2/${DIFFICULTY}/wrongs/"
echo "  - Narrative 日志: $LOG_DIR/"
echo "========================================="

# 列出失败文件
FAILED_LOGS=$(grep -l "❌ Failed\|❌" "$LOG_DIR"/*.log 2>/dev/null)
if [ -n "$FAILED_LOGS" ]; then
    echo ""
    echo "失败文件详情（查看对应 log）:"
    echo "$FAILED_LOGS" | while read log_file; do
        echo "  - $(basename "$log_file" .log)"
    done
fi

# 清理临时脚本
rm -f /tmp/check_value_completeness.py

if [ $SUCCESS_COUNT -eq 0 ]; then
    exit 1
fi
