"""整个项目的统一编码检测工具。

此模块提供智能编码检测，支持字节流和文件，
支持多语言内容（UTF-8, GBK, GB18030）和BOM处理。
"""

from pathlib import Path
from typing import List


class EncodingDetector:
    """字节和文件的智能编码检测。"""

    # Standard encodings (no BOM)
    STANDARD_ENCODINGS: List[str] = ['utf-8', 'gbk', 'gb18030']

    # Encodings with BOM support (for external files)
    ENCODINGS_WITH_BOM: List[str] = ['utf-8', 'utf-8-sig', 'gbk', 'gb18030']

    @staticmethod
    def decode_bytes(data: bytes, support_bom: bool = False) -> str:
        """智能解码字节流，自动检测编码。

        此方法在严格模式下尝试多种编码，返回第一个成功解码的结果。
        如果所有编码都失败，则回退到UTF-8并使用errors='replace'，
        确保函数永不抛出异常。

        使用场景：实时stdout/stderr流处理，数据完整性重要但失败不应导致工作流崩溃。

        Args:
            data: 要解码的字节流
            support_bom: 如果为True，尝试UTF-8-BOM编码（默认：False）

        Returns:
            解码后的字符串（UTF-8兼容）

        Example:
            >>> line = b'\xe4\xb8\xad\xe6\x96\x87'  # UTF-8编码的"中文"
            >>> EncodingDetector.decode_bytes(line)
            '中文'
        """
        if not data:
            return ""

        encodings = (EncodingDetector.ENCODINGS_WITH_BOM if support_bom
                    else EncodingDetector.STANDARD_ENCODINGS)

        # Phase 1: Try each encoding in strict mode
        for encoding in encodings:
            try:
                return data.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                continue  # Try next encoding

        # Phase 2: All encodings failed, use fallback with replacement
        # This ensures we never lose data even with corrupted/mixed encodings
        return data.decode('utf-8', errors='replace')

    @staticmethod
    def read_file(file_path: Path, support_bom: bool = False) -> str:
        """智能文件读取，自动检测编码。

        此方法在严格模式下尝试多种编码，如果所有尝试都失败则抛出异常。
        这确保文件读取错误是明确的和可追溯的。

        使用场景：读取配置文件或用户提供的文件，编码错误应报告给调用者。

        Args:
            file_path: 要读取的文件路径
            support_bom: 如果为True，尝试UTF-8-BOM编码（默认：False）

        Returns:
            文件内容字符串

        Raises:
            FileNotFoundError: 如果文件不存在
            UnicodeDecodeError: 如果文件无法用任何支持的编码解码

        Example:
            >>> path = Path("review-request.md")
            >>> content = EncodingDetector.read_file(path, support_bom=True)
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        encodings = (EncodingDetector.ENCODINGS_WITH_BOM if support_bom
                    else EncodingDetector.STANDARD_ENCODINGS)
        last_error = None

        # Try each encoding in strict mode
        for encoding in encodings:
            try:
                content = file_path.read_text(encoding=encoding)
                # Explicitly remove BOM if present (utf-8-sig should handle this but doesn't always)
                if content and content[0] == '\ufeff':
                    content = content[1:]
                return content
            except (UnicodeDecodeError, LookupError) as e:
                last_error = e
                continue

        # All encodings failed: raise descriptive error
        raise UnicodeDecodeError(
            'multiple',
            b'',
            0,
            1,
            f"File {file_path} cannot be decoded with any of {encodings}. "
            f"Last error: {last_error}"
        )
