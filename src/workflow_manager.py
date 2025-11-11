"""CLI工具审查流程的工作流管理器。"""

import os
import shutil
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

try:
    from .file_generator import FileGenerator
    from .reviewer import CliReviewer
    from .report_parser import ReportParser
    from .data_models import ReviewResult, ParsedReport
    from .cli_config import get_current_config
    from .command_builder import CommandBuilder
except ImportError:
    from file_generator import FileGenerator
    from reviewer import CliReviewer
    from report_parser import ReportParser
    from data_models import ReviewResult, ParsedReport
    from cli_config import get_current_config
    from command_builder import CommandBuilder


class CliWorkflowManager:
    """管理完整的CLI工具审查工作流。"""

    # Session management constants
    DEFAULT_KEEP_SESSIONS = 10  # 保留最近N个session

    def __init__(self, base_dir: str = "VetMediatorSessions", project_root: str = None):
        """初始化工作流管理器。

        Args:
            base_dir: 所有session的基础目录（相对于项目根目录）
            project_root: 项目根目录的绝对路径（必需参数）
        """
        if not project_root:
            raise ValueError("project_root is required parameter")

        self.project_root = Path(project_root)
        self.base_dir = self.project_root / base_dir

    async def start_review(
        self,
        review_index_path: str,
        draft_paths: List[str],
        max_iterations: int = 3,
        initiator: Optional[str] = None,
        original_requirement_path: Optional[str] = None,
        task_planning_path: Optional[str] = None,
        enable_two_stage_review: bool = True
    ) -> ReviewResult:
        """启动CLI工具审查流程（支持两阶段审查）

        Args:
            review_index_path: MCP客户端生成的ReviewIndex.md临时文件路径
            draft_paths: MCP客户端生成的任务文件临时路径列表（按任务顺序）
            max_iterations: 最大迭代轮次（默认3，未来扩展）
            initiator: 发起审查的客户端名称（如ClaudeCode、Cursor等）
            original_requirement_path: OriginalRequirement.md临时文件路径（可选）
            task_planning_path: TaskPlanning.md临时文件路径（可选）
            enable_two_stage_review: 是否启用两阶段审查（默认True）

        Returns:
            ReviewResult instance with review data and parsed report
        """
        # 1. 创建session目录
        session_dir = self._create_session_dir()

        try:
            # 2. 验证两阶段审查参数
            if enable_two_stage_review:
                if not original_requirement_path or not task_planning_path:
                    # 如果启用两阶段审查但缺少文件，回退到单阶段模式
                    enable_two_stage_review = False

            # 3. 提前加载config获取审阅者名称
            config = get_current_config(self.project_root)
            command_builder = CommandBuilder(config)
            reviewer = command_builder.get_display_name()

            # 4. 复制文件到session目录并统一编码，注入元数据
            file_gen = FileGenerator(session_dir, project_root=self.project_root)

            review_file, task_files = file_gen.copy_files_to_session(
                review_index_path,
                draft_paths,
                initiator=initiator,
                reviewer=reviewer,
                original_requirement_path=original_requirement_path,
                task_planning_path=task_planning_path
            )

            # 5. 启动CLI工具审查
            cli_reviewer = CliReviewer()
            result = await cli_reviewer.start_review(
                session_dir=str(session_dir),
                project_root=str(self.project_root)
            )

            # 5. 解析report.md并重新构造ReviewResult（dataclass不可变）
            # 只要report.md存在且有内容，就尝试解析（不管进程退出码）
            if result.report_content and result.report_content.strip():
                parsed = ReportParser.parse_report(result.report_content)
                # 重新构造ReviewResult，使用parsed的status
                result = ReviewResult(
                    status=parsed.status,
                    report_content=result.report_content,
                    log_tail=result.log_tail,
                    execution_time=result.execution_time,
                    parsed=parsed,
                    session_dir=result.session_dir
                )
            else:
                # 报告不存在或为空，保持原始status
                result = ReviewResult(
                    status=result.status,
                    report_content=result.report_content,
                    log_tail=result.log_tail,
                    execution_time=result.execution_time,
                    parsed=ParsedReport(
                        status=result.status,
                        issues=[],
                        suggestions=[],
                        raw_content=result.report_content or ""
                    ),
                    session_dir=result.session_dir
                )

            return result

        except Exception as e:
            return ReviewResult(
                status="failed",
                report_content="",
                log_tail=f"Error: {str(e)}",
                execution_time=0,
                parsed=ParsedReport(
                    status="failed",
                    issues=[],
                    suggestions=[],
                    raw_content=""
                ),
                session_dir=str(session_dir) if 'session_dir' in locals() else None
            )

    def _cleanup_old_sessions(self, keep_count: int = 10):
        """清理旧的session目录，保留最近N个

        Args:
            keep_count: 保留最近N个session目录（默认10个）
        """
        if not self.base_dir.exists():
            return

        # 获取所有session目录 | Get all session directories
        session_dirs = [d for d in self.base_dir.iterdir() if d.is_dir() and d.name.startswith("session-")]

        # 按修改时间排序（最新的在前）| Sort by modification time (newest first)
        session_dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)

        # 删除超出保留数量的旧session | Delete old sessions beyond keep count
        for old_session in session_dirs[keep_count:]:
            try:
                shutil.rmtree(old_session)
            except Exception:
                pass  # 忽略删除失败的情况 | Ignore deletion failures

    def _create_session_dir(self) -> Path:
        """创建session目录 | Create session directory

        Returns:
            创建的session目录路径 | Created session directory path
        """
        # 清理旧的session目录（保留最近10个）| Cleanup old session directories (keep most recent 10)
        self._cleanup_old_sessions(keep_count=self.DEFAULT_KEEP_SESSIONS)

        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

        # Directory path: VetMediatorSessions/session-{timestamp}/
        session_dir = self.base_dir / f"session-{timestamp}"

        # Create directory
        session_dir.mkdir(parents=True, exist_ok=True)

        return session_dir

    def cleanup_session(self, session_dir: str) -> bool:
        """清理session目录

        Args:
            session_dir: Session目录路径

        Returns:
            True表示清理成功，False表示失败
        """
        try:
            import shutil
            shutil.rmtree(session_dir)
            return True
        except Exception:
            return False
