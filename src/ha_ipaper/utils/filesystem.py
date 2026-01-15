from pathlib import Path

from fastapi import HTTPException


def resolve_safe_path(base_folder: str, filename: str, suffix: str = "") -> Path:
    """Resolve and validate a file path is within the base folder."""
    base = Path(base_folder).resolve()
    file_path = (base / f"{filename}{suffix}").resolve()

    if not file_path.is_file() or not file_path.is_relative_to(base):
        raise HTTPException(status_code=404, detail="File not found")
    return file_path
