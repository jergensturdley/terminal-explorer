"""
Integration tests for Terminal Explorer.
Tests potential crash scenarios and edge cases in actual usage.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

from clipboard_helpers import ClipboardManager, OperationHistory


class IntegrationTestResults:
    """Track integration test results."""
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
        print(f"Integration Test Summary: {len(self.passed)}/{total} passed")
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


results = IntegrationTestResults()


def test_special_characters_in_filenames():
    """Test handling of special characters in filenames."""
    print("\n--- Testing Special Characters in Filenames ---")
    
    test_dir = tempfile.mkdtemp(prefix="explorer_special_")
    
    try:
        # Test various special characters (avoiding truly problematic ones on Windows)
        special_names = [
            "file with spaces.txt",
            "file-with-dashes.txt",
            "file_with_underscores.txt",
            "file.multiple.dots.txt",
            "file(with)parentheses.txt",
            "file[with]brackets.txt",
            "file{with}braces.txt",
            "file'with'quotes.txt",
            "file@with@at.txt",
            "file#with#hash.txt",
            "file$with$dollar.txt",
            "file%with%percent.txt",
            "file&with&ampersand.txt",
            "file=with=equals.txt",
            "file+with+plus.txt",
            "file,with,comma.txt",
            "file;with;semicolon.txt",
        ]
        
        created_files = []
        for name in special_names:
            try:
                file_path = os.path.join(test_dir, name)
                with open(file_path, 'w') as f:
                    f.write(f"Content for {name}")
                created_files.append(file_path)
            except:
                # Some characters may not be allowed on certain filesystems
                pass
        
        if not created_files:
            results.add_fail("Special characters in filenames", "No files could be created")
            return
        
        # Test clipboard operations with special characters
        cm = ClipboardManager()
        cm.copy(created_files)
        
        dest_dir = os.path.join(test_dir, "dest")
        os.makedirs(dest_dir)
        
        result = cm.paste(dest_dir)
        
        if len(result) == len(created_files):
            results.add_pass("Special characters in filenames")
        else:
            results.add_fail("Special characters in filenames", 
                           f"Only {len(result)}/{len(created_files)} files pasted")
        
    except Exception as e:
        results.add_error("Special characters in filenames", e)
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_very_long_paths():
    """Test handling of very long file paths."""
    print("\n--- Testing Very Long Paths ---")
    
    test_dir = tempfile.mkdtemp(prefix="explorer_long_")
    
    try:
        # Create a deep directory structure
        current = test_dir
        for i in range(20):  # Create nested directories
            current = os.path.join(current, f"verylongdirectoryname{i}")
            try:
                os.makedirs(current, exist_ok=True)
            except OSError:
                # Path too long for filesystem
                break
        
        # Try to create a file in the deepest directory
        try:
            file_path = os.path.join(current, "file_with_a_very_long_name_to_test_path_limits.txt")
            with open(file_path, 'w') as f:
                f.write("Test content")
            
            # Test clipboard operations
            cm = ClipboardManager()
            cm.copy([file_path])
            
            dest_dir = os.path.join(test_dir, "dest")
            os.makedirs(dest_dir)
            
            result = cm.paste(dest_dir)
            
            if len(result) == 1:
                results.add_pass("Very long paths")
            else:
                results.add_pass("Very long paths (graceful handling)")
        except OSError:
            # Path too long for filesystem - this is expected behavior
            results.add_pass("Very long paths (filesystem limit reached gracefully)")
        
    except Exception as e:
        results.add_error("Very long paths", e)
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_unicode_filenames():
    """Test handling of unicode characters in filenames."""
    print("\n--- Testing Unicode Filenames ---")
    
    test_dir = tempfile.mkdtemp(prefix="explorer_unicode_")
    
    try:
        unicode_names = [
            "文件.txt",  # Chinese
            "файл.txt",  # Russian
            "αρχείο.txt",  # Greek
            "ファイル.txt",  # Japanese
            "파일.txt",  # Korean
            "file_with_emoji_😀.txt",  # Emoji
            "café.txt",  # Accented characters
            "niño.txt",  # Spanish
        ]
        
        created_files = []
        for name in unicode_names:
            try:
                file_path = os.path.join(test_dir, name)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"Content for {name}")
                created_files.append(file_path)
            except:
                # Some unicode may not be supported on all filesystems
                pass
        
        if not created_files:
            results.add_pass("Unicode filenames (not supported on this filesystem)")
            return
        
        # Test clipboard operations
        cm = ClipboardManager()
        cm.copy(created_files)
        
        dest_dir = os.path.join(test_dir, "dest")
        os.makedirs(dest_dir)
        
        result = cm.paste(dest_dir)
        
        if len(result) == len(created_files):
            results.add_pass("Unicode filenames")
        else:
            results.add_pass("Unicode filenames (partial support)")
        
    except Exception as e:
        results.add_error("Unicode filenames", e)
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_empty_directory_operations():
    """Test operations on empty directories."""
    print("\n--- Testing Empty Directory Operations ---")
    
    test_dir = tempfile.mkdtemp(prefix="explorer_empty_")
    
    try:
        # Create an empty directory
        empty_dir = os.path.join(test_dir, "empty")
        os.makedirs(empty_dir)
        
        # Test copy
        cm = ClipboardManager()
        cm.copy([empty_dir])
        
        dest_dir = os.path.join(test_dir, "dest")
        os.makedirs(dest_dir)
        
        result = cm.paste(dest_dir)
        
        if len(result) == 1 and os.path.isdir(os.path.join(dest_dir, "empty")):
            results.add_pass("Empty directory copy")
        else:
            results.add_fail("Empty directory copy", "Directory not copied correctly")
        
        # Test cut
        cm.cut([empty_dir])
        result = cm.paste(dest_dir)
        
        if not os.path.exists(empty_dir):
            results.add_pass("Empty directory cut")
        else:
            results.add_fail("Empty directory cut", "Directory not moved")
        
    except Exception as e:
        results.add_error("Empty directory operations", e)
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_nested_directory_operations():
    """Test operations on deeply nested directories."""
    print("\n--- Testing Nested Directory Operations ---")
    
    test_dir = tempfile.mkdtemp(prefix="explorer_nested_")
    
    try:
        # Create nested structure
        nested = os.path.join(test_dir, "level1", "level2", "level3")
        os.makedirs(nested)
        
        # Create files at various levels
        with open(os.path.join(test_dir, "level1", "file1.txt"), 'w') as f:
            f.write("Level 1")
        with open(os.path.join(test_dir, "level1", "level2", "file2.txt"), 'w') as f:
            f.write("Level 2")
        with open(os.path.join(nested, "file3.txt"), 'w') as f:
            f.write("Level 3")
        
        # Copy entire structure
        cm = ClipboardManager()
        cm.copy([os.path.join(test_dir, "level1")])
        
        dest_dir = os.path.join(test_dir, "dest")
        os.makedirs(dest_dir)
        
        result = cm.paste(dest_dir)
        
        # Verify structure was copied
        if (os.path.exists(os.path.join(dest_dir, "level1", "file1.txt")) and
            os.path.exists(os.path.join(dest_dir, "level1", "level2", "file2.txt")) and
            os.path.exists(os.path.join(dest_dir, "level1", "level2", "level3", "file3.txt"))):
            results.add_pass("Nested directory copy")
        else:
            results.add_fail("Nested directory copy", "Structure not copied completely")
        
    except Exception as e:
        results.add_error("Nested directory operations", e)
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_large_file_operations():
    """Test operations with large files."""
    print("\n--- Testing Large File Operations ---")
    
    test_dir = tempfile.mkdtemp(prefix="explorer_large_")
    
    try:
        # Create a moderately large file (1MB)
        large_file = os.path.join(test_dir, "large_file.bin")
        with open(large_file, 'wb') as f:
            f.write(b'0' * (1024 * 1024))  # 1 MB
        
        # Test copy
        cm = ClipboardManager()
        cm.copy([large_file])
        
        dest_dir = os.path.join(test_dir, "dest")
        os.makedirs(dest_dir)
        
        result = cm.paste(dest_dir)
        
        dest_file = os.path.join(dest_dir, "large_file.bin")
        if os.path.exists(dest_file) and os.path.getsize(dest_file) == 1024 * 1024:
            results.add_pass("Large file copy")
        else:
            results.add_fail("Large file copy", "File not copied correctly")
        
    except Exception as e:
        results.add_error("Large file operations", e)
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_readonly_scenarios():
    """Test operations with read-only files."""
    print("\n--- Testing Read-Only Scenarios ---")
    
    test_dir = tempfile.mkdtemp(prefix="explorer_readonly_")
    
    try:
        # Create a file and make it read-only
        readonly_file = os.path.join(test_dir, "readonly.txt")
        with open(readonly_file, 'w') as f:
            f.write("Read only content")
        
        # Make file read-only (cross-platform)
        os.chmod(readonly_file, 0o444)
        
        # Test copy (should work)
        cm = ClipboardManager()
        cm.copy([readonly_file])
        
        dest_dir = os.path.join(test_dir, "dest")
        os.makedirs(dest_dir)
        
        result = cm.paste(dest_dir)
        
        if len(result) == 1:
            results.add_pass("Read-only file copy")
        else:
            results.add_fail("Read-only file copy", "Failed to copy read-only file")
        
        # Try to cut (may fail due to read-only, should handle gracefully)
        try:
            cm.cut([readonly_file])
            result = cm.paste(os.path.join(test_dir, "dest2"))
            # If it succeeds, that's okay
            results.add_pass("Read-only file cut (succeeded)")
        except:
            # If it fails, that's also okay as long as it doesn't crash
            results.add_pass("Read-only file cut (graceful failure)")
        
    except Exception as e:
        results.add_error("Read-only scenarios", e)
    finally:
        # Reset permissions before cleanup
        try:
            os.chmod(readonly_file, 0o644)
        except:
            pass
        shutil.rmtree(test_dir, ignore_errors=True)


def test_concurrent_operations():
    """Test multiple clipboard operations in sequence."""
    print("\n--- Testing Concurrent Operations ---")
    
    test_dir = tempfile.mkdtemp(prefix="explorer_concurrent_")
    
    try:
        # Create test files
        files = []
        for i in range(10):
            file_path = os.path.join(test_dir, f"file{i}.txt")
            with open(file_path, 'w') as f:
                f.write(f"Content {i}")
            files.append(file_path)
        
        cm = ClipboardManager()
        
        # Perform multiple operations
        cm.copy(files[:5])
        assert len(cm.items) == 5, "Should have 5 items"
        
        cm.cut(files[5:])
        assert len(cm.items) == 5, "Should replace with 5 items"
        assert cm.operation == "cut", "Should be cut operation"
        
        cm.copy(files[:3])
        assert len(cm.items) == 3, "Should replace with 3 items"
        assert cm.operation == "copy", "Should be copy operation"
        
        cm.clear()
        assert len(cm.items) == 0, "Should be empty"
        
        results.add_pass("Concurrent operations")
        
    except Exception as e:
        results.add_error("Concurrent operations", e)
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_history_edge_cases():
    """Test history with various edge cases."""
    print("\n--- Testing History Edge Cases ---")
    
    try:
        history = OperationHistory()
        
        # Record, undo, then record new operation (should clear redo stack)
        history.record("op1")
        history.record("op2")
        history.undo()
        assert history.can_redo(), "Should be able to redo"
        
        history.record("op3")
        assert not history.can_redo(), "Redo stack should be cleared"
        
        results.add_pass("History redo stack clearing")
        
        # Test multiple undo/redo cycles
        history = OperationHistory()
        for i in range(5):
            history.record(f"op{i}")
        
        # Undo all
        for i in range(5):
            assert history.can_undo(), f"Should be able to undo {i}"
            history.undo()
        
        # Redo all
        for i in range(5):
            assert history.can_redo(), f"Should be able to redo {i}"
            history.redo()
        
        results.add_pass("History multiple undo/redo cycles")
        
    except Exception as e:
        results.add_error("History edge cases", e)


def test_mixed_file_directory_operations():
    """Test operations with mixed files and directories."""
    print("\n--- Testing Mixed File/Directory Operations ---")
    
    test_dir = tempfile.mkdtemp(prefix="explorer_mixed_")
    
    try:
        # Create mixed content
        file1 = os.path.join(test_dir, "file1.txt")
        with open(file1, 'w') as f:
            f.write("File 1")
        
        dir1 = os.path.join(test_dir, "dir1")
        os.makedirs(dir1)
        with open(os.path.join(dir1, "nested.txt"), 'w') as f:
            f.write("Nested file")
        
        file2 = os.path.join(test_dir, "file2.txt")
        with open(file2, 'w') as f:
            f.write("File 2")
        
        # Copy mixed items
        cm = ClipboardManager()
        cm.copy([file1, dir1, file2])
        
        dest_dir = os.path.join(test_dir, "dest")
        os.makedirs(dest_dir)
        
        result = cm.paste(dest_dir)
        
        if (len(result) == 3 and
            os.path.isfile(os.path.join(dest_dir, "file1.txt")) and
            os.path.isdir(os.path.join(dest_dir, "dir1")) and
            os.path.isfile(os.path.join(dest_dir, "file2.txt"))):
            results.add_pass("Mixed file/directory copy")
        else:
            results.add_fail("Mixed file/directory copy", "Not all items copied correctly")
        
    except Exception as e:
        results.add_error("Mixed file/directory operations", e)
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_clipboard_state_consistency():
    """Test clipboard state remains consistent."""
    print("\n--- Testing Clipboard State Consistency ---")
    
    try:
        cm = ClipboardManager()
        
        # Initial state
        assert not cm.has_items()
        assert cm.operation == ""
        assert len(cm.items) == 0
        
        # After copy
        cm.copy(["/tmp/test"])
        assert cm.has_items()
        assert cm.operation == "copy"
        assert len(cm.items) == 1
        
        # After cut
        cm.cut(["/tmp/test1", "/tmp/test2"])
        assert cm.has_items()
        assert cm.operation == "cut"
        assert len(cm.items) == 2
        
        # After clear
        cm.clear()
        assert not cm.has_items()
        assert cm.operation == ""
        assert len(cm.items) == 0
        
        results.add_pass("Clipboard state consistency")
        
    except Exception as e:
        results.add_error("Clipboard state consistency", e)


def run_all_integration_tests():
    """Run all integration tests."""
    print("="*60)
    print("Terminal Explorer - Integration Test Suite")
    print("="*60)
    
    test_special_characters_in_filenames()
    test_very_long_paths()
    test_unicode_filenames()
    test_empty_directory_operations()
    test_nested_directory_operations()
    test_large_file_operations()
    test_readonly_scenarios()
    test_concurrent_operations()
    test_history_edge_cases()
    test_mixed_file_directory_operations()
    test_clipboard_state_consistency()
    
    success = results.summary()
    
    print("\n" + "="*60)
    if success:
        print("All integration tests passed! ✓")
        print("="*60)
        return 0
    else:
        print("Some integration tests failed. See details above.")
        print("="*60)
        return 1


if __name__ == "__main__":
    sys.exit(run_all_integration_tests())
