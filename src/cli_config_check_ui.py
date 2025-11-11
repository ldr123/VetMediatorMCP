"""配置文件缺失检查UI | Configuration file missing check UI.

当全局和项目配置文件都不存在时，弹出此UI让用户选择创建位置。
Displays a dialog when no configuration file is found, allowing users to create
either a global (~/.VetMediatorSetting.json) or project-level (.VetMediatorSetting.json) configuration.
"""

import argparse
import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

try:
    from .cli_config import create_config_file, get_user_config_path
except ImportError:
    from cli_config import create_config_file, get_user_config_path


class ConfigCheckDialog:
    """配置文件缺失检查对话框 | Configuration file missing check dialog."""

    COLOR_BG = '#f0f0f0'
    COLOR_DANGER = '#d9534f'
    COLOR_SUCCESS = '#5cb85c'
    COLOR_PRIMARY = '#0275d8'
    COLOR_WHITE = 'white'

    def __init__(self, project_root: Path):
        """初始化对话框 | Initialize dialog

        Args:
            project_root: 项目根目录路径 | Project root directory path
        """
        self.project_root = project_root
        self.user_config_path = get_user_config_path()
        self.project_config_path = project_root / ".VetMediatorSetting.json"
        self.exit_code = 1

        self.root = tk.Tk()
        self.root.title("Configuration File Missing")
        self.root.geometry("600x300")
        self.root.resizable(False, False)

        self._center_window()
        self._create_widgets()

        self.root.protocol("WM_DELETE_WINDOW", self.on_cancel)

    def _center_window(self):
        """Center the window on screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def _create_widgets(self):
        """Create UI components."""
        title_frame = tk.Frame(self.root, bg=self.COLOR_BG, height=60)
        title_frame.pack(fill=tk.X, padx=0, pady=0)
        title_frame.pack_propagate(False)

        title_label = tk.Label(
            title_frame,
            text="⚠️ Configuration File Missing",
            font=('Arial', 16, 'bold'),
            bg=self.COLOR_BG,
            fg=self.COLOR_DANGER
        )
        title_label.pack(pady=15)

        content_frame = tk.Frame(self.root, padx=20, pady=10)
        content_frame.pack(fill=tk.BOTH, expand=True)

        info_text = (
            "No configuration file found. Please create one to continue.\n\n"
            "Configuration file locations:\n"
        )
        info_label = tk.Label(
            content_frame,
            text=info_text,
            font=('Arial', 10),
            justify=tk.LEFT,
            anchor='w'
        )
        info_label.pack(fill=tk.X, pady=(0, 5))

        global_path_label = tk.Label(
            content_frame,
            text=f"• Global:  {self.user_config_path}  [Not Found]",
            font=('Courier', 9),
            justify=tk.LEFT,
            anchor='w',
            fg=self.COLOR_DANGER
        )
        global_path_label.pack(fill=tk.X, pady=2)

        project_path_label = tk.Label(
            content_frame,
            text=f"• Project: {self.project_config_path}  [Not Found]",
            font=('Courier', 9),
            justify=tk.LEFT,
            anchor='w',
            fg=self.COLOR_DANGER
        )
        project_path_label.pack(fill=tk.X, pady=2)

        button_frame = tk.Frame(self.root, padx=20, pady=15)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)

        create_global_btn = tk.Button(
            button_frame,
            text="Create Global Config",
            command=self.on_create_global,
            width=20,
            height=2,
            bg=self.COLOR_SUCCESS,
            fg=self.COLOR_WHITE,
            font=('Arial', 10, 'bold'),
            relief=tk.RAISED,
            cursor='hand2'
        )
        create_global_btn.pack(side=tk.LEFT, padx=5)

        create_project_btn = tk.Button(
            button_frame,
            text="Create Project Config",
            command=self.on_create_project,
            width=20,
            height=2,
            bg=self.COLOR_PRIMARY,
            fg=self.COLOR_WHITE,
            font=('Arial', 10, 'bold'),
            relief=tk.RAISED,
            cursor='hand2'
        )
        create_project_btn.pack(side=tk.LEFT, padx=5)

        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            command=self.on_cancel,
            width=15,
            height=2,
            bg=self.COLOR_DANGER,
            fg=self.COLOR_WHITE,
            font=('Arial', 10),
            relief=tk.RAISED,
            cursor='hand2'
        )
        cancel_btn.pack(side=tk.RIGHT, padx=5)

    def _create_config_and_open(self, config_path: Path, config_type: str):
        """Create configuration file and open in editor.

        Args:
            config_path: Path to create configuration file
            config_type: Configuration type for display ("Global" or "Project")
        """
        try:
            create_config_file(config_path)
            self._open_editor(config_path)
            messagebox.showinfo(
                "Success",
                f"{config_type} configuration created:\n{config_path}\n\n"
                "Please edit the file and configure your CLI tool."
            )
            self.exit_code = 100
            self.root.destroy()
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to create {config_type.lower()} config:\n{str(e)}"
            )

    def on_create_global(self):
        """Handle create global configuration button click."""
        self._create_config_and_open(self.user_config_path, "Global")

    def on_create_project(self):
        """Handle create project configuration button click."""
        self._create_config_and_open(self.project_config_path, "Project")

    def on_cancel(self):
        """Handle cancel button click."""
        self.exit_code = 1
        self.root.destroy()

    def _open_editor(self, file_path: Path):
        """Open file in default editor."""
        try:
            if sys.platform == 'win32':
                os.startfile(str(file_path))
            elif sys.platform == 'darwin':
                subprocess.run(['open', str(file_path)], check=False)
            else:
                subprocess.run(['xdg-open', str(file_path)], check=False)
        except Exception as e:
            print(f"[WARN] Failed to open editor: {e}", file=sys.stderr)

    def run(self) -> int:
        """Run dialog and return exit code.

        Returns:
            100: User created config (retry)
            1: User cancelled
        """
        self.root.mainloop()
        return self.exit_code


def main():
    """Command line entry point."""
    parser = argparse.ArgumentParser(description="Configuration file missing check UI")
    parser.add_argument('--project-root', required=True, help='Project root directory')

    args = parser.parse_args()
    project_root = Path(args.project_root)

    dialog = ConfigCheckDialog(project_root)
    exit_code = dialog.run()

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
