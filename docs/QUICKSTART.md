# VetMediator MCP - Quick Start / 快速开始

**[🏠 Home](../README.md)** | **Language / 语言**: [English](#english-version) | [中文](#中文版本)

---

## English Version

### 3-Minute Setup

#### Prerequisites
- **Python 3.10+** → [Download](https://python.org)
- **uvx** → Run: `pip install uv`
- **MCP-compatible AI tool** → Claude Code, Cursor, etc.
- **At least one CLI review tool** → iFlow, Codex, or Claude CLI

#### Step 1: One-Command Installation (1 minute)

```bash
# Navigate to your project directory
cd /path/to/your/project

# Run installation script
curl -sSL https://raw.githubusercontent.com/ldr123/VetMediatorMCP/master/install.sh | bash

# Or download and run manually
# wget https://raw.githubusercontent.com/ldr123/VetMediatorMCP/master/install.sh
# chmod +x install.sh && ./install.sh
```

The script will automatically:
- ✅ Check Python 3.10+ and uvx
- ✅ Generate `.mcp.json` configuration
- ✅ Detect installed CLI tools
- ✅ Inject rules to `CLAUDE.md` (with your confirmation)
- ✅ Create `VetMediatorSessions/` directory

#### Step 2: Verify Installation (30 seconds)

```bash
# Run verification script
curl -sSL https://raw.githubusercontent.com/ldr123/VetMediatorMCP/master/verify-config.sh | bash

# Or if you downloaded install.sh
# ./verify-config.sh
```

Expected output:
```
✓ Python version correct (Python 3.10+)
✓ uvx installed
✓ .mcp.json configuration file
✓ VetMediatorSessions/ directory
🎉 All checks passed!
```

#### Step 3: First Use (30 seconds)

1. **Restart your AI tool** (Claude Code / Cursor)
2. **Verify MCP tools**:
   ```
   Type in AI tool: 查看CLI配置
   or: show cli config
   ```
3. **Start your first review**:
   ```
   Type in AI tool: 使用vet验证
   or: use vet validation
   ```

#### Install CLI Review Tool (if not installed)

Choose one:

```bash
# iFlow CLI (Recommended for Chinese users)
npm install -g @iflow-ai/iflow-cli

# Codex CLI
npm install -g @openai/codex

# Claude CLI
npm install -g @anthropic-ai/claude-code
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| CLI tool not found | Install iFlow/Codex/Claude CLI |
| .mcp.json missing | Run `./install.sh` again |
| Permission denied | Run with `sudo` or check directory permissions |
| Python version < 3.10 | Upgrade Python to 3.10+ |

📚 **Full Documentation**: [docs/en/README.md](en/README.md)

---

## 中文版本

### 3分钟配置

#### 前置要求
- **Python 3.10+** → [下载](https://python.org)
- **uvx** → 运行: `pip install uv`
- **MCP兼容的AI工具** → Claude Code、Cursor等
- **至少一个CLI审查工具** → iFlow、Codex或Claude CLI

#### 第1步：一键安装（1分钟）

```bash
# 进入项目目录
cd /path/to/your/project

# 运行安装脚本
curl -sSL https://raw.githubusercontent.com/ldr123/VetMediatorMCP/master/install.sh | bash

# 或手动下载并运行
# wget https://raw.githubusercontent.com/ldr123/VetMediatorMCP/master/install.sh
# chmod +x install.sh && ./install.sh

# 中国用户可使用 Gitee 镜像
# curl -sSL https://gitee.com/ldr123/VetMediatorMCP/raw/master/install.sh | bash
```

脚本会自动：
- ✅ 检查 Python 3.10+ 和 uvx
- ✅ 生成 `.mcp.json` 配置
- ✅ 检测已安装的CLI工具
- ✅ 向 `CLAUDE.md` 注入规则（需要您确认）
- ✅ 创建 `VetMediatorSessions/` 目录

#### 第2步：验证安装（30秒）

```bash
# 运行验证脚本
curl -sSL https://raw.githubusercontent.com/ldr123/VetMediatorMCP/master/verify-config.sh | bash

# 或如果已下载 install.sh
# ./verify-config.sh
```

预期输出：
```
✓ Python 版本正确 (Python 3.10+)
✓ uvx 已安装
✓ .mcp.json 配置文件
✓ VetMediatorSessions/ 目录
🎉 所有检查通过！
```

#### 第3步：首次使用（30秒）

1. **重启AI工具**（Claude Code / Cursor）
2. **验证MCP工具**：
   ```
   在AI工具中输入：查看CLI配置
   ```
3. **开始首次审查**：
   ```
   在AI工具中输入：使用vet验证
   ```

#### 安装CLI审查工具（如未安装）

选择一个：

```bash
# iFlow CLI（推荐中文用户）
npm install -g @iflow-ai/iflow-cli

# Codex CLI
npm install -g @openai/codex

# Claude CLI
npm install -g @anthropic-ai/claude-code
```

### 常见问题

| 问题 | 解决方案 |
|------|----------|
| 找不到CLI工具 | 安装 iFlow/Codex/Claude CLI |
| .mcp.json 缺失 | 重新运行 `./install.sh` |
| 权限被拒绝 | 使用 `sudo` 或检查目录权限 |
| Python 版本 < 3.10 | 升级 Python 到 3.10+ |

📚 **完整文档**: [docs/zh/README.md](zh/README.md)

---

## Next Steps / 下一步

- 📖 Read full documentation / 阅读完整文档
- 🎬 View real project example / 查看真实项目示例: [docs/sample/README.md](sample/README.md)
- 🔧 Learn advanced configuration / 学习高级配置
- 🛠️ Troubleshooting guide / 故障排除指南

---

**Version / 版本**: 2.1.0
**Last Updated / 最后更新**: 2025-11-13
**License / 许可证**: MIT
