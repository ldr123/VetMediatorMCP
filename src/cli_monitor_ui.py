"""CLI工具审查实时监控UI界面

此模块提供一个独立的GUI窗口，用于：
1. 实时显示日志文件的内容
2. 快速打开ReviewIndex.md和Task*.md文件
3. 允许用户中止审查流程
4. 显示项目信息链接

运行方式：
    python codex_monitor_ui.py \\
        --log-path /path/to/tool.log \\
        --file-path /path/to/ReviewIndex.md \\
        --file-path /path/to/Task1_Feature.md \\
        --file-path /path/to/Task2_Feature.md \\
        --tool-name "ToolName"
"""

import sys
import argparse
from pathlib import Path
from typing import Optional, List

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QPalette, QColor, QTextCursor, QDesktopServices, QCloseEvent

try:
    from .gui_utils import get_dark_mode_palette
    from .cli_check_ui import CliCheckWindow
    from .cli_config import load_config
except ImportError:
    from gui_utils import get_dark_mode_palette
    from cli_check_ui import CliCheckWindow
    from cli_config import load_config


# UI样式常量
LINK_BUTTON_STYLE = """
    QPushButton {
        color: #2A82DA;
        text-decoration: underline;
        border: none;
        padding: 5px;
    }
    QPushButton:hover {
        color: #4A9EFF;
    }
"""

EXIT_BUTTON_STYLE = """
    QPushButton {
        background-color: #C0504D;
        color: white;
        border: none;
        padding: 5px 15px;
        border-radius: 3px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #E06666;
    }
    QPushButton:pressed {
        background-color: #A03938;
    }
"""

# UI尺寸常量
DEFAULT_WINDOW_WIDTH = 800
DEFAULT_WINDOW_HEIGHT = 600
LOG_UPDATE_INTERVAL_MS = 200
SCROLL_POSITION_THRESHOLD = 10


class CliMonitorWindow(QMainWindow):
    """CLI工具审查实时监控窗口"""

    def __init__(
        self,
        log_path: str,
        file_paths: List[str],
        tool_name: str = "Codex"
    ) -> None:
        """初始化监控窗口

        Args:
            log_path: 日志文件的绝对路径
            file_paths: 要监控的文件路径列表（ReviewIndex.md和Task*.md）
            tool_name: CLI工具显示名称（默认为Codex）
        """
        super().__init__()

        # 保存文件路径和工具名称
        self.log_path = Path(log_path)
        self.file_paths = [Path(p) for p in file_paths]
        self.tool_name = tool_name

        # 日志读取状态
        self.last_log_size = 0  # 上次读取的文件大小（用于增量读取）
        self.user_scrolled = False  # 用户是否手动滚动过
        self.log_exists = False  # 日志文件是否已创建

        # 预览窗口引用（如果用户点击"查看"按钮）
        self.preview_window = None

        # 设置窗口属性
        self.setWindowTitle(f"{self.tool_name} is processing...")
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)  # 使用常量

        # 设置窗口置顶（始终显示在最前面）
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        # 创建UI组件
        self._create_ui()

        # 启动定时器（每200ms检测日志更新）
        self.log_timer = QTimer(self)
        self.log_timer.timeout.connect(self._update_log)
        self.log_timer.start(LOG_UPDATE_INTERVAL_MS)  # 使用常量

    def _create_ui(self) -> None:
        """创建UI界面布局"""
        # 中央容器
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局（垂直）
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 添加各个UI组件
        toolbar_layout = self._create_toolbar()
        main_layout.addLayout(toolbar_layout)

        self.log_text_edit = self._create_log_area()
        main_layout.addWidget(self.log_text_edit, stretch=1)

        footer_layout = self._create_footer()
        main_layout.addLayout(footer_layout)

    def _create_toolbar(self) -> QHBoxLayout:
        """创建顶部工具栏（文件链接 + 退出按钮）"""
        toolbar_layout = QHBoxLayout()

        # 左侧：文件链接按钮（动态创建，支持自动换行）
        file_links_container = QVBoxLayout()
        file_links_container.setSpacing(5)

        # 80字符换行限制
        MAX_LINE_LENGTH = 80
        # 每个按钮额外占用的空间（padding、间距等，估算）
        BUTTON_OVERHEAD = 3

        current_line_layout = QHBoxLayout()
        current_line_layout.setSpacing(10)
        current_line_length = 0

        # 为每个文件创建按钮，自动换行
        for file_path in self.file_paths:
            file_name = file_path.name
            # 计算按钮占用的字符数（文件名长度 + 额外开销）
            button_length = len(file_name) + BUTTON_OVERHEAD

            # 检查是否需要换行
            if current_line_length > 0 and current_line_length + button_length > MAX_LINE_LENGTH:
                # 当前行已满，添加到容器并创建新行
                current_line_layout.addStretch()
                file_links_container.addLayout(current_line_layout)

                current_line_layout = QHBoxLayout()
                current_line_layout.setSpacing(10)
                current_line_length = 0

            # 创建按钮
            file_btn = QPushButton(file_name)
            file_btn.setFlat(True)
            file_btn.setStyleSheet(LINK_BUTTON_STYLE)
            # 使用默认参数捕获file_path，避免闭包问题
            file_btn.clicked.connect(
                lambda checked=False, fp=file_path: self._open_file(fp)
            )
            current_line_layout.addWidget(file_btn)
            current_line_length += button_length

        # 添加最后一行
        if current_line_length > 0:
            current_line_layout.addStretch()
            file_links_container.addLayout(current_line_layout)

        toolbar_layout.addLayout(file_links_container)
        toolbar_layout.addStretch()  # 弹性空间，将右侧按钮推到最右边

        # 右侧：查看按钮 + 退出按钮
        self.view_btn = QPushButton("查看")
        self.view_btn.setStyleSheet(EXIT_BUTTON_STYLE)
        self.view_btn.clicked.connect(self._on_view_clicked)
        toolbar_layout.addWidget(self.view_btn)

        self.exit_btn = QPushButton("Exit")
        self.exit_btn.setStyleSheet(EXIT_BUTTON_STYLE)
        self.exit_btn.clicked.connect(self._on_exit_clicked)
        toolbar_layout.addWidget(self.exit_btn)

        return toolbar_layout

    def _create_log_area(self) -> QTextEdit:
        """创建中间日志显示区域"""
        log_text_edit = QTextEdit()
        log_text_edit.setReadOnly(True)
        log_text_edit.setLineWrapMode(QTextEdit.WidgetWidth)

        # 设置等宽字体（便于阅读日志）
        font = log_text_edit.font()
        # 添加emoji字体fallback（Windows: Segoe UI Emoji, macOS: Apple Color Emoji）
        font.setFamily("Consolas, Segoe UI Emoji, Apple Color Emoji, monospace")
        font.setPointSize(9)
        log_text_edit.setFont(font)

        # 设置初始提示文字
        log_file_name = self.log_path.name
        log_text_edit.setPlaceholderText(f"Waiting for {log_file_name}...")

        # 监听滚动条移动事件（检测用户是否手动滚动）
        scrollbar = log_text_edit.verticalScrollBar()
        scrollbar.sliderMoved.connect(self._on_user_scroll)
        scrollbar.valueChanged.connect(self._check_scroll_position)

        return log_text_edit

    def _create_footer(self) -> QHBoxLayout:
        """创建底部信息栏（Git项目链接）"""
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()  # 居中对齐

        # Git项目链接 - 国内区
        gitee_link_label = QLabel(
            '国内区: <a href="https://gitee.com/ldr123/VetMediatorMCP">'
            'https://gitee.com/ldr123/VetMediatorMCP'
            '</a>'
        )
        gitee_link_label.setOpenExternalLinks(True)
        gitee_link_label.setStyleSheet("color: #2A82DA;")
        footer_layout.addWidget(gitee_link_label)

        # 分隔符
        separator_label = QLabel("  |  ")
        separator_label.setStyleSheet("color: #666666;")
        footer_layout.addWidget(separator_label)

        # Git项目链接 - Global
        github_link_label = QLabel(
            'Global: <a href="https://github.com/ldr123/VetMediatorMCP">'
            'https://github.com/ldr123/VetMediatorMCP'
            '</a>'
        )
        github_link_label.setOpenExternalLinks(True)
        github_link_label.setStyleSheet("color: #2A82DA;")
        footer_layout.addWidget(github_link_label)

        footer_layout.addStretch()  # 居中对齐

        return footer_layout

    def _open_file(self, file_path: Path) -> None:
        """使用系统默认编辑器打开文件

        Args:
            file_path: 要打开的文件路径
        """
        if not file_path.exists():
            QMessageBox.warning(
                self,
                "File Not Found",
                f"File does not exist:\n{file_path}"
            )
            return

        # 使用QDesktopServices打开文件（跨平台）
        success = QDesktopServices.openUrl(QUrl.fromLocalFile(str(file_path)))

        if not success:
            QMessageBox.warning(
                self,
                "Open Failed",
                f"Failed to open file:\n{file_path}"
            )

    def _confirm_exit(self) -> bool:
        """显示退出确认对话框

        Returns:
            bool: True表示用户确认退出，False表示取消
        """
        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            f"Are you sure you want to exit?\n\n"
            f"This will abort the {self.tool_name} review process.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No  # 默认选中"No"
        )
        return reply == QMessageBox.Yes

    def _on_exit_clicked(self) -> None:
        """处理退出按钮点击事件（显示确认对话框）"""
        if self._confirm_exit():
            # 用户确认退出，使用特殊退出码99通知MCP
            sys.exit(99)

    def _on_view_clicked(self) -> None:
        """处理查看按钮点击事件（显示CLI工具配置预览）"""
        try:
            # 从log_path推断project_root | Infer project_root from log_path
            # log_path格式 | log_path format: project_root/VetMediatorSessions/session-xxx/tool.log
            log_path = Path(self.log_path)
            project_root = log_path.parent.parent.parent

            # 获取当前CLI工具名称
            full_config = load_config(project_root)
            current_tool = full_config.get("current_cli_tool", "codex")

            # 创建预览窗口
            preview_window = CliCheckWindow(
                project_root=project_root,
                current_tool=current_tool,
                error_detail="Preview Mode - Configuration View",
                preview_mode=True
            )

            # 显示预览窗口（非模态）
            preview_window.show()
            # 保持窗口引用，避免被垃圾回收
            self.preview_window = preview_window

        except Exception as e:
            QMessageBox.warning(
                self,
                "无法打开预览 (Cannot Open Preview)",
                f"无法显示CLI工具配置：{e}\n\nCannot display CLI tool configuration: {e}"
            )

    def _on_user_scroll(self, value: int) -> None:
        """用户拖动滚动条时触发"""
        self.user_scrolled = True

    def _check_scroll_position(self, value: int) -> None:
        """检查滚动条位置，如果用户滚动回底部则恢复自动滚动"""
        scrollbar = self.log_text_edit.verticalScrollBar()
        # 如果滚动条在底部（允许SCROLL_POSITION_THRESHOLD像素误差），恢复自动滚动
        if value >= scrollbar.maximum() - SCROLL_POSITION_THRESHOLD:
            self.user_scrolled = False

    def _update_log(self) -> None:
        """定时器回调：读取并显示新的日志内容"""
        # 检查日志文件是否存在
        if not self.log_path.exists():
            if self.log_exists:
                # 文件之前存在，现在消失了（异常情况）
                self.log_text_edit.append("\n[WARNING] Log file disappeared!")
                self.log_exists = False
            return

        if not self.log_exists:
            # 文件首次出现
            self.log_exists = True
            # 清除占位符文字
            self.log_text_edit.clear()

        try:
            # 检查文件大小
            current_size = self.log_path.stat().st_size

            if current_size < self.last_log_size:
                # 文件被截断或重建（罕见情况）
                self.log_text_edit.clear()
                self.last_log_size = 0

            if current_size == self.last_log_size:
                # 没有新内容
                return

            # 增量读取新内容（只读取新增部分）
            with open(self.log_path, 'r', encoding='utf-8', errors='replace') as f:
                f.seek(self.last_log_size)
                new_content = f.read()

            # 更新上次读取位置
            self.last_log_size = current_size

            # 追加新内容到文本框
            cursor = self.log_text_edit.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.log_text_edit.setTextCursor(cursor)
            self.log_text_edit.insertPlainText(new_content)

            # 自动滚动到底部（如果用户未手动滚动）
            if not self.user_scrolled:
                scrollbar = self.log_text_edit.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())

        except Exception as e:
            # 读取失败（文件被占用、权限问题等），忽略错误，下次再试
            pass

    def closeEvent(self, event: QCloseEvent) -> None:
        """窗口关闭事件（用户点击X按钮或通过其他方式关闭窗口）"""
        if self._confirm_exit():
            # 停止定时器
            self.log_timer.stop()

            # 关闭预览窗口（如果存在）
            if self.preview_window and not self.preview_window.isHidden():
                self.preview_window.close()

            # 接受关闭事件，使用特殊退出码
            event.accept()
            sys.exit(99)
        else:
            # 忽略关闭事件
            event.ignore()


def main() -> None:
    """主程序入口"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="CLI Tool Review Monitor UI"
    )
    parser.add_argument(
        "--log-path",
        required=True,
        help="Path to log file"
    )
    parser.add_argument(
        "--file-path",
        action="append",
        required=True,
        help="Path to file (can be specified multiple times for ReviewIndex.md and Task*.md)"
    )
    parser.add_argument(
        "--tool-name",
        default="Codex",
        help="CLI tool display name (default: Codex)"
    )
    args = parser.parse_args()

    # 创建Qt应用
    app = QApplication(sys.argv)

    # 应用暗色主题
    app.setPalette(get_dark_mode_palette(app))
    app.setStyle("Fusion")

    # 创建并显示窗口
    window = CliMonitorWindow(
        log_path=args.log_path,
        file_paths=args.file_path,
        tool_name=args.tool_name
    )
    window.show()

    # 运行事件循环
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
