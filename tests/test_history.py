"""Persistent local sidebar vault (no external storage)."""
from __future__ import annotations

import pytest
from stegoshield import history


@pytest.fixture
def sandbox_vault(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "ROOT", tmp_path)
    monkeypatch.setattr(history, "INDEX", tmp_path / "index.json")
    return tmp_path


def test_save_load_and_clear(sandbox_vault):
    data = b"fake encoded stego file contents"
    entry = history.save_history(data, display_name="stego_image.png", fmt="Image", mime="image/png")
    assert len(history.list_history()) == 1
    saved_entry, raw = history.load_history(entry["id"])
    assert saved_entry["name"] == "stego_image.png"
    assert raw == data
    history.clear_history()
    assert history.list_history() == []
    assert list(sandbox_vault.glob("*.png")) == []


def test_history_survives_new_list_calls(sandbox_vault):
    history.save_history(b"some audio", display_name="test.wav", fmt="Audio", mime="audio/wav")
    assert len(history.list_history()) == 1
    assert len(history.list_history()) == 1


def test_limits_and_cleans_old_files(sandbox_vault):
    for i in range(11):
        history.save_history(str(i).encode(), display_name=f"sample_{i}.txt", fmt="Text", mime="text/plain")
    assert len(history.list_history()) == 8
    assert len(list(sandbox_vault.glob("*.txt"))) == 8
    assert history.list_history()[0]["name"] == "sample_10.txt"


def test_invalid_history_id_is_rejected(sandbox_vault):
    history.save_history(b"x", display_name="safe.png", fmt="Image", mime="image/png")
    with pytest.raises(history.HistoryError):
        history.load_history("../../README.md")


def test_large_file_rejected_without_writing(sandbox_vault, monkeypatch):
    monkeypatch.setattr(history, "MAX_ITEM_BYTES", 4)
    with pytest.raises(history.HistoryError):
        history.save_history(b"12345", display_name="large.png", fmt="Image", mime="image/png")
    assert not list(sandbox_vault.glob("*.png"))
