"""CLI工具检查UI - 当CLI工具未找到时提供交互式重试界面 (v2.0)

此模块提供独立的GUI窗口，用于：
1. 显示CLI工具未找到的详细错误信息
2. 显示配置文件链接（全局和项目）
3. 展示所有配置工具的状态表格
4. 允许用户激活其他健康的CLI工具
5. 允许用户重试检查（重新加载配置）
6. 允许用户取消审查

运行方式：
    python cli_check_ui.py \\
        --project-root "D:\\MyProject" \\
        --current-tool "codex" \\
        --error-detail "FileNotFoundError: codex.exe"

退出码：
    100: 用户选择重试或激活新工具（reviewer应重新加载配置）
    1: 用户选择取消（reviewer应生成错误报告）
"""

import sys
import argparse
import subprocess
from pathlib import Path
from typing import Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor, QFont, QCloseEvent

try:
    from .cli_config import get_current_config, update_current_cli_tool, load_config
    from .gui_utils import get_dark_mode_palette
except ImportError:
    from cli_config import get_current_config, update_current_cli_tool, load_config
    from gui_utils import get_dark_mode_palette


RETRY_BUTTON_STYLE = """
    QPushButton {
        background-color: #2A82DA;
        color: white;
        border: none;
        padding: 8px 20px;
        border-radius: 4px;
        font-size: 11pt;
        font-weight: bold;
        min-width: 120px;
    }
    QPushButton:hover { background-color: #4A9EFF; }
    QPushButton:pressed { background-color: #1A72CA; }
"""

CANCEL_BUTTON_STYLE = """
    QPushButton {
        background-color: #C0504D;
        color: white;
        border: none;
        padding: 8px 20px;
        border-radius: 4px;
        font-size: 11pt;
        font-weight: bold;
        min-width: 120px;
    }
    QPushButton:hover { background-color: #E06666; }
    QPushButton:pressed { background-color: #A03938; }
"""

ACTIVATE_BUTTON_STYLE = """
    QPushButton {
        background-color: #70AD47;
        color: white;
        border: none;
        padding: 4px 12px;
        border-radius: 3px;
        font-size: 9pt;
        font-weight: bold;
    }
    QPushButton:hover { background-color: #8FBF6A; }
    QPushButton:pressed { background-color: #5A8C39; }
"""

DEFAULT_WINDOW_WIDTH = 700
DEFAULT_WINDOW_HEIGHT = 800


class CliCheckWindow(QMainWindow):
    """CLI工具检查窗口 (v2.0)"""

    def __init__(
        self,
        project_root: Path,
        current_tool: str,
        error_detail: str,
        preview_mode: bool = False,
        config_mode: bool = False
    ) -> None:
        """初始化检查窗口

        Args:
            project_root: 项目根目录路径
            current_tool: 当前失败的CLI工具名（如"codex"）
            error_detail: 错误详情
            preview_mode: 预览模式（True时禁用重试和激活功能）
            config_mode: 配置管理模式（True时允许激活但不显示重试，总是显示配置界面）
        """
        super().__init__()

        self.project_root = project_root
        self.current_tool = current_tool
        self.error_detail = error_detail
        self.preview_mode = preview_mode
        self.config_mode = config_mode

        try:
            full_config = load_config(self.project_root)
            self.cli_presets = full_config.get("cli_presets", {})
            self.current_cli_tool = full_config.get("current_cli_tool", current_tool)
        except Exception as e:
            QMessageBox.critical(
                None,
                "配置加载失败 (Config Load Failed)",
                f"无法加载配置文件：{e}\n\nCannot load configuration: {e}"
            )
            sys.exit(1)

        self.tool_health = self._check_all_tools_health()

        # 设置窗口标题
        if self.config_mode:
            self.setWindowTitle("CLI Tool Configuration")
        elif self.preview_mode:
            self.setWindowTitle(f"{self.current_cli_tool.capitalize()} CLI Tool Configuration - Preview")
        else:
            self.setWindowTitle(f"{self.current_cli_tool.capitalize()} CLI Tool Not Found")
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        self._create_ui()

    def _check_single_tool(self, tool_name: str, tool_config: dict) -> bool:
        """检查单个CLI工具的健康状态

        Args:
            tool_name: 工具名称（如"iflow", "claude"）
            tool_config: 工具配置字典

        Returns:
            True表示工具可用（包含版本检查成功或超时）
            False表示工具不可用（未安装或执行失败）

        说明：
            - 成功或超时：返回True（工具存在，可以尝试使用）
            - 未找到或其他错误：返回False（工具不可用）
        """
        try:
            executable = tool_config.get("executable", tool_name)
            # 在Windows上使用shell=True以支持.cmd/.bat文件
            # npm安装的CLI工具在Windows上通常是.cmd批处理文件
            is_windows = sys.platform == 'win32'

            result = subprocess.run(
                [executable, "--version"],
                capture_output=True,
                timeout=5,  # 5秒超时
                text=True,
                shell=is_windows
            )
            # 返回码为0表示成功
            return result.returncode == 0

        except subprocess.TimeoutExpired:
            # 超时：进程已启动（工具存在）但未在5秒内完成
            # 策略：返回True，因为工具存在，只是版本检查慢
            return True

        except (FileNotFoundError, OSError):
            # 未找到：工具未安装或不在PATH中
            return False

        except Exception:
            # 其他异常：返回False（不健康）
            return False

    def _check_all_tools_health(self) -> Dict[str, bool]:
        """并发检查所有CLI工具的健康状态

        Returns:
            {tool_name: is_healthy}
        """
        results = {}

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self._check_single_tool, name, config): name
                for name, config in self.cli_presets.items()
            }

            for future in as_completed(futures):
                tool_name = futures[future]
                try:
                    results[tool_name] = future.result()
                except Exception:
                    results[tool_name] = False

        return results

    def _create_ui(self) -> None:
        """创建UI界面布局"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 添加各个UI组件
        self.warning_label = self._create_warning_label()
        main_layout.addWidget(self.warning_label)

        config_links_layout = self._create_config_links()
        main_layout.addLayout(config_links_layout)

        self.tools_table = self._create_tools_table()
        main_layout.addWidget(self.tools_table)

        self.log_text = self._create_log_area()
        main_layout.addWidget(self.log_text, stretch=1)

        button_layout = self._create_buttons()
        main_layout.addLayout(button_layout)

        footer_layout = self._create_footer()
        main_layout.addLayout(footer_layout)

    def _create_warning_label(self) -> QLabel:
        """创建顶部警告标签（基于真实健康检查结果）"""
        is_current_tool_healthy = self.tool_health.get(self.current_tool, False)

        if self.config_mode or is_current_tool_healthy:
            # 配置模式或工具健康：显示正常状态
            if self.config_mode:
                warning_label = QLabel(
                    f"CLI工具配置管理\n"
                    f"当前激活: {self.current_tool.capitalize()}"
                )
            else:
                warning_label = QLabel(
                    f"{self.current_tool.capitalize()} CLI工具运行正常\n"
                    f"当前配置和健康状态"
                )
            warning_label.setStyleSheet(
                "color: #2A82DA; font-size: 14pt; font-weight: bold; padding: 10px;"
            )
        else:
            # 工具不健康：显示错误警告
            warning_label = QLabel(
                f"未找到 {self.current_tool.capitalize()} CLI工具\n"
                f"请检查 {self.current_tool.capitalize()} 是否安装或配置是否正确"
            )
            warning_label.setStyleSheet(
                "color: #C0504D; font-size: 14pt; font-weight: bold; padding: 10px;"
            )
        warning_label.setAlignment(Qt.AlignCenter)
        warning_label.setWordWrap(True)
        return warning_label

    def _create_config_links(self) -> QHBoxLayout:
        """创建配置文件链接栏"""
        config_links_layout = QHBoxLayout()
        config_links_layout.addWidget(QLabel("配置文件: "))

        global_config_path = Path.home() / ".VetMediatorSetting.json"
        global_link = QLabel()
        if global_config_path.exists():
            global_link.setText(f'<a href="file:///{global_config_path}">全局配置</a>')
            global_link.setOpenExternalLinks(True)
        else:
            global_link.setText('<span style="color:gray">全局配置(不存在)</span>')
        global_link.setTextFormat(Qt.RichText)
        config_links_layout.addWidget(global_link)

        config_links_layout.addWidget(QLabel(" | "))

        project_config_path = self.project_root / ".VetMediatorSetting.json"
        project_link = QLabel()
        if project_config_path.exists():
            project_link.setText(f'<a href="file:///{project_config_path}">项目配置</a>')
            project_link.setOpenExternalLinks(True)
        else:
            project_link.setText('<span style="color:gray">项目配置(不存在)</span>')
        project_link.setTextFormat(Qt.RichText)
        config_links_layout.addWidget(project_link)

        config_links_layout.addStretch()
        return config_links_layout

    def _create_tools_table(self) -> QTableWidget:
        """创建CLI工具状态表格"""
        tools_table = QTableWidget()
        tools_table.setColumnCount(4)
        tools_table.setHorizontalHeaderLabels(["选中", "工具名", "状态", "操作"])
        tools_table.setRowCount(len(self.cli_presets))
        tools_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        tools_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tools_table.setFixedHeight(200)

        tools_table.setColumnWidth(0, 40)
        tools_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        tools_table.setColumnWidth(2, 80)
        tools_table.setColumnWidth(3, 80)

        for row, (tool_name, tool_config) in enumerate(self.cli_presets.items()):
            check_item = QTableWidgetItem("✓" if tool_name == self.current_cli_tool else "")
            check_item.setTextAlignment(Qt.AlignCenter)
            tools_table.setItem(row, 0, check_item)

            name_item = QTableWidgetItem(tool_name.capitalize())
            tools_table.setItem(row, 1, name_item)

            is_healthy = self.tool_health.get(tool_name, False)
            status_item = QTableWidgetItem("● 健康" if is_healthy else "● 不可用")
            status_item.setForeground(QColor(0, 255, 0) if is_healthy else QColor(255, 0, 0))
            status_item.setTextAlignment(Qt.AlignCenter)
            tools_table.setItem(row, 2, status_item)

            if tool_name != self.current_cli_tool and is_healthy and (not self.preview_mode or self.config_mode):
                # 非预览模式或配置模式：显示激活按钮
                activate_btn = QPushButton("激活")
                activate_btn.setStyleSheet(ACTIVATE_BUTTON_STYLE)
                activate_btn.clicked.connect(lambda checked, t=tool_name: self._on_activate(t))
                tools_table.setCellWidget(row, 3, activate_btn)
            else:
                empty_item = QTableWidgetItem("")
                tools_table.setItem(row, 3, empty_item)

        return tools_table

    def _create_log_area(self) -> QTextEdit:
        """创建日志显示区域"""
        log_text = QTextEdit()
        log_text.setReadOnly(True)
        log_text.setFont(QFont("Consolas", 9))
        log_text.setMinimumHeight(300)
        self._append_initial_log_to(log_text)
        return log_text

    def _create_buttons(self) -> QHBoxLayout:
        """创建底部按钮栏"""
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # 预览模式或配置模式下不显示重试按钮
        if not self.preview_mode and not self.config_mode:
            retry_btn = QPushButton("重试 (Retry)")
            retry_btn.setStyleSheet(RETRY_BUTTON_STYLE)
            retry_btn.clicked.connect(self._on_retry)
            button_layout.addWidget(retry_btn)

            button_layout.addSpacing(20)

        cancel_btn = QPushButton("关闭 (Close)" if (self.preview_mode or self.config_mode) else "关闭 (Cancel)")
        cancel_btn.setStyleSheet(CANCEL_BUTTON_STYLE)
        cancel_btn.clicked.connect(self._on_cancel)
        button_layout.addWidget(cancel_btn)

        button_layout.addStretch()
        return button_layout

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

    def _append_initial_log_to(self, log_text: QTextEdit) -> None:
        """显示初始诊断信息（基于真实健康检查结果）"""
        is_current_tool_healthy = self.tool_health.get(self.current_tool, False)
        current_config = self.cli_presets.get(self.current_tool, {})
        executable = current_config.get("executable", self.current_tool)

        if self.config_mode or is_current_tool_healthy:
            # 配置模式或工具健康：显示配置摘要
            # 统计健康工具数量
            healthy_count = sum(1 for is_healthy in self.tool_health.values() if is_healthy)
            total_count = len(self.tool_health)

            # 配置文件路径
            global_config = Path.home() / ".VetMediatorSetting.json"
            project_config = self.project_root / ".VetMediatorSetting.json"

            if self.config_mode:
                log_content = f"""[INFO] CLI Tool Configuration Manager

Current Active Tool: {self.current_tool.capitalize()}
Executable: {executable}
Health Status: {"✓ Healthy" if is_current_tool_healthy else "✗ Not Available"}

Tool Health Summary:
  • Healthy tools: {healthy_count}/{total_count}
  • All configured tools are listed in the table above

Configuration Files:
  • Global: {global_config} {"(exists)" if global_config.exists() else "(not found)"}
  • Project: {project_config} {"(exists)" if project_config.exists() else "(not found)"}

Available Actions:
  • View detailed status for each CLI tool
  • Switch to another healthy tool by clicking 'Activate'
  • Check configuration files via the links above
  • Close this window anytime

Note: Changes made here will take effect immediately for the current project.
"""
            else:
                log_content = f"""[INFO] CLI Tool Status: OK

Current Active Tool: {self.current_tool.capitalize()}
Executable: {executable}
Version Check: Passed

Tool Health Status:
  • Healthy tools: {healthy_count}/{total_count}
  • All configured tools are listed in the table above

Configuration Files:
  • Global: {global_config} {"(exists)" if global_config.exists() else "(not found)"}
  • Project: {project_config} {"(exists)" if project_config.exists() else "(not found)"}

You can:
  • View all tool configurations in the table above
  • Check health status for each tool
"""
                if self.preview_mode:
                    log_content += "  • Close this window anytime (no confirmation needed)\n"
                else:
                    log_content += "  • Activate another tool if needed\n  • Click 'Retry' to recheck tool status\n"

                log_content += "\nThis window shows real-time CLI tool status based on version checks.\n"
        else:
            # 工具不健康：显示错误诊断
            install_cmd = current_config.get("install_command", "")

            log_content = f"""[ERROR] {self.current_tool.capitalize()} CLI Tool Not Found

Attempted to execute: {executable} --version
Error details: {self.error_detail}

Possible causes:
  • {self.current_tool.capitalize()} is not installed
  • PATH environment variable is not configured
  • Configuration in .VetMediatorSetting.json is incorrect
"""

            if install_cmd:
                log_content += f"""
Recommended installation command:
  {install_cmd}
"""

            log_content += f"""
Additional checks:
  • Verify PATH:
    - Linux/Mac: echo $PATH
    - Windows: echo %PATH%
  • Check configuration file: .VetMediatorSetting.json
  • Verify executable:
    - Linux/Mac: which {executable}
    - Windows: where {executable}

You can also activate another healthy CLI tool from the table above"""

            if not self.preview_mode:
                log_content += ",\nor fix the issue and click 'Retry' to continue.\n"
            else:
                log_content += ".\n"

        log_text.setPlainText(log_content)

    def _refresh_after_activation(self, new_tool: str) -> None:
        """刷新界面以反映新激活的工具

        Args:
            new_tool: 新激活的工具名称
        """
        try:
            # 1. 重新加载配置
            full_config = load_config(self.project_root)
            self.current_cli_tool = full_config.get("current_cli_tool", new_tool)
            self.current_tool = self.current_cli_tool

            # 2. 更新窗口标题
            self.setWindowTitle("CLI Tool Configuration")

            # 3. 更新警告标签
            is_healthy = self.tool_health.get(self.current_tool, False)
            self.warning_label.setText(
                f"CLI工具配置管理\n"
                f"当前激活: {self.current_tool.capitalize()}"
            )

            # 4. 更新表格的选中标记和操作按钮
            for row, tool_name in enumerate(self.cli_presets.keys()):
                # 更新选中标记
                check_item = self.tools_table.item(row, 0)
                if check_item:
                    check_item.setText("✓" if tool_name == self.current_cli_tool else "")

                # 更新操作列的激活按钮
                is_healthy = self.tool_health.get(tool_name, False)
                if tool_name != self.current_cli_tool and is_healthy:
                    # 不是当前工具且健康：显示激活按钮
                    activate_btn = QPushButton("激活")
                    activate_btn.setStyleSheet(ACTIVATE_BUTTON_STYLE)
                    activate_btn.clicked.connect(lambda checked, t=tool_name: self._on_activate(t))
                    self.tools_table.setCellWidget(row, 3, activate_btn)
                else:
                    # 是当前工具或不健康：清除按钮，显示空白
                    self.tools_table.setCellWidget(row, 3, None)
                    empty_item = QTableWidgetItem("")
                    self.tools_table.setItem(row, 3, empty_item)

            # 5. 更新日志区域
            self.log_text.clear()
            self._append_initial_log_to(self.log_text)

        except Exception as e:
            # 如果刷新失败，至少记录错误
            self.log_text.append(f"\n[WARNING] Failed to refresh UI: {e}")

    def _on_activate(self, tool_name: str) -> None:
        """处理激活按钮点击"""
        try:
            update_current_cli_tool(self.project_root, tool_name)

            if self.config_mode:
                # 配置管理模式：先显示确认框，用户确认后再刷新界面
                QMessageBox.information(
                    self,
                    "工具已激活 (Tool Activated)",
                    f"已将当前CLI工具切换为 {tool_name.capitalize()}\n"
                    f"配置已更新并生效。\n\n"
                    f"Switched current CLI tool to {tool_name.capitalize()}.\n"
                    f"Configuration updated and applied."
                )

                # 用户确认后再刷新界面
                self._refresh_after_activation(tool_name)
                # 不退出，继续显示窗口
            else:
                # 审查流程模式：显示消息后退出以重启流程
                QMessageBox.information(
                    self,
                    "工具已激活 (Tool Activated)",
                    f"已将当前CLI工具切换为 {tool_name.capitalize()}\n"
                    f"将重新加载配置并继续审查。\n\n"
                    f"Switched current CLI tool to {tool_name.capitalize()}.\n"
                    f"Will reload configuration and continue review."
                )
                sys.exit(100)

        except Exception as e:
            QMessageBox.critical(
                self,
                "激活失败 (Activation Failed)",
                f"无法更新配置文件：{e}\n\nCannot update configuration: {e}"
            )

    def _on_retry(self) -> None:
        """处理重试按钮点击"""
        sys.exit(100)

    def _on_cancel(self) -> None:
        """处理关闭按钮点击"""
        if self.preview_mode or self.config_mode:
            # 预览模式或配置模式：直接关闭窗口，不需要确认
            self.close()
            return

        # 正常模式：显示确认对话框
        reply = QMessageBox.question(
            self,
            "确认关闭 (Confirm Cancel)",
            "关闭后将终止审查流程，确定要关闭吗？\n"
            "This will terminate the review process. Are you sure?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            sys.exit(1)

    def closeEvent(self, event: QCloseEvent) -> None:
        """窗口关闭事件（用户点击X按钮）"""
        if self.preview_mode or self.config_mode:
            # 预览模式或配置模式：直接接受关闭事件
            event.accept()
            return

        # 正常模式：显示确认对话框
        reply = QMessageBox.question(
            self,
            "确认关闭 (Confirm Cancel)",
            "关闭后将终止审查流程，确定要关闭吗？\n"
            "This will terminate the review process. Are you sure?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            event.accept()
            sys.exit(1)
        else:
            event.ignore()


def main() -> None:
    """主程序入口"""
    parser = argparse.ArgumentParser(
        description="CLI Tool Check UI - Interactive retry interface (v2.0)"
    )
    parser.add_argument(
        "--project-root",
        required=True,
        help="Project root directory path"
    )
    parser.add_argument(
        "--current-tool",
        required=True,
        help="Current failed CLI tool name (e.g., 'codex')"
    )
    parser.add_argument(
        "--error-detail",
        required=True,
        help="Error details from the failed check"
    )
    parser.add_argument(
        "--preview-mode",
        action="store_true",
        help="Preview mode - show configuration without error context"
    )
    parser.add_argument(
        "--config-mode",
        action="store_true",
        help="Configuration management mode - allow tool activation without retry button"
    )

    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setPalette(get_dark_mode_palette(app))
    app.setStyle("Fusion")

    window = CliCheckWindow(
        project_root=Path(args.project_root),
        current_tool=args.current_tool,
        error_detail=args.error_detail,
        preview_mode=args.preview_mode,
        config_mode=args.config_mode
    )
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
