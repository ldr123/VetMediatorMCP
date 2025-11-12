"""
Built-in Rule Templates

This module contains the complete content of all review rules as Python string constants.
Rule content is embedded in the code during packaging, eliminating external file dependencies.
"""

RULE_FILE_GENERATOR = """# CLI Tool Cross-Validation Review - File Generation Rules

**Trigger Keywords**: `use vet validation` OR `let vet validate for me` OR `use CLI tool cross-validation`

**Execution Steps**:
1. Generate OriginalRequirement.md (original user requirements)
2. Generate TaskPlanning.md (task planning proposal)
3. Generate ReviewIndex.md (review index)
4. Generate separate files for each task: Task1_XXX.md, Task2_XXX.md, ...
5. Invoke MCP tool: `mcp__vet-mediator-mcp__start_review`
   - Required parameters:
     - `review_index_path`: Temporary file path for ReviewIndex.md
     - `draft_paths`: List of task file paths (in order)
     - `project_root`: Absolute path to project root directory
   - Recommended parameters (provides complete review context):
     - `original_requirement_path`: Temporary file path for OriginalRequirement.md (optional but strongly recommended)
     - `task_planning_path`: Temporary file path for TaskPlanning.md (optional but strongly recommended)
     - `initiator`: Name of the AI tool initiating the review (e.g., "Claude Code", "Cursor"), used to identify source in the report
   - Optional parameters:
     - `max_iterations`: Maximum iteration rounds (default 3, future enhancement)

**Encoding Requirements**:
- All generated files must use UTF-8 encoding (without BOM)
- MCP server automatically handles unified output to UTF-8 without BOM format


**[IMPORTANT!!!] Temporary File Naming Convention**:
- OriginalRequirement.md: `OriginalRequirement-{random}.md`
- TaskPlanning.md: `TaskPlanning-{random}.md`
- ReviewIndex.md: `ReviewIndex-{random}.md`
- Task files: `{TargetName}-{random}.md` (e.g., `Task1_LoginUpgrade-abc123.md`)
- MCP server automatically extracts target filename (substring before the last "-")
- Write temporary files to VetMediatorSessions/tmp directory (create if it doesn't exist). IMPORTANT: Generate to this directory, NOT to system temp directory (e.g., ~/)

---

## OriginalRequirement.md Format

**ENCODING REQUIREMENT**: This file MUST be saved as UTF-8 without BOM.

### Template

```markdown
# Original User Requirements

## User Input (Verbatim)
[Preserve the user's original words completely without modification, including:
- Initial requirement description
- Supplementary clarifications from multi-turn conversations
- Points emphasized by the user
- Constraints mentioned by the user]

## Conversation Context
[If there are multiple conversation turns, record key clarification exchanges:
Q: [AI agent's question]
A: [User's answer]
...]

## Inferred Implicit Requirements
[Implicit requirements inferred by the AI agent based on experience:
- Non-functional requirements (performance, security, maintainability)
- Industry best practices
- Compatibility considerations with existing systems]

## Scope Boundaries
[Explicitly state what is NOT in scope:
- Features explicitly excluded by the user
- Requirements deferred for later
- Items beyond technical scope]
```

### Field Descriptions

| Section | Description | Requirement |
|---------|-------------|-------------|
| User Input (Verbatim) | Preserve user's original words without alteration | Required, do not rewrite or polish |
| Conversation Context | Key clarifications from multi-turn dialogue | Required if multiple conversation turns exist |
| Inferred Implicit Requirements | Unstated requirements inferred by AI | Optional but recommended |
| Scope Boundaries | Explicitly define what is excluded | Optional but helps reviewer understand scope |

---

## TaskPlanning.md Format

**ENCODING REQUIREMENT**: This file MUST be saved as UTF-8 without BOM.

### Template

```markdown
# Task Planning Proposal

## Requirements Analysis
### Core Objectives
[Summarize the core objectives in 1-2 sentences]

### Key Constraints
- Technology stack constraints: [e.g., Must use .NET 8]
- Time constraints: [e.g., Must complete within 2 weeks]
- Compatibility constraints: [e.g., Must maintain backward compatibility with legacy API]

### Expected Deliverables
[List final deliverables]

## Technical Solution Selection
### Solution Comparison
| Solution | Pros | Cons | Adopted |
|----------|------|------|---------|
| Solution A | ... | ... | ✅ |
| Solution B | ... | ... | ❌ Reason... |

### Selection Rationale
[Explain why the current solution was chosen]

## Task Decomposition
### Decomposition Principles
- Decompose by [module/feature/layer/dependency]
- Each task should be completable within [X] hours

### Task List
| No. | Task Name | Objective | Dependencies | Risks |
|-----|-----------|-----------|--------------|-------|
| 1 | Task1_XXX | [Objective] | None | [Risk assessment] |
| 2 | Task2_XXX | [Objective] | Task1 | [Risk assessment] |

### Task Dependency Graph
```
Task1 → Task2 ─┐
         ↓     ├→ Task4
       Task3 ──┘
```

### Alternative Approaches (Not Adopted)
[Explain other decomposition approaches and why they were not chosen:
- Approach X: [Reason]
- Approach Y: [Reason]]

## Risk Assessment
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| [Risk1] | High | Medium | [Measures] |
```

### Field Descriptions

| Section | Description | Requirement |
|---------|-------------|-------------|
| Requirements Analysis | Structured analysis of user requirements | Required |
| Technical Solution Selection | Rationale for technical solution choice | Required, must include solution comparison |
| Task Decomposition | Detailed task breakdown plan | Required, task list must match ReviewIndex |
| Risk Assessment | Identify potential risks and mitigation measures | Recommended |

---

## ReviewIndex.md Format

**ENCODING REQUIREMENT**: This file MUST be saved as UTF-8 without BOM.

### Template

```markdown
# Review Index

## Original Requirements
[Summarize core requirements and objectives in 1-3 paragraphs]

## Task List

| No. | Title | Filename | Task Summary |
|-----|-------|----------|--------------|
| 1 | [Task title] | Task1_XXX.md | [One-sentence summary] |
| 2 | [Task title] | Task2_XXX.md | [One-sentence summary] |

{{INJECT:REVIEWER_INSTRUCTIONS}}

{{INJECT:REPORT_FORMAT}}
```

### Filename Rules

- **Format**: `Task{N}_{Description}.md`
- **Requirements**:
  - N: Sequential integer starting from 1
  - Description: English description, use PascalCase or snake_case
  - May only contain: letters, numbers, underscores
  - **Hyphens "-" are NOT allowed** (reserved for temporary files)
  - Maximum 100 characters in length
- **Examples**:
  - ✅ Task1_LoginUpgrade.md
  - ✅ Task2_RefreshEndpoint.md
  - ✅ Task3_PasswordReset.md
  - ❌ Task1-Login.md (contains "-")
  - ❌ Task1.md (missing description)

### Task List Table Completion

| Column | Description | Example |
|--------|-------------|---------|
| No. | Task number, starting from 1 | 1, 2, 3 |
| Title | Complete task title | Upgrade login endpoint to JWT authentication |
| Filename | Task filename (must match actual generated filename) | Task1_LoginUpgrade.md |
| Task Summary | One-sentence summary, 15-50 words, including key technical points | Session→JWT dual tokens (15min access + 7day refresh) |

### Placeholder Descriptions

- `{{INJECT:REVIEWER_INSTRUCTIONS}}`: MCP tool replaces this with complete AI review guidelines
- `{{INJECT:REPORT_FORMAT}}`: MCP tool replaces this with report.md format specification
- **Position**: Must be placed under designated section headings (see template)
- **Copy exactly**: Include double braces and colon, case-sensitive

---

## Individual Task File Format

**ENCODING REQUIREMENT**: Each task file MUST be saved as UTF-8 without BOM.

### Template

```markdown
# Task {N}: [Task Title]

## Task Description
[Explain in 1-3 sentences what functionality to implement or problem to solve]

## Implementation Approach
[Explain in 2-5 sentences why this solution was chosen, technical selection rationale, expected benefits]

## Implementation

### Old Code
```[language]
# File path (if applicable)
[Complete code of original implementation]
# If creating new module: # New module, no old code
```

### New Code
```[language]
# File path
[Complete code of new implementation]
```
```

### Filename and Content Consistency

**Critical Requirements**:
- The Description in the filename should relate to the task title
- Filename in ReviewIndex.md table must exactly match the actual generated filename
- Task number N must match the N in the filename

**Example**:
```markdown
In ReviewIndex.md write:
| 1 | Upgrade login endpoint to JWT authentication | Task1_LoginUpgrade.md | ... |

Then you MUST generate file: Task1_LoginUpgrade.md
And file content first line must be: # Task 1: Upgrade login endpoint to JWT authentication
```

---

## Complete Example: JWT Authentication System (2 Tasks)

**ENCODING NOTE**: All files shown in this example must be created as UTF-8 without BOM.

### ReviewIndex.md

```markdown
# Review Index

## Original Requirements

Upgrade existing Session authentication system to JWT authentication and implement token refresh mechanism to improve user experience.

## Task List

| No. | Title | Filename | Task Summary |
|-----|-------|----------|--------------|
| 1 | Upgrade login endpoint to JWT authentication | Task1_LoginUpgrade.md | Session→JWT dual tokens (15min access + 7day refresh) |
| 2 | Add token refresh endpoint | Task2_RefreshEndpoint.md | Implement refresh endpoint to exchange refresh token for new access token |

## Instructions for AI Code Reviewer
{{INJECT:REVIEWER_INSTRUCTIONS}}

## Report Format
{{INJECT:REPORT_FORMAT}}
```

### Task1_LoginUpgrade.md

```markdown
# Task 1: Upgrade login endpoint to JWT authentication

## Task Description

Replace existing Session authentication with JWT token authentication, supporting token refresh mechanism.

## Implementation Approach

Use JWT standard (HS256 algorithm) to implement stateless authentication with dual-token mechanism (15min access token + 7day refresh token) to avoid frequent logins while maintaining security.

## Implementation

### Old Code
```python
# auth/login.py
from flask import session

def login(username, password):
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session['user_id'] = user.id
        return {"status": "success"}
    return {"status": "failed"}
```

### New Code
```python
# auth/jwt_auth.py
import jwt
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key"

def login(username, password):
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return {"status": "failed"}

    # Generate dual tokens (15min access + 7day refresh)
    access_token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(minutes=15)
    }, SECRET_KEY)

    refresh_token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(days=7)
    }, SECRET_KEY)

    return {
        "status": "success",
        "access_token": access_token,
        "refresh_token": refresh_token
    }
```
```

### Task2_RefreshEndpoint.md

```markdown
# Task 2: Add token refresh endpoint

## Task Description

Implement refresh_token endpoint to allow users to obtain new access tokens using refresh tokens.

## Implementation Approach

Refresh token has long validity (7 days), users don't need to frequently enter password; access token has short validity (15 minutes), even if leaked the impact is limited. Combining both achieves balance between security and convenience.

## Implementation

### Old Code
```python
# New feature, no old code
```

### New Code
```python
# auth/jwt_auth.py (continued)
def refresh_access_token(refresh_token):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=['HS256'])
        user_id = payload['user_id']

        # Generate new access token
        new_access_token = jwt.encode({
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(minutes=15)
        }, SECRET_KEY)

        return {"status": "success", "access_token": new_access_token}
    except jwt.ExpiredSignatureError:
        return {"status": "failed", "error": "refresh_token_expired"}
    except jwt.InvalidTokenError:
        return {"status": "failed", "error": "invalid_token"}
```
```

---

## MCP Tool Invocation

After generating all files, invoke the MCP tool:

**Tool Name**: `mcp__vet-mediator-mcp__start_review`

**Required Parameters** (all file paths must point to UTF-8 without BOM encoded files):
- `review_index_path`: Temporary file path for ReviewIndex.md
- `draft_paths`: List of task file paths (in order)
- `project_root`: Absolute path to project root directory
- `original_requirement_path`: Temporary file path for OriginalRequirement.md (**must provide**)
- `task_planning_path`: Temporary file path for TaskPlanning.md (**must provide**)

**Recommended Parameters**:
- `initiator`: Name of AI tool initiating the review (e.g., "Claude Code", "Cursor"), used to identify source in report

**Invocation Example**:
```python
mcp__vet-mediator-mcp__start_review(
    review_index_path="/path/to/VetMediatorSessions/tmp/ReviewIndex-abc123.md",
    draft_paths=[
        "/path/to/VetMediatorSessions/tmp/Task1_LoginUpgrade-abc123.md",
        "/path/to/VetMediatorSessions/tmp/Task2_RefreshEndpoint-abc123.md"
    ],
    project_root="/path/to/project",
    original_requirement_path="/path/to/VetMediatorSessions/tmp/OriginalRequirement-abc123.md",
    task_planning_path="/path/to/VetMediatorSessions/tmp/TaskPlanning-abc123.md",
    initiator="Claude Code"
)
```

**MCP Workflow**:
1. Validate all file paths exist
2. Extract target filenames and validate format
3. Copy all files to session directory (automatically handle BOM, unified output to UTF-8 without BOM)
   - OriginalRequirement.md (if provided) - original user requirements
   - TaskPlanning.md (if provided) - AI task decomposition rationale
   - ReviewIndex.md - task list index
   - Task*.md - all task implementations
4. Replace placeholders in ReviewIndex.md, inject complete review rules
   - If OriginalRequirement and TaskPlanning are provided, review rules will guide reviewer to first validate task decomposition reasonableness
5. Launch CLI tool for one-time comprehensive review
   - Reviewer first validates task decomposition reasonableness (if planning documents exist)
   - Then reviews code implementation for each task
6. Generate complete report.md
7. Return review results

**Important Notes**:
- draft_paths array order must match task order in ReviewIndex.md table
- Filenames must strictly follow `Task{N}_{Description}.md` format
- Description must NOT contain hyphens "-"
- Providing original_requirement_path and task_planning_path allows reviewer to validate task decomposition reasonableness
"""

# Rule type mapping table
RULE_TEMPLATES = {
    "file-generator": RULE_FILE_GENERATOR,
}


def get_rule_content(rule_type: str = "file-generator") -> str:
    """Get rule content for specified type

    Args:
        rule_type: Rule type (default: file-generator)

    Returns:
        Rule content string

    Raises:
        KeyError: If rule type does not exist
    """
    return RULE_TEMPLATES[rule_type]


def get_available_rule_types() -> list[str]:
    """Get list of all available rule types"""
    return list(RULE_TEMPLATES.keys())
