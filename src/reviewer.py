"""CLI工具审查器核心逻辑：监控CLI进程并检查终止条件。| CLI Tool Reviewer Core Logic: Monitor CLI process and check termination conditions."""

import time
import asyncio
import subprocess
import sys
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any

# 配置logging输出到stderr（不影响MCP的stdout JSON通信）| Configure logging output to stderr (does not affect MCP stdout JSON communication)
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# 导入GUI工具和编码工具 | Import GUI utils and encoding utils
try:
    from .gui_utils import check_gui_available
    from .encoding_utils import EncodingDetector
    from .data_models import ReviewResult
    from .cli_config import get_current_config, load_config, update_current_cli_tool, get_default_config, get_user_config_path, create_config_file
    from .command_builder import CommandBuilder
except ImportError:
    from gui_utils import check_gui_available
    from encoding_utils import EncodingDetector
    from data_models import ReviewResult
    from cli_config import get_current_config, load_config, update_current_cli_tool, get_default_config, get_user_config_path, create_config_file
    from command_builder import CommandBuilder


class CliReviewer:
    """监控CLI工具审查进程，检查终止条件，返回审查结果 | Monitor CLI tool review process, check termination conditions, return review result"""

    # Timeout constants (seconds)
    CLI_VERSION_CHECK_TIMEOUT = 30
    UI_STARTUP_CHECK_DELAY = 0.5
    PROCESS_TERMINATION_TIMEOUT = 3
    UI_TERMINATION_TIMEOUT = 2
    REPORT_DETECTION_WAIT_TIME = 10
    MAIN_LOOP_POLL_INTERVAL = 1
    LOG_TASK_CLEANUP_TIMEOUT = 5

    # File I/O constants
    LOG_FILE_LINE_BUFFERING = 1
    REPORT_MIN_SIZE_BYTES = 100

    def __init__(self):
        """初始化审查器 | Initialize reviewer"""
        pass

    def _check_cli_installed(self, version_check_args: list, display_name: str) -> tuple[bool, str]:
        """检查CLI工具是否已安装并可用 | Check if CLI tool is installed and available

        Args:
            version_check_args: 版本检查参数列表（如["codex", "--version"]）| Version check arguments list (e.g., ["codex", "--version"])
            display_name: 工具显示名称（用于错误提示和日志）| Tool display name (for error messages and logs)

        Returns:
            (is_available, info_or_error):
            - True表示工具可用（包含版本检查成功或超时但可继续）| True if tool is available (version check success or timeout but can continue)
            - False表示工具不可用（未安装或执行失败）| False if tool is unavailable (not installed or execution failed)
            - info_or_error包含版本信息、警告或错误信息 | info_or_error contains version info, warnings or error messages

        说明 | Notes:
            - 成功：返回(True, version_string) | Success: return (True, version_string)
            - 超时：返回(True, warning_message) - 工具存在但版本检查超时，允许继续审查 | Timeout: return (True, warning_message) - tool exists but version check timed out, allow review to continue
            - 未安装：返回(False, error_message) - 工具不存在，必须修复 | Not installed: return (False, error_message) - tool doesn't exist, must fix
            - 其他错误：返回(False, error_message) - 执行失败，需要用户检查 | Other errors: return (False, error_message) - execution failed, user needs to check
        """
        logger.debug(f"[MCP] Checking {display_name} availability: {' '.join(version_check_args)}")

        try:
            # 在Windows上使用shell=True以支持.cmd/.bat文件 | Use shell=True on Windows to support .cmd/.bat files
            # npm安装的CLI工具在Windows上通常是.cmd批处理文件 | npm-installed CLI tools on Windows are usually .cmd batch files
            is_windows = sys.platform == 'win32'

            result = subprocess.run(
                version_check_args,
                capture_output=True,
                text=True,
                timeout=5,  # 5秒超时，避免长时间等待或交互式提示 | 5s timeout to avoid long wait or interactive prompts
                shell=is_windows,
                stdin=subprocess.DEVNULL  # 关闭stdin，防止CLI工具等待输入 | Close stdin to prevent CLI tool waiting for input
            )

            if result.returncode == 0:
                # 成功：工具存在且版本检查通过 | Success: tool exists and version check passed
                version = result.stdout.strip() or result.stderr.strip()
                logger.info(f"[MCP] {display_name} version: {version}")
                return True, version
            else:
                # 命令执行失败：工具存在但返回了错误码 | Command execution failed: tool exists but returned error code
                stderr = result.stderr.strip()
                logger.warning(f"[MCP] {display_name} command failed (returncode={result.returncode}): {stderr[:100]}")
                return False, f"{display_name} command failed: {stderr}"

        except subprocess.TimeoutExpired:
            # 超时：进程已启动（工具存在）但5秒内未完成 | Timeout: process started (tool exists) but didn't complete within 5s
            # 可能原因：等待用户输入、网络请求、性能问题 | Possible reasons: waiting for user input, network requests, performance issues
            # 策略：允许继续审查（跳过版本验证）| Strategy: allow review to continue (skip version verification)
            logger.warning(f"[MCP] {display_name} version check timed out after 5s, skipping version verification")
            return True, "[WARNING] Version check timed out, continuing without version verification"

        except FileNotFoundError:
            # 未找到：工具未安装或不在PATH中 | Not found: tool not installed or not in PATH
            logger.error(f"[MCP] {display_name} CLI not found in PATH")
            return False, f"{display_name} CLI not found. Please install it first."

        except Exception as e:
            # 其他异常：权限问题、系统错误等 | Other exceptions: permission issues, system errors, etc.
            logger.error(f"[MCP] Unexpected error checking {display_name}: {type(e).__name__}: {str(e)}")
            return False, f"Error checking {display_name}: {str(e)}"

    async def _launch_cli_check_ui(
        self,
        project_root: Path,
        current_tool: str,
        error_detail: str
    ) -> int:
        """启动CLI工具检查UI（GUI模式）| Launch CLI tool check UI (GUI mode)

        Args:
            project_root: 项目根目录路径 | Project root directory path
            current_tool: 当前失败的CLI工具名 | Current failed CLI tool name
            error_detail: 错误详情 | Error details

        Returns:
            100: 用户选择重试或激活新工具 | User chose to retry or activate new tool
            1: 用户选择取消 | User chose to cancel
            其他: UI启动失败（降级处理）| Other: UI launch failed (fallback handling)
        """
        script_dir = Path(__file__).parent
        ui_script = script_dir / "cli_check_ui.py"

        if not ui_script.exists():
            logger.warning(f"[MCP] CLI check UI script not found: {ui_script}")
            return 1

        logger.info(f"[MCP] Launching CLI check UI for {current_tool}")

        ui_cmd_args = [
            sys.executable,
            "-m",  # 使用模块方式运行 | Run as module
            "src.cli_check_ui",  # 模块路径 | Module path
            "--project-root", str(project_root),
            "--current-tool", current_tool,
            "--error-detail", error_detail,
        ]

        try:
            ui_process = await asyncio.create_subprocess_exec(
                *ui_cmd_args,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(project_root)  # 设置工作目录 | Set working directory
            )

            await ui_process.wait()
            logger.info(f"[MCP] CLI check UI exited with code: {ui_process.returncode}")

            return ui_process.returncode

        except Exception as e:
            logger.error(f"[MCP] Failed to launch CLI check UI: {e}")
            return 1

    async def _terminal_cli_check(
        self,
        tool_name: str,
        executable: str,
        version_args: list,
        install_cmd: str,
        error_detail: str
    ) -> bool:
        """终端交互式CLI工具检查（Headless环境）| Terminal interactive CLI tool check (Headless environment)

        Args:
            tool_name: 工具显示名称 | Tool display name
            executable: 可执行文件名 | Executable file name
            version_args: 版本检查参数列表 | Version check arguments list
            install_cmd: 安装命令建议 | Installation command suggestion
            error_detail: 错误详情 | Error details

        Returns:
            True: 用户选择重试 | User chose to retry
            False: 用户选择取消 | User chose to cancel
        """
        version_cmd = f"{executable} {' '.join(version_args)}"

        error_msg = f"""
{'='*70}
[ERROR] {tool_name} CLI Tool Not Found
{'='*70}

Attempted to execute: {version_cmd}
Error details: {error_detail}

Possible causes:
  - {tool_name} is not installed
  - PATH environment variable is not configured
  - Configuration in .VetMediatorSetting.json is incorrect
"""

        if install_cmd:
            error_msg += f"""
Recommended installation command:
  {install_cmd}
"""

        error_msg += f"""
Please select an action:
  r - Retry check (after fixing the issue)
  c - Cancel review
{'='*70}
"""

        print(error_msg, file=sys.stderr, flush=True)

        loop = asyncio.get_event_loop()
        try:
            choice = await loop.run_in_executor(
                None,
                lambda: input("Enter your choice (r/c): ").strip().lower()
            )

            logger.info(f"[MCP] User choice in terminal: {choice}")
            return choice == 'r'

        except Exception as e:
            logger.error(f"[MCP] Failed to read user input: {e}")
            return False

    def _reload_and_check_cli(
        self,
        project_root_path: Path,
        version_check_args: list
    ) -> tuple[bool, str, str]:
        """重新加载配置并检查CLI工具 | Reload configuration and check CLI tool

        Args:
            project_root_path: 项目根目录路径 | Project root directory path
            version_check_args: 当前的版本检查参数（用于提取version_args）| Current version check arguments (for extracting version_args)

        Returns:
            (is_installed, version_or_error, current_cli_tool):
            - is_installed: CLI是否安装 | Whether CLI is installed
            - version_or_error: 版本信息或错误详情 | Version info or error details
            - current_cli_tool: 更新后的当前CLI工具名 | Updated current CLI tool name

        Raises:
            ValueError: 配置验证错误 | Configuration validation error
            json.JSONDecodeError: JSON格式错误 | JSON format error
            KeyError: 配置缺少必需字段 | Configuration missing required fields

        Side effects:
            更新self.command_builder, self.display_name, self.log_file_name | Updates self.command_builder, self.display_name, self.log_file_name
        """
        config = get_current_config(project_root_path)
        self.command_builder = CommandBuilder(config)
        self.display_name = self.command_builder.get_display_name()
        self.log_file_name = config["log_file_name"]
        current_cli_tool = load_config(project_root_path).get("current_cli_tool", "iflow")

        version_check_args = self.command_builder.get_version_check_args()

        is_installed, version_or_error = self._check_cli_installed(
            version_check_args,
            self.display_name
        )

        return is_installed, version_or_error, current_cli_tool

    def _handle_config_error(
        self,
        e: Exception,
        report_path: Path,
        project_root_path: Path,
        is_terminal: bool = False
    ) -> ReviewResult:
        """处理配置错误并生成错误报告 | Handle configuration error and generate error report

        Args:
            e: 异常对象（ValueError或其他）| Exception object (ValueError or other)
            report_path: 报告文件路径 | Report file path
            project_root_path: 项目根目录路径 | Project root directory path
            is_terminal: 是否为终端模式（需要额外输出到stderr）| Whether in terminal mode (needs additional output to stderr)

        Returns:
            ReviewResult: 失败的审查结果 | Failed review result
        """
        if isinstance(e, ValueError):
            error_type = "Configuration Validation Error"
            summary_detail = "has validation errors"
        else:
            error_type = "Configuration Error"
            summary_detail = "has errors"

        logger.error(f"[MCP] {error_type}: {e}")

        if is_terminal:
            print(f"\n[ERROR] {error_type}: {e}", file=sys.stderr)
            print("Please fix the configuration file and restart the review.", file=sys.stderr)

        error_report = f"""# Review Report

## Status
error

## Error Message
Configuration Error: {str(e)}

## Summary
The configuration file (.VetMediatorSetting.json) {summary_detail}. Please check the file format and fix the issues.

Error details:
- {str(e)}

Configuration file locations (in priority order):
1. {project_root_path}/.VetMediatorSetting.json
2. ~/.VetMediatorSetting.json

Please refer to .VetMediatorSetting.json.example for correct format.
"""
        report_path.write_text(error_report, encoding='utf-8')

        return ReviewResult(
            status="failed",
            report_content=error_report,
            log_tail=str(e),
            execution_time=0,
            session_dir=None
        )

    def _generate_cli_not_found_report(
        self,
        report_path: Path,
        display_name: str,
        version_or_error: str,
        install_cmd: str = ""
    ) -> str:
        """生成CLI未找到错误报告 | Generate CLI not found error report

        Args:
            report_path: 报告文件路径 | Report file path
            display_name: CLI工具显示名称 | CLI tool display name
            version_or_error: 错误详情 | Error details
            install_cmd: 安装命令建议 | Installation command suggestion

        Returns:
            str: 错误报告内容 | Error report content
        """
        error_report = f"""# Review Report

## Status
error

## Error Message
{display_name} CLI tool not found: {version_or_error}

## Summary
{display_name} CLI is not available. The review was cancelled by the user or failed after multiple retry attempts.

Please ensure {display_name} is installed and properly configured:
"""

        if install_cmd:
            error_report += f"""
Installation command:
  {install_cmd}
"""

        error_report += f"""
Configuration check:
  - Verify {display_name} is installed
  - Check PATH environment variable
  - Verify .VetMediatorSetting.json configuration
"""

        report_path.write_text(error_report, encoding='utf-8')
        return error_report

    async def _cleanup_process(self, process, timeout=5):
        """优雅地清理进程及其子进程 | Gracefully cleanup process and its subprocesses

        尝试terminate()优雅终止，等待timeout秒，如果失败则使用kill()强制终止。| Try terminate() for graceful termination, wait for timeout seconds, if failed then use kill() to force terminate.
        即使主进程已退出，也会尝试清理，因为子进程可能成为孤儿进程继续运行。| Even if main process exited, still try cleanup, because subprocesses may become orphans and continue running.

        Args:
            process: asyncio subprocess对象 | asyncio subprocess object
            timeout: terminate后等待的秒数 | Seconds to wait after terminate
        """
        if process is None:
            return  # 进程对象不存在 | Process object doesn't exist

        # 注意：不检查returncode，即使主进程已退出也尝试terminate/kill | Note: don't check returncode, attempt terminate/kill even if main process exited
        # 这是因为在Windows上，shell启动的子进程可能成为孤儿进程继续运行 | This is because on Windows, shell-launched subprocesses may become orphans and continue running

        try:
            # 尝试优雅终止 | Try graceful termination
            process.terminate()
            await asyncio.wait_for(process.wait(), timeout=timeout)
            logger.info(f"[MCP] Process {process.pid} terminated gracefully")
        except asyncio.TimeoutError:
            # terminate失败，强制kill | Terminate failed, force kill
            logger.warning(f"[MCP] Process {process.pid} did not terminate, killing")
            process.kill()
            try:
                await asyncio.wait_for(process.wait(), timeout=2)
                logger.info(f"[MCP] Process {process.pid} killed")
            except asyncio.TimeoutError:
                logger.error(f"[MCP] Failed to kill process {process.pid}")
        except ProcessLookupError:
            # 进程已不存在（可能已自然退出）| Process no longer exists (may have exited naturally)
            logger.info(f"[MCP] Process {process.pid} already exited")
        except ProcessLookupError:
            # 进程已不存在（可能已自然退出）| Process no longer exists (may have exited naturally)
            logger.info(f"[MCP] Process {process.pid} already exited")

    async def _capture_and_write_log(self, stdout: asyncio.StreamReader, log_path: Path):
        """Capture CLI tool stdout in real-time, detect encoding, write to UTF-8 log.

        This replaces shell redirection (>) to achieve 100% control over log encoding.
        Each line is decoded using smart encoding detection, then written as UTF-8.

        **IMPORTANT**: Log file is ALWAYS written in UTF-8 encoding (without BOM).
        This ensures consistent encoding across different platforms and CLI tools.

        Args:
            stdout: asyncio.StreamReader from subprocess
            log_path: Path to log file (will be created with UTF-8 encoding)
        """
        try:
            # IMPORTANT: Explicitly use UTF-8 encoding for log file
            # buffering=1 enables line buffering for real-time log viewing
            with open(log_path, 'w', encoding='utf-8', buffering=1) as f:
                while True:
                    # Read line as bytes
                    line_bytes = await stdout.readline()
                    if not line_bytes:
                        break  # EOF

                    # Smart decode (try UTF-8/GBK/GB18030)
                    text = EncodingDetector.decode_bytes(line_bytes)

                    # Write to UTF-8 log (no BOM)
                    f.write(text)
        except Exception as e:
            # Log capture failure should not crash the review workflow
            logger.error(f"[MCP] Log capture error: {str(e)}")

    async def start_review(
        self,
        session_dir: str,
        project_root: str
    ) -> ReviewResult:
        """启动CLI审查并监控进度（异步版本，实时日志流式处理）| Start CLI review and monitor progress (async version, real-time log streaming)

        Args:
            session_dir: Session目录路径 | Session directory path
            project_root: 项目根目录路径（CLI工具工作目录）| Project root directory path (CLI tool working directory)

        Returns:
            ReviewResult instance with review data
        """
        session_path = Path(session_dir)
        project_root_path = Path(project_root)

        # === 配置文件检查：确保至少存在一个配置文件 === | === Configuration file check: ensure at least one config file exists ===
        global_config_path = get_user_config_path()
        project_config_path = project_root_path / ".VetMediatorSetting.json"

        global_exists = global_config_path.exists()
        project_exists = project_config_path.exists()

        if not global_exists and not project_exists:
            logger.warning("[MCP] No configuration file found")

            # 检查GUI是否可用 | Check if GUI is available
            gui_available = check_gui_available()

            if gui_available:
                # GUI模式：启动配置检查UI | GUI mode: launch config check UI
                logger.info("[MCP] Launching config check UI...")

                script_dir = Path(__file__).parent
                ui_script = script_dir / "cli_config_check_ui.py"

                if not ui_script.exists():
                    logger.error(f"[MCP] Config check UI script not found: {ui_script}")
                    # Fallback: 创建项目配置 | Fallback: create project config
                    create_config_file(project_config_path)
                    error_report = self._generate_config_missing_report(
                        session_path / "report.md",
                        project_config_path
                    )
                    return ReviewResult(
                        status="failed",
                        report_content=error_report,
                        log_tail="Configuration file missing",
                        execution_time=0,
                        session_dir=session_dir
                    )

                ui_cmd_args = [
                    sys.executable,
                    "-m",  # 使用模块方式运行 | Run as module
                    "src.cli_config_check_ui",  # 模块路径 | Module path
                    "--project-root", str(project_root_path)
                ]

                try:
                    ui_process = await asyncio.create_subprocess_exec(
                        *ui_cmd_args,
                        stdin=asyncio.subprocess.DEVNULL,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        cwd=str(project_root_path)  # 设置工作目录 | Set working directory
                    )

                    await ui_process.wait()
                    logger.info(f"[MCP] Config check UI exited with code: {ui_process.returncode}")

                    if ui_process.returncode == 100:
                        # 用户创建了配置，继续执行（会重新加载配置）| User created config, continue (will reload config)
                        logger.info("[MCP] Configuration created, continuing...")
                    else:
                        # 用户取消 | User cancelled
                        logger.info("[MCP] User cancelled config creation")
                        error_report = self._generate_config_missing_report(
                            session_path / "report.md",
                            project_config_path
                        )
                        return ReviewResult(
                            status="failed",
                            report_content=error_report,
                            log_tail="User cancelled configuration",
                            execution_time=0,
                            session_dir=session_dir
                        )

                except Exception as e:
                    logger.error(f"[MCP] Failed to launch config check UI: {e}")
                    # Fallback: 创建项目配置 | Fallback: create project config
                    create_config_file(project_config_path)
                    error_report = self._generate_config_missing_report(
                        session_path / "report.md",
                        project_config_path
                    )
                    return ReviewResult(
                        status="failed",
                        report_content=error_report,
                        log_tail=f"Config check UI failed: {str(e)}",
                        execution_time=0,
                        session_dir=session_dir
                    )

            else:
                # Headless模式：创建项目配置并提示用户 | Headless mode: create project config and prompt user
                logger.info("[MCP] Headless mode: creating project config...")
                create_config_file(project_config_path)

                error_msg = (
                    f"\n{'='*70}\n"
                    "[ERROR] Configuration File Missing\n"
                    f"{'='*70}\n\n"
                    "No configuration file found. A default configuration has been created at:\n"
                    f"  {project_config_path}\n\n"
                    "Please edit this file to configure your CLI tool and restart the review.\n"
                    f"{'='*70}\n"
                )
                print(error_msg, file=sys.stderr, flush=True)

                error_report = self._generate_config_missing_report(
                    session_path / "report.md",
                    project_config_path
                )
                return ReviewResult(
                    status="failed",
                    report_content=error_report,
                    log_tail="Configuration file created, please edit and restart",
                    execution_time=0,
                    session_dir=session_dir
                )

        start_time = time.time()

        # [Modification 4]: 加载配置 | Load configuration
        try:
            config = get_current_config(project_root_path)
            self.command_builder = CommandBuilder(config)
            self.display_name = self.command_builder.get_display_name()
            self.log_file_name = config["log_file_name"]
        except ValueError as e:
            # 配置验证错误 - 快速失败（不应fallback）| Configuration validation error - fast fail (should not fallback)
            raise ValueError(f"Invalid configuration: {e}") from e
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            # 配置文件缺失或格式错误 - fallback到默认配置 | Config file missing or malformed - fallback to default config
            logger.warning(f"[MCP] Config file missing/malformed: {e}, using default (iflow)")
            default_config = get_default_config()
            config = default_config["cli_presets"]["iflow"]
            self.command_builder = CommandBuilder(config)
            self.display_name = "iflow"
            self.log_file_name = "iflow.log"

        # [Modification 5]: 日志文件名 | Log file name
        report_path = session_path / "report.md"
        log_path = session_path / self.log_file_name

        # [Modification 6]: 版本检查 | Version check
        version_check_args = self.command_builder.get_version_check_args()
        is_installed, version_or_error = self._check_cli_installed(
            version_check_args,
            self.display_name
        )

        if not is_installed:
            logger.warning(f"[MCP] {self.display_name} CLI tool not found: {version_or_error}")

            version_args_only = version_check_args[1:] if len(version_check_args) > 1 else ["--version"]
            current_cli_tool = load_config(project_root_path).get("current_cli_tool", "iflow")

            while True:
                gui_available = check_gui_available()

                if gui_available:
                    exit_code = await self._launch_cli_check_ui(
                        project_root=project_root_path,
                        current_tool=current_cli_tool,
                        error_detail=version_or_error
                    )

                    if exit_code == 100:
                        logger.info(f"[MCP] User requested retry, reloading configuration...")

                        try:
                            is_installed, version_or_error, current_cli_tool = self._reload_and_check_cli(
                                project_root_path,
                                version_check_args
                            )

                            if is_installed:
                                logger.info(f"[MCP] {self.display_name} CLI tool found: {version_or_error}")
                                break

                            logger.warning(f"[MCP] {self.display_name} still not found after retry")

                        except (ValueError, json.JSONDecodeError, KeyError) as e:
                            return self._handle_config_error(e, report_path, project_root_path, is_terminal=False)

                    else:
                        logger.info(f"[MCP] User cancelled (exit code: {exit_code})")
                        break

                else:
                    logger.info(f"[MCP] GUI not available, using terminal interaction")

                    install_cmd = config.get("install_command", "")
                    retry = await self._terminal_cli_check(
                        tool_name=self.display_name,
                        executable=config["executable"],
                        version_args=version_args_only,
                        install_cmd=install_cmd,
                        error_detail=version_or_error
                    )

                    if retry:
                        logger.info(f"[MCP] User requested retry in terminal, reloading configuration...")

                        try:
                            is_installed, version_or_error, current_cli_tool = self._reload_and_check_cli(
                                project_root_path,
                                version_check_args
                            )

                            if is_installed:
                                logger.info(f"[MCP] {self.display_name} CLI tool found: {version_or_error}")
                                break

                            logger.warning(f"[MCP] {self.display_name} still not found after retry")

                        except (ValueError, json.JSONDecodeError, KeyError) as e:
                            return self._handle_config_error(e, report_path, project_root_path, is_terminal=True)

                    else:
                        logger.info(f"[MCP] User cancelled in terminal")
                        break

            if not is_installed:
                install_cmd = config.get("install_command", "")
                error_report = self._generate_cli_not_found_report(
                    report_path,
                    self.display_name,
                    version_or_error,
                    install_cmd
                )

                return ReviewResult(
                    status="failed",
                    report_content=error_report,
                    log_tail=version_or_error,
                    execution_time=0,
                    session_dir=None
                )

        logger.info(f"[MCP] {self.display_name} version: {version_or_error}")

        try:
            # [Modification 7]: 环境变量 | Environment variables
            env = os.environ.copy()
            env_vars = self.command_builder.get_env_vars()
            env.update(env_vars)

            if env_vars:
                logger.info(f"[MCP] Setting env vars: {', '.join(env_vars.keys())}")

            # [Modification 8]: 计算session相对路径 | Calculate session relative path
            session_rel_path = session_path.relative_to(project_root_path)

            # [Modification 9]: 构建命令参数列表 | Build command arguments list
            # 使用as_posix()转换为Unix风格路径（正斜杠），避免Windows反斜杠在shell中被转义 | Use as_posix() to convert to Unix-style path (forward slash), avoid Windows backslash being escaped in shell
            cli_cmd_args = self.command_builder.build_review_command_args(session_rel_path.as_posix())

            # [Modification 10]: 检查prompt长度 | Check prompt length
            # 提取最后一个参数（prompt）| Extract last argument (prompt)
            if cli_cmd_args:
                prompt = cli_cmd_args[-1]
                if self.command_builder.check_prompt_length(prompt):
                    max_len = config.get('max_prompt_length', 800)
                    logger.warning(
                        f"[MCP] Prompt length ({len(prompt)} chars) exceeds recommended limit "
                        f"({max_len} chars). This may cause issues."
                    )

            # [Modification 11]: 日志输出（用字符串形式）| Log output (as string format)
            cli_cmd_str = self.command_builder.build_review_command_string(session_rel_path.as_posix())
            logger.info(f"[MCP] Executing {self.display_name} command: {cli_cmd_str}")

            # [Modification 12]: 在Windows上通过cmd.exe运行CLI工具 | Run CLI tool via cmd.exe on Windows
            # npm安装的CLI工具在Windows上通常是.cmd批处理文件 | npm-installed CLI tools on Windows are usually .cmd batch files
            # asyncio.create_subprocess_exec不能直接运行.cmd文件，必须通过cmd.exe调用 | asyncio.create_subprocess_exec cannot run .cmd files directly, must call via cmd.exe
            # cmd.exe可以处理.cmd/.bat/.exe等所有类型的可执行文件 | cmd.exe can handle all types of executables like .cmd/.bat/.exe
            is_windows = sys.platform == 'win32'
            if is_windows:
                cli_cmd_args = ['cmd.exe', '/c'] + cli_cmd_args
                logger.debug(f"[MCP] Running via cmd.exe on Windows")

            # [Modification 13]: 启动进程（使用subprocess_exec）| Start process (using subprocess_exec)
            process = await asyncio.create_subprocess_exec(
                *cli_cmd_args,  # 解包参数列表 | Unpack arguments list
                cwd=str(project_root_path),
                stdin=asyncio.subprocess.DEVNULL,  # 关闭stdin，防止CLI工具等待输入 | Close stdin to prevent CLI tool waiting for input
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=env
            )

            logger.info(f"[MCP] {self.display_name} process started with PID {process.pid}")

            # === 启动日志捕获任务（后台异步运行）=== | === Start log capture task (async background) ===
            # 实时读取 CLI工具 stdout，智能检测编码，写入 UTF-8 日志 | Real-time read CLI tool stdout, smart encoding detection, write UTF-8 log
            log_task = asyncio.create_task(
                self._capture_and_write_log(process.stdout, log_path)
            )
            logger.info(f"[MCP] Log capture task started, writing to {log_path}")

            # === 启动CLI进程后，检查并启动监控UI === | === After starting CLI process, check and start monitor UI ===
            ui_process = None

            # 检查GUI环境是否可用 | Check if GUI environment is available
            logger.info("[MCP] Checking GUI availability...")
            gui_available = check_gui_available()
            logger.info(f"[MCP] GUI available: {gui_available}")

            if gui_available:
                try:
                    # 构建UI脚本路径 | Build UI script path
                    script_dir = Path(__file__).parent
                    ui_script = script_dir / "cli_monitor_ui.py"

                    logger.info(f"[MCP] UI script path: {ui_script}")
                    logger.info(f"[MCP] UI script exists: {ui_script.exists()}")

                    if not ui_script.exists():
                        logger.warning(f"[MCP] UI script not found at {ui_script}, skipping GUI")
                    else:
                        logger.info(f"[MCP] Launching GUI with Python: {sys.executable}")
                        logger.info(f"[MCP] Log path: {log_path}")

                        # 收集session目录中的所有审查文件 | Collect all review files in session directory
                        review_files = []

                        # 1. 添加ReviewIndex.md | Add ReviewIndex.md
                        review_index = session_path / "ReviewIndex.md"
                        if review_index.exists():
                            review_files.append(str(review_index))

                        # 2. 添加所有Task*.md文件（按文件名排序）| Add all Task*.md files (sorted by filename)
                        task_files = sorted(session_path.glob("Task*.md"))
                        review_files.extend([str(f) for f in task_files])

                        logger.info(f"[MCP] Found {len(review_files)} review files for GUI")

                        # 构建GUI启动参数（使用-m模块方式避免相对导入问题）| Build GUI launch arguments (use -m module mode to avoid relative import issues)
                        ui_cmd_args = [
                            sys.executable,  # Python解释器路径 | Python interpreter path
                            "-m",  # 使用模块方式运行 | Run as module
                            "src.cli_monitor_ui",  # 模块路径 | Module path
                            "--log-path", str(log_path),
                            "--tool-name", self.display_name,
                        ]

                        # 添加所有文件路径 | Add all file paths
                        for file_path in review_files:
                            ui_cmd_args.extend(["--file-path", file_path])

                        # 启动UI子进程（设置工作目录为项目根目录）| Start UI subprocess (set working directory to project root)
                        ui_process = await asyncio.create_subprocess_exec(
                            *ui_cmd_args,
                            stdin=asyncio.subprocess.DEVNULL,  # 避免继承父进程stdin | Avoid inheriting parent process stdin
                            stdout=asyncio.subprocess.PIPE,  # 捕获输出用于调试 | Capture output for debugging
                            stderr=asyncio.subprocess.PIPE,
                            cwd=str(project_root_path)  # 设置工作目录为项目根目录 | Set working directory to project root
                        )

                        # 等待一小段时间，检查UI是否成功启动 | Wait a short time to check if UI started successfully
                        await asyncio.sleep(0.5)

                        if ui_process.returncode is not None:
                            # UI进程已经退出（启动失败）| UI process already exited (startup failed)
                            stdout, stderr = await ui_process.communicate()
                            logger.error(f"[MCP] GUI failed to start (exit code: {ui_process.returncode})")
                            logger.error(f"[MCP] GUI stdout: {stdout.decode('utf-8', errors='replace')}")
                            logger.error(f"[MCP] GUI stderr: {stderr.decode('utf-8', errors='replace')}")
                            ui_process = None
                        else:
                            logger.info(f"[MCP] GUI started successfully (PID: {ui_process.pid})")

                except Exception as e:
                    # UI启动失败不影响主流程，继续执行 | UI startup failure doesn't affect main flow, continue execution
                    logger.error(f"[MCP] Exception while launching GUI: {type(e).__name__}: {str(e)}")
                    import traceback
                    logger.error(f"[MCP] Traceback: {traceback.format_exc()}")
            else:
                logger.info("[MCP] GUI not available, running in headless mode")

            # 主监控循环：等待进程退出或超时/UI中止 | Main monitor loop: wait for process exit or timeout/UI abort
            start_time = time.monotonic()
            report_detected_time = None  # 首次检测到report.md的时间戳 | Timestamp when report.md first detected

            # 智能超时：监控log文件活跃度 | Smart timeout: monitor log file activity
            last_log_mtime = 0  # 上次log文件修改时间 | Last log file modification time
            last_activity_time = start_time  # 上次有活跃的时间 | Last activity time
            IDLE_TIMEOUT = 300  # 无响应超时：5分钟无新输出就终止 | Idle timeout: terminate after 5 minutes with no new output

            try:
                while True:
                    # ========================================
                    # 检查1：UI进程状态（最高优先级）| Check 1: UI process status (highest priority)
                    # ========================================
                    if ui_process and ui_process.returncode is not None:
                        # UI进程已退出 | UI process exited
                        if ui_process.returncode == 99:
                            # 退出码99：用户主动中止审查 | Exit code 99: user actively aborted review
                            # 终止CLI进程 | Terminate CLI process
                            if process.returncode is None:
                                await self._cleanup_process(process, timeout=2)

                            # 生成中止报告 | Generate abort report
                            self._generate_error_report(
                                report_path,
                                status="error",
                                error_message="User aborted the review",
                                summary="The review was manually cancelled by the user through the monitor UI."
                            )

                            return ReviewResult(
                                status="failed",
                                report_content=self._read_report(report_path),
                                log_tail=self._read_log_tail(log_path, 10),
                                execution_time=int(time.time() - start_time),
                                session_dir=session_dir
                            )
                        else:
                            # 其他退出码：UI意外崩溃 | Other exit codes: UI crashed unexpectedly
                            # 不中止审查，继续等待CLI完成 | Don't abort review, continue waiting for CLI to complete
                            ui_process = None  # 清空引用，不再检查 | Clear reference, no longer check

                    # ========================================
                    # 检查2：智能超时（基于log文件活跃度）| Check 2: Smart timeout (based on log file activity)
                    # ========================================
                    elapsed = time.monotonic() - start_time

                    # 检查log文件活跃度 | Check log file activity
                    try:
                        if log_path.exists():
                            current_log_mtime = log_path.stat().st_mtime
                            if current_log_mtime > last_log_mtime:
                                # log文件有更新，重置活跃时间 | Log file updated, reset activity time
                                last_log_mtime = current_log_mtime
                                last_activity_time = time.monotonic()
                                logger.debug(f"[MCP] Log file updated, reset activity timer")
                    except Exception as e:
                        logger.debug(f"[MCP] Failed to check log file: {e}")

                    # 计算无响应时长 | Calculate idle duration
                    idle_time = time.monotonic() - last_activity_time

                    # 检查无响应超时（5分钟无新输出）| Check idle timeout (5 minutes with no new output)
                    if idle_time > IDLE_TIMEOUT:
                        # CLI工具无响应超过5分钟，终止进程 | CLI tool no response for over 5 minutes, terminate process
                        await self._cleanup_process(process, timeout=2)
                        if ui_process and ui_process.returncode is None:
                            ui_process.kill()

                        await process.wait()

                        # 生成超时报告 | Generate timeout report
                        self._generate_error_report(
                            report_path,
                            status="timeout",
                            error_message=f"CLI tool has no response for {int(idle_time)} seconds (idle timeout: {IDLE_TIMEOUT}s)",
                            summary=f"The {self.display_name} review was terminated due to no output for {int(idle_time)} seconds. The CLI tool may be stuck or waiting for input."
                        )

                        return ReviewResult(
                            status="timeout",
                            report_content=self._read_report(report_path),
                            log_tail=self._read_log_tail(log_path, 10),
                            execution_time=int(elapsed),
                            session_dir=session_dir
                        )

                    # ========================================
                    # 检查3：report.md保底方案（10秒强制终止）| Check 3: report.md fallback (10s force terminate)
                    # ========================================
                    # 如果report.md已生成且CLI进程未退出，等待10秒后强制终止 | If report.md generated and CLI process not exited, force terminate after 10s
                    # 要求文件至少100字节（避免误判空文件）| Require file at least 100 bytes (avoid false positive empty files)
                    if report_path.exists() and report_path.stat().st_size > 100:
                        if report_detected_time is None:
                            # 首次检测到report.md | First detected report.md
                            report_detected_time = time.monotonic()
                            logger.info(f"[MCP] report.md detected ({report_path.stat().st_size} bytes), starting 10-second countdown")
                        else:
                            # 检查是否已等待超过10秒 | Check if waited for more than 10s
                            report_wait_time = time.monotonic() - report_detected_time
                            if report_wait_time > 10:
                                # 超过10秒，先关闭UI（让用户有足够时间查看日志）| Over 10s, close UI first (give user enough time to view log)
                                logger.info("[MCP] 10 seconds elapsed since report.md detected, closing UI")
                                if ui_process and ui_process.returncode is None:
                                    ui_process.kill()
                                    try:
                                        await asyncio.wait_for(ui_process.wait(), timeout=2)
                                    except asyncio.TimeoutError:
                                        pass

                                # 然后检测CLI进程是否还在运行 | Then check if CLI process still running
                                if process.returncode is None:
                                    logger.info(f"[MCP] {self.display_name} process still running, force-terminating")
                                    await self._cleanup_process(process, timeout=2)
                                else:
                                    logger.info(f"[MCP] {self.display_name} process already exited")

                                # 跳出循环，进入正常结果读取流程 | Break loop, enter normal result reading flow
                                break

                    # ========================================
                    # 检查4：等待进程退出（1秒超时）| Check 4: Wait for process exit (1s timeout)
                    # ========================================
                    try:
                        await asyncio.wait_for(process.wait(), timeout=1)
                        # 进程已退出，跳出循环 | Process exited, break loop
                        break
                    except asyncio.TimeoutError:
                        # 进程还在运行，继续循环 | Process still running, continue loop
                        continue

            finally:
                # 清理CLI进程（确保所有退出路径都清理进程）| Cleanup CLI process (ensure all exit paths cleanup process)
                await self._cleanup_process(process, timeout=3)

                # 清理UI进程 | Cleanup UI process
                if ui_process and ui_process.returncode is None:
                    ui_process.kill()
                    try:
                        await asyncio.wait_for(ui_process.wait(), timeout=2)
                    except asyncio.TimeoutError:
                        pass

                # 等待日志捕获任务完成（读取剩余的 stdout）| Wait for log capture task to complete (read remaining stdout)
                try:
                    await asyncio.wait_for(log_task, timeout=5)
                    logger.info("[MCP] Log capture task completed")
                except asyncio.TimeoutError:
                    logger.warning("[MCP] Log capture task timeout, cancelling")
                    log_task.cancel()
                    try:
                        await log_task
                    except asyncio.CancelledError:
                        pass
                except Exception as e:
                    logger.error(f"[MCP] Log capture task error: {str(e)}")

            # 进程已退出，读取结果 | Process exited, read results
            # 场景判断：| Scenario determination:
            # 场景1：report.md存在 + 有结束标记 → completed | Scenario 1: report.md exists + has completion marker → completed
            # 场景2：report.md存在 + 无结束标记 → incomplete | Scenario 2: report.md exists + no completion marker → incomplete
            # 场景3：report.md不存在 → failed（生成错误报告）| Scenario 3: report.md doesn't exist → failed (generate error report)

            # 场景3：检查report.md是否存在 | Scenario 3: Check if report.md exists
            if not report_path.exists() or report_path.stat().st_size == 0:
                self._generate_error_report(
                    report_path,
                    status="error",
                    error_message=f"{self.display_name} process exited without generating report (exit code {process.returncode})",
                    summary=f"The {self.display_name} review process terminated unexpectedly. Check {self.log_file_name} for details."
                )
                return ReviewResult(
                    status="failed",
                    report_content=self._read_report(report_path),
                    log_tail=self._read_log_tail(log_path, 10),
                    execution_time=int(time.time() - start_time),
                    session_dir=session_dir
                )

            # 场景1 & 2：report.md存在，读取内容并检查完整性 | Scenario 1 & 2: report.md exists, read content and check integrity
            report_content = self._read_report(report_path)

            # 检查报告完整性标记 | Check report completion marker
            has_completion_marker = ("<!-- REVIEW_COMPLETE -->" in report_content or
                                     "---END_OF_REVIEW---" in report_content)

            if not has_completion_marker:
                # 场景2：报告不完整（流式写入中断）| Scenario 2: Report incomplete (streaming write interrupted)
                logger.warning(f"[MCP] Report is incomplete (missing completion marker)")
                return ReviewResult(
                    status="incomplete",
                    report_content=report_content,
                    log_tail=self._read_log_tail(log_path, 10),
                    execution_time=int(time.time() - start_time),
                    session_dir=session_dir
                )

            # 场景1：报告完整 | Scenario 1: Report complete
            return ReviewResult(
                status="completed",
                report_content=report_content,
                log_tail=self._read_log_tail(log_path, 10),
                execution_time=int(time.time() - start_time),
                session_dir=session_dir
            )

        except Exception as e:

            # 生成异常报告 | Generate exception report
            exception_report = f"""# Review Report

## Status
error

## Error Message
{str(e)}

## Summary
An unexpected error occurred during the review process.
"""
            report_path.write_text(exception_report, encoding='utf-8')

            return ReviewResult(
                status="failed",
                report_content=exception_report,
                log_tail=f"Error: {str(e)}",
                execution_time=int(time.time() - start_time),
                session_dir=session_dir
            )

    def _get_log_line_count(self, log_path: Path) -> int:
        """Get log file line count"""
        if not log_path.exists():
            return 0
        try:
            content = EncodingDetector.read_file(log_path)
            return content.count('\n') + 1
        except:
            return 0

    def _read_log_tail(self, log_path: Path, lines: int) -> str:
        """Read last N lines of log file"""
        if not log_path.exists():
            return ""
        try:
            content = EncodingDetector.read_file(log_path)
            all_lines = content.splitlines()
            return "\n".join(all_lines[-lines:])
        except:
            return ""

    def _read_report(self, report_path: Path) -> str:
        """Read report.md content"""
        if not report_path.exists():
            return ""
        try:
            return EncodingDetector.read_file(report_path)
        except UnicodeDecodeError as e:
            return f"[ENCODING ERROR] Cannot read report.md: {str(e)}"

    def _generate_error_report(
        self,
        report_path: Path,
        status: str,
        error_message: str,
        summary: str
    ):
        """生成并写入错误报告 | Generate and write error report

        Args:
            report_path: report.md文件路径 | report.md file path
            status: 状态（error/timeout等）| Status (error/timeout, etc.)
            error_message: 错误消息 | Error message
            summary: 摘要说明 | Summary description
        """
        content = f"""# Review Report

## Status
{status}

## Error Message
{error_message}

## Summary
{summary}
"""
        report_path.write_text(content, encoding='utf-8')

    async def _terminate_process(
        self,
        process,
        timeout: int = None,
        process_name: str = "process"
    ):
        """优雅终止异步进程 | Gracefully terminate async process

        Args:
            process: 异步进程对象 | Async process object
            timeout: 等待超时（秒），默认使用PROCESS_TERMINATION_TIMEOUT | Wait timeout (seconds), default uses PROCESS_TERMINATION_TIMEOUT
            process_name: 进程名称（用于日志）| Process name (for logging)
        """
        if timeout is None:
            timeout = self.PROCESS_TERMINATION_TIMEOUT

        if process and process.returncode is None:
            logger.info(f"[MCP] Terminating {process_name}...")
            process.kill()
            try:
                await asyncio.wait_for(process.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning(f"[MCP] {process_name} termination timed out")

    def _generate_config_missing_report(
        self,
        report_path: Path,
        created_config_path: Path
    ) -> str:
        """生成配置文件缺失错误报告 | Generate configuration file missing error report

        Args:
            report_path: 报告文件路径 | Report file path
            created_config_path: 创建的配置文件路径 | Created configuration file path

        Returns:
            str: 错误报告内容 | Error report content
        """
        error_report = f"""# Review Report

## Status
error

## Error Message
Configuration file missing

## Summary
No configuration file was found (.VetMediatorSetting.json). A default configuration has been created at:

{created_config_path}

Please edit this file to configure your CLI tool (iflow, claude, or other) and restart the review.

Configuration locations (in priority order):
1. Project: {created_config_path.parent}/.VetMediatorSetting.json
2. Global: {Path.home()}/.VetMediatorSetting.json

Required fields in each CLI tool preset:
- executable: CLI tool executable name
- args: Command line arguments
- log_file_name: Log file name (relative path)
- extended_prompt: (Optional) Additional prompt for the tool
"""
        report_path.write_text(error_report, encoding='utf-8')
        return error_report
