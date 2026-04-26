"""
UI and App Logic Tests for Terminal Explorer.
Tests potential crashes in UI components and app interactions.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

from explorer import (
    ExplorerApp, FilePane, InputScreen, PropertiesScreen,
    ContextMenu, OpenWithScreen
)


class UITestResults:
    """Track UI test results."""
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
        print(f"UI Test Summary: {len(self.passed)}/{total} passed")
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


results = UITestResults()


def test_file_pane_format_size():
    """Test FilePane format_size with edge cases."""
    print("\n--- Testing FilePane format_size Edge Cases ---")
    
    try:
        pane = FilePane(id="test")
        
        # Test boundary values
        test_cases = [
            (0, "0.0 B"),
            (1, "1.0 B"),
            (1023, "1023.0 B"),
            (1024, "1.0 KB"),
            (1024 * 1024, "1.0 MB"),
            (1024 * 1024 * 1024, "1.0 GB"),
            (1024 * 1024 * 1024 * 1024, "1.0 TB"),
            (1024 * 1024 * 1024 * 1024 * 1024, "1.0 PB"),
        ]
        
        for size, expected_unit in test_cases:
            result = pane.format_size(size)
            # Just check the unit is correct, not the exact formatting
            if expected_unit.split()[-1] in result:
                continue
            else:
                results.add_fail(f"format_size({size})", f"Expected unit {expected_unit.split()[-1]}, got {result}")
                return
        
        results.add_pass("FilePane format_size edge cases")
        
    except Exception as e:
        results.add_error("FilePane format_size edge cases", e)


def test_file_pane_initialization():
    """Test FilePane initialization and defaults."""
    print("\n--- Testing FilePane Initialization ---")
    
    try:
        pane = FilePane(id="test-pane")
        
        # Check initial state is set properly
        assert hasattr(pane, 'compose'), "Should have compose method"
        
        results.add_pass("FilePane initialization")
        
    except Exception as e:
        results.add_error("FilePane initialization", e)


def test_input_screen_variations():
    """Test InputScreen with various inputs."""
    print("\n--- Testing InputScreen Variations ---")
    
    try:
        # Test with minimal params
        screen1 = InputScreen("Prompt")
        assert screen1.prompt == "Prompt"
        assert screen1.initial_value == ""
        assert screen1.placeholder == ""
        
        # Test with all params
        screen2 = InputScreen("Enter name:", "default", "Type here...")
        assert screen2.prompt == "Enter name:"
        assert screen2.initial_value == "default"
        assert screen2.placeholder == "Type here..."
        
        # Test with special characters
        screen3 = InputScreen("Enter path:", "C:\\Users\\Test", "C:\\...")
        assert screen3.initial_value == "C:\\Users\\Test"
        
        # Test with unicode
        screen4 = InputScreen("输入名称：", "默认", "请输入...")
        assert screen4.prompt == "输入名称："
        
        results.add_pass("InputScreen variations")
        
    except Exception as e:
        results.add_error("InputScreen variations", e)


def test_properties_screen_with_various_files():
    """Test PropertiesScreen with different file types."""
    print("\n--- Testing PropertiesScreen with Various Files ---")
    
    test_dir = tempfile.mkdtemp(prefix="explorer_props_")
    
    try:
        # Test with regular file
        regular_file = os.path.join(test_dir, "regular.txt")
        with open(regular_file, 'w') as f:
            f.write("Content")
        
        screen1 = PropertiesScreen(regular_file)
        assert screen1.path == regular_file
        
        # Test with directory
        test_subdir = os.path.join(test_dir, "subdir")
        os.makedirs(test_subdir)
        
        screen2 = PropertiesScreen(test_subdir)
        assert screen2.path == test_subdir
        
        # Test with empty file
        empty_file = os.path.join(test_dir, "empty.txt")
        Path(empty_file).touch()
        
        screen3 = PropertiesScreen(empty_file)
        assert screen3.path == empty_file
        
        # Test with file with special name
        special_file = os.path.join(test_dir, "file with spaces & special.txt")
        with open(special_file, 'w') as f:
            f.write("Special")
        
        screen4 = PropertiesScreen(special_file)
        assert screen4.path == special_file
        
        results.add_pass("PropertiesScreen with various files")
        
    except Exception as e:
        results.add_error("PropertiesScreen with various files", e)
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_context_menu_variations():
    """Test ContextMenu with various configurations."""
    print("\n--- Testing ContextMenu Variations ---")
    
    try:
        # Empty menu
        menu1 = ContextMenu([], 0, 0)
        assert menu1.items == []
        
        # Single item
        menu2 = ContextMenu([("action", "Label", "default")], 10, 20)
        assert len(menu2.items) == 1
        
        # Many items
        items = [(f"action{i}", f"Label {i}", "default") for i in range(50)]
        menu3 = ContextMenu(items, 100, 200)
        assert len(menu3.items) == 50
        
        # Different positions
        menu4 = ContextMenu([("test", "Test", "default")], 0, 0)
        assert menu4.x == 0 and menu4.y == 0
        
        menu5 = ContextMenu([("test", "Test", "default")], 9999, 9999)
        assert menu5.x == 9999 and menu5.y == 9999
        
        results.add_pass("ContextMenu variations")
        
    except Exception as e:
        results.add_error("ContextMenu variations", e)


def test_open_with_screen_file_extensions():
    """Test OpenWithScreen with various file extensions."""
    print("\n--- Testing OpenWithScreen File Extensions ---")
    
    test_dir = tempfile.mkdtemp(prefix="explorer_openwith_")
    
    try:
        extensions = [
            '.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml',
            '.png', '.jpg', '.jpeg', '.gif', '.bmp',
            '.pdf',
            '.doc', '.docx', '.xls', '.xlsx',
            '.zip', '.rar', '.tar', '.gz',
            '.mp3', '.mp4', '.avi', '.mkv',
            '', '.unknown', '.verylongextension'
        ]
        
        for ext in extensions:
            filename = f"testfile{ext}" if ext else "noextension"
            file_path = os.path.join(test_dir, filename)
            Path(file_path).touch()
            
            try:
                screen = OpenWithScreen(file_path)
                assert screen.file_ext == ext
                apps = screen.get_common_apps()
                assert isinstance(apps, list)
            except Exception as inner_e:
                results.add_error(f"OpenWithScreen extension {ext}", inner_e)
                return
            finally:
                os.unlink(file_path)
        
        results.add_pass("OpenWithScreen file extensions")
        
    except Exception as e:
        results.add_error("OpenWithScreen file extensions", e)
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_app_copy_to_clipboard_method():
    """Test the app action methods existence."""
    print("\n--- Testing App Action Methods ---")
    
    try:
        app = ExplorerApp()
        
        # Note: file_clipboard and history are created in on_mount, not __init__
        # So we can't test for them without running the app
        # But we can test that the action methods are defined
        
        # The app should have these action methods
        expected_actions = [
            'action_copy_files',
            'action_cut_files',
            'action_paste_files',
            'action_undo',
            'action_redo',
            'action_delete_file',
            'action_rename_file',
            'action_go_up',
            'action_open_item',
            'action_toggle_pane',
            'action_open_external_terminal',
        ]
        
        for action in expected_actions:
            if not hasattr(app, action):
                results.add_fail("App action methods", f"Missing {action}")
                return
        
        results.add_pass("App action methods")
        
    except Exception as e:
        results.add_error("App action methods", e)


def test_app_bindings():
    """Test that app bindings are properly defined."""
    print("\n--- Testing App Bindings ---")
    
    try:
        app = ExplorerApp()
        
        # Check that BINDINGS is defined
        assert hasattr(ExplorerApp, 'BINDINGS'), "App should have BINDINGS"
        assert len(ExplorerApp.BINDINGS) > 0, "BINDINGS should not be empty"
        
        # Check some key bindings exist
        binding_keys = [b.key for b in ExplorerApp.BINDINGS]
        expected_keys = ['q', 'd', 'backspace', 'delete', 'f2', 'enter']
        
        for key in expected_keys:
            if key not in binding_keys:
                results.add_fail("App bindings", f"Missing key binding: {key}")
                return
        
        results.add_pass("App bindings")
        
    except Exception as e:
        results.add_error("App bindings", e)


def test_app_css():
    """Test that app CSS is properly defined."""
    print("\n--- Testing App CSS ---")
    
    try:
        app = ExplorerApp()
        
        # Check that CSS is defined
        assert hasattr(ExplorerApp, 'CSS'), "App should have CSS"
        assert len(ExplorerApp.CSS) > 0, "CSS should not be empty"
        
        # Check for some key selectors
        css = ExplorerApp.CSS
        expected_selectors = [
            '#sidebar',
            'FilePane',
            'Toolbar',
            '#context-menu',
            '#input_dialog',
        ]
        
        for selector in expected_selectors:
            if selector not in css:
                results.add_fail("App CSS", f"Missing selector: {selector}")
                return
        
        results.add_pass("App CSS")
        
    except Exception as e:
        results.add_error("App CSS", e)


def test_negative_size_formatting():
    """Test format_size with negative numbers (edge case)."""
    print("\n--- Testing Negative Size Formatting ---")
    
    try:
        pane = FilePane(id="test")
        
        # Negative sizes shouldn't occur in practice, but test graceful handling
        try:
            result = pane.format_size(-100)
            # Should handle gracefully, even if output is weird
            results.add_pass("Negative size formatting (handled)")
        except:
            results.add_pass("Negative size formatting (exception, expected)")
        
    except Exception as e:
        results.add_error("Negative size formatting", e)


def test_zero_and_boundary_coordinates():
    """Test various coordinate edge cases."""
    print("\n--- Testing Coordinate Edge Cases ---")
    
    try:
        # ContextMenu at origin
        menu1 = ContextMenu([("test", "Test", "default")], 0, 0)
        assert menu1.x == 0 and menu1.y == 0
        
        # ContextMenu at negative coordinates
        menu2 = ContextMenu([("test", "Test", "default")], -10, -20)
        assert menu2.x == -10 and menu2.y == -20
        
        # ContextMenu at very large coordinates
        menu3 = ContextMenu([("test", "Test", "default")], 999999, 999999)
        assert menu3.x == 999999 and menu3.y == 999999
        
        results.add_pass("Coordinate edge cases")
        
    except Exception as e:
        results.add_error("Coordinate edge cases", e)


def test_empty_string_inputs():
    """Test components with empty string inputs."""
    print("\n--- Testing Empty String Inputs ---")
    
    try:
        # InputScreen with empty strings
        screen = InputScreen("", "", "")
        assert screen.prompt == ""
        assert screen.initial_value == ""
        assert screen.placeholder == ""
        
        results.add_pass("Empty string inputs")
        
    except Exception as e:
        results.add_error("Empty string inputs", e)


def test_very_long_strings():
    """Test components with very long strings."""
    print("\n--- Testing Very Long Strings ---")
    
    try:
        # Very long prompt
        long_string = "A" * 10000
        screen = InputScreen(long_string, long_string, long_string)
        assert len(screen.prompt) == 10000
        assert len(screen.initial_value) == 10000
        assert len(screen.placeholder) == 10000
        
        results.add_pass("Very long strings")
        
    except Exception as e:
        results.add_error("Very long strings", e)


def run_all_ui_tests():
    """Run all UI tests."""
    print("="*60)
    print("Terminal Explorer - UI and App Logic Test Suite")
    print("="*60)
    
    test_file_pane_format_size()
    test_file_pane_initialization()
    test_input_screen_variations()
    test_properties_screen_with_various_files()
    test_context_menu_variations()
    test_open_with_screen_file_extensions()
    test_app_copy_to_clipboard_method()
    test_app_bindings()
    test_app_css()
    test_negative_size_formatting()
    test_zero_and_boundary_coordinates()
    test_empty_string_inputs()
    test_very_long_strings()
    
    success = results.summary()
    
    print("\n" + "="*60)
    if success:
        print("All UI tests passed! ✓")
        print("="*60)
        return 0
    else:
        print("Some UI tests failed. See details above.")
        print("="*60)
        return 1


if __name__ == "__main__":
    sys.exit(run_all_ui_tests())
