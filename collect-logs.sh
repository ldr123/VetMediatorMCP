#!/bin/bash

# VetMediator MCP 日志收集脚本
# 收集诊断信息以便排查问题

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 打印带颜色的消息
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  VetMediator MCP 日志收集    ${NC}"
    echo -e "${BLUE}================================${NC}"
}

# 获取项目根目录
get_project_root() {
    local current_dir=$(pwd)

    # 检查当前目录
    if [ -f "$current_dir/pyproject.toml" ] && grep -q "vet-mediator-mcp" "$current_dir/pyproject.toml" 2>/dev/null; then
        echo "$current_dir"
        return 0
    fi

    # 检查父目录
    local parent_dir=$(dirname "$current_dir")
    if [ -f "$parent_dir/pyproject.toml" ] && grep -q "vet-mediator-mcp" "$parent_dir/pyproject.toml" 2>/dev/null; then
        echo "$parent_dir"
        return 0
    fi

    # 未找到，使用当前目录
    echo "$current_dir"
}

# 创建临时目录
create_temp_dir() {
    local temp_dir=$(mktemp -d)
    echo "$temp_dir"
}

# 收集系统信息
collect_system_info() {
    local output_file=$1

    print_message "收集系统信息..."

    cat > "$output_file" << EOF
=== VetMediator MCP 诊断信息 ===
生成时间: $(date)

=== 系统信息 ===
操作系统: $(uname -s)
系统版本: $(uname -r)
架构: $(uname -m)

=== Python 信息 ===
EOF

    if command -v python3 >/dev/null 2>&1; then
        echo "Python 版本: $(python3 --version)" >> "$output_file"
        echo "Python 路径: $(which python3)" >> "$output_file"
    else
        echo "Python: 未找到" >> "$output_file"
    fi

    cat >> "$output_file" << EOF

=== uvx/uv 信息 ===
EOF

    if command -v uvx >/dev/null 2>&1; then
        echo "uvx 版本: $(uvx --version 2>&1)" >> "$output_file"
        echo "uvx 路径: $(which uvx)" >> "$output_file"
    elif command -v uv >/dev/null 2>&1; then
        echo "uv 版本: $(uv --version 2>&1)" >> "$output_file"
        echo "uv 路径: $(which uv)" >> "$output_file"
    else
        echo "uvx/uv: 未找到" >> "$output_file"
    fi

    cat >> "$output_file" << EOF

=== CLI 审查工具 ===
EOF

    if command -v iflow >/dev/null 2>&1; then
        echo "iFlow: $(iflow --version 2>&1 | head -n1)" >> "$output_file"
    else
        echo "iFlow: 未安装" >> "$output_file"
    fi

    if command -v codex >/dev/null 2>&1; then
        echo "Codex: $(codex --version 2>&1 | head -n1)" >> "$output_file"
    else
        echo "Codex: 未安装" >> "$output_file"
    fi

    if command -v claude >/dev/null 2>&1; then
        echo "Claude: $(claude --version 2>&1 | head -n1)" >> "$output_file"
    else
        echo "Claude: 未安装" >> "$output_file"
    fi

    print_message "系统信息收集完成 ✓"
}

# 收集配置文件
collect_config_files() {
    local project_root=$1
    local temp_dir=$2

    print_message "收集配置文件..."

    # 收集 .mcp.json
    if [ -f "$project_root/.mcp.json" ]; then
        cp "$project_root/.mcp.json" "$temp_dir/mcp-config.json"
        print_message "  ✓ .mcp.json"
    else
        echo "文件不存在" > "$temp_dir/mcp-config-missing.txt"
        print_warning "  ⚠ .mcp.json 不存在"
    fi

    # 收集 CLAUDE.md（前100行，避免泄露敏感信息）
    if [ -f "$project_root/CLAUDE.md" ]; then
        head -n 100 "$project_root/CLAUDE.md" > "$temp_dir/CLAUDE-head.md"
        print_message "  ✓ CLAUDE.md（前100行）"
    fi

    # 收集 .VetMediatorSetting.json
    if [ -f "$project_root/.VetMediatorSetting.json" ]; then
        cp "$project_root/.VetMediatorSetting.json" "$temp_dir/VetMediatorSetting.json"
        print_message "  ✓ .VetMediatorSetting.json"
    fi

    # 收集全局配置
    local global_config="$HOME/.vetmediator/config.json"
    if [ -f "$global_config" ]; then
        cp "$global_config" "$temp_dir/global-config.json"
        print_message "  ✓ 全局配置"
    fi

    print_message "配置文件收集完成 ✓"
}

# 收集 session 日志
collect_session_logs() {
    local project_root=$1
    local temp_dir=$2

    print_message "收集最近的 session 日志..."

    local sessions_dir="$project_root/VetMediatorSessions"
    if [ ! -d "$sessions_dir" ]; then
        print_warning "  ⚠ VetMediatorSessions/ 目录不存在"
        return 0
    fi

    # 创建 sessions 目录
    mkdir -p "$temp_dir/sessions"

    # 获取最近3个 session
    local count=0
    for session in $(ls -t "$sessions_dir" | head -n 3); do
        if [ -d "$sessions_dir/$session" ]; then
            # 复制整个 session 目录（排除大文件）
            mkdir -p "$temp_dir/sessions/$session"

            # 复制日志文件
            find "$sessions_dir/$session" -name "*.log" -exec cp {} "$temp_dir/sessions/$session/" \; 2>/dev/null || true

            # 复制报告文件
            find "$sessions_dir/$session" -name "Report.md" -exec cp {} "$temp_dir/sessions/$session/" \; 2>/dev/null || true

            # 复制进度文件
            find "$sessions_dir/$session" -name "progress.json" -exec cp {} "$temp_dir/sessions/$session/" \; 2>/dev/null || true

            ((count++))
            print_message "  ✓ Session: $session"
        fi
    done

    if [ $count -eq 0 ]; then
        print_warning "  ⚠ 未找到任何 session"
    else
        print_message "Session 日志收集完成 ✓（共 $count 个）"
    fi
}

# 收集错误日志
collect_error_logs() {
    local project_root=$1
    local temp_dir=$2

    print_message "搜索错误日志..."

    # 搜索最近的错误
    local sessions_dir="$project_root/VetMediatorSessions"
    if [ -d "$sessions_dir" ]; then
        # 收集所有包含 ERROR 或 FAILED 的日志行
        grep -r "ERROR\|FAILED\|Exception\|Traceback" "$sessions_dir" 2>/dev/null | tail -n 100 > "$temp_dir/errors.txt" || true

        if [ -s "$temp_dir/errors.txt" ]; then
            print_message "  ✓ 找到错误日志"
        else
            echo "未找到错误" > "$temp_dir/no-errors.txt"
            print_message "  ✓ 未找到错误（很好！）"
        fi
    fi
}

# 打包文件
package_files() {
    local temp_dir=$1
    local project_root=$2

    print_message "打包诊断文件..."

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local archive_name="vet-mediator-debug-$timestamp.tar.gz"
    local archive_path="$project_root/$archive_name"

    # 打包
    tar -czf "$archive_path" -C "$(dirname $temp_dir)" "$(basename $temp_dir)" 2>/dev/null

    echo "$archive_path"
}

# 清理临时目录
cleanup() {
    local temp_dir=$1
    rm -rf "$temp_dir"
}

# 主函数
main() {
    print_header
    echo ""

    # 获取项目根目录
    PROJECT_ROOT=$(get_project_root)
    print_message "项目根目录: $PROJECT_ROOT"
    echo ""

    # 创建临时目录
    TEMP_DIR=$(create_temp_dir)
    print_message "临时目录: $TEMP_DIR"
    echo ""

    # 收集系统信息
    collect_system_info "$TEMP_DIR/system-info.txt"
    echo ""

    # 收集配置文件
    collect_config_files "$PROJECT_ROOT" "$TEMP_DIR"
    echo ""

    # 收集 session 日志
    collect_session_logs "$PROJECT_ROOT" "$TEMP_DIR"
    echo ""

    # 收集错误日志
    collect_error_logs "$PROJECT_ROOT" "$TEMP_DIR"
    echo ""

    # 打包文件
    ARCHIVE_PATH=$(package_files "$TEMP_DIR" "$PROJECT_ROOT")
    echo ""

    # 清理临时目录
    cleanup "$TEMP_DIR"

    # 显示完成信息
    print_header
    print_message "🎉 日志收集完成！"
    echo ""
    print_message "诊断文件位置:"
    echo "  $ARCHIVE_PATH"
    echo ""
    print_message "下一步操作:"
    echo "1. 解压查看诊断信息: tar -xzf $(basename $ARCHIVE_PATH)"
    echo "2. 在 GitHub Issues 提交问题时附上此文件"
    echo "3. 注意：请检查文件中是否包含敏感信息（API密钥等）"
    echo ""
    print_message "文件包含:"
    echo "  - 系统信息（OS, Python, uvx版本）"
    echo "  - 配置文件（.mcp.json, CLAUDE.md等）"
    echo "  - 最近3次审查的日志"
    echo "  - 错误日志摘要"
    echo ""
}

# 运行主函数
main "$@"
