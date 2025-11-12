# Changelog

All notable changes to VetMediator MCP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.1] - 2025-11-12

### ✨ 改进 (Improvements)

#### CLI 提示词和路径处理优化
- **优化** `src/cli_config.py` 中的 `BUILTIN_PROMPT`：
  - 添加详细的文件访问说明，强调使用文件读取工具而非 shell 命令
  - 明确工作目录为项目根目录，所有路径使用相对路径
  - 添加示例路径说明（如 `{session_rel_path}/ReviewIndex.md`），提高 AI 代理理解准确性
- **优化** `src/template.py` 中的 `GENERIC_REVIEWER_TEMPLATE`：
  - 添加 `{SESSION_REL_PATH}` 占位符支持，动态注入会话目录相对路径
  - 详细说明文件访问方式和路径使用规范（禁止 shell 命令，使用文件读取工具）
  - 强化跨平台兼容性说明（统一使用正斜杠路径分隔符）
  - 在 Step 0、Step 1、Step 2、Step 6 中明确路径示例和操作规范
- **改进** `src/file_generator.py`：
  - 在 `_expand_placeholders()` 方法中添加 `session_rel_path` 参数
  - 在模板注入时动态传入会话相对路径，替换 `GENERIC_REVIEWER_TEMPLATE` 中的路径占位符
  - 确保生成的审查文件包含正确的跨平台路径

#### 性能优化
- **优化** `src/report_parser.py`：
  - 将所有正则表达式编译为类级别缓存（新增 10+ 个预编译正则表达式常量）
  - 减少重复编译开销，提升报告解析性能
  - 正则表达式常量包括：`_STATUS_PATTERN`、`_OVERALL_ASSESSMENT_PATTERN`、`_QUALITY_ASSESSMENT_PATTERN`、`_CRITICAL_PATTERN`、`_MAJOR_PATTERN`、`_ISSUE_SECTION_PATTERN` 等
- **改进** `src/reviewer.py`：
  - 从 `time.time()` 改为 `time.monotonic()` 进行时间测量
  - 提高超时检测和活跃度监控的准确性和可靠性
  - 不受系统时间调整（如 NTP 同步、夏令时切换）影响
  - 涉及 4 处时间测量点：`start_time`、`last_activity_time`、`report_detected_time`、时间差计算

#### 用户体验改进
- **移除** GUI 窗口置顶功能：
  - `src/cli_check_ui.py`：移除 `Qt.WindowStaysOnTopHint` 标志
  - `src/cli_monitor_ui.py`：移除 `Qt.WindowStaysOnTopHint` 标志
  - 允许用户更灵活地管理窗口层级，避免强制置顶干扰其他应用

### 📚 文档 (Documentation)
- **优化** `rules/CLAUDE.md`：
  - 明确规则缓存文件的命名格式（`vet_mediator_rule_{hash}.md`）
  - 添加自动清理旧缓存文件的说明（删除非当前 hash 的缓存文件）
  - 移除冗余标题"# Claude Code 开发指南"，精简格式
  - 移除尾部多余空行，统一格式

### 🔧 配置 (Configuration)
- **更新** `.gitignore`：添加 `.claude` 目录到忽略列表

### 🐛 修复 (Bug Fixes)
- **修复** `src/reviewer.py`：移除重复的 `ProcessLookupError` 异常处理块（代码冗余）

### 🔄 技术细节 (Technical Details)
- **src/cli_config.py**：
  - 重构 `BUILTIN_PROMPT` 字符串模板，从简单的路径引用改为详细的操作指南
  - 新增多行说明：工作目录、相对路径、文件访问工具、编码要求等
- **src/template.py**：
  - `GENERIC_REVIEWER_TEMPLATE` 增加约 40 行详细说明
  - 新增 "FILE ACCESS INSTRUCTIONS (CRITICAL)" 章节
  - 在 Workflow 各步骤中添加路径示例和禁止事项
- **src/file_generator.py**：
  - `_expand_placeholders()` 方法签名变更：新增 `session_rel_path` 参数
  - `_create_review_index()` 方法调用时计算并传入 `session_rel_path`
- **src/report_parser.py**：
  - 新增类级别正则表达式常量（性能优化）
  - 所有 `re.search()` 和 `re.finditer()` 调用改为使用预编译的正则表达式

---

## [2.0.0] - 2025-11-11

### 🚀 Major Features

#### Hash-Based Rule Caching System
- **Added** `get_review_rule_hash` MCP tool - Returns SHA-256 hash (first 12 chars) of embedded rule templates
- **Added** `get_review_rules` MCP tool - Returns complete rule content in Markdown format
- **Added** `src/rule_templates.py` - Embedded rule templates as Python string constants (moved from `rules/rule-agent-file-generator.md`)
- **How it works**: AI agents call `get_review_rule_hash` to check rule version, download via `get_review_rules` if hash differs, cache locally in `~/.vetmediator/`
- **Benefit**: First use downloads ~4000 tokens once, subsequent uses read from local cache = **0 tokens per use**

#### Configuration Path Standardization
- **Changed**: Global config path from `~/.VetMediatorSetting.json` → `~/.vetmediator/config.json`
- **Added**: Automatic migration on first load (reads old file, migrates to new path, deletes old file)
- **Added**: `get_legacy_config_path()` and `migrate_legacy_config()` functions in `cli_config.py`
- **Benefit**: Unified `~/.vetmediator/` directory for all VetMediator data (config + rule cache + future data)

#### Simplified Installation Process
- **Removed**: Manual rule file copying step from installation guide
- **Improved**: User only needs to copy `rules/CLAUDE.md` content to their project's AI tool rule file
- **Automated**: Rules automatically downloaded and cached on first use via MCP tools

### ✨ Added
- Smart caching workflow in `rules/CLAUDE.md` with hash verification instructions
- Automatic cleanup of outdated rule cache files (keeps only current version)
- Support for `original_requirement_path` and `task_planning_path` parameters in `start_review` tool (enables planning validation)
- Enhanced `GENERIC_REVIEWER_TEMPLATE` with Step 0 logic to detect optional planning documents

### 🔄 Changed
- **Breaking**: Installation no longer requires copying `rules/rule-agent-file-generator.md` to user projects
- **Breaking**: AI agents must update workflow to use hash-based caching (see updated `rules/CLAUDE.md`)
- Rule templates now embedded in code for reliable packaging and distribution
- Documentation simplified - removed complex path reference update instructions

### 📚 Documentation
- Updated `docs/zh/README.md`:
  - Added smart caching feature description
  - Removed manual rule file copying steps (Steps 3-4)
  - Updated installation to 2-step process
- Updated `docs/en/README.md`:
  - Same updates as Chinese version
  - Updated file structure diagram
- Simplified `rules/CLAUDE.md`:
  - Added hash-based caching workflow
  - Removed redundant file name enumeration
  - Cleaner, more concise instructions

### 🐛 Fixed
- Potential issues with rule file distribution and updates (now embedded in code)
- Config file scattered in user home directory (now unified in `~/.vetmediator/`)

### 🔧 Technical Details
- **server.py**:
  - Added `GetReviewRuleHashArgs` and `GetReviewRulesArgs` models
  - Added hash calculation and rule content retrieval handlers
  - Imported `hashlib` for SHA-256 hashing
- **cli_config.py**:
  - New `get_user_config_path()` returns new path `~/.vetmediator/config.json`
  - New `get_legacy_config_path()` returns old path `~/.VetMediatorSetting.json`
  - New `migrate_legacy_config()` handles automatic migration
  - Updated `load_config()` to call migration before loading
- **rule_templates.py** (new file):
  - `RULE_FILE_GENERATOR` constant contains full rule content (~4000 tokens)
  - `RULE_TEMPLATES` dict maps rule types to content
  - `get_rule_content()` and `get_available_rule_types()` helper functions
- **file_generator.py**:
  - Enhanced to handle `original_requirement_path` and `task_planning_path`
  - Copy planning documents if provided
- **workflow_manager.py**:
  - Added `original_requirement_path` and `task_planning_path` parameters
  - Simplified workflow (removed separate stage logic experiments)
- **template.py**:
  - Enhanced `GENERIC_REVIEWER_TEMPLATE` with Step 0 to detect planning documents
  - If OriginalRequirement.md and TaskPlanning.md exist, reviewer validates planning first

### 📊 Performance Impact

**Token Consumption Comparison**:

| Scenario | Old Method | New Method (v2.0) | Savings |
|----------|-----------|-------------------|---------|
| First use | 1,000 tokens/conversation | 200 + 4,000 (one-time) = 4,200 tokens | Higher first use |
| 2nd-10th use | 1,000 × 9 = 9,000 tokens | 200 × 9 = 1,800 tokens | **80% savings** |
| 10 conversations, 3 reviews | 10,000 tokens | 6,050 tokens | **40% savings** |
| 100 conversations, 10 reviews | 100,000 tokens | 24,050 tokens | **76% savings** |
| 1000 conversations, 50 reviews | 1,000,000 tokens | 222,500 tokens | **78% savings** |

**Caching Hit Rate**: Expected >95% for active users (rules rarely change)

### ⚠️ Migration Guide

**For End Users**:
1. **Update rule file**: Replace content in your project's `CLAUDE.md` (or `AGENTS.md`/`IFLOW.md`) with latest version from `rules/CLAUDE.md` in this repository
2. **Remove old rule file**: Delete `rules/rule-agent-file-generator.md` from your project (no longer needed)
3. **First run**: When you trigger "use vet verification", AI agent will auto-download and cache rules
4. **Config migration**: Happens automatically on first MCP server startup (if you had old config at `~/.VetMediatorSetting.json`)

**For Developers/Contributors**:
- If you modified `rules/rule-agent-file-generator.md`, update `src/rule_templates.py` instead
- Rule content is now version-controlled in Python code, not separate markdown files
- To add new rule types, extend `RULE_TEMPLATES` dict in `rule_templates.py`

### 🔐 Security & Privacy
- Rule cache stored in user home directory `~/.vetmediator/` (not project directory)
- No sensitive data in rule templates
- Config migration preserves existing settings and permissions

---

## [1.0.0] - 2025-11-1

### Initial Release
- Multi-tool CLI review coordination via MCP protocol
- Real-time monitoring with GUI window
- Configuration management interface with tool health checks
- Structured report generation (P0/P1/P2 issue classification, 7-dimension quality rubric)
- UTF-8 encoding with automatic BOM handling
- Session-based workflow management with automatic cleanup (keeps 10 most recent sessions)
- Support for multiple AI clients (Claude Code, Cursor, Codex, iFlow, etc.)
- Template-based reviewer instructions with placeholder injection

