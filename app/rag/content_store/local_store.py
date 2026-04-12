"""本地文件系统内容存储实现。"""

from __future__ import annotations

from pathlib import Path
import shutil


class LocalRAGContentStore:
    """用于保存原始文件与 normalized text 快照的本地存储。"""

    def __init__(self, *, root_path: str | Path) -> None:
        self._root_path = Path(root_path).resolve()
        self._root_path.mkdir(parents=True, exist_ok=True)

    @property
    def root_path(self) -> Path:
        """返回内容存储根目录。"""
        return self._root_path

    def save_raw_file(
        self,
        *,
        document_id: str,
        version_id: str,
        raw_bytes: bytes,
    ) -> str:
        """保存原始文件并返回相对存储路径。"""
        relative_path = Path("raw") / document_id / version_id / "source.bin"
        absolute_path = self._root_path / relative_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_path.write_bytes(raw_bytes)
        return relative_path.as_posix()

    def save_normalized_text(
        self,
        *,
        document_id: str,
        version_id: str,
        normalized_text: str,
    ) -> str:
        """保存 normalized 文本并返回相对存储路径。"""
        relative_path = Path("normalized") / document_id / version_id / "normalized.txt"
        absolute_path = self._root_path / relative_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_path.write_text(normalized_text, encoding="utf-8")
        return relative_path.as_posix()

    def read_raw_file(self, *, storage_path: str) -> bytes:
        """读取原始文件字节内容。"""
        return self._resolve_absolute_path(storage_path).read_bytes()

    def read_normalized_text(self, *, storage_path: str) -> str:
        """读取 normalized 文本内容。"""
        return self._resolve_absolute_path(storage_path).read_text(encoding="utf-8")

    def delete_version_files(self, *, document_id: str, version_id: str) -> None:
        """删除指定文档版本对应的原始与 normalized 内容。"""
        raw_dir = self._root_path / "raw" / document_id / version_id
        normalized_dir = self._root_path / "normalized" / document_id / version_id
        if raw_dir.exists():
            shutil.rmtree(raw_dir, ignore_errors=True)
        if normalized_dir.exists():
            shutil.rmtree(normalized_dir, ignore_errors=True)

    def _resolve_absolute_path(self, storage_path: str) -> Path:
        normalized_path = storage_path.strip().replace("\\", "/")
        if not normalized_path:
            raise ValueError("storage_path 不能为空。")
        absolute_path = (self._root_path / normalized_path).resolve()
        if not str(absolute_path).startswith(str(self._root_path)):
            raise ValueError("storage_path 非法，超出内容存储根目录。")
        return absolute_path

