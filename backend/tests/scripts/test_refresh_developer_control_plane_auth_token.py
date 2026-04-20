from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.refresh_developer_control_plane_auth_token import mask_token, update_env_file


def test_update_env_file_replaces_existing_token_line(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "BIJMANTRA_DEVELOPER_CONTROL_PLANE_BASE_URL=http://127.0.0.1:8000\n"
        "BIJMANTRA_DEVELOPER_CONTROL_PLANE_AUTH_TOKEN=old-token\n",
        encoding="utf-8",
    )

    update_env_file(
        env_path=env_path,
        key="BIJMANTRA_DEVELOPER_CONTROL_PLANE_AUTH_TOKEN",
        value="new-token",
    )

    assert env_path.read_text(encoding="utf-8").splitlines() == [
        "BIJMANTRA_DEVELOPER_CONTROL_PLANE_BASE_URL=http://127.0.0.1:8000",
        "BIJMANTRA_DEVELOPER_CONTROL_PLANE_AUTH_TOKEN=new-token",
    ]


def test_mask_token_hides_middle_characters():
    masked = mask_token("abcdefghijklmnopqrstuvwxyz")

    assert masked.startswith("abcdefgh...")
    assert masked.endswith("uvwxyz")