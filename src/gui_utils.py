"""GUI environment detection utilities."""

import os
import sys
import logging
from typing import Dict, Any

# 配置logging输出到stderr
logging.basicConfig(
    level=logging.INFO,
    format='[GUI][%(levelname)s] %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


def get_dark_mode_palette(app):
    """获取暗色主题调色板

    Args:
        app: QApplication实例

    Returns:
        QPalette: 配置好的暗色主题调色板
    """
    from PySide6.QtGui import QPalette, QColor
    from PySide6.QtCore import Qt

    dark_palette = app.palette()
    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
    dark_palette.setColor(QPalette.Base, QColor(42, 42, 42))
    dark_palette.setColor(QPalette.AlternateBase, QColor(66, 66, 66))
    dark_palette.setColor(QPalette.ToolTipBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
    dark_palette.setColor(QPalette.Dark, QColor(35, 35, 35))
    dark_palette.setColor(QPalette.Shadow, QColor(20, 20, 20))
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(80, 80, 80))
    dark_palette.setColor(QPalette.HighlightedText, Qt.white)
    dark_palette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(127, 127, 127))
    dark_palette.setColor(QPalette.PlaceholderText, QColor(127, 127, 127))
    return dark_palette


def check_gui_available() -> bool:
    """检测当前环境是否支持GUI显示

    检测策略：
    1. Linux/Unix环境：检查DISPLAY或WAYLAND_DISPLAY环境变量
    2. 尝试导入PySide6（不创建QApplication实例，避免单例冲突）

    Returns:
        bool: True表示支持GUI，False表示headless环境

    Notes:
        - 此函数只检测PySide6可用性，不创建QApplication单例
        - 实际的QApplication实例由UI脚本创建
    """
    logger.info(f"[GUI] Checking GUI availability on {os.name} platform")

    # 第一步：检查Linux/Unix环境变量
    if os.name == 'posix':  # Linux, macOS, Unix
        has_display = bool(os.environ.get('DISPLAY'))
        has_wayland = bool(os.environ.get('WAYLAND_DISPLAY'))

        logger.info(f"[GUI] DISPLAY={os.environ.get('DISPLAY', 'not set')}")
        logger.info(f"[GUI] WAYLAND_DISPLAY={os.environ.get('WAYLAND_DISPLAY', 'not set')}")

        if not has_display and not has_wayland:
            logger.info("[GUI] No display server environment variables found, likely headless")
            return False

    # 第二步：尝试导入PySide6（不创建实例）
    try:
        logger.info("[GUI] Attempting to import PySide6...")
        from PySide6.QtWidgets import QApplication
        logger.info("[GUI] PySide6 imported successfully")
        logger.info("[GUI] GUI is available")
        return True

    except Exception as e:
        logger.warning(f"[GUI] PySide6 not available: {type(e).__name__}: {str(e)}")
        return False


def get_gui_info() -> Dict[str, Any]:
    """获取GUI环境详细信息（用于调试）

    Returns:
        dict: 包含平台、环境变量等信息
    """
    info = {
        'os_name': os.name,
        'platform': sys.platform,
        'display': os.environ.get('DISPLAY', 'Not set'),
        'wayland_display': os.environ.get('WAYLAND_DISPLAY', 'Not set'),
    }

    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            info['qt_platform'] = app.platformName()
            info['gui_available'] = True
        else:
            info['gui_available'] = False
    except Exception:
        info['gui_available'] = False
        info['qt_platform'] = 'Not available'

    return info
