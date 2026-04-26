import os
import shutil

from clipboard_helpers import ClipboardManager, OperationHistory


def test_clipboard_copy_cut_clear():
    clipboard = ClipboardManager()

    assert not clipboard.has_items()

    clipboard.copy(["/tmp/a.txt", "/tmp/b.txt"])
    assert clipboard.has_items()
    assert clipboard.operation == "copy"
    assert clipboard.items == ["/tmp/a.txt", "/tmp/b.txt"]

    clipboard.cut(["/tmp/c.txt"])
    assert clipboard.operation == "cut"
    assert clipboard.items == ["/tmp/c.txt"]

    clipboard.clear()
    assert not clipboard.has_items()
    assert clipboard.operation == ""


def test_clipboard_copy_file(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("hello", encoding="utf-8")
    destination = tmp_path / "destination"
    destination.mkdir()

    clipboard = ClipboardManager()
    clipboard.copy([str(source)])

    results = clipboard.paste(str(destination))

    copied = destination / "source.txt"
    assert results == [(str(source), str(copied))]
    assert copied.read_text(encoding="utf-8") == "hello"
    assert clipboard.has_items()
    assert clipboard.last_errors == []


def test_clipboard_cut_file_clears_clipboard(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("hello", encoding="utf-8")
    destination = tmp_path / "destination"
    destination.mkdir()

    clipboard = ClipboardManager()
    clipboard.cut([str(source)])

    results = clipboard.paste(str(destination))

    moved = destination / "source.txt"
    assert results == [(str(source), str(moved))]
    assert moved.exists()
    assert not source.exists()
    assert not clipboard.has_items()


def test_clipboard_name_conflict(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("new", encoding="utf-8")
    destination = tmp_path / "destination"
    destination.mkdir()
    (destination / "source.txt").write_text("existing", encoding="utf-8")

    clipboard = ClipboardManager()
    clipboard.copy([str(source)])

    results = clipboard.paste(str(destination))

    copied = destination / "source (1).txt"
    assert results == [(str(source), str(copied))]
    assert copied.read_text(encoding="utf-8") == "new"


def test_clipboard_copy_directory(tmp_path):
    source = tmp_path / "folder"
    source.mkdir()
    (source / "file.txt").write_text("nested", encoding="utf-8")
    destination = tmp_path / "destination"
    destination.mkdir()

    clipboard = ClipboardManager()
    clipboard.copy([str(source)])

    results = clipboard.paste(str(destination))

    copied = destination / "folder"
    assert results == [(str(source), str(copied))]
    assert (copied / "file.txt").read_text(encoding="utf-8") == "nested"


def test_clipboard_missing_source_is_ignored(tmp_path):
    clipboard = ClipboardManager()
    clipboard.copy([str(tmp_path / "missing.txt")])

    assert clipboard.paste(str(tmp_path)) == []
    assert clipboard.last_errors == []


def test_clipboard_records_paste_errors(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("hello", encoding="utf-8")
    missing_destination = tmp_path / "missing" / "child"

    clipboard = ClipboardManager()
    clipboard.copy([str(source)])

    assert clipboard.paste(str(missing_destination)) == []
    assert len(clipboard.last_errors) == 1
    assert clipboard.last_errors[0][0] == str(source)


def test_operation_history_record_undo_redo():
    history = OperationHistory(max_size=5)

    assert not history.can_undo()
    assert not history.can_redo()

    history.record("paste", items=[("a", "b")])
    assert history.can_undo()

    op = history.undo()
    assert op == {"op": "paste", "items": [("a", "b")]}
    assert history.can_redo()

    assert history.redo() == op
    assert history.can_undo()


def test_operation_history_max_size_and_redo_clear():
    history = OperationHistory(max_size=2)

    history.record("one")
    history.record("two")
    history.record("three")

    assert [op["op"] for op in history.undo_stack] == ["two", "three"]

    assert history.undo()["op"] == "three"
    assert history.can_redo()

    history.record("four")
    assert not history.can_redo()
    assert [op["op"] for op in history.undo_stack] == ["two", "four"]
