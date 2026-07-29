from abc import ABC, abstractmethod


class StorageBackend(ABC):
    """存储后端抽象接口"""

    @abstractmethod
    def save(self, file_id: str, data: bytes) -> None:
        """保存文件"""
        ...

    @abstractmethod
    def get_url(self, file_id: str, expires: int = 300) -> str | None:
        """获取文件下载 URL。

        Args:
            file_id: 文件 ID
            expires: URL 过期时间（秒），仅 OSS 模式有效

        Returns:
            下载 URL 字符串，若返回 None 则使用本地 send_file 方式
        """
        ...

    @abstractmethod
    def delete(self, file_id: str) -> None:
        """删除文件"""
        ...

    @abstractmethod
    def get_data(self, file_id: str) -> bytes | None:
        """获取文件内容（用于本地模式直接下载）。
        
        OSS 模式可以返回 None，下载通过 get_url 实现。
        """
        ...