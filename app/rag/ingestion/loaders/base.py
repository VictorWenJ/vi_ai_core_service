"""文档加载器基础抽象。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass
class LoadedDocument:
    # 加载后的正文文本内容。
    text: str
    # 加载后的文档标题；为空时由上层回退到文件名。
    title: str | None = None
    # 文档来源类型标记（如 text_file / markdown_file / pdf_file）。
    source_type: str = "raw_text"
    # 文档来源 URI；通常为文件绝对路径字符串。
    origin_uri: str | None = None
    # 原始文件名。
    file_name: str | None = None
    # loader 产出的附加元数据快照。
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseDocumentLoader(Protocol):
    """文档加载器协议。"""

    def load(self, file_path: str | Path) -> LoadedDocument:
        """加载文件并返回内部标准化文档对象。"""

