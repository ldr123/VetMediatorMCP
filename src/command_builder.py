"""命令构建器：根据配置生成CLI命令 | Command Builder: Generate CLI commands from configuration"""

import logging
from pathlib import Path
from typing import Dict, Any, List

try:
    from .cli_config import BUILTIN_PROMPT
except ImportError:
    from cli_config import BUILTIN_PROMPT

logger = logging.getLogger(__name__)


class CommandBuilder:
    """根据配置构建CLI命令的工具类 | Utility class for building CLI commands from configuration"""

    def __init__(self, config: Dict[str, Any]):
        """初始化命令构建器 | Initialize command builder

        Args:
            config: CLI配置字典（从cli_config.get_current_config获取）
                    CLI configuration dict (from cli_config.get_current_config)
        """
        self.config = config

    def build_review_command_args(self, session_rel_path: str, project_root: str) -> List[str]:
        """构建审查命令参数列表（用于subprocess执行）
        Build CLI command arguments list for subprocess execution.

        Args:
            session_rel_path: session目录相对于项目根的路径
                            Session directory path relative to project root
            project_root: 项目根目录路径
                         Project root directory path

        Returns:
            完整的命令参数列表: [executable, *args, prompt]
            Complete command arguments list: [executable, *args, prompt]
        """
        executable = self.config.get("executable", "")
        args = self.config.get("args", [])[:]

        prompt = BUILTIN_PROMPT.format(session_rel_path=session_rel_path, PROJECT_ROOT=project_root)

        extended_prompt = self.config.get("extended_prompt", "").strip()
        if extended_prompt:
            prompt = f"{prompt}\n\nIMPORTANT: {extended_prompt}"
            logger.debug(f"Using extended prompt for {executable}: {extended_prompt[:50]}...")

        return [executable] + args + [prompt]

    def build_review_command_string(self, session_rel_path: str, project_root: str) -> str:
        """构建命令字符串（仅用于日志显示）
        Build command string (for logging only)

        Args:
            session_rel_path: session目录相对于项目根的路径
                            Session directory path relative to project root
            project_root: 项目根目录路径
                         Project root directory path

        Returns:
            命令字符串 | Command string
        """
        args = self.build_review_command_args(session_rel_path, project_root)
        return ' '.join(args)

    def get_version_check_args(self) -> List[str]:
        """获取版本检查参数列表 | Get version check arguments list

        Returns:
            版本检查参数列表（如["iflow", "--version"]）
            Version check arguments list (e.g., ["iflow", "--version"])
        """
        executable = self.config.get("executable", "")
        return [executable, "--version"]

    def get_env_vars(self) -> Dict[str, str]:
        """获取环境变量 | Get environment variables

        Returns:
            环境变量字典（会合并到os.environ）
            Environment variables dict (will be merged into os.environ)
        """
        return self.config.get("env_vars", {})

    def get_display_name(self) -> str:
        """从executable提取显示名称 | Extract display name from executable

        Returns:
            显示名称（basename，无扩展名）
            Display name (basename without extension)

        Example:
            >>> config = {"executable": "iflow"}
            >>> CommandBuilder(config).get_display_name()
            'iflow'

            >>> config = {"executable": "/usr/bin/iflow"}
            >>> CommandBuilder(config).get_display_name()
            'iflow'

            >>> config = {"executable": "C:\\Program Files\\iflow.exe"}
            >>> CommandBuilder(config).get_display_name()
            'iflow'
        """
        executable = self.config.get("executable", "unknown")
        return Path(executable).stem

    def get_log_file_name(self) -> str:
        """获取日志文件名 | Get log file name

        Returns:
            日志文件名（如"iflow.log"）
            Log file name (e.g., "iflow.log")
        """
        return self.config.get("log_file_name", "cli.log")

    def check_prompt_length(self, prompt: str) -> bool:
        """检查prompt长度是否超过阈值 | Check if prompt length exceeds threshold

        Args:
            prompt: 要检查的prompt字符串 | Prompt string to check

        Returns:
            True表示超过阈值（需要警告），False表示在合理范围内
            True if exceeds threshold (warning needed), False if within reasonable range
        """
        max_length = self.config.get("max_prompt_length", 800)
        actual_length = len(prompt)

        if actual_length > max_length:
            logger.warning(
                f"[CommandBuilder] Prompt length ({actual_length}) exceeds "
                f"recommended limit ({max_length})"
            )
            return True

        return False
