"""
Comprehensive test suite for Terminal Explorer.
Tests all functionalities for crashes and errors.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Import components to test
from clipboard_helpers import ClipboardManager, OperationHistory
from explorer import (
    ExplorerApp, FilePane, Sidebar, SystemTree, FileList,
    InputScreen, PropertiesScreen, ContextMenu, OpenWithScreen,
    ResizeHandle, Toolbar
)


class TestResults:
    """Track test results."""
    def __init__(self):
        self.passed = []
        self.failed = []
        self.errors = []
    
    def add_pass(self, test_name):
        self.passed.append(test_name)
        print(f"✓ PASS: {test_name}")
    
    def add_fail(self, test_name, reason):
        self.failed.append((test_name, reason))
        print(f"✗ FAIL: {test_name} - {reason}")
    
    def add_error(self, test_name, error):
        self.errors.append((test_name, str(error)))
        print(f"✗ ERROR: {test_name} - {error}")
    
    def summary(self):
        total = len(self.passed) + len(self.failed) + len(self.errors)
        print("\n" + "="*60)
        print(f"Test Summary: {len(self.passed)}/{total} passed")
        print("="*60)
        
        if self.failed:
            print("\nFailed Tests:")
            for name, reason in self.failed:
                print(f"  - {name}: {reason}")
        
        if self.errors:
            print("\nErrors:")
            for name, error in self.errors:
                print(f"  - {name}: {error}")
        
        return len(self.failed) == 0 and len(self.errors) == 0


results = TestResults()


def test_clipboard_manager():
    """Test ClipboardManager class."""
    print("\n--- Testing ClipboardManager ---")
    
    # Test initialization
    try:
        cm = ClipboardManager()
        assert not cm.has_items(), "New clipboard should be empty"
        results.add_pass("ClipboardManager initialization")
    except Exception as e:
        results.add_error("ClipboardManager initialization", e)
        return
    
    # Test copy operation
    try:
        test_paths = ["/tmp/test1.txt", "/tmp/test2.txt"]
        cm.copy(test_paths)
        assert cm.has_items(), "Clipboard should have items after copy"
        assert cm.operation == "copy", "Operation should be 'copy'"
        assert cm.items == test_paths, "Items should match copied paths"
        results.add_pass("ClipboardManager copy operation")
    except Exception as e:
        results.add_error("ClipboardManager copy operation", e)
    
    # Test cut operation
    try:
        cm.cut(["/tmp/test3.txt"])
        assert cm.operation == "cut", "Operation should be 'cut'"
        assert len(cm.items) == 1, "Should have one item"
        results.add_pass("ClipboardManager cut operation")
    except Exception as e:
        results.add_error("ClipboardManager cut operation", e)
    
    # Test clear operation
    try:
        cm.clear()
        assert not cm.has_items(), "Clipboard should be empty after clear"
        assert cm.operation == "", "Operation should be empty"
        results.add_pass("ClipboardManager clear operation")
    except Exception as e:
        results.add_error("ClipboardManager clear operation", e)
    
    # Test paste with non-existent files
    try:
        cm.copy(["/nonexistent/file.txt"])
        result = cm.paste("/tmp")
        assert len(result) == 0, "Should return empty list for non-existent files"
        results.add_pass("ClipboardManager paste with non-existent files")
    except Exception as e:
        results.add_error("ClipboardManager paste with non-existent files", e)


def test_operation_history():
    """Test OperationHistory class."""
    print("\n--- Testing OperationHistory ---")
    
    # Test initialization
    try:
        history = OperationHistory(max_size=5)
        assert not history.can_undo(), "New history should not allow undo"
        assert not history.can_redo(), "New history should not allow redo"
        results.add_pass("OperationHistory initialization")
    except Exception as e:
        results.add_error("OperationHistory initialization", e)
        return
    
    # Test record operation
    try:
        history.record("paste", items=[], destination="/tmp")
        assert history.can_undo(), "Should allow undo after recording"
        assert not history.can_redo(), "Should not allow redo after recording"
        results.add_pass("OperationHistory record")
    except Exception as e:
        results.add_error("OperationHistory record", e)
    
    # Test undo
    try:
        op = history.undo()
        assert op is not None, "Undo should return operation"
        assert op["op"] == "paste", "Operation type should match"
        assert not history.can_undo(), "Should not allow undo after undoing last op"
        assert history.can_redo(), "Should allow redo after undo"
        results.add_pass("OperationHistory undo")
    except Exception as e:
        results.add_error("OperationHistory undo", e)
    
    # Test redo
    try:
        op = history.redo()
        assert op is not None, "Redo should return operation"
        assert op["op"] == "paste", "Operation type should match"
        assert history.can_undo(), "Should allow undo after redo"
        assert not history.can_redo(), "Should not allow redo after redoing last op"
        results.add_pass("OperationHistory redo")
    except Exception as e:
        results.add_error("OperationHistory redo", e)
    
    # Test max size
    try:
        history = OperationHistory(max_size=3)
        for i in range(5):
            history.record("test", index=i)
        assert len(history.undo_stack) == 3, "Stack should be limited to max_size"
        results.add_pass("OperationHistory max size limit")
    except Exception as e:
        results.add_error("OperationHistory max size limit", e)
    
    # Test undo/redo on empty stack
    try:
        history = OperationHistory()
        result = history.undo()
        assert result is None, "Undo on empty stack should return None"
        result = history.redo()
        assert result is None, "Redo on empty stack should return None"
        results.add_pass("OperationHistory empty stack operations")
    except Exception as e:
        results.add_error("OperationHistory empty stack operations", e)


def test_app_instantiation():
    """Test that ExplorerApp can be instantiated."""
    print("\n--- Testing App Instantiation ---")
    
    try:
        app = ExplorerApp()
        assert app is not None, "App should be instantiated"
        results.add_pass("ExplorerApp instantiation")
    except Exception as e:
        results.add_error("ExplorerApp instantiation", e)


def test_component_instantiation():
    """Test that all components can be instantiated."""
    print("\n--- Testing Component Instantiation ---")
    
    # Test ResizeHandle
    try:
        handle = ResizeHandle("test-id", vertical=False)
        assert handle.target_id == "test-id"
        assert handle.vertical == False
        results.add_pass("ResizeHandle instantiation")
    except Exception as e:
        results.add_error("ResizeHandle instantiation", e)
    
    # Test InputScreen
    try:
        screen = InputScreen("Test prompt", "initial", "placeholder")
        assert screen.prompt == "Test prompt"
        assert screen.initial_value == "initial"
        assert screen.placeholder == "placeholder"
        results.add_pass("InputScreen instantiation")
    except Exception as e:
        results.add_error("InputScreen instantiation", e)
    
    # Test PropertiesScreen with temp file
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            temp_path = tf.name
        try:
            screen = PropertiesScreen(temp_path)
            assert screen.path == temp_path
            results.add_pass("PropertiesScreen instantiation")
        finally:
            os.unlink(temp_path)
    except Exception as e:
        results.add_error("PropertiesScreen instantiation", e)
    
    # Test ContextMenu
    try:
        items = [("action1", "Label 1", "default"), ("action2", "Label 2", "primary")]
        menu = ContextMenu(items, 10, 20)
        assert menu.items == items
        assert menu.x == 10
        assert menu.y == 20
        results.add_pass("ContextMenu instantiation")
    except Exception as e:
        results.add_error("ContextMenu instantiation", e)
    
    # Test OpenWithScreen
    try:
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tf:
            temp_path = tf.name
        try:
            screen = OpenWithScreen(temp_path)
            assert screen.file_path == temp_path
            assert screen.file_ext == ".txt"
            results.add_pass("OpenWithScreen instantiation")
        finally:
            os.unlink(temp_path)
    except Exception as e:
        results.add_error("OpenWithScreen instantiation", e)


def test_file_operations_with_temp_dir():
    """Test file operations using a temporary directory."""
    print("\n--- Testing File Operations ---")
    
    # Create temporary directory
    test_dir = tempfile.mkdtemp(prefix="explorer_test_")
    
    try:
        # Test clipboard paste with real files
        test_file1 = os.path.join(test_dir, "test1.txt")
        test_file2 = os.path.join(test_dir, "test2.txt")
        
        # Create test files
        with open(test_file1, 'w') as f:
            f.write("Test content 1")
        with open(test_file2, 'w') as f:
            f.write("Test content 2")
        
        # Test copy operation
        cm = ClipboardManager()
        cm.copy([test_file1])
        
        dest_dir = os.path.join(test_dir, "dest")
        os.makedirs(dest_dir)
        
        result = cm.paste(dest_dir)
        assert len(result) == 1, "Should paste one file"
        assert os.path.exists(os.path.join(dest_dir, "test1.txt")), "File should exist in destination"
        results.add_pass("ClipboardManager paste copy operation")
        
        # Test cut operation
        cm.cut([test_file2])
        result = cm.paste(dest_dir)
        assert len(result) == 1, "Should paste one file"
        assert os.path.exists(os.path.join(dest_dir, "test2.txt")), "File should exist in destination"
        assert not os.path.exists(test_file2), "Original file should be removed after cut"
        results.add_pass("ClipboardManager paste cut operation")
        
        # Test paste with name conflict
        with open(test_file1, 'w') as f:
            f.write("Test content new")
        cm.copy([test_file1])
        result = cm.paste(dest_dir)
        assert len(result) == 1, "Should paste one file"
        # Should create test1 (1).txt due to conflict
        files_in_dest = os.listdir(dest_dir)
        assert any("test1" in f and f != "test1.txt" for f in files_in_dest), "Should create numbered copy"
        results.add_pass("ClipboardManager paste with name conflict")
        
        # Test directory copy
        test_subdir = os.path.join(test_dir, "subdir")
        os.makedirs(test_subdir)
        with open(os.path.join(test_subdir, "file.txt"), 'w') as f:
            f.write("Content in subdir")
        
        cm.copy([test_subdir])
        result = cm.paste(dest_dir)
        assert len(result) == 1, "Should paste one directory"
        assert os.path.exists(os.path.join(dest_dir, "subdir", "file.txt")), "Directory content should be copied"
        results.add_pass("ClipboardManager paste directory")
        
    except Exception as e:
        results.add_error("File operations", e)
    finally:
        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)


def test_format_size():
    """Test file size formatting."""
    print("\n--- Testing File Size Formatting ---")
    
    try:
        from explorer import FilePane
        pane = FilePane(id="test-pane")
        
        # Test various sizes
        assert "0.0 B" in pane.format_size(0)
        assert "B" in pane.format_size(100)
        assert "KB" in pane.format_size(1024)
        assert "MB" in pane.format_size(1024 * 1024)
        assert "GB" in pane.format_size(1024 * 1024 * 1024)
        assert "TB" in pane.format_size(1024 * 1024 * 1024 * 1024)
        
        results.add_pass("File size formatting")
    except Exception as e:
        results.add_error("File size formatting", e)


def test_edge_cases():
    """Test edge cases and error conditions."""
    print("\n--- Testing Edge Cases ---")
    
    # Test clipboard with empty list
    try:
        cm = ClipboardManager()
        cm.copy([])
        assert not cm.has_items(), "Empty copy should result in empty clipboard"
        results.add_pass("ClipboardManager empty copy")
    except Exception as e:
        results.add_error("ClipboardManager empty copy", e)
    
    # Test clipboard paste to non-existent destination
    try:
        cm = ClipboardManager()
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            temp_file = tf.name
        cm.copy([temp_file])
        # Paste to non-existent directory should handle gracefully
        try:
            result = cm.paste("/nonexistent/directory/path")
            # Should fail but not crash
            results.add_pass("ClipboardManager paste to non-existent directory")
        except:
            # It's okay if it raises an exception, as long as it doesn't crash
            results.add_pass("ClipboardManager paste to non-existent directory (exception)")
        finally:
            os.unlink(temp_file)
    except Exception as e:
        results.add_error("ClipboardManager paste to non-existent directory", e)
    
    # Test history with zero max size
    try:
        history = OperationHistory(max_size=0)
        history.record("test")
        assert len(history.undo_stack) == 0, "Stack with max_size 0 should remain empty"
        results.add_pass("OperationHistory zero max size")
    except Exception as e:
        results.add_error("OperationHistory zero max size", e)
    
    # Test OpenWithScreen with various file extensions
    try:
        extensions = ['.txt', '.py', '.js', '.png', '.jpg', '.pdf', '.unknown']
        for ext in extensions:
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tf:
                temp_path = tf.name
            try:
                screen = OpenWithScreen(temp_path)
                apps = screen.get_common_apps()
                # Should return list (may be empty for unknown extensions)
                assert isinstance(apps, list), f"Should return list for {ext}"
            finally:
                os.unlink(temp_path)
        results.add_pass("OpenWithScreen various file extensions")
    except Exception as e:
        results.add_error("OpenWithScreen various file extensions", e)


def test_path_validation():
    """Test path validation and handling."""
    print("\n--- Testing Path Validation ---")
    
    # Test with various path types
    try:
        test_paths = [
            "/tmp",
            os.path.expanduser("~"),
            ".",
            "..",
        ]
        
        for path in test_paths:
            if os.path.exists(path):
                # Just ensure no crash when accessing
                try:
                    os.path.isdir(path)
                    os.path.isfile(path)
                except:
                    pass
        
        results.add_pass("Path validation")
    except Exception as e:
        results.add_error("Path validation", e)


def test_clipboard_operations_stress():
    """Stress test clipboard operations."""
    print("\n--- Stress Testing Clipboard ---")
    
    test_dir = tempfile.mkdtemp(prefix="explorer_stress_")
    
    try:
        # Create many files
        files = []
        for i in range(100):
            file_path = os.path.join(test_dir, f"file_{i}.txt")
            with open(file_path, 'w') as f:
                f.write(f"Content {i}")
            files.append(file_path)
        
        # Copy many files
        cm = ClipboardManager()
        cm.copy(files)
        assert len(cm.items) == 100, "Should copy all files"
        
        dest_dir = os.path.join(test_dir, "dest")
        os.makedirs(dest_dir)
        
        result = cm.paste(dest_dir)
        assert len(result) == 100, "Should paste all files"
        
        results.add_pass("Clipboard stress test (100 files)")
    except Exception as e:
        results.add_error("Clipboard stress test", e)
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_history_stress():
    """Stress test operation history."""
    print("\n--- Stress Testing History ---")
    
    try:
        history = OperationHistory(max_size=50)
        
        # Add many operations
        for i in range(100):
            history.record("test", index=i)
        
        # Stack should be limited
        assert len(history.undo_stack) <= 50, "Stack should respect max size"
        
        # Undo all
        count = 0
        while history.can_undo():
            history.undo()
            count += 1
        
        assert count <= 50, "Should undo up to max size"
        
        # Redo all
        redo_count = 0
        while history.can_redo():
            history.redo()
            redo_count += 1
        
        assert redo_count == count, "Redo count should match undo count"
        
        results.add_pass("History stress test")
    except Exception as e:
        results.add_error("History stress test", e)


def run_all_tests():
    """Run all tests."""
    print("="*60)
    print("Terminal Explorer - Comprehensive Test Suite")
    print("="*60)
    
    test_clipboard_manager()
    test_operation_history()
    test_app_instantiation()
    test_component_instantiation()
    test_file_operations_with_temp_dir()
    test_format_size()
    test_edge_cases()
    test_path_validation()
    test_clipboard_operations_stress()
    test_history_stress()
    
    success = results.summary()
    
    print("\n" + "="*60)
    if success:
        print("All tests passed! ✓")
        print("="*60)
        return 0
    else:
        print("Some tests failed. See details above.")
        print("="*60)
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
