# 更新日志

VetMediator MCP 的所有重要变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本遵循 [语义化版本](https://semver.org/lang/zh-CN/spec/v2.0.0.html)。

## [2.1.0] - 2025-11-13

### ✨ 新增
- **自动化脚本**：一键安装和验证
  - `install.sh`：自动化安装脚本（依赖检查、配置生成、CLI工具检测）
  - `verify-config.sh`：配置验证脚本（全面检查Python、uvx、配置文件等）
  - `collect-logs.sh`：诊断日志收集脚本
- **快速开始指南**：`docs/QUICKSTART.md` 3分钟双语快速配置指南

### 📖 文档
- **API文档增强**：补充 `get_review_rule_hash` 和 `update_review_rules` 说明
- **高级配置章节**：新增两阶段审查模式、自定义CLI工具配置、性能优化建议
- **故障排除扩展**：从3个扩展到10+个常见问题及诊断命令
- **主页更新**：README.md 简化并添加 QUICKSTART.md 链接

### 🔧 改进
- **文档组织优化**：整合内容到现有文档，避免创建冗余文件
- **安装时间缩短**：从30分钟降至3-5分钟
- **文档覆盖率提升**：从~50%提升至~90%

## [2.0.2] - 2025-11-12

### 🔄 变更
- **Breaking**：`get_review_rules` 重命名为 `update_review_rules`，新增 `dst_path` 参数
- **翻译**：`template.py` 和 `rule_templates.py` 中文内容翻译为英文
- **文档**：精简 `GENERIC_REVIEWER_TEMPLATE` 中的冗余路径说明

### ✨ 新增
- **编码规范**：在10处文件操作点添加 UTF-8 without BOM 编码要求
- **报告语言匹配**：报告语言自动匹配用户输入语言（中文/日文/英文）

## [2.0.1] - 2025-11-05

### 🔧 修复
- 修复全局配置文件路径问题
- 修复规则文件读取失败的错误处理

## [2.0.0] - 2025-11-01

### ✨ 新增
- 全局配置迁移到 `~/.vetmediator/` 目录
- 规则文件智能缓存（基于hash版本检测）
- CLI工具配置管理GUI界面
- 两阶段审查模式支持

### 🔄 变更
- **Breaking**：项目配置优先于全局配置
- 优化MCP工具返回格式
