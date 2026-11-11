import pytest
from fastapi import HTTPException

from ha_ipaper.utils.filesystem import resolve_safe_path


@pytest.fixture
def folders(tmp_path):
    """Two template folders: 'custom' overrides 'default'."""
    custom = tmp_path / "custom"
    default = tmp_path / "default"
    (custom / "components").mkdir(parents=True)
    (default / "components").mkdir(parents=True)
    (custom / "style.css").write_text("custom")
    (default / "style.css").write_text("default")
    (default / "index.html").write_text("default")
    (default / "components" / "lights.html").write_text("default")
    (tmp_path / "secret.txt").write_text("secret")
    return [str(custom), str(default)]


def test_first_folder_wins(folders):
    assert resolve_safe_path(folders, "style.css").read_text() == "custom"


def test_falls_back_to_next_folder(folders):
    assert resolve_safe_path(folders, "index", ".html").read_text() == "default"
    assert resolve_safe_path(folders, "components/lights.html").read_text() == "default"


@pytest.mark.parametrize("filename", ["missing.html", "components", "../secret.txt", "components/../../secret.txt"])
def test_missing_directory_or_outside_is_404(folders, filename):
    with pytest.raises(HTTPException) as exc:
        resolve_safe_path(folders, filename)
    assert exc.value.status_code == 404
