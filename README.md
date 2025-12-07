# Terminal Explorer

A Textual based terminal file explorer with dual pane support.

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
# terminal-explorer
