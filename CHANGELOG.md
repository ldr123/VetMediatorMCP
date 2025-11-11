# Changelog

All notable changes to VetMediator MCP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-11-11

### 🚀 Major Changes

#### Hash-Based Rule Caching System
- **Added** `get_review_rule_hash` MCP tool - Returns SHA-256 hash (first 12 chars) of rule templates
- **Added** `get_review_rules` MCP tool - Returns complete rule content in Markdown format
- **Added** `src/rule_templates.py` - Embedded rule templates as Python constants
- **Benefit**: AI agents cache rules locally (~4000 tokens), only download on first use or updates
- **Impact**: Saves 76-78% token consumption in long-term usage (tested over 1000 conversations)

#### Configuration Path Migration
- **Changed**: Global config moved from `~/.VetMediatorSetting.json` to `~/.vetmediator/config.json`
- **Added**: Automatic migration on first load (reads old path, writes to new path, deletes old file)
- **Added**: `get_legacy_config_path()` and `migrate_legacy_config()` in `cli_config.py`
- **Benefit**: Unified `~/.vetmediator/` directory for all VetMediator data (config + rule cache)

#### Architecture Simplification
- **Removed**: Two-stage review system (Stage1: planning validation, Stage2: code review)
- **Changed**: Single-pass holistic review with intelligent template detection
- **Enhanced**: `GENERIC_REVIEWER_TEMPLATE` with Step 0 logic to auto-detect planning documents
- **Impact**: Reduced ~250 lines of code while maintaining full functionality

### ✨ Added
- Smart caching workflow in `rules/CLAUDE.md` with step-by-step instructions
- Hash verification prevents unnecessary rule downloads
- Automatic cleanup of old rule cache files

### 🔄 Changed
- **Breaking**: `rules/rule-agent-file-generator.md` removed - now embedded in code
- **Breaking**: MCP clients must use new hash-based caching workflow
- Simplified installation steps (no need to copy rule files manually)
- Updated documentation (Chinese & English) to reflect new workflow

### 🗑️ Removed
- `rules/rule-agent-file-generator.md` - Embedded as `RULE_FILE_GENERATOR` in `src/rule_templates.py`
- Two-stage review methods: `_two_stage_review()` and `_single_stage_review()` from `workflow_manager.py`
- `enable_two_stage_review` parameter from MCP tool arguments
- STAGE1/STAGE2 specific reviewer templates from `template.py`

### 🐛 Fixed
- Planning documents (OriginalRequirement.md, TaskPlanning.md) now accessible in single review pass
- Reviewer can validate task decomposition before code review
- Configuration conflicts resolved with unified directory structure

### 📚 Documentation
- Updated `docs/zh/README.md` - Added smart caching feature, removed manual rule copying steps
- Updated `docs/en/README.md` - Same updates as Chinese version
- Simplified `rules/CLAUDE.md` - Concise caching workflow without redundant details

### 🔧 Technical Details
- **server.py**: Added hash calculation and rule retrieval endpoints
- **cli_config.py**: Added `migrate_legacy_config()` with automatic migration logic
- **workflow_manager.py**: Simplified from 300+ lines to ~120 lines
- **template.py**: Consolidated 3 templates into 1 enhanced template with conditional logic
- **file_generator.py**: Removed stage-specific logic, always use generic template

### 📊 Performance
- **Token Savings**:
  - First use: +50 tokens (hash check) + 4000 tokens (download) = ~4050 tokens
  - Subsequent uses: +0 tokens (read from cache)
  - 10 conversations, 3 reviews: 6,050 tokens (vs 10,000 tokens old method) - **40% savings**
  - 100 conversations, 10 reviews: 24,050 tokens (vs 100,000 tokens old method) - **76% savings**

### ⚠️ Migration Guide

**For Users:**
1. Update `rules/CLAUDE.md` in your project to latest version from repository
2. Delete old `rules/rule-agent-file-generator.md` from your project (no longer needed)
3. First run will auto-migrate config from `~/.VetMediatorSetting.json` to `~/.vetmediator/config.json`
4. AI agent will auto-download and cache rules on first "use vet verification" trigger

**For Developers:**
- If you extended the two-stage review system, update to use single-pass with template detection
- Check if you have custom templates - they should now use `GENERIC_REVIEWER_TEMPLATE` pattern

---

## [1.0.0] - 2025-10-XX

### Initial Release
- Multi-tool CLI review coordination
- Real-time monitoring with GUI window
- Configuration management interface
- Structured report generation (P0/P1/P2 classification)
- UTF-8 encoding with BOM handling
- Session-based workflow management
