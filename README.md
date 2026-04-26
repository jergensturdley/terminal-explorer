# Terminal Explorer

A Textual based terminal file explorer with dual pane support.

## Requirements
- Python 3.10 or newer
- `pip`
- A terminal with Unicode support

## Run On macOS
The verified macOS flow for this repository is to use the virtual environment's Python directly, which avoids shell-specific activation issues.

Run these commands from the project root, where `requirements.txt` and `explorer.py` are located.

1. Change into the project directory:
   ```bash
   cd /path/to/terminal-explorer
   ```
2. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   ```
3. Install dependencies:
   ```bash
   ./.venv/bin/python -m pip install -r requirements.txt
   ```
4. Start the app:
   ```bash
   ./.venv/bin/python explorer.py
   ```

Optional activation commands:

```bash
# zsh or bash
source .venv/bin/activate

# fish
source .venv/bin/activate.fish
```

## Run On Linux
Run these commands from the project root, where `requirements.txt` and `explorer.py` are located.

1. Change into the project directory:
   ```bash
   cd /path/to/terminal-explorer
   ```
2. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   ```
3. Install dependencies:
   ```bash
   ./.venv/bin/python -m pip install -r requirements.txt
   ```
4. Start the app:
   ```bash
   ./.venv/bin/python explorer.py
   ```

If you prefer activating the environment first, use `source .venv/bin/activate` for `bash` or `zsh`, or `source .venv/bin/activate.fish` for `fish`.

If your Linux distribution uses Wayland or does not already provide clipboard helpers, install one of `wl-clipboard`, `xclip`, or `xsel` if clipboard actions do not work as expected in your terminal session.

## Features
- Dual pane file navigation
- Back/forward/up/refresh navigation controls
- Toggle hidden files with `h`
- Clipboard integration
- Custom icon and Windows executable builds

## Testing
```bash
python test_all.py
```

The active test suite uses `pytest` and lives in `tests/`. Older script-style tests are kept in `legacy_tests/` for reference.

## Building
Two build options are provided:
1. **Single‑file executable** (slow start, easy distribution)
   ```powershell
   pyinstaller --onefile --console --icon=explorer.ico --name="Terminal Explorer" explorer.py
   ```
2. **Fast folder build** (quick start, requires distributing the folder)
   ```powershell
   pyinstaller --onedir --console --icon=explorer.ico --name="Terminal Explorer Fast" explorer.py
   ```

### macOS App Wrapper
If you want a Launch Services `.app` bundle that can be launched from Finder and opened against folders, build the wrapper from the project root:

```bash
chmod +x build_macos_app.sh
./build_macos_app.sh
```

This creates `dist/Terminal Explorer.app`. The wrapper launches the bundled terminal binary inside Terminal.app and forwards any folder paths Finder sends to the app.

For a custom app icon, add `explorer.icns`, `explorer.png`, or `explorer.ico` at the project root before running the script. If a PNG or ICO is present, the script converts it to an `.icns` file automatically.

The generated executables are located in the `dist` directory.

## License
This project is licensed under the GNU General Public License v3.0. See the `LICENSE` file for details.
