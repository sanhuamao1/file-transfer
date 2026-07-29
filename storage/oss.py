import os

from .base import StorageBackend


class OSSStorage(StorageBackend):
    """阿里云 OSS 存储实现"""

    def __init__(self) -> None:
        import oss2

        key_id = os.environ["OSS_ACCESS_KEY_ID"]
        key_secret = os.environ["OSS_ACCESS_KEY_SECRET"]
        bucket_name = os.environ["OSS_BUCKET_NAME"]
        endpoint = os.environ["OSS_ENDPOINT"]

        auth = oss2.Auth(key_id, key_secret)
        self._bucket = oss2.Bucket(auth, endpoint, bucket_name)

    def save(self, file_id: str, data: bytes) -> None:
        self._bucket.put_object(file_id, data)

    def get_url(self, file_id: str, expires: int = 300) -> str | None:
        return self._bucket.sign_url("GET", file_id, expires)

    def delete(self, file_id: str) -> None:
        self._bucket.delete_object(file_id)

    def get_data(self, file_id: str) -> bytes | None:
        try:
            obj = self._bucket.get_object(file_id)
            return obj.read()
        except:
            return None
