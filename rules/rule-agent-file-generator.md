# CLI工具交叉验证文件生成规则

**触发词**：`使用vet验证` 或 `让vet帮我验证` 或 `使用CLI工具交叉验证`

**执行步骤**：
1. 生成OriginalRequirement.md（用户原始需求）
2. 生成TaskPlanning.md（任务规划方案）
3. 生成ReviewIndex.md（审查索引）
4. 为每个任务生成独立的文件：Task1_XXX.md, Task2_XXX.md, ...
5. 调用MCP工具：`mcp__vet-mediator-mcp__start_review`
   - 必需参数：
     - `review_index_path`: ReviewIndex.md的临时文件路径
     - `draft_paths`: 任务文件路径列表（按顺序）
     - `project_root`: 项目根目录绝对路径
   - 推荐参数（提供完整审查上下文）：
     - `original_requirement_path`: OriginalRequirement.md的临时文件路径（可选但强烈推荐）
     - `task_planning_path`: TaskPlanning.md的临时文件路径（可选但强烈推荐）
     - `initiator`: 发起审查的AI工具名称（如"Claude Code"、"Cursor"等），用于在报告中标识来源
   - 可选参数：
     - `max_iterations`: 最大迭代轮次（默认3，未来扩展）

**编码要求**：
- 所有生成的文件使用UTF-8编码（不带BOM）
- MCP服务器自动处理统一输出UTF-8无BOM格式


**[重要!!!]临时文件命名约定**:
- OriginalRequirement.md: `OriginalRequirement-{random}.md`
- TaskPlanning.md: `TaskPlanning-{random}.md`
- ReviewIndex.md: `ReviewIndex-{random}.md`
- 任务文件: `{TargetName}-{random}.md`（如 `Task1_LoginUpgrade-abc123.md`）
- MCP服务器会自动提取目标文件名（截取最后一个"-"前的部分）
- 将临时文件写入VetMediatorSessions/tmp目录（如果目录不存在就生成），注意：一定要生成到这个目录，而不是生成到系统临时目录(比如~/)

---

## OriginalRequirement.md格式

### 模板

```markdown
# 用户原始需求

## 用户输入（Verbatim）
[完整保留用户的原话，一字不改，包括：
- 初始需求描述
- 多轮对话中的补充说明
- 用户强调的重点
- 用户提到的约束条件]

## 对话上下文
[如果有多轮对话，记录关键的澄清过程：
Q: [AI代理的疑问]
A: [用户的回答]
...]

## 隐含需求推断
[AI代理基于经验推断出的隐含需求：
- 非功能性需求（性能、安全、可维护性）
- 行业最佳实践
- 与现有系统的兼容性考虑]

## 边界与非需求
[明确指出哪些是NOT在范围内的：
- 用户明确不需要的功能
- 延后处理的需求
- 超出技术范围的部分]
```

### 填写说明

| 章节 | 说明 | 要求 |
|-----|------|------|
| 用户输入（Verbatim） | 原封不动地保留用户的原话 | 必填，不要改写或润色 |
| 对话上下文 | 多轮对话的关键澄清 | 如有多轮对话则必填 |
| 隐含需求推断 | AI推断的未明说需求 | 可选，但推荐填写 |
| 边界与非需求 | 明确不做什么 | 可选，但有助于审查员理解范围 |

---

## TaskPlanning.md格式

### 模板

```markdown
# 任务规划方案

## 需求分析
### 核心目标
[用1-2句话概括最核心的目标]

### 关键约束
- 技术栈约束：[例如：必须使用.NET 8]
- 时间约束：[例如：需要在2周内完成]
- 兼容性约束：[例如：需要兼容旧版API]

### 预期产出
[列出最终交付物]

## 技术方案选型
### 方案对比
| 方案 | 优点 | 缺点 | 是否采用 |
|-----|------|------|---------|
| 方案A | ... | ... | ✅ |
| 方案B | ... | ... | ❌ 理由... |

### 最终选型依据
[说明为什么选择当前方案]

## 任务拆分
### 拆分原则
- 按[模块/功能/层次/依赖]进行拆分
- 每个任务的粒度控制在[X]小时内完成

### 任务列表
| 编号 | 任务名 | 目标 | 依赖 | 风险 |
|-----|--------|------|------|------|
| 1 | Task1_XXX | [目标] | 无 | [风险评估] |
| 2 | Task2_XXX | [目标] | Task1 | [风险评估] |

### 任务依赖图
```
Task1 → Task2 ─┐
         ↓     ├→ Task4
       Task3 ──┘
```

### 替代方案（未采用）
[说明有哪些其他拆分方式，为什么不选择：
- 方案X：[原因]
- 方案Y：[原因]]

## 风险评估
| 风险 | 影响 | 概率 | 缓解措施 |
|-----|------|------|---------|
| [风险1] | 高 | 中 | [措施] |
```

### 填写说明

| 章节 | 说明 | 要求 |
|-----|------|------|
| 需求分析 | 对用户需求的结构化分析 | 必填 |
| 技术方案选型 | 说明为什么选择这个技术方案 | 必填，必须包含方案对比 |
| 任务拆分 | 详细的任务拆分计划 | 必填，任务列表必须与ReviewIndex一致 |
| 风险评估 | 识别潜在风险和缓解措施 | 推荐填写 |

---

## ReviewIndex.md格式

### 模板

```markdown
# Review Index

## 原始需求
[用户原始需求，1-3段话概括核心需求和目标]

## 任务列表

| 编号 | 标题 | 文件名 | 任务摘要 |
|-----|------|--------|---------|
| 1 | [任务标题] | Task1_XXX.md | [一句话概括] |
| 2 | [任务标题] | Task2_XXX.md | [一句话概括] |

{{INJECT:REVIEWER_INSTRUCTIONS}}

{{INJECT:REPORT_FORMAT}}
```

### 文件名规则

- **格式**: `Task{N}_{Description}.md`
- **要求**:
  - N: 从1开始的连续整数
  - Description: 英文描述，使用PascalCase或snake_case
  - 只能包含：字母、数字、下划线
  - **不允许使用连字符"-"**（保留用于临时文件）
  - 长度不超过100字符
- **示例**:
  - ✅ Task1_LoginUpgrade.md
  - ✅ Task2_RefreshEndpoint.md
  - ✅ Task3_PasswordReset.md
  - ❌ Task1-Login.md（包含"-"）
  - ❌ Task1.md（缺少描述）

### 任务列表表格填写

| 列名 | 说明 | 示例 |
|-----|------|------|
| 编号 | 任务序号，从1开始 | 1, 2, 3 |
| 标题 | 任务的完整标题 | 升级登录接口为JWT认证 |
| 文件名 | 任务文件名（必须与实际生成的文件名一致） | Task1_LoginUpgrade.md |
| 任务摘要 | 一句话概括，15-50字，包含关键技术点 | Session→JWT双Token（15分钟访问+7天刷新） |

### 占位符说明

- `{{INJECT:REVIEWER_INSTRUCTIONS}}`：MCP工具会替换为完整的AI审查指南
- `{{INJECT:REPORT_FORMAT}}`：MCP工具会替换为report.md格式规范
- **位置**：必须在指定章节标题下（见模板）
- **原样复制**：包括双花括号和冒号，区分大小写

---

## 单个任务文件格式

### 模板

```markdown
# 任务{N}：[任务标题]

## 任务内容
[1-3句话，说明要实现什么功能或解决什么问题]

## 任务思路
[2-5句话，说明为什么选择这个方案、技术选型理由、预期收益]

## 实现

### 老代码
```[语言]
# 文件路径（如果适用）
[原有实现的完整代码]
# 如果是新建模块，写：# 新建模块，无老代码
```

### 新代码
```[语言]
# 文件路径
[新实现的完整代码]
```
```

### 文件命名与内容一致性

**关键要求**:
- 文件名中的Description应该与任务标题相关
- ReviewIndex.md表格中的文件名必须与实际生成的文件名完全一致
- 任务编号N必须与文件名中的N一致

**示例**:
```markdown
ReviewIndex.md中写：
| 1 | 升级登录接口为JWT认证 | Task1_LoginUpgrade.md | ... |

那么必须生成文件：Task1_LoginUpgrade.md
且文件内容第一行为：# 任务1：升级登录接口为JWT认证
```

---

## 完整示例：JWT认证系统（2个任务）

### ReviewIndex.md

```markdown
# Review Index

## 原始需求

将现有Session认证系统升级为JWT认证，并实现Token刷新机制以提升用户体验。

## 任务列表

| 编号 | 标题 | 文件名 | 任务摘要 |
|-----|------|--------|---------|
| 1 | 升级登录接口为JWT认证 | Task1_LoginUpgrade.md | Session→JWT双Token（15分钟访问+7天刷新） |
| 2 | 添加Token刷新接口 | Task2_RefreshEndpoint.md | 实现refresh端点，用刷新令牌换取新访问令牌 |

## Instructions for AI Code Reviewer
{{INJECT:REVIEWER_INSTRUCTIONS}}

## Report Format
{{INJECT:REPORT_FORMAT}}
```

### Task1_LoginUpgrade.md

```markdown
# 任务1：升级登录接口为JWT认证

## 任务内容

将原有的Session认证方式替换为JWT Token认证，支持Token刷新机制。

## 任务思路

使用JWT标准（HS256算法）实现无状态认证，设置双Token机制（15分钟访问令牌+7天刷新令牌），避免频繁登录，同时保证安全性。

## 实现

### 老代码
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

### 新代码
```python
# auth/jwt_auth.py
import jwt
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key"

def login(username, password):
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return {"status": "failed"}

    # 生成双Token（15分钟访问+7天刷新）
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
# 任务2：添加Token刷新接口

## 任务内容

实现refresh_token端点，允许用户使用刷新令牌获取新的访问令牌。

## 任务思路

刷新令牌有效期长（7天），用户无需频繁输入密码；访问令牌有效期短（15分钟），即使泄露影响也有限。两者结合实现安全性和便利性的平衡。

## 实现

### 老代码
```python
# 新建功能，无老代码
```

### 新代码
```python
# auth/jwt_auth.py (续)
def refresh_access_token(refresh_token):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=['HS256'])
        user_id = payload['user_id']

        # 生成新的访问令牌
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

## MCP工具调用

生成所有文件后，调用MCP工具：

**工具名**: `mcp__vet-mediator-mcp__start_review`

**必需参数**:
- `review_index_path`: ReviewIndex.md的临时文件路径
- `draft_paths`: 任务文件路径列表（按顺序）
- `project_root`: 项目根目录绝对路径
- `original_requirement_path`: OriginalRequirement.md的临时文件路径（**必须提供**）
- `task_planning_path`: TaskPlanning.md的临时文件路径（**必须提供**）

**推荐参数**:
- `initiator`: 发起审查的AI工具名称（如"Claude Code"、"Cursor"等），用于在报告中标识来源

**调用示例**:
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

**MCP工作流程**:
1. 验证所有文件路径存在
2. 提取目标文件名并验证格式
3. 复制所有文件到session目录（自动处理BOM，统一输出UTF-8无BOM）
   - OriginalRequirement.md（如果提供）- 用户原始需求
   - TaskPlanning.md（如果提供）- AI任务拆分思路
   - ReviewIndex.md - 任务列表索引
   - Task*.md - 所有任务实现
4. 替换ReviewIndex.md中的占位符，注入完整审查规则
   - 如果提供了OriginalRequirement和TaskPlanning，审查规则会引导审查员先验证任务拆分的合理性
5. 启动CLI工具进行一次性整体审查
   - 审查员先验证任务拆分是否合理（如果有规划文档）
   - 再审查每个任务的代码实现
6. 生成完整的report.md
7. 返回审查结果

**注意事项**:
- draft_paths数组顺序必须与ReviewIndex.md表格中的任务顺序一致
- 文件名必须严格遵循`Task{N}_{Description}.md`格式
- Description中不能包含连字符"-"
- 提供original_requirement_path和task_planning_path可以让审查员验证任务拆分的合理性
