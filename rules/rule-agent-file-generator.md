# CLI工具交叉验证文件生成规则

**触发词**：`使用vet验证` 或 `让vet帮我验证` 或 `使用CLI工具交叉验证`

**执行步骤**：
1. 生成ReviewIndex.md（审查索引）
2. 为每个任务生成独立的文件：Task1_XXX.md, Task2_XXX.md, ...
3. 调用MCP工具：`mcp__vet-mediator-mcp__start_review`
   - 必需参数：
     - `review_index_path`: ReviewIndex.md的临时文件路径
     - `draft_paths`: 任务文件路径列表（按顺序）
     - `project_root`: 项目根目录绝对路径
   - 推荐参数：
     - `initiator`: 发起审查的AI工具名称（如"Claude Code"、"Cursor"等），用于在报告中标识来源
   - 可选参数：
     - `max_iterations`: 最大迭代轮次（默认3，未来扩展）

**编码要求**：
- 所有生成的文件使用UTF-8编码（不带BOM）
- MCP服务器自动处理统一输出UTF-8无BOM格式


**[重要!!!]临时文件命名约定**:
- ReviewIndex.md: `ReviewIndex-{random}.md`
- 任务文件: `{TargetName}-{random}.md`（如 `Task1_LoginUpgrade-abc123.md`）
- MCP服务器会自动提取目标文件名（截取最后一个"-"前的部分）
- 将临时文件写入VetMediatorSessions/tmp目录（如果目录不存在就生成），注意：一定要生成到这个目录，而不是生成到系统临时目录(比如~/)

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

**工具名**: `mcp__codex-review-mcp__start_review`

**必需参数**:
- `review_index_path`: ReviewIndex.md临时文件的绝对路径（string）
- `draft_paths`: 任务文件临时路径列表（List[string]），按任务顺序排列
- `project_root`: 项目根目录的绝对路径（string）

**调用示例**:
```python
mcp__codex-review-mcp__start_review(
    review_index_path="/tmp/ReviewIndex-abc123.md",
    draft_paths=[
        "/tmp/Task1_LoginUpgrade-abc123.md",
        "/tmp/Task2_RefreshEndpoint-abc123.md"
    ],
    project_root="/path/to/project"
)
```

**MCP工作流程**:
1. 验证所有文件路径存在
2. 提取目标文件名并验证格式
3. 复制文件到session目录（自动处理BOM，统一输出UTF-8无BOM）
4. 替换ReviewIndex.md中的占位符，注入完整的审查规则
5. 启动CLI工具进程执行审查
6. 监控进度，生成report.md
7. 返回审查结果

**注意事项**:
- draft_paths数组顺序必须与ReviewIndex.md表格中的任务顺序一致
- 文件名必须严格遵循`Task{N}_{Description}.md`格式
- Description中不能包含连字符"-"
