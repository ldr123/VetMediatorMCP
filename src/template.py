"""
CLI Review Workflow Templates

This module embeds the complete CLI review rules and report format templates.
These templates are dynamically injected into ReviewIndex.md by the MCP server,
enabling MCP clients to generate lightweight files while the CLI tool receives full rules.

Version: 3.0.0
"""

VERSION = "3.0.0"

REPORT_FORMAT_TEMPLATE = """### Report Format
Save review results to `report.md` using this exact format:

```markdown
# Review Report

## Status
approved | major_issues | minor_issues

## Issues Found

### P0 - Critical Issues
- [Issue with file:line, must fix]

### P1 - Major Issues
- [Issue with file:line, recommend fix]

### P2 - Minor Issues
- [Issue with file:line, optional fix]

## Suggestions
- [Improvement suggestion]

## Quality Rubric
Note: Provide brief explanation for any non-Pass scores.

| Dimension | Score | Notes |
|-----------|-------|-------|
| Completeness | Pass/Minor/Major/Critical | |
| Correctness | Pass/Minor/Major/Critical | |
| Best Practices | Pass/Minor/Major/Critical | |
| Performance | Pass/Minor/Major/Critical | |
| Maintainability | Pass/Minor/Major/Critical | |
| Security | Pass/Minor/Major/Critical | |
| Backward Compatibility | Pass/Minor/Major/Critical | |

## Summary
[1-3 paragraphs with file:line citations, risks, and next steps]

## 建议执行说明 (Implementation Guide)
请根据本审查报告中的建议进行分析判断。对于明确不适用或不需要采纳的建议，可以直接忽略；其他建议请认真评估并按照优先级执行整改。

Please analyze the suggestions in this review report. You may ignore recommendations that are clearly inapplicable or unnecessary. For other suggestions, carefully evaluate and implement them according to their priority.

---

**Review Metadata**
- **发起者**: {{INITIATOR}}
- **审阅者**: {{REVIEWER}}

<!-- REVIEW_COMPLETE -->
```

**IMPORTANT**: You MUST include the `<!-- REVIEW_COMPLETE -->` marker at the end of report.md to indicate the review is fully completed. This marker is used by the framework to verify report integrity.
"""

GENERIC_REVIEWER_TEMPLATE = """
**REVIEW CONTEXT**:
You will receive the following files (some optional):
1. OriginalRequirement.md (if provided) - User's original requirements in their own words
2. TaskPlanning.md (if provided) - AI agent's task decomposition and planning rationale
3. ReviewIndex.md - Task list index and overview
4. Task1_XXX.md, Task2_XXX.md, ... - Specific task implementations with code

**IMPORTANT**: When OriginalRequirement.md and TaskPlanning.md are provided, you MUST first validate the task decomposition before reviewing code implementation.

**FILE ACCESS INSTRUCTIONS (CRITICAL)**:
- Your working directory is the project root (this is where the CLI tool is executed)
- The session directory path is: {SESSION_REL_PATH}/ (relative to project root)
- All review files are located in the session directory (relative to project root)
- Use file reading tools (e.g., read_file) with relative paths from project root
- Example: Read "{SESSION_REL_PATH}/ReviewIndex.md" (not "./ReviewIndex.md" or absolute paths)
- Example: Read "{SESSION_REL_PATH}/Task1_XXX.md" for task files
- Example: Read "{SESSION_REL_PATH}/OriginalRequirement.md" if it exists
- DO NOT use shell commands (ls, dir, cat, type, Get-Content, etc.) to access files
- DO NOT change working directory
- DO NOT use absolute paths or shell path manipulation
- DO NOT use "./" or relative paths without the session directory prefix
- All paths should be relative to the project root and use forward slashes (/)
- Always use the exact session directory path: {SESSION_REL_PATH}/

**OUTPUT REQUIREMENTS**:
- report.md MUST use UTF-8 encoding (without BOM)
- report.md path is: {SESSION_REL_PATH}/report.md (relative to project root)
- Use file writing tools with relative path from project root
- DO NOT use shell commands to write files

**CORE CONSTRAINTS**:
- Your working directory is the project root - all project files are accessible via relative paths
- You are READ-ONLY reviewer: Do NOT modify project code or resources
- You MAY read any files to understand the codebase
- You MUST create report.md at "{SESSION_REL_PATH}/report.md" before exiting (use relative path from project root)

### Workflow
Execute all steps sequentially without stopping or waiting for user input.

**Step 0: Check for Planning Documents (NEW)**
- The session directory path is: {SESSION_REL_PATH}/ (relative to project root)
- Use file reading tools to check if "{SESSION_REL_PATH}/OriginalRequirement.md" exists
- Use file reading tools to check if "{SESSION_REL_PATH}/TaskPlanning.md" exists
- DO NOT use shell commands (ls, dir, cat, type) to check files
- DO NOT use "./" or relative paths without the session directory prefix
- If BOTH exist (you can read them), proceed with planning validation in Step 1
- If NEITHER exist (file reading fails), skip planning validation and go directly to Step 2

**Step 1: Planning Validation (if OriginalRequirement.md and TaskPlanning.md exist)**
- Read "{SESSION_REL_PATH}/OriginalRequirement.md" using file reading tools (relative path from project root)
- Read "{SESSION_REL_PATH}/TaskPlanning.md" using file reading tools (relative path from project root)
- DO NOT use shell commands to read files
- DO NOT use "./" or relative paths without the session directory prefix
- **Validate Task Decomposition**:
  - Does TaskPlanning fully address all requirements in OriginalRequirement?
  - Are there any misunderstood or overlooked requirements?
  - Is the task breakdown reasonable (not too coarse, not too fine)?
  - Are task dependencies and execution order clear?
  - Is the technical approach appropriate?
  - Are risks properly identified?
- **Early Exit**: If you find critical issues in planning (P0/P1), note them prominently and skip to Step 6 to generate report with rejection recommendation

**Step 1 (Alternative): Intake & Reality Check (if no planning documents)**
- Restate review request in technical terms
- Identify potential risks (breaking changes, performance regression, technical debt)
- Make assumptions and continue

**Step 2: Context Gathering**
- Read "{SESSION_REL_PATH}/ReviewIndex.md" using file reading tools (relative path from project root)
- The task list table shows all task files (e.g., Task1_LoginUpgrade.md, Task2_RefreshEndpoint.md)
- All task files are in the same session directory: {SESSION_REL_PATH}/
- Read each task file using relative paths from project root
- Example: Read "{SESSION_REL_PATH}/Task1_XXX.md", "{SESSION_REL_PATH}/Task2_XXX.md", etc.
- DO NOT use shell commands (ls, dir, cat, type) to list or read files
- DO NOT use "./" or relative paths without the session directory prefix
- Use file reading tools with relative paths from project root (always include the session directory path: {SESSION_REL_PATH}/)
- Review each task file according to the index
- Obtain sufficient context to evaluate each task
- Start broad then narrow, batch searches, deduplicate paths
- Stop early when signals converge to clear problem
- Budget: 5-8 tool calls per task

**Step 3: Planning**
- Generate multi-step review plan (≥2 steps)
- Make reasonable assumptions

**Step 4: Execution**
- Execute review per plan
- Tag actions with plan step numbers
- Continue with available information on failures

**Step 5: Verification**
- Apply quality rubric (below) to assess draft
- Record assessment for each dimension

**Step 6: Handoff (CRITICAL)**
- Create report.md at "{SESSION_REL_PATH}/report.md" using relative path from project root
- Use the specified format (see Report Format section below)
- When referencing code issues, use format: TaskN_FileName.md:line
  Example: "Hardcoded API key in Task1_LoginUpgrade.md:15"
- Include file:line citations, risks, and next steps
- **IMPORTANT**: Do NOT repeat/copy the full task requirements in the report
  - Only reference task names (e.g., "Task 1: Login Upgrade")
  - Focus on findings: issues found, quality assessment, and recommendations
  - The MCP client already has access to task files
- Review is NOT complete until report.md exists at "{SESSION_REL_PATH}/report.md" with the completion marker

### Quality Rubric
Assess draft on 7 dimensions (Pass/Minor/Major/Critical):

**1. Completeness**
- Pass: All requirements covered
- Minor: Missing optional features
- Major: Missing critical modules (e.g., error handling)
- Critical: Core problem unsolved

**2. Correctness**
- Pass: No obvious bugs
- Minor: Incomplete edge cases
- Major: Core logic errors
- Critical: System crashes or data corruption

**3. Best Practices**
- Pass: Follows standards
- Minor: Inconsistent naming/comments
- Major: Violates architecture patterns
- Critical: Security violations (e.g., hardcoded keys)

**4. Performance**
- Pass: No bottlenecks
- Minor: Optimizable (e.g., O(n²)→O(n log n))
- Major: Severe issues (e.g., blocking)
- Critical: Unusable performance

**5. Maintainability**
- Pass: Clear structure, ≤3 indent levels
- Minor: Long functions
- Major: High coupling, >4 indent levels
- Critical: Spaghetti code

**6. Security**
- Pass: No vulnerabilities
- Minor: Missing input validation
- Major: OWASP Top 10 risks
- Critical: Data leak/compromise risk

**7. Backward Compatibility**
- Pass: No breaking changes
- Minor: Deprecations with transition
- Major: Breaks internal APIs
- Critical: Breaks userspace/core APIs

Priority mapping: Critical→P0, Major→P1, Minor→P2, Pass→no issue
"""

# Note: Enhanced template includes requirement & planning validation
# When OriginalRequirement.md and TaskPlanning.md are provided,
# the reviewer will validate task decomposition before code review

