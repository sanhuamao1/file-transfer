import os
from .base import StorageBackend
from .local import LocalStorage
from .oss import OSSStorage


def create_storage(backend: str = None) -> StorageBackend:
    """创建存储后端实例。

    策略：
      1. 显式指定 backend 优先
      2. 读取环境变量 STORAGE_BACKEND
      3. 自动检测 OSS 凭据是否完整，完整则用 OSS，否则降级为本地存储

    Args:
        backend: 存储模式，'local' 或 'oss'。

    Returns:
        StorageBackend 实例
    """
    mode = backend or os.environ.get("STORAGE_BACKEND")

    if mode == "local":
        path = os.environ.get("LOCAL_STORAGE_PATH", "./storage")
        return LocalStorage(path)

    if mode == "oss":
        return OSSStorage()

    # 未显式指定：自动检测 OSS 凭据是否完整
    oss_keys = ("OSS_ACCESS_KEY_ID", "OSS_ACCESS_KEY_SECRET", "OSS_BUCKET_NAME", "OSS_ENDPOINT")
    if all(k in os.environ for k in oss_keys):
        return OSSStorage()

    # OSS 凭据不全 → 自动降级到本地存储
    path = os.environ.get("LOCAL_STORAGE_PATH", "./storage")
    return LocalStorage(path)
