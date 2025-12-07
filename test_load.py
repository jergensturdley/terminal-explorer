from explorer import ExplorerApp
import sys

try:
    app = ExplorerApp()
    print("App instantiated successfully")
except Exception as e:
    print(f"Failed to instantiate app: {e}")
    sys.exit(1)
