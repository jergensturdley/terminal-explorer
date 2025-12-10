import subprocess
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, DirectoryTree, DataTable, Static, Label, Input, Button, ListItem, ListView, Tree, RichLog
from textual.widgets.tree import TreeNode
from textual.screen import ModalScreen, Screen
from textual.binding import Binding
from textual import events
from textual.message import Message
import os
import shutil
import datetime
import send2trash
from clipboard_helpers import ClipboardManager, OperationHistory

class ResizeHandle(Static):
    def __init__(self, target_id: str, vertical: bool = False, **kwargs):
        super().__init__("", **kwargs)
        self.target_id = target_id
        self.vertical = vertical
        self.dragging = False

    def on_mouse_down(self, event: events.MouseDown) -> None:
        self.capture_mouse()
        self.dragging = True

    def on_mouse_up(self, event: events.MouseUp) -> None:
        self.release_mouse()
        self.dragging = False

    def on_mouse_move(self, event: events.MouseMove) -> None:
        if not self.dragging: return
        target = self.app.query_one(f"#{self.target_id}")
        if self.vertical:
            new_height = self.app.size.height - event.screen_y
            if new_height > 5:
                target.styles.height = new_height
        else:
            if event.screen_x > 5:
                target.styles.width = event.screen_x

class InputScreen(ModalScreen[str]):
    def __init__(self, prompt: str, initial_value: str = "", placeholder: str = ""):
        super().__init__()
        self.prompt = prompt
        self.initial_value = initial_value
        self.placeholder = placeholder

    def compose(self) -> ComposeResult:
        yield Container(
            Label(self.prompt),
            Input(value=self.initial_value, placeholder=self.placeholder),
            Horizontal(
                Button("OK", variant="primary", id="ok"),
                Button("Cancel", variant="default", id="cancel"),
                classes="buttons"
            ),
            id="input_dialog"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            self.dismiss(self.query_one(Input).value)
        else:
            self.dismiss(None)

class PropertiesScreen(ModalScreen):
    def __init__(self, path: str):
        super().__init__()
        self.path = path

    def compose(self) -> ComposeResult:
        stats = os.stat(self.path)
        created = datetime.datetime.fromtimestamp(stats.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
        modified = datetime.datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        size = f"{stats.st_size:,} bytes"
        
        yield Container(
            Label(f"Properties: {os.path.basename(self.path)}", classes="title"),
            Label(f"Path: {self.path}"),
            Label(f"Size: {size}"),
            Label(f"Created: {created}"),
            Label(f"Modified: {modified}"),
            Button("Close", id="close", variant="primary"),
            id="properties_dialog"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()

class SystemTree(Tree[dict]):
    def __init__(self):
        super().__init__("Root")
        self.show_root = False
        self.guide_depth = 2

    def on_mount(self) -> None:
        favorites = self.root.add("⭐ Favorites", expand=True) 
        home = os.path.expanduser("~")
        
        common_paths = {
            "Home": home,
            "Desktop": os.path.join(home, "Desktop"),
            "Documents": os.path.join(home, "Documents"),
            "Downloads": os.path.join(home, "Downloads"),
        }
        
        for name, path in common_paths.items():
            if os.path.exists(path):
                icon = "🏠" if name=="Home" else "📁"
                favorites.add(f"{icon} {name}", data={"path": path, "is_dir": True, "loaded": False}, allow_expand=True)

        drives = self.root.add("DISK Drives", expand=True)
        available_drives = ["C:\\"]
        
        import string
        for letter in string.ascii_uppercase:
            if letter == "C": continue
            path = f"{letter}:\\"
            if os.path.exists(path):
                available_drives.append(path)
                
        for drive in available_drives:
            drives.add(f"💾 {drive}", data={"path": drive, "is_dir": True, "loaded": False}, allow_expand=True)

    def on_tree_node_expanded(self, event: Tree.NodeExpanded) -> None:
        node = event.node
        if node.data and not node.data.get("loaded", False):
            self._load_directory(node)

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        if not event.node.data:
            event.stop()

    def _load_directory(self, node: TreeNode) -> None:
        if not node.data or not node.data.get("path"): return
        path = node.data["path"]
        node.remove_children() 
        try:
            entries = list(os.scandir(path))
            entries.sort(key=lambda e: (not e.is_dir(), e.name.lower()))
            for entry in entries:
                if entry.is_dir():
                    node.add(f"📁 {entry.name}", data={"path": entry.path, "is_dir": True, "loaded": False}, allow_expand=True)
            node.data["loaded"] = True
        except PermissionError:
            pass

    def on_click(self, event: events.Click) -> None:
        if event.button == 3: 
            if self.cursor_node and self.cursor_node.data:
                 self.show_context_menu(event.screen_x, event.screen_y)

    def show_context_menu(self, x: int, y: int) -> None:
        def handle_action(action: str | None) -> None:
            if action == "open":
                if self.cursor_node: self.cursor_node.expand()
            elif action == "copy":
                 if self.cursor_node and self.cursor_node.data:
                    path = self.cursor_node.data.get("path")
                    if path:
                        self.app.copy_to_clipboard(path)
                        self.app.notify(f"Copied: {path}")
            elif action == "term":
                 if self.cursor_node and self.cursor_node.data:
                    path = self.cursor_node.data.get("path")
                    if path:
                         self.app.action_open_external_terminal(path)

        items = [
            ("open", "Expand/Open", "default"),
            ("copy", "Copy Path", "default"),
            ("term", "Open Terminal", "default")
        ]
        self.app.push_screen(ContextMenu(items, x, y), handle_action)

class Sidebar(Container):
    def compose(self) -> ComposeResult:
        yield Label(" Drives & Folders", id="sidebar-title")
        yield SystemTree()

class Toolbar(Horizontal):
    """Enhanced toolbar with navigation and clipboard operations."""
    def compose(self) -> ComposeResult:
        yield Button("←", id="back", variant="primary", disabled=True)
        yield Button("→", id="forward", variant="primary", disabled=True)
        yield Button("↑", id="up", variant="default")
        yield Button("↻", id="refresh", variant="default")
        yield Button("📋", id="copy", variant="default", tooltip="Copy")
        yield Button("✂", id="cut", variant="default", tooltip="Cut")
        yield Button("📄", id="paste", variant="default", disabled=True, tooltip="Paste")
        yield Button("🗑", id="delete", variant="error", tooltip="Delete")
        yield Button("↶", id="undo", variant="default", disabled=True, tooltip="Undo")
        yield Button("↷", id="redo", variant="default", disabled=True, tooltip="Redo")
        yield Input(placeholder="Path...", id="address-bar")

class ContextMenu(ModalScreen[str]):
    def __init__(self, items: list[tuple[str, str, str]], x: int, y: int):
        super().__init__()
        self.items = items
        self.x = x
        self.y = y

    def compose(self) -> ComposeResult:
        with Vertical(id="context-menu") as menu:
            menu.styles.offset = (self.x, self.y)
            for action_id, label, variant in self.items:
                yield Button(label, id=action_id, variant=variant)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id)

    def on_click(self, event: events.Click) -> None:
        """Dismiss menu on any click."""
        self.dismiss(None)
    
    def on_key(self, event: events.Key) -> None:
        """Dismiss menu on any key."""
        self.dismiss(None)

class OpenWithScreen(ModalScreen[str]):
    """Modal screen for selecting an application to open a file."""
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
        self.file_ext = os.path.splitext(file_path)[1].lower()
    
    def compose(self) -> ComposeResult:
        with Vertical(id="open-with-dialog"):
            yield Label(f"Open: {os.path.basename(self.file_path)}", id="open-with-title")
            yield Label("Choose an application:", id="open-with-subtitle")
            
            apps = self.get_common_apps()
            for app_id, app_name, app_path in apps:
                yield Button(app_name, id=app_id, variant="primary")
            
            yield Button("Browse...", id="browse", variant="default")
            yield Button("Default Program", id="default", variant="default")
            yield Button("Cancel", id="cancel", variant="default")
    
    def get_common_apps(self) -> list[tuple[str, str, str]]:
        """Get common applications based on file extension."""
        apps = []
        
        if self.file_ext in ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml']:
            apps.append(("notepad", "Notepad", "notepad.exe"))
            apps.append(("vscode", "VS Code", "code"))
        
        if self.file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            apps.append(("paint", "Paint", "mspaint.exe"))
        
        if self.file_ext == '.pdf':
            apps.append(("edge", "Microsoft Edge", "msedge.exe"))
        
        return apps
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        
        if button_id == "cancel":
            self.dismiss(None)
        elif button_id == "default":
            self.dismiss("default")
        elif button_id == "browse":
            self.dismiss("browse")
        else:
            self.dismiss(button_id)

class FileList(DataTable):
    def on_mount(self) -> None:
        self.cursor_type = "row"
        self.add_columns("Name", "Size", "Date Modified", "Type")

    def on_click(self, event: events.Click) -> None:
        if event.button == 3: 
            if self.cursor_coordinate:
                self.parent.show_context_menu_for_item(event.screen_x, event.screen_y)
            else:
                self.parent.show_context_menu_empty(event.screen_x, event.screen_y)
            event.stop()
            return 

        if event.button == 1 and hasattr(event, "chain") and event.chain == 2:
            if self.cursor_coordinate:
                row_key = self.coordinate_to_cell_key(self.cursor_coordinate).row_key
                self.parent.on_file_double_clicked(row_key.value)

class FilePane(Container):
    """A self-contained file explorer pane with toolbar and list."""
    
    def compose(self) -> ComposeResult:
        yield Toolbar()
        yield FileList()

    def on_mount(self) -> None:
        self.history: list[str] = []
        self.history_index: int = -1
        self.current_path = os.getcwd()
        self.update_file_list(self.current_path)

    def on_file_double_clicked(self, path: str) -> None:
        if os.path.isdir(path):
            self.update_file_list(path)
        else:
            try:
                os.startfile(path)
                self.app.notify(f"Opened {path}")
            except Exception as e:
                self.app.notify(f"Error opening file: {e}", severity="error")

    def on_click(self, event: events.Click) -> None:
        if event.button == 3: 
            self.show_context_menu_empty(event.screen_x, event.screen_y)

    def show_context_menu_for_item(self, x: int, y: int) -> None:
        items = [
            ("open", "Open", "default"),
            ("open_with", "Open With...", "default"),
            ("copy_file", "Copy", "default"),
            ("cut_file", "Cut", "default"),
            ("paste_file", "Paste", "default"),
            ("duplicate", "Duplicate", "default"),
            ("rename", "Rename", "default"),
            ("delete", "Delete", "error"),
            ("properties", "Properties", "default"),
            ("copy_path", "Copy Path", "default"),
            ("term", "Open Terminal", "default")
        ]
        self.show_menu(items, x, y)

    def show_context_menu_empty(self, x: int, y: int) -> None:
        items = [
            ("refresh", "Refresh", "default"),
            ("paste_file", "Paste", "default"),
            ("new_file", "New File", "primary"),
            ("new_folder", "New Folder", "primary"),
            ("term_here", "Open Terminal", "default")
        ]
        self.show_menu(items, x, y)

    def show_menu(self, items, x, y):
        def handle_action(action: str | None) -> None:
            if action == "open": self.action_open_selected()
            elif action == "open_with": self.action_open_with()
            elif action == "properties": self.action_properties()
            elif action == "rename": self.action_rename_file()
            elif action == "duplicate": self.action_duplicate_file()
            elif action == "delete": self.action_delete_file()
            elif action == "copy_path": self.action_copy_path()
            elif action == "copy_file": self.app.action_copy_files()
            elif action == "cut_file": self.app.action_cut_files()
            elif action == "paste_file": self.app.action_paste_files()
            elif action == "refresh": self.update_file_list(self.current_path, add_to_history=False)
            elif action == "new_file": self.action_new_file()
            elif action == "new_folder": self.action_new_folder()
            elif action == "term_here": self.app.action_open_external_terminal(self.current_path)
            elif action == "term": 
                table = self.query_one(FileList)
                path = self.current_path
                if table.row_count:
                    try:
                        sel = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
                        if os.path.isdir(sel): path = sel
                    except: pass
                self.app.action_open_external_terminal(path)
        
        self.app.push_screen(ContextMenu(items, x, y), handle_action)

    def action_new_file(self) -> None:
        def handle_input(name: str | None) -> None:
            if name:
                try:
                    path = os.path.join(self.current_path, name)
                    with open(path, 'w') as f: pass
                    self.app.notify(f"Created file: {name}")
                    self.update_file_list(self.current_path, add_to_history=False)
                except Exception as e:
                    self.app.notify(f"Error: {e}", severity="error")
        self.app.push_screen(InputScreen("New File Name:", "new_file.txt"), handle_input)

    def action_duplicate_file(self) -> None:
        table = self.query_one(FileList)
        if not table.row_count: return
        try:
            path = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
            dirname = os.path.dirname(path)
            basename = os.path.basename(path)
            name, ext = os.path.splitext(basename)
            new_path = os.path.join(dirname, f"{name} - Copy{ext}")
            
            counter = 1
            while os.path.exists(new_path):
                new_path = os.path.join(dirname, f"{name} - Copy ({counter}){ext}")
                counter += 1
                
            if os.path.isdir(path):
                shutil.copytree(path, new_path)
            else:
                shutil.copy2(path, new_path)
                
            self.app.notify(f"Duplicated to: {os.path.basename(new_path)}")
            self.update_file_list(self.current_path, add_to_history=False)
        except Exception as e:
             self.app.notify(f"Error duplicating: {e}", severity="error")
             
    def action_properties(self) -> None:
        table = self.query_one(FileList)
        if not table.row_count: return
        try:
            path = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
            self.app.push_screen(PropertiesScreen(path))
        except: pass

    def action_new_folder(self) -> None:
        def handle_input(name: str | None) -> None:
            if name:
                try:
                    path = os.path.join(self.current_path, name)
                    os.makedirs(path, exist_ok=False)
                    self.app.notify(f"Created: {name}")
                    self.update_file_list(self.current_path, add_to_history=False)
                except Exception as e:
                    self.app.notify(f"Error: {e}", severity="error")
        
        self.app.push_screen(InputScreen("New Folder Name:", "New Folder"), handle_input)

    def action_open_selected(self) -> None:
        table = self.query_one(FileList)
        if not table.row_count: return
        try:
            path = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
            self.on_file_double_clicked(path)
        except: pass

    def action_copy_path(self) -> None:
        table = self.query_one(FileList)
        if not table.row_count: return
        try:
            path = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
            self.app.copy_to_clipboard(path)
            self.app.notify(f"Copied path: {path}")
        except: pass

    def action_delete_file(self) -> None:
        table = self.query_one(FileList)
        if not table.row_count: return
        try:
            path = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
            if os.path.exists(path):
                send2trash.send2trash(path)
                self.app.notify(f"Moved to trash: {path}")
                self.update_file_list(self.current_path, add_to_history=False)
        except Exception as e:
            self.app.notify(f"Error deleting: {e}", severity="error")
    
    def action_open_with(self) -> None:
        """Open file with selected application."""
        table = self.query_one(FileList)
        if not table.row_count:
            return
        
        try:
            path = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
            if os.path.isfile(path):
                def handle_app_choice(app_choice: str | None) -> None:
                    if app_choice:
                        self.app.open_file_with_app(path, app_choice)
                
                self.app.push_screen(OpenWithScreen(path), handle_app_choice)
        except:
            pass

    def action_rename_file(self) -> None:
        """Rename the selected file."""
        table = self.query_one(FileList)
        if not table.row_count: return
        try:
            path = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
        except: return

        def handle_rename(new_name: str | None) -> None:
            if new_name:
                try:
                    dirname = os.path.dirname(path)
                    new_path = os.path.join(dirname, new_name)
                    os.rename(path, new_path)
                    self.app.notify(f"Renamed to: {new_name}")
                    self.update_file_list(self.current_path, add_to_history=False)
                except Exception as e:
                    self.app.notify(f"Error renaming: {e}", severity="error")
        
        self.app.push_screen(InputScreen("Rename to:", os.path.basename(path)), handle_rename)

    def action_go_up(self) -> None:
        parent = os.path.dirname(self.current_path)
        if parent != self.current_path:
            self.update_file_list(parent)

    def action_open_item(self) -> None:
        self.action_open_selected()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle address bar Enter."""
        if event.input.id == "address-bar":
            path = event.value
            if os.path.exists(path) and os.path.isdir(path):
                self.update_file_list(path)
            else:
                self.app.notify(f"Invalid path: {path}", severity="error")

    def update_file_list(self, path: str, add_to_history: bool = True) -> None:
        """Update the file list with the contents of the given path."""
        if add_to_history and (not self.history or self.history[self.history_index] != path):
            if self.history_index < len(self.history) - 1:
                self.history = self.history[:self.history_index+1]
            self.history.append(path)
            self.history_index = len(self.history) - 1
            
        self.current_path = path

        try:
            self.query_one("#back", Button).disabled = self.history_index <= 0
            self.query_one("#forward", Button).disabled = self.history_index >= len(self.history) - 1
            self.query_one("#address-bar", Input).value = path
        except:
            pass 

        table = self.query_one(FileList)
        table.clear()

        try:
            entries = list(os.scandir(path))
            entries.sort(key=lambda e: (not e.is_dir(), e.name.lower()))
            
            for entry in entries:
                try:
                    stats = entry.stat()
                    size = self.format_size(stats.st_size) if entry.is_file() else ""
                    modified = datetime.datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M")
                    file_type = "Folder" if entry.is_dir() else os.path.splitext(entry.name)[1].upper()[1:] or "File"
                    icon = "📁" if entry.is_dir() else "📄"
                    
                    table.add_row(f"{icon} {entry.name}", size, modified, file_type, key=entry.path)
                except:
                    pass
        except PermissionError:
            self.app.notify(f"Permission denied: {path}", severity="error")
        except Exception as e:
            self.app.notify(f"Error reading directory: {e}", severity="error")

    def format_size(self, size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

class ExplorerApp(App):
    CSS = """
    Screen {
        layout: horizontal;
    }

    #sidebar {
        width: 30;
        height: 100%;
        background: $panel;
        border-right: vkey $accent;
        layout: vertical;
    }

    #sidebar-title {
        background: $accent;
        color: $text;
        padding: 0 1;
        width: 100%;
        text-style: bold;
        height: 1;
    }

    #tree-view {
        height: 1fr;
        width: 100%;
    }
    
    #main-content {
        width: 1fr;
        height: 100%;
        layout: vertical;
    }
    
    #dual-pane {
        width: 100%;
        height: 100%;
        layout: horizontal;
    }

    FilePane {
        width: 1fr;
        height: 100%;
        border: heavy $accent;
        margin: 0 1;
        layout: vertical;
    }
    
    FilePane:focus-within {
        border: double $primary;
    }

    Toolbar {
        height: 1;
        width: 100%;
        layout: horizontal;
        background: $surface;
        padding: 0 1;
        align-vertical: middle;
        dock: top;
    }
    
    Toolbar Button {
        min-width: 3;
        width: auto;
        margin-right: 1;
        height: 1;
        border: none;
    }

    #address-bar {
        width: 1fr;
        height: 1;
        border: none;
        background: $boost;
    }

    FileList {
        width: 100%;
        height: 1fr;
    }
    
    #input_dialog {
        layout: grid;
        grid-size: 2;
        grid-gutter: 1 2;
        grid-rows: 1fr 3 3;
        padding: 0 1;
        width: 60;
        height: 15;
        border: thick $background 80%;
        background: $surface;
        align: center middle;
    }
    
    #input_dialog Label {
        column-span: 2;
        height: 1;
        width: 100%;
        content-align: center middle;
    }
    
    #input_dialog Input {
        column-span: 2;
        width: 100%;
    }
    
    .buttons {
        column-span: 2;
        width: 100%;
        align: center middle;
    }

    #context-menu {
        width: auto;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1;
    }
    
    #context-menu Button {
        width: 100%;
        height: 1;
        border: none;
        content-align: left middle;
    }

    #properties_dialog {
        layout: vertical;
        padding: 1 2;
        width: 60;
        height: auto;
        border: thick $background 80%;
        background: $surface;
        align: center middle;
    }

    .hidden {
        display: none;
    }
    ResizeHandle {
        background: $accent;
    }
    ResizeHandle:hover {
        background: $primary;
    }
    #sidebar-handle {
        width: 1;
        height: 100%;
        dock: left;
        background: $accent;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("d", "toggle_dark", "Toggle Dark Mode"),
        Binding("backspace", "go_up", "Go Up"),
        Binding("delete", "delete_file", "Delete"),
        Binding("f2", "rename_file", "Rename"),
        Binding("enter", "open_item", "Open"),
        Binding("ctrl+d", "toggle_pane", "Dual Pane"),
        Binding("ctrl+c", "copy_files", "Copy"),
        Binding("ctrl+x", "cut_files", "Cut"),
        Binding("ctrl+v", "paste_files", "Paste"),
        Binding("ctrl+z", "undo", "Undo"),
        Binding("ctrl+y", "redo", "Redo"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            yield Sidebar(id="sidebar")
            with Container(id="main-content"):
                with Container(id="dual-pane"):
                    yield FilePane(id="left-pane")
                    yield FilePane(id="right-pane")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Terminal Explorer"
        self.file_clipboard = ClipboardManager()
        self.history = OperationHistory()

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Update the active pane when a sidebar node is clicked."""
        if not event.node.data or not event.node.data.get("path"):
            return
            
        path = event.node.data["path"]
        
        focused = self.query("FilePane:focus-within")
        if focused:
            pane = focused.first()
        else:
            pane = self.query_one("#left-pane", FilePane)
        
        pane.update_file_list(path)

    def action_delete_file(self) -> None:
        focused = self.query("FilePane:focus-within")
        if focused:
            pane = focused.first()
        else:
            try:
                pane = self.query_one("#left-pane", FilePane)
            except Exception:
                return

        pane.action_delete_file()

    def action_rename_file(self) -> None:
        focused = self.query("FilePane:focus-within")
        if focused:
            pane = focused.first()
        else:
            try:
                pane = self.query_one("#left-pane", FilePane)
            except Exception:
                return

        pane.action_rename_file()
            
    def action_go_up(self) -> None:
        focused = self.query("FilePane:focus-within")
        if focused:
            pane = focused.first()
        else:
            try:
                pane = self.query_one("#left-pane", FilePane)
            except Exception:
                return

        pane.action_go_up()

    def action_open_item(self) -> None:
        focused = self.query("FilePane:focus-within")
        if focused:
            focused.first().action_open_item()

    def action_toggle_pane(self) -> None:
        right = self.query_one("#right-pane")
        right.display = not right.display

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle toolbar button clicks."""
        button_id = event.button.id
        
        if button_id == "copy":
            self.action_copy_files()
        elif button_id == "cut":
            self.action_cut_files()
        elif button_id == "paste":
            self.action_paste_files()
        elif button_id == "delete":
            self.action_delete_file()
        elif button_id == "undo":
            self.action_undo()
        elif button_id == "redo":
            self.action_redo()
        
        self.update_toolbar_state()
    
    def update_toolbar_state(self) -> None:
        """Update toolbar button enabled/disabled states."""
        try:
            paste_btn = self.query_one("#paste", Button)
            paste_btn.disabled = not self.file_clipboard.has_items()
            
            undo_btn = self.query_one("#undo", Button)
            undo_btn.disabled = not self.history.can_undo()
            
            redo_btn = self.query_one("#redo", Button)
            redo_btn.disabled = not self.history.can_redo()
        except:
            pass
    
    def action_copy_files(self) -> None:
        """Copy selected files to clipboard."""
        focused = self.query("FilePane:focus-within")
        if not focused:
            return
        
        pane = focused.first()
        table = pane.query_one(FileList)
        if not table.row_count:
            return
        
        try:
            sel = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
            self.file_clipboard.copy([sel])
            self.notify(f"Copied: {os.path.basename(sel)}")
            self.update_toolbar_state()
        except:
            pass
    
    def action_cut_files(self) -> None:
        """Cut selected files to clipboard."""
        focused = self.query("FilePane:focus-within")
        if not focused:
            return
        
        pane = focused.first()
        table = pane.query_one(FileList)
        if not table.row_count:
            return
        
        try:
            sel = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
            self.file_clipboard.cut([sel])
            self.notify(f"Cut: {os.path.basename(sel)}")
            self.update_toolbar_state()
        except:
            pass
    
    def action_paste_files(self) -> None:
        """Paste files from clipboard to current directory."""
        focused = self.query("FilePane:focus-within")
        if not focused:
            pane = self.query_one("#left-pane", FilePane)
        else:
            pane = focused.first()
        
        dest = pane.current_path
        results = self.file_clipboard.paste(dest)
        
        if results:
            self.history.record("paste", items=results, destination=dest)
            self.notify(f"Pasted {len(results)} item(s)")
            pane.update_file_list(dest, add_to_history=False)
            self.update_toolbar_state()
    
    def action_undo(self) -> None:
        """Undo last operation."""
        op = self.history.undo()
        if not op:
            return
        
        if op["op"] == "paste":
            for _, dest in op["items"]:
                try:
                    if os.path.isdir(dest):
                        shutil.rmtree(dest)
                    else:
                        os.remove(dest)
                except:
                    pass
            self.notify("Undone: Paste")
        elif op["op"] == "delete":
            self.notify("Cannot undo delete (sent to trash)")
        
        focused = self.query("FilePane:focus-within")
        if focused:
            pane = focused.first()
            pane.update_file_list(pane.current_path, add_to_history=False)
        
        self.update_toolbar_state()
    
    def action_redo(self) -> None:
        """Redo last undone operation."""
        op = self.history.redo()
        if not op:
            return
        
        if op["op"] == "paste":
            for src, dest in op["items"]:
                try:
                    if os.path.isdir(src):
                        shutil.copytree(src, dest)
                    else:
                        shutil.copy2(src, dest)
                except:
                    pass
            self.notify("Redone: Paste")
        
        focused = self.query("FilePane:focus-within")
        if focused:
            pane = focused.first()
            pane.update_file_list(pane.current_path, add_to_history=False)
        
        self.update_toolbar_state()

    def open_file_with_app(self, file_path: str, app_choice: str) -> None:
        """Open a file with the specified application."""
        app_map = {
            "notepad": "notepad.exe",
            "vscode": "code",
            "paint": "mspaint.exe",
            "edge": "msedge.exe"
        }
        
        try:
            if app_choice == "default":
                os.startfile(file_path)
                self.notify(f"Opened with default program")
            elif app_choice == "browse":
                # Use list instead of shell=True to prevent shell injection
                subprocess.Popen(["rundll32.exe", "shell32.dll,OpenAs_RunDLL", file_path])
            elif app_choice in app_map:
                app_exe = app_map[app_choice]
                subprocess.Popen([app_exe, file_path])
                self.notify(f"Opened with {app_choice}")
        except Exception as e:
            self.notify(f"Error opening file: {e}", severity="error")

    def action_open_external_terminal(self, path: str = None) -> None:
        """Launch Windows Terminal or PowerShell externally."""
        target_path = path or self.query_one("#left-pane", FilePane).current_path
        
        try:
            subprocess.Popen(f'wt.exe -d "{target_path}"', shell=False, 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            self.notify(f"Opened Windows Terminal")
            return
        except FileNotFoundError:
            pass
        except Exception:
            pass

        try:
            subprocess.Popen(f'pwsh.exe -NoExit -Command "cd \'{target_path}\'"', 
                           shell=False, creationflags=subprocess.CREATE_NEW_CONSOLE)
            self.notify(f"Opened PowerShell")
            return
        except Exception:
            pass

        try:
            subprocess.Popen(f'cmd.exe /k "cd /d {target_path}"', 
                           shell=False, creationflags=subprocess.CREATE_NEW_CONSOLE)
            self.notify(f"Opened Command Prompt")
            return
        except Exception as e:
            self.notify(f"Could not launch terminal: {e}", severity="error")

if __name__ == "__main__":
    app = ExplorerApp()
    app.run()
