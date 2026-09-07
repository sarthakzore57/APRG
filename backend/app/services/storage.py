from pathlib import Path
from fastapi import UploadFile

from app.core.config import get_settings
from app.core.security import assert_inside, safe_filename


class StorageService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_path = self.settings.storage_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def validate_upload(self, upload: UploadFile, size: int) -> None:
        extension = Path(upload.filename or "").suffix.lower()
        if extension not in self.settings.upload_extensions:
            raise ValueError(f"File type {extension or '(none)'} is not allowed")
        if size > self.settings.max_upload_mb * 1024 * 1024:
            raise ValueError(f"File exceeds {self.settings.max_upload_mb} MB limit")

    async def save_upload(self, upload: UploadFile, folder: str) -> tuple[str, int]:
        data = await upload.read()
        self.validate_upload(upload, len(data))
        directory = self.base_path / folder
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / safe_filename(upload.filename or "upload")
        assert_inside(self.base_path, path)
        path.write_bytes(data)
        return str(path.relative_to(self.base_path)), len(data)

    def write_bytes(self, data: bytes, folder: str, filename: str) -> tuple[str, int]:
        directory = self.base_path / folder
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / safe_filename(filename)
        assert_inside(self.base_path, path)
        path.write_bytes(data)
        return str(path.relative_to(self.base_path)), len(data)

    def path_for(self, key: str) -> Path:
        path = self.base_path / key
        assert_inside(self.base_path, path)
        return path

    def restore_if_missing(self, key: str, data: bytes | None) -> Path:
        path = self.path_for(key)
        if not path.exists() and data:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        return path
