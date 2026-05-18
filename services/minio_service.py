# services/minio_service.py
"""MinIO 对象存储服务封装"""
import os
import logging
from datetime import timedelta
from minio import Minio
from minio.error import S3Error
from core.config import settings

logger = logging.getLogger(__name__)


class MinIOService:
    def __init__(self):
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=False,
        )
        self.bucket = settings.minio_bucket_name
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                logger.info(f"MinIO bucket 已创建: {self.bucket}")
            else:
                logger.info(f"MinIO bucket 已存在: {self.bucket}")
        except S3Error as e:
            logger.error(f"MinIO bucket 创建失败: {e}")
            raise

    def upload_file(self, file_path: str, object_name: str = None) -> str:
        """上传文件到 MinIO，返回 object_name"""
        if object_name is None:
            object_name = os.path.basename(file_path)
        try:
            self.client.fput_object(
                self.bucket, object_name, file_path,
                content_type=self._guess_content_type(object_name),
            )
            logger.info(f"MinIO 上传成功: {object_name}")
            return object_name
        except S3Error as e:
            logger.error(f"MinIO 上传失败: {e}")
            raise

    def download_to_file(self, object_name: str, dest_path: str):
        """从 MinIO 下载文件到本地路径"""
        try:
            self.client.fget_object(self.bucket, object_name, dest_path)
            logger.info(f"MinIO 下载成功: {object_name} -> {dest_path}")
        except S3Error as e:
            logger.error(f"MinIO 下载失败: {e}")
            raise

    def get_presigned_url(self, object_name: str, expires: timedelta = timedelta(hours=1)) -> str:
        """获取预签名下载 URL"""
        try:
            return self.client.presigned_get_object(
                self.bucket, object_name, expires=expires
            )
        except S3Error as e:
            logger.error(f"MinIO 预签名 URL 生成失败: {e}")
            raise

    def list_files(self) -> list[dict]:
        """列出 bucket 中所有文件"""
        files = []
        try:
            objects = self.client.list_objects(self.bucket, recursive=True)
            for obj in objects:
                files.append({
                    "filename": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified.isoformat() if obj.last_modified else "",
                })
            files.sort(key=lambda x: x["last_modified"], reverse=True)
        except S3Error as e:
            logger.error(f"MinIO 列出文件失败: {e}")
        return files

    def delete_file(self, object_name: str):
        """删除文件"""
        try:
            self.client.remove_object(self.bucket, object_name)
            logger.info(f"MinIO 删除成功: {object_name}")
        except S3Error as e:
            logger.error(f"MinIO 删除失败: {e}")
            raise

    def file_exists(self, object_name: str) -> bool:
        """检查文件是否存在"""
        try:
            self.client.stat_object(self.bucket, object_name)
            return True
        except S3Error:
            return False

    @staticmethod
    def _guess_content_type(filename: str) -> str:
        ext = os.path.splitext(filename)[1].lower()
        return {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".csv": "text/csv",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".html": "text/html",
        }.get(ext, "application/octet-stream")


# 全局实例
minio_service = MinIOService()
