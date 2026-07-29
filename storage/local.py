import os

from .base import StorageBackend


class LocalStorage(StorageBackend):
    """本地文件系统存储实现"""

    def __init__(self, storage_path: str = "./storage") -> None:
        self._path = os.path.abspath(storage_path)
        os.makedirs(self._path, exist_ok=True)

    def _file_path(self, file_id: str) -> str:
        return os.path.join(self._path, file_id)

    def save(self, file_id: str, data: bytes) -> None:
        with open(self._file_path(file_id), "wb") as f:
            f.write(data)

    def get_url(self, file_id: str, expires: int = 300) -> str | None:
        # 本地模式不使用签名 URL，返回 None 交由 app.py 用 send_file
        return None

    def delete(self, file_id: str) -> None:
        path = self._file_path(file_id)
        if os.path.exists(path):
            os.remove(path)

    def get_data(self, file_id: str) -> bytes | None:
        path = self._file_path(file_id)
        if not os.path.exists(path):
            return None
        with open(path, "rb") as f:
            return f.read()