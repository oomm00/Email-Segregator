import asyncio
import logging
from io import BytesIO

from minio import Minio
from minio.error import S3Error

from src.common.config import settings

logger = logging.getLogger(__name__)


class AttachmentStorage:
    def __init__(self) -> None:
        self.client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
            region=settings.minio_region,
        )
        self.bucket = settings.minio_bucket

    async def ensure_bucket(self) -> None:
        exists = await asyncio.to_thread(self.client.bucket_exists, self.bucket)
        if not exists:
            await asyncio.to_thread(self.client.make_bucket, self.bucket)
            logger.info("created bucket", bucket=self.bucket)

    async def upload(self, path: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        await asyncio.to_thread(
            self.client.put_object,
            self.bucket,
            path,
            BytesIO(data),
            len(data),
            content_type=content_type,
        )
        return path

    async def download(self, path: str) -> bytes:
        response = await asyncio.to_thread(self.client.get_object, self.bucket, path)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    async def delete(self, path: str) -> None:
        await asyncio.to_thread(self.client.remove_object, self.bucket, path)

    async def exists(self, path: str) -> bool:
        try:
            await asyncio.to_thread(self.client.stat_object, self.bucket, path)
            return True
        except S3Error:
            return False

    async def health(self) -> bool:
        try:
            await asyncio.to_thread(self.client.list_buckets)
            return True
        except Exception:
            return False


storage = AttachmentStorage()
