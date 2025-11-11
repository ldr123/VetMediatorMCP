"""Codex审查结果的报告解析器。"""

import re
from typing import Dict, List, Optional

# Import data models
try:
    from .data_models import ParsedReport
except ImportError:
    from data_models import ParsedReport


class ReportParser:
    """解析Codex审查的report.md文件。"""

    @staticmethod
    def parse_report(report_content: str) -> ParsedReport:
        """解析report.md内容为结构化数据。

        Args:
            report_content: report.md的原始内容

        Returns:
            包含结构化数据的ParsedReport实例
        """
        if not report_content or not report_content.strip():
            return ParsedReport(
                status="unknown",
                issues=[],
                suggestions=[],
                raw_content=report_content or ""
            )

        # 1. 检查报告完整性标记
        has_completion_marker = ("<!-- REVIEW_COMPLETE -->" in report_content or
                                 "---END_OF_REVIEW---" in report_content)

        if not has_completion_marker:
            # 向后兼容：检查是否是旧版本完整报告
            has_conclusion = bool(re.search(r'##\s+(Summary|Conclusion)', report_content, re.IGNORECASE))
            report_length = len(report_content.strip())

            if not (has_conclusion and report_length > 1000):
                # 报告不完整（流式写入中断）
                return ParsedReport(
                    status="incomplete",
                    issues=[],
                    suggestions=[],
                    raw_content=report_content
                )

        # 2. 继续正常解析
        status = ReportParser._extract_status(report_content)
        issues = ReportParser._extract_issues(report_content)
        suggestions = ReportParser._extract_suggestions(report_content)

        return ParsedReport(
            status=status,
            issues=issues,
            suggestions=suggestions,
            raw_content=report_content
        )

    @staticmethod
    def _extract_status(content: str) -> str:
        """从报告中提取审查状态。

        Returns:
            "approved", "major_issues", "minor_issues"或"unknown"
        """
        # Remove BOM if present
        content = content.lstrip('\ufeff')

        # 0. 优先检查最直接的格式：## Status\n{status_value}
        status_match = re.search(r'##\s+Status\s*\n\s*(\w+)', content, re.IGNORECASE)
        if status_match:
            status = status_match.group(1).strip().lower()
            if status in ["approved", "major_issues", "minor_issues"]:
                return status

        # 1. 尝试旧格式：Match "## Overall Assessment" followed by status on next line
        match = re.search(r'##\s+Overall\s+Assessment\s*\n\s*([A-Z_]+)', content, re.IGNORECASE)
        if match:
            status = match.group(1).strip().upper()
            if status == "APPROVED":
                return "approved"
            elif status == "MAJOR_ISSUES":
                return "major_issues"
            elif status == "MINOR_ISSUES":
                return "minor_issues"

        # 2. 尝试新格式：检测Quality Assessment表格和Issues
        has_quality_table = bool(re.search(r'###\s+Quality\s+Assessment', content, re.IGNORECASE))

        if has_quality_table:
            # 新格式：从Quality Assessment和Issues推断status
            # 检查是否有Critical评分或P0 issues
            has_critical = bool(re.search(r'\|\s*Critical\s*\||Issues\s+Found.*?\[P0\]', content, re.IGNORECASE | re.DOTALL))
            if has_critical:
                return "major_issues"

            # 检查是否有Major评分或P1 issues
            has_major = bool(re.search(r'\|\s*Major\s*\||Issues\s+Found.*?\[P1\]', content, re.IGNORECASE | re.DOTALL))
            if has_major:
                return "minor_issues"

            # 都是Pass或Minor，认为approved
            return "approved"

        # 3. Fallback: 旧格式兼容（检查Overall Assessment和Conclusion章节）
        has_overall_assessment = bool(re.search(r'##\s+Overall\s+Assessment', content, re.IGNORECASE))
        has_conclusion = bool(re.search(r'##\s+Conclusion', content, re.IGNORECASE))
        has_error_markers = bool(re.search(r'\[ERROR\]|\bFAILED\b|\bCRITICAL\b', content, re.IGNORECASE))

        if (has_overall_assessment or has_conclusion) and not has_error_markers and len(content.strip()) > 500:
            # 报告完整且无明显错误，默认为approved
            return "approved"

        return "unknown"

    @staticmethod
    def _extract_issues(content: str) -> List[Dict[str, str]]:
        """从报告中提取问题列表。

        Returns:
            {"priority": "P0/P1/P2", "description": "..."}的列表
        """
        issues = []

        # Find "## Issue List" section
        match = re.search(r'##\s*Issue\s*List\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL | re.IGNORECASE)
        if not match:
            return issues

        issues_section = match.group(1)

        # Extract issues: - [P0] description or - [P1] file:line - description
        pattern = r'-\s*\[([P0-2])\]\s*(.+)'
        for issue_match in re.finditer(pattern, issues_section):
            priority = issue_match.group(1).strip()
            description = issue_match.group(2).strip()

            # Skip empty entries
            if description.lower() in ['', 'none', 'n/a']:
                continue

            issues.append({
                "priority": priority,
                "description": description
            })

        return issues

    @staticmethod
    def _extract_suggestions(content: str) -> List[str]:
        """从报告中提取建议列表。

        Returns:
            建议字符串列表
        """
        suggestions = []

        # Find "## Improvement Suggestions" section
        match = re.search(r'##\s*Improvement\s*Suggestions\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL | re.IGNORECASE)
        if not match:
            return suggestions

        suggestions_section = match.group(1)

        # Extract suggestions: - suggestion
        pattern = r'-\s*(.+)'
        for sug_match in re.finditer(pattern, suggestions_section):
            suggestion = sug_match.group(1).strip()

            # Skip empty entries
            if suggestion.lower() in ['', 'none', 'n/a']:
                continue

            suggestions.append(suggestion)

        return suggestions
