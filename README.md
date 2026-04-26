# Terminal Explorer

A Textual based terminal file explorer with dual pane support.

## Requirements
- Python 3.10 or newer
- `pip`
- A terminal with Unicode support

## Run On macOS
1. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   python3 -m pip install -r requirements.txt
   ```
3. Start the app:
   ```bash
   python3 explorer.py
   ```

## Run On Linux
1. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   python3 -m pip install -r requirements.txt
   ```
3. Start the app:
   ```bash
   python3 explorer.py
   ```

If your Linux distribution uses Wayland or does not already provide clipboard helpers, install one of `wl-clipboard`, `xclip`, or `xsel` if clipboard actions do not work as expected in your terminal session.

## Features
- Dual pane file navigation
- Clipboard integration
- Custom icon and Windows executable builds

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

The generated executables are located in the `dist` directory.

## License
This project is licensed under the GNU General Public License v3.0. See the `LICENSE` file for details.
