from pathlib import Path

from fastapi import HTTPException


def resolve_safe_path(
    folders: list[str],
    filename: str,
    suffix: str = "",
) -> Path:
    for folder in folders:
        base = Path(folder).resolve()
        file_path = (base / f"{filename}{suffix}").resolve()

        if file_path.is_file() and file_path.is_relative_to(base):
            return file_path

    raise HTTPException(status_code=404, detail="File not found")
