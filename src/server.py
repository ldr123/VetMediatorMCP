"""CLI工具审查工作流的MCP服务器，提供完整的工作流管理。"""

import os
import sys
import asyncio
import hashlib
from pathlib import Path
from typing import Any, List, Optional

# Fix import path for both module and direct execution
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from mcp.server import InitializationOptions, NotificationOptions, Server
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field
from mcp.server.stdio import stdio_server

# Try relative import first, fallback to absolute
try:
    from .workflow_manager import CliWorkflowManager
    from .rule_templates import get_rule_content, get_available_rule_types
except ImportError:
    from workflow_manager import CliWorkflowManager
    from rule_templates import get_rule_content, get_available_rule_types


class StartReviewArgs(BaseModel):
    """start_review工具的参数"""
    review_index_path: str = Field(
        description="MCP客户端生成的ReviewIndex.md临时文件绝对路径（UTF-8编码，MCP服务器自动处理BOM）"
    )
    draft_paths: List[str] = Field(
        description="MCP客户端生成的任务文件临时路径列表（按任务顺序，UTF-8编码，MCP服务器自动处理BOM）"
    )
    project_root: str = Field(description="项目根目录绝对路径（必需参数，由MCP客户端传递）")
    max_iterations: int = Field(default=3, description="最大迭代轮次（未来扩展），默认3轮")
    initiator: Optional[str] = Field(default=None, description="发起审查的客户端名称（如ClaudeCode、Cursor等），可选")
    original_requirement_path: Optional[str] = Field(
        default=None,
        description="OriginalRequirement.md临时文件绝对路径（启用两阶段审查时推荐提供）"
    )
    task_planning_path: Optional[str] = Field(
        default=None,
        description="TaskPlanning.md临时文件绝对路径（启用两阶段审查时推荐提供）"
    )


class ShowCliConfigArgs(BaseModel):
    """show_cli_config工具的参数"""
    project_root: str = Field(description="项目根目录绝对路径")


class GetReviewRuleHashArgs(BaseModel):
    """get_review_rule_hash工具的参数"""
    rule_type: str = Field(
        default="file-generator",
        description="规则类型：file-generator（文件生成规则）"
    )


class GetReviewRulesArgs(BaseModel):
    """get_review_rules工具的参数"""
    rule_type: str = Field(
        default="file-generator",
        description="规则类型：file-generator（文件生成规则）"
    )



# Initialize MCP server
app = Server("vet-mediator-mcp")

# workflow_manager will be created per-request with project_root


@app.list_tools()
async def list_tools() -> list[Tool]:
    """列出可用的MCP工具"""
    return [
        Tool(
            name="start_review",
            description=(
                "启动CLI工具审查工作流：创建session目录、复制文件、启动CLI进程、监控进度、解析报告"
            ),
            inputSchema=StartReviewArgs.model_json_schema()
        ),
        Tool(
            name="show_cli_config",
            description=(
                "显示CLI工具配置界面，允许用户查看所有配置工具的健康状态并切换当前激活的CLI工具"
            ),
            inputSchema=ShowCliConfigArgs.model_json_schema()
        ),
        Tool(
            name="get_review_rule_hash",
            description=(
                "获取审查规则文件的SHA-256 hash值（前12位），用于本地缓存版本检测。"
                "AI代理可以通过hash判断本地缓存的规则文件是否是最新版本。"
            ),
            inputSchema=GetReviewRuleHashArgs.model_json_schema()
        ),
        Tool(
            name="get_review_rules",
            description=(
                "获取完整的审查规则文档内容（Markdown格式）。"
                "仅在hash不匹配时调用，用于更新本地缓存。"
                "规则文档包含：文件格式规范、模板、示例、MCP调用说明等。"
            ),
            inputSchema=GetReviewRulesArgs.model_json_schema()
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """处理MCP工具调用

    Args:
        name: 工具名称（"start_review"、"show_cli_config"、"get_review_rule_hash"、"get_review_rules"）
        arguments: 工具参数

    Returns:
        包含结果的TextContent列表
    """
    if name == "get_review_rule_hash":
        args = GetReviewRuleHashArgs(**arguments)
        try:
            # 从内置模板获取规则内容并计算hash
            content = get_rule_content(args.rule_type)
            hash_value = hashlib.sha256(content.encode('utf-8')).hexdigest()[:12]
            return [TextContent(type="text", text=hash_value)]
        except KeyError:
            available_types = get_available_rule_types()
            return [TextContent(
                type="text",
                text=f"[ERROR] Unknown rule type: {args.rule_type}. Available types: {', '.join(available_types)}"
            )]
        except Exception as e:
            return [TextContent(type="text", text=f"[ERROR] Failed to calculate hash: {str(e)}")]

    elif name == "get_review_rules":
        args = GetReviewRulesArgs(**arguments)
        try:
            # 从内置模板获取规则内容
            content = get_rule_content(args.rule_type)
            return [TextContent(type="text", text=content)]
        except KeyError:
            available_types = get_available_rule_types()
            return [TextContent(
                type="text",
                text=f"[ERROR] Unknown rule type: {args.rule_type}. Available types: {', '.join(available_types)}"
            )]
        except Exception as e:
            return [TextContent(type="text", text=f"[ERROR] Failed to read rules: {str(e)}")]

    elif name == "start_review":
        args = StartReviewArgs(**arguments)

        # Create workflow_manager instance with project_root
        workflow_manager = CliWorkflowManager(
            base_dir="VetMediatorSessions",
            project_root=args.project_root
        )

        # Start review workflow
        try:
            result = await workflow_manager.start_review(
                review_index_path=args.review_index_path,
                draft_paths=args.draft_paths,
                max_iterations=args.max_iterations,
                initiator=args.initiator,
                original_requirement_path=args.original_requirement_path,
                task_planning_path=args.task_planning_path
            )

            # Format result as text response
            # If review completed and parsed, use parsed status; otherwise use execution status
            if result.parsed:
                review_status = result.parsed.status
                status_emoji = {
                    "approved": "[APPROVED]",
                    "major_issues": "[MAJOR_ISSUES]",
                    "minor_issues": "[MINOR_ISSUES]",
                    "incomplete": "[INCOMPLETE]"
                }.get(review_status, "[UNKNOWN]")
            else:
                review_status = result.status
                status_emoji = {
                    "completed": "[SUCCESS]",
                    "timeout": "[TIMEOUT]",
                    "failed": "[FAILED]",
                    "incomplete": "[INCOMPLETE]"
                }.get(review_status, "[UNKNOWN]")

            response_text = f"""{status_emoji} Review {review_status}

**Execution Time**: {result.execution_time} seconds
**Session Directory**: {result.session_dir or 'N/A'}

**Review Report**:
{result.report_content}

**Review Log (last 10 lines)**:
{result.log_tail}
"""
            return [TextContent(type="text", text=response_text)]

        except Exception as e:
            error_text = f"[ERROR] Review workflow failed: {str(e)}"
            return [TextContent(type="text", text=error_text)]

    elif name == "show_cli_config":
        args = ShowCliConfigArgs(**arguments)

        try:
            # Load current configuration
            try:
                from .cli_config import load_config
            except ImportError:
                from cli_config import load_config

            config = load_config(Path(args.project_root))
            current_tool = config.get("current_cli_tool", "iflow")

            # Launch GUI in background (using -m module mode)
            import subprocess
            ui_cmd = [
                sys.executable,
                "-m",
                "src.cli_check_ui",
                "--project-root", args.project_root,
                "--current-tool", current_tool,
                "--error-detail", "Configuration Management",
                "--config-mode"
            ]

            # Start background process
            subprocess.Popen(
                ui_cmd,
                cwd=args.project_root,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            response_text = f"""[INFO] CLI Configuration Window Opened

Current Active Tool: {current_tool}
Project Root: {args.project_root}

The GUI window has been launched in the background.
You can:
- View all configured CLI tools and their health status
- Switch to another CLI tool by clicking 'Activate'
- Check configuration files (Global and Project)
- Close the window anytime

Note: Changes made in the configuration window will take effect immediately.
"""
            return [TextContent(type="text", text=response_text)]

        except Exception as e:
            error_text = f"[ERROR] Failed to open CLI configuration window: {str(e)}"
            return [TextContent(type="text", text=error_text)]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def async_main():
    """MCP服务器异步主入口"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="vet-mediator-mcp",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                )
            )
        )


def main():
    """同步入口（由uv调用）"""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
