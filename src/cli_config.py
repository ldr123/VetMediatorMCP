"""
CLI工具配置加载器 | CLI Tool Configuration Loader

功能 | Features:
- 从JSON配置文件加载配置 | Load configuration from JSON files
- 支持三层优先级：项目配置 > 用户配置 > 默认配置 | Support 3-tier priority: project > user > default
- 深度合并配置 | Deep merge configurations
- 按需生成配置文件 | Create configuration files on demand
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any
from copy import deepcopy

logger = logging.getLogger(__name__)

# 内置提示词模板（所有CLI工具共享）| Built-in prompt template (shared by all CLI tools)
BUILTIN_PROMPT = (
    "Please read {session_rel_path}/ReviewIndex.md for the review index. "
    "It contains a task list table showing all task files in the same directory. "
    "Review each task file according to the index and generate a comprehensive report. "
    "Write report.md to {session_rel_path}/    "
    "CRITICAL REQUIREMENT: You MUST use UTF-8 encoding WITHOUT BOM (Byte Order Mark) "
    "for ALL file operations (reading ReviewIndex.md, reading task files, writing report.md, "
    "and any other file I/O). Do NOT use UTF-8 with BOM, UTF-16, or any other encoding. "
    "This is mandatory to ensure cross-platform compatibility."
)


def validate_tool_config(config: Dict[str, Any], tool_name: str) -> None:
    """验证CLI工具配置的有效性 | Validate CLI tool configuration

    Args:
        config: CLI工具配置字典 | CLI tool configuration dict
        tool_name: 工具名称（用于错误提示）| Tool name (for error messages)

    Raises:
        ValueError: 如果配置无效 | If configuration is invalid
    """
    # 检查executable
    executable = config.get("executable", "")
    if not executable or not isinstance(executable, str):
        raise ValueError(f"Invalid 'executable' in '{tool_name}' config: must be non-empty string")

    # 检查args
    args = config.get("args")
    if not isinstance(args, list):
        raise ValueError(f"Invalid 'args' in '{tool_name}' config: must be a list")

    # 检查log_file_name
    log_file_name = config.get("log_file_name", "")
    if not log_file_name:
        raise ValueError(f"Missing 'log_file_name' in '{tool_name}' config")

    if Path(log_file_name).is_absolute():
        raise ValueError(
            f"Invalid 'log_file_name' in '{tool_name}' config: "
            f"must be relative path, got '{log_file_name}'"
        )


def get_default_config() -> Dict[str, Any]:
    """返回内置默认配置 | Return built-in default configuration"""
    return {
        "current_cli_tool": "iflow",
        "env_vars": {
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1"
        },
        "cli_presets": {
            "iflow": {
                "executable": "iflow",
                "args": [
                    "-y",
                    "-p"
                ],
                "log_file_name": "iflow.log",
                "extended_prompt": "",
                "install_command": "npm i -g @iflow-ai/iflow-cli"
            },
            "codex": {
                "executable": "codex",
                "args": [
                    "exec",
                    "--skip-git-repo-check",
                    "--dangerously-bypass-approvals-and-sandbox"
                ],
                "log_file_name": "codex.log",
                "extended_prompt": "",
                "install_command": "npm install -g @openai/codex"
            },
            "claude": {
                "executable": "claude",
                "args": [
                    "--dangerously-skip-permissions"
                ],
                "log_file_name": "claude.log",
                "extended_prompt": "Please use ultrathink mode for deep analysis",
                "install_command": "npm install -g @anthropic-ai/claude-code"
            }
        }
    }


def deep_merge_dict(base: dict, override: dict) -> dict:
    """深度合并两个字典 | Deep merge two dictionaries

    Args:
        base: 基础字典 | Base dictionary
        override: 覆盖字典 | Override dictionary

    Returns:
        合并后的字典（新字典，不修改原字典）
        Merged dictionary (new dict, original dicts unchanged)
    """
    result = deepcopy(base)

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dict(result[key], value)
        else:
            result[key] = deepcopy(value)

    return result


def get_user_config_path() -> Path:
    """返回用户全局配置文件路径（不自动创建）
    Return user global configuration file path (without auto-creation)

    Returns:
        用户配置文件路径 (~/.vetmediator/config.json)
        User configuration file path (~/.vetmediator/config.json)
    """
    return Path.home() / ".vetmediator" / "config.json"


def get_legacy_config_path() -> Path:
    """返回旧版全局配置文件路径（用于向后兼容）
    Return legacy global configuration file path (for backward compatibility)

    Returns:
        旧版配置文件路径 (~/.VetMediatorSetting.json)
        Legacy configuration file path (~/.VetMediatorSetting.json)
    """
    return Path.home() / ".VetMediatorSetting.json"


def migrate_legacy_config() -> bool:
    """自动迁移旧版配置到新路径（如果存在）
    Automatically migrate legacy config to new path (if exists)

    Returns:
        True表示迁移成功或无需迁移，False表示迁移失败
        True if migration succeeded or not needed, False if migration failed
    """
    legacy_path = get_legacy_config_path()
    new_path = get_user_config_path()

    # 如果新路径已存在，无需迁移
    if new_path.exists():
        return True

    # 如果旧路径不存在，无需迁移
    if not legacy_path.exists():
        return True

    try:
        # 确保新目录存在
        new_path.parent.mkdir(parents=True, exist_ok=True)

        # 读取旧配置
        legacy_content = legacy_path.read_text(encoding='utf-8')

        # 写入新路径
        new_path.write_text(legacy_content, encoding='utf-8')

        # 设置文件权限（仅用户可读写）
        try:
            new_path.chmod(0o600)
        except Exception:
            pass  # 忽略权限设置失败

        # 删除旧文件
        legacy_path.unlink()

        logger.info(f"[Config] Migrated legacy config from {legacy_path} to {new_path}")
        return True

    except Exception as e:
        logger.error(f"[Config] Failed to migrate legacy config: {e}")
        return False


def create_config_file(path: Path) -> None:
    """创建配置文件到指定路径 | Create configuration file at specified path

    Args:
        path: 配置文件路径（全局或项目）| Configuration file path (global or project)

    Raises:
        Exception: 文件创建失败 | File creation failed
    """
    default_config = get_default_config()

    try:
        # 确保父目录存在
        path.parent.mkdir(parents=True, exist_ok=True)

        # 写入配置文件
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)

        logger.info(f"[Config] Created config file: {path}")

        # 设置文件权限（仅用户可读写）
        try:
            path.chmod(0o600)
        except Exception as e:
            logger.warning(f"[Config] Failed to set file permission: {e}")

    except Exception as e:
        logger.error(f"[Config] Failed to create config file: {e}")
        raise


def load_config(project_root: Path) -> Dict[str, Any]:
    """加载配置（三层优先级）| Load configuration (3-tier priority)

    优先级（从高到低）| Priority (high to low):
    1. 项目目录/.VetMediatorSetting.json | Project directory/.VetMediatorSetting.json
    2. ~/.vetmediator/config.json (自动从旧路径迁移 | Auto-migrated from legacy path)
    3. 内置默认配置 | Built-in default configuration

    注意：不会自动创建配置文件 | Note: No auto-creation of config files

    Args:
        project_root: 项目根目录 | Project root directory

    Returns:
        合并后的配置字典 | Merged configuration dict
    """
    # 0. 尝试自动迁移旧配置（仅在首次加载时触发）
    migrate_legacy_config()

    # 1. 从默认配置开始
    config = get_default_config()

    # 2. 尝试加载用户全局配置（不自动创建）
    user_config_path = get_user_config_path()
    if user_config_path.exists():
        try:
            user_config_text = user_config_path.read_text(encoding='utf-8')
            user_config = json.loads(user_config_text)
            config = deep_merge_dict(config, user_config)
            logger.debug(f"[Config] Loaded user config from {user_config_path}")
        except json.JSONDecodeError as e:
            logger.warning(f"[Config] Failed to parse user config: {e}. Using default.")
        except Exception as e:
            logger.warning(f"[Config] Failed to read user config: {e}. Using default.")

    # 3. 尝试加载项目配置 | Try to load project config
    project_config_path = project_root / ".VetMediatorSetting.json"
    if project_config_path.exists():
        try:
            project_config_text = project_config_path.read_text(encoding='utf-8')
            project_config = json.loads(project_config_text)
            config = deep_merge_dict(config, project_config)
            logger.debug(f"[Config] Loaded project config from {project_config_path}")
        except json.JSONDecodeError as e:
            logger.warning(f"[Config] Failed to parse project config: {e}. Ignoring.")
        except Exception as e:
            logger.warning(f"[Config] Failed to read project config: {e}. Ignoring.")

    return config


def get_current_config(project_root: Path) -> Dict[str, Any]:
    """获取当前CLI工具的配置 | Get current CLI tool configuration

    Args:
        project_root: 项目根目录 | Project root directory

    Returns:
        当前CLI工具的配置字典（已合并）| Current CLI tool configuration dict (merged)

    Raises:
        ValueError: 如果配置无效（current_cli_tool不存在、配置验证失败等）
                   If configuration is invalid (current_cli_tool not found, validation failed, etc.)
    """
    full_config = load_config(project_root)

    current_tool = full_config.get("current_cli_tool")
    if not current_tool:
        logger.warning("[Config] 'current_cli_tool' not specified, using 'codex'")
        current_tool = "codex"

    cli_presets = full_config.get("cli_presets", {})
    if current_tool not in cli_presets:
        available_tools = list(cli_presets.keys())
        raise ValueError(
            f"Unknown CLI tool: '{current_tool}'. "
            f"Available tools: {available_tools}"
        )

    tool_config = deepcopy(cli_presets[current_tool])

    # 从顶层配置获取env_vars（如果tool_config中没有）
    if "env_vars" not in tool_config:
        env_vars = full_config.get("env_vars")
        if env_vars:
            tool_config["env_vars"] = env_vars

    # 验证配置有效性（这会抛出ValueError）
    try:
        validate_tool_config(tool_config, current_tool)
    except ValueError as e:
        # 配置验证错误应该立即失败，不应该fallback
        logger.error(f"[Config] Configuration validation failed: {e}")
        raise

    return tool_config


def update_current_cli_tool(project_root: Path, new_tool: str) -> None:
    """更新项目配置中的current_cli_tool | Update current_cli_tool in project configuration

    Args:
        project_root: 项目根目录路径 | Project root directory path
        new_tool: 新的CLI工具名称（如"iflow"、"claude"）| New CLI tool name (e.g., "iflow", "claude")

    注意 | Note:
        - 如果项目配置文件不存在，会创建新文件 | Creates new file if project config doesn't exist
        - 只修改current_cli_tool字段，保留其他配置 | Only modifies current_cli_tool, keeps other configs
        - 使用UTF-8编码，ensure_ascii=False支持多语言 | Uses UTF-8 encoding, ensure_ascii=False for i18n
    """
    project_config_path = project_root / ".VetMediatorSetting.json"

    if project_config_path.exists():
        try:
            with open(project_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"[Config] Failed to read existing project config: {e}. Creating new config.")
            config = {}
    else:
        config = {}

    config["current_cli_tool"] = new_tool

    try:
        with open(project_config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        logger.info(f"[Config] Updated current_cli_tool to '{new_tool}' in {project_config_path}")
    except Exception as e:
        logger.error(f"[Config] Failed to write project config: {e}")
        raise
