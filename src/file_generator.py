"""CLI审查工作流的文件生成器。"""

import json
import re
from pathlib import Path
from typing import List, Optional

# Import encoding detector
try:
    from .encoding_utils import EncodingDetector
except ImportError:
    from encoding_utils import EncodingDetector

# Import review templates
try:
    from .template import GENERIC_REVIEWER_TEMPLATE, REPORT_FORMAT_TEMPLATE
except ImportError:
    from template import GENERIC_REVIEWER_TEMPLATE, REPORT_FORMAT_TEMPLATE


class FileGenerator:
    """为CLI审查生成所有必需的文件。"""

    def __init__(self, session_dir: Path, project_root: Path) -> None:
        """初始化文件生成器。

        Args:
            session_dir: 会话目录路径
            project_root: 项目根目录路径
        """
        self.session_dir = Path(session_dir)
        self.project_root = Path(project_root)

    def _expand_placeholders(self, text: str, initiator: Optional[str] = None, reviewer: Optional[str] = None) -> str:
        """替换文本中的占位符为完整的审查规则和元数据。

        占位符系统：
        - {{INJECT:REVIEWER_INSTRUCTIONS}} → 完整的六步工作流和七维质量标准
        - {{INJECT:REPORT_FORMAT}} → 完整的report.md格式规范（包含元数据占位符）
        - {{INITIATOR}} → 发起者名称（在REPORT_FORMAT中）
        - {{REVIEWER}} → 审阅者名称（在REPORT_FORMAT中）

        使用通用模板GENERIC_REVIEWER_TEMPLATE（agent-agnostic设计）。

        这使MCP客户端能够生成轻量级文件（~2k tokens），
        而审查工具获得完整规则（~15-20k tokens）。

        Args:
            text: 包含占位符的原始文本
            initiator: 发起审查的客户端名称（如ClaudeCode）
            reviewer: 审阅工具名称（如iFlow）

        Returns:
            替换占位符后的文本
        """
        text = text.replace('{{INJECT:REVIEWER_INSTRUCTIONS}}', GENERIC_REVIEWER_TEMPLATE)

        # 替换REPORT_FORMAT，其中包含{{INITIATOR}}和{{REVIEWER}}占位符
        report_format = REPORT_FORMAT_TEMPLATE
        report_format = report_format.replace('{{INITIATOR}}', initiator or '未指定')
        report_format = report_format.replace('{{REVIEWER}}', reviewer or '未指定')

        text = text.replace('{{INJECT:REPORT_FORMAT}}', report_format)
        return text

    def copy_files_to_session(
        self,
        review_index_path: str,
        draft_paths: List[str],
        initiator: Optional[str] = None,
        reviewer: Optional[str] = None
    ) -> tuple[Path, List[Path]]:
        """将MCP客户端临时文件复制到会话目录，统一使用UTF-8编码，注入元数据。

        工作流程：
        1. 智能读取ReviewIndex.md临时文件（尝试UTF-8/UTF-8-BOM/GBK/GB18030）
        2. 替换ReviewIndex.md中的占位符（注入完整审查规则和元数据）
        3. 写入会话目录（统一使用UTF-8无BOM）
        4. 处理每个任务文件（提取目标文件名、验证格式、复制）
        5. 删除所有临时文件（使用try-finally确保清理）

        Args:
            review_index_path: ReviewIndex.md临时文件的绝对路径
            draft_paths: 任务文件临时路径列表（按任务顺序）
            initiator: 发起审查的客户端名称（如ClaudeCode）
            reviewer: 审阅工具名称（如iFlow）

        Returns:
            (review_index_file, task_files): 会话目录中的文件路径

        Raises:
            FileNotFoundError: 临时文件未找到
            UnicodeDecodeError: 文件编码无法检测
            ValueError: 文件名格式不正确
        """
        # 1. 读取ReviewIndex.md
        review_text = EncodingDetector.read_file(Path(review_index_path), support_bom=True)
        review_text = self._expand_placeholders(review_text, initiator=initiator, reviewer=reviewer)

        # 2. 写入ReviewIndex.md到会话目录
        review_file = self.session_dir / "ReviewIndex.md"
        review_file.write_text(review_text, encoding='utf-8')

        # 3. 处理每个任务文件
        task_files = []
        temp_files_to_delete = [Path(review_index_path)]

        try:
            for temp_path in draft_paths:
                temp_path_obj = Path(temp_path)
                temp_files_to_delete.append(temp_path_obj)

                # 3.1 提取目标文件名
                target_filename = self._extract_target_filename(temp_path_obj.name)

                # 3.2 验证文件名格式
                self._validate_task_filename(target_filename)

                # 3.3 读取任务文件
                task_text = EncodingDetector.read_file(temp_path_obj, support_bom=True)

                # 3.4 写入会话目录
                task_file = self.session_dir / target_filename
                task_file.write_text(task_text, encoding='utf-8')
                task_files.append(task_file)

        finally:
            # 4. 清理所有临时文件（即使出错也要执行）
            for temp_file in temp_files_to_delete:
                temp_file.unlink(missing_ok=True)

        return review_file, task_files

    def _extract_target_filename(self, temp_filename: str) -> str:
        """从临时文件名提取目标文件名。

        Args:
            temp_filename: 临时文件名，如 "Task1_LoginUpgrade-abc123.md"

        Returns:
            目标文件名，如 "Task1_LoginUpgrade.md"

        Raises:
            ValueError: 文件名格式不正确
        """
        if not temp_filename.endswith('.md'):
            raise ValueError(f"Invalid file extension: {temp_filename}")

        # 去掉.md后缀，split最后一个"-"
        name_without_ext = temp_filename[:-3]
        parts = name_without_ext.rsplit('-', 1)

        if len(parts) != 2:
            raise ValueError(
                f"Invalid temp filename format: {temp_filename}. "
                f"Expected format: {{TargetName}}-{{Random}}.md"
            )

        return parts[0] + '.md'

    def _validate_task_filename(self, filename: str) -> None:
        """验证任务文件名格式。

        Args:
            filename: 任务文件名，如 "Task1_LoginUpgrade.md"

        Raises:
            ValueError: 文件名格式不正确
        """
        # 格式：Task{N}_{Description}.md
        # Description只能包含字母、数字、下划线，不允许"-"
        pattern = r'^Task\d+_[A-Za-z0-9_]+\.md$'

        if not re.match(pattern, filename):
            raise ValueError(
                f"Invalid task filename: {filename}. "
                f"Expected format: Task{{N}}_{{Description}}.md "
                f"(Description can only contain letters, numbers, and underscores)"
            )

        # 检查路径遍历攻击
        if '..' in filename or '/' in filename or '\\' in filename:
            raise ValueError(f"Invalid characters in filename: {filename}")

        # 长度检查
        if len(filename) > 255:
            raise ValueError(f"Filename too long: {filename}")

