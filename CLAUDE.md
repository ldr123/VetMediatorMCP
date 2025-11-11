# Claude Code 开发指南

## 🤝 CLI工具交叉验证

**触发词**：`使用vet验证` 或 `让vet帮我验证` 或 `使用CLI工具交叉验证`

**执行步骤**：
1. 读取规则文件：`rules/rule-agent-file-generator.md`
2. 按规则生成ReviewIndex.md和多个任务文件（UTF-8编码）
3. 调用MCP工具：`mcp__vet-mediator-mcp__start_review`
   - 必需参数：`review_index_path`、`draft_paths`、`project_root`
   - 推荐参数：`initiator="Claude Code"`（标识发起审查的AI工具）

**支持的CLI工具**：
- iFlow（默认）
- Claude Code
- 其他AI代码审查工具（通过配置文件`.VetMediatorSetting.json`指定）

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

