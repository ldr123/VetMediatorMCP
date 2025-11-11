# VetMediator MCP

<div align="center">

![Logo](docs/imgs/icon.png)

**AI CLI Tool Review Coordinator**
**AI CLI工具审查协调器**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compatible](https://img.shields.io/badge/MCP-1.0.0+-green.svg)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

*Enable AI agents to invoke other CLI review tools for cross-validation*
*让AI代理调用其他CLI审查工具进行代码交叉验证*

---

## 📖 Documentation / 文档

### Choose Your Language / 选择语言

<table>
<tr>
<td width="50%" align="center">

### [🇨🇳 中文文档](docs/zh/README.md)

完整的中文使用指南

**包含内容**：
- ✨ 核心特性
- 🎬 完整工作流程
- 🚀 快速开始
- 🔧 配置管理
- 🛠️ 故障排除

</td>
<td width="50%" align="center">

### [🇬🇧 English Documentation](docs/en/README.md)

Complete English guide

**Includes**:
- ✨ Core Features
- 🎬 Complete Workflow
- 🚀 Quick Start
- 🔧 Configuration
- 🛠️ Troubleshooting

</td>
</tr>
</table>

---

## 🚀 Quick Start / 快速开始

### Prerequisites / 前置要求

- **Python 3.10+** - [Download](https://python.org)
- **uvx** - Python package runner (installed with uv): `pip install uv` / Python包运行器：`pip install uv`
- **MCP-compatible AI agent** - e.g., Claude Code, Cursor, etc. / MCP兼容的AI代理，如Claude Code、Cursor等
- **CLI review tool** - e.g., Codex, Claude CLI or iFlow (at least one required) / CLI审查工具，如Codex、Claude CLI或iFlow（至少一个）

### Installation / 安装

**Using uvx (Recommended) / 使用uvx（推荐）**:

📋 **Step 1: Copy MCP configuration to your project root / 复制MCP配置到项目根目录**

Copy `rules/.mcp.json` from this repository to your project root directory as `.mcp.json`

从本仓库复制 `rules/.mcp.json` 到你的项目根目录并命名为 `.mcp.json`

```json
{
  "mcpServers": {
    "vet-mediator-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/ldr123/VetMediatorMCP.git",
        "vet-mediator-mcp"
      ]
    }
  }
}
```

**China Mirror / 中国镜像**:
```json
"git+https://gitee.com/ldr123/VetMediatorMCP.git"
```

📋 **Step 2: Add VetMediator configuration to your AI tool's rule file / 添加VetMediator配置到AI工具的规则文件**

View the content of `rules/CLAUDE.md` in this repository, and add it to your AI tool's rule file **at the beginning**.

查看本仓库的 `rules/CLAUDE.md` 文件内容，并将其添加到你的AI工具规则文件的**开头部分**。

**Configuration for different AI tools / 不同AI工具的配置方式**:

| AI Tool / 工具 | Rule File / 规则文件 | Location / 位置 | Notes / 说明 |
|----------------|---------------------|----------------|--------------|
| **Claude Code** | `CLAUDE.md` | Project root / 项目根目录 | System default / 系统预设 |
| **Cursor** | `*.mdc` | `.cursor/rules/` | Multi-level priority, auto-load / 多级优先级，自动加载 |
| **Codex** | `AGENTS.md` | Project root / 项目根目录 | Supports global & project level / 支持全局与项目级 |
| **iFlow** | `IFLOW.md` | Project root / 项目根目录 | Supports including other files / 支持包含其他文件 |
| **Gemini CLI** | `GEMINI.md` | Project root / 项目根目录 | Supports module-level rules / 支持模块级规则 |

**Example for Claude Code / Claude Code示例**:
- Copy the content of `rules/CLAUDE.md` to the **beginning** of your project's `CLAUDE.md`
- 将 `rules/CLAUDE.md` 的内容复制到项目根目录的 `CLAUDE.md` **开头部分**

**Example for Cursor / Cursor示例**:
- Create `.cursor/rules/vetmediator.mdc` in your project
- Copy the content of `rules/CLAUDE.md` into it
- 在项目中创建 `.cursor/rules/vetmediator.mdc`
- 将 `rules/CLAUDE.md` 的内容复制进去

**Example for Codex / Codex示例**:
- Copy the content of `rules/CLAUDE.md` to the **beginning** of your project's `AGENTS.md`
- 将 `rules/CLAUDE.md` 的内容复制到项目根目录的 `AGENTS.md` **开头部分**

**Example for iFlow / iFlow示例**:
- Copy the content of `rules/CLAUDE.md` to the **beginning** of your project's `IFLOW.md`
- 将 `rules/CLAUDE.md` 的内容复制到项目根目录的 `IFLOW.md` **开头部分**

**Example for Gemini CLI / Gemini CLI示例**:
- Copy the content of `rules/CLAUDE.md` to the **beginning** of your project's `GEMINI.md`
- 将 `rules/CLAUDE.md` 的内容复制到项目根目录的 `GEMINI.md` **开头部分**

This content includes trigger words and execution steps for the AI tool to use VetMediator.

此内容包含AI工具使用VetMediator的触发词和执行步骤。

📋 **Step 3: Copy task generation rules to your project / 复制任务生成规则到项目**

Copy `rules/rule-agent-file-generator.md` from this repository to your project's `rules/` directory

从本仓库复制 `rules/rule-agent-file-generator.md` 到你的项目的 `rules/` 目录

📋 **Step 4: Update the path reference in your AI tool's rule file / 更新AI工具规则文件中的路径引用**

⚠️ **Important / 重要**: After copying the content from `rules/CLAUDE.md`, you need to **update the file path** in your AI tool's rule file.

复制 `rules/CLAUDE.md` 的内容后，你需要**更新**AI工具规则文件中的文件路径。

**Original line in `rules/CLAUDE.md` / `rules/CLAUDE.md` 中的原始内容**:
```markdown
1. 读取规则文件：`rule-agent-file-generator.md`（与本文件位于同一目录）
```

**What you need to change / 你需要修改为**:

If you placed `rule-agent-file-generator.md` in `rules/` directory:

如果你将 `rule-agent-file-generator.md` 放在 `rules/` 目录:

```markdown
1. 读取规则文件：`rules/rule-agent-file-generator.md`
```

Or, if you placed it in another directory, update the path accordingly:

或者，如果你放在其他目录，相应更新路径：

```markdown
1. 读取规则文件：`path/to/your/rule-agent-file-generator.md`
```

**Example for different locations / 不同位置的示例**:
- If in `rules/` folder: `rules/rule-agent-file-generator.md`
- If in `docs/` folder: `docs/rule-agent-file-generator.md`
- If in project root: `rule-agent-file-generator.md`
- If in `.cursor/rules/` folder (for Cursor): `rule-agent-file-generator.md` (same directory)

⚠️ **Important / 重要**: The AI tool's rule file references `rule-agent-file-generator.md`. You can place `rule-agent-file-generator.md` in any directory, but make sure to update the path reference accordingly.

**File locations summary / 文件位置总结**:
```
YourProject/
├── .mcp.json                           # MCP server configuration / MCP服务器配置
├── CLAUDE.md (or AGENTS.md, etc.)     # AI tool rule file (add VetMediator config to beginning)
│                                       # AI工具规则文件（将VetMediator配置添加到开头）
└── rules/
    └── rule-agent-file-generator.md    # Task generation rules / 任务生成规则
```

📚 **For detailed instructions, see documentation above**
**详细说明请查看上方文档**

---

## 🌟 Key Features / 核心特性

| Feature | 功能 |
|---------|------|
| 🤖 Multi-Tool Support | 多工具支持 |
| 🔄 Smart Coordination | 智能协调 |
| 📊 Real-time Monitoring | 实时监控 |
| 🎯 Configuration Management | 配置管理 |
| 📝 Structured Reports | 结构化报告 |
| 🌐 Multilingual Support | 多语言支持 |

---

## 📚 Real Project Example / 真实项目示例

Want to see VetMediator in action? Check out our complete example!
想看看VetMediator的实际效果？查看完整示例！

👉 **[Unity Project Code Review Example / Unity项目代码审查示例](docs/sample/README.md)**

- 🎯 Claude Code + iFlow workflow / Claude Code + iFlow 工作流
- 🐛 4 P0-level bugs fixed / 修复4个P0级别BUG
- ⏱️ 310-second comprehensive review / 310秒全面审查
- 📸 18 real screenshots / 18张真实截图

---

## 🔗 Links / 链接

- **Repository / 代码仓库**:
  - 🌍 International: [GitHub](https://github.com/ldr123/VetMediatorMCP)
  - 🇨🇳 China: [Gitee](https://gitee.com/ldr123/VetMediatorMCP)
- **Issues / 问题反馈**: [GitHub Issues](https://github.com/ldr123/VetMediatorMCP/issues)
- ![Initiate Review](docs/imgs/weixin.png)
- **License / 许可证**: MIT

---

## 📊 Project Status / 项目状态

**Version / 版本**: 0.0.1
**Status / 状态**: Active Development / 积极开发中
**Python / Python版本**: 3.10+
**MCP Compatibility / MCP兼容性**: 1.0.0+

---

<div align="center">

**Made with ❤️ for the AI development community**
**为AI开发社区用心打造**

</div>
