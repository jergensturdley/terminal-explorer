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

class ClipboardManager:
    """Manages file clipboard operations (copy/cut/paste)."""
    def __init__(self):
        self.items: list[str] = []
        self.operation: str = ""  # "copy" or "cut"
    
    def copy(self, paths: list[str]) -> None:
        self.items = paths.copy()
        self.operation = "copy"
    
    def cut(self, paths: list[str]) -> None:
        self.items = paths.copy()
        self.operation = "cut"
    
    def paste(self, destination: str) -> list[tuple[str, str]]:
        """Paste items to destination. Returns list of (source, dest) tuples."""
        results = []
        for item in self.items:
            if not os.path.exists(item):
                continue
            
            basename = os.path.basename(item)
            dest_path = os.path.join(destination, basename)
            
            # Handle name conflicts
            if os.path.exists(dest_path):
                name, ext = os.path.splitext(basename)
                counter = 1
                while os.path.exists(dest_path):
                    dest_path = os.path.join(destination, f"{name} ({counter}){ext}")
                    counter += 1
            
            try:
                if self.operation == "copy":
                    if os.path.isdir(item):
                        shutil.copytree(item, dest_path)
                    else:
                        shutil.copy2(item, dest_path)
                elif self.operation == "cut":
                    shutil.move(item, dest_path)
                
                results.append((item, dest_path))
            except Exception:
                pass
        
        # Clear clipboard after cut operation
        if self.operation == "cut":
            self.clear()
        
        return results
    
    def clear(self) -> None:
        self.items = []
        self.operation = ""
    
    def has_items(self) -> bool:
        return len(self.items) > 0

class OperationHistory:
    """Tracks file operations for undo/redo."""
    def __init__(self, max_size: int = 50):
        self.max_size = max_size
        self.undo_stack: list[dict] = []
        self.redo_stack: list[dict] = []
    
    def record(self, operation: str, **kwargs) -> None:
        """Record an operation. Clears redo stack."""
        self.undo_stack.append({"op": operation, **kwargs})
        if len(self.undo_stack) > self.max_size:
            self.undo_stack.pop(0)
        self.redo_stack.clear()
    
    def can_undo(self) -> bool:
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        return len(self.redo_stack) > 0
    
    def undo(self) -> dict | None:
        """Pop and return the last operation for reversal."""
        if not self.can_undo():
            return None
        op = self.undo_stack.pop()
        self.redo_stack.append(op)
        return op
    
    def redo(self) -> dict | None:
        """Pop and return the last undone operation for re-application."""
        if not self.can_redo():
            return None
        op = self.redo_stack.pop()
        self.undo_stack.append(op)
        return op
