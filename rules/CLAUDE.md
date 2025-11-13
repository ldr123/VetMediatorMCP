## 🤝 CLI Tool Cross-Validation
**Triggers:** `使用vet验证` | `让vet帮我验证` | `使用CLI工具交叉验证` | `use vet validation` | `let vet validate` | `use CLI cross-validation`

**[MANDATORY] Execute all steps in order. Do not skip any step.**

### Phase 1: Fetch Latest Rules
1. Call `mcp__vet-mediator-mcp__get_review_rule_hash` to get rule version hash
2. Check if `VetMediatorSessions/vet_mediator_rule_{hash}.md` exists
3. **Based on file existence:**
   - **If not exists:** Call `mcp__vet-mediator-mcp__update_review_rules(rule_type="file-generator", dst_path="{project_root}/VetMediatorSessions")` to download rule file (where `project_root` = project root directory path)
   - **If exists:** Skip download, proceed to next phase

### Phase 2: Execute Review Process
4. Read `VetMediatorSessions/vet_mediator_rule_{hash}.md` completely to understand file format specs and MCP call methods
5. Generate required files per rule spec, then call `mcp__vet-mediator-mcp__start_review` to start review

---

## 🔧 CLI Tool Configuration
**Triggers:** `查看CLI配置` | `切换CLI工具` | `show cli config` | `view CLI config` | `switch CLI tool` | `change CLI tool`

**Execution:**
Call MCP tool: `mcp__vet-mediator-mcp__show_cli_config`
- Required parameter: `project_root` (project root directory path)

