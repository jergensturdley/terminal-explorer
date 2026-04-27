import os
import sys

import pytest

explorer = pytest.importorskip("explorer")


def test_explorer_app_instantiates():
    app = explorer.ExplorerApp()
    assert app is not None
    assert app.title is not None


def test_file_pane_format_size_without_mount():
    pane = explorer.FilePane()

    assert pane.format_size(0) == "0.0 B"
    assert pane.format_size(512) == "512.0 B"
    assert pane.format_size(1024) == "1.0 KB"
    assert pane.format_size(1024 * 1024) == "1.0 MB"


def test_file_pane_hidden_detection_for_dotfile(tmp_path):
    pane = explorer.FilePane()
    hidden_file = tmp_path / ".env"
    hidden_file.write_text("secret", encoding="utf-8")

    with os.scandir(tmp_path) as entries:
        entry = next(entries)
        assert pane.is_hidden(entry)


def test_input_screen_stores_values():
    screen = explorer.InputScreen("Prompt", initial_value="value", placeholder="placeholder")

    assert screen.prompt == "Prompt"
    assert screen.initial_value == "value"
    assert screen.placeholder == "placeholder"


def test_properties_screen_stores_path(tmp_path):
    path = tmp_path / "file.txt"
    path.write_text("hello", encoding="utf-8")

    screen = explorer.PropertiesScreen(str(path))

    assert screen.path == str(path)


def test_context_menu_stores_items_and_coordinates():
    items = [("open", "Open", "default"), ("delete", "Delete", "error")]
    menu = explorer.ContextMenu(items, 10, 20)

    assert menu.items == items
    assert menu.x == 10
    assert menu.y == 20


def test_open_with_common_apps():
    text_screen = explorer.OpenWithScreen("example.txt")
    image_screen = explorer.OpenWithScreen("example.png")
    pdf_screen = explorer.OpenWithScreen("example.pdf")

    text_apps = {app_id for app_id, _, _ in text_screen.get_common_apps()}
    image_apps = {app_id for app_id, _, _ in image_screen.get_common_apps()}
    pdf_apps = {app_id for app_id, _, _ in pdf_screen.get_common_apps()}

    if os.name == "nt":
        assert "notepad" in text_apps
        assert "paint" in image_apps
        assert "edge" in pdf_apps
    elif sys.platform == "darwin":
        assert "textedit" in text_apps
        assert "preview" in image_apps
        assert "preview" in pdf_apps
    else:
        assert "vscode" in text_apps


def test_bindings_include_recent_navigation_shortcuts():
    actions = {binding.action for binding in explorer.ExplorerApp.BINDINGS}

    assert "toggle_hidden" in actions
    assert "refresh" in actions
    assert "back" in actions
    assert "forward" in actions
