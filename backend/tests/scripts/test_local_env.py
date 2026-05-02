import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.local_env import load_local_env


def test_load_local_env_reads_selected_keys_from_dotenv(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "FIRST=alpha\nSECOND=\"two words\"\nINLINE=value # comment\nIGNORED=skip\n",
        encoding="utf-8",
    )
    for key in ("FIRST", "SECOND", "INLINE"):
        monkeypatch.delenv(key, raising=False)

    loaded = load_local_env(keys=["FIRST", "SECOND", "INLINE"], env_path=env_path)

    assert loaded == {
        "FIRST": "alpha",
        "SECOND": "two words",
        "INLINE": "value",
    }
    assert os.environ["FIRST"] == "alpha"
    assert os.environ["SECOND"] == "two words"
    assert os.environ["INLINE"] == "value"


def test_load_local_env_preserves_existing_values_without_override(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text("FIRST=from-file\n", encoding="utf-8")
    monkeypatch.setenv("FIRST", "already-set")

    loaded = load_local_env(keys=["FIRST"], env_path=env_path)

    assert loaded == {"FIRST": "already-set"}
    assert os.environ["FIRST"] == "already-set"


def test_load_local_env_can_override_existing_values(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text("FIRST=from-file\n", encoding="utf-8")
    monkeypatch.setenv("FIRST", "already-set")

    loaded = load_local_env(keys=["FIRST"], env_path=env_path, override=True)

    assert loaded == {"FIRST": "from-file"}
    assert os.environ["FIRST"] == "from-file"