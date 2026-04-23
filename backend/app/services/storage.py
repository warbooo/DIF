from __future__ import annotations

import secrets
from pathlib import Path

from ..core.settings import settings, storage_root


def init_storage() -> None:
    root = storage_root()
    root.mkdir(parents=True, exist_ok=True)
    (root / "uploads").mkdir(parents=True, exist_ok=True)
    (root / "results").mkdir(parents=True, exist_ok=True)
    (root / "exports").mkdir(parents=True, exist_ok=True)


def new_task_id() -> str:
    # 用于前端回传/轮询时的标识（同时作为文件名的一部分）
    return secrets.token_hex(16)


def save_upload_bytes(data: bytes, filename: str, user_id: Optional[int] = None) -> Path:
    root = storage_root()
    uploads_dir = root / "uploads"
    if user_id is not None:
        uploads_dir = uploads_dir / str(user_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(filename).suffix.lower()
    safe_suffix = suffix if suffix and len(suffix) <= 10 else ".bin"
    name = new_task_id() + safe_suffix
    path = uploads_dir / name
    path.write_bytes(data)
    return path


def save_result_image_bytes(data: bytes, task_id: str, user_id: Optional[int] = None, filename: str = "result.png") -> Path:
    root = storage_root()
    results_dir = root / "results"
    if user_id is not None:
        results_dir = results_dir / str(user_id)
    results_dir.mkdir(parents=True, exist_ok=True)
    path = results_dir / f"{task_id}_{filename}"
    path.write_bytes(data)
    # 返回相对于 storage_root 的相对路径
    rel_path = path.relative_to(root)
    return rel_path

