"""Agent审查工作流的数据模型。

此模块定义了类型化的数据结构来替代原始字典，
提供类型安全、IDE自动补全，并防止键名拼写错误。
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Optional


@dataclass
class ParsedReport:
    """解析后的审查报告结构。

    表示ReportParser.parse_report()的结构化输出。

    Attributes:
        status: 审查状态（"approved", "major_issues", "minor_issues", "unknown"）
        issues: 问题列表，包含优先级和描述
        suggestions: 改进建议列表
        raw_content: 原始report.md内容
    """
    status: str
    issues: List[Dict[str, str]]
    suggestions: List[str]
    raw_content: str

    def to_dict(self) -> Dict:
        """转换为字典（向后兼容）。

        Returns:
            字典表示
        """
        return asdict(self)


@dataclass
class ReviewResult:
    """完整的审查工作流结果。

    表示CliReviewer.start_review()和CliWorkflowManager.start_review()的最终输出。

    Attributes:
        status: 执行状态（"completed", "failed", "timeout"）
        report_content: report.md的完整内容
        log_tail: CLI工具日志的最后N行
        execution_time: 执行时间（秒）
        parsed: 解析后的报告结构（解析失败时为None）
        session_dir: 会话目录路径（未创建时为None）
    """
    status: str
    report_content: str
    log_tail: str
    execution_time: int
    parsed: Optional[ParsedReport] = None
    session_dir: Optional[str] = None

    def to_dict(self) -> Dict:
        """转换为字典（向后兼容）。

        parsed字段如果存在也会转换为字典。

        Returns:
            字典表示
        """
        result = {
            "status": self.status,
            "report_content": self.report_content,
            "log_tail": self.log_tail,
            "execution_time": self.execution_time
        }

        if self.parsed is not None:
            result["parsed"] = self.parsed.to_dict()

        if self.session_dir is not None:
            result["session_dir"] = self.session_dir

        return result

    @classmethod
    def from_dict(cls, data: Dict) -> 'ReviewResult':
        """从字典创建ReviewResult实例。

        Args:
            data: 包含审查结果数据的字典

        Returns:
            ReviewResult实例
        """
        parsed_data = data.get("parsed")
        parsed = None
        if parsed_data is not None:
            parsed = ParsedReport(**parsed_data)

        return cls(
            status=data["status"],
            report_content=data["report_content"],
            log_tail=data["log_tail"],
            execution_time=data["execution_time"],
            parsed=parsed,
            session_dir=data.get("session_dir")
        )
