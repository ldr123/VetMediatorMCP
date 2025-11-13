#!/bin/bash

# VetMediator MCP 配置验证脚本
# 检查配置是否正确并可以正常工作

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 计数器
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# 打印带颜色的消息
print_success() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED_CHECKS++))
}

print_error() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED_CHECKS++))
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# 检查函数
check_command() {
    local cmd=$1
    local description=$2
    ((TOTAL_CHECKS++))

    print_info "检查 $description..."
    if command -v "$cmd" >/dev/null 2>&1; then
        local version=$($cmd --version 2>&1 | head -n1 || echo "unknown")
        print_success "$description 已安装 ($version)"
        return 0
    else
        print_error "$description 未找到"
        return 1
    fi
}

check_python_version() {
    ((TOTAL_CHECKS++))

    print_info "检查 Python 版本..."
    if command -v python3 >/dev/null 2>&1; then
        local version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        local major=$(echo "$version" | cut -d. -f1)
        local minor=$(echo "$version" | cut -d. -f2)

        if [ "$major" -ge 3 ] && [ "$minor" -ge 10 ]; then
            print_success "Python 版本正确 (Python $version)"
            return 0
        else
            print_error "Python 版本过低 (Python $version, 需要 3.10+)"
            return 1
        fi
    else
        print_error "Python 未找到"
        return 1
    fi
}

check_file() {
    local file=$1
    local description=$2
    ((TOTAL_CHECKS++))

    print_info "检查 $description..."
    if [ -f "$file" ]; then
        print_success "$description 存在"
        return 0
    else
        print_error "$description 不存在"
        return 1
    fi
}

check_directory() {
    local dir=$1
    local description=$2
    ((TOTAL_CHECKS++))

    print_info "检查 $description..."
    if [ -d "$dir" ]; then
        print_success "$description 存在"
        return 0
    else
        print_error "$description 不存在"
        return 1
    fi
}

validate_json() {
    local file=$1
    ((TOTAL_CHECKS++))

    print_info "验证 JSON 格式..."
    if python3 -m json.tool "$file" >/dev/null 2>&1; then
        print_success "JSON 格式正确"
        return 0
    else
        print_error "JSON 格式错误"
        return 1
    fi
}

check_mcp_config_content() {
    local file=$1
    ((TOTAL_CHECKS++))

    print_info "检查 .mcp.json 内容..."
    if grep -q "vet-mediator-mcp" "$file" 2>/dev/null; then
        print_success ".mcp.json 包含 vet-mediator-mcp 配置"
        return 0
    else
        print_error ".mcp.json 缺少 vet-mediator-mcp 配置"
        return 1
    fi
}

check_claude_md_rules() {
    local file=$1
    ((TOTAL_CHECKS++))

    print_info "检查 CLAUDE.md 规则..."
    if [ ! -f "$file" ]; then
        print_warning "CLAUDE.md 不存在（如使用其他AI工具可忽略）"
        return 0
    fi

    if grep -q "CLI Tool Cross-Validation" "$file" 2>/dev/null; then
        print_success "CLAUDE.md 包含 VetMediator 规则"
        return 0
    else
        print_warning "CLAUDE.md 未包含 VetMediator 规则（需要手动添加）"
        return 0
    fi
}

check_cli_tools() {
    print_info "检查已安装的 CLI 审查工具..."

    local found=0

    if command -v iflow >/dev/null 2>&1; then
        print_success "  iFlow CLI 可用"
        found=1
    fi

    if command -v codex >/dev/null 2>&1; then
        print_success "  Codex CLI 可用"
        found=1
    fi

    if command -v claude >/dev/null 2>&1; then
        print_success "  Claude CLI 可用"
        found=1
    fi

    if [ $found -eq 0 ]; then
        print_warning "  未检测到任何 CLI 审查工具（需要安装至少一个）"
    fi
}

check_directory_permissions() {
    local dir=$1
    ((TOTAL_CHECKS++))

    print_info "检查 VetMediatorSessions/ 目录权限..."
    if [ -w "$dir" ]; then
        print_success "VetMediatorSessions/ 目录可写"
        return 0
    else
        print_error "VetMediatorSessions/ 目录不可写"
        return 1
    fi
}

# 获取项目根目录
get_project_root() {
    local current_dir=$(pwd)

    # 检查当前目录是否是项目根目录
    if [ -f "$current_dir/pyproject.toml" ] && grep -q "vet-mediator-mcp" "$current_dir/pyproject.toml" 2>/dev/null; then
        echo "$current_dir"
        return 0
    fi

    # 检查是否在项目子目录中
    local parent_dir=$(dirname "$current_dir")
    if [ -f "$parent_dir/pyproject.toml" ] && grep -q "vet-mediator-mcp" "$parent_dir/pyproject.toml" 2>/dev/null; then
        echo "$parent_dir"
        return 0
    fi

    # 未找到，使用当前目录
    echo "$current_dir"
}

# 主验证函数
main() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  VetMediator MCP 配置验证    ${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""

    # 获取项目根目录
    PROJECT_ROOT=$(get_project_root)
    print_info "项目根目录: $PROJECT_ROOT"
    echo ""

    # 检查基本依赖
    print_info "检查系统依赖..."
    check_python_version

    # 检查 uvx/uv
    if command -v uvx >/dev/null 2>&1; then
        check_command "uvx" "uvx"
    elif command -v uv >/dev/null 2>&1; then
        check_command "uv" "uv"
    else
        ((TOTAL_CHECKS++))
        print_error "uvx/uv 未找到"
    fi
    echo ""

    # 检查配置文件
    print_info "检查配置文件..."
    local mcp_config="$PROJECT_ROOT/.mcp.json"
    check_file "$mcp_config" ".mcp.json 配置文件"

    if [ -f "$mcp_config" ]; then
        validate_json "$mcp_config"
        check_mcp_config_content "$mcp_config"
    fi
    echo ""

    # 检查 CLAUDE.md 规则
    print_info "检查 AI 工具规则文件..."
    check_claude_md_rules "$PROJECT_ROOT/CLAUDE.md"
    echo ""

    # 检查 CLI 工具
    print_info "检查 CLI 审查工具..."
    check_cli_tools
    echo ""

    # 检查工作目录
    print_info "检查工作目录..."
    local sessions_dir="$PROJECT_ROOT/VetMediatorSessions"
    check_directory "$sessions_dir" "VetMediatorSessions/ 目录"

    if [ -d "$sessions_dir" ]; then
        check_directory_permissions "$sessions_dir"
    fi
    echo ""

    # 显示验证结果
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}        验证结果总结            ${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
    echo -e "总检查项: ${BLUE}$TOTAL_CHECKS${NC}"
    echo -e "通过检查: ${GREEN}$PASSED_CHECKS${NC}"
    echo -e "失败检查: ${RED}$FAILED_CHECKS${NC}"
    echo ""

    if [ $FAILED_CHECKS -eq 0 ]; then
        print_success "🎉 所有检查通过！配置完全正确"
        echo ""
        print_info "下一步:"
        echo "1. 重启您的 AI 工具（Claude Code / Cursor 等）"
        echo "2. 在 AI 工具中输入: 查看CLI配置"
        echo "3. 确认能看到 vet-mediator-mcp 工具"
        echo ""
        print_info "使用方法:"
        echo "  在 AI 工具中说: 使用vet验证"
        exit 0
    else
        print_error "发现 $FAILED_CHECKS 个问题需要修复"
        echo ""
        print_info "修复建议:"
        echo "1. 重新运行安装脚本: ./install.sh"
        echo "2. 查看故障排除指南: docs/zh/README.md#故障排除"
        echo "3. 在 GitHub Issues 提交问题"
        exit 1
    fi
}

# 运行主函数
main "$@"
