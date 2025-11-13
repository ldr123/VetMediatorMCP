#!/bin/bash

# VetMediator MCP 一键安装脚本
# 支持 macOS, Linux, Windows (Git Bash)

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
    echo -e "${BLUE}  VetMediator MCP 安装向导    ${NC}"
    echo -e "${BLUE}================================${NC}"
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查依赖
check_dependencies() {
    print_message "检查系统依赖..."

    local missing_deps=()

    # 检查 Python 版本
    if command_exists python3; then
        local python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        local python_major=$(echo "$python_version" | cut -d. -f1)
        local python_minor=$(echo "$python_version" | cut -d. -f2)

        if [ "$python_major" -lt 3 ] || ([ "$python_major" -eq 3 ] && [ "$python_minor" -lt 10 ]); then
            print_error "Python 版本过低: $python_version (需要 3.10+)"
            missing_deps+=("Python 3.10+")
        else
            print_message "Python 版本: $python_version ✓"
        fi
    else
        missing_deps+=("Python 3.10+")
    fi

    # 检查 uvx/uv
    if ! command_exists uvx && ! command_exists uv; then
        missing_deps+=("uvx/uv")
    else
        print_message "uvx/uv 已安装 ✓"
    fi

    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "缺少以下依赖: ${missing_deps[*]}"
        echo ""
        print_message "安装建议:"
        echo "  Python 3.10+: https://www.python.org/"
        echo "  uv: pip install uv"
        exit 1
    fi

    print_message "所有依赖检查通过 ✓"
}

# 检测项目根目录
get_project_root() {
    # 优先使用当前目录
    local current_dir=$(pwd)

    # 检查是否在 VetMediatorMCP 项目目录中
    if [ -f "$current_dir/pyproject.toml" ] && grep -q "vet-mediator-mcp" "$current_dir/pyproject.toml" 2>/dev/null; then
        echo "$current_dir"
        return 0
    fi

    # 如果不在项目目录，询问用户
    echo ""
    print_warning "未检测到 VetMediatorMCP 项目目录"
    read -p "请输入项目根目录路径（或按 Enter 使用当前目录）: " user_input

    if [ -z "$user_input" ]; then
        echo "$current_dir"
    else
        echo "$user_input"
    fi
}

# 生成 .mcp.json 配置
generate_mcp_config() {
    local project_root=$1
    local config_file="$project_root/.mcp.json"

    if [ -f "$config_file" ]; then
        print_warning ".mcp.json 已存在，跳过创建"
        return 0
    fi

    print_message "生成 .mcp.json 配置文件..."

    # 检测是否在中国（通过是否能访问GitHub）
    local use_mirror=false
    if ! curl -s --connect-timeout 3 https://github.com >/dev/null 2>&1; then
        print_warning "GitHub连接较慢，建议使用Gitee镜像"
        read -p "是否使用Gitee镜像？(Y/n): " use_gitee
        if [[ ! "$use_gitee" =~ ^[Nn]$ ]]; then
            use_mirror=true
        fi
    fi

    local git_url
    if [ "$use_mirror" = true ]; then
        git_url="git+https://gitee.com/ldr123/VetMediatorMCP.git"
    else
        git_url="git+https://github.com/ldr123/VetMediatorMCP.git"
    fi

    cat > "$config_file" << EOF
{
  "mcpServers": {
    "vet-mediator-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "$git_url",
        "vet-mediator-mcp"
      ]
    }
  }
}
EOF

    print_message ".mcp.json 生成完成 ✓"
}

# 检测已安装的CLI工具
detect_cli_tools() {
    print_message "检测已安装的CLI审查工具..."

    local found_tools=()

    if command_exists iflow; then
        found_tools+=("iFlow CLI")
        print_message "  ✓ iFlow CLI ($(iflow --version 2>/dev/null || echo 'unknown'))"
    fi

    if command_exists codex; then
        found_tools+=("Codex CLI")
        print_message "  ✓ Codex CLI ($(codex --version 2>/dev/null || echo 'unknown'))"
    fi

    if command_exists claude; then
        found_tools+=("Claude CLI")
        print_message "  ✓ Claude CLI ($(claude --version 2>/dev/null || echo 'unknown'))"
    fi

    if [ ${#found_tools[@]} -eq 0 ]; then
        print_warning "未检测到任何CLI审查工具"
        echo ""
        print_message "推荐安装 iFlow CLI:"
        echo "  npm install -g @iflow-ai/iflow-cli"
        echo ""
        print_message "或安装其他CLI工具:"
        echo "  Codex: npm install -g @openai/codex"
        echo "  Claude: npm install -g @anthropic-ai/claude-code"
        echo ""
        read -p "是否继续安装（稍后可手动安装CLI工具）？(Y/n): " continue_install
        if [[ "$continue_install" =~ ^[Nn]$ ]]; then
            print_error "安装已取消"
            exit 1
        fi
    else
        print_message "检测到 ${#found_tools[@]} 个CLI工具 ✓"
    fi
}

# 注入规则到 CLAUDE.md
inject_rules() {
    local project_root=$1
    local claude_md="$project_root/CLAUDE.md"
    local rules_file="$project_root/rules/CLAUDE.md"

    # 检查规则文件是否存在
    if [ ! -f "$rules_file" ]; then
        print_warning "规则文件不存在: $rules_file"
        return 0
    fi

    echo ""
    print_message "是否向 CLAUDE.md 注入VetMediator使用规则？"
    echo "  这将在CLAUDE.md开头添加VetMediator的MCP调用规则"
    read -p "注入规则到 CLAUDE.md？(Y/n): " inject_confirm

    if [[ "$inject_confirm" =~ ^[Nn]$ ]]; then
        print_message "跳过规则注入"
        return 0
    fi

    # 检查是否已经注入过
    if [ -f "$claude_md" ] && grep -q "CLI Tool Cross-Validation" "$claude_md" 2>/dev/null; then
        print_warning "CLAUDE.md 已包含VetMediator规则，跳过注入"
        return 0
    fi

    # 创建备份
    if [ -f "$claude_md" ]; then
        cp "$claude_md" "$claude_md.backup"
        print_message "已备份现有CLAUDE.md到 CLAUDE.md.backup"
    fi

    # 注入规则
    if [ -f "$claude_md" ]; then
        # 在现有文件开头插入规则
        cat "$rules_file" <(echo) <(cat "$claude_md") > "$claude_md.tmp"
        mv "$claude_md.tmp" "$claude_md"
    else
        # 创建新文件
        cp "$rules_file" "$claude_md"
    fi

    print_message "规则注入完成 ✓"
}

# 创建工作目录
create_working_directories() {
    local project_root=$1
    local sessions_dir="$project_root/VetMediatorSessions"

    if [ ! -d "$sessions_dir" ]; then
        mkdir -p "$sessions_dir"
        print_message "创建 VetMediatorSessions/ 目录 ✓"
    else
        print_message "VetMediatorSessions/ 目录已存在 ✓"
    fi
}

# 验证安装
verify_installation() {
    local project_root=$1
    print_message "验证安装..."

    local all_ok=true

    # 检查 .mcp.json
    if [ -f "$project_root/.mcp.json" ]; then
        print_message "  ✓ .mcp.json 配置文件"
    else
        print_error "  ✗ .mcp.json 配置文件缺失"
        all_ok=false
    fi

    # 检查 VetMediatorSessions 目录
    if [ -d "$project_root/VetMediatorSessions" ]; then
        print_message "  ✓ VetMediatorSessions/ 目录"
    else
        print_error "  ✗ VetMediatorSessions/ 目录缺失"
        all_ok=false
    fi

    if [ "$all_ok" = true ]; then
        print_message "安装验证完成 ✓"
        return 0
    else
        print_error "安装验证失败"
        return 1
    fi
}

# 显示完成信息
show_completion() {
    local project_root=$1
    echo ""
    print_header
    print_message "🎉 VetMediator MCP 安装完成！"
    echo ""
    print_message "配置文件位置:"
    echo "  $project_root/.mcp.json"
    echo ""
    print_message "下一步操作:"
    echo "1. 重启您的AI工具（Claude Code / Cursor等）"
    echo "2. 在AI工具中输入: 查看CLI配置"
    echo "3. 确认能看到 vet-mediator-mcp 工具"
    echo ""
    print_message "快速验证:"
    echo "  运行验证脚本: ./verify-config.sh"
    echo ""
    print_message "使用方法:"
    echo "  在AI工具中说: 使用vet验证"
    echo ""
    print_message "如遇问题，请查看:"
    echo "  文档: docs/zh/README.md"
    echo "  快速开始: docs/QUICKSTART.md"
    echo "  故障排除: docs/zh/README.md#故障排除"
    echo ""
}

# 主函数
main() {
    print_header
    echo ""

    # 检查依赖
    check_dependencies
    echo ""

    # 获取项目根目录
    print_message "检测项目根目录..."
    PROJECT_ROOT=$(get_project_root)
    print_message "项目根目录: $PROJECT_ROOT"
    echo ""

    # 生成 .mcp.json 配置
    generate_mcp_config "$PROJECT_ROOT"
    echo ""

    # 检测CLI工具
    detect_cli_tools
    echo ""

    # 注入规则
    inject_rules "$PROJECT_ROOT"
    echo ""

    # 创建工作目录
    create_working_directories "$PROJECT_ROOT"
    echo ""

    # 验证安装
    verify_installation "$PROJECT_ROOT"
    echo ""

    # 显示完成信息
    show_completion "$PROJECT_ROOT"
}

# 运行主函数
main "$@"
