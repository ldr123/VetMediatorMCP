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

📋 **Step 1: Configure MCP server in your project / 在项目中配置MCP服务器**

Create `.mcp.json` in your project root directory with the following content:

在项目根目录创建 `.mcp.json` 文件，内容如下：

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

📋 **Step 2: Add VetMediator rules to your AI tool's rule file / 添加VetMediator规则到AI工具的规则文件**

Copy the content of `rules/CLAUDE.md` from this repository to the **beginning** of your project's AI tool rule file.

从本仓库复制 `rules/CLAUDE.md` 的内容到你的项目的AI工具规则文件的**开头部分**。

**Different AI tools use different rule files / 不同AI工具使用不同的规则文件**:

| AI Tool / 工具 | Rule File / 规则文件 | Location / 位置 |
|----------------|---------------------|----------------|
| **Claude Code** | `CLAUDE.md` | Project root / 项目根目录 |
| **Cursor** | `*.mdc` | `.cursor/rules/` |
| **Codex** | `AGENTS.md` | Project root / 项目根目录 |
| **iFlow** | `IFLOW.md` | Project root / 项目根目录 |
| **Gemini CLI** | `GEMINI.md` | Project root / 项目根目录 |

**Examples / 示例**:
- **Claude Code**: Copy `rules/CLAUDE.md` content → Your project's `CLAUDE.md` (beginning)
- **Codex**: Copy `rules/CLAUDE.md` content → Your project's `AGENTS.md` (beginning)
- **iFlow**: Copy `rules/CLAUDE.md` content → Your project's `IFLOW.md` (beginning)

复制示例：
- **Claude Code**：复制 `rules/CLAUDE.md` 内容 → 你的项目的 `CLAUDE.md`（开头部分）
- **Codex**：复制 `rules/CLAUDE.md` 内容 → 你的项目的 `AGENTS.md`（开头部分）
- **iFlow**：复制 `rules/CLAUDE.md` 内容 → 你的项目的 `IFLOW.md`（开头部分）

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

**Version / 版本**: 2.0.1
**Status / 状态**: Active Development / 积极开发中
**Python / Python版本**: 3.10+
**MCP Compatibility / MCP兼容性**: 1.0.0+

---

<div align="center">

**Made with ❤️ for the AI development community**
**为AI开发社区用心打造**

</div>
