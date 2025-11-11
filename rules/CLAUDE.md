# Claude Code 开发指南

## 🤝 CLI工具交叉验证

**触发词**：`使用vet验证` 或 `让vet帮我验证` 或 `使用CLI工具交叉验证`

**执行步骤（智能缓存，节省Token）**：

### Step 1: 获取最新规则（自动缓存）
1. 调用 `mcp__vet-mediator-mcp__get_review_rule_hash` 获取当前规则版本hash
2. 检查本地 `~/.vetmediator/` 目录是否有对应hash的缓存文件
3. **如无缓存**：调用 `mcp__vet-mediator-mcp__get_review_rules(rule_type="file-generator")` 下载并保存
4. **如有缓存**：直接读取本地文件（节省~4000 tokens）

### Step 2-N: 按规则执行审查流程
- 读取规则文件，了解所有文件格式和MCP调用方式
- 生成必需文件并调用 `mcp__vet-mediator-mcp__start_review` 启动审查
- 详细规则见缓存文件

**支持的CLI工具**：
- iFlow（默认）
- Claude Code
- 其他AI代码审查工具（通过配置文件指定）

## 🔧 CLI工具配置管理

**触发词**：`查看CLI配置` 或 `切换CLI工具` 或 `show cli config`

**功能说明**：
- 显示GUI界面查看所有配置的CLI工具状态
- 实时检查每个工具的健康状态（是否已安装）
- 允许用户一键切换当前激活的CLI工具
- 显示配置文件路径（全局和项目）

**执行步骤**：
调用MCP工具：`mcp__vet-mediator-mcp__show_cli_config`
- 必需参数：`project_root`（项目根目录路径）

